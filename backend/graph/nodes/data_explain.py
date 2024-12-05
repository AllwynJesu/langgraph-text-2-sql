from typing import Dict

from backend.graph.state import QueryState
from backend.graph.chains.data_explainer import data_explainer_chain


def explain_data(state: QueryState) -> Dict[str, str]:
    result = data_explainer_chain.invoke(
        {"messages": state["messages"], "data": state["data"]}
    )
    return {"explanation": result.explanation}
