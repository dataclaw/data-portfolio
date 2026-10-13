CREATE DATABASE IF NOT EXISTS supply_chain;

CREATE EXTERNAL TABLE IF NOT EXISTS supply_chain.dim_date (
    date_key INT,
    calendar_date DATE,
    year INT,
    month INT,
    day_of_month INT,
    quarter INT
)
STORED AS PARQUET
LOCATION 's3://supply-chain-test-20261013-a84f2e/curated/model/dim_date/';

CREATE EXTERNAL TABLE IF NOT EXISTS supply_chain.dim_product (
    product_card_id INT,
    product_name STRING,
    product_category_id INT,
    category_name STRING,
    department_id INT,
    department_name STRING,
    product_price DOUBLE,
    product_status INT
)
STORED AS PARQUET
LOCATION 's3://supply-chain-test-20261013-a84f2e/curated/model/dim_product/';

CREATE EXTERNAL TABLE IF NOT EXISTS supply_chain.dim_geography (
    geography_key INT,
    market STRING,
    order_country STRING,
    order_region STRING,
    order_state STRING,
    order_city STRING
)
STORED AS PARQUET
LOCATION 's3://supply-chain-test-20261013-a84f2e/curated/model/dim_geography/';

CREATE EXTERNAL TABLE IF NOT EXISTS supply_chain.fact_orders (
    order_id INT,
    order_date_key INT,
    shipping_date_key INT,
    order_timestamp TIMESTAMP,
    shipping_timestamp TIMESTAMP,
    payment_type STRING,
    customer_segment STRING,
    order_status STRING,
    delivery_status STRING,
    shipping_mode STRING,
    late_delivery_risk INT,
    days_for_shipping_real INT,
    days_for_shipment_scheduled INT,
    geography_key INT
)
STORED AS PARQUET
LOCATION 's3://supply-chain-test-20261013-a84f2e/curated/model/fact_orders/';

CREATE EXTERNAL TABLE IF NOT EXISTS supply_chain.fact_order_items (
    order_item_id INT,
    order_id INT,
    product_card_id INT,
    quantity INT,
    item_product_price DOUBLE,
    discount_amount DOUBLE,
    discount_rate DOUBLE,
    source_sales DOUBLE,
    source_order_item_total DOUBLE,
    source_order_item_profit_ratio DOUBLE
)
STORED AS PARQUET
LOCATION 's3://supply-chain-test-20261013-a84f2e/curated/model/fact_order_items/';