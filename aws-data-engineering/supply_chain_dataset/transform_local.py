from pathlib import Path
import json

import pandas as pd


BASE_DIR = Path(__file__).parent
RAW_FILE = BASE_DIR / "data" / "raw" / "DataCoSupplyChainDataset.csv"
OUTPUT_DIR = BASE_DIR / "data" / "curated"

# Allowlist analytical fields. Customer names, IDs, contact details,
# addresses, credentials, and customer location fields are excluded.
COLUMNS = {
    "Type": "type",
    "Days for shipping (real)": "days_for_shipping_real",
    "Days for shipment (scheduled)": "days_for_shipment_scheduled",
    "Delivery Status": "delivery_status",
    "Late_delivery_risk": "late_delivery_risk",
    "Category Id": "category_id",
    "Category Name": "category_name",
    "Customer Segment": "customer_segment",
    "Department Id": "department_id",
    "Department Name": "department_name",
    "Market": "market",
    "Order City": "order_city",
    "Order Country": "order_country",
    "Order Region": "order_region",
    "Order State": "order_state",
    "order date (DateOrders)": "order_date",
    "Order Id": "order_id",
    "Order Item Cardprod Id": "order_item_cardprod_id",
    "Order Item Discount": "order_item_discount",
    "Order Item Discount Rate": "order_item_discount_rate",
    "Order Item Id": "order_item_id",
    "Order Item Product Price": "order_item_product_price",
    "Order Item Profit Ratio": "source_order_item_profit_ratio",
    "Order Item Quantity": "order_item_quantity",
    "Sales": "source_sales",
    "Order Item Total": "source_order_item_total",
    "Order Status": "order_status",
    "Product Card Id": "product_card_id",
    "Product Category Id": "product_category_id",
    "Product Name": "product_name",
    "Product Price": "product_price",
    "Product Status": "product_status",
    "shipping date (DateOrders)": "shipping_date",
    "Shipping Mode": "shipping_mode",
}

DATE_COLUMNS = [
    "order date (DateOrders)",
    "shipping date (DateOrders)",
]

REQUIRED_COLUMNS = [
    "Order Item Id",
    "Order Id",
    "order date (DateOrders)",
    "shipping date (DateOrders)",
    "Delivery Status",
    "Shipping Mode",
]


def main():
    df = pd.read_csv(
        RAW_FILE,
        encoding="latin1",
        usecols=list(COLUMNS),
    )

    # Convert both dates to a consistent ISO format.
    for column in DATE_COLUMNS:
        dates = pd.to_datetime(
            df[column],
            format="%m/%d/%Y %H:%M",
            errors="coerce",
        )
        invalid_count = int(dates.isna().sum())
        if invalid_count:
            raise ValueError(
                f"{invalid_count} unparseable values in {column}"
            )
        df[column] = dates.dt.strftime("%Y-%m-%d %H:%M:%S")

    missing = df[REQUIRED_COLUMNS].isna().sum()
    missing = missing[missing > 0]
    if not missing.empty:
        raise ValueError(f"Missing values in required fields:\n{missing}")

    duplicate_ids = int(df["Order Item Id"].duplicated().sum())
    if duplicate_ids:
        raise ValueError(f"Found {duplicate_ids} duplicate Order Item Ids")

    curated = df.rename(columns=COLUMNS)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / "supply_chain_items.csv"
    curated.to_csv(output_file, index=False, encoding="utf-8")

    summary = {
        "rows": int(len(curated)),
        "columns": int(len(curated.columns)),
        "order_date_min": curated["order_date"].min(),
        "order_date_max": curated["order_date"].max(),
        "duplicate_order_item_ids": duplicate_ids,
        "customer_names_ids_addresses_and_contact_fields_included": False,
        "note": (
            "Source Sales, Order Item Total, and Order Item Profit Ratio "
            "are retained with neutral names; their business meanings "
            "are not inferred."
        ),
    }
    summary_file = OUTPUT_DIR / "transformation_summary.json"
    summary_file.write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Curated {summary['rows']:,} rows and {summary['columns']} columns.")
    print(
        f"Order dates: {summary['order_date_min']} "
        f"through {summary['order_date_max']}"
    )
    print(f"Output: {output_file}")
    print(f"Summary: {summary_file}")


if __name__ == "__main__":
    main()