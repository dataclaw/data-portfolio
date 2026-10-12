from pathlib import Path
import sqlite3

import pandas as pd


BASE_DIR = Path(__file__).parent
CURATED_FILE = BASE_DIR / "data" / "curated" / "supply_chain_items.csv"

df = pd.read_csv(
    CURATED_FILE,
    usecols=["order_id", "shipping_mode", "delivery_status"],
)

with sqlite3.connect(":memory:") as connection:
    df.to_sql("supply_chain_items", connection, index=False)

    conflicts = pd.read_sql_query(
        """
        SELECT COUNT(*) AS inconsistent_orders
        FROM (
            SELECT order_id
            FROM supply_chain_items
            GROUP BY order_id
            HAVING COUNT(DISTINCT shipping_mode) != 1
                OR COUNT(DISTINCT delivery_status) != 1
        );
        """,
        connection,
    ).loc[0, "inconsistent_orders"]

    if conflicts:
        raise ValueError(
            f"{conflicts} orders have multiple shipping modes "
            "or delivery statuses. Review those before counting orders."
        )

    query = """
    WITH orders AS (
        SELECT
            order_id,
            MIN(shipping_mode) AS shipping_mode,
            MIN(delivery_status) AS delivery_status
        FROM supply_chain_items
        GROUP BY order_id
    ),
    status_counts AS (
        SELECT
            shipping_mode,
            delivery_status,
            COUNT(*) AS distinct_orders
        FROM orders
        GROUP BY shipping_mode, delivery_status
    ),
    mode_totals AS (
        SELECT
            shipping_mode,
            SUM(distinct_orders) AS total_orders
        FROM status_counts
        GROUP BY shipping_mode
    )
    SELECT
        status_counts.shipping_mode,
        status_counts.delivery_status,
        status_counts.distinct_orders,
        ROUND(
            100.0 * status_counts.distinct_orders / mode_totals.total_orders,
            1
        ) AS pct_of_mode_orders
    FROM status_counts
    JOIN mode_totals USING (shipping_mode)
    ORDER BY shipping_mode, delivery_status;
    """

    results = pd.read_sql_query(query, connection)

print(results.to_string(index=False))