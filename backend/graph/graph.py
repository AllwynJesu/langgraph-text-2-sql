from langgraph.graph import END, StateGraph

from backend.graph.consts import (
    DB_CONFIG_VALIDATOR_NODE,
    FETCH_DB_SCHEMA_NODE,
    DATA_FETCH_NODE,
    USER_INPUT_VALIDATOR_NODE,
    SQL_GENERATION_NODE,
    FORMAT_DB_SCHEMA_NODE,
    DATA_EXPLAINER_NODE,
)
from backend.graph.nodes.data_explain import explain_data
from backend.graph.nodes.db_config_checker import db_config_checker
from backend.graph.nodes.fetch_data import fetch_db_data
from backend.graph.nodes.fetch_db_schema import fetch_db_schema_details
from backend.graph.nodes.format_db_schema import format_db_schema
from backend.graph.nodes.sql_generation import sql_generation
from backend.graph.nodes.user_input_checker import user_input_validator_agent
from backend.graph.state import QueryState


def is_user_input_valid(state: QueryState):
    if state["is_error"]:
        return END
    return DB_CONFIG_VALIDATOR_NODE


def is_db_config_valid(state: QueryState):
    state["is_error"] = (
        state["is_error"] == "True"
        if isinstance(state["is_error"], str)
        else state["is_error"]
    )
    if state["is_error"]:
        return END
    return FETCH_DB_SCHEMA_NODE


def is_sql_generated(state: QueryState):
    state["is_error"] = (
        state["is_error"] == "True"
        if isinstance(state["is_error"], str)
        else state["is_error"]
    )
    if state["is_error"]:
        return END
    return DATA_FETCH_NODE


workflow = StateGraph(QueryState)
workflow.add_node(USER_INPUT_VALIDATOR_NODE, user_input_validator_agent)
workflow.add_node(DB_CONFIG_VALIDATOR_NODE, db_config_checker)
workflow.add_node(FETCH_DB_SCHEMA_NODE, fetch_db_schema_details)
workflow.add_node(FORMAT_DB_SCHEMA_NODE, format_db_schema)
workflow.add_node(SQL_GENERATION_NODE, sql_generation)
workflow.add_node(DATA_FETCH_NODE, fetch_db_data)
workflow.add_node(DATA_EXPLAINER_NODE, explain_data)

workflow.set_entry_point(USER_INPUT_VALIDATOR_NODE)
workflow.add_conditional_edges(
    USER_INPUT_VALIDATOR_NODE,
    is_user_input_valid,
    {DB_CONFIG_VALIDATOR_NODE: DB_CONFIG_VALIDATOR_NODE, END: END},
)
workflow.add_conditional_edges(
    DB_CONFIG_VALIDATOR_NODE,
    is_db_config_valid,
    {FETCH_DB_SCHEMA_NODE: FETCH_DB_SCHEMA_NODE, END: END},
)
workflow.add_edge(FETCH_DB_SCHEMA_NODE, FORMAT_DB_SCHEMA_NODE)
workflow.add_edge(FORMAT_DB_SCHEMA_NODE, SQL_GENERATION_NODE)
workflow.add_conditional_edges(
    SQL_GENERATION_NODE, is_sql_generated, {DATA_FETCH_NODE: DATA_FETCH_NODE, END: END}
)
workflow.add_edge(DATA_FETCH_NODE, DATA_EXPLAINER_NODE)
workflow.add_edge(DATA_EXPLAINER_NODE, END)

graph = workflow.compile()
graph.get_graph().draw_mermaid_png(output_file_path="graph.png")
