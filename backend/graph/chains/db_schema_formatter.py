from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

from typing import List

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


class ColumnInfo(BaseModel):
    name: str = Field(description="Specifies the name of the column")
    type: str = Field(
        description="Specifies the data type of the column, such as VARCHAR, INT, etc."
    )
    explanation: str = Field(
        description="Provides a description of the column's purpose or usage"
    )


class TableInfo(BaseModel):
    table_name: str = Field(description="Specifies the name of the table")
    description: str = Field(description="Provides a description/summary of the table")
    columns: List[ColumnInfo] = Field(description="Lists all the columns in the table")
    relation_ship: str = Field(
        description="Lists related tables, separated by commas, indicating relationships with this table"
    )


class DatabaseSchema(BaseModel):
    tables: List[TableInfo] = Field(
        description="Lists all the tables in the database schema"
    )


llm = ChatOpenAI(temperature=0)
structured_llm_formatter = llm.with_structured_output(DatabaseSchema)

system_role = """
    You are a database schema analyzer and formatter. Your task is to analyze a given SQL DDL string containing definitions 
    for multiple tables and format it into a structured schema using the provided Pydantic model format. The input may 
    include additional lines that are not part of table definitions—these should be ignored.
    
    ### Input:
    A string containing DDL statements for tables in SQL. Each table includes its name, columns, and optionally relationships or constraints.
    
    ### Output:
    A valid Pydantic model representation of the schema, adhering to the following structure:
    
    1. **`ColumnInfo`**:
       - `name`: Name of the column.
       - `type`: Data type of the column (e.g., VARCHAR, INT).
       - `explanation`: Provide an explanation if available (from comments or constraints). If not available, please your own.
    
    2. **`TableInfo`**:
       - `table_name`: Name of the table.
       - `columns`: List of `ColumnInfo` for the table.
       - `relation_ship`: Comma-separated related tables inferred from foreign keys. If none, set as `"None"`.
       - `description`:provides a description/summary of the table
    
    3. **`DatabaseSchema`**:
       - `tables`: List of all `TableInfo`.
    
    ### Additional Notes:
    - Include only table definitions; ignore non-table lines.
    - Preserve column order from the DDL.
    - Extract relationships from foreign key constraints, if any.
    - Ensure descriptions are precise, even if inferred.
"""

user_input_validator_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_role),
        ("human", "DDL string: \n\n {ddl}"),
    ]
)
db_schema_formatter_chain = user_input_validator_prompt | structured_llm_formatter
