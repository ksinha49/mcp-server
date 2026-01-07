/**
 * Provider Discovery and Lazy Loading Registry
 *
 * Implements filesystem-based discovery for progressive tool loading
 * as described in "Code Execution with MCP" pattern.
 */

import type { Provider, ToolDefinition, PythonBackend, ToolResult } from './types.ts';

/**
 * Manifest of available providers (for fast startup without loading all modules)
 */
export interface ProviderManifest {
  providers: string[];
  version: string;
  generatedAt: string;
}

/**
 * Lazy-loading provider registry
 *
 * Providers are loaded on-demand when first accessed,
 * reducing initial context window usage.
 */
export class LazyProviderRegistry {
  private basePath: string;
  private loaded = new Map<string, Provider>();
  private loading = new Map<string, Promise<Provider>>();
  private manifest: ProviderManifest;

  constructor(basePath: string) {
    this.basePath = basePath;
    this.manifest = {
      providers: ['outlook', 'sharepoint', 'teams', 'azuredevops', 'snowflake'],
      version: '1.0.0',
      generatedAt: new Date().toISOString(),
    };
  }

  /**
   * List available providers without loading them
   */
  listProviders(): string[] {
    return this.manifest.providers;
  }

  /**
   * Check if a provider exists
   */
  hasProvider(name: string): boolean {
    return this.manifest.providers.includes(name);
  }

  /**
   * Get a provider, loading it if necessary
   */
  async getProvider(name: string): Promise<Provider | null> {
    if (this.loaded.has(name)) {
      return this.loaded.get(name)!;
    }

    if (!this.hasProvider(name)) {
      return null;
    }

    if (this.loading.has(name)) {
      return this.loading.get(name)!;
    }

    const promise = this.loadProvider(name);
    this.loading.set(name, promise);

    try {
      const provider = await promise;
      this.loaded.set(name, provider);
      return provider;
    } finally {
      this.loading.delete(name);
    }
  }

  /**
   * Load a provider module dynamically
   */
  private async loadProvider(name: string): Promise<Provider> {
    const module = await import(`./${name}/index.ts`);
    return module.default || module.provider;
  }

  /**
   * Get all tool definitions from loaded providers
   */
  async getAllTools(enabled?: string[]): Promise<ToolDefinition[]> {
    const providers = enabled || this.manifest.providers;
    const tools: ToolDefinition[] = [];

    for (const name of providers) {
      const provider = await this.getProvider(name);
      if (provider) {
        tools.push(...provider.listTools());
      }
    }

    return tools;
  }

  /**
   * Get tool count without loading providers
   */
  getToolCount(): Record<string, number> {
    // Hardcoded counts to avoid loading all modules
    return {
      outlook: 6,
      sharepoint: 4,
      teams: 5,
      azuredevops: 6,
      snowflake: 6,
    };
  }
}

/**
 * Create a Python backend client for tool execution
 */
export function createPythonBackend(backendUrl: string, authToken?: string): PythonBackend {
  return {
    async callTool<T>(
      provider: string,
      tool: string,
      args: Record<string, unknown>
    ): Promise<ToolResult<T>> {
      const startTime = Date.now();

      try {
        const response = await fetch(`${backendUrl}/mcp/${provider}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
          },
          body: JSON.stringify({
            jsonrpc: '2.0',
            method: 'tools/call',
            params: {
              name: tool,
              arguments: args,
            },
            id: crypto.randomUUID(),
          }),
        });

        if (!response.ok) {
          return {
            success: false,
            error: `HTTP ${response.status}: ${await response.text()}`,
            metadata: {
              executionTimeMs: Date.now() - startTime,
              cached: false,
            },
          };
        }

        const result = await response.json();

        if (result.error) {
          return {
            success: false,
            error: result.error.message || 'Unknown error',
            metadata: {
              executionTimeMs: Date.now() - startTime,
              cached: false,
            },
          };
        }

        // Parse the result content
        const content = result.result?.content?.[0];
        let data: T;

        if (content?.type === 'text') {
          try {
            data = JSON.parse(content.text) as T;
          } catch {
            data = content.text as T;
          }
        } else {
          data = result.result as T;
        }

        return {
          success: true,
          data,
          metadata: {
            executionTimeMs: Date.now() - startTime,
            cached: false,
          },
        };
      } catch (error) {
        return {
          success: false,
          error: error instanceof Error ? error.message : String(error),
          metadata: {
            executionTimeMs: Date.now() - startTime,
            cached: false,
          },
        };
      }
    },
  };
}

// Default registry instance
let registryInstance: LazyProviderRegistry | null = null;

export function getRegistry(basePath?: string): LazyProviderRegistry {
  if (!registryInstance) {
    registryInstance = new LazyProviderRegistry(basePath || './providers');
  }
  return registryInstance;
}

export default getRegistry;
