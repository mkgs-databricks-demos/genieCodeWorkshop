# Databricks notebook source
# MAGIC %md
# MAGIC # Silver Layer — Cleaned & Conformed Tables
# MAGIC
# MAGIC Materialized views that read from bronze, deduplicate, cast types,
# MAGIC handle nulls, and join dimension context.

# COMMAND ----------

from pyspark import pipelines as dp
from pyspark.sql.functions import col, coalesce, lit, datediff, trim, lower


# COMMAND ----------

# MAGIC %md
# MAGIC ## Core Dimension Tables

# COMMAND ----------

@dp.materialized_view(
    name="silver_destinations",
    comment="Cleaned destination reference with standardized naming"
)
@dp.expect("pk_not_null", "destination_id IS NOT NULL")
def silver_destinations():
    return (
        spark.read.table("bronze_destinations")
        .dropDuplicates(["destination_id"])
        .select(
            col("destination_id"),
            trim(col("destination")).alias("destination_name"),
            trim(col("country")).alias("country"),
            trim(col("state_or_province")).alias("state_or_province"),
            col("state_or_province_code")
        )
    )

# COMMAND ----------

@dp.materialized_view(
    name="silver_countries",
    comment="Cleaned country reference data"
)
@dp.expect("pk_not_null", "country IS NOT NULL")
def silver_countries():
    return (
        spark.read.table("bronze_countries")
        .dropDuplicates(["country"])
        .select(
            trim(col("country")).alias("country"),
            col("country_code"),
            trim(col("continent")).alias("continent")
        )
    )

# COMMAND ----------

@dp.materialized_view(
    name="silver_amenities",
    comment="Cleaned amenity catalog"
)
@dp.expect("pk_not_null", "amenity_id IS NOT NULL")
def silver_amenities():
    return (
        spark.read.table("bronze_amenities")
        .dropDuplicates(["amenity_id"])
        .select(
            col("amenity_id"),
            trim(col("name")).alias("amenity_name"),
            trim(col("category")).alias("category"),
            col("icon")
        )
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Core Entity Tables

# COMMAND ----------

@dp.materialized_view(
    name="silver_properties",
    comment="Cleaned property listings with destination context joined"
)
@dp.expect("pk_not_null", "property_id IS NOT NULL")
@dp.expect("valid_price", "base_price BETWEEN 10 AND 10000")
def silver_properties():
    properties = (
        spark.read.table("bronze_properties")
        .dropDuplicates(["property_id"])
    )
    destinations = (
        spark.read.table("bronze_destinations")
        .dropDuplicates(["destination_id"])
        .select(
            col("destination_id"),
            trim(col("destination")).alias("destination_name"),
            trim(col("country")).alias("destination_country")
        )
    )
    return (
        properties.join(destinations, "destination_id", "left")
        .select(
            col("property_id"),
            col("host_id"),
            col("destination_id"),
            col("destination_name"),
            col("destination_country"),
            trim(col("title")).alias("title"),
            col("description"),
            col("base_price").cast("double").alias("base_price"),
            trim(col("property_type")).alias("property_type"),
            coalesce(col("max_guests"), lit(1)).alias("max_guests"),
            coalesce(col("bedrooms"), lit(0)).alias("bedrooms"),
            coalesce(col("bathrooms"), lit(0)).alias("bathrooms"),
            col("property_latitude").cast("double").alias("latitude"),
            col("property_longitude").cast("double").alias("longitude"),
            col("created_at").alias("listed_at")
        )
    )

# COMMAND ----------

@dp.materialized_view(
    name="silver_bookings",
    comment="Cleaned bookings with duration calculated and status standardized"
)
@dp.expect("pk_not_null", "booking_id IS NOT NULL")
@dp.expect("valid_dates", "check_out > check_in")
@dp.expect("positive_amount", "total_amount > 0")
def silver_bookings():
    return (
        spark.read.table("bronze_bookings")
        .dropDuplicates(["booking_id"])
        .select(
            col("booking_id"),
            col("user_id"),
            col("property_id"),
            col("check_in"),
            col("check_out"),
            datediff(col("check_out"), col("check_in")).alias("duration_nights"),
            coalesce(col("guests_count"), lit(1)).alias("guests_count"),
            col("total_amount").cast("double").alias("total_amount"),
            lower(trim(col("status"))).alias("status"),
            col("created_at"),
            col("updated_at")
        )
    )

# COMMAND ----------

@dp.materialized_view(
    name="silver_reviews",
    comment="Cleaned reviews with booking and property context"
)
@dp.expect("pk_not_null", "review_id IS NOT NULL")
@dp.expect("valid_rating", "rating BETWEEN 1.0 AND 5.0")
def silver_reviews():
    return (
        spark.read.table("bronze_reviews")
        .dropDuplicates(["review_id"])
        .select(
            col("review_id"),
            col("booking_id"),
            col("property_id"),
            col("user_id"),
            col("rating").cast("double").alias("rating"),
            trim(col("comment")).alias("review_text"),
            col("is_deleted"),
            col("created_at").alias("reviewed_at"),
            col("updated_at")
        )
    )

# COMMAND ----------

@dp.materialized_view(
    name="silver_users",
    comment="Cleaned guest/user profiles"
)
@dp.expect("pk_not_null", "user_id IS NOT NULL")
def silver_users():
    return (
        spark.read.table("bronze_users")
        .dropDuplicates(["user_id"])
        .select(
            col("user_id"),
            trim(col("name")).alias("user_name"),
            col("email"),
            trim(col("country")).alias("country"),
            trim(col("user_type")).alias("user_type"),
            col("is_business"),
            col("company_name"),
            col("created_at").alias("registered_at")
        )
    )

# COMMAND ----------

@dp.materialized_view(
    name="silver_hosts",
    comment="Cleaned host profiles with verification status"
)
@dp.expect("pk_not_null", "host_id IS NOT NULL")
def silver_hosts():
    return (
        spark.read.table("bronze_hosts")
        .dropDuplicates(["host_id"])
        .select(
            col("host_id"),
            trim(col("name")).alias("host_name"),
            col("email"),
            col("phone"),
            col("is_verified"),
            col("is_active"),
            col("rating").cast("double").alias("host_rating"),
            trim(col("country")).alias("country"),
            col("joined_at")
        )
    )

# COMMAND ----------

@dp.materialized_view(
    name="silver_payments",
    comment="Cleaned payment records with standardized method names"
)
@dp.expect("pk_not_null", "payment_id IS NOT NULL")
@dp.expect("positive_amount", "amount > 0")
def silver_payments():
    return (
        spark.read.table("bronze_payments")
        .dropDuplicates(["payment_id"])
        .select(
            col("payment_id"),
            col("booking_id"),
            col("amount").cast("double").alias("amount"),
            lower(trim(col("payment_method"))).alias("payment_method"),
            lower(trim(col("status"))).alias("payment_status"),
            col("payment_date")
        )
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Junction & Reference Tables

# COMMAND ----------

@dp.materialized_view(
    name="silver_property_amenities",
    comment="Property-amenity relationships with amenity names joined"
)
@dp.expect("property_id_not_null", "property_id IS NOT NULL")
@dp.expect("amenity_id_not_null", "amenity_id IS NOT NULL")
def silver_property_amenities():
    pa = (
        spark.read.table("bronze_property_amenities")
        .dropDuplicates(["property_id", "amenity_id"])
    )
    amenities = (
        spark.read.table("bronze_amenities")
        .dropDuplicates(["amenity_id"])
        .select(col("amenity_id"), trim(col("name")).alias("amenity_name"), col("category"))
    )
    return pa.join(amenities, "amenity_id", "left")

# COMMAND ----------

@dp.materialized_view(
    name="silver_property_images",
    comment="Cleaned property image metadata"
)
@dp.expect("pk_not_null", "image_id IS NOT NULL")
def silver_property_images():
    return (
        spark.read.table("bronze_property_images")
        .dropDuplicates(["image_id"])
        .select(
            col("image_id"),
            col("property_id"),
            col("url").alias("image_url"),
            col("sequence"),
            col("is_primary"),
            col("uploaded_at")
        )
    )
