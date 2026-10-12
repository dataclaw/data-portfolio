import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("DataCoSupplyChainDataset.csv", encoding="latin1")

category_sales = (
    df.groupby("Category Name")
    .agg(
        item_rows=("Order Item Id", "count"),
        orders=("Order Id", "nunique"),
        item_total=("Order Item Total", "sum"),
    )
    .sort_values("item_total", ascending=False)
)

print(category_sales.head(10).round(1))

category_sales.head(10).sort_values("item_total").plot(
    kind="barh",
    y="item_total",
    legend=False,
    figsize=(9, 6),
)

plt.title("Top 10 Categories by Sum of Order Item Total")
plt.xlabel("Sum of Order Item Total")
plt.ylabel("Category")
plt.tight_layout()
plt.show()

# print(
#     df.groupby("Order Id")[
#         ["Benefit per order", "Order Profit Per Order"]
#     ].nunique().max()
# )

print("Benefit equals Order Profit:", 
      (df["Benefit per order"] == df["Order Profit Per Order"]).mean())

print(df[[
    "Order Item Total",
    "Benefit per order",
    "Order Profit Per Order",
    "Order Item Profit Ratio",
]].describe().round(2))

category_profit = df.groupby("Category Name")["Order Item Profit Ratio"].agg(
    item_rows="count",
    mean_ratio="mean",
    median_ratio="median",
)

negative_share = (
    df.assign(negative=df["Order Item Profit Ratio"] < 0)
      .groupby("Category Name")["negative"]
      .mean() * 100
)

category_profit["negative_ratio_pct"] = negative_share
print(category_profit.sort_values("mean_ratio", ascending=False).round(2))

discount_analysis = df.groupby("Order Item Discount Rate").agg(
    item_rows=("Order Item Id", "count"),
    mean_ratio=("Order Item Profit Ratio", "mean"),
    negative_ratio_pct=(
        "Order Item Profit Ratio",
        lambda values: (values < 0).mean() * 100,
    ),
)

print(discount_analysis.round(2))

df["order_date"] = pd.to_datetime(
    df["order date (DateOrders)"],
    format="%m/%d/%Y %H:%M",
)

monthly = (
    df.set_index("order_date")
      .resample("MS")
      .agg(
          item_rows=("Order Item Id", "count"),
          item_total=("Order Item Total", "sum"),
      )
)

print(monthly.head())
print(monthly.tail())

monthly["item_total"].plot(
    title="Monthly Sum of Order Item Total",
    ylabel="Summed Order Item Total",
    figsize=(10, 5),
)

plt.tight_layout()
plt.show()