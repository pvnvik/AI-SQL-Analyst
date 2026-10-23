"""Database schema introspection, metadata extraction, and LLM context formatting."""

from dataclasses import dataclass, field
import logging
import time
from typing import Dict, List, Optional, Set
from sqlalchemy import Engine, inspect
from app.database import connection

logger = logging.getLogger("querypilot.schema")

# Approved analytical tables that the agent and users are permitted to access
APPROVED_TABLES: Set[str] = {
    "customers",
    "products",
    "orders",
    "order_items",
}

# Clear semantic table descriptions to guide SQL generation
TABLE_DESCRIPTIONS: Dict[str, str] = {
    "customers": "Customer demographic details including region, city, and account creation date.",
    "products": "Product catalog containing product name, category, and standard unit price.",
    "orders": "Header records for customer orders, including order date and current fulfillment status.",
    "order_items": "Individual line items for each order, with quantity, sold unit price, and discount.",
}

# Canonical revenue definition for the retail domain
REVENUE_BUSINESS_RULE = (
    "REVENUE DEFINITION:\n"
    "Revenue is calculated on each line item as: (quantity * unit_price - discount_amount).\n"
    "Total revenue is: SUM(order_items.quantity * order_items.unit_price - order_items.discount_amount).\n"
    "CRITICAL RULE: There is NO 'revenue' or 'total_amount' column in any table. "
    "Do NOT write 'orders.revenue' or 'products.revenue'. Always calculate revenue using the formula above."
)


@dataclass
class ColumnInfo:
    """Metadata describing a single table column."""
    name: str
    type_name: str
    nullable: bool
    primary_key: bool
    foreign_key: Optional[str] = None


@dataclass
class TableInfo:
    """Metadata describing a single database table."""
    name: str
    description: str
    columns: List[ColumnInfo] = field(default_factory=list)
    primary_keys: List[str] = field(default_factory=list)
    foreign_keys: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class DatabaseSchema:
    """Complete inspected schema representation."""
    dialect: str
    tables: Dict[str, TableInfo] = field(default_factory=dict)
    inspected_at: float = field(default_factory=time.time)


# In-memory schema cache
_cached_schema: Optional[DatabaseSchema] = None
_cached_prompt_context: Optional[str] = None
_cache_ttl_seconds: int = 300  # 5 minutes


def introspect_schema(
    engine: Optional[Engine] = None, force_refresh: bool = False
) -> DatabaseSchema:
    """Introspect approved tables and columns from the database.

    Args:
        engine: SQLAlchemy engine to inspect. Defaults to the configured engine.
        force_refresh: If True, bypass the in-memory cache.

    Returns:
        DatabaseSchema containing metadata for all approved tables.
    """
    global _cached_schema, _cached_prompt_context

    now = time.time()
    if (
        not force_refresh
        and _cached_schema is not None
        and (now - _cached_schema.inspected_at) < _cache_ttl_seconds
    ):
        return _cached_schema

    target_engine = engine or connection.get_engine()
    inspector = inspect(target_engine)
    dialect_name = target_engine.dialect.name

    available_tables = set(inspector.get_table_names())
    # Keep only tables in the allowlist
    valid_tables = available_tables.intersection(APPROVED_TABLES)

    tables_meta: Dict[str, TableInfo] = {}

    for table_name in valid_tables:
        col_list: List[ColumnInfo] = []
        pk_constraint = inspector.get_pk_constraint(table_name)
        primary_keys = pk_constraint.get("constrained_columns", []) if pk_constraint else []

        fks = inspector.get_foreign_keys(table_name)
        fk_map: Dict[str, str] = {}
        fk_records: List[Dict[str, str]] = []

        for fk in fks:
            referred_table = fk.get("referred_table")
            for local_col, ref_col in zip(
                fk.get("constrained_columns", []),
                fk.get("referred_columns", []),
            ):
                target_str = f"{referred_table}.{ref_col}"
                fk_map[local_col] = target_str
                fk_records.append({"column": local_col, "references": target_str})

        raw_columns = inspector.get_columns(table_name)
        for col in raw_columns:
            c_name = col["name"]
            c_type = str(col["type"])
            c_null = col.get("nullable", True)
            c_pk = c_name in primary_keys
            c_fk = fk_map.get(c_name)

            col_list.append(
                ColumnInfo(
                    name=c_name,
                    type_name=c_type,
                    nullable=c_null,
                    primary_key=c_pk,
                    foreign_key=c_fk,
                )
            )

        tables_meta[table_name] = TableInfo(
            name=table_name,
            description=TABLE_DESCRIPTIONS.get(table_name, ""),
            columns=col_list,
            primary_keys=primary_keys,
            foreign_keys=fk_records,
        )

    schema = DatabaseSchema(
        dialect=dialect_name,
        tables=tables_meta,
        inspected_at=now,
    )

    _cached_schema = schema
    _cached_prompt_context = None  # Invalidate formatted string cache
    return schema


def get_schema_prompt_context(
    engine: Optional[Engine] = None, force_refresh: bool = False
) -> str:
    """Generate a clean, structured schema prompt string for Gemini SQL generator.

    Includes tables, columns with types, keys, relationships, and domain rules.
    """
    global _cached_prompt_context

    if not force_refresh and _cached_prompt_context is not None:
        return _cached_prompt_context

    schema = introspect_schema(engine=engine, force_refresh=force_refresh)

    lines: List[str] = [
        f"Database Dialect: {schema.dialect.upper()}",
        "",
        "Approved Schema Tables:",
    ]

    for table_name in sorted(schema.tables.keys()):
        tbl = schema.tables[table_name]
        lines.append(f"\nTable: {tbl.name}")
        if tbl.description:
            lines.append(f"  Description: {tbl.description}")
        lines.append("  Columns:")
        for col in tbl.columns:
            attrs = []
            if col.primary_key:
                attrs.append("PRIMARY KEY")
            if col.foreign_key:
                attrs.append(f"REFERENCES {col.foreign_key}")
            if not col.nullable and not col.primary_key:
                attrs.append("NOT NULL")
            attr_str = f" ({', '.join(attrs)})" if attrs else ""
            lines.append(f"    - {col.name}: {col.type_name}{attr_str}")

    lines.append("\n" + "=" * 50)
    lines.append(REVENUE_BUSINESS_RULE)
    lines.append("=" * 50)

    formatted_context = "\n".join(lines)
    _cached_prompt_context = formatted_context
    return formatted_context


STATIC_APPROVED_COLUMNS: Dict[str, List[str]] = {
    "customers": ["id", "customer_name", "region", "city", "created_at"],
    "products": ["id", "product_name", "category", "unit_price"],
    "orders": ["id", "customer_id", "order_date", "status"],
    "order_items": ["id", "order_id", "product_id", "quantity", "unit_price", "discount_amount"],
}


def get_approved_schema_dict(engine: Optional[Engine] = None) -> Dict[str, List[str]]:
    """Return a mapping of approved table names to their approved column names.

    Used by SQL validator and AST checker to verify table and column references.
    Falls back gracefully to STATIC_APPROVED_COLUMNS if database is unconfigured.
    """
    try:
        schema = introspect_schema(engine=engine)
        if schema and schema.tables:
            return {
                table_name: [c.name for c in tbl.columns]
                for table_name, tbl in schema.tables.items()
            }
    except Exception as exc:
        logger.debug("Database inspection unavailable, using static schema allowlist: %s", exc)

    return STATIC_APPROVED_COLUMNS


def clear_schema_cache() -> None:
    """Clear all cached schema metadata."""
    global _cached_schema, _cached_prompt_context
    _cached_schema = None
    _cached_prompt_context = None
