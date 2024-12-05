from typing import Dict

from backend.graph.state import QueryState
from backend.graph.chains.sql_query_generator import sql_query_generator_chain


def sql_generation(state: QueryState) -> Dict[str, any]:
    result = sql_query_generator_chain.invoke({"messages": state["messages"]})
    if result.is_error:
        return {
            "is_error": result.is_error,
            "error_explanation": result.error_explanation,
        }
    return {"sql": result.query}
