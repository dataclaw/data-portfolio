from pathlib import Path
import sqlite3

import pandas as pd


BASE_DIR = Path(__file__).parent
CURATED_FILE = BASE_DIR / "data" / "curated" / "supply_chain_items.csv"
OUTPUT_FILE = BASE_DIR / "data" / "curated" / "delivery_kpis_by_mode.csv"

df = pd.read_csv(
    CURATED_FILE,
    usecols=["order_id", "shipping_mode", "delivery_status"],
)

with sqlite3.connect(":memory:") as connection:
    df.to_sql("supply_chain_items", connection, index=False)

    query = """
    WITH orders AS (
        SELECT
            order_id,
            MIN(shipping_mode) AS shipping_mode,
            MIN(delivery_status) AS delivery_status
        FROM supply_chain_items
        GROUP BY order_id
    ),
    mode_counts AS (
        SELECT
            shipping_mode,
            COUNT(*) AS total_orders,
            SUM(CASE WHEN delivery_status = 'Shipping canceled'
                     THEN 1 ELSE 0 END) AS canceled_orders,
            SUM(CASE WHEN delivery_status = 'Late delivery'
                     THEN 1 ELSE 0 END) AS late_orders,
            SUM(CASE WHEN delivery_status = 'Shipping on time'
                     THEN 1 ELSE 0 END) AS on_time_orders,
            SUM(CASE WHEN delivery_status = 'Advance shipping'
                     THEN 1 ELSE 0 END) AS advance_orders
        FROM orders
        GROUP BY shipping_mode
    )
    SELECT
        shipping_mode,
        total_orders,
        canceled_orders,
        ROUND(100.0 * canceled_orders / total_orders, 1)
            AS canceled_pct,
        late_orders,
        on_time_orders,
        advance_orders,
        total_orders - canceled_orders AS non_canceled_orders,
        ROUND(
            100.0 * late_orders / (total_orders - canceled_orders),
            1
        ) AS late_pct_of_non_canceled
    FROM mode_counts
    ORDER BY shipping_mode;
    """

    results = pd.read_sql_query(query, connection)

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
results.to_csv(OUTPUT_FILE, index=False)

print(results.to_string(index=False))
print(f"\nSaved: {OUTPUT_FILE}")