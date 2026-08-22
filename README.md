# Self Healing Data Pipeline

## Overview
This project implements an autonomous AI agent designed to detect, diagnose, and resolve data pipeline failures caused by upstream schema drift. When a database schema changes unexpectedly (e.g., column renaming or type alterations), standard dbt pipelines crash. This system uses a LangGraph ReAct agent to inspect the live database, rewrite the broken SQL models, verify the fix via dbt tests, and automatically push the corrected code to a new Git branch for human review.

## The Problem
Data pipelines are highly fragile. A common scenario in enterprise data engineering is "schema drift"—when an upstream API or database alters its structure without coordinating with downstream consumers. When this happens, Extract, Load, Transform (ELT) pipelines fail, requiring manual intervention from data engineers to read error logs, trace the schema change, rewrite SQL, and open a Pull Request. This manual toil can take hours, during which dashboards and downstream models are broken.

## The Solution
Instead of relying on manual intervention, this system employs an autonomous AI agent. When the dbt pipeline fails, the agent is triggered. It enters a cyclical reasoning loop (ReAct) where it uses custom Python tools to interact directly with PostgreSQL, the local file system, and the command line. It maps the new database schema to the existing SQL expectations, writes the fix, validates it, and handles the Git operations autonomously.

## Tech Stack
* **Database:** PostgreSQL 15
* **Transformation:** dbt (Data Build Tool)
* **Orchestration:** Apache Airflow
* **AI/Agentic Framework:** LangGraph, LangChain
* **LLM Integration:** OpenAI-compatible APIs (Tested with Groq: Llama-3.3-70b / GPT-4o)
* **Infrastructure:** Docker, Docker Compose
* **Version Control:** Git (Automated GitOps)

## Architecture Flow
1. **Ingestion:** A Python script generates mock e-commerce data and loads it into a `raw_orders` table in PostgreSQL.
2. **Transformation & Testing:** dbt runs staging (`stg_orders`) and mart (`mart_revenue`) models. It executes data quality tests (`not_null`, `unique`) to validate the pipeline.
3. **Sabotage (Simulated Drift):** A script intentionally alters the `raw_orders` schema (e.g., `ALTER TABLE raw_orders RENAME COLUMN order_amount TO total_amount`).
4. **Failure & Trigger:** The subsequent dbt run fails. The error log is passed to the AI Agent.
5. **Agentic Loop (LangGraph):**
   * **Inspect:** The agent queries `information_schema.columns` to see the current database state.
   * **Read:** The agent reads the failing `.sql` file from the local filesystem.
   * **Write:** The agent rewrites the SQL to alias the new schema to the expected schema (e.g., `SELECT total_amount AS order_amount`).
   * **Test:** The agent executes `dbt test`. If it fails, it loops back to Inspect. If it passes, it proceeds.
6. **GitOps Finish:** The agent creates an isolated Git branch, commits the fixed `.sql` file, and pushes it to GitHub, generating a Pull Request for human review.

## Project Structure
```text
self-healing-pipeline/
├── docker-compose.yml       # Docker services for Postgres and Airflow
├── Dockerfile               # Custom Airflow image with dbt installed
├── requirements.txt         # Python dependencies
├── demo.py                  # One-click script to run the full break/fix cycle
├── init/
│   └── init.sql             # Postgres initialization script (creates raw table)
├── src/
│   ├── data_generator.py    # Generates mock data using Faker
│   ├── schema_breaker.py    # Simulates upstream schema drift
│   ├── agent_tools.py       # Python functions the AI uses to interact with the system
│   └── agent.py             # LangGraph ReAct agent initialization and execution
└── dbt_project/
    ├── dbt_project.yml      # dbt configuration
    ├── profiles.yml         # dbt database connection profile
    └── models/
        ├── staging/
        │   ├── stg_orders.sql  # Target model for AI fixes
        │   └── schema.yml      # dbt tests
        └── marts/
            └── mart_revenue.sql
```

## Setup and Installation

### Prerequisites
* Docker and Docker Compose
* Python 3.10+ and `venv`
* An OpenAI-compatible API key (e.g., Groq, OpenAI, Zhipu AI)

### 1. Environment Configuration
Clone the repository and create a `.env` file in the root directory:
```env
POSTGRES_USER=admin
POSTGRES_PASSWORD=(whatever you password is)
POSTGRES_DB=my_db
AIRFLOW_UID=1000
OPENAI_API_KEY=your_api_key_here
```

### 2. Python Environment
Create and activate a virtual environment, then install dependencies:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Infrastructure Setup
Start the PostgreSQL and Airflow containers. The `init.sql` script will automatically create the `raw_orders` table on first startup.
```bash
docker compose up -d
```

### 4. dbt Configuration
Ensure `dbt_project/profiles.yml` points to your local Docker container:
```yaml
dbt_project:
  outputs:
    dev:
      type: postgres
      host: localhost
      user: admin
      password: (whatever you password is)
      port: 5432
      dbname: my_db
      schema: public
      threads: 1
  target: dev
```

## Usage

### Running the One-Click Demo
The `demo.py` script automates the entire process: it resets the environment, generates data, runs dbt, sabotages the schema, and triggers the AI agent.

```bash
export OPENAI_API_KEY="your_api_key_here"
python demo.py
```

### Expected Output
1. The script resets `stg_orders.sql` to its clean state.
2. Docker containers are wiped and rebuilt to ensure a pristine database.
3. Mock data is generated and dbt tests pass.
4. The `schema_breaker.py` alters the database schema.
5. `agent.py` executes. The AI will output its reasoning, call the tools to inspect the database, rewrite the SQL, and run the tests.
6. Upon success, the AI creates a Git branch and pushes the fix.

### Reviewing the Fix
After the script completes, check your local Git branches or your GitHub repository. The AI will have pushed a branch named similarly to `agent-fix/stg_orders-<timestamp>`. Review the commit to see the AI-generated SQL fix.

## Engineering Decisions
* **LangGraph for Cyclical Logic:** Standard LLM chains are linear. Data engineering requires trial and error. LangGraph allows the agent to loop: if the `run_dbt_tests` tool fails, the agent reads the new error, loops back to the rewrite phase, and tries again.
* **Idempotent Infrastructure:** The `demo.py` script uses `docker compose down -v` to completely wipe the database volume on every run. This guarantees zero state drift between test runs, ensuring the saboteur always breaks a clean schema.
* **Human-in-the-Loop (HITL):** The AI does not push directly to `main`. It creates an isolated branch and pushes that. This adheres to enterprise GitOps standards, ensuring a human reviews the AI's logic before it affects production data.
