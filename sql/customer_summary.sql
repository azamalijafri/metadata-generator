SELECT 
    c.customer_id,
    c.customer_name,
    COUNT(o.order_id) AS total_orders,
    SUM(o.order_amount) AS total_spent,
    MAX(o.order_date) AS last_order_date
FROM 
    workspace.default.raw_customers c
LEFT JOIN 
    workspace.default.raw_orders o 
    ON c.customer_id = o.customer_id
GROUP BY 
    c.customer_id, 
    c.customer_name;