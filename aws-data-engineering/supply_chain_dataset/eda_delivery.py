import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("DataCoSupplyChainDataset.csv", encoding="latin1")

delivery_mix = pd.crosstab(
    df["Shipping Mode"],
    df["Delivery Status"],
    normalize="index"
) * 100

print(delivery_mix.round(1))

delivery_mix.plot(kind="bar", stacked=True, figsize=(10, 6))
plt.title("Delivery Status Mix by Shipping Mode")
plt.xlabel("Shipping Mode")
plt.ylabel("Share of order items (%)")
plt.legend(title="Delivery Status", bbox_to_anchor=(1.02, 1), loc="upper left")
plt.tight_layout()
plt.show()

late_risk = df.groupby("Shipping Mode").agg(
    item_count=("Order Item Id", "count"),
    late_risk_rate=("Late_delivery_risk", "mean"),
)

late_risk["late_risk_rate"] *= 100
print(late_risk.round(1))

df["days_vs_schedule"] = (
    df["Days for shipping (real)"]
    - df["Days for shipment (scheduled)"]
)

df["is_late_by_days"] = df["days_vs_schedule"] > 0

shipping_check = df.groupby("Shipping Mode").agg(
    item_count=("Order Item Id", "count"),
    average_days_vs_schedule=("days_vs_schedule", "mean"),
    late_by_days_rate=("is_late_by_days", "mean"),
)

shipping_check["late_by_days_rate"] *= 100
print("\nActual versus scheduled shipping days:")
print(shipping_check.round(1))

print("\nDelivery status versus actual days:")
print(
    pd.crosstab(
        df["Delivery Status"],
        df["is_late_by_days"],
        normalize="index"
    ).mul(100).round(1)
)