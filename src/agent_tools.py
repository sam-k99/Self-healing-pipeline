import psycopg2
import os
import subprocess
from datetime import datetime 

# Dynamically find the project root directory based on this file's location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
DBT_PROJECT_DIR = os.path.join(PROJECT_ROOT, "dbt_project")
STAGING_DIR = os.path.join(DBT_PROJECT_DIR, "models", "staging")
MARTS_DIR = os.path.join(DBT_PROJECT_DIR, "models", "marts")

# Tool 1: Inspect the database schema
def inspect_schema(table_name: str) -> str:
    """Connects to Postgres and returns the current column names of a table."""
    conn = psycopg2.connect(
        host="localhost",
        database="my_db",
        user="admin",
        password="password123",
        port="5432"
    )
    cursor = conn.cursor()
    cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}';")
    columns = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return f"The current columns in table '{table_name}' are: {', '.join(columns)}"

# Tool 2: Read the broken dbt file
def read_dbt_file(model_name: str) -> str:
    """Reads the SQL code from a dbt model file."""
    # Check staging first, then marts
    file_path = os.path.join(STAGING_DIR, f"{model_name}.sql")
    if not os.path.exists(file_path):
        file_path = os.path.join(MARTS_DIR, f"{model_name}.sql")
        
    if not os.path.exists(file_path):
        return f"Error: Could not find file for model {model_name}"
        
    with open(file_path, 'r') as file:
        content = file.read()
    return f"Current SQL code in {model_name}.sql:\n{content}"

# Tool 3: Write the fixed dbt file
def write_dbt_file(model_name: str, new_sql: str) -> str:
    """Overwrites the SQL file with the new fixed code."""
    file_path = os.path.join(STAGING_DIR, f"{model_name}.sql")
    if not os.path.exists(file_path):
        file_path = os.path.join(MARTS_DIR, f"{model_name}.sql")
        
    with open(file_path, 'w') as file:
        file.write(new_sql)
    return f"Successfully wrote new SQL code to {model_name}.sql"

# Tool 4: Run dbt tests to verify the fix
def run_dbt_tests() -> str:
    """Runs dbt test and returns the output so the AI knows if it passed or failed."""
    try:
        result = subprocess.run(
            ["dbt", "test", "--profiles-dir", "."], 
            cwd=DBT_PROJECT_DIR,  # Use the absolute path here
            capture_output=True, 
            text=True
        )
        output = result.stdout[-1500:] if result.stdout else result.stderr[-1500:]
        return f"dbt test output:\n{output}"
    except Exception as e:
        return f"Failed to run dbt test: {str(e)}"


# Tool 5: Commit the fix and push to GitHub
def commit_and_push_fix(model_name: str, fix_description: str) -> str:
    """Commits the fixed SQL file to a new git branch and pushes it to GitHub."""
    try:
        # Create a unique branch name
        branch_name = f"agent-fix/{model_name}-{int(datetime.now().timestamp())}"
        
        # 1. Create and checkout the new branch
        subprocess.run(["git", "checkout", "-b", branch_name], cwd=PROJECT_ROOT, check=True)
        
        # 2. Stage the fixed file
        file_path = os.path.join(STAGING_DIR, f"{model_name}.sql")
        if not os.path.exists(file_path):
            file_path = os.path.join(MARTS_DIR, f"{model_name}.sql")
            
        subprocess.run(["git", "add", file_path], cwd=PROJECT_ROOT, check=True)
        
        # 3. Commit the changes
        subprocess.run(["git", "commit", "-m", fix_description], cwd=PROJECT_ROOT, check=True)
        
        # 4. Push the branch to GitHub
        subprocess.run(["git", "push", "-u", "origin", branch_name], cwd=PROJECT_ROOT, check=True)
        
        return f"Success! Pushed fix to branch {branch_name}. A human reviewer can now open a Pull Request."
    except subprocess.CalledProcessError as e:
        return f"Git command failed: {str(e)}. Make sure you have a GitHub remote set up and configured."
