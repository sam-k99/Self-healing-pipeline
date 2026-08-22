import os
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from agent_tools import inspect_schema, read_dbt_file, write_dbt_file, run_dbt_tests, commit_and_push_fix

# Load your ZAI API key
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY", "your-api-key-here")

# Initialize the LLM using the OpenAI wrapper, but point it to ZAI's base URL
# (Replace the base_url with the actual ZAI endpoint if it's different)
llm = ChatOpenAI(
    model="openai/gpt-oss-120b",  # <--- CHANGE THIS
    temperature=0,
    openai_api_key=os.getenv("GROQ_API_KEY"),
    openai_api_base="https://api.groq.com/openai/v1"
)

# The list of tools the agent is allowed to use
tools = [
    inspect_schema,
    read_dbt_file,
    write_dbt_file,
    run_dbt_tests
    commit_and_push_fix
]


# The system prompt gives the AI its persona and strict rules
SYSTEM_PROMPT = """You are an elite Data Engineer AI agent. 
A dbt pipeline has broken because the upstream database schema changed.
Your job is to:
1. Inspect the live database to see the current column names.
2. Read the broken dbt SQL file to see what it expects.
3. Rewrite the dbt SQL file so the column names match the live database.
4. Run the dbt tests to verify your fix works.

Rules:
- ALWAYS inspect the database first.
- DO NOT drop or delete columns. If a column is missing, map it or cast it.
- If the tests fail, read the new error, inspect the schema again, and try to fix the SQL again.
- CRITICAL: When the tests pass, you MUST use the commit_and_push_fix tool to commit your fix and push it to GitHub. Do not just summarize; call the tool!
"""
# Create the ReAct (Reasoning + Acting) Agent
# create_react_agent handles the cyclical loop automatically. 
# It will call a tool, read the output, and decide if it needs to call another tool.
agent_executor = create_react_agent(llm, tools, messages_modifier=SYSTEM_PROMPT)

def run_agent():
    print("Agent starting up...")
    
    # The initial trigger/prompt for the agent
    error_log = "Database Error in model stg_orders: column 'order_amount' does not exist."
    initial_input = f"The dbt pipeline failed with this error: {error_log}. Please fix it."
    
        # Run the agent
    print("Agent is thinking...")
    response = agent_executor.invoke(
        {"messages": [("user", initial_input)]},
        {"recursion_limit": 50}  # <--- INCREASE LIMIT HERE
    )
    # Print the final message from the AI
    print("\n--- AGENT FINISHED ---")
    print(response["messages"][-1].content)

if __name__ == "__main__":
    run_agent()
