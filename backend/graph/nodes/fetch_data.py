from typing import Dict

import psycopg2
from langchain_core.prompts import HumanMessagePromptTemplate

from backend.graph.state import QueryState


def fetch_db_data(state: QueryState) -> Dict[str, any]:
    db_config_details = state["db_config"]
    sql_query = state["sql"]

    connection_string = (
        f"dbname={db_config_details.get('database')} "
        f"user={db_config_details.get('username')} "
        f"password={db_config_details.get('password')} "
        f"host={db_config_details.get('host')} "
        f"port={db_config_details.get('port')}"
    )

    try:
        with psycopg2.connect(connection_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql_query)
                column_names = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                return {"data": [dict(zip(column_names, row)) for row in rows]}

    except psycopg2.Error as e:
        error_message = str(e)
        return {
            "is_error": True,
            "messages": [HumanMessagePromptTemplate.from_template(error_message)],
        }


if __name__ == "__main__":
    db_config = {
        "host": "localhost",
        "port": "6432",
        "database": "online_store",
        "username": "admin",
        "password": "password",
    }
    state = QueryState(
        db_config=db_config,
        sql="WITH max_order AS (SELECT MAX(total_amount) AS max_total FROM orders) "
        "SELECT o.order_id, o.total_amount, u.first_name, u.last_name, p.product_name, "
        "oi.quantity FROM orders o JOIN users u ON o.user_id = u.user_id JOIN "
        "order_items oi ON o.order_id = oi.order_id JOIN products p ON oi.product_id = p.product_id "
        "WHERE o.total_amount = (SELECT max_total FROM max_order);",
    )
    print(fetch_db_data(state))
