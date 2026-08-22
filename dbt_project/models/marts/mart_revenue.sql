-- This model aggregates the clean data to find daily revenue
SELECT 
    DATE(created_at) as order_date,
    SUM(order_amount) as total_revenue,
    COUNT(order_id) as total_orders
FROM {{ ref('stg_orders') }}
GROUP BY 1
