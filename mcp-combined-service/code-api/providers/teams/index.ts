/**
 * Teams Provider
 *
 * Chat, channels, and meeting management via Microsoft Graph API.
 */

import type { Provider, ToolDefinition, Tool, PythonBackend } from '../types.ts';

const tools: Record<string, Tool> = {
  list_teams: {
    definition: {
      name: 'list_teams',
      provider: 'teams',
      description: 'List accessible Teams',
      inputSchema: {
        type: 'object',
        properties: {
          max_results: { type: 'integer', description: 'Maximum results', default: 25 },
        },
      },
    },
    execute: async (backend: PythonBackend, input: Record<string, unknown>) => {
      return backend.callTool('teams', 'list_teams', input);
    },
  },

  list_channels: {
    definition: {
      name: 'list_channels',
      provider: 'teams',
      description: 'List channels in a team',
      inputSchema: {
        type: 'object',
        properties: {
          team_id: { type: 'string', description: 'Team ID' },
        },
        required: ['team_id'],
      },
    },
    execute: async (backend: PythonBackend, input: Record<string, unknown>) => {
      return backend.callTool('teams', 'list_channels', input);
    },
  },

  send_channel_message: {
    definition: {
      name: 'send_channel_message',
      provider: 'teams',
      description: 'Send a message to a channel',
      inputSchema: {
        type: 'object',
        properties: {
          team_id: { type: 'string', description: 'Team ID' },
          channel_id: { type: 'string', description: 'Channel ID' },
          content: { type: 'string', description: 'Message content' },
        },
        required: ['team_id', 'channel_id', 'content'],
      },
    },
    execute: async (backend: PythonBackend, input: Record<string, unknown>) => {
      return backend.callTool('teams', 'send_channel_message', input);
    },
  },

  list_chats: {
    definition: {
      name: 'list_chats',
      provider: 'teams',
      description: 'List chat conversations',
      inputSchema: {
        type: 'object',
        properties: {
          max_results: { type: 'integer', description: 'Maximum results', default: 25 },
        },
      },
    },
    execute: async (backend: PythonBackend, input: Record<string, unknown>) => {
      return backend.callTool('teams', 'list_chats', input);
    },
  },

  create_meeting: {
    definition: {
      name: 'create_meeting',
      provider: 'teams',
      description: 'Create an online meeting',
      inputSchema: {
        type: 'object',
        properties: {
          subject: { type: 'string', description: 'Meeting subject' },
          start: { type: 'string', description: 'Start time (ISO format)' },
          end: { type: 'string', description: 'End time (ISO format)' },
          attendees: {
            type: 'array',
            items: { type: 'string' },
            description: 'Attendee emails',
          },
        },
        required: ['subject', 'start', 'end'],
      },
    },
    execute: async (backend: PythonBackend, input: Record<string, unknown>) => {
      return backend.callTool('teams', 'create_meeting', input);
    },
  },
};

export const provider: Provider = {
  name: 'teams',
  description: 'Microsoft Teams chat, channels, and meetings',

  listTools(): ToolDefinition[] {
    return Object.values(tools).map((t) => t.definition);
  },

  getTool(name: string): Tool | null {
    return tools[name] || null;
  },
};

export default provider;
