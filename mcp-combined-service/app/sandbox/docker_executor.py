"""
Docker Sandbox Executor

Executes TypeScript code in isolated Docker containers with seccomp profiles.
Provides maximum isolation with pre-warmed container pool for low latency.
"""

import asyncio
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import (
    ExecutionContext,
    ExecutionResult,
    SandboxManager,
    ToolCall,
    ValidationResult,
)

logger = logging.getLogger(__name__)


@dataclass
class Container:
    """Represents a pre-warmed Docker container."""
    id: str
    port: int
    created_at: float
    in_use: bool = False


class ContainerPool:
    """Manages a pool of pre-warmed Docker containers."""

    def __init__(
        self,
        pool_size: int = 5,
        image: str = "mcp-code-executor:latest",
        base_port: int = 9000,
        max_container_age: int = 3600,
        python_backend_url: str = "http://host.docker.internal:8000",
    ):
        self.pool_size = pool_size
        self.image = image
        self.base_port = base_port
        self.max_container_age = max_container_age
        self.python_backend_url = python_backend_url
        self._containers: List[Container] = []
        self._lock = asyncio.Lock()
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the container pool."""
        if self._initialized:
            return

        logger.info(f"Initializing container pool with {self.pool_size} containers")
        tasks = [
            self._create_container(self.base_port + i)
            for i in range(self.pool_size)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Failed to create container: {result}")
            elif result:
                self._containers.append(result)

        self._initialized = True
        logger.info(f"Container pool initialized with {len(self._containers)} containers")

    async def _create_container(self, port: int) -> Optional[Container]:
        """Create a new pre-warmed container."""
        container_name = f"mcp-executor-{port}"

        # Remove existing container if any
        await self._run_docker_command(["rm", "-f", container_name])

        # Get seccomp profile path
        seccomp_path = Path(__file__).parent.parent.parent / "docker" / "executor" / "seccomp-profile.json"

        # Build docker run command
        cmd = [
            "run", "-d",
            "--name", container_name,
            "-p", f"{port}:3000",
            "--memory", "128m",
            "--cpus", "0.5",
            "--network", "none",
            "--read-only",
            "--security-opt", "no-new-privileges",
            "-e", f"PYTHON_BACKEND_URL={self.python_backend_url}",
            "-e", "NODE_ENV=production",
        ]

        # Add seccomp profile if exists
        if seccomp_path.exists():
            cmd.extend(["--security-opt", f"seccomp={seccomp_path}"])

        cmd.append(self.image)

        try:
            result = await self._run_docker_command(cmd)
            if result:
                container_id = result.strip()[:12]
                container = Container(
                    id=container_id,
                    port=port,
                    created_at=time.time(),
                )
                logger.info(f"Created container {container_name} on port {port}")
                return container
        except Exception as e:
            logger.error(f"Failed to create container on port {port}: {e}")
            return None

    async def _run_docker_command(self, args: List[str]) -> Optional[str]:
        """Run a docker command and return stdout."""
        try:
            process = await asyncio.create_subprocess_exec(
                "docker", *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                if stderr:
                    logger.debug(f"Docker command stderr: {stderr.decode()}")
                return None
            return stdout.decode() if stdout else ""
        except Exception as e:
            logger.error(f"Docker command failed: {e}")
            return None

    async def acquire(self) -> Optional[Container]:
        """Acquire a container from the pool."""
        async with self._lock:
            # Find available container
            for container in self._containers:
                if not container.in_use:
                    container.in_use = True
                    return container

            # No available containers
            logger.warning("No available containers in pool")
            return None

    async def release(self, container: Container) -> None:
        """Release a container back to the pool."""
        async with self._lock:
            container.in_use = False

            # Check if container is too old and needs recycling
            if time.time() - container.created_at > self.max_container_age:
                await self._recycle_container(container)

    async def _recycle_container(self, old_container: Container) -> None:
        """Recycle an old container with a fresh one."""
        logger.info(f"Recycling container on port {old_container.port}")

        # Remove from pool
        self._containers = [c for c in self._containers if c.id != old_container.id]

        # Kill old container
        await self._run_docker_command(["rm", "-f", f"mcp-executor-{old_container.port}"])

        # Create new container
        new_container = await self._create_container(old_container.port)
        if new_container:
            self._containers.append(new_container)

    async def shutdown(self) -> None:
        """Shutdown all containers in the pool."""
        logger.info("Shutting down container pool")
        for container in self._containers:
            await self._run_docker_command(["rm", "-f", f"mcp-executor-{container.port}"])
        self._containers = []
        self._initialized = False

    def get_status(self) -> Dict[str, Any]:
        """Get pool status."""
        available = sum(1 for c in self._containers if not c.in_use)
        return {
            "pool_size": self.pool_size,
            "active_containers": len(self._containers),
            "available": available,
            "in_use": len(self._containers) - available,
        }


class DockerExecutor(SandboxManager):
    """Docker-based sandbox executor using isolated containers."""

    def __init__(
        self,
        pool_size: int = 5,
        image: str = "mcp-code-executor:latest",
        base_port: int = 9000,
        python_backend_port: int = 8000,
    ):
        self.python_backend_port = python_backend_port
        self._pool = ContainerPool(
            pool_size=pool_size,
            image=image,
            base_port=base_port,
            python_backend_url=f"http://host.docker.internal:{python_backend_port}",
        )

    async def start(self) -> None:
        """Initialize the container pool."""
        await self._pool.initialize()

    async def stop(self) -> None:
        """Shutdown the container pool."""
        await self._pool.shutdown()

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute TypeScript code in Docker container."""
        import httpx

        # Pre-validate code
        validation = self.pre_validate(context.code)
        if not validation.valid:
            return ExecutionResult(
                success=False,
                error=f"Code validation failed: {validation.errors[0]['message']}",
            )

        # Acquire container from pool
        container = await self._pool.acquire()
        if not container:
            return ExecutionResult(
                success=False,
                error="No available execution containers. Please try again later.",
            )

        try:
            async with httpx.AsyncClient(timeout=context.timeout_ms / 1000 + 5) as client:
                response = await client.post(
                    f"http://localhost:{container.port}/execute",
                    json={
                        "code": context.code,
                        "timeout_ms": context.timeout_ms,
                        "variables": context.variables,
                        "auth_token": context.auth_token,
                    },
                )

                if response.status_code != 200:
                    return ExecutionResult(
                        success=False,
                        error=f"Execution failed with status {response.status_code}: {response.text}",
                    )

                data = response.json()
                return ExecutionResult(
                    success=data.get("success", False),
                    result=data.get("result"),
                    error=data.get("error"),
                    logs=data.get("logs", []),
                    execution_time_ms=data.get("execution_time_ms", 0),
                    tools_called=[
                        ToolCall(
                            provider=tc.get("provider", ""),
                            tool=tc.get("tool", ""),
                            arguments=tc.get("arguments", {}),
                            duration_ms=tc.get("duration_ms", 0),
                            success=tc.get("success", True),
                            error=tc.get("error"),
                        )
                        for tc in data.get("tools_called", [])
                    ],
                )

        except httpx.TimeoutException:
            return ExecutionResult(
                success=False,
                error=f"Execution timed out after {context.timeout_ms}ms",
            )
        except Exception as e:
            logger.exception("Execution failed")
            return ExecutionResult(
                success=False,
                error=str(e),
            )
        finally:
            await self._pool.release(container)

    async def validate(self, code: str) -> ValidationResult:
        """Validate TypeScript code without executing."""
        # For Docker mode, we only do static analysis
        # Full TypeScript validation would require running in container
        return self.pre_validate(code)

    async def health_check(self) -> Dict[str, Any]:
        """Check Docker executor health."""
        pool_status = self._pool.get_status()
        return {
            "status": "healthy" if pool_status["available"] > 0 else "degraded",
            "mode": "docker",
            **pool_status,
        }
