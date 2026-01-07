/**
 * Outlook Provider
 *
 * Email, calendar, and contact management via Microsoft Graph API.
 */

import type { Provider, ToolDefinition, Tool, PythonBackend, ToolResult } from '../types.ts';

const tools: Record<string, Tool> = {
  search_emails: {
    definition: {
      name: 'search_emails',
      provider: 'outlook',
      description: 'Search emails in mailbox by query, folder, or date range',
      inputSchema: {
        type: 'object',
        properties: {
          query: { type: 'string', description: 'Search query (OData filter or keyword)' },
          folder: { type: 'string', description: 'Folder to search in', default: 'inbox' },
          max_results: { type: 'integer', description: 'Maximum results to return', default: 25 },
        },
      },
      outputSchema: {
        type: 'array',
        items: {
          type: 'object',
          properties: {
            id: { type: 'string' },
            subject: { type: 'string' },
            from: { type: 'string' },
            received: { type: 'string' },
            isRead: { type: 'boolean' },
          },
        },
      },
    },
    execute: async (backend: PythonBackend, input: Record<string, unknown>) => {
      return backend.callTool('outlook', 'search_emails', input);
    },
  },

  get_email: {
    definition: {
      name: 'get_email',
      provider: 'outlook',
      description: 'Get a specific email by ID with optional attachments',
      inputSchema: {
        type: 'object',
        properties: {
          email_id: { type: 'string', description: 'Email ID' },
          include_attachments: { type: 'boolean', description: 'Include attachment info', default: false },
        },
        required: ['email_id'],
      },
    },
    execute: async (backend: PythonBackend, input: Record<string, unknown>) => {
      return backend.callTool('outlook', 'get_email', input);
    },
  },

  send_email: {
    definition: {
      name: 'send_email',
      provider: 'outlook',
      description: 'Send an email to one or more recipients',
      inputSchema: {
        type: 'object',
        properties: {
          to: {
            type: 'array',
            items: { type: 'string' },
            description: 'Recipient email addresses',
          },
          subject: { type: 'string', description: 'Email subject' },
          body: { type: 'string', description: 'Email body content' },
          body_type: {
            type: 'string',
            enum: ['text', 'html'],
            description: 'Body content type',
            default: 'text',
          },
        },
        required: ['to', 'subject', 'body'],
      },
    },
    execute: async (backend: PythonBackend, input: Record<string, unknown>) => {
      return backend.callTool('outlook', 'send_email', input);
    },
  },

  list_calendar_events: {
    definition: {
      name: 'list_calendar_events',
      provider: 'outlook',
      description: 'List calendar events within a date range',
      inputSchema: {
        type: 'object',
        properties: {
          start_date: { type: 'string', description: 'Start date (ISO format)' },
          end_date: { type: 'string', description: 'End date (ISO format)' },
          max_results: { type: 'integer', description: 'Maximum results', default: 50 },
        },
      },
    },
    execute: async (backend: PythonBackend, input: Record<string, unknown>) => {
      return backend.callTool('outlook', 'list_calendar_events', input);
    },
  },

  create_calendar_event: {
    definition: {
      name: 'create_calendar_event',
      provider: 'outlook',
      description: 'Create a new calendar event',
      inputSchema: {
        type: 'object',
        properties: {
          subject: { type: 'string', description: 'Event subject' },
          start: { type: 'string', description: 'Start time (ISO format)' },
          end: { type: 'string', description: 'End time (ISO format)' },
          attendees: {
            type: 'array',
            items: { type: 'string' },
            description: 'Attendee email addresses',
          },
          is_online_meeting: { type: 'boolean', description: 'Create as Teams meeting', default: false },
        },
        required: ['subject', 'start', 'end'],
      },
    },
    execute: async (backend: PythonBackend, input: Record<string, unknown>) => {
      return backend.callTool('outlook', 'create_calendar_event', input);
    },
  },

  search_contacts: {
    definition: {
      name: 'search_contacts',
      provider: 'outlook',
      description: 'Search contacts by name or email',
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
      return backend.callTool('outlook', 'search_contacts', input);
    },
  },
};

export const provider: Provider = {
  name: 'outlook',
  description: 'Microsoft Outlook email, calendar, and contacts',

  listTools(): ToolDefinition[] {
    return Object.values(tools).map((t) => t.definition);
  },

  getTool(name: string): Tool | null {
    return tools[name] || null;
  },
};

export default provider;
