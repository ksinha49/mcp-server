/**
 * Common types for MCP Code Execution providers
 */

/**
 * JSON Schema type for tool input/output definitions
 */
export interface JsonSchema {
  type: string;
  properties?: Record<string, JsonSchema>;
  items?: JsonSchema;
  required?: string[];
  description?: string;
  default?: unknown;
  enum?: unknown[];
  minimum?: number;
  maximum?: number;
  minLength?: number;
  maxLength?: number;
  pattern?: string;
  additionalProperties?: boolean | JsonSchema;
}

/**
 * Tool definition with input/output schemas
 */
export interface ToolDefinition {
  name: string;
  provider: string;
  description: string;
  inputSchema: JsonSchema;
  outputSchema?: JsonSchema;
}

/**
 * Result of a tool execution
 */
export interface ToolResult<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
  metadata?: {
    executionTimeMs: number;
    cached: boolean;
  };
}

/**
 * Interface for calling Python backend tools
 */
export interface PythonBackend {
  callTool<T = unknown>(
    provider: string,
    tool: string,
    args: Record<string, unknown>
  ): Promise<ToolResult<T>>;
}

/**
 * Provider interface
 */
export interface Provider {
  name: string;
  description: string;
  listTools(): ToolDefinition[];
  getTool(name: string): Tool | null;
}

/**
 * Individual tool module interface
 */
export interface Tool {
  definition: ToolDefinition;
  execute: (
    backend: PythonBackend,
    input: Record<string, unknown>
  ) => Promise<ToolResult>;
}

/**
 * Execution context passed to code execution
 */
export interface ExecutionContext {
  tools: AvailableTools;
  stdlib: StandardLibrary;
  variables: Record<string, unknown>;
  timeout: number;
}

/**
 * Available tools organized by provider
 */
export interface AvailableTools {
  outlook: OutlookTools;
  sharepoint: SharePointTools;
  teams: TeamsTools;
  azuredevops: AzureDevOpsTools;
  snowflake: SnowflakeTools;
}

/**
 * Standard library utilities available in code execution
 */
export interface StandardLibrary {
  transform: TransformUtils;
  format: FormatUtils;
  validate: ValidateUtils;
}

/**
 * Transformation utilities
 */
export interface TransformUtils {
  filter<T>(arr: T[], predicate: (item: T) => boolean): T[];
  map<T, U>(arr: T[], mapper: (item: T) => U): U[];
  groupBy<T>(arr: T[], keyFn: (item: T) => string): Record<string, T[]>;
  sortBy<T>(arr: T[], keyFn: (item: T) => number | string, order?: 'asc' | 'desc'): T[];
  unique<T>(arr: T[], keyFn?: (item: T) => unknown): T[];
  flatten<T>(arr: T[][]): T[];
  chunk<T>(arr: T[], size: number): T[][];
  take<T>(arr: T[], n: number): T[];
  skip<T>(arr: T[], n: number): T[];
}

/**
 * Formatting utilities
 */
export interface FormatUtils {
  toJSON(data: unknown, pretty?: boolean): string;
  toCSV<T extends Record<string, unknown>>(data: T[], columns?: string[]): string;
  toMarkdownTable<T extends Record<string, unknown>>(data: T[], columns?: string[]): string;
  truncate(str: string, maxLength: number, suffix?: string): string;
  formatDate(date: Date | string, format?: string): string;
  formatNumber(num: number, options?: Intl.NumberFormatOptions): string;
}

/**
 * Validation utilities
 */
export interface ValidateUtils {
  isEmail(str: string): boolean;
  isURL(str: string): boolean;
  isDate(str: string): boolean;
  isNumeric(str: string): boolean;
  isEmpty(value: unknown): boolean;
  hasProperty<T extends object>(obj: T, key: string): boolean;
}

// Provider-specific tool interfaces

export interface OutlookTools {
  search_emails(input: {
    query?: string;
    folder?: string;
    max_results?: number;
  }): Promise<ToolResult<Email[]>>;
  get_email(input: {
    email_id: string;
    include_attachments?: boolean;
  }): Promise<ToolResult<Email>>;
  send_email(input: {
    to: string[];
    subject: string;
    body: string;
    body_type?: 'text' | 'html';
  }): Promise<ToolResult<{ id: string; sent: boolean }>>;
  list_calendar_events(input: {
    start_date?: string;
    end_date?: string;
    max_results?: number;
  }): Promise<ToolResult<CalendarEvent[]>>;
  create_calendar_event(input: {
    subject: string;
    start: string;
    end: string;
    attendees?: string[];
    is_online_meeting?: boolean;
  }): Promise<ToolResult<CalendarEvent>>;
  search_contacts(input: {
    query: string;
    max_results?: number;
  }): Promise<ToolResult<Contact[]>>;
}

export interface SharePointTools {
  list_sites(input: {
    search?: string;
    max_results?: number;
  }): Promise<ToolResult<Site[]>>;
  get_site(input: { site_id: string }): Promise<ToolResult<Site>>;
  search_documents(input: {
    query: string;
    max_results?: number;
  }): Promise<ToolResult<Document[]>>;
  list_folder_contents(input: {
    site_id: string;
    folder_path: string;
  }): Promise<ToolResult<FolderItem[]>>;
}

export interface TeamsTools {
  list_teams(input: { max_results?: number }): Promise<ToolResult<Team[]>>;
  list_channels(input: { team_id: string }): Promise<ToolResult<Channel[]>>;
  send_channel_message(input: {
    team_id: string;
    channel_id: string;
    content: string;
  }): Promise<ToolResult<{ id: string; sent: boolean }>>;
  list_chats(input: { max_results?: number }): Promise<ToolResult<Chat[]>>;
  create_meeting(input: {
    subject: string;
    start: string;
    end: string;
    attendees?: string[];
  }): Promise<ToolResult<Meeting>>;
}

export interface AzureDevOpsTools {
  list_projects(input: { max_results?: number }): Promise<ToolResult<Project[]>>;
  search_work_items(input: {
    project: string;
    query: string;
    max_results?: number;
  }): Promise<ToolResult<WorkItem[]>>;
  get_work_item(input: { work_item_id: number }): Promise<ToolResult<WorkItem>>;
  list_repos(input: { project: string }): Promise<ToolResult<Repository[]>>;
  list_pipelines(input: { project: string }): Promise<ToolResult<Pipeline[]>>;
  list_pull_requests(input: {
    project: string;
    repo: string;
    status?: string;
  }): Promise<ToolResult<PullRequest[]>>;
}

export interface SnowflakeTools {
  list_databases(input: { pattern?: string }): Promise<ToolResult<Database[]>>;
  list_schemas(input: { database: string }): Promise<ToolResult<Schema[]>>;
  list_tables(input: {
    database: string;
    schema: string;
  }): Promise<ToolResult<Table[]>>;
  describe_table(input: {
    database: string;
    schema: string;
    table: string;
  }): Promise<ToolResult<TableDescription>>;
  execute_query(input: {
    query: string;
    max_rows?: number;
  }): Promise<ToolResult<QueryResult>>;
  preview_table(input: {
    database: string;
    schema: string;
    table: string;
    limit?: number;
  }): Promise<ToolResult<QueryResult>>;
}

// Data types

export interface Email {
  id: string;
  subject: string;
  from: string;
  to: string[];
  received: string;
  body?: string;
  isRead: boolean;
  hasAttachments: boolean;
}

export interface CalendarEvent {
  id: string;
  subject: string;
  start: string;
  end: string;
  location?: string;
  attendees: string[];
  isOnlineMeeting: boolean;
  onlineJoinUrl?: string;
}

export interface Contact {
  id: string;
  displayName: string;
  email: string;
  phone?: string;
  company?: string;
}

export interface Site {
  id: string;
  name: string;
  url: string;
  description?: string;
}

export interface Document {
  id: string;
  name: string;
  path: string;
  size: number;
  modified: string;
  modifiedBy: string;
}

export interface FolderItem {
  id: string;
  name: string;
  type: 'file' | 'folder';
  size?: number;
  modified: string;
}

export interface Team {
  id: string;
  displayName: string;
  description?: string;
}

export interface Channel {
  id: string;
  displayName: string;
  description?: string;
}

export interface Chat {
  id: string;
  topic?: string;
  chatType: string;
  lastUpdated: string;
}

export interface Meeting {
  id: string;
  subject: string;
  start: string;
  end: string;
  joinUrl: string;
}

export interface Project {
  id: string;
  name: string;
  description?: string;
  state: string;
}

export interface WorkItem {
  id: number;
  title: string;
  type: string;
  state: string;
  assignedTo?: string;
  createdDate: string;
}

export interface Repository {
  id: string;
  name: string;
  url: string;
  defaultBranch: string;
}

export interface Pipeline {
  id: number;
  name: string;
  folder: string;
}

export interface PullRequest {
  id: number;
  title: string;
  status: string;
  createdBy: string;
  createdDate: string;
  sourceRefName: string;
  targetRefName: string;
}

export interface Database {
  name: string;
  owner: string;
  created: string;
}

export interface Schema {
  name: string;
  owner: string;
}

export interface Table {
  name: string;
  kind: string;
  rows: number;
}

export interface TableDescription {
  columns: Column[];
  primaryKey?: string[];
}

export interface Column {
  name: string;
  type: string;
  nullable: boolean;
  default?: string;
}

export interface QueryResult {
  columns: string[];
  data: Record<string, unknown>[];
  rowCount: number;
}
