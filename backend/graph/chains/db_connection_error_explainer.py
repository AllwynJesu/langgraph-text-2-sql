from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


class DBConnectionValidator(BaseModel):

    is_error: bool = Field(description="Answer addresses the question, 'yes' or 'no'")
    error_explanation: str = Field(
        description="Explain why given DB connection test failed and suggest 2-3 fixes. Populate only if 'is_error' file is yes",
        default=None,
    )


#
llm = ChatOpenAI(temperature=0)
# db = SQLDatabase.from_uri("postgresql://admin:password@localhost:6432/online_store")
# toolkit = SQLDatabaseToolkit(db=db, llm=llm)
# tools = toolkit.get_tools()
system_role = """
    You are a database troubleshooting assistant specializing in PostgreSQL. Your task is to analyze PostgreSQL connection 
    error messages and provide the user with a clear explanation of what might have gone wrong and how they can resolve the issue.
    
    Instructions:
    1. Input: The user will provide an error message from their PostgreSQL connection attempt.
    2. Output: Analyze the error message and respond with:
       - A brief explanation of the possible cause(s) of the error and Suggested actionable steps to resolve the issue.
    
    Your response should follow this format:
    is_error: yes
    error_explanation: <Provide a clear and concise explanation of what might have gone wrong. Mention common reasons for the error.> and Suggested 2-3 Fixes:
    1. <Provide actionable steps to resolve the issue.>
    2. <If applicable, include alternative solutions.>
    
    Examples:
    
    1. Input:
       Error: could not connect to server: Connection refused
       Is the server running on host "localhost" and accepting TCP/IP connections on port 5432?
    
       Output:
       is_error=True 
       error_explanation: This error indicates that the PostgreSQL server is either not running, or it is not accessible on the specified host and port.Suggested Fixes are
       1. Ensure the PostgreSQL server is running by executing `systemctl status postgresql` (Linux) or checking the service in Task Manager (Windows).
       2. Verify that the host ("localhost") and port (5432) are correct.
       3. Check the PostgreSQL configuration file (`postgresql.conf`) to ensure it is set to accept connections on the desired host and port.
       4. Confirm that your firewall or network settings are not blocking the connection.
    
    2. Input:
       Error: FATAL: password authentication failed for user "admin"
    
       Output:
       is_error=True 
       error_explanation: This error occurs when the provided username and password do not match the credentials stored in the PostgreSQL database.Suggested Fixes:
       1. Verify that the username and password are correct.
       2. Check the `pg_hba.conf` file to ensure it allows password authentication for the specified user and host.
       3. Reset the password for the user "admin" if needed, using the `ALTER USER` SQL command.
    
    Always provide clear, actionable solutions that users can follow easily. If the error message is ambiguous, mention possible causes and suggest a general troubleshooting approach.
"""

db_connection_explain_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_role),
        ("human", "Error message: \n\n {error}"),
    ]
)

structured_llm_explainer = llm.with_structured_output(DBConnectionValidator)
db_connection_error_explain_chain = (
    db_connection_explain_prompt | structured_llm_explainer
)

if __name__ == "__main__":
    result = db_connection_error_explain_chain.invoke(
        {
            "error": "could not connect to server: Connection refused. Is the server running on host 'localhost' and accepting TCP/IP connections on port 5432?"
        }
    )
    print(result)
    pass
