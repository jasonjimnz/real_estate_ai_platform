# File Structure

* `config.py`: Handles Env vars & LLM instantiation.
* `sub_agents.py`: Defines the agents and wraps them as typed Tools.
* `main.py`: The Supervisor agent that calls the tools.

---

## 1. `config.py` (Rule 1: Env Vars & Local First)

```python
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load .env file
load_dotenv()

def get_llm(temperature: float = 0.0):
    """
    Returns an LLM instance based on environment variables.
    Default defaults to local inference if not specified.
    """
    base_url = os.getenv("LLM_BASE_URL", "http://localhost:1234/v1")
    api_key = os.getenv("LLM_API_KEY", "lm-studio") # Dummy key for local
    model_name = os.getenv("LLM_MODEL", "llama-3.2-3b-instruct")

    print(f"🔌 Connecting to LLM at: {base_url} (Model: {model_name})")

    return ChatOpenAI(
        base_url=base_url,
        api_key=api_key,
        model=model_name,
        temperature=temperature,
        streaming=True
    )

```

## 2. `sub_agents.py` (Rule 2 & 3: Agents as Pydantic Tools)

```python
from typing import Type
from pydantic import BaseModel, Field
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool, BaseTool

from config import get_llm

# --- defined simple tools for the sub-agent ---
@tool
def check_database_schema(table_name: str) -> str:
    """Checks the schema of a specific SQL table."""
    return f"Schema for {table_name}: [id: int, status: varchar, created_at: datetime]"

# --- Sub-Agent Definition ---

class SQLAgentInput(BaseModel):
    """Rule 3: Strict Pydantic Typing for the Supervisor"""
    natural_language_query: str = Field(
        description="The full query or request from the user that requires SQL knowledge."
    )

def create_sql_specialist_tool() -> BaseTool:
    """
    Rule 2: Wraps a Sub-Agent as a Tool.
    The parent sees this as a single function, but inside it runs an Agent loop.
    """
    
    # 1. Define the Sub-Agent's Brain
    llm = get_llm(temperature=0)
    tools = [check_database_schema]
    
    # Standard System Prompt (Rule 4: Standard format, no specialized tokens)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a SQL Specialist. Your job is to generate SQL queries. "
                   "You have access to tools to check schemas. "
                   "Do not execute DML statements (INSERT/DELETE). "
                   "Return only the final SQL or the answer."),
        ("user", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    # 2. Create the Agent
    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    # 3. Define the Wrapper Function
    def run_sql_agent(natural_language_query: str) -> str:
        try:
            response = agent_executor.invoke({"input": natural_language_query})
            return response["output"]
        except Exception as e:
            return f"SQL Agent failed: {str(e)}"

    # 4. Return as a LangChain Tool
    from langchain_core.tools import Tool
    return Tool(
        name="sql_specialist",
        func=run_sql_agent,
        description="Use this tool when you need to write SQL, check database schemas, or query data.",
        args_schema=SQLAgentInput # Enforces Pydantic
    )

```

## 3. `main.py` (The Supervisor)

```python
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from config import get_llm
from sub_agents import create_sql_specialist_tool

def main():
    # 1. Setup Local LLM
    llm = get_llm(temperature=0.1)

    # 2. Load Sub-Agents as Tools
    sql_tool = create_sql_specialist_tool()
    tools = [sql_tool]

    # 3. Supervisor Prompt
    # We use a generic 'tool_calling_agent' prompt structure which works with 
    # OpenAI-compatible local servers (Ollama/LM Studio).
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are the Main Supervisor. "
                   "You receive requests and delegate them to specialized tools. "
                   "If the request is about databases, use the 'sql_specialist'. "
                   "Always answer the user's question directly based on the tool output."),
        ("user", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    # 4. Create Supervisor
    agent = create_tool_calling_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    # 5. Run
    user_query = "I need to know the status of the users table."
    print(f"\nUser: {user_query}\n")
    
    result = executor.invoke({"input": user_query})
    
    print(f"\n🤖 Final Answer: {result['output']}")

if __name__ == "__main__":
    main()

```

## `.env` Example

```ini
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=ollama
LLM_MODEL=llama3.2

```