

from langgraph.graph import StateGraph, END
from sql_agent import retrieve_similar_queries, save_sql_example
from sql_agent import query_ollama_together, get_database_schema
from sqlalchemy import text, exc
import logging
import json
from typing import List, Union, TypedDict,Optional
from sql_agent import get_session
import re

# ✅ Define the Workflow State Schema
class AgentState(TypedDict):
    question: str  # The user’s question
    sql_query: str  # SQL query generated based on the question
    query_result: Union[str, List[dict]]  # The result of the SQL query or error message
    sql_error: bool  # Flag indicating if there was an SQL error
    garage_ids: List[int]  # List of garage IDs associated with the user
    userType: str  # The role of the user, e.g., 'owner' or 'customer'
    customerID: Optional[int]  # The customer ID for customers, or None for other roles

# ✅ Define workflow
workflow = StateGraph(state_schema=AgentState)

def clean_sql_query(query: str) -> str:
    """Cleans the generated SQL query by removing unwanted formatting, comments, and artifacts."""
    if not query:
        return ""

    query = query.strip().replace("ILIKE", "LIKE")

    # ✅ Remove unwanted markdown code block markers
    query = re.sub(r"```sql|```", "", query).strip()

    # ✅ Remove AI response artifacts
    query = query.replace("<s>", "").strip()

    # ✅ Remove comments
    query = re.sub(r'--.*', '', query)  # Inline comments
    query = re.sub(r'/\*[\s\S]*?\*/', '', query)  # Block comments

    return query

def execute_sql(state, config):
    """Execute the SQL query and return results using SQLAlchemy."""
    logging.debug(f"🟢 Executing SQL Query: {state['sql_query']}")
    
    session = config.get("configurable", {}).get("session")
    user_role = config.get("configurable", {}).get("role", "").lower()
    garage_ids = state.get("garage_ids", [])

    if not session:
        raise ValueError("Session is not available in config.")

    query = clean_sql_query(state["sql_query"]).strip()
    logging.debug(f"🟢 Executing SQL Query: {query}")

    # ✅ Define allowed tables per role
    # ROLE_TABLE_ACCESS = {
    #     "admin": ["customer_vehicle_info", "job_card_details", "vehicle_service_details", "vehicle_service_summary"],
    #     "owner": ["job_card_details", "vehicle_service_details", "vehicle_service_summary", "customer_vehicle_info"],
    #     "customer": ["job_card_details","vehicle_service_summary"]  # Only customer-specific data
    # }

    # ✅ Extract tables used in the query
    # used_tables = [table for table in ROLE_TABLE_ACCESS["admin"] if table in query.lower()]

    # 🚨 Reject customer queries for non-customer data
    # if user_role == "customer" and not set(used_tables).issubset(ROLE_TABLE_ACCESS["customer"]):
    #     logging.error(f"❌ Query out of domain for role 'customer'. Query: {query}")
    #     state["query_result"] = {"raw_answer": "", "human_readable": "Query out of domain"}
    #     state["sql_error"] = True
    #     return state

    # ✅ Continue with SQL execution only if query is valid
    try:
        result = session.execute(text(query))
        rows = result.fetchall()
        keys = result.keys()

        state["query_result"] = {"data": [dict(zip(keys, row)) for row in rows]}
        logging.debug(f"✅ Query Execution Successful. Results: {state['query_result']}")
        state["sql_error"] = False

    except exc.SQLAlchemyError as e:
        logging.error(f"❌ SQLAlchemy Error: {str(e)}")
        state["query_result"] = {"error": f"Database error: {str(e)}"}
        state["sql_error"] = True

    except Exception as e:
        logging.error(f"❌ General Error: {str(e)}")
        state["query_result"] = {"error": f"An error occurred: {str(e)}"}
        state["sql_error"] = True

    return generate_human_readable_response_with_llama(state)


def convert_nl_to_sql(state, config):
    """Convert a natural language query into an SQL query with RAG-based retrieval."""
    print("state in nl to sql: ", state)
    userType = state.get("userType")
    print(f"userType in nl to sql: {userType}")
    customerID = state.get("customerID")

    logging.debug(f"🟠 Inside convert_nl_to_sql | userType: {userType} | customerID: {customerID}")

    session = config.get("configurable", {}).get("session")
    if not session:
        raise ValueError("Session is not available in config.")

    question = state["question"]
    schema = get_database_schema(session)
    retrieved_queries = retrieve_similar_queries(question)
    retrieved_examples = "\n".join(retrieved_queries) if retrieved_queries else "No relevant examples found."

    # ✅ Ensure customer_id filter is applied for customers only
    if userType == "customer" and customerID:
        print(f"customerID: {customerID}")
        customer_filter = f"vs.customer_id = {customerID}"
    else:
        customer_filter = "True"

    # ✅ Improved Prompt Instructions
    prompt = f"""
### Instructions:
You are a MySQL SQL query generator. Follow these rules:
- Only output a valid `SELECT` statement.
- Use table aliases and define them before use.
- Correctly apply `JOIN ON` conditions.
- For customers:
  - Always include `WHERE {customer_filter}` to restrict results to their own data.
  - If a customer is querying for another customer’s data, return no results by using `WHERE {customer_filter}`.

- Ensure table aliases are correctly defined in `FROM` or `JOIN` before use.

#### Database Schema:
{schema}

#### Example Queries:
{retrieved_examples}

#### User's Question:
"{question}"

#### Correct SQL Query:
"""

    try:
        sql_query = query_ollama_together(prompt, "Qwen/Qwen2.5-Coder-32B-Instruct").strip()
        logging.debug(f"🟢 Generated SQL Query: {sql_query}")

        sql_query = clean_sql_query(sql_query)
        state["sql_query"] = sql_query

    except Exception as e:
        logging.error(f"❌ Error Occurred: {str(e)}")
        state["sql_query"] = "Query could not be generated."
        state["query_result"] = {"error": str(e)}

    return state


def generate_human_readable_response_with_llama(state):
    """Generate both a raw SQL query result and a human-readable response."""

    query_result = state["query_result"]
    if state["sql_error"]:
        state["query_result"] = {
            "raw_answer": query_result,
            "human_readable": f"An error occurred: {query_result}"
        }
        return state

    if not query_result or "data" not in query_result or not query_result["data"]:
        state["query_result"] = {
            "raw_answer": query_result,
            "human_readable": "No relevant data found."
        }
        return state

    results = query_result["data"]
    state["query_result"] = {
        "raw_answer": results,
        "human_readable": f"Data found: {results}"
    }

    return state

workflow.add_node("convert_nl_to_sql", convert_nl_to_sql)
workflow.add_node("execute_sql", execute_sql)
workflow.add_edge("convert_nl_to_sql", "execute_sql")
workflow.add_edge("execute_sql", END)
workflow.set_entry_point("convert_nl_to_sql")

