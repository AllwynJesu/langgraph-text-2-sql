from typing import Optional

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

from dotenv import load_dotenv, find_dotenv

from backend.graph.nodes.fetch_db_schema import fetch_db_schema_details
from backend.graph.nodes.format_db_schema import format_db_schema
from backend.graph.state import QueryState

load_dotenv(find_dotenv())


class SQLQueryResult(BaseModel):
    query: Optional[str] = Field(
        description="Generated PostgreSQL query, or null if the query cannot be generated",
        default=None,
    )
    is_error: bool = Field(
        description="Indicates whether there was an error in generating the query. True for an error, False otherwise",
        default=False,
    )
    error_explanation: str = Field(
        description="Provides an explanation of why the query could not be generated. Populated only if 'is_error' is True",
        default=None,
    )


system_role = """
    You are a smart assistant for generating PostgreSQL SQL queries based on a provided database schema and a user query.
    Your task is to:
    1. Analyze the user query in the context of the given database schema.
    2. Generate a detailed SQL query that includes meaningful columns, not just ID columns. For example:
       - If the user asks for products with quantity greater than 20, include columns like product names, descriptions, and other useful columns in the result.
       - If relationships between tables are indirect or unclear, infer them logically where possible and include them in the query.
    3. Handle error scenarios:
       - If you cannot infer or establish the required relationships between tables to generate the query, set `is_error=True`.
       - Provide a clear `error_explanation` describing why the query could not be generated or why the request is invalid.
"""
llm = ChatOpenAI(temperature=0, model="gpt-4")
structured_llm_generator = llm.with_structured_output(SQLQueryResult)

sql_query_generator_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_role),
        ("placeholder", "{messages}"),
    ],
    template_format="jinja2",
)
sql_query_generator_chain = sql_query_generator_prompt | structured_llm_generator

if __name__ == "__main__":
    messages = [
        HumanMessagePromptTemplate.from_template(
            "is there any customer who order multiple times"
        ).format()
    ]
    db_config = {
        "host": "localhost",
        "port": "6432",
        "database": "online_store",
        "username": "admin",
        "password": "password",
    }
    state = QueryState(db_config=db_config, messages=messages)
    state["messages"].append(fetch_db_schema_details(state)["messages"][-1])
    state["messages"].append(format_db_schema(state)["messages"][-1])
    # print(state["messages"][-1])
    result = sql_query_generator_chain.invoke({"messages": state["messages"]})
    print(result.model_dump_json())
