from pathlib import Path
from math import erfc, exp, pi, sqrt

import pandas as pd


BASE_DIR = Path(__file__).parent
CURATED_FILE = BASE_DIR / "data" / "curated" / "supply_chain_items.csv"

df = pd.read_csv(
    CURATED_FILE,
    usecols=["order_id", "shipping_mode", "delivery_status"],
)

# Confirm each order has one shipping mode and delivery status.
consistency = df.groupby("order_id").agg(
    shipping_modes=("shipping_mode", "nunique"),
    delivery_statuses=("delivery_status", "nunique"),
)
if (consistency > 1).any().any():
    raise ValueError("Some orders have inconsistent mode or delivery status.")

# Keep one row per order and exclude canceled orders from this comparison.
orders = df.drop_duplicates("order_id").copy()
orders = orders[orders["delivery_status"] != "Shipping canceled"]
orders["is_late"] = orders["delivery_status"] == "Late delivery"

# Build the 4-by-2 table: shipping mode by late / not late.
table = pd.crosstab(orders["shipping_mode"], orders["is_late"])
table = table.reindex(columns=[False, True], fill_value=0)
table.columns = ["not_late_orders", "late_orders"]

n = int(table.to_numpy().sum())
row_totals = table.sum(axis=1)
column_totals = table.sum(axis=0)

chi_square = 0.0
for mode in table.index:
    for result in table.columns:
        observed = table.loc[mode, result]
        expected = row_totals[mode] * column_totals[result] / n
        chi_square += (observed - expected) ** 2 / expected

degrees_of_freedom = (len(table.index) - 1) * (len(table.columns) - 1)

# Chi-square survival probability for 3 degrees of freedom.
p_value = (
    erfc(sqrt(chi_square / 2))
    + sqrt(2 * chi_square / pi) * exp(-chi_square / 2)
)

# Cramer's V; for a 4-by-2 table, the divisor's min dimension is 1.
cramers_v = sqrt(chi_square / n)

print("Orders by shipping mode and late status:")
print(table)
print(f"\nOrders included: {n:,}")
print(f"Chi-square: {chi_square:.2f}")
print(f"Degrees of freedom: {degrees_of_freedom}")
if p_value < 1e-300:
    print("p-value: < 1e-300")
else:
    print(f"p-value: {p_value:.3e}")
print(f"Cramer's V: {cramers_v:.3f}")