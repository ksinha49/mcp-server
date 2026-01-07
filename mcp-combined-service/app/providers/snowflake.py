"""
Snowflake Provider for Combined Service

Simplified Snowflake provider for combined deployment.
"""

import logging
import re
from typing import Any, Dict, List, Optional

import snowflake.connector
from snowflake.connector import DictCursor
from mcp.types import Tool

log = logging.getLogger(__name__)

SNOWFLAKE_TOOLS = [
    Tool(
        name="list_databases",
        description="List available Snowflake databases.",
        inputSchema={
            "type": "object",
            "properties": {"pattern": {"type": "string"}},
        },
    ),
    Tool(
        name="list_schemas",
        description="List schemas in a database.",
        inputSchema={
            "type": "object",
            "properties": {"database": {"type": "string"}},
            "required": ["database"],
        },
    ),
    Tool(
        name="list_tables",
        description="List tables and views in a schema.",
        inputSchema={
            "type": "object",
            "properties": {
                "database": {"type": "string"},
                "schema": {"type": "string"},
            },
            "required": ["database", "schema"],
        },
    ),
    Tool(
        name="describe_table",
        description="Get table schema and column information.",
        inputSchema={
            "type": "object",
            "properties": {
                "database": {"type": "string"},
                "schema": {"type": "string"},
                "table": {"type": "string"},
            },
            "required": ["database", "schema", "table"],
        },
    ),
    Tool(
        name="execute_query",
        description="Execute a SQL SELECT query and return results.",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "max_rows": {"type": "integer", "default": 1000},
            },
            "required": ["query"],
        },
    ),
    Tool(
        name="preview_table",
        description="Preview data from a table (first N rows).",
        inputSchema={
            "type": "object",
            "properties": {
                "database": {"type": "string"},
                "schema": {"type": "string"},
                "table": {"type": "string"},
                "limit": {"type": "integer", "default": 10},
            },
            "required": ["database", "schema", "table"],
        },
    ),
]


class SnowflakeProvider:
    """Snowflake provider implementation."""

    def __init__(self, account: str, warehouse: str, database: Optional[str] = None, schema: Optional[str] = None,
                 role: Optional[str] = None, user: Optional[str] = None, password: Optional[str] = None,
                 private_key_path: Optional[str] = None, private_key_passphrase: Optional[str] = None,
                 oauth_access_token: Optional[str] = None):
        self.account = account
        self.warehouse = warehouse
        self.database = database
        self.schema = schema
        self.role = role
        self.user = user
        self.password = password
        self.private_key_path = private_key_path
        self.private_key_passphrase = private_key_passphrase
        self.oauth_access_token = oauth_access_token
        self._connection = None

    def _get_connection(self):
        if self._connection and not self._connection.is_closed():
            return self._connection
        conn_params = {"account": self.account, "warehouse": self.warehouse}
        if self.database:
            conn_params["database"] = self.database
        if self.schema:
            conn_params["schema"] = self.schema
        if self.role:
            conn_params["role"] = self.role
        if self.oauth_access_token:
            conn_params["authenticator"] = "oauth"
            conn_params["token"] = self.oauth_access_token
        elif self.private_key_path:
            conn_params["user"] = self.user
            conn_params["private_key_file"] = self.private_key_path
            if self.private_key_passphrase:
                conn_params["private_key_file_pwd"] = self.private_key_passphrase
        elif self.password:
            conn_params["user"] = self.user
            conn_params["password"] = self.password
        else:
            raise ValueError("No authentication method configured")
        self._connection = snowflake.connector.connect(**conn_params)
        return self._connection

    def _execute_query(self, query: str, max_rows: int = 1000) -> List[Dict]:
        conn = self._get_connection()
        cursor = conn.cursor(DictCursor)
        try:
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchmany(max_rows)]
        finally:
            cursor.close()

    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        handlers = {
            "list_databases": self._list_databases,
            "list_schemas": self._list_schemas,
            "list_tables": self._list_tables,
            "describe_table": self._describe_table,
            "execute_query": self._execute_query_tool,
            "preview_table": self._preview_table,
        }
        handler = handlers.get(name)
        if not handler:
            raise ValueError(f"Unknown tool: {name}")
        return await handler(**arguments)

    async def _list_databases(self, pattern: Optional[str] = None, **kwargs) -> List[Dict]:
        query = "SHOW DATABASES"
        if pattern:
            query += f" LIKE '{pattern}'"
        results = self._execute_query(query)
        return [{"name": r.get("name"), "owner": r.get("owner")} for r in results]

    async def _list_schemas(self, database: str, **kwargs) -> List[Dict]:
        results = self._execute_query(f"SHOW SCHEMAS IN DATABASE {database}")
        return [{"name": r.get("name"), "owner": r.get("owner")} for r in results]

    async def _list_tables(self, database: str, schema: str, **kwargs) -> List[Dict]:
        results = self._execute_query(f"SHOW TABLES IN {database}.{schema}")
        return [{"name": r.get("name"), "rows": r.get("rows")} for r in results]

    async def _describe_table(self, database: str, schema: str, table: str, **kwargs) -> Dict:
        columns = self._execute_query(f"DESCRIBE TABLE {database}.{schema}.{table}")
        return {"database": database, "schema": schema, "table": table, "columns": [{"name": c.get("name"), "type": c.get("type")} for c in columns]}

    async def _execute_query_tool(self, query: str, max_rows: int = 1000, **kwargs) -> Dict:
        query_upper = query.strip().upper()
        if not query_upper.startswith("SELECT") and not query_upper.startswith("WITH"):
            raise ValueError("Only SELECT queries are allowed for safety.")
        dangerous = [r'\bDROP\b', r'\bDELETE\b', r'\bUPDATE\b', r'\bINSERT\b', r'\bTRUNCATE\b', r'\bALTER\b', r'\bCREATE\b']
        for p in dangerous:
            if re.search(p, query_upper):
                raise ValueError(f"Query contains forbidden keyword")
        results = self._execute_query(query, max_rows)
        return {"row_count": len(results), "columns": list(results[0].keys()) if results else [], "data": results}

    async def _preview_table(self, database: str, schema: str, table: str, limit: int = 10, **kwargs) -> Dict:
        results = self._execute_query(f"SELECT * FROM {database}.{schema}.{table} LIMIT {limit}", limit)
        return {"table": f"{database}.{schema}.{table}", "row_count": len(results), "data": results}

    def close(self):
        if self._connection and not self._connection.is_closed():
            self._connection.close()
