from typing import Dict

from backend.graph.state import QueryState
from backend.graph.chains.user_input_validator import user_input_validator_chain


def user_input_validator_agent(state: QueryState) -> Dict[str, str]:
    user_input = state["messages"][-1].content
    result = user_input_validator_chain.invoke({"question": user_input})
    if result.is_error:
        return {
            "is_error": result.is_error,
            "error_explanation": result.error_explanation,
        }
    return {"is_error": "False"}