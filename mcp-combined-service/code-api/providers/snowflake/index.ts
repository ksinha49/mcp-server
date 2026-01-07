/**
 * Snowflake Provider
 *
 * Data warehouse queries, schema exploration, and data preview.
 */

import type { Provider, ToolDefinition, Tool, PythonBackend } from '../types.ts';

const tools: Record<string, Tool> = {
  list_databases: {
    definition: {
      name: 'list_databases',
      provider: 'snowflake',
      description: 'List all accessible databases',
      inputSchema: {
        type: 'object',
        properties: {
          pattern: { type: 'string', description: 'Filter pattern (SQL LIKE syntax)' },
        },
      },
      outputSchema: {
        type: 'array',
        items: {
          type: 'object',
          properties: {
            name: { type: 'string' },
            owner: { type: 'string' },
            created: { type: 'string' },
          },
        },
      },
    },
    execute: async (backend: PythonBackend, input: Record<string, unknown>) => {
      return backend.callTool('snowflake', 'list_databases', input);
    },
  },

  list_schemas: {
    definition: {
      name: 'list_schemas',
      provider: 'snowflake',
      description: 'List schemas in a database',
      inputSchema: {
        type: 'object',
        properties: {
          database: { type: 'string', description: 'Database name' },
        },
        required: ['database'],
      },
    },
    execute: async (backend: PythonBackend, input: Record<string, unknown>) => {
      return backend.callTool('snowflake', 'list_schemas', input);
    },
  },

  list_tables: {
    definition: {
      name: 'list_tables',
      provider: 'snowflake',
      description: 'List tables in a schema',
      inputSchema: {
        type: 'object',
        properties: {
          database: { type: 'string', description: 'Database name' },
          schema: { type: 'string', description: 'Schema name' },
        },
        required: ['database', 'schema'],
      },
    },
    execute: async (backend: PythonBackend, input: Record<string, unknown>) => {
      return backend.callTool('snowflake', 'list_tables', input);
    },
  },

  describe_table: {
    definition: {
      name: 'describe_table',
      provider: 'snowflake',
      description: 'Get table structure and column definitions',
      inputSchema: {
        type: 'object',
        properties: {
          database: { type: 'string', description: 'Database name' },
          schema: { type: 'string', description: 'Schema name' },
          table: { type: 'string', description: 'Table name' },
        },
        required: ['database', 'schema', 'table'],
      },
      outputSchema: {
        type: 'object',
        properties: {
          columns: {
            type: 'array',
            items: {
              type: 'object',
              properties: {
                name: { type: 'string' },
                type: { type: 'string' },
                nullable: { type: 'boolean' },
              },
            },
          },
        },
      },
    },
    execute: async (backend: PythonBackend, input: Record<string, unknown>) => {
      return backend.callTool('snowflake', 'describe_table', input);
    },
  },

  execute_query: {
    definition: {
      name: 'execute_query',
      provider: 'snowflake',
      description: 'Execute a SELECT query (read-only)',
      inputSchema: {
        type: 'object',
        properties: {
          query: { type: 'string', description: 'SQL query (SELECT/WITH only)' },
          max_rows: { type: 'integer', description: 'Maximum rows to return', default: 1000 },
        },
        required: ['query'],
      },
      outputSchema: {
        type: 'object',
        properties: {
          columns: { type: 'array', items: { type: 'string' } },
          data: { type: 'array', items: { type: 'object' } },
          rowCount: { type: 'integer' },
        },
      },
    },
    execute: async (backend: PythonBackend, input: Record<string, unknown>) => {
      return backend.callTool('snowflake', 'execute_query', input);
    },
  },

  preview_table: {
    definition: {
      name: 'preview_table',
      provider: 'snowflake',
      description: 'Preview first N rows of a table',
      inputSchema: {
        type: 'object',
        properties: {
          database: { type: 'string', description: 'Database name' },
          schema: { type: 'string', description: 'Schema name' },
          table: { type: 'string', description: 'Table name' },
          limit: { type: 'integer', description: 'Number of rows', default: 100 },
        },
        required: ['database', 'schema', 'table'],
      },
    },
    execute: async (backend: PythonBackend, input: Record<string, unknown>) => {
      return backend.callTool('snowflake', 'preview_table', input);
    },
  },
};

export const provider: Provider = {
  name: 'snowflake',
  description: 'Snowflake data warehouse queries and exploration',

  listTools(): ToolDefinition[] {
    return Object.values(tools).map((t) => t.definition);
  },

  getTool(name: string): Tool | null {
    return tools[name] || null;
  },
};

export default provider;
