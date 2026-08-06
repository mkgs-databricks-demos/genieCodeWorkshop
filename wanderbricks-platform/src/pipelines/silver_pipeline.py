# Databricks notebook source
# MAGIC %md
# MAGIC # Silver Layer — Cleaned & Conformed
# MAGIC
# MAGIC Materialized views that:
# MAGIC - Deduplicate on natural keys
# MAGIC - Cast types appropriately
# MAGIC - Handle nulls with sensible defaults
# MAGIC - Standardize naming conventions
# MAGIC - Join dimension keys where needed

# COMMAND ----------

from pyspark import pipelines as dp
from pyspark.sql.functions import (
    col, trim, lower, coalesce, lit, datediff, when
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Core Entities

# COMMAND ----------

@dp.materialized_view(
    name="silver_properties",
    comment="Cleaned property listings with standardized types and null handling"
)
@dp.expect("pk_not_null", "property_id IS NOT NULL")
@dp.expect("valid_price", "base_price > 0")
def silver_properties():
    return (
        spark.read.table("bronze_properties")
        .dropDuplicates(["property_id"])
        .select(
            col("property_id"),
            col("host_id"),
            col("destination_id"),
            trim(col("title")).alias("title"),
            col("description"),
            col("base_price").cast("double").alias("base_price"),
            trim(col("property_type")).alias("property_type"),
            coalesce(col("max_guests"), lit(1)).alias("max_guests"),
            coalesce(col("bedrooms"), lit(0)).alias("bedrooms"),
            coalesce(col("bathrooms"), lit(0)).alias("bathrooms"),
            col("property_latitude").cast("double").alias("latitude"),
            col("property_longitude").cast("double").alias("longitude"),
            col("created_at")
        )
    )

# COMMAND ----------

@dp.materialized_view(
    name="silver_bookings",
    comment="Cleaned bookings with computed duration_nights and standardized status"
)
@dp.expect("pk_not_null", "booking_id IS NOT NULL")
@dp.expect("valid_dates", "check_out >= check_in")
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
            col("guests_count"),
            col("total_amount").cast("double").alias("total_amount"),
            lower(trim(col("status"))).alias("status"),
            col("created_at"),
            col("updated_at")
        )
    )

# COMMAND ----------

@dp.materialized_view(
    name="silver_reviews",
    comment="Cleaned reviews excluding deleted entries"
)
@dp.expect("pk_not_null", "review_id IS NOT NULL")
@dp.expect("valid_rating", "rating BETWEEN 1.0 AND 5.0")
def silver_reviews():
    return (
        spark.read.table("bronze_reviews")
        .filter(col("is_deleted") == False)
        .dropDuplicates(["review_id"])
        .select(
            col("review_id"),
            col("booking_id"),
            col("property_id"),
            col("user_id"),
            col("rating").cast("double").alias("rating"),
            trim(col("comment")).alias("comment"),
            col("created_at"),
            col("updated_at")
        )
    )

# COMMAND ----------

@dp.materialized_view(
    name="silver_users",
    comment="Cleaned guest profiles with standardized fields"
)
@dp.expect("pk_not_null", "user_id IS NOT NULL")
def silver_users():
    return (
        spark.read.table("bronze_users")
        .dropDuplicates(["user_id"])
        .select(
            col("user_id"),
            trim(col("name")).alias("user_name"),
            lower(trim(col("email"))).alias("email"),
            trim(col("country")).alias("country"),
            lower(trim(col("user_type"))).alias("user_type"),
            col("is_business"),
            trim(col("company_name")).alias("company_name"),
            col("created_at")
        )
    )

# COMMAND ----------

@dp.materialized_view(
    name="silver_hosts",
    comment="Cleaned host profiles with standardized fields"
)
@dp.expect("pk_not_null", "host_id IS NOT NULL")
def silver_hosts():
    return (
        spark.read.table("bronze_hosts")
        .dropDuplicates(["host_id"])
        .select(
            col("host_id"),
            trim(col("name")).alias("host_name"),
            lower(trim(col("email"))).alias("email"),
            col("phone"),
            col("is_verified"),
            col("is_active"),
            col("rating").cast("double").alias("rating"),
            trim(col("country")).alias("country"),
            col("joined_at")
        )
    )

# COMMAND ----------

@dp.materialized_view(
    name="silver_destinations",
    comment="Cleaned destinations joined with country continent data"
)
@dp.expect("pk_not_null", "destination_id IS NOT NULL")
def silver_destinations():
    destinations = spark.read.table("bronze_destinations")
    countries = spark.read.table("bronze_countries")
    return (
        destinations
        .join(countries, destinations["country"] == countries["country"], "left")
        .dropDuplicates(["destination_id"])
        .select(
            destinations["destination_id"],
            trim(destinations["destination"]).alias("destination_name"),
            trim(destinations["country"]).alias("country"),
            countries["country_code"],
            countries["continent"],
            trim(destinations["state_or_province"]).alias("state_or_province"),
            destinations["state_or_province_code"],
            destinations["description"]
        )
    )

# COMMAND ----------

@dp.materialized_view(
    name="silver_payments",
    comment="Cleaned payment records with standardized method and status"
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
            lower(trim(col("status"))).alias("status"),
            col("payment_date")
        )
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Reference and Junction Tables

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

@dp.materialized_view(
    name="silver_property_amenities",
    comment="Cleaned property-amenity junction table"
)
@dp.expect("property_id_not_null", "property_id IS NOT NULL")
@dp.expect("amenity_id_not_null", "amenity_id IS NOT NULL")
def silver_property_amenities():
    return (
        spark.read.table("bronze_property_amenities")
        .dropDuplicates(["property_id", "amenity_id"])
        .select(
            col("property_id"),
            col("amenity_id")
        )
    )

# COMMAND ----------

@dp.materialized_view(
    name="silver_property_images",
    comment="Cleaned property images with sequence ordering"
)
@dp.expect("pk_not_null", "image_id IS NOT NULL")
def silver_property_images():
    return (
        spark.read.table("bronze_property_images")
        .dropDuplicates(["image_id"])
        .select(
            col("image_id"),
            col("property_id"),
            trim(col("url")).alias("image_url"),
            col("sequence"),
            col("is_primary"),
            col("uploaded_at")
        )
    )

# COMMAND ----------

@dp.materialized_view(
    name="silver_booking_updates",
    comment="Cleaned booking status change history"
)
@dp.expect("pk_not_null", "booking_update_id IS NOT NULL")
def silver_booking_updates():
    return (
        spark.read.table("bronze_booking_updates")
        .dropDuplicates(["booking_update_id"])
        .select(
            col("booking_update_id"),
            col("booking_id"),
            col("property_id"),
            col("user_id"),
            lower(trim(col("status"))).alias("status"),
            col("total_amount").cast("double").alias("total_amount"),
            col("check_in"),
            col("check_out"),
            col("guests_count"),
            col("created_at"),
            col("updated_at")
        )
    )

# COMMAND ----------

@dp.materialized_view(
    name="silver_page_views",
    comment="Cleaned page view analytics"
)
@dp.expect("pk_not_null", "view_id IS NOT NULL")
def silver_page_views():
    return (
        spark.read.table("bronze_page_views")
        .dropDuplicates(["view_id"])
        .select(
            col("view_id"),
            col("user_id"),
            col("property_id"),
            lower(trim(col("device_type"))).alias("device_type"),
            trim(col("page_url")).alias("page_url"),
            lower(trim(col("referrer"))).alias("referrer"),
            col("timestamp").alias("view_timestamp")
        )
    )

# COMMAND ----------

@dp.materialized_view(
    name="silver_employees",
    comment="Cleaned employee/staff records"
)
@dp.expect("pk_not_null", "employee_id IS NOT NULL")
def silver_employees():
    return (
        spark.read.table("bronze_employees")
        .dropDuplicates(["employee_id"])
        .select(
            col("employee_id"),
            col("host_id"),
            trim(col("name")).alias("employee_name"),
            lower(trim(col("role"))).alias("role"),
            lower(trim(col("email"))).alias("email"),
            col("phone"),
            trim(col("country")).alias("country"),
            col("joined_at"),
            col("end_service_date"),
            col("is_currently_employed")
        )
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Complex/Nested Tables

# COMMAND ----------

@dp.materialized_view(
    name="silver_customer_support_logs",
    comment="Cleaned support tickets preserving nested message structure"
)
@dp.expect("pk_not_null", "ticket_id IS NOT NULL")
def silver_customer_support_logs():
    return (
        spark.read.table("bronze_customer_support_logs")
        .dropDuplicates(["ticket_id"])
        .select(
            col("ticket_id"),
            col("user_id"),
            trim(col("support_agent_id")).alias("support_agent_id"),
            col("messages"),
            col("created_at")
        )
    )

# COMMAND ----------

@dp.materialized_view(
    name="silver_clickstream",
    comment="Cleaned clickstream events with flattened metadata"
)
@dp.expect("user_id_not_null", "user_id IS NOT NULL")
def silver_clickstream():
    return (
        spark.read.table("bronze_clickstream")
        .select(
            col("user_id"),
            col("property_id"),
            lower(trim(col("event"))).alias("event_type"),
            lower(col("metadata.device")).alias("device"),
            lower(col("metadata.referrer")).alias("referrer"),
            col("timestamp").alias("event_timestamp")
        )
    )
