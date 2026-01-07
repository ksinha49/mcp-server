"""
Schema Capability for Snowflake MCP Server

Handles schema exploration operations:
- List databases
- List schemas
- List tables
- Describe table
"""

import logging
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)


class SchemaCapability:
    """Schema capability implementation."""

    def __init__(self, db_client):
        self.db = db_client

    async def list_databases(self, pattern: Optional[str] = None) -> List[Dict]:
        """List available databases."""
        query = "SHOW DATABASES"
        if pattern:
            query += f" LIKE '{pattern}'"

        results = self.db.execute_query(query)
        return [
            {
                "name": row.get("name"),
                "owner": row.get("owner"),
                "comment": row.get("comment", ""),
                "created": str(row.get("created_on", "")),
            }
            for row in results
        ]

    async def list_schemas(
        self,
        database: str,
        pattern: Optional[str] = None,
    ) -> List[Dict]:
        """List schemas in a database."""
        query = f"SHOW SCHEMAS IN DATABASE {database}"
        if pattern:
            query += f" LIKE '{pattern}'"

        results = self.db.execute_query(query)
        return [
            {
                "name": row.get("name"),
                "owner": row.get("owner"),
                "comment": row.get("comment", ""),
                "created": str(row.get("created_on", "")),
            }
            for row in results
        ]

    async def list_tables(
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
        tables = self.db.execute_query(query)
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
            views = self.db.execute_query(query)
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

    async def describe_table(
        self,
        database: str,
        schema: str,
        table: str,
    ) -> Dict:
        """Get table schema information."""
        columns = self.db.execute_query(f"DESCRIBE TABLE {database}.{schema}.{table}")

        # Get table comment and row count
        try:
            info_query = f"""
                SELECT ROW_COUNT, COMMENT
                FROM {database}.INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = '{schema}' AND TABLE_NAME = '{table}'
            """
            info = self.db.execute_query(info_query, max_rows=1)
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
