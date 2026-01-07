"""
Utility Capability for Snowflake MCP Server

Handles utility operations:
- Get warehouse status
- Search objects
"""

import logging
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)


class UtilityCapability:
    """Utility capability implementation."""

    def __init__(self, db_client, default_warehouse: str):
        self.db = db_client
        self.default_warehouse = default_warehouse

    async def get_warehouse_status(
        self,
        warehouse: Optional[str] = None,
    ) -> Dict:
        """Get warehouse status."""
        wh = warehouse or self.default_warehouse

        query = f"SHOW WAREHOUSES LIKE '{wh}'"
        results = self.db.execute_query(query, max_rows=1)

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

    async def search_objects(
        self,
        search_term: str,
        object_types: Optional[List[str]] = None,
        max_results: int = 50,
    ) -> List[Dict]:
        """Search for database objects by name."""
        if object_types is None:
            object_types = ["TABLE", "VIEW"]

        results = []
        pattern = f"%{search_term}%"

        for obj_type in object_types:
            if obj_type.upper() == "DATABASE":
                query = f"SHOW DATABASES LIKE '{pattern}'"
                objs = self.db.execute_query(query, max_rows=max_results)
                results.extend([
                    {"type": "DATABASE", "name": o.get("name")}
                    for o in objs
                ])
            elif obj_type.upper() == "SCHEMA":
                query = f"""
                    SELECT CATALOG_NAME, SCHEMA_NAME
                    FROM INFORMATION_SCHEMA.SCHEMATA
                    WHERE SCHEMA_NAME ILIKE '{pattern}'
                    LIMIT {max_results}
                """
                try:
                    objs = self.db.execute_query(query)
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
                    objs = self.db.execute_query(query)
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
                    objs = self.db.execute_query(query)
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
