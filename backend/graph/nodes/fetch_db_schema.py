from typing import Dict

from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_core.prompts import (
    HumanMessagePromptTemplate,
)
from langchain_openai import ChatOpenAI

from backend.graph.state import QueryState
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
llm = ChatOpenAI(temperature=0)


def fetch_db_schema_details(state: QueryState) -> Dict[str, any]:
    db_config_details = state["db_config"]
    db = SQLDatabase.from_uri(
        f"postgresql://{db_config_details.get("username")}:{db_config_details.get("password")}@{db_config_details.get("host")}:{db_config_details.get("port")}/{db_config_details.get("database")}"
    )
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    tools = toolkit.get_tools()
    list_tables_tool = next(tool for tool in tools if tool.name == "sql_db_list_tables")
    get_schema_tool = next(tool for tool in tools if tool.name == "sql_db_schema")
    table_names = list_tables_tool.invoke("")
    # return {"messages": [("user", get_schema_tool.invoke(table_names))]}
    return {
        "messages": [
            HumanMessagePromptTemplate.from_template(
                get_schema_tool.invoke(table_names)
            ).format()
        ]
    }


if __name__ == "__main__":
    db_config = {
        "host": "localhost",
        "port": "6432",
        "database": "online_store",
        "username": "admin",
        "password": "password",
    }
    state = QueryState(db_config=db_config)
    print(fetch_db_schema_details(state))
