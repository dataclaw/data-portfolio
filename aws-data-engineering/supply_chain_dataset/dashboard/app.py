import pandas as pd
import streamlit as st

st.set_page_config(page_title="Supply Chain Dashboard", layout="wide")

st.title("DataCo Supply Chain Dashboard")
st.write("Explore delivery performance and order patterns.")

delivery = pd.read_csv("published/delivery_kpis_by_mode.csv")

shipping_modes = ["All"] + sorted(delivery["shipping_mode"].unique())
selected_mode = st.selectbox("Shipping mode", shipping_modes)

if selected_mode == "All":
    results = delivery
else:
    results = delivery[delivery["shipping_mode"] == selected_mode]

total_orders = results["total_orders"].sum()
non_canceled_orders = results["non_canceled_orders"].sum()
late_orders = results["late_orders"].sum()

late_percent = round(late_orders / non_canceled_orders * 100, 1)

first_column, second_column, third_column = st.columns(3)

first_column.metric("Orders", f"{total_orders:,}")
second_column.metric("Non-canceled orders", f"{non_canceled_orders:,}")
third_column.metric("Late delivery rate", f"{late_percent}%")

chart_data = results.set_index("shipping_mode")[["late_pct_of_non_canceled"]]
st.bar_chart(chart_data)

highest_late_mode = results.loc[
    results["late_pct_of_non_canceled"].idxmax()
]

st.write(
    f"In this view, {highest_late_mode['shipping_mode']} has the highest "
    f"late delivery rate ({highest_late_mode['late_pct_of_non_canceled']}%)."
)

st.subheader("Delivery details")
st.dataframe(results, hide_index=True)

monthly = pd.read_csv("published/monthly_coverage.csv")

st.subheader("Monthly item rows and orders")

monthly_chart = monthly.set_index("order_month")[["item_rows", "distinct_orders"]]
st.line_chart(monthly_chart)

september = monthly[monthly["order_month"] == "2017-09"]
october = monthly[monthly["order_month"] == "2017-10"]

if not september.empty and not october.empty:
    september_ratio = (
        september["item_rows"].iloc[0] / september["distinct_orders"].iloc[0]
    )
    october_ratio = (
        october["item_rows"].iloc[0] / october["distinct_orders"].iloc[0]
    )

    st.info(
        f"Item rows per order changed from {september_ratio:.2f} in "
        f"September 2017 to {october_ratio:.2f} in October 2017. "
        f"The reason for this change in dataset composition is unknown."
    )

late_rates = pd.read_csv("published/late_rate_by_market_year.csv")

st.subheader("Late delivery by year and market")

years = sorted(late_rates["order_year"].astype(str).unique())
markets = ["All"] + sorted(late_rates["market"].dropna().unique())

selected_year = st.selectbox("Year", years)
selected_market = st.selectbox("Market", markets)

filtered_rates = late_rates[
    late_rates["order_year"].astype(str) == selected_year
]

if selected_market != "All":
    filtered_rates = filtered_rates[
        filtered_rates["market"] == selected_market
    ]

# Sum the order counts first, then calculate the rate from those totals.
mode_totals = filtered_rates.groupby("shipping_mode", as_index=False).agg(
    non_canceled_orders=("non_canceled_orders", "sum"),
    late_orders=("late_orders", "sum")
)

mode_totals["late_pct"] = (
    mode_totals["late_orders"] / mode_totals["non_canceled_orders"] * 100
).round(1)

late_rate_chart = mode_totals.set_index("shipping_mode")[["late_pct"]]
st.bar_chart(late_rate_chart)

st.dataframe(mode_totals, hide_index=True)

if not mode_totals.empty:
    highest_late_mode = mode_totals.loc[mode_totals["late_pct"].idxmax()]

    if selected_market == "All":
        market_text = "all markets"
    else:
        market_text = selected_market

    st.info(
        f"For {market_text} in {selected_year}, "
        f"{highest_late_mode['shipping_mode']} has the highest late rate "
        f"({highest_late_mode['late_pct']}%), based on "
        f"{int(highest_late_mode['non_canceled_orders']):,} non-canceled orders."
    )

    if (mode_totals["non_canceled_orders"] < 100).any():
        st.caption(
            "Some shipping mode groups have fewer than 100 orders, "
            "so their percentages may be less stable."
        )