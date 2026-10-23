"""Deterministic SQLGlot AST validation, schema allowlisting, and safety enforcement."""

from dataclasses import dataclass, field
import logging
import re
from typing import Dict, List, Optional, Set
import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError
from app.config import get_settings
from app.database.schema_introspection import APPROVED_TABLES, get_approved_schema_dict

logger = logging.getLogger("querypilot.guardrails.sql_validator")

# Forbidden SQL statement and expression types
FORBIDDEN_EXPRESSION_TYPES = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Drop,
    exp.Alter,
    exp.Create,
    exp.TruncateTable,
    exp.Command,
    exp.Commit,
    exp.Rollback,
    exp.Transaction,
    exp.Grant,
    exp.Revoke,
    exp.Set,
)


@dataclass
class SQLValidationResult:
    """Detailed result of SQL AST safety and schema validation."""

    status: str  # "passed", "rejected_unsafe_sql", "rejected_invalid_sql", "rejected_unknown_schema_reference"
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    sanitized_sql: str = ""
    tables_used: List[str] = field(default_factory=list)
    columns_used: List[str] = field(default_factory=list)

    @property
    def summary_message(self) -> str:
        if self.is_valid:
            return "SQL validation passed successfully."
        return "; ".join(self.errors)


def validate_sql(
    sql: str,
    dialect: Optional[str] = None,
    schema_allowlist: Optional[Dict[str, List[str]]] = None,
    max_rows: Optional[int] = None,
) -> SQLValidationResult:
    """Deterministically parse and validate a SQL query using SQLGlot AST inspection.

    Enforces:
    1. Exactly one valid SQL statement.
    2. Only SELECT or CTE WITH ... SELECT queries.
    3. Strict rejection of write, DDL, session, or modification commands (INSERT, UPDATE, DELETE, DROP, etc.).
    4. Table references must strictly be members of APPROVED_TABLES.
    5. Column references must exist in the referenced tables if schema_allowlist is provided.
    6. Injects a LIMIT clause if missing to protect against unbounded scans.

    Args:
        sql: The SQL query string to validate.
        dialect: SQL dialect (default 'postgres').
        schema_allowlist: Optional mapping of approved table names to approved column names.
        max_rows: Optional limit to enforce. Defaults to settings.max_rows.

    Returns:
        SQLValidationResult with validation status, sanitized SQL, and extracted tables/columns.
    """
    settings = get_settings()
    target_dialect = dialect or settings.database_dialect
    row_limit = max_rows or settings.max_rows
    # Normalize dialect name for SQLGlot
    sqlglot_dialect = "postgres" if "postgres" in target_dialect.lower() else "sqlite"

    cleaned_sql = sql.strip()
    if not cleaned_sql:
        return SQLValidationResult(
            status="rejected_invalid_sql",
            is_valid=False,
            errors=["SQL query cannot be empty."],
        )

    # 1. Parse statement(s)
    try:
        parsed_statements = sqlglot.parse(cleaned_sql, read=sqlglot_dialect)
    except ParseError as exc:
        return SQLValidationResult(
            status="rejected_invalid_sql",
            is_valid=False,
            errors=[f"SQL parsing error: {str(exc).splitlines()[0]}"],
        )
    except Exception as exc:
        return SQLValidationResult(
            status="rejected_invalid_sql",
            is_valid=False,
            errors=[f"Unable to parse SQL: {str(exc).splitlines()[0]}"],
        )

    # 2. Enforce exactly one statement
    if len(parsed_statements) != 1 or parsed_statements[0] is None:
        return SQLValidationResult(
            status="rejected_unsafe_sql",
            is_valid=False,
            errors=[
                f"Expected exactly 1 SQL statement, but found {len(parsed_statements)}. Multi-statement queries are strictly prohibited."
            ],
        )

    ast = parsed_statements[0]

    # 3. Top-level statement must be read-only (Select or Union)
    if not isinstance(ast, (exp.Select, exp.Union)):
        return SQLValidationResult(
            status="rejected_unsafe_sql",
            is_valid=False,
            errors=[
                f"Forbidden statement type '{ast.key.upper()}'. Only read-only SELECT queries are permitted."
            ],
        )

    # 4. Search entire AST tree for any forbidden write or DDL operations
    for forbidden_type in FORBIDDEN_EXPRESSION_TYPES:
        found_forbidden = list(ast.find_all(forbidden_type))
        if found_forbidden:
            op_name = forbidden_type.__name__.replace("Table", "").upper()
            return SQLValidationResult(
                status="rejected_unsafe_sql",
                is_valid=False,
                errors=[
                    f"Forbidden operation '{op_name}' detected. Write and DDL operations are strictly prohibited."
                ],
            )

    # 5. Extract CTE alias names to differentiate CTE references from real tables
    cte_names: Set[str] = {
        cte.alias.lower()
        for cte in ast.find_all(exp.CTE)
        if cte.alias
    }

    # 6. Extract table aliases and validate physical tables against approved allowlist
    tables_found: Set[str] = set()
    unknown_tables: Set[str] = set()
    table_alias_map: Dict[str, str] = {}  # alias -> real table or cte name

    for table_node in ast.find_all(exp.Table):
        t_name = table_node.name.lower()
        t_alias = table_node.alias.lower() if table_node.alias else None

        if t_alias:
            table_alias_map[t_alias] = t_name

        if t_name in cte_names:
            continue

        tables_found.add(t_name)
        if t_name not in APPROVED_TABLES:
            unknown_tables.add(t_name)

    if unknown_tables:
        return SQLValidationResult(
            status="rejected_unknown_schema_reference",
            is_valid=False,
            errors=[
                f"Referenced unapproved table(s): {', '.join(sorted(unknown_tables))}. "
                f"Permitted tables: {', '.join(sorted(APPROVED_TABLES))}."
            ],
            tables_used=list(tables_found),
        )

    # 7. Collect projection aliases (e.g. SUM(...) AS revenue, COUNT(*) AS count)
    select_aliases: Set[str] = {
        alias_node.alias.lower()
        for alias_node in ast.find_all(exp.Alias)
        if alias_node.alias
    }

    # 8. Extract and validate columns if allowlist provided
    columns_found: Set[str] = set()
    unknown_columns: List[str] = []

    active_allowlist = schema_allowlist or get_approved_schema_dict()

    # Collect all approved columns across referenced physical tables
    all_allowed_columns: Set[str] = set()
    for t in tables_found:
        if t in active_allowlist:
            all_allowed_columns.update(c.lower() for c in active_allowlist[t])

    for col_node in ast.find_all(exp.Column):
        col_name = col_node.name.lower()
        # Wildcard (*) is skipped
        if col_name == "*":
            continue

        # If it is an alias defined in SELECT (used in ORDER BY, GROUP BY, etc.), allow it
        if col_name in select_aliases:
            continue

        columns_found.add(col_name)

        # Check explicit table prefix e.g. customers.region or alias e.g. c.region
        table_prefix = col_node.table.lower() if col_node.table else None
        if table_prefix:
            resolved_table = table_alias_map.get(table_prefix, table_prefix)
            if resolved_table in cte_names:
                # Column belongs to a CTE, allowed
                continue
            elif resolved_table in active_allowlist:
                allowed_for_table = {c.lower() for c in active_allowlist[resolved_table]}
                if col_name not in allowed_for_table:
                    unknown_columns.append(f"{resolved_table}.{col_name}")
            elif resolved_table in APPROVED_TABLES:
                # Table in approved tables but not in custom allowlist dict
                continue
            else:
                unknown_columns.append(f"{table_prefix}.{col_name}")
        else:
            # Column without table prefix: must exist in at least one of the referenced tables
            if all_allowed_columns and col_name not in all_allowed_columns:
                unknown_columns.append(col_name)

    if unknown_columns:
        return SQLValidationResult(
            status="rejected_unknown_schema_reference",
            is_valid=False,
            errors=[
                f"Referenced unapproved column(s): {', '.join(sorted(set(unknown_columns)))}. "
                "These columns do not exist in the referenced schema."
            ],
            tables_used=list(tables_found),
            columns_used=list(columns_found),
        )

    # 8. Inject or enforce LIMIT clause
    limit_clause = ast.args.get("limit")
    if limit_clause is None:
        ast = ast.limit(row_limit)
    else:
        # If model generated a limit greater than max_rows, cap it
        try:
            current_limit_val = int(limit_clause.expression.this)
            if current_limit_val > row_limit:
                ast = ast.limit(row_limit)
        except (ValueError, TypeError, AttributeError):
            pass

    # Generate sanitized SQL string in target dialect
    sanitized_sql = ast.sql(dialect=sqlglot_dialect, pretty=True)

    return SQLValidationResult(
        status="passed",
        is_valid=True,
        errors=[],
        sanitized_sql=sanitized_sql,
        tables_used=sorted(list(tables_found)),
        columns_used=sorted(list(columns_found)),
    )
