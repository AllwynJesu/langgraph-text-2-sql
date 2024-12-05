from langchain_core.prompts import HumanMessagePromptTemplate

from backend.graph.graph import graph

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
    result = graph.invoke({"messages": messages, "db_config": db_config})
    print(result)
    pass
