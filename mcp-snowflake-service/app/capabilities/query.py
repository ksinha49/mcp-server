"""
Query Capability for Snowflake MCP Server

Handles query operations:
- Execute query
- Preview table
- Get query history
"""

import logging
import re
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)


class QueryCapability:
    """Query capability implementation."""

    def __init__(self, db_client):
        self.db = db_client

    async def execute_query(
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

        results = self.db.execute_query(query, database, schema, max_rows)

        return {
            "row_count": len(results),
            "columns": list(results[0].keys()) if results else [],
            "data": results,
            "truncated": len(results) >= max_rows,
        }

    async def preview_table(
        self,
        database: str,
        schema: str,
        table: str,
        limit: int = 10,
    ) -> Dict:
        """Preview data from a table."""
        query = f"SELECT * FROM {database}.{schema}.{table} LIMIT {limit}"
        results = self.db.execute_query(query, max_rows=limit)

        return {
            "database": database,
            "schema": schema,
            "table": table,
            "row_count": len(results),
            "columns": list(results[0].keys()) if results else [],
            "data": results,
        }

    async def get_query_history(
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
            results = self.db.execute_query(query, max_rows=max_results)
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
