import subprocess
import time
import os

# The clean SQL state that we want to reset to
CLEAN_SQL = """-- This model cleans the raw data
SELECT 
    order_id,
    user_id,
    order_amount,
    user_dob,
    created_at
FROM raw_orders
"""

def run_command(command, cwd=None):
    """Helper function to run shell commands and print them."""
    print(f"\n> {' '.join(command)}")
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr and "Error" not in result.stderr and "error" not in result.stderr:
        # Print warnings/info but don't stop script for standard docker/dbt output
        pass
    elif result.returncode != 0 and "dbt test" not in command:
        print("Command failed, but continuing demo sequence...")
    return result

def main():
    print("STARTING ONE-CLICK DEMO SEQUENCE...")

    # 1. Reset local dbt file
    print("\n--- Resetting stg_orders.sql to clean state ---")
    sql_path = os.path.join("dbt_project", "models", "staging", "stg_orders.sql")
    with open(sql_path, "w") as f:
        f.write(CLEAN_SQL)
    print("✅ SQL file reset.")

    # 2. Nuke Docker environment
    print("\n--- Wiping Docker Database ---")
    run_command(["docker", "compose", "down", "-v"])
    
    # 3. Start fresh Docker environment
    print("\n--- Spinning up fresh Database & Airflow ---")
    run_command(["docker", "compose", "up", "-d"])
    
    # 4. Wait for Postgres to initialize
    print("\n--- Waiting 5 seconds for Postgres to boot ---")
    time.sleep(5)

    # 5. Generate fake data
    print("\n--- Generating Fake Data ---")
    run_command(["python", "src/data_generator.py"])

    # 6. Run dbt (should pass)
    print("\n--- Running dbt (Proving it works) ---")
    run_command(["dbt", "run", "--profiles-dir", "."], cwd="dbt_project")
    run_command(["dbt", "test", "--profiles-dir", "."], cwd="dbt_project")

    # 7. Sabotage the pipeline!
    print("\n--- SABOTEUR ACTIVATED ---")
    run_command(["python", "src/schema_breaker.py"])

    # 8. Run the AI Agent to fix it!
    print("\n---  AI AGENT WAKING UP ---")
    run_command(["python", "src/agent.py"])

    print("\n DEMO SEQUENCE COMPLETE. Check GitHub for the Pull Request!")

if __name__ == "__main__":
    main()
