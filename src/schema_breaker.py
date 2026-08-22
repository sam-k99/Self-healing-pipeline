import psycopg2
import random

def break_schema():
    # Connect to the database using the hardcoded password we just confirmed works
    conn = psycopg2.connect(
        host="localhost",
        database="my_db",
        user="admin",
        password="password123",
        port="5432"
    )
    cursor = conn.cursor()

    # List of evil things to do to a database schema
    sabotage_options = [
        "ALTER TABLE raw_orders RENAME COLUMN user_dob TO date_of_birth;",
        "ALTER TABLE raw_orders RENAME COLUMN order_amount TO total_amount;",
        "ALTER TABLE raw_orders DROP COLUMN user_dob;",
        "ALTER TABLE raw_orders ALTER COLUMN order_amount TYPE TEXT USING order_amount::TEXT;"
    ]

    # Pick a random sabotage tactic
    sabotage_query = random.choice(sabotage_options)
    
    try:
        cursor.execute(sabotage_query)
        conn.commit()
        print(f"\n SABOTAGE SUCCESSFUL: Executed -> {sabotage_query}\n")
    except Exception as e:
        print(f"\n Sabotage failed (maybe it was already broken?): {e}\n")
        conn.rollback()

    cursor.close()
    conn.close()

if __name__ == "__main__":
    break_schema()
