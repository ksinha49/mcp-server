"""
Sandbox Manager for Code Execution

Provides a unified interface for executing TypeScript code in sandboxed environments.
Supports both Deno (V8 isolates) and Docker (container-based) sandboxing.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
import re


class SandboxMode(Enum):
    """Available sandbox modes."""
    DENO = "deno"
    DOCKER = "docker"


@dataclass
class ExecutionContext:
    """Context for code execution."""
    code: str
    timeout_ms: int = 60000
    max_memory_mb: int = 128
    variables: Dict[str, Any] = field(default_factory=dict)
    auth_token: Optional[str] = None
    user_id: Optional[str] = None


@dataclass
class ToolCall:
    """Record of a tool call during execution."""
    provider: str
    tool: str
    arguments: Dict[str, Any]
    duration_ms: int
    success: bool
    error: Optional[str] = None


@dataclass
class ExecutionResult:
    """Result of code execution."""
    success: bool
    result: Any = None
    error: Optional[str] = None
    logs: List[str] = field(default_factory=list)
    execution_time_ms: int = 0
    tools_called: List[ToolCall] = field(default_factory=list)


@dataclass
class ValidationResult:
    """Result of code validation."""
    valid: bool
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)


class CodeAnalyzer:
    """Static code analysis for security."""

    FORBIDDEN_PATTERNS = [
        (r'\beval\s*\(', "eval() is not allowed"),
        (r'\bFunction\s*\(', "Function constructor is not allowed"),
        (r'\bnew\s+Function\s*\(', "new Function() is not allowed"),
        (r'import\s*\(', "Dynamic imports are not allowed"),
        (r'\bDeno\.', "Direct Deno API access is not allowed"),
        (r'\bglobalThis\b', "globalThis access is not allowed"),
        (r'__proto__', "__proto__ access is not allowed"),
        (r'\bconstructor\s*\[', "constructor[] access is not allowed"),
        (r'\brequire\s*\(', "require() is not allowed"),
        (r'\bprocess\.', "process access is not allowed"),
        (r'\bchild_process', "child_process is not allowed"),
        (r'\bfs\s*\.', "fs module access is not allowed"),
        (r'Buffer\s*\.from\s*\([^)]*,\s*[\'"]base64[\'"]\s*\)', "Base64 buffer operations require review"),
    ]

    @classmethod
    def analyze(cls, code: str) -> ValidationResult:
        """Analyze code for security issues."""
        errors = []
        warnings = []

        for pattern, message in cls.FORBIDDEN_PATTERNS:
            matches = list(re.finditer(pattern, code, re.IGNORECASE))
            for match in matches:
                line_num = code[:match.start()].count('\n') + 1
                errors.append({
                    "line": line_num,
                    "column": match.start() - code.rfind('\n', 0, match.start()),
                    "message": message,
                    "pattern": pattern,
                })

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )


class SandboxManager(ABC):
    """Abstract base class for sandbox execution managers."""

    @abstractmethod
    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute code in the sandbox."""
        pass

    @abstractmethod
    async def validate(self, code: str) -> ValidationResult:
        """Validate code without executing."""
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check sandbox health status."""
        pass

    @abstractmethod
    async def start(self) -> None:
        """Start the sandbox environment."""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop the sandbox environment."""
        pass

    def pre_validate(self, code: str) -> ValidationResult:
        """Run static analysis before execution."""
        return CodeAnalyzer.analyze(code)

    @staticmethod
    def create(mode: SandboxMode, **kwargs) -> "SandboxManager":
        """Factory method to create appropriate sandbox manager."""
        if mode == SandboxMode.DENO:
            from .deno_executor import DenoExecutor
            return DenoExecutor(**kwargs)
        elif mode == SandboxMode.DOCKER:
            from .docker_executor import DockerExecutor
            return DockerExecutor(**kwargs)
        else:
            raise ValueError(f"Unknown sandbox mode: {mode}")
