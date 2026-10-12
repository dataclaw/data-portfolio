from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


BASE_DIR = Path(__file__).parent
INPUT_FILE = BASE_DIR / "data" / "curated" / "delivery_kpis_by_mode.csv"
OUTPUT_FILE = BASE_DIR / "data" / "curated" / "delivery_kpis_by_mode.png"

df = pd.read_csv(INPUT_FILE)

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

charts = [
    ("late_pct_of_non_canceled", "Late among non-canceled orders"),
    ("canceled_pct", "Canceled orders"),
]

for ax, (column, title) in zip(axes, charts):
    bars = ax.bar(df["shipping_mode"], df[column], color="#3977a8")
    ax.set_title(title)
    ax.set_ylabel("Percent")
    ax.set_ylim(0, 105 if column == "late_pct_of_non_canceled" else 7)
    ax.tick_params(axis="x", rotation=25)

    for bar, value in zip(bars, df[column]):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{value:.1f}%",
            ha="center",
            va="bottom",
        )

fig.suptitle("Delivery outcomes by shipping mode")
fig.tight_layout()
fig.savefig(OUTPUT_FILE, dpi=150)
plt.show()

print(f"Chart saved to: {OUTPUT_FILE}")