"""
Snowflake MCP Tool Definitions

Defines MCP tools for Snowflake operations:
- Schema: list databases, schemas, tables
- Query: execute queries, get results
- Data: preview data, describe tables
"""

from mcp.types import Tool

SNOWFLAKE_TOOLS = [
    # Schema Exploration Tools
    Tool(
        name="list_databases",
        description="""List available Snowflake databases.

Returns database names with basic metadata.""",
        inputSchema={
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Optional LIKE pattern to filter databases",
                },
            },
        },
    ),
    Tool(
        name="list_schemas",
        description="""List schemas in a database.

Returns schema names with basic metadata.""",
        inputSchema={
            "type": "object",
            "properties": {
                "database": {
                    "type": "string",
                    "description": "Database name",
                },
                "pattern": {
                    "type": "string",
                    "description": "Optional LIKE pattern to filter schemas",
                },
            },
            "required": ["database"],
        },
    ),
    Tool(
        name="list_tables",
        description="""List tables and views in a schema.

Returns table/view names with type and row count.""",
        inputSchema={
            "type": "object",
            "properties": {
                "database": {
                    "type": "string",
                    "description": "Database name",
                },
                "schema": {
                    "type": "string",
                    "description": "Schema name",
                },
                "pattern": {
                    "type": "string",
                    "description": "Optional LIKE pattern to filter tables",
                },
                "include_views": {
                    "type": "boolean",
                    "description": "Include views in results",
                    "default": True,
                },
            },
            "required": ["database", "schema"],
        },
    ),
    Tool(
        name="describe_table",
        description="""Get table/view schema and column information.

Returns column names, types, nullable, and comments.""",
        inputSchema={
            "type": "object",
            "properties": {
                "database": {
                    "type": "string",
                    "description": "Database name",
                },
                "schema": {
                    "type": "string",
                    "description": "Schema name",
                },
                "table": {
                    "type": "string",
                    "description": "Table or view name",
                },
            },
            "required": ["database", "schema", "table"],
        },
    ),

    # Query Tools
    Tool(
        name="execute_query",
        description="""Execute a SQL query and return results.

IMPORTANT: Only SELECT queries are allowed for safety.
Results are limited to prevent memory issues.

Returns query results as structured data.""",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "SQL SELECT query to execute",
                },
                "database": {
                    "type": "string",
                    "description": "Database context (optional if in query)",
                },
                "schema": {
                    "type": "string",
                    "description": "Schema context (optional if in query)",
                },
                "max_rows": {
                    "type": "integer",
                    "description": "Maximum rows to return",
                    "default": 1000,
                },
            },
            "required": ["query"],
        },
    ),
    Tool(
        name="preview_table",
        description="""Preview data from a table (first N rows).

A quick way to see sample data without writing a query.""",
        inputSchema={
            "type": "object",
            "properties": {
                "database": {
                    "type": "string",
                    "description": "Database name",
                },
                "schema": {
                    "type": "string",
                    "description": "Schema name",
                },
                "table": {
                    "type": "string",
                    "description": "Table name",
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of rows to preview",
                    "default": 10,
                },
            },
            "required": ["database", "schema", "table"],
        },
    ),
    Tool(
        name="get_query_history",
        description="""Get recent query history for the user.

Returns recent queries with execution time and status.""",
        inputSchema={
            "type": "object",
            "properties": {
                "max_results": {
                    "type": "integer",
                    "description": "Maximum queries to return",
                    "default": 25,
                },
                "days": {
                    "type": "integer",
                    "description": "Look back this many days",
                    "default": 7,
                },
            },
        },
    ),

    # Utility Tools
    Tool(
        name="get_warehouse_status",
        description="""Get current warehouse status and usage.

Returns warehouse state, size, and recent usage statistics.""",
        inputSchema={
            "type": "object",
            "properties": {
                "warehouse": {
                    "type": "string",
                    "description": "Warehouse name (uses default if not specified)",
                },
            },
        },
    ),
    Tool(
        name="search_objects",
        description="""Search for database objects by name.

Searches across databases, schemas, tables, views, and columns.""",
        inputSchema={
            "type": "object",
            "properties": {
                "search_term": {
                    "type": "string",
                    "description": "Search term (supports wildcards)",
                },
                "object_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Object types to search (DATABASE, SCHEMA, TABLE, VIEW, COLUMN)",
                    "default": ["TABLE", "VIEW"],
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum results",
                    "default": 50,
                },
            },
            "required": ["search_term"],
        },
    ),
]
