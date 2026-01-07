/**
 * Azure DevOps Provider
 *
 * Projects, repos, pipelines, and work items via Azure DevOps REST API.
 */

import type { Provider, ToolDefinition, Tool, PythonBackend } from '../types.ts';

const tools: Record<string, Tool> = {
  list_projects: {
    definition: {
      name: 'list_projects',
      provider: 'azuredevops',
      description: 'List accessible projects',
      inputSchema: {
        type: 'object',
        properties: {
          max_results: { type: 'integer', description: 'Maximum results', default: 25 },
        },
      },
    },
    execute: async (backend: PythonBackend, input: Record<string, unknown>) => {
      return backend.callTool('azuredevops', 'list_projects', input);
    },
  },

  search_work_items: {
    definition: {
      name: 'search_work_items',
      provider: 'azuredevops',
      description: 'Search work items by query',
      inputSchema: {
        type: 'object',
        properties: {
          project: { type: 'string', description: 'Project name' },
          query: { type: 'string', description: 'WIQL or keyword query' },
          max_results: { type: 'integer', description: 'Maximum results', default: 25 },
        },
        required: ['project', 'query'],
      },
    },
    execute: async (backend: PythonBackend, input: Record<string, unknown>) => {
      return backend.callTool('azuredevops', 'search_work_items', input);
    },
  },

  get_work_item: {
    definition: {
      name: 'get_work_item',
      provider: 'azuredevops',
      description: 'Get work item details by ID',
      inputSchema: {
        type: 'object',
        properties: {
          work_item_id: { type: 'integer', description: 'Work item ID' },
        },
        required: ['work_item_id'],
      },
    },
    execute: async (backend: PythonBackend, input: Record<string, unknown>) => {
      return backend.callTool('azuredevops', 'get_work_item', input);
    },
  },

  list_repos: {
    definition: {
      name: 'list_repos',
      provider: 'azuredevops',
      description: 'List repositories in a project',
      inputSchema: {
        type: 'object',
        properties: {
          project: { type: 'string', description: 'Project name' },
        },
        required: ['project'],
      },
    },
    execute: async (backend: PythonBackend, input: Record<string, unknown>) => {
      return backend.callTool('azuredevops', 'list_repos', input);
    },
  },

  list_pipelines: {
    definition: {
      name: 'list_pipelines',
      provider: 'azuredevops',
      description: 'List pipelines in a project',
      inputSchema: {
        type: 'object',
        properties: {
          project: { type: 'string', description: 'Project name' },
        },
        required: ['project'],
      },
    },
    execute: async (backend: PythonBackend, input: Record<string, unknown>) => {
      return backend.callTool('azuredevops', 'list_pipelines', input);
    },
  },

  list_pull_requests: {
    definition: {
      name: 'list_pull_requests',
      provider: 'azuredevops',
      description: 'List pull requests in a repository',
      inputSchema: {
        type: 'object',
        properties: {
          project: { type: 'string', description: 'Project name' },
          repo: { type: 'string', description: 'Repository name' },
          status: {
            type: 'string',
            enum: ['active', 'completed', 'abandoned', 'all'],
            default: 'active',
          },
        },
        required: ['project', 'repo'],
      },
    },
    execute: async (backend: PythonBackend, input: Record<string, unknown>) => {
      return backend.callTool('azuredevops', 'list_pull_requests', input);
    },
  },
};

export const provider: Provider = {
  name: 'azuredevops',
  description: 'Azure DevOps projects, repos, pipelines, and work items',

  listTools(): ToolDefinition[] {
    return Object.values(tools).map((t) => t.definition);
  },

  getTool(name: string): Tool | null {
    return tools[name] || null;
  },
};

export default provider;
