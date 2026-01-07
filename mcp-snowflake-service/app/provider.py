"""
Snowflake MCP Provider

Implements Snowflake operations:
- Schema exploration (databases, schemas, tables)
- Query execution (SELECT only for safety)
- Data preview
- Warehouse management

Supports OAuth, key-pair, and username/password authentication.
"""

import logging
import re
from typing import Any, Dict, List, Optional

import snowflake.connector
from snowflake.connector import DictCursor

log = logging.getLogger(__name__)


class SnowflakeProvider:
    """
    Snowflake MCP Provider.

    Implements tool execution using Snowflake Python connector.
    Supports multiple authentication methods.
    """

    def __init__(
        self,
        account: str,
        warehouse: str,
        database: Optional[str] = None,
        schema: Optional[str] = None,
        role: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        private_key_path: Optional[str] = None,
        private_key_passphrase: Optional[str] = None,
        oauth_access_token: Optional[str] = None,
    ):
        """
        Initialize Snowflake provider.

        Args:
            account: Snowflake account identifier
            warehouse: Default warehouse to use
            database: Default database (optional)
            schema: Default schema (optional)
            role: Role to use (optional)
            user: Username (for password or key-pair auth)
            password: Password (for password auth)
            private_key_path: Path to private key file (for key-pair auth)
            private_key_passphrase: Passphrase for private key
            oauth_access_token: OAuth access token (takes precedence)
        """
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
        """Get or create Snowflake connection."""
        if self._connection and not self._connection.is_closed():
            return self._connection

        conn_params = {
            "account": self.account,
            "warehouse": self.warehouse,
        }

        if self.database:
            conn_params["database"] = self.database
        if self.schema:
            conn_params["schema"] = self.schema
        if self.role:
            conn_params["role"] = self.role

        # Authentication method priority: OAuth > Key-pair > Password
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

    def _execute_query(
        self,
        query: str,
        database: Optional[str] = None,
        schema: Optional[str] = None,
        max_rows: int = 1000,
    ) -> List[Dict]:
        """Execute a query and return results."""
        conn = self._get_connection()

        # Set context if provided
        if database:
            conn.cursor().execute(f"USE DATABASE {database}")
        if schema:
            conn.cursor().execute(f"USE SCHEMA {schema}")

        cursor = conn.cursor(DictCursor)
        try:
            cursor.execute(query)
            results = cursor.fetchmany(max_rows)
            return [dict(row) for row in results]
        finally:
            cursor.close()

    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool by name."""
        tool_handlers = {
            "list_databases": self._list_databases,
            "list_schemas": self._list_schemas,
            "list_tables": self._list_tables,
            "describe_table": self._describe_table,
            "execute_query": self._execute_query_tool,
            "preview_table": self._preview_table,
            "get_query_history": self._get_query_history,
            "get_warehouse_status": self._get_warehouse_status,
            "search_objects": self._search_objects,
        }

        handler = tool_handlers.get(name)
        if not handler:
            raise ValueError(f"Unknown tool: {name}")

        return await handler(**arguments)

    async def _list_databases(self, pattern: Optional[str] = None) -> List[Dict]:
        """List available databases."""
        query = "SHOW DATABASES"
        if pattern:
            query += f" LIKE '{pattern}'"

        results = self._execute_query(query)
        return [
            {
                "name": row.get("name"),
                "owner": row.get("owner"),
                "comment": row.get("comment", ""),
                "created": str(row.get("created_on", "")),
            }
            for row in results
        ]

    async def _list_schemas(
        self,
        database: str,
        pattern: Optional[str] = None,
    ) -> List[Dict]:
        """List schemas in a database."""
        query = f"SHOW SCHEMAS IN DATABASE {database}"
        if pattern:
            query += f" LIKE '{pattern}'"

        results = self._execute_query(query)
        return [
            {
                "name": row.get("name"),
                "owner": row.get("owner"),
                "comment": row.get("comment", ""),
                "created": str(row.get("created_on", "")),
            }
            for row in results
        ]

    async def _list_tables(
        self,
        database: str,
        schema: str,
        pattern: Optional[str] = None,
        include_views: bool = True,
    ) -> List[Dict]:
        """List tables and views in a schema."""
        results = []

        # Get tables
        query = f"SHOW TABLES IN {database}.{schema}"
        if pattern:
            query += f" LIKE '{pattern}'"
        tables = self._execute_query(query)
        results.extend([
            {
                "name": row.get("name"),
                "type": "TABLE",
                "rows": row.get("rows"),
                "owner": row.get("owner"),
                "comment": row.get("comment", ""),
            }
            for row in tables
        ])

        # Get views if requested
        if include_views:
            query = f"SHOW VIEWS IN {database}.{schema}"
            if pattern:
                query += f" LIKE '{pattern}'"
            views = self._execute_query(query)
            results.extend([
                {
                    "name": row.get("name"),
                    "type": "VIEW",
                    "owner": row.get("owner"),
                    "comment": row.get("comment", ""),
                }
                for row in views
            ])

        return results

    async def _describe_table(
        self,
        database: str,
        schema: str,
        table: str,
    ) -> Dict:
        """Get table schema information."""
        # Get column information
        query = f"DESCRIBE TABLE {database}.{schema}.{table}"
        columns = self._execute_query(query)

        # Get table comment and row count
        try:
            info_query = f"""
                SELECT ROW_COUNT, COMMENT
                FROM {database}.INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = '{schema}' AND TABLE_NAME = '{table}'
            """
            info = self._execute_query(info_query, max_rows=1)
            row_count = info[0].get("ROW_COUNT") if info else None
            comment = info[0].get("COMMENT") if info else None
        except Exception:
            row_count = None
            comment = None

        return {
            "database": database,
            "schema": schema,
            "table": table,
            "row_count": row_count,
            "comment": comment,
            "columns": [
                {
                    "name": col.get("name"),
                    "type": col.get("type"),
                    "nullable": col.get("null?") == "Y",
                    "default": col.get("default"),
                    "comment": col.get("comment", ""),
                }
                for col in columns
            ],
        }

    async def _execute_query_tool(
        self,
        query: str,
        database: Optional[str] = None,
        schema: Optional[str] = None,
        max_rows: int = 1000,
    ) -> Dict:
        """Execute a SQL query (SELECT only)."""
        # Safety check: only allow SELECT queries
        query_stripped = query.strip().upper()
        if not query_stripped.startswith("SELECT") and not query_stripped.startswith("WITH"):
            raise ValueError("Only SELECT queries are allowed for safety. Use WITH...SELECT for CTEs.")

        # Disallow dangerous patterns
        dangerous_patterns = [
            r'\bDROP\b', r'\bDELETE\b', r'\bUPDATE\b', r'\bINSERT\b',
            r'\bTRUNCATE\b', r'\bALTER\b', r'\bCREATE\b', r'\bGRANT\b',
            r'\bREVOKE\b', r'\bEXECUTE\b',
        ]
        for pattern in dangerous_patterns:
            if re.search(pattern, query_stripped):
                raise ValueError(f"Query contains forbidden keyword: {pattern}")

        results = self._execute_query(query, database, schema, max_rows)

        return {
            "row_count": len(results),
            "columns": list(results[0].keys()) if results else [],
            "data": results,
            "truncated": len(results) >= max_rows,
        }

    async def _preview_table(
        self,
        database: str,
        schema: str,
        table: str,
        limit: int = 10,
    ) -> Dict:
        """Preview data from a table."""
        query = f"SELECT * FROM {database}.{schema}.{table} LIMIT {limit}"
        results = self._execute_query(query, max_rows=limit)

        return {
            "database": database,
            "schema": schema,
            "table": table,
            "row_count": len(results),
            "columns": list(results[0].keys()) if results else [],
            "data": results,
        }

    async def _get_query_history(
        self,
        max_results: int = 25,
        days: int = 7,
    ) -> List[Dict]:
        """Get recent query history."""
        query = f"""
            SELECT
                QUERY_ID,
                QUERY_TEXT,
                DATABASE_NAME,
                SCHEMA_NAME,
                QUERY_TYPE,
                EXECUTION_STATUS,
                TOTAL_ELAPSED_TIME,
                ROWS_PRODUCED,
                START_TIME
            FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY(
                DATEADD('days', -{days}, CURRENT_TIMESTAMP()),
                CURRENT_TIMESTAMP(),
                RESULT_LIMIT => {max_results}
            ))
            ORDER BY START_TIME DESC
        """

        try:
            results = self._execute_query(query, max_rows=max_results)
            return [
                {
                    "query_id": row.get("QUERY_ID"),
                    "query_text": row.get("QUERY_TEXT", "")[:500],
                    "database": row.get("DATABASE_NAME"),
                    "schema": row.get("SCHEMA_NAME"),
                    "query_type": row.get("QUERY_TYPE"),
                    "status": row.get("EXECUTION_STATUS"),
                    "elapsed_time_ms": row.get("TOTAL_ELAPSED_TIME"),
                    "rows_produced": row.get("ROWS_PRODUCED"),
                    "start_time": str(row.get("START_TIME", "")),
                }
                for row in results
            ]
        except Exception as e:
            log.warning("Failed to get query history: %s", e)
            return []

    async def _get_warehouse_status(
        self,
        warehouse: Optional[str] = None,
    ) -> Dict:
        """Get warehouse status."""
        wh = warehouse or self.warehouse

        query = f"SHOW WAREHOUSES LIKE '{wh}'"
        results = self._execute_query(query, max_rows=1)

        if not results:
            return {"error": f"Warehouse '{wh}' not found"}

        wh_info = results[0]
        return {
            "name": wh_info.get("name"),
            "state": wh_info.get("state"),
            "size": wh_info.get("size"),
            "running": wh_info.get("running"),
            "queued": wh_info.get("queued"),
            "auto_suspend": wh_info.get("auto_suspend"),
            "auto_resume": wh_info.get("auto_resume"),
            "owner": wh_info.get("owner"),
        }

    async def _search_objects(
        self,
        search_term: str,
        object_types: Optional[List[str]] = None,
        max_results: int = 50,
    ) -> List[Dict]:
        """Search for database objects by name."""
        if object_types is None:
            object_types = ["TABLE", "VIEW"]

        results = []

        # Convert search term to LIKE pattern
        pattern = f"%{search_term}%"

        for obj_type in object_types:
            if obj_type.upper() == "DATABASE":
                query = f"SHOW DATABASES LIKE '{pattern}'"
                objs = self._execute_query(query, max_rows=max_results)
                results.extend([
                    {"type": "DATABASE", "name": o.get("name")}
                    for o in objs
                ])
            elif obj_type.upper() == "SCHEMA":
                # Search across databases (limited)
                query = f"""
                    SELECT CATALOG_NAME, SCHEMA_NAME
                    FROM INFORMATION_SCHEMA.SCHEMATA
                    WHERE SCHEMA_NAME ILIKE '{pattern}'
                    LIMIT {max_results}
                """
                try:
                    objs = self._execute_query(query)
                    results.extend([
                        {
                            "type": "SCHEMA",
                            "database": o.get("CATALOG_NAME"),
                            "name": o.get("SCHEMA_NAME"),
                        }
                        for o in objs
                    ])
                except Exception:
                    pass
            elif obj_type.upper() in ("TABLE", "VIEW"):
                query = f"""
                    SELECT TABLE_CATALOG, TABLE_SCHEMA, TABLE_NAME, TABLE_TYPE
                    FROM INFORMATION_SCHEMA.TABLES
                    WHERE TABLE_NAME ILIKE '{pattern}'
                    AND TABLE_TYPE = '{obj_type.upper()}'
                    LIMIT {max_results}
                """
                try:
                    objs = self._execute_query(query)
                    results.extend([
                        {
                            "type": o.get("TABLE_TYPE"),
                            "database": o.get("TABLE_CATALOG"),
                            "schema": o.get("TABLE_SCHEMA"),
                            "name": o.get("TABLE_NAME"),
                        }
                        for o in objs
                    ])
                except Exception:
                    pass
            elif obj_type.upper() == "COLUMN":
                query = f"""
                    SELECT TABLE_CATALOG, TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME, DATA_TYPE
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE COLUMN_NAME ILIKE '{pattern}'
                    LIMIT {max_results}
                """
                try:
                    objs = self._execute_query(query)
                    results.extend([
                        {
                            "type": "COLUMN",
                            "database": o.get("TABLE_CATALOG"),
                            "schema": o.get("TABLE_SCHEMA"),
                            "table": o.get("TABLE_NAME"),
                            "name": o.get("COLUMN_NAME"),
                            "data_type": o.get("DATA_TYPE"),
                        }
                        for o in objs
                    ])
                except Exception:
                    pass

        return results[:max_results]

    def close(self):
        """Close the connection."""
        if self._connection and not self._connection.is_closed():
            self._connection.close()
