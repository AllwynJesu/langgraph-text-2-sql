from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


class UserInputValidator(BaseModel):

    is_error: bool = Field(description="Answer addresses the question, 'yes' or 'no'")
    error_explanation: str = Field(
        description="Explain why given query is invalid. Populate only if 'is_error' file is yes",
        default=None,
    )


llm = ChatOpenAI(temperature=0)
structured_llm_validator = llm.with_structured_output(UserInputValidator)

system_role = """
You are an intelligent assistant specialized in understanding natural language database queries. Your task is to analyze a given query in plain English and determine:

1. Whether the query corresponds to a "data selection" operation (e.g., retrieving data via SELECT).
2. Whether the query involves a DML operation (e.g., INSERT, UPDATE, DELETE).

Instructions:
- If the query corresponds to only "data selection" (retrieving data), respond with:
  - `is_error: no`
  - `error_explanation`: `N/A`

- If the query involves any DML operation (e.g., inserting, updating, or deleting data), respond with:
  - `is_error: yes`
  - `error_explanation` : A clear explanation of why the query is invalid for selection purposes and mention that it involves data modification.
"""

user_input_validator_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_role),
        ("human", "User question: \n\n {question}"),
    ]
)

user_input_validator_chain = user_input_validator_prompt | structured_llm_validator

if __name__ == "__main__":
    result = user_input_validator_chain.invoke(
        {"question": "get list of people who watch movie matrix"}
    )
    print(result)
    pass
