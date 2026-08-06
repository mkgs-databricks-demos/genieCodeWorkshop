# Databricks notebook source
# DBTITLE 1,Silver Layer — Overview
# MAGIC %md
# MAGIC # Silver Layer — Cleaned & Conformed Tables
# MAGIC
# MAGIC Materialized views that read from bronze streaming tables.
# MAGIC Transformations: deduplication, type casting, null handling, name standardization, dimension joins.

# COMMAND ----------

# DBTITLE 1,Imports
from pyspark import pipelines as dp
from pyspark.sql import functions as F

# COMMAND ----------

# DBTITLE 1,silver_destinations
@dp.materialized_view(
    name="silver_destinations",
    comment="Cleaned destination dimension with country context"
)
@dp.expect("pk_not_null", "destination_id IS NOT NULL")
def silver_destinations():
    destinations = spark.read.table("bronze_destinations")
    countries = spark.read.table("bronze_countries")
    return (
        destinations
        .dropDuplicates(["destination_id"])
        .join(countries, destinations.country == countries.country, "left")
        .select(
            destinations.destination_id,
            destinations.destination.alias("destination_name"),
            destinations.country.alias("country_name"),
            destinations.state_or_province,
            destinations.state_or_province_code,
            destinations.description,
            countries.country_code,
            countries.continent
        )
    )

# COMMAND ----------

# DBTITLE 1,silver_countries
@dp.materialized_view(
    name="silver_countries",
    comment="Cleaned country reference dimension"
)
@dp.expect("pk_not_null", "country_name IS NOT NULL")
def silver_countries():
    return (
        spark.read.table("bronze_countries")
        .dropDuplicates(["country"])
        .select(
            F.col("country").alias("country_name"),
            "country_code",
            "continent"
        )
    )

# COMMAND ----------

# DBTITLE 1,silver_hosts
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
            "host_id",
            F.col("name").alias("host_name"),
            "email",
            "phone",
            F.coalesce(F.col("is_verified"), F.lit(False)).alias("is_verified"),
            F.coalesce(F.col("is_active"), F.lit(True)).alias("is_active"),
            F.coalesce(F.col("rating"), F.lit(0.0)).cast("double").alias("host_rating"),
            "country",
            "joined_at"
        )
    )

# COMMAND ----------

# DBTITLE 1,silver_users
@dp.materialized_view(
    name="silver_users",
    comment="Cleaned user profiles with standardized fields"
)
@dp.expect("pk_not_null", "user_id IS NOT NULL")
def silver_users():
    return (
        spark.read.table("bronze_users")
        .dropDuplicates(["user_id"])
        .select(
            "user_id",
            F.col("name").alias("user_name"),
            "email",
            "country",
            F.coalesce(F.col("user_type"), F.lit("guest")).alias("user_type"),
            F.coalesce(F.col("is_business"), F.lit(False)).alias("is_business"),
            "company_name",
            "created_at"
        )
    )

# COMMAND ----------

# DBTITLE 1,silver_amenities
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
            "amenity_id",
            F.col("name").alias("amenity_name"),
            "category",
            "icon"
        )
    )

# COMMAND ----------

# DBTITLE 1,silver_properties
@dp.materialized_view(
    name="silver_properties",
    comment="Cleaned property listings with destination name joined"
)
@dp.expect("pk_not_null", "property_id IS NOT NULL")
@dp.expect("valid_price", "base_price > 0")
def silver_properties():
    properties = spark.read.table("bronze_properties")
    destinations = spark.read.table("silver_destinations")
    return (
        properties
        .dropDuplicates(["property_id"])
        .join(destinations, "destination_id", "left")
        .select(
            properties.property_id,
            properties.host_id,
            properties.destination_id,
            destinations.destination_name,
            destinations.country_name.alias("destination_country"),
            destinations.continent,
            properties.title,
            properties.description,
            F.coalesce(properties.base_price, F.lit(0.0)).cast("double").alias("base_price"),
            properties.property_type,
            F.coalesce(properties.max_guests, F.lit(1)).alias("max_guests"),
            F.coalesce(properties.bedrooms, F.lit(0)).alias("bedrooms"),
            F.coalesce(properties.bathrooms, F.lit(0)).alias("bathrooms"),
            properties.property_latitude,
            properties.property_longitude,
            properties.created_at
        )
    )

# COMMAND ----------

# DBTITLE 1,silver_bookings
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
            "booking_id",
            "user_id",
            "property_id",
            "check_in",
            "check_out",
            F.datediff("check_out", "check_in").alias("duration_nights"),
            F.coalesce(F.col("guests_count"), F.lit(1)).alias("guests_count"),
            F.col("total_amount").cast("double").alias("total_amount"),
            F.lower(F.trim(F.coalesce(F.col("status"), F.lit("pending")))).alias("status"),
            "created_at",
            "updated_at"
        )
    )

# COMMAND ----------

# DBTITLE 1,silver_reviews
@dp.materialized_view(
    name="silver_reviews",
    comment="Cleaned reviews excluding deleted, with validated ratings"
)
@dp.expect("pk_not_null", "review_id IS NOT NULL")
@dp.expect("valid_rating", "rating BETWEEN 1.0 AND 5.0")
def silver_reviews():
    return (
        spark.read.table("bronze_reviews")
        .filter(F.col("is_deleted") == False)
        .dropDuplicates(["review_id"])
        .select(
            "review_id",
            "booking_id",
            "property_id",
            "user_id",
            F.col("rating").cast("double").alias("rating"),
            "comment",
            "created_at",
            "updated_at"
        )
    )

# COMMAND ----------

# DBTITLE 1,silver_payments
@dp.materialized_view(
    name="silver_payments",
    comment="Cleaned payment records with standardized types"
)
@dp.expect("pk_not_null", "payment_id IS NOT NULL")
@dp.expect("positive_amount", "amount > 0")
def silver_payments():
    return (
        spark.read.table("bronze_payments")
        .dropDuplicates(["payment_id"])
        .select(
            "payment_id",
            "booking_id",
            F.col("amount").cast("double").alias("amount"),
            F.lower(F.trim(F.col("payment_method"))).alias("payment_method"),
            F.lower(F.trim(F.col("status"))).alias("status"),
            "payment_date"
        )
    )

# COMMAND ----------

# DBTITLE 1,silver_property_amenities
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
        .select("property_id", "amenity_id")
    )

# COMMAND ----------

# DBTITLE 1,silver_property_images
@dp.materialized_view(
    name="silver_property_images",
    comment="Cleaned property image records"
)
@dp.expect("pk_not_null", "image_id IS NOT NULL")
def silver_property_images():
    return (
        spark.read.table("bronze_property_images")
        .dropDuplicates(["image_id"])
        .select(
            "image_id",
            "property_id",
            "url",
            F.coalesce(F.col("sequence"), F.lit(0)).alias("sequence"),
            F.coalesce(F.col("is_primary"), F.lit(False)).alias("is_primary"),
            "uploaded_at"
        )
    )

# COMMAND ----------

# DBTITLE 1,silver_booking_updates
@dp.materialized_view(
    name="silver_booking_updates",
    comment="Cleaned booking status change events"
)
@dp.expect("pk_not_null", "booking_update_id IS NOT NULL")
def silver_booking_updates():
    return (
        spark.read.table("bronze_booking_updates")
        .dropDuplicates(["booking_update_id"])
        .select(
            "booking_update_id",
            "booking_id",
            "property_id",
            "user_id",
            F.lower(F.trim(F.col("status"))).alias("status"),
            "check_in",
            "check_out",
            F.coalesce(F.col("guests_count"), F.lit(1)).alias("guests_count"),
            F.col("total_amount").cast("double").alias("total_amount"),
            "created_at",
            "updated_at"
        )
    )

# COMMAND ----------

# DBTITLE 1,silver_page_views
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
            "view_id",
            "user_id",
            "property_id",
            "page_url",
            F.lower(F.trim(F.col("device_type"))).alias("device_type"),
            F.lower(F.trim(F.col("referrer"))).alias("referrer"),
            F.col("timestamp").alias("view_timestamp")
        )
    )

# COMMAND ----------

# DBTITLE 1,silver_employees
@dp.materialized_view(
    name="silver_employees",
    comment="Cleaned employee records"
)
@dp.expect("pk_not_null", "employee_id IS NOT NULL")
def silver_employees():
    return (
        spark.read.table("bronze_employees")
        .dropDuplicates(["employee_id"])
        .select(
            "employee_id",
            "host_id",
            F.col("name").alias("employee_name"),
            "role",
            "email",
            "phone",
            "country",
            "joined_at",
            "end_service_date",
            F.coalesce(F.col("is_currently_employed"), F.lit(True)).alias("is_currently_employed")
        )
    )

# COMMAND ----------

# DBTITLE 1,silver_customer_support_logs
@dp.materialized_view(
    name="silver_customer_support_logs",
    comment="Cleaned customer support tickets with parsed timestamps"
)
@dp.expect("pk_not_null", "ticket_id IS NOT NULL")
def silver_customer_support_logs():
    return (
        spark.read.table("bronze_customer_support_logs")
        .dropDuplicates(["ticket_id"])
        .select(
            "ticket_id",
            "user_id",
            "support_agent_id",
            F.to_timestamp(F.col("created_at")).alias("created_at"),
            "messages"
        )
    )

# COMMAND ----------

# DBTITLE 1,silver_clickstream
@dp.materialized_view(
    name="silver_clickstream",
    comment="Cleaned clickstream events with flattened metadata"
)
@dp.expect("user_id_not_null", "user_id IS NOT NULL")
def silver_clickstream():
    return (
        spark.read.table("bronze_clickstream")
        .select(
            "user_id",
            "property_id",
            F.lower(F.trim(F.col("event"))).alias("event_type"),
            F.col("metadata.device").alias("device"),
            F.col("metadata.referrer").alias("referrer"),
            F.col("timestamp").alias("event_timestamp")
        )
    )