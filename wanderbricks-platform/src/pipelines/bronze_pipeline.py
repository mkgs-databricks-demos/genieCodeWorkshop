# Databricks notebook source
# DBTITLE 1,Bronze Layer — Raw Ingestion
# MAGIC %md
# MAGIC # Bronze Layer — Raw Ingestion from samples.wanderbricks
# MAGIC
# MAGIC Streaming tables that ingest all 16 source tables from `samples.wanderbricks`.
# MAGIC Minimal transformation: preserve all source columns, add ingestion timestamp.
# MAGIC Each table has a basic PK not-null expectation.

# COMMAND ----------

# DBTITLE 1,Imports and Config
from pyspark import pipelines as dp
from pyspark.sql import functions as F

SOURCE_CATALOG = "samples"
SOURCE_SCHEMA = "wanderbricks"

# COMMAND ----------

# DBTITLE 1,bronze_properties
@dp.table(
    name="bronze_properties",
    comment="Raw property listings ingested from samples.wanderbricks.properties"
)
@dp.expect("pk_not_null", "property_id IS NOT NULL")
def bronze_properties():
    return (
        spark.readStream.table(f"{SOURCE_CATALOG}.{SOURCE_SCHEMA}.properties")
        .withColumn("_ingested_at", F.current_timestamp())
    )

# COMMAND ----------

# DBTITLE 1,bronze_bookings
@dp.table(
    name="bronze_bookings",
    comment="Raw booking records ingested from samples.wanderbricks.bookings"
)
@dp.expect("pk_not_null", "booking_id IS NOT NULL")
def bronze_bookings():
    return (
        spark.readStream.table(f"{SOURCE_CATALOG}.{SOURCE_SCHEMA}.bookings")
        .withColumn("_ingested_at", F.current_timestamp())
    )

# COMMAND ----------

# DBTITLE 1,bronze_reviews
@dp.table(
    name="bronze_reviews",
    comment="Raw guest reviews ingested from samples.wanderbricks.reviews"
)
@dp.expect("pk_not_null", "review_id IS NOT NULL")
def bronze_reviews():
    return (
        spark.readStream.table(f"{SOURCE_CATALOG}.{SOURCE_SCHEMA}.reviews")
        .withColumn("_ingested_at", F.current_timestamp())
    )

# COMMAND ----------

# DBTITLE 1,bronze_users
@dp.table(
    name="bronze_users",
    comment="Raw user profiles ingested from samples.wanderbricks.users"
)
@dp.expect("pk_not_null", "user_id IS NOT NULL")
def bronze_users():
    return (
        spark.readStream.table(f"{SOURCE_CATALOG}.{SOURCE_SCHEMA}.users")
        .withColumn("_ingested_at", F.current_timestamp())
    )

# COMMAND ----------

# DBTITLE 1,bronze_hosts
@dp.table(
    name="bronze_hosts",
    comment="Raw host profiles ingested from samples.wanderbricks.hosts"
)
@dp.expect("pk_not_null", "host_id IS NOT NULL")
def bronze_hosts():
    return (
        spark.readStream.table(f"{SOURCE_CATALOG}.{SOURCE_SCHEMA}.hosts")
        .withColumn("_ingested_at", F.current_timestamp())
    )

# COMMAND ----------

# DBTITLE 1,bronze_destinations
@dp.table(
    name="bronze_destinations",
    comment="Raw destination/location records ingested from samples.wanderbricks.destinations"
)
@dp.expect("pk_not_null", "destination_id IS NOT NULL")
def bronze_destinations():
    return (
        spark.readStream.table(f"{SOURCE_CATALOG}.{SOURCE_SCHEMA}.destinations")
        .withColumn("_ingested_at", F.current_timestamp())
    )

# COMMAND ----------

# DBTITLE 1,bronze_payments
@dp.table(
    name="bronze_payments",
    comment="Raw payment records ingested from samples.wanderbricks.payments"
)
@dp.expect("pk_not_null", "payment_id IS NOT NULL")
def bronze_payments():
    return (
        spark.readStream.table(f"{SOURCE_CATALOG}.{SOURCE_SCHEMA}.payments")
        .withColumn("_ingested_at", F.current_timestamp())
    )

# COMMAND ----------

# DBTITLE 1,bronze_countries
@dp.table(
    name="bronze_countries",
    comment="Raw country reference data ingested from samples.wanderbricks.countries"
)
@dp.expect("pk_not_null", "country IS NOT NULL")
def bronze_countries():
    return (
        spark.readStream.table(f"{SOURCE_CATALOG}.{SOURCE_SCHEMA}.countries")
        .withColumn("_ingested_at", F.current_timestamp())
    )

# COMMAND ----------

# DBTITLE 1,bronze_amenities
@dp.table(
    name="bronze_amenities",
    comment="Raw amenity catalog ingested from samples.wanderbricks.amenities"
)
@dp.expect("pk_not_null", "amenity_id IS NOT NULL")
def bronze_amenities():
    return (
        spark.readStream.table(f"{SOURCE_CATALOG}.{SOURCE_SCHEMA}.amenities")
        .withColumn("_ingested_at", F.current_timestamp())
    )

# COMMAND ----------

# DBTITLE 1,bronze_property_amenities
@dp.table(
    name="bronze_property_amenities",
    comment="Raw property-amenity junction table ingested from samples.wanderbricks.property_amenities"
)
@dp.expect("property_id_not_null", "property_id IS NOT NULL")
@dp.expect("amenity_id_not_null", "amenity_id IS NOT NULL")
def bronze_property_amenities():
    return (
        spark.readStream.table(f"{SOURCE_CATALOG}.{SOURCE_SCHEMA}.property_amenities")
        .withColumn("_ingested_at", F.current_timestamp())
    )

# COMMAND ----------

# DBTITLE 1,bronze_property_images
@dp.table(
    name="bronze_property_images",
    comment="Raw property image records ingested from samples.wanderbricks.property_images"
)
@dp.expect("pk_not_null", "image_id IS NOT NULL")
def bronze_property_images():
    return (
        spark.readStream.table(f"{SOURCE_CATALOG}.{SOURCE_SCHEMA}.property_images")
        .withColumn("_ingested_at", F.current_timestamp())
    )

# COMMAND ----------

# DBTITLE 1,bronze_booking_updates
@dp.table(
    name="bronze_booking_updates",
    comment="Raw booking status change events ingested from samples.wanderbricks.booking_updates"
)
@dp.expect("pk_not_null", "booking_update_id IS NOT NULL")
def bronze_booking_updates():
    return (
        spark.readStream.table(f"{SOURCE_CATALOG}.{SOURCE_SCHEMA}.booking_updates")
        .withColumn("_ingested_at", F.current_timestamp())
    )

# COMMAND ----------

# DBTITLE 1,bronze_page_views
@dp.table(
    name="bronze_page_views",
    comment="Raw page view analytics ingested from samples.wanderbricks.page_views"
)
@dp.expect("pk_not_null", "view_id IS NOT NULL")
def bronze_page_views():
    return (
        spark.readStream.table(f"{SOURCE_CATALOG}.{SOURCE_SCHEMA}.page_views")
        .withColumn("_ingested_at", F.current_timestamp())
    )

# COMMAND ----------

# DBTITLE 1,bronze_employees
@dp.table(
    name="bronze_employees",
    comment="Raw employee records ingested from samples.wanderbricks.employees"
)
@dp.expect("pk_not_null", "employee_id IS NOT NULL")
def bronze_employees():
    return (
        spark.readStream.table(f"{SOURCE_CATALOG}.{SOURCE_SCHEMA}.employees")
        .withColumn("_ingested_at", F.current_timestamp())
    )

# COMMAND ----------

# DBTITLE 1,bronze_customer_support_logs
@dp.table(
    name="bronze_customer_support_logs",
    comment="Raw customer support tickets ingested from samples.wanderbricks.customer_support_logs"
)
@dp.expect("pk_not_null", "ticket_id IS NOT NULL")
def bronze_customer_support_logs():
    return (
        spark.readStream.table(f"{SOURCE_CATALOG}.{SOURCE_SCHEMA}.customer_support_logs")
        .withColumn("_ingested_at", F.current_timestamp())
    )

# COMMAND ----------

# DBTITLE 1,bronze_clickstream
@dp.table(
    name="bronze_clickstream",
    comment="Raw clickstream events ingested from samples.wanderbricks.clickstream"
)
@dp.expect("user_id_not_null", "user_id IS NOT NULL")
def bronze_clickstream():
    return (
        spark.readStream.table(f"{SOURCE_CATALOG}.{SOURCE_SCHEMA}.clickstream")
        .withColumn("_ingested_at", F.current_timestamp())
    )