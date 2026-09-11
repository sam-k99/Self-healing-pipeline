<div align="center">
  <img src="assets/shp.png" alt="SHP Logo" width="220">
</div>

<h1 align="center">Self-Healing Data Pipeline</h1>

<p align="center">
An autonomous data engineering system that detects upstream schema drift, diagnoses broken dbt models, and repairs them without human intervention — then opens a Pull Request so a human stays in the loop before anything reaches production.
</p>

<p align="center">
Built with <b>PostgreSQL</b>, <b>dbt</b>, <b>LangGraph</b>, and <b>Airflow</b> — an agentic response to pipeline failure that investigates its own errors, proposes a fix, verifies it against real tests, and hands off a reviewable artifact.
</p>

<br>

| ![Agent Reasoning](assets/preview1.png) | ![Pull Request](assets/preview2.png) |
|---|---|

<br>

## Features

- **Fully autonomous recovery** — no manual triage, the agent investigates and fixes on its own
- **Closed-loop verification** — every fix is proven against real `dbt test` runs before it ships
- **Schema-aware reasoning** — the agent inspects `information_schema` directly, not guesswork
- **GitOps-native** — isolated branches and Pull Requests, never a direct push to `main`
- **Reproducible by design** — idempotent Docker infrastructure, zero state drift between runs
- **One-command demo** — the entire break/fix cycle runs end to end with a single script
- **Model-agnostic** — works with any OpenAI-compatible API (OpenAI, Groq, Zhipu AI)

<br>

## Components

| Component | Tool |
|---|---|
| Orchestration | [Airflow](https://airflow.apache.org/) |
| Transformation & Testing | [dbt](https://www.getdbt.com/) |
| Database | PostgreSQL |
| Agentic Reasoning | [LangGraph](https://www.langchain.com/langgraph) (ReAct agent) |
| Data Generation | Python + Faker |
| Version Control | Git / GitHub (automated PRs) |
| Runtime | Docker & Docker Compose |

<br>

## Requirements

- Docker and Docker Compose
- Python 3.10+ and `venv`
- An OpenAI-compatible API key (OpenAI, Groq, Zhipu AI, or similar)

<details>
<summary><b>Full dependency list (click to expand)</b></summary>

```bash
# Python packages (requirements.txt)
langgraph
langchain
langchain-openai
dbt-postgres
psycopg2-binary
faker
python-dotenv
GitPython
PyGithub
```

</details>

<br>

## Installation

> Back up any existing `.env` or local configs before you start.

```bash
# Clone the repo
git clone https://github.com/your-username/self-healing-pipeline.git
cd self-healing-pipeline

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

Then set up your `.env` file:

```env
POSTGRES_USER=admin
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=my_db
AIRFLOW_UID=1000
OPENAI_API_KEY=your_api_key_here
```

<details>
<summary><b>Infrastructure & dbt setup (click to expand)</b></summary>

Start the PostgreSQL and Airflow containers. The `init.sql` script automatically creates the `raw_orders` table on first startup.

```bash
docker compose up -d
```

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

</details>

<br>

## Usage

The `demo.py` script automates the entire cycle: it resets the environment, generates data, runs dbt, sabotages the schema, and triggers the AI agent.

```bash
export OPENAI_API_KEY="your_api_key_here"
python demo.py
```

**What happens, step by step:**

1. `stg_orders.sql` is reset to its clean state
2. Docker containers are wiped and rebuilt for a pristine database
3. Mock data is generated and the initial dbt run passes cleanly
4. `schema_breaker.py` alters the schema, simulating upstream drift
5. `agent.py` runs: it reasons aloud, inspects the database, rewrites the SQL, and reruns the tests
6. On success, the agent creates a Git branch and pushes the fix

<br>

## How It Works

The core of the system is a LangGraph-orchestrated ReAct agent that cycles through four actions until its fix is verified:

| Step | Action |
|---|---|
| Inspect | Queries `information_schema.columns` to see the database's current, actual state |
| Read | Loads the failing `.sql` file to understand what the model expects |
| Write | Rewrites the SQL to reconcile the mismatch (e.g. `SELECT total_amount AS order_amount`) |
| Test | Runs `dbt test` — a failure loops back to Inspect, a pass moves on to GitOps |

This loop is what separates the system from a simple find-and-replace script: the agent reasons over real error output and real schema state, and only stops once its fix is empirically verified.

<br>

## Reviewing the Fix

After the script completes, check your local Git branches or your GitHub repository. The agent will have pushed a branch named similarly to:

```text
agent-fix/stg_orders-<timestamp>
```

Open the associated Pull Request to review the AI-generated SQL fix, its reasoning trail, and the passing test output before merging.

<br>

## Repository Structure

```
self-healing-pipeline/
├── assets/              # Screenshots and preview images
├── init/                # Postgres initialization script
├── src/                 # Data generator, schema breaker, agent tools, agent
├── dbt_project/         # dbt models, staging, marts, tests
├── docker-compose.yml   # Postgres and Airflow services
├── Dockerfile           # Custom Airflow image with dbt installed
├── requirements.txt     # Python dependencies
├── demo.py              # One-click break/fix demo
└── README.md
```

<br>

## Design Decisions

- **LangGraph for cyclical logic** — standard LLM chains are linear and can't recover from their own mistakes; LangGraph lets the agent loop until its fix converges
- **Idempotent infrastructure** — `docker compose down -v` wipes the database volume on every run, guaranteeing zero state drift between demos
- **Human-in-the-loop** — the agent never pushes to `main`; it opens a Pull Request so a human always reviews the logic before it touches production data

<br>

## Roadmap

- Support for additional drift scenarios beyond column renames (type changes, dropped columns, new required fields)
- Slack or email notifications when the agent opens a Pull Request
- A dashboard visualizing the agent's reasoning trail and historical fix success rate
- Support for additional warehouses beyond PostgreSQL (Snowflake, BigQuery)

<br>

## Contributing

Found a bug or have an idea to make this pipeline smarter?

1. Fork the repo
2. Create your branch (`git checkout -b feature/amazing-idea`)
3. Commit your changes (`git commit -m 'add amazing idea'`)
4. Push and open a Pull Request

<br>

## Show Some Love

If this project helped you understand agentic data engineering, consider dropping a **star** — it helps others find it too.

<div align="center">

Thanks for stopping by.

</div>
