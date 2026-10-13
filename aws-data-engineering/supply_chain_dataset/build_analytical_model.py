from pathlib import Path
import sqlite3

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent
SOURCE_FILE = PROJECT_DIR / "data" / "curated" / "supply_chain_items.csv"
DATABASE_FILE = PROJECT_DIR / "data" / "curated" / "supply_chain_model.db"

if not SOURCE_FILE.exists():
    raise FileNotFoundError(f"Curated CSV not found: {SOURCE_FILE}")

data = pd.read_csv(
    SOURCE_FILE,
    parse_dates=["order_date", "shipping_date"],
)

# Stop if the relationships used to design the model no longer hold.
order_fields = [
    "order_date",
    "shipping_date",
    "order_status",
    "delivery_status",
    "late_delivery_risk",
    "shipping_mode",
    "days_for_shipping_real",
    "days_for_shipment_scheduled",
    "type",
    "market",
    "customer_segment",
    "order_city",
    "order_country",
    "order_region",
    "order_state",
]

product_fields = [
    "category_id",
    "product_category_id",
    "category_name",
    "department_id",
    "department_name",
    "product_name",
    "product_price",
    "product_status",
]

order_changes = (
    data.groupby("order_id")[order_fields]
    .nunique(dropna=False)
    .gt(1)
    .any()
    .any()
)

product_changes = (
    data.groupby("product_card_id")[product_fields]
    .nunique(dropna=False)
    .gt(1)
    .any()
    .any()
)

if order_changes:
    raise ValueError("At least one order has inconsistent order-level fields.")

if product_changes:
    raise ValueError("At least one product has inconsistent product fields.")

if data["order_item_id"].duplicated().any():
    raise ValueError("order_item_id is not unique.")

if not data["product_card_id"].eq(data["order_item_cardprod_id"]).all():
    raise ValueError("The two product ID columns no longer match.")

if not data["category_id"].eq(data["product_category_id"]).all():
    raise ValueError("The two category ID columns no longer match.")

# dim_date: one row per calendar date.
date_values = pd.concat(
    [
        data["order_date"].dt.normalize(),
        data["shipping_date"].dt.normalize(),
    ],
    ignore_index=True,
).dropna().drop_duplicates().sort_values()

dim_date = pd.DataFrame(
    {"calendar_date": date_values.dt.strftime("%Y-%m-%d")}
)
date_parsed = pd.to_datetime(dim_date["calendar_date"])

dim_date["date_key"] = date_parsed.dt.strftime("%Y%m%d").astype("int64")
dim_date["year"] = date_parsed.dt.year
dim_date["month"] = date_parsed.dt.month
dim_date["day_of_month"] = date_parsed.dt.day
dim_date["quarter"] = date_parsed.dt.quarter
dim_date = dim_date[
    ["date_key", "calendar_date", "year", "month", "day_of_month", "quarter"]
]

# dim_product: one row per product_card_id.
dim_product = (
    data[
        [
            "product_card_id",
            "product_name",
            "product_category_id",
            "category_name",
            "department_id",
            "department_name",
            "product_price",
            "product_status",
        ]
    ]
    .drop_duplicates(subset=["product_card_id"])
    .copy()
)

# dim_geography: one row per distinct location combination.
geography_fields = [
    "market",
    "order_country",
    "order_region",
    "order_state",
    "order_city",
]

dim_geography = (
    data[geography_fields]
    .drop_duplicates()
    .sort_values(geography_fields, na_position="last")
    .reset_index(drop=True)
)
dim_geography.insert(0, "geography_key", range(1, len(dim_geography) + 1))

# fact_orders: one row per order_id.
order_fields_for_table = [
    "order_id",
    "order_date",
    "shipping_date",
    "type",
    "customer_segment",
    "order_status",
    "delivery_status",
    "shipping_mode",
    "late_delivery_risk",
    "days_for_shipping_real",
    "days_for_shipment_scheduled",
    *geography_fields,
]

fact_orders = (
    data[order_fields_for_table]
    .drop_duplicates(subset=["order_id"])
    .copy()
)

fact_orders["order_date_key"] = (
    fact_orders["order_date"].dt.strftime("%Y%m%d").astype("int64")
)
fact_orders["shipping_date_key"] = (
    fact_orders["shipping_date"].dt.strftime("%Y%m%d").astype("int64")
)

fact_orders = fact_orders.merge(
    dim_geography,
    on=geography_fields,
    how="left",
    validate="many_to_one",
)

fact_orders = fact_orders.rename(
    columns={
        "order_date": "order_timestamp",
        "shipping_date": "shipping_timestamp",
        "type": "payment_type",
    }
)

fact_orders = fact_orders[
    [
        "order_id",
        "order_date_key",
        "shipping_date_key",
        "order_timestamp",
        "shipping_timestamp",
        "payment_type",
        "customer_segment",
        "order_status",
        "delivery_status",
        "shipping_mode",
        "late_delivery_risk",
        "days_for_shipping_real",
        "days_for_shipment_scheduled",
        "geography_key",
    ]
]

# fact_order_items: one row per order_item_id.
fact_order_items = data[
    [
        "order_item_id",
        "order_id",
        "product_card_id",
        "order_item_quantity",
        "order_item_product_price",
        "order_item_discount",
        "order_item_discount_rate",
        "source_sales",
        "source_order_item_total",
        "source_order_item_profit_ratio",
    ]
].rename(
    columns={
        "order_item_quantity": "quantity",
        "order_item_product_price": "item_product_price",
        "order_item_discount": "discount_amount",
        "order_item_discount_rate": "discount_rate",
    }
)

# Rebuild the model tables each time this script is run.
with sqlite3.connect(DATABASE_FILE) as connection:
    connection.execute("PRAGMA foreign_keys = OFF")

    connection.executescript(
        """
        DROP TABLE IF EXISTS fact_order_items;
        DROP TABLE IF EXISTS fact_orders;
        DROP TABLE IF EXISTS dim_product;
        DROP TABLE IF EXISTS dim_geography;
        DROP TABLE IF EXISTS dim_date;

        CREATE TABLE dim_date (
            date_key INTEGER PRIMARY KEY,
            calendar_date TEXT NOT NULL UNIQUE,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            day_of_month INTEGER NOT NULL,
            quarter INTEGER NOT NULL
        );

        CREATE TABLE dim_product (
            product_card_id INTEGER PRIMARY KEY,
            product_name TEXT,
            product_category_id INTEGER,
            category_name TEXT,
            department_id INTEGER,
            department_name TEXT,
            product_price REAL,
            product_status INTEGER
        );

        CREATE TABLE dim_geography (
            geography_key INTEGER PRIMARY KEY,
            market TEXT,
            order_country TEXT,
            order_region TEXT,
            order_state TEXT,
            order_city TEXT,
            UNIQUE (market, order_country, order_region, order_state, order_city)
        );

        CREATE TABLE fact_orders (
            order_id INTEGER PRIMARY KEY,
            order_date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
            shipping_date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
            order_timestamp TEXT NOT NULL,
            shipping_timestamp TEXT NOT NULL,
            payment_type TEXT,
            customer_segment TEXT,
            order_status TEXT,
            delivery_status TEXT,
            shipping_mode TEXT,
            late_delivery_risk INTEGER,
            days_for_shipping_real INTEGER,
            days_for_shipment_scheduled INTEGER,
            geography_key INTEGER REFERENCES dim_geography(geography_key)
        );

        CREATE TABLE fact_order_items (
            order_item_id INTEGER PRIMARY KEY,
            order_id INTEGER NOT NULL REFERENCES fact_orders(order_id),
            product_card_id INTEGER NOT NULL REFERENCES dim_product(product_card_id),
            quantity INTEGER,
            item_product_price REAL,
            discount_amount REAL,
            discount_rate REAL,
            source_sales REAL,
            source_order_item_total REAL,
            source_order_item_profit_ratio REAL
        );
        """
    )

    connection.execute("PRAGMA foreign_keys = ON")

    dim_date.to_sql("dim_date", connection, if_exists="append", index=False)
    dim_product.to_sql("dim_product", connection, if_exists="append", index=False)
    dim_geography.to_sql("dim_geography", connection, if_exists="append", index=False)
    fact_orders.to_sql("fact_orders", connection, if_exists="append", index=False)
    fact_order_items.to_sql(
        "fact_order_items",
        connection,
        if_exists="append",
        index=False,
        chunksize=5000,
    )

    connection.executescript(
        """
        CREATE INDEX idx_fact_orders_geography
            ON fact_orders(geography_key);

        CREATE INDEX idx_fact_order_items_order
            ON fact_order_items(order_id);

        CREATE INDEX idx_fact_order_items_product
            ON fact_order_items(product_card_id);
        """
    )

    foreign_key_errors = connection.execute(
        "PRAGMA foreign_key_check"
    ).fetchall()

    if foreign_key_errors:
        raise ValueError(f"Foreign key errors found: {foreign_key_errors[:5]}")

    order_count = connection.execute(
        "SELECT COUNT(*) FROM fact_orders"
    ).fetchone()[0]

    item_count = connection.execute(
        "SELECT COUNT(*) FROM fact_order_items"
    ).fetchone()[0]

    product_count = connection.execute(
        "SELECT COUNT(*) FROM dim_product"
    ).fetchone()[0]

    geography_count = connection.execute(
        "SELECT COUNT(*) FROM dim_geography"
    ).fetchone()[0]

print(f"Model database created: {DATABASE_FILE}")
print(f"Orders: {order_count:,}")
print(f"Order items: {item_count:,}")
print(f"Products: {product_count:,}")
print(f"Geographies: {geography_count:,}")
print("Foreign key check: passed")