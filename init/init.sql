CREATE TABLE IF NOT EXISTS raw_orders (
    order_id VARCHAR PRIMARY KEY,
    user_id VARCHAR,
    order_amount NUMERIC(10, 2),
    user_dob DATE,
    created_at TIMESTAMP
);
