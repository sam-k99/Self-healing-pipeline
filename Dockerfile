# Use the official Airflow image as the base
FROM apache/airflow:2.9.2-python3.11

# Add the dbt-postgres adapter so Airflow can run dbt commands
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Switch back to the airflow user for security
USER airflow

# Copy our requirements file into the container
COPY requirements.txt /tmp/requirements.txt

# Install our Python dependencies
RUN pip install --no-cache-dir -r /tmp/requirements.txt
