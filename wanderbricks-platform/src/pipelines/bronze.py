# Databricks notebook source
# MAGIC %md
# MAGIC # Bronze Layer — Raw Ingestion from samples.wanderbricks
# MAGIC
# MAGIC Streaming tables that ingest all source tables with minimal transformation.
# MAGIC Adds ingestion timestamp and preserves all source columns.

# COMMAND ----------

from pyspark import pipelines as dp
from pyspark.sql.functions import current_timestamp

source_catalog = spark.conf.get("source_catalog")
source_schema = spark.conf.get("source_schema")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Core Entity Tables

# COMMAND ----------

@dp.table(
    name="bronze_properties",
    comment="Raw property listings ingested from samples.wanderbricks.properties"
)
@dp.expect("pk_not_null", "property_id IS NOT NULL")
def bronze_properties():
    return (
        spark.readStream.table(f"{source_catalog}.{source_schema}.properties")
        .withColumn("_ingested_at", current_timestamp())
    )

# COMMAND ----------

@dp.table(
    name="bronze_bookings",
    comment="Raw booking records ingested from samples.wanderbricks.bookings"
)
@dp.expect("pk_not_null", "booking_id IS NOT NULL")
@dp.expect("valid_dates", "check_out > check_in")
@dp.expect("positive_amount", "total_amount > 0")
def bronze_bookings():
    return (
        spark.readStream.table(f"{source_catalog}.{source_schema}.bookings")
        .withColumn("_ingested_at", current_timestamp())
    )

# COMMAND ----------

@dp.table(
    name="bronze_reviews",
    comment="Raw guest reviews ingested from samples.wanderbricks.reviews"
)
@dp.expect("pk_not_null", "review_id IS NOT NULL")
@dp.expect("valid_rating", "rating BETWEEN 1.0 AND 5.0")
def bronze_reviews():
    return (
        spark.readStream.table(f"{source_catalog}.{source_schema}.reviews")
        .withColumn("_ingested_at", current_timestamp())
    )

# COMMAND ----------

@dp.table(
    name="bronze_users",
    comment="Raw guest profiles ingested from samples.wanderbricks.users"
)
@dp.expect("pk_not_null", "user_id IS NOT NULL")
def bronze_users():
    return (
        spark.readStream.table(f"{source_catalog}.{source_schema}.users")
        .withColumn("_ingested_at", current_timestamp())
    )

# COMMAND ----------

@dp.table(
    name="bronze_hosts",
    comment="Raw host profiles ingested from samples.wanderbricks.hosts"
)
@dp.expect("pk_not_null", "host_id IS NOT NULL")
def bronze_hosts():
    return (
        spark.readStream.table(f"{source_catalog}.{source_schema}.hosts")
        .withColumn("_ingested_at", current_timestamp())
    )

# COMMAND ----------

@dp.table(
    name="bronze_destinations",
    comment="Raw destination/location data ingested from samples.wanderbricks.destinations"
)
@dp.expect("pk_not_null", "destination_id IS NOT NULL")
def bronze_destinations():
    return (
        spark.readStream.table(f"{source_catalog}.{source_schema}.destinations")
        .withColumn("_ingested_at", current_timestamp())
    )

# COMMAND ----------

@dp.table(
    name="bronze_payments",
    comment="Raw payment records ingested from samples.wanderbricks.payments"
)
@dp.expect("pk_not_null", "payment_id IS NOT NULL")
def bronze_payments():
    return (
        spark.readStream.table(f"{source_catalog}.{source_schema}.payments")
        .withColumn("_ingested_at", current_timestamp())
    )

# COMMAND ----------

@dp.table(
    name="bronze_countries",
    comment="Raw country reference data ingested from samples.wanderbricks.countries"
)
@dp.expect("pk_not_null", "country IS NOT NULL")
def bronze_countries():
    return (
        spark.readStream.table(f"{source_catalog}.{source_schema}.countries")
        .withColumn("_ingested_at", current_timestamp())
    )

# COMMAND ----------

@dp.table(
    name="bronze_amenities",
    comment="Raw amenity catalog ingested from samples.wanderbricks.amenities"
)
@dp.expect("pk_not_null", "amenity_id IS NOT NULL")
def bronze_amenities():
    return (
        spark.readStream.table(f"{source_catalog}.{source_schema}.amenities")
        .withColumn("_ingested_at", current_timestamp())
    )

# COMMAND ----------

@dp.table(
    name="bronze_property_amenities",
    comment="Raw property-amenity junction table ingested from samples.wanderbricks.property_amenities"
)
@dp.expect("property_id_not_null", "property_id IS NOT NULL")
@dp.expect("amenity_id_not_null", "amenity_id IS NOT NULL")
def bronze_property_amenities():
    return (
        spark.readStream.table(f"{source_catalog}.{source_schema}.property_amenities")
        .withColumn("_ingested_at", current_timestamp())
    )

# COMMAND ----------

@dp.table(
    name="bronze_property_images",
    comment="Raw property image metadata ingested from samples.wanderbricks.property_images"
)
@dp.expect("pk_not_null", "image_id IS NOT NULL")
def bronze_property_images():
    return (
        spark.readStream.table(f"{source_catalog}.{source_schema}.property_images")
        .withColumn("_ingested_at", current_timestamp())
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Event & Activity Tables

# COMMAND ----------

@dp.table(
    name="bronze_booking_updates",
    comment="Raw booking status change events ingested from samples.wanderbricks.booking_updates"
)
@dp.expect("pk_not_null", "booking_update_id IS NOT NULL")
def bronze_booking_updates():
    return (
        spark.readStream.table(f"{source_catalog}.{source_schema}.booking_updates")
        .withColumn("_ingested_at", current_timestamp())
    )

# COMMAND ----------

@dp.table(
    name="bronze_customer_support_logs",
    comment="Raw customer support tickets with nested messages ingested from samples.wanderbricks.customer_support_logs"
)
@dp.expect("pk_not_null", "ticket_id IS NOT NULL")
def bronze_customer_support_logs():
    return (
        spark.readStream.table(f"{source_catalog}.{source_schema}.customer_support_logs")
        .withColumn("_ingested_at", current_timestamp())
    )

# COMMAND ----------

@dp.table(
    name="bronze_clickstream",
    comment="Raw clickstream events ingested from samples.wanderbricks.clickstream"
)
@dp.expect("user_id_not_null", "user_id IS NOT NULL")
def bronze_clickstream():
    return (
        spark.readStream.table(f"{source_catalog}.{source_schema}.clickstream")
        .withColumn("_ingested_at", current_timestamp())
    )

# COMMAND ----------

@dp.table(
    name="bronze_page_views",
    comment="Raw page view analytics ingested from samples.wanderbricks.page_views"
)
@dp.expect("pk_not_null", "view_id IS NOT NULL")
def bronze_page_views():
    return (
        spark.readStream.table(f"{source_catalog}.{source_schema}.page_views")
        .withColumn("_ingested_at", current_timestamp())
    )

# COMMAND ----------

@dp.table(
    name="bronze_employees",
    comment="Raw internal employee data ingested from samples.wanderbricks.employees"
)
@dp.expect("pk_not_null", "employee_id IS NOT NULL")
def bronze_employees():
    return (
        spark.readStream.table(f"{source_catalog}.{source_schema}.employees")
        .withColumn("_ingested_at", current_timestamp())
    )
