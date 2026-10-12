import pandas as pd

df = pd.read_csv("DataCoSupplyChainDataset.csv", encoding="latin1")

required = [
    "Order Item Id",
    "Order Id",
    "Order Customer Id",
    "order date (DateOrders)",
    "shipping date (DateOrders)",
    "Shipping Mode",
    "Delivery Status",
    "Category Name",
]

print("Rows, columns:", df.shape)

print("\nMissing required values:")
print(df[required].isna().sum())

print("\nDuplicate Order Item Ids:", df["Order Item Id"].duplicated().sum())

order_dates = pd.to_datetime(
    df["order date (DateOrders)"],
    format="%m/%d/%Y %H:%M",
    errors="coerce",
)
shipping_dates = pd.to_datetime(
    df["shipping date (DateOrders)"],
    format="%m/%d/%Y %H:%M",
    errors="coerce",
)

print("\nUnparseable order dates:", order_dates.isna().sum())
print("Unparseable shipping dates:", shipping_dates.isna().sum())

print("\nPotential numeric anomalies:")
print("Quantity <= 0:", (df["Order Item Quantity"] <= 0).sum())
print("Negative actual shipping days:", (df["Days for shipping (real)"] < 0).sum())
print("Negative scheduled shipping days:", (df["Days for shipment (scheduled)"] < 0).sum())

over_schedule = (
    df["Days for shipping (real)"] > df["Days for shipment (scheduled)"]
)
not_canceled = df["Delivery Status"] != "Shipping canceled"
status_says_late = df["Delivery Status"] == "Late delivery"

print(
    "\nnon canceled rows where delivery status disagrees with shipping days:",
    ((status_says_late != over_schedule) & not_canceled).sum(),
)