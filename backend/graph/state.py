from typing import List, Dict, TypedDict, Annotated

from langgraph.graph import add_messages
from marshmallow.fields import Boolean


class QueryState(TypedDict):
    db_config: Dict[str, str]
    messages: Annotated[list, add_messages]
    is_error: Boolean
    error_explanation: str
    sql: str
    data: List[Dict[str, any]]
    explanation: str
