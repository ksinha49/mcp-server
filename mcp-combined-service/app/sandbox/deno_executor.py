"""
Deno Sandbox Executor

Executes TypeScript code in Deno's sandboxed V8 isolate environment.
Provides fast startup (~50ms) with granular permission controls.
"""

import asyncio
import json
import logging
import os
import signal
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import httpx

from . import (
    ExecutionContext,
    ExecutionResult,
    SandboxManager,
    ToolCall,
    ValidationResult,
)

logger = logging.getLogger(__name__)


class DenoExecutor(SandboxManager):
    """Deno-based sandbox executor using V8 isolates."""

    def __init__(
        self,
        deno_server_port: int = 8001,
        python_backend_port: int = 8000,
        code_api_path: Optional[str] = None,
        startup_timeout: int = 30,
    ):
        self.deno_server_port = deno_server_port
        self.python_backend_port = python_backend_port
        self.code_api_path = code_api_path or self._find_code_api_path()
        self.startup_timeout = startup_timeout
        self._process: Optional[asyncio.subprocess.Process] = None
        self._client: Optional[httpx.AsyncClient] = None
        self._base_url = f"http://localhost:{deno_server_port}"

    def _find_code_api_path(self) -> str:
        """Find the code-api directory relative to this file."""
        current_dir = Path(__file__).parent.parent.parent
        code_api_path = current_dir / "code-api"
        return str(code_api_path)

    async def start(self) -> None:
        """Start the Deno server subprocess."""
        if self._process is not None:
            logger.warning("Deno server already running")
            return

        server_path = Path(self.code_api_path) / "server.ts"
        if not server_path.exists():
            raise FileNotFoundError(f"Deno server not found: {server_path}")

        env = os.environ.copy()
        env["PYTHON_BACKEND_URL"] = f"http://localhost:{self.python_backend_port}"
        env["DENO_PORT"] = str(self.deno_server_port)

        logger.info(f"Starting Deno server on port {self.deno_server_port}")

        self._process = await asyncio.create_subprocess_exec(
            "deno",
            "run",
            "--allow-net=localhost",
            "--allow-read=" + self.code_api_path,
            "--allow-env=PYTHON_BACKEND_URL,DENO_PORT",
            str(server_path),
            cwd=self.code_api_path,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        self._client = httpx.AsyncClient(timeout=60.0)

        # Wait for server to be ready
        await self._wait_for_ready()
        logger.info("Deno server started successfully")

    async def _wait_for_ready(self) -> None:
        """Wait for the Deno server to become ready."""
        start_time = asyncio.get_event_loop().time()
        while True:
            try:
                response = await self._client.get(f"{self._base_url}/health")
                if response.status_code == 200:
                    return
            except httpx.ConnectError:
                pass

            if asyncio.get_event_loop().time() - start_time > self.startup_timeout:
                await self.stop()
                raise TimeoutError(
                    f"Deno server failed to start within {self.startup_timeout}s"
                )

            await asyncio.sleep(0.1)

    async def stop(self) -> None:
        """Stop the Deno server subprocess."""
        if self._client:
            await self._client.aclose()
            self._client = None

        if self._process:
            logger.info("Stopping Deno server")
            try:
                self._process.terminate()
                try:
                    await asyncio.wait_for(self._process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    self._process.kill()
                    await self._process.wait()
            except ProcessLookupError:
                pass
            self._process = None

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute TypeScript code in Deno sandbox."""
        # Pre-validate code
        validation = self.pre_validate(context.code)
        if not validation.valid:
            return ExecutionResult(
                success=False,
                error=f"Code validation failed: {validation.errors[0]['message']}",
            )

        if not self._client:
            await self.start()

        try:
            response = await self._client.post(
                f"{self._base_url}/execute",
                json={
                    "code": context.code,
                    "timeout_ms": context.timeout_ms,
                    "variables": context.variables,
                    "auth_token": context.auth_token,
                },
                timeout=context.timeout_ms / 1000 + 5,
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

    async def validate(self, code: str) -> ValidationResult:
        """Validate TypeScript code without executing."""
        # First run static analysis
        static_result = self.pre_validate(code)
        if not static_result.valid:
            return static_result

        if not self._client:
            await self.start()

        try:
            response = await self._client.post(
                f"{self._base_url}/validate",
                json={"code": code},
            )

            if response.status_code != 200:
                return ValidationResult(
                    valid=False,
                    errors=[{"message": f"Validation request failed: {response.text}"}],
                )

            data = response.json()
            return ValidationResult(
                valid=data.get("valid", False),
                errors=data.get("errors", []),
                warnings=data.get("warnings", []),
            )

        except Exception as e:
            return ValidationResult(
                valid=False,
                errors=[{"message": str(e)}],
            )

    async def health_check(self) -> Dict[str, Any]:
        """Check Deno server health."""
        if not self._client or not self._process:
            return {
                "status": "stopped",
                "mode": "deno",
            }

        try:
            response = await self._client.get(f"{self._base_url}/health")
            data = response.json()
            return {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "mode": "deno",
                "port": self.deno_server_port,
                **data,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "mode": "deno",
                "error": str(e),
            }
