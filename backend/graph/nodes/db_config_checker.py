from typing import Dict
import psycopg2

from backend.graph.state import QueryState
from backend.graph.chains.db_connection_error_explainer import (
    db_connection_error_explain_chain,
)


def db_config_checker(state: QueryState) -> Dict[str, str]:
    try:
        db_config = state["db_config"]
        conn = psycopg2.connect(
            host=db_config.get("host"),
            port=db_config.get("port"),
            database=db_config.get("database"),
            user=db_config.get("username"),
            password=db_config.get("password"),
        )
        conn.close()
        return {"is_error": "False"}
    except psycopg2.Error as e:
        error_message = str(e)
        result = db_connection_error_explain_chain.invoke({"error": error_message})
        return {
            "is_error": result.is_error,
            "error_explanation": result.error_explanation,
        }


if __name__ == "__main__":
    db_config = {
        "host": "localhost",
        "port": "5432",
        "database": "online_store",
        "username": "admin",
        "password": "password",
    }
    state = QueryState(db_config=db_config)
    print(db_config_checker(state))
