/**
 * Code Executor
 *
 * Sandboxed TypeScript code execution engine.
 * Executes agent-generated code with access to MCP tools.
 */

import { getRegistry, createPythonBackend } from './providers/index.ts';
import type { PythonBackend, ToolResult } from './providers/types.ts';
import * as stdlib from './stdlib/index.ts';

/**
 * Execution options
 */
export interface ExecutionOptions {
  timeout: number;
  variables: Record<string, unknown>;
  authToken?: string;
  maxToolCalls?: number;
}

/**
 * Tool call record
 */
export interface ToolCallRecord {
  provider: string;
  tool: string;
  arguments: Record<string, unknown>;
  duration_ms: number;
  success: boolean;
  error?: string;
}

/**
 * Execution result
 */
export interface ExecutionResult {
  success: boolean;
  result?: unknown;
  error?: string;
  logs: string[];
  execution_time_ms: number;
  tools_called: ToolCallRecord[];
}

/**
 * Validation result
 */
export interface ValidationResult {
  valid: boolean;
  errors: Array<{ line?: number; column?: number; message: string }>;
  warnings: Array<{ line?: number; column?: number; message: string }>;
}

/**
 * Forbidden patterns for static analysis
 */
const FORBIDDEN_PATTERNS: Array<[RegExp, string]> = [
  [/\beval\s*\(/i, 'eval() is not allowed'],
  [/\bFunction\s*\(/i, 'Function constructor is not allowed'],
  [/\bnew\s+Function\s*\(/i, 'new Function() is not allowed'],
  [/import\s*\(/i, 'Dynamic imports are not allowed'],
  [/\bDeno\./i, 'Direct Deno API access is not allowed'],
  [/\bglobalThis\b/i, 'globalThis access is not allowed'],
  [/__proto__/i, '__proto__ access is not allowed'],
  [/\bconstructor\s*\[/i, 'constructor[] access is not allowed'],
  [/\brequire\s*\(/i, 'require() is not allowed'],
  [/\bprocess\./i, 'process access is not allowed'],
];

/**
 * Static code analysis
 */
function analyzeCode(code: string): ValidationResult {
  const errors: Array<{ line?: number; column?: number; message: string }> = [];
  const warnings: Array<{ line?: number; column?: number; message: string }> = [];

  for (const [pattern, message] of FORBIDDEN_PATTERNS) {
    const matches = code.matchAll(new RegExp(pattern, 'gi'));
    for (const match of matches) {
      const lineNum = code.slice(0, match.index).split('\n').length;
      const lastNewline = code.lastIndexOf('\n', match.index);
      const column = match.index! - lastNewline;
      errors.push({ line: lineNum, column, message });
    }
  }

  return {
    valid: errors.length === 0,
    errors,
    warnings,
  };
}

/**
 * Code Executor class
 */
export class Executor {
  private pythonBackendUrl: string;
  private maxToolCalls: number;

  constructor(pythonBackendUrl: string, maxToolCalls = 50) {
    this.pythonBackendUrl = pythonBackendUrl;
    this.maxToolCalls = maxToolCalls;
  }

  /**
   * Validate code without executing
   */
  validate(code: string): ValidationResult {
    return analyzeCode(code);
  }

  /**
   * Execute code in sandboxed environment
   */
  async execute(code: string, options: ExecutionOptions): Promise<ExecutionResult> {
    const startTime = Date.now();
    const logs: string[] = [];
    const toolsCalled: ToolCallRecord[] = [];
    let toolCallCount = 0;

    // Static analysis
    const validation = this.validate(code);
    if (!validation.valid) {
      return {
        success: false,
        error: `Validation failed: ${validation.errors[0]?.message}`,
        logs,
        execution_time_ms: Date.now() - startTime,
        tools_called: toolsCalled,
      };
    }

    // Create backend with tool call tracking
    const backend = this.createTrackedBackend(
      options.authToken,
      toolsCalled,
      () => {
        toolCallCount++;
        if (toolCallCount > (options.maxToolCalls || this.maxToolCalls)) {
          throw new Error(`Maximum tool calls exceeded (${this.maxToolCalls})`);
        }
      }
    );

    // Create tools proxy
    const tools = this.createToolsProxy(backend);

    // Create console capture
    const console = this.createConsoleMock(logs);

    // Execute with timeout
    try {
      const result = await this.executeWithTimeout(
        code,
        { tools, stdlib, console, ...options.variables },
        options.timeout
      );

      return {
        success: true,
        result,
        logs,
        execution_time_ms: Date.now() - startTime,
        tools_called: toolsCalled,
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : String(error),
        logs,
        execution_time_ms: Date.now() - startTime,
        tools_called: toolsCalled,
      };
    }
  }

  /**
   * Create a backend that tracks tool calls
   */
  private createTrackedBackend(
    authToken: string | undefined,
    toolsCalled: ToolCallRecord[],
    onCall: () => void
  ): PythonBackend {
    const backend = createPythonBackend(this.pythonBackendUrl, authToken);

    return {
      async callTool<T>(
        provider: string,
        tool: string,
        args: Record<string, unknown>
      ): Promise<ToolResult<T>> {
        onCall();
        const startTime = Date.now();

        try {
          const result = await backend.callTool<T>(provider, tool, args);
          toolsCalled.push({
            provider,
            tool,
            arguments: args,
            duration_ms: Date.now() - startTime,
            success: result.success,
            error: result.error,
          });
          return result;
        } catch (error) {
          const errorMsg = error instanceof Error ? error.message : String(error);
          toolsCalled.push({
            provider,
            tool,
            arguments: args,
            duration_ms: Date.now() - startTime,
            success: false,
            error: errorMsg,
          });
          throw error;
        }
      },
    };
  }

  /**
   * Create a proxy for accessing provider tools
   */
  private createToolsProxy(backend: PythonBackend): Record<string, unknown> {
    const registry = getRegistry();
    const providers = registry.listProviders();

    const tools: Record<string, Record<string, unknown>> = {};

    for (const provider of providers) {
      tools[provider] = new Proxy(
        {},
        {
          get(_target, prop: string) {
            return async (args: Record<string, unknown>) => {
              const result = await backend.callTool(provider, prop, args);
              if (!result.success) {
                throw new Error(result.error || 'Tool execution failed');
              }
              return result.data;
            };
          },
        }
      );
    }

    return tools;
  }

  /**
   * Create a mock console that captures logs
   */
  private createConsoleMock(logs: string[]): Record<string, (...args: unknown[]) => void> {
    const formatArgs = (...args: unknown[]): string => {
      return args
        .map((arg) => {
          if (typeof arg === 'object') {
            try {
              return JSON.stringify(arg);
            } catch {
              return String(arg);
            }
          }
          return String(arg);
        })
        .join(' ');
    };

    return {
      log: (...args: unknown[]) => logs.push(`[LOG] ${formatArgs(...args)}`),
      info: (...args: unknown[]) => logs.push(`[INFO] ${formatArgs(...args)}`),
      warn: (...args: unknown[]) => logs.push(`[WARN] ${formatArgs(...args)}`),
      error: (...args: unknown[]) => logs.push(`[ERROR] ${formatArgs(...args)}`),
      debug: (...args: unknown[]) => logs.push(`[DEBUG] ${formatArgs(...args)}`),
    };
  }

  /**
   * Execute code with a timeout
   */
  private async executeWithTimeout(
    code: string,
    context: Record<string, unknown>,
    timeoutMs: number
  ): Promise<unknown> {
    // Wrap code in an async function that has access to context variables
    const contextKeys = Object.keys(context);
    const contextValues = Object.values(context);

    // Create the wrapped code
    const wrappedCode = `
      return (async function(${contextKeys.join(', ')}) {
        ${code}
      })(${contextKeys.map((_, i) => `arguments[${i}]`).join(', ')});
    `;

    // Create and execute the function with timeout
    const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
    const fn = new AsyncFunction(...contextKeys, wrappedCode);

    // Execute with timeout
    const timeoutPromise = new Promise((_, reject) => {
      setTimeout(() => reject(new Error(`Execution timed out after ${timeoutMs}ms`)), timeoutMs);
    });

    return Promise.race([fn(...contextValues), timeoutPromise]);
  }

  /**
   * List all available tools
   */
  async listAllTools(): Promise<
    Array<{ provider: string; tool: string; description: string }>
  > {
    const registry = getRegistry();
    const tools = await registry.getAllTools();
    return tools.map((t) => ({
      provider: t.provider,
      tool: t.name,
      description: t.description,
    }));
  }
}

// Default executor instance
let executorInstance: Executor | null = null;

export function getExecutor(pythonBackendUrl?: string): Executor {
  if (!executorInstance) {
    const url = pythonBackendUrl || 'http://localhost:8000';
    executorInstance = new Executor(url);
  }
  return executorInstance;
}

export default Executor;
