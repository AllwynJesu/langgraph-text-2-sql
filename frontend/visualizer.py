from typing import List, Dict, Union, Optional

from dotenv import load_dotenv, find_dotenv
from langchain_core.prompts import (
    HumanMessagePromptTemplate,
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain_openai import ChatOpenAI
from pandas.io.formats.style import jinja2
from pydantic import BaseModel, Field

from backend.graph.nodes.fetch_data import fetch_db_data
from backend.graph.state import QueryState

load_dotenv(find_dotenv())


class VisualizationOptions(BaseModel):
    """
    Additional options for visualization, such as tooltip columns.
    """

    tooltip: Optional[List[str]] = Field(
        None,
        description="List of column names to display as tooltips on the visualization.",
    )


class VisualizationConfig(BaseModel):
    """
    Main model for visualization configuration. Represents the structure for determining
    if visualization is possible and how it should be rendered.
    """

    is_visualization_possible: bool = Field(
        ..., description="Indicates whether the data can be visualized."
    )
    chart_type: Optional[str] = Field(
        None,
        description="The type of chart suitable for visualization, e.g., 'Line Chart', 'Bar Chart'.",
    )
    explanation: Optional[str] = Field(
        None,
        description="Explanation of why the suggested chart type is suitable, or why visualization is not possible.",
    )
    data: Optional[List[Dict[str, Union[str, int, float, None]]]] = Field(
        None,
        description="The dataset to be visualized, represented as a list of records (rows).",
    )
    x_axis: Optional[str] = Field(
        None,
        description="The column name to be used as the X-axis in the visualization.",
    )
    y_axis: Optional[Union[str, List[str]]] = Field(
        None,
        description="The column name or list of column names to be used as the Y-axis in the visualization.",
    )
    other_options: Optional[VisualizationOptions] = Field(
        None, description="Additional options for customization, such as tooltips."
    )


llm = ChatOpenAI(temperature=0, model="gpt-4")
structured_llm_visualizer = llm.with_structured_output(VisualizationConfig)

system_role = """
    You are an AI assistant responsible for generating visualization configurations based on provided SQL query results 
    or data structure. Your task is to determine if the data can be visualized, suggest the appropriate chart type, and 
    provide a detailed configuration for rendering the chart dynamically.
    
    ### Instructions:
    1. **Analyze the Data**:
       - Examine the provided data (columns, data types, and content).
       - Identify patterns like time-series data, categorical values, or numerical relationships.
    
    2. **Chart Types**:
       - Suggest a suitable chart type based on the data:
         - **Line Chart**: For time-series or continuous numerical data.
         - **Bar Chart**: For categorical data with numerical values.
         - **Pie Chart**: For proportions or percentages.
         - **Scatter Plot**: For relationships between two numerical variables.
         - **Histogram**: For distribution of a single numerical variable.
         - **Table**: For data that is better suited to tabular representation.
    
    3. **Output Format**:
       - If visualization is possible, generate a JSON object with the following structure:
         ```json
         {
             "is_visualization_possible": true,
             "chart_type": "<chosen_chart_type>",
             "explanation": "<why this chart type is suitable>",
             "data": <data_array>,
             "x_axis": "<x_axis_column>",
             "y_axis": "<y_axis_column_or_columns>",
             "other_options": {
                 "tooltip": ["<columns_to_display_in_tooltips>"]
             }
         }
         ```
       - If visualization is not possible, generate a JSON object with this structure:
         ```json
         {
             "is_visualization_possible": false,
             "explanation": "<reason why visualization is not possible>"
         }
         ```
    
    4. **Examples**:
    
    #### Example 1:
    **Input:**
    - SQL Query: `SELECT order_date, SUM(total_amount) AS daily_sales FROM orders GROUP BY order_date;`
    - Data:
      ```json
      [
          {"order_date": "2023-12-01", "daily_sales": 5000.0},
          {"order_date": "2023-12-02", "daily_sales": 3000.0},
          {"order_date": "2023-12-03", "daily_sales": 4500.0}
      ]
    ```
    **Output:**
    ```json
    {
        "is_visualization_possible": true,
        "chart_type": "Line Chart",
        "explanation": "The data contains time-series information (order_date) with numerical aggregation (daily_sales), making it suitable for a line chart.",
        "data": [
            {"order_date": "2023-12-01", "daily_sales": 5000.0},
            {"order_date": "2023-12-02", "daily_sales": 3000.0},
            {"order_date": "2023-12-03", "daily_sales": 4500.0}
        ],
        "x_axis": "order_date",
        "y_axis": "daily_sales",
        "other_options": {
            "tooltip": ["order_date", "daily_sales"]
        }
    }
    ```
"""

visualizer_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(
            system_role, template_format="jinja2"
        ),
        HumanMessagePromptTemplate.from_template("SQL Query: {sql} \n Data: {data}"),
    ],
)

visualizer_chain = visualizer_prompt | structured_llm_visualizer
pass

if __name__ == "__main__":
    db_config = {
        "host": "localhost",
        "port": "6432",
        "database": "online_store",
        "username": "admin",
        "password": "password",
    }
    sql = """
        WITH max_order AS (SELECT MAX(total_amount) AS max_total FROM orders) 
        SELECT o.order_id, o.total_amount, u.first_name, u.last_name, p.product_name, 
        oi.quantity FROM orders o JOIN users u ON o.user_id = u.user_id JOIN 
        order_items oi ON o.order_id = oi.order_id JOIN products p ON oi.product_id = p.product_id 
        WHERE o.total_amount = (SELECT max_total FROM max_order);
        """
    state = QueryState(
        db_config=db_config,
        sql=sql,
    )
    data = fetch_db_data(state)
    result = visualizer_chain.invoke({"sql": sql, "data": data["data"]})
    print(result)
