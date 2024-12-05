import pandas as pd
import altair as alt
import streamlit as st
from typing import Dict, List, Any

from langchain_core.prompts import HumanMessagePromptTemplate

from backend.graph.graph import graph
from frontend.visualizer import visualizer_chain


def backend_call(db_config: Dict[str, str], query: str):
    messages = [HumanMessagePromptTemplate.from_template(query).format()]
    result = graph.invoke({"messages": messages, "db_config": db_config})
    return result


def create_chart(visual_config):
    # Convert data to DataFrame
    df = pd.DataFrame(visual_config.data)

    # Check if y_axis is a list and reshape the data if necessary
    if isinstance(visual_config.y_axis, list):
        long_data = pd.melt(
            df,
            id_vars=[visual_config.x_axis]
            + [col for col in df.columns if col not in visual_config.y_axis],
            value_vars=visual_config.y_axis,
            var_name="Metric",
            value_name="Value",
        )
    else:
        long_data = df

    # Create the chart dynamically based on the chart type
    if visual_config.chart_type == "Bar Chart":
        if isinstance(visual_config.y_axis, list):
            chart = (
                alt.Chart(long_data)
                .mark_bar()
                .encode(
                    x=alt.X(visual_config.x_axis),
                    y=alt.Y("Value"),
                    color=alt.Color("Metric"),
                    tooltip=visual_config.other_options.tooltip,
                )
                .properties(title="Bar Chart", width=800, height=400)
            )
        else:
            chart = (
                alt.Chart(long_data)
                .mark_bar()
                .encode(
                    x=alt.X(visual_config.x_axis),
                    y=alt.Y(visual_config.y_axis),
                    tooltip=visual_config.other_options.tooltip,
                )
                .properties(title="Bar Chart", width=800, height=400)
            )
    elif visual_config.chart_type == "Line Chart":
        chart = (
            alt.Chart(long_data)
            .mark_line()
            .encode(
                x=alt.X(visual_config.x_axis),
                y=alt.Y(
                    (
                        "Value"
                        if isinstance(visual_config.y_axis, list)
                        else visual_config.y_axis
                    ),
                    title="Value",
                ),
                color=alt.Color(
                    "Metric" if isinstance(visual_config.y_axis, list) else None,
                    title="Metric",
                ),
                tooltip=visual_config.other_options.tooltip,
            )
            .properties(title="Line Chart", width=800, height=400)
        )
    elif visual_config.chart_type == "Pie Chart":
        if isinstance(visual_config.y_axis, list):
            st.error("Pie Charts do not support multiple metrics in y_axis.")
            return None
        chart = (
            alt.Chart(long_data)
            .mark_arc()
            .encode(
                theta=alt.Theta(visual_config.y_axis),
                color=alt.Color(visual_config.x_axis),
                tooltip=visual_config.other_options.tooltip,
            )
            .properties(title="Pie Chart", width=400, height=400)
        )
    else:
        st.error(f"Unsupported chart type: {visual_config.chart_type}")
        return None

    return chart


# Streamlit App
st.set_page_config(
    page_title="SmartSQL Assistant", layout="wide", initial_sidebar_state="expanded"
)

st.title("SmartSQL Assistant")

st.sidebar.header("Database Configuration")
db_config = {
    "host": st.sidebar.text_input("Host", value="localhost"),
    "port": st.sidebar.text_input("Port", value="6432"),
    "database": st.sidebar.text_input("Database", value="database"),
    "username": st.sidebar.text_input("Username", value="admin"),
    "password": st.sidebar.text_input("Password", type="password"),
}

st.subheader("User Query")
user_query = st.text_area(
    "Enter your query:",
    placeholder="e.g., is there any customer who order multiple times",
)

if st.button("Execute Query"):
    with st.spinner("Processing query..."):
        # Call the backend with user inputs
        result = backend_call(db_config, user_query)

    # Display the result
    if result["is_error"]:
        st.error(f"Error: {result['error_explanation']}")
    else:
        st.success("Your query processed successfully!")

        st.subheader("SQL Query")
        st.code(result["sql"], language="sql")

        st.subheader("Explanation")
        st.write(result["explanation"])

        st.subheader("Data")
        if result["data"]:
            st.table(result["data"])
            llm_output = visualizer_chain.invoke(
                {"sql": result["data"], "data": result["data"]}
            )
            pass
            if llm_output.is_visualization_possible:
                chart = create_chart(llm_output)
                if chart:
                    st.altair_chart(chart, use_container_width=True)
            else:
                st.error("Visualization is not possible.")
                st.write(llm_output["explanation"])
        else:
            st.write("No data found.")

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("Authored by Allwyn Jesu")
