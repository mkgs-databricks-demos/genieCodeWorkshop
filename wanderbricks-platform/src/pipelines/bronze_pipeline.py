# Databricks notebook source
# MAGIC %md
# MAGIC # Bronze Layer — Raw Ingestion from samples.wanderbricks
# MAGIC
# MAGIC Streaming tables for all 16 source tables with:
# MAGIC - Ingestion timestamp (`_ingested_at`)
# MAGIC - Primary key not-null expectations
# MAGIC - All source columns preserved

# COMMAND ----------

from pyspark import pipelines as dp
from pyspark.sql.functions import current_timestamp

SOURCE_CATALOG = "samples"
SOURCE_SCHEMA = "wanderbricks"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Core Entity Tables

# COMMAND ----------

@dp.table(
    name="bronze_properties",
    comment="Raw property listings from samples.wanderbricks.properties"
)
@dp.expect("pk_not_null", "property_id IS NOT NULL")
def bronze_properties():
    return (
        spark.readStream.table(f"{SOURCE_CATALOG}.{SOURCE_SCHEMA}.properties")
        .withColumn("_ingested_at", current_timestamp())
    )

# COMMAND ----------

@dp.table(
    name="bronze_bookings",
    comment="Raw booking records from samples.wanderbricks.bookings"
)
@dp.expect("pk_not_null", "booking_id IS NOT NULL")
def bronze_bookings():
    return (
        spark.readStream.table(f"{SOURCE_CATALOG}.{SOURCE_SCHEMA}.bookings")
        .withColumn("_ingested_at", current_timestamp())
    )

# COMMAND ----------

@dp.table(
    name="bronze_reviews",
    comment="Raw guest reviews from samples.wanderbricks.reviews"
)
@dp.expect("pk_not_null", "review_id IS NOT NULL")
def bronze_reviews():
    return (
        spark.readStream.table(f"{SOURCE_CATALOG}.{SOURCE_SCHEMA}.reviews")
        .withColumn("_ingested_at", current_timestamp())
    )

# COMMAND ----------

@dp.table(
    name="bronze_users",
    comment="Raw guest profiles from samples.wanderbricks.users"
)
@dp.expect("pk_not_null", "user_id IS NOT NULL")
def bronze_users():
    return (
        spark.readStream.table(f"{SOURCE_CATALOG}.{SOURCE_SCHEMA}.users")
        .withColumn("_ingested_at", current_timestamp())
    )

# COMMAND ----------

@dp.table(
    name="bronze_hosts",
    comment="Raw host profiles from samples.wanderbricks.hosts"
)
@dp.expect("pk_not_null", "host_id IS NOT NULL")
def bronze_hosts():
    return (
        spark.readStream.table(f"{SOURCE_CATALOG}.{SOURCE_SCHEMA}.hosts")
        .withColumn("_ingested_at", current_timestamp())
    )

# COMMAND ----------

@dp.table(
    name="bronze_destinations",
    comment="Raw destination/location data from samples.wanderbricks.destinations"
)
@dp.expect("pk_not_null", "destination_id IS NOT NULL")
def bronze_destinations():
    return (
        spark.readStream.table(f"{SOURCE_CATALOG}.{SOURCE_SCHEMA}.destinations")
        .withColumn("_ingested_at", current_timestamp())
    )

# COMMAND ----------

@dp.table(
    name="bronze_payments",
    comment="Raw payment records from samples.wanderbricks.payments"
)
@dp.expect("pk_not_null", "payment_id IS NOT NULL")
def bronze_payments():
    return (
        spark.readStream.table(f"{SOURCE_CATALOG}.{SOURCE_SCHEMA}.payments")
        .withColumn("_ingested_at", current_timestamp())
    )

# COMMAND ----------

@dp.table(
    name="bronze_countries",
    comment="Raw country reference data from samples.wanderbricks.countries"
)
@dp.expect("pk_not_null", "country IS NOT NULL")
def bronze_countries():
    return (
        spark.readStream.table(f"{SOURCE_CATALOG}.{SOURCE_SCHEMA}.countries")
        .withColumn("_ingested_at", current_timestamp())
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Junction and Supplementary Tables

# COMMAND ----------

@dp.table(
    name="bronze_amenities",
    comment="Raw amenity catalog from samples.wanderbricks.amenities"
)
@dp.expect("pk_not_null", "amenity_id IS NOT NULL")
def bronze_amenities():
    return (
        spark.readStream.table(f"{SOURCE_CATALOG}.{SOURCE_SCHEMA}.amenities")
        .withColumn("_ingested_at", current_timestamp())
    )

# COMMAND ----------

@dp.table(
    name="bronze_property_amenities",
    comment="Raw property-amenity junction from samples.wanderbricks.property_amenities"
)
@dp.expect("property_id_not_null", "property_id IS NOT NULL")
@dp.expect("amenity_id_not_null", "amenity_id IS NOT NULL")
def bronze_property_amenities():
    return (
        spark.readStream.table(f"{SOURCE_CATALOG}.{SOURCE_SCHEMA}.property_amenities")
        .withColumn("_ingested_at", current_timestamp())
    )

# COMMAND ----------

@dp.table(
    name="bronze_property_images",
    comment="Raw property image URLs from samples.wanderbricks.property_images"
)
@dp.expect("pk_not_null", "image_id IS NOT NULL")
def bronze_property_images():
    return (
        spark.readStream.table(f"{SOURCE_CATALOG}.{SOURCE_SCHEMA}.property_images")
        .withColumn("_ingested_at", current_timestamp())
    )

# COMMAND ----------

@dp.table(
    name="bronze_booking_updates",
    comment="Raw booking status change history from samples.wanderbricks.booking_updates"
)
@dp.expect("pk_not_null", "booking_update_id IS NOT NULL")
def bronze_booking_updates():
    return (
        spark.readStream.table(f"{SOURCE_CATALOG}.{SOURCE_SCHEMA}.booking_updates")
        .withColumn("_ingested_at", current_timestamp())
    )

# COMMAND ----------

@dp.table(
    name="bronze_page_views",
    comment="Raw page view analytics from samples.wanderbricks.page_views"
)
@dp.expect("pk_not_null", "view_id IS NOT NULL")
def bronze_page_views():
    return (
        spark.readStream.table(f"{SOURCE_CATALOG}.{SOURCE_SCHEMA}.page_views")
        .withColumn("_ingested_at", current_timestamp())
    )

# COMMAND ----------

@dp.table(
    name="bronze_employees",
    comment="Raw employee/staff records from samples.wanderbricks.employees"
)
@dp.expect("pk_not_null", "employee_id IS NOT NULL")
def bronze_employees():
    return (
        spark.readStream.table(f"{SOURCE_CATALOG}.{SOURCE_SCHEMA}.employees")
        .withColumn("_ingested_at", current_timestamp())
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Complex/Nested Tables

# COMMAND ----------

@dp.table(
    name="bronze_customer_support_logs",
    comment="Raw support tickets with nested messages from samples.wanderbricks.customer_support_logs"
)
@dp.expect("pk_not_null", "ticket_id IS NOT NULL")
def bronze_customer_support_logs():
    return (
        spark.readStream.table(f"{SOURCE_CATALOG}.{SOURCE_SCHEMA}.customer_support_logs")
        .withColumn("_ingested_at", current_timestamp())
    )

# COMMAND ----------

@dp.table(
    name="bronze_clickstream",
    comment="Raw clickstream events with nested metadata from samples.wanderbricks.clickstream"
)
@dp.expect("user_id_not_null", "user_id IS NOT NULL")
def bronze_clickstream():
    return (
        spark.readStream.table(f"{SOURCE_CATALOG}.{SOURCE_SCHEMA}.clickstream")
        .withColumn("_ingested_at", current_timestamp())
    )
