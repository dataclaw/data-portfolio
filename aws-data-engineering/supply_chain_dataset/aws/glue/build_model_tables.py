import sys
from functools import reduce
from operator import or_

from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql import functions as F
from pyspark.sql.window import Window


args = getResolvedOptions(
    sys.argv,
    ["JOB_NAME", "SOURCE_S3_URI", "TARGET_S3_URI"],
)

sc = SparkContext.getOrCreate()
glue_context = GlueContext(sc)
spark = glue_context.spark_session
job = Job(glue_context)
job.init(args["JOB_NAME"], args)


source_uri = args["SOURCE_S3_URI"]
target_uri = args["TARGET_S3_URI"].rstrip("/")

data = (
    spark.read
    .option("header", "true")
    .option("inferSchema", "true")
    .csv(source_uri)
)

required_columns = [
    "order_id",
    "order_item_id",
    "order_date",
    "shipping_date",
    "type",
    "customer_segment",
    "order_status",
    "delivery_status",
    "late_delivery_risk",
    "shipping_mode",
    "days_for_shipping_real",
    "days_for_shipment_scheduled",
    "market",
    "order_country",
    "order_region",
    "order_state",
    "order_city",
    "product_card_id",
    "order_item_cardprod_id",
    "category_id",
    "product_category_id",
    "category_name",
    "department_id",
    "department_name",
    "product_name",
    "product_price",
    "product_status",
    "order_item_quantity",
    "order_item_product_price",
    "order_item_discount",
    "order_item_discount_rate",
    "source_sales",
    "source_order_item_total",
    "source_order_item_profit_ratio",
]

missing_columns = sorted(set(required_columns) - set(data.columns))
if missing_columns:
    raise ValueError(f"Input is missing required columns: {missing_columns}")

if data.filter(F.col("order_item_id").isNull()).limit(1).count():
    raise ValueError("order_item_id contains null values.")

if data.groupBy("order_item_id").count().filter(F.col("count") > 1).limit(1).count():
    raise ValueError("order_item_id is not unique.")

if data.filter(
    F.col("product_card_id") != F.col("order_item_cardprod_id")
).limit(1).count():
    raise ValueError("The product ID columns do not match.")

if data.filter(
    F.col("category_id") != F.col("product_category_id")
).limit(1).count():
    raise ValueError("The category ID columns do not match.")

data = (
    data
    .withColumn("order_date", F.to_timestamp("order_date"))
    .withColumn("shipping_date", F.to_timestamp("shipping_date"))
)

# Check that the attributes used for one-row-per-order and
# one-row-per-product tables are consistent within their keys.
order_fields = [
    "order_date",
    "shipping_date",
    "type",
    "customer_segment",
    "order_status",
    "delivery_status",
    "late_delivery_risk",
    "shipping_mode",
    "days_for_shipping_real",
    "days_for_shipment_scheduled",
    "market",
    "order_country",
    "order_region",
    "order_state",
    "order_city",
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


def has_multiple_values(frame, key, fields):
    counts = frame.groupBy(key).agg(
        *[F.countDistinct(F.col(field)).alias(field) for field in fields]
    )
    mismatch = reduce(
        or_,
        [F.col(field) > 1 for field in fields],
    )
    return counts.filter(mismatch).limit(1).count() > 0


if has_multiple_values(data, "order_id", order_fields):
    raise ValueError("Order-level fields vary within an order.")

if has_multiple_values(data, "product_card_id", product_fields):
    raise ValueError("Product fields vary within a product ID.")

# dim_date: one row per calendar date.
order_dates = data.select(F.to_date("order_date").alias("calendar_date"))
shipping_dates = data.select(F.to_date("shipping_date").alias("calendar_date"))

dim_date = (
    order_dates
    .union(shipping_dates)
    .filter(F.col("calendar_date").isNotNull())
    .distinct()
    .withColumn("date_key", F.date_format("calendar_date", "yyyyMMdd").cast("int"))
    .withColumn("year", F.year("calendar_date"))
    .withColumn("month", F.month("calendar_date"))
    .withColumn("day_of_month", F.dayofmonth("calendar_date"))
    .withColumn("quarter", F.quarter("calendar_date"))
    .select(
        "date_key",
        "calendar_date",
        "year",
        "month",
        "day_of_month",
        "quarter",
    )
)

# dim_product: one row per product_card_id.
dim_product = (
    data.select(
        "product_card_id",
        "product_name",
        "product_category_id",
        "category_name",
        "department_id",
        "department_name",
        "product_price",
        "product_status",
    )
    .dropDuplicates(["product_card_id"])
)

# dim_geography: one row per distinct location combination.
geography_fields = [
    "market",
    "order_country",
    "order_region",
    "order_state",
    "order_city",
]

geography_window = Window.orderBy(*geography_fields)

dim_geography = (
    data.select(*geography_fields)
    .distinct()
    .withColumn("geography_key", F.row_number().over(geography_window))
    .select("geography_key", *geography_fields)
)

# fact_orders: one row per order_id.
fact_orders = (
    data.select(
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
    )
    .dropDuplicates(["order_id"])
    .withColumn(
        "order_date_key",
        F.date_format(F.to_date("order_date"), "yyyyMMdd").cast("int"),
    )
    .withColumn(
        "shipping_date_key",
        F.date_format(F.to_date("shipping_date"), "yyyyMMdd").cast("int"),
    )
    .join(dim_geography, on=geography_fields, how="left")
    .select(
        "order_id",
        "order_date_key",
        "shipping_date_key",
        F.col("order_date").alias("order_timestamp"),
        F.col("shipping_date").alias("shipping_timestamp"),
        F.col("type").alias("payment_type"),
        "customer_segment",
        "order_status",
        "delivery_status",
        "shipping_mode",
        "late_delivery_risk",
        "days_for_shipping_real",
        "days_for_shipment_scheduled",
        "geography_key",
    )
)

# fact_order_items: one row per order_item_id.
fact_order_items = data.select(
    "order_item_id",
    "order_id",
    "product_card_id",
    F.col("order_item_quantity").alias("quantity"),
    F.col("order_item_product_price").alias("item_product_price"),
    F.col("order_item_discount").alias("discount_amount"),
    F.col("order_item_discount_rate").alias("discount_rate"),
    "source_sales",
    "source_order_item_total",
    "source_order_item_profit_ratio",
)

tables = {
    "dim_date": dim_date,
    "dim_product": dim_product,
    "dim_geography": dim_geography,
    "fact_orders": fact_orders,
    "fact_order_items": fact_order_items,
}

for table_name, frame in tables.items():
    output_uri = f"{target_uri}/{table_name}/"
    (
        frame.write
        .mode("overwrite")
        .format("parquet")
        .save(output_uri)
    )
    print(f"Wrote {table_name} to {output_uri}")

job.commit()