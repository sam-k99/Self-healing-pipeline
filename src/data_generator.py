import psycopg2
from faker import Faker
import random
from datetime import datetime

fake = Faker()

def generate_and_load_data():
    conn = psycopg2.connect(
        host="localhost",
        database="my_db",
        user="admin",
        password="password123",
        port="5432"
    )

    cursor = conn.cursor()

    for _ in range(5):
        order_id = fake.uuid4()
        user_id = fake.uuid4()
        order_amount = round(random.uniform(10.0, 500.0), 2)
        user_dob = fake.date_of_birth().isoformat()
        created_at = datetime.now()
        
        insert_query = """
        INSERT INTO raw_orders (order_id, user_id, order_amount, user_dob, created_at)
        VALUES (%s, %s, %s, %s, %s);
        """
        
        cursor.execute(insert_query, (order_id, user_id, order_amount, user_dob, created_at))
        conn.commit()

    print("Successfully inserted 5 fake orders into raw_orders!")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    generate_and_load_data()
