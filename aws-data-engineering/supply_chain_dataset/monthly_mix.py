from pathlib import Path
import sqlite3

import pandas as pd


BASE_DIR = Path(__file__).parent
CURATED_FILE = BASE_DIR / "data" / "curated" / "supply_chain_items.csv"

df = pd.read_csv(
    CURATED_FILE,
    usecols=[
        "order_date",
        "order_id",
        "order_status",
        "market",
        "shipping_mode",
    ],
)

with sqlite3.connect(":memory:") as connection:
    df.to_sql("supply_chain_items", connection, index=False)

    for column in ["order_status", "market", "shipping_mode"]:
        query = f"""
        SELECT
            SUBSTR(order_date, 1, 7) AS order_month,
            {column} AS group_value,
            COUNT(*) AS item_rows,
            COUNT(DISTINCT order_id) AS distinct_orders
        FROM supply_chain_items
        WHERE SUBSTR(order_date, 1, 7) BETWEEN '2017-08' AND '2018-01'
        GROUP BY order_month, group_value
        ORDER BY order_month, group_value;
        """

        print(f"\nBy {column.replace('_', ' ')}:")
        print(pd.read_sql_query(query, connection).to_string(index=False))