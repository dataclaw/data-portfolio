from pathlib import Path
import sqlite3

import pandas as pd


BASE_DIR = Path(__file__).parent
CURATED_FILE = BASE_DIR / "data" / "curated" / "supply_chain_items.csv"

df = pd.read_csv(
    CURATED_FILE,
    usecols=["shipping_mode", "delivery_status"],
)

with sqlite3.connect(":memory:") as connection:
    df.to_sql("supply_chain_items", connection, index=False)

    query = """
    WITH status_counts AS (
        SELECT
            shipping_mode,
            delivery_status,
            COUNT(*) AS item_rows
        FROM supply_chain_items
        GROUP BY shipping_mode, delivery_status
    ),
    mode_totals AS (
        SELECT
            shipping_mode,
            SUM(item_rows) AS total_item_rows
        FROM status_counts
        GROUP BY shipping_mode
    )
    SELECT
        status_counts.shipping_mode,
        status_counts.delivery_status,
        status_counts.item_rows,
        ROUND(
            100.0 * status_counts.item_rows / mode_totals.total_item_rows,
            1
        ) AS pct_of_mode_item_rows
    FROM status_counts
    JOIN mode_totals USING (shipping_mode)
    ORDER BY shipping_mode, delivery_status;
    """

    results = pd.read_sql_query(query, connection)

print(results.to_string(index=False))