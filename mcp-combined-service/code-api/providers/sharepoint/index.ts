/**
 * SharePoint Provider
 *
 * Document and site management via Microsoft Graph API.
 */

import type { Provider, ToolDefinition, Tool, PythonBackend } from '../types.ts';

const tools: Record<string, Tool> = {
  list_sites: {
    definition: {
      name: 'list_sites',
      provider: 'sharepoint',
      description: 'List accessible SharePoint sites',
      inputSchema: {
        type: 'object',
        properties: {
          search: { type: 'string', description: 'Search query' },
          max_results: { type: 'integer', description: 'Maximum results', default: 25 },
        },
      },
    },
    execute: async (backend: PythonBackend, input: Record<string, unknown>) => {
      return backend.callTool('sharepoint', 'list_sites', input);
    },
  },

  get_site: {
    definition: {
      name: 'get_site',
      provider: 'sharepoint',
      description: 'Get site details by ID',
      inputSchema: {
        type: 'object',
        properties: {
          site_id: { type: 'string', description: 'Site ID' },
        },
        required: ['site_id'],
      },
    },
    execute: async (backend: PythonBackend, input: Record<string, unknown>) => {
      return backend.callTool('sharepoint', 'get_site', input);
    },
  },

  search_documents: {
    definition: {
      name: 'search_documents',
      provider: 'sharepoint',
      description: 'Search documents across SharePoint',
      inputSchema: {
        type: 'object',
        properties: {
          query: { type: 'string', description: 'Search query' },
          max_results: { type: 'integer', description: 'Maximum results', default: 25 },
        },
        required: ['query'],
      },
    },
    execute: async (backend: PythonBackend, input: Record<string, unknown>) => {
      return backend.callTool('sharepoint', 'search_documents', input);
    },
  },

  list_folder_contents: {
    definition: {
      name: 'list_folder_contents',
      provider: 'sharepoint',
      description: 'List contents of a folder',
      inputSchema: {
        type: 'object',
        properties: {
          site_id: { type: 'string', description: 'Site ID' },
          folder_path: { type: 'string', description: 'Folder path' },
        },
        required: ['site_id', 'folder_path'],
      },
    },
    execute: async (backend: PythonBackend, input: Record<string, unknown>) => {
      return backend.callTool('sharepoint', 'list_folder_contents', input);
    },
  },
};

export const provider: Provider = {
  name: 'sharepoint',
  description: 'Microsoft SharePoint sites and documents',

  listTools(): ToolDefinition[] {
    return Object.values(tools).map((t) => t.definition);
  },

  getTool(name: string): Tool | null {
    return tools[name] || null;
  },
};

export default provider;
