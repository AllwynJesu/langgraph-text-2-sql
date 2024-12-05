from typing import Dict

from langchain_core.prompts import HumanMessagePromptTemplate

from backend.graph.nodes.fetch_db_schema import fetch_db_schema_details
from backend.graph.state import QueryState

from backend.graph.chains.db_schema_formatter import db_schema_formatter_chain
import json


def format_db_schema(state: QueryState) -> Dict[str, any]:
    all_table_schema = state["messages"][-1].content
    # print(f"Schema : {all_table_schema}")
    schema = db_schema_formatter_chain.invoke({"ddl": all_table_schema})
    template = """
    The following is database schema:
    {schema}
    """
    schema_str = schema.json()
    prompt = HumanMessagePromptTemplate.from_template(template)
    return {"messages": [prompt.format(schema=schema_str)]}


if __name__ == "__main__":
    db_config = {
        "host": "localhost",
        "port": "6432",
        "database": "online_store",
        "username": "admin",
        "password": "password",
    }
    state = QueryState(db_config=db_config)
    state["messages"] = fetch_db_schema_details(state)["messages"]
    result = format_db_schema(state)
    pass
