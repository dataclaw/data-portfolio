WITH rates AS (
    SELECT
        d.year AS order_year,
        g.market,
        o.shipping_mode,
        COUNT(*) AS non_canceled_orders,
        SUM(CASE WHEN o.delivery_status = 'Late delivery' THEN 1 ELSE 0 END)
            AS late_orders,
        1.0 * SUM(CASE WHEN o.delivery_status = 'Late delivery' THEN 1 ELSE 0 END)
            / COUNT(*) AS late_rate
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
    HAVING COUNT(*) >= 100
),
ranked AS (
    SELECT
        *,
        RANK() OVER (
            PARTITION BY order_year
            ORDER BY late_rate DESC
        ) AS late_rate_rank
    FROM rates
)
SELECT
    order_year,
    market,
    shipping_mode,
    non_canceled_orders,
    late_orders,
    ROUND(100.0 * late_rate, 1) AS late_pct,
    late_rate_rank
FROM ranked
WHERE late_rate_rank <= 5
ORDER BY order_year, late_rate_rank, market, shipping_mode;