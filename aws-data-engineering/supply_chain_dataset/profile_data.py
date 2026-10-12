import pandas as pd

df = pd.read_csv("DataCoSupplyChainDataset.csv", encoding="latin1")
print('Order Item Id unique:', df['Order Item Id'].is_unique)
print('Duplicate Order Item Ids:', df['Order Item Id'].duplicated().sum())
print('Order/customer ID mismatches:', (df['Order Customer Id'] != df['Customer Id']).sum())

print("Shape:", df.shape)
print("\nColumns and data types:")
print(df.dtypes)
print("\nMissing values:")
print(df.isna().sum().sort_values(ascending=False).head(15))
print("\nDuplicate rows:", df.duplicated().sum())
print("\nOrder items per order:")
items_per_order = df.groupby("Order Id").size()

print("\nItems per order — summary:")
print(items_per_order.describe())

print("\nOrders by number of items:")
print(items_per_order.value_counts().sort_index())

order_dates = pd.to_datetime(df["order date (DateOrders)"], format="%m/%d/%Y %H:%M", errors="coerce",)

print("\nOrder date range:")
print(order_dates.min(), "to", order_dates.max())
print("Unparsed order dates:", order_dates.isna().sum())
print("\nOrder status counts:")
print(df["Order Status"].value_counts())

# df.shape()
# df.dtypes()
# df.isna().sum().sort(ascending=False).head(10)
# df.duplicated().sum()
# df.groupby("orderId")["order_id_item"].sum().describe()


