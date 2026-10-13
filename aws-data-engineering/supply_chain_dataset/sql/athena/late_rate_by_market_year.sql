SELECT
    d.year AS order_year,
    g.market,
    o.shipping_mode,
    COUNT(*) AS non_canceled_orders,
    SUM(CASE WHEN o.delivery_status = 'Late delivery' THEN 1 ELSE 0 END)
        AS late_orders,
    ROUND(
        100.0 * SUM(CASE WHEN o.delivery_status = 'Late delivery' THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0),
        1
    ) AS late_pct
FROM fact_orders AS o
JOIN dim_date AS d
    ON o.order_date_key = d.date_key
JOIN dim_geography AS g
    ON o.geography_key = g.geography_key
WHERE o.delivery_status <> 'Shipping canceled'
GROUP BY
    d.year,
    g.market,
    o.shipping_mode
ORDER BY
    d.year,
    g.market,
    o.shipping_mode;