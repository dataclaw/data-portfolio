WITH order_counts AS (
    SELECT
        shipping_mode,
        COUNT(*) AS total_orders,
        SUM(CASE WHEN delivery_status = 'Shipping canceled' THEN 1 ELSE 0 END)
            AS canceled_orders,
        SUM(CASE WHEN delivery_status = 'Late delivery' THEN 1 ELSE 0 END)
            AS late_orders,
        SUM(CASE WHEN delivery_status = 'Shipping on time' THEN 1 ELSE 0 END)
            AS on_time_orders,
        SUM(CASE WHEN delivery_status = 'Advance shipping' THEN 1 ELSE 0 END)
            AS advance_orders
    FROM fact_orders
    GROUP BY shipping_mode
)
SELECT
    shipping_mode,
    total_orders,
    canceled_orders,
    late_orders,
    on_time_orders,
    advance_orders,
    ROUND(
        100.0 * late_orders
        / NULLIF(total_orders - canceled_orders, 0),
        1
    ) AS late_pct_of_non_canceled
FROM order_counts
ORDER BY shipping_mode;