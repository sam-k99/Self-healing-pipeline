-- This model cleans the raw data
SELECT 
    order_id,
    user_id,
    order_amount,
    date_of_birth AS user_dob,
    created_at
FROM raw_orders