from langchain.chains.question_answering.map_reduce_prompt import messages
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

from dotenv import load_dotenv, find_dotenv

from backend.graph.nodes.fetch_data import fetch_db_data
from backend.graph.state import QueryState

load_dotenv(find_dotenv())


class DataExplain(BaseModel):
    explanation: str = Field(
        description="Provides explanation on tabular data based on a user query",
        default=None,
    )


llm = ChatOpenAI(temperature=0, model="gpt-4")
structured_llm_explainer = llm.with_structured_output(DataExplain)

system_role = """
    You are a smart assistant for analyzing and explaining tabular data based on a user query. Your task is to:
    1. Analyze the provided data, which is a list of dictionaries where each dictionary represents a row of a table, and keys are the column names.
    2. Relate the analysis to the given user query:
       - Summarize how the data satisfies or does not satisfy the query conditions.
       - Provide relevant observations based on the query.
    3. Summarize the structure of the data:
       - List all column names and their data types (inferred from the values).
       - Describe the number of rows and columns.
    4. Highlight key observations:
       - Summarize trends, patterns, or anomalies in the data (e.g., average values, frequent items, empty fields).
       - If applicable, describe relationships between columns.
    5. If the data is empty (`[]` or 'None'), explain that no data is available, relate this to the query, suggest potential reasons, and provide possible next steps.
    
    ### Input Format:
    {
        "data": [
            {"order_id": 101, "total_amount": 500.0, "first_name": "John", "last_name": "Doe", "product_name": "Laptop", "quantity": 1},
            {"order_id": 102, "total_amount": 450.0, "first_name": "Jane", "last_name": "Smith", "product_name": "Phone", "quantity": 2}
        ],
        "messages": [
            ("type": "human", "content": "Get me the orders whose amount is greater than 400.")
        ]
    }
    
    ### Example Output:
    ### Output Format:
    ```json
    {
        "explanation": "<detailed explanation of the data and its relation to the query>"
    }```
        
    ### Input Example for Empty Data:
    {
        "data": [],
        "query": "Get me the orders whose amount is greater than 400."
    }
    
    ### Example Output for Empty Data:
    ### Output Format:
    ```json
    {
        "explanation": "No orders have a total amount greater than 400 and Possible next steps <give_steps>"
    }```
    
"""

data_explainer_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_role),
        ("placeholder", "{messages}"),
        HumanMessagePromptTemplate.from_template("Data is {data}"),
    ],
    template_format="jinja2",
)

data_explainer_chain = data_explainer_prompt | structured_llm_explainer

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
    data = fetch_db_data(state)
    messages = [
        HumanMessagePromptTemplate.from_template(
            "is there any customer who order multiple times"
        ).format()
    ]
    result = data_explainer_chain.invoke({"messages": messages, "data": data["data"]})
    print(result)
