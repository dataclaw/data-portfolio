from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


BASE_DIR = Path(__file__).parent
CURATED_FILE = BASE_DIR / "data" / "curated" / "supply_chain_items.csv"
OUTPUT_FILE = BASE_DIR / "data" / "curated" / "monthly_market_coverage.png"

df = pd.read_csv(
    CURATED_FILE,
    usecols=["order_date", "order_id", "market"],
)
df["order_month"] = df["order_date"].str[:7]
df = df[df["order_month"].between("2017-08", "2018-01")]

monthly = (
    df.groupby(["order_month", "market"])
    .agg(
        item_rows=("order_id", "size"),
        distinct_orders=("order_id", "nunique"),
    )
    .reset_index()
)

months = sorted(monthly["order_month"].unique())

def make_pivot(value):
    return (
        monthly.pivot(index="order_month", columns="market", values=value)
        .reindex(months)
        .fillna(0)
    )

fig, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=True)

for ax, metric, title in [
    (axes[0], "item_rows", "Item rows by market"),
    (axes[1], "distinct_orders", "Distinct orders by market"),
]:
    values = make_pivot(metric)
    bottom = [0] * len(values)

    for market in values.columns:
        ax.bar(values.index, values[market], bottom=bottom, label=market)
        bottom = [
            total + value
            for total, value in zip(bottom, values[market])
        ]

    ax.set_title(title)
    ax.set_ylabel("Count")
    ax.legend(title="Market")

axes[1].set_xlabel("Order month")
plt.xticks(range(len(months)), months, rotation=45)
fig.suptitle("Dataset composition, August 2017–January 2018")
fig.tight_layout()
fig.savefig(OUTPUT_FILE, dpi=150)
plt.show()

print(f"Chart saved to: {OUTPUT_FILE}")