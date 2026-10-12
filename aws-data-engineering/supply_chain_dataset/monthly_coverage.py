from pathlib import Path
import sqlite3

import pandas as pd


BASE_DIR = Path(__file__).parent
CURATED_FILE = BASE_DIR / "data" / "curated" / "supply_chain_items.csv"
OUTPUT_FILE = BASE_DIR / "data" / "curated" / "monthly_coverage.csv"

df = pd.read_csv(
    CURATED_FILE,
    usecols=["order_date", "order_id"],
)

with sqlite3.connect(":memory:") as connection:
    df.to_sql("supply_chain_items", connection, index=False)

    query = """
    SELECT
        SUBSTR(order_date, 1, 7) AS order_month,
        COUNT(*) AS item_rows,
        COUNT(DISTINCT order_id) AS distinct_orders
    FROM supply_chain_items
    GROUP BY SUBSTR(order_date, 1, 7)
    ORDER BY order_month;
    """

    monthly = pd.read_sql_query(query, connection)

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
monthly.to_csv(OUTPUT_FILE, index=False)

print(monthly.to_string(index=False))
print(f"\nSaved: {OUTPUT_FILE}")