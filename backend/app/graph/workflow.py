"""Compiled LangGraph workflow assembly for QueryPilot."""

from langgraph.graph import END, START, StateGraph
from app.graph.nodes import (
    analyze_results_node,
    build_chart_node,
    classify_question_node,
    execute_sql_node,
    finalize_response_node,
    generate_sql_node,
    get_schema_node,
    repair_sql_node,
    validate_sql_node,
)
from app.graph.routing import (
    route_after_classification,
    route_after_execution,
    route_after_validation,
)
from app.graph.state import SQLState


def create_workflow() -> StateGraph:
    """Construct and compile the QueryPilot LangGraph query processing state graph."""
    builder = StateGraph(SQLState)

    # 1. Register all nodes
    builder.add_node("classify_question", classify_question_node)
    builder.add_node("get_schema", get_schema_node)
    builder.add_node("generate_sql", generate_sql_node)
    builder.add_node("validate_sql", validate_sql_node)
    builder.add_node("repair_sql", repair_sql_node)
    builder.add_node("execute_sql", execute_sql_node)
    builder.add_node("analyze_results", analyze_results_node)
    builder.add_node("build_chart", build_chart_node)
    builder.add_node("finalize_response", finalize_response_node)

    # 2. Add entry point edge
    builder.add_edge(START, "classify_question")

    # 3. Question classification conditional routing
    builder.add_conditional_edges(
        "classify_question",
        route_after_classification,
        {
            "get_schema": "get_schema",
            "finalize_response": "finalize_response",
        },
    )

    # 4. Standard linear flow: get_schema -> generate_sql -> validate_sql
    builder.add_edge("get_schema", "generate_sql")
    builder.add_edge("generate_sql", "validate_sql")

    # 5. Validation conditional routing (pass -> execute, fail -> repair or finalize)
    builder.add_conditional_edges(
        "validate_sql",
        route_after_validation,
        {
            "execute_sql": "execute_sql",
            "repair_sql": "repair_sql",
            "finalize_response": "finalize_response",
        },
    )

    # 6. Repair loop (repair -> validate)
    builder.add_edge("repair_sql", "validate_sql")

    # 7. Execution conditional routing (success -> analyze, error -> repair or finalize)
    builder.add_conditional_edges(
        "execute_sql",
        route_after_execution,
        {
            "analyze_results": "analyze_results",
            "repair_sql": "repair_sql",
            "finalize_response": "finalize_response",
        },
    )

    # 8. Post-analysis flow: analyze_results -> build_chart -> finalize_response -> END
    builder.add_edge("analyze_results", "build_chart")
    builder.add_edge("build_chart", "finalize_response")
    builder.add_edge("finalize_response", END)

    return builder.compile()


# Singleton compiled workflow instance
querypilot_workflow = create_workflow()
