<div align="center"> <img src="assets/shp.png" alt="SHP Logo" width="220"> </div>

# Self-Healing Data Pipeline

An autonomous data engineering system that detects upstream schema drift, diagnoses broken dbt models, and repairs them without human intervention — then opens a Pull Request so a human stays in the loop before anything reaches production.

Built with **PostgreSQL**, **dbt**, **LangGraph**, and **Airflow**, this project demonstrates what an agentic response to pipeline failure looks like in practice: not an alert that pages an engineer at 2 AM, but a system that investigates its own failure, proposes a fix, verifies the fix against real tests, and hands off a reviewable artifact.

---

## Table of Contents

- [Why This Exists](#why-this-exists)
- [How It Works](#how-it-works)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Setup and Installation](#setup-and-installation)
- [Usage](#usage)
- [Reviewing the Fix](#reviewing-the-fix)
- [Engineering Decisions](#engineering-decisions)
- [Roadmap](#roadmap)
- [License](#license)

---

## Why This Exists

Schema drift is one of the most common and most disruptive failure modes in analytics engineering. An upstream team renames a column, a source system changes its export format, or an API contract shifts silently — and downstream dbt models break, tests fail, and dashboards go stale until someone manually traces the error back to its root cause.

This project simulates that entire failure-and-recovery cycle end to end, with an AI agent standing in for the on-call engineer's first response: inspect the schema, understand the discrepancy, patch the SQL, and prove the patch works before ever touching `main`.

## How It Works

The pipeline runs through six coordinated stages, from data generation to a reviewable Git branch:

| Stage | Description |
|---|---|
| **1. Ingestion** | A Python script generates mock e-commerce data and loads it into a `raw_orders` table in PostgreSQL. |
| **2. Transformation & Testing** | dbt runs staging (`stg_orders`) and mart (`mart_revenue`) models, executing `not_null` and `unique` tests to validate the pipeline. |
| **3. Sabotage (Simulated Drift)** | A script intentionally alters the `raw_orders` schema — for example, renaming `order_amount` to `total_amount` — to simulate an upstream breaking change. |
| **4. Failure & Trigger** | The next dbt run fails. The resulting error log is passed to the AI agent as its starting context. |
| **5. Agentic Loop (LangGraph)** | The agent inspects, reads, rewrites, and tests in a closed loop until the fix passes. |
| **6. GitOps Finish** | The agent commits the fix to an isolated branch and opens a Pull Request for human review. |

### The Agentic Loop in Detail

The core of the system is a LangGraph-orchestrated ReAct agent that cycles through four actions:

1. **Inspect** — Queries `information_schema.columns` to see the database's current, actual state.
2. **Read** — Loads the failing `.sql` file from the local filesystem to understand what the model expects.
3. **Write** — Rewrites the SQL to reconcile the mismatch, for example aliasing the new column name back to the expected one (`SELECT total_amount AS order_amount`).
4. **Test** — Runs `dbt test` against the change. A failure sends the agent back to **Inspect**; a pass moves the workflow forward to the GitOps stage.

This loop is what separates the system from a simple find-and-replace script: the agent reasons over real error output and real schema state, and it only stops once its fix is empirically verified.

## Project Structure

```text
self-healing-pipeline/
├── docker-compose.yml       # Docker services for Postgres and Airflow
├── Dockerfile                # Custom Airflow image with dbt installed
├── requirements.txt          # Python dependencies
├── demo.py                   # One-click script to run the full break/fix cycle
├── init/
│   └── init.sql               # Postgres initialization script (creates raw table)
├── src/
│   ├── data_generator.py      # Generates mock data using Faker
│   ├── schema_breaker.py      # Simulates upstream schema drift
│   ├── agent_tools.py         # Python functions the AI uses to interact with the system
│   └── agent.py                # LangGraph ReAct agent initialization and execution
└── dbt_project/
    ├── dbt_project.yml        # dbt configuration
    ├── profiles.yml            # dbt database connection profile
    └── models/
        ├── staging/
        │   ├── stg_orders.sql  # Target model for AI fixes
        │   └── schema.yml      # dbt tests
        └── marts/
            └── mart_revenue.sql
```

## Prerequisites

- Docker and Docker Compose
- Python 3.10+ and `venv`
- An OpenAI-compatible API key (OpenAI, Groq, Zhipu AI, or similar)

## Setup and Installation

### 1. Environment Configuration

Clone the repository and create a `.env` file in the root directory:

```env
POSTGRES_USER=admin
POSTGRES_PASSWORD=your_secure_password
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

Start the PostgreSQL and Airflow containers. The `init.sql` script automatically creates the `raw_orders` table on first startup.

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
      password: your_secure_password
      port: 5432
      dbname: my_db
      schema: public
      threads: 1
  target: dev
```

## Usage

### Running the One-Click Demo

The `demo.py` script automates the entire cycle: it resets the environment, generates data, runs dbt, sabotages the schema, and triggers the AI agent.

```bash
export OPENAI_API_KEY="your_api_key_here"
python demo.py
```

### Expected Output

1. The script resets `stg_orders.sql` to its clean state.
2. Docker containers are wiped and rebuilt to ensure a pristine database.
3. Mock data is generated and the initial dbt run passes cleanly.
4. `schema_breaker.py` alters the database schema, simulating upstream drift.
5. `agent.py` executes: the agent reasons aloud, inspects the database, rewrites the SQL, and reruns the tests.
6. Upon success, the agent creates a Git branch and pushes the fix.

## Reviewing the Fix

After the script completes, check your local Git branches or your GitHub repository. The agent will have pushed a branch named similarly to:

```text
agent-fix/stg_orders-<timestamp>
```

Open the associated Pull Request to review the AI-generated SQL fix, its reasoning trail, and the passing test output before merging.

## Engineering Decisions

**LangGraph for cyclical logic.** Standard LLM chains are linear and cannot recover from their own mistakes. Data engineering fixes are inherently iterative — LangGraph lets the agent loop: if `run_dbt_tests` fails, the agent reads the new error, returns to the rewrite phase, and tries again until it converges on a working fix.

**Idempotent infrastructure.** `demo.py` runs `docker compose down -v` to fully wipe the database volume on every execution. This guarantees zero state drift between runs, so the saboteur always breaks a known-clean schema and every demo run is reproducible.

**Human-in-the-loop (HITL).** The agent never pushes directly to `main`. It commits to an isolated branch and opens a Pull Request instead, following standard enterprise GitOps practice — a human always reviews the agent's reasoning and diff before it can affect production data.

## Roadmap

Ideas for extending this project further:

- Support for additional drift scenarios beyond column renames (type changes, dropped columns, new required fields)
- Slack or email notifications when the agent opens a Pull Request
- A dashboard visualizing the agent's reasoning trail and historical fix success rate
- Support for additional warehouses beyond PostgreSQL (Snowflake, BigQuery)


<div align="center">

Thanks for stopping by <img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Animals/Cat.png" alt="Cat" width="32" height="32" />

