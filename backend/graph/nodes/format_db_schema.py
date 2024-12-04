from backend.graph.nodes.fetch_db_schema import fetch_db_schema_details
from backend.graph.state import QueryState

from backend.graph.chains.db_schema_formatter import db_schema_formatter_chain


def format_db_schema(state: QueryState):
    all_table_schema = state["messages"][-1].content
    print(f"Schema : {all_table_schema}")
    print(db_schema_formatter_chain.invoke({"ddl": all_table_schema}))
    pass


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
    print(format_db_schema(state))
