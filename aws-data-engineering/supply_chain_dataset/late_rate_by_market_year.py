from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).parent
CURATED_FILE = BASE_DIR / "data" / "curated" / "supply_chain_items.csv"
OUTPUT_FILE = BASE_DIR / "data" / "curated" / "late_rate_by_market_year.csv"

df = pd.read_csv(
    CURATED_FILE,
    usecols=[
        "order_date",
        "order_id",
        "market",
        "shipping_mode",
        "delivery_status",
    ],
)

# Check each order has one year, market, mode, and delivery status.
consistency = df.groupby("order_id").agg(
    years=("order_date", lambda values: values.str[:4].nunique()),
    markets=("market", "nunique"),
    shipping_modes=("shipping_mode", "nunique"),
    delivery_statuses=("delivery_status", "nunique"),
)
if (consistency > 1).any().any():
    raise ValueError("Some orders have inconsistent grouping fields.")

orders = df.drop_duplicates("order_id").copy()
orders["order_year"] = orders["order_date"].str[:4]
orders = orders[orders["delivery_status"] != "Shipping canceled"]

summary = (
    orders.groupby(["order_year", "market", "shipping_mode"])
    .agg(
        non_canceled_orders=("order_id", "size"),
        late_orders=(
            "delivery_status",
            lambda statuses: (statuses == "Late delivery").sum(),
        ),
    )
    .reset_index()
)

summary["late_pct"] = (
    100 * summary["late_orders"] / summary["non_canceled_orders"]
).round(1)

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
summary.to_csv(OUTPUT_FILE, index=False)

print(summary.to_string(index=False))
print(f"\nSaved: {OUTPUT_FILE}")