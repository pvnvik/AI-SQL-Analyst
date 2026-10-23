"""Schema metadata route for QueryPilot."""

import logging
from fastapi import APIRouter, HTTPException, status
from app.api.schemas import ColumnSchema, DatabaseSchemaResponse, TableSchema
from app.database.schema_introspection import REVENUE_BUSINESS_RULE, introspect_schema

logger = logging.getLogger("querypilot.api.schema")
router = APIRouter(tags=["Schema"])


@router.get("/schema", response_model=DatabaseSchemaResponse)
async def get_database_schema():
    """Retrieve approved database schema metadata and domain business rules."""
    try:
        schema = introspect_schema()
        table_schemas = [
            TableSchema(
                name=tbl.name,
                description=tbl.description,
                primary_keys=tbl.primary_keys,
                columns=[
                    ColumnSchema(
                        name=col.name,
                        type=col.type_name,
                        nullable=col.nullable,
                        primary_key=col.primary_key,
                        foreign_key=col.foreign_key,
                    )
                    for col in tbl.columns
                ],
            )
            for tbl in schema.tables.values()
        ]

        return DatabaseSchemaResponse(
            dialect=schema.dialect,
            tables=table_schemas,
            approved_tables_count=len(table_schemas),
            revenue_rule=REVENUE_BUSINESS_RULE,
        )
    except Exception as exc:
        logger.error("Failed to inspect database schema: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database schema metadata is currently unavailable. Ensure database is running and configured.",
        )
