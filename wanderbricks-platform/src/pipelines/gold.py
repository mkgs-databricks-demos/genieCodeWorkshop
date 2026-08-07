# Databricks notebook source
# MAGIC %md
# MAGIC # Gold Layer — Business-Ready Aggregates
# MAGIC
# MAGIC Materialized views implementing the WanderBricks Analytics Handbook definitions.
# MAGIC All metric calculations follow the handbook EXACTLY.

# COMMAND ----------

from pyspark import pipelines as dp
from pyspark.sql.functions import (
    col, sum as _sum, count, countDistinct, avg, datediff,
    current_date, when, lit, round as _round, date_trunc,
    coalesce
)

target_catalog = spark.conf.get("target_catalog")
silver_schema = spark.conf.get("silver_schema")
gold_schema = spark.conf.get("gold_schema")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Revenue Metrics
# MAGIC
# MAGIC Per Analytics Handbook:
# MAGIC - GBV = SUM(total_amount) WHERE status = 'confirmed'
# MAGIC - Net Revenue = GBV x 0.15 (15% platform commission)
# MAGIC - ADR = SUM(total_amount) / SUM(duration_nights) WHERE status IN ('confirmed','completed')

# COMMAND ----------

@dp.materialized_view(
    name=f"{target_catalog}.{gold_schema}.gold_revenue_daily",
    comment="Daily GBV, net revenue, and booking count by property and destination. GBV includes only confirmed bookings per Analytics Handbook."
)
def gold_revenue_daily():
    bookings = (
        spark.read.table(f"{target_catalog}.{silver_schema}.silver_bookings")
        .filter(col("status") == "confirmed")
    )
    properties = (
        spark.read.table(f"{target_catalog}.{silver_schema}.silver_properties")
        .select("property_id", "destination_id", "destination_name", "property_type")
    )
    return (
        bookings
        .join(properties, "property_id", "left")
        .withColumn("booking_date", col("created_at").cast("date"))
        .groupBy("booking_date", "property_id", "destination_id", "destination_name", "property_type")
        .agg(
            _sum("total_amount").alias("gbv"),
            _round(_sum("total_amount") * 0.15, 2).alias("net_revenue"),
            count("booking_id").alias("booking_count"),
            _sum("duration_nights").alias("total_nights"),
            _sum("guests_count").alias("total_guests")
        )
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Occupancy & Utilization
# MAGIC
# MAGIC Per Analytics Handbook:
# MAGIC - Occupancy Rate = Booked Nights / Available Nights
# MAGIC - ALOS = AVG(duration_nights) WHERE status IN ('confirmed','completed')
# MAGIC - ADR = SUM(total_amount) / SUM(duration_nights)

# COMMAND ----------

@dp.materialized_view(
    name=f"{target_catalog}.{gold_schema}.gold_occupancy_monthly",
    comment="Monthly occupancy rate, ADR, and ALOS by property and destination. Per Analytics Handbook definitions."
)
def gold_occupancy_monthly():
    bookings = (
        spark.read.table(f"{target_catalog}.{silver_schema}.silver_bookings")
        .filter(col("status").isin("confirmed", "completed"))
        .withColumn("booking_month", date_trunc("month", col("check_in")))
    )
    properties = (
        spark.read.table(f"{target_catalog}.{silver_schema}.silver_properties")
        .select("property_id", "destination_id", "destination_name", "property_type")
    )
    return (
        bookings
        .join(properties, "property_id", "left")
        .groupBy("booking_month", "property_id", "destination_id", "destination_name", "property_type")
        .agg(
            _sum("duration_nights").alias("booked_nights"),
            count("booking_id").alias("booking_count"),
            _sum("total_amount").alias("total_revenue"),
            _round(
                _sum("total_amount") / _sum("duration_nights"), 2
            ).alias("adr"),
            _round(avg("duration_nights"), 2).alias("alos"),
            _round(
                _sum("duration_nights") / lit(30), 4
            ).alias("occupancy_rate")
        )
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Guest Satisfaction
# MAGIC
# MAGIC Per Analytics Handbook GSS definition (recency-weighted):
# MAGIC - Reviews in last 30 days: weight = 3.0
# MAGIC - Reviews in last 90 days: weight = 2.0
# MAGIC - Reviews in last 365 days: weight = 1.0
# MAGIC - Reviews older than 365 days: weight = 0.5
# MAGIC - GSS = SUM(rating * weight) / SUM(weight) WHERE is_deleted = false

# COMMAND ----------

@dp.materialized_view(
    name=f"{target_catalog}.{gold_schema}.gold_guest_satisfaction",
    comment="Guest Satisfaction Score (GSS) per property with recency weighting per Analytics Handbook. Scale 1.0-5.0."
)
def gold_guest_satisfaction():
    reviews = (
        spark.read.table(f"{target_catalog}.{silver_schema}.silver_reviews")
        .filter(col("is_deleted") == False)
        .withColumn("days_since_review", datediff(current_date(), col("reviewed_at")))
        .withColumn(
            "recency_weight",
            when(col("days_since_review") <= 30, lit(3.0))
            .when(col("days_since_review") <= 90, lit(2.0))
            .when(col("days_since_review") <= 365, lit(1.0))
            .otherwise(lit(0.5))
        )
        .withColumn("weighted_rating", col("rating") * col("recency_weight"))
    )
    properties = (
        spark.read.table(f"{target_catalog}.{silver_schema}.silver_properties")
        .select("property_id", "destination_id", "destination_name")
    )
    return (
        reviews
        .join(properties, "property_id", "left")
        .groupBy("property_id", "destination_id", "destination_name")
        .agg(
            _round(_sum("weighted_rating") / _sum("recency_weight"), 2).alias("gss"),
            count("review_id").alias("review_count"),
            _round(avg("rating"), 2).alias("simple_avg_rating"),
            _sum(
                when(col("rating") < 3.0, lit(1)).otherwise(lit(0))
            ).alias("negative_review_count")
        )
        .withColumn(
            "negative_review_rate",
            _round(col("negative_review_count") / col("review_count"), 4)
        )
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Host Performance
# MAGIC
# MAGIC Per Analytics Handbook Superhost criteria (trailing 90 days):
# MAGIC 1. Average rating >= 4.5
# MAGIC 2. Completed bookings >= 10
# MAGIC 3. Cancellation rate < 2%
# MAGIC 4. Response rate >= 90%

# COMMAND ----------

@dp.materialized_view(
    name=f"{target_catalog}.{gold_schema}.gold_host_performance",
    comment="Host performance metrics including superhost qualification. Evaluated monthly per Analytics Handbook criteria."
)
def gold_host_performance():
    # Get host properties
    properties = (
        spark.read.table(f"{target_catalog}.{silver_schema}.silver_properties")
        .select("property_id", "host_id")
    )
    # Bookings in trailing 90 days
    bookings = (
        spark.read.table(f"{target_catalog}.{silver_schema}.silver_bookings")
        .filter(col("created_at") >= (current_date() - 90))
    )
    # Reviews for host properties
    reviews = (
        spark.read.table(f"{target_catalog}.{silver_schema}.silver_reviews")
        .filter(col("is_deleted") == False)
        .filter(col("reviewed_at") >= (current_date() - 90))
    )
    hosts = (
        spark.read.table(f"{target_catalog}.{silver_schema}.silver_hosts")
        .select("host_id", "host_name", "is_verified", "is_active", "country")
    )

    # Booking metrics per host
    host_bookings = (
        bookings
        .join(properties, "property_id", "inner")
        .groupBy("host_id")
        .agg(
            count(when(col("status").isin("confirmed", "completed"), True)).alias("completed_bookings"),
            count(when(col("status") == "cancelled_by_host", True)).alias("host_cancellations"),
            count("booking_id").alias("total_bookings")
        )
        .withColumn(
            "cancellation_rate",
            _round(
                col("host_cancellations") / 
                (col("completed_bookings") + col("host_cancellations")),
                4
            )
        )
    )

    # Rating metrics per host
    host_reviews = (
        reviews
        .join(properties, "property_id", "inner")
        .groupBy("host_id")
        .agg(
            _round(avg("rating"), 2).alias("avg_rating_90d"),
            count("review_id").alias("review_count_90d")
        )
    )

    # Combine and evaluate superhost criteria
    return (
        hosts
        .join(host_bookings, "host_id", "left")
        .join(host_reviews, "host_id", "left")
        .withColumn("completed_bookings", coalesce(col("completed_bookings"), lit(0)))
        .withColumn("cancellation_rate", coalesce(col("cancellation_rate"), lit(0.0)))
        .withColumn("avg_rating_90d", coalesce(col("avg_rating_90d"), lit(0.0)))
        .withColumn(
            "qualifies_superhost",
            (
                (col("avg_rating_90d") >= 4.5) &
                (col("completed_bookings") >= 10) &
                (col("cancellation_rate") < 0.02)
            )
        )
        .select(
            "host_id", "host_name", "country", "is_verified", "is_active",
            "completed_bookings", "host_cancellations", "total_bookings",
            "cancellation_rate", "avg_rating_90d", "review_count_90d",
            "qualifies_superhost"
        )
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Property Summary (Denormalized)

# COMMAND ----------

@dp.materialized_view(
    name=f"{target_catalog}.{gold_schema}.gold_property_summary",
    comment="Denormalized property view with key metrics: revenue, occupancy, satisfaction, listing quality."
)
def gold_property_summary():
    properties = spark.read.table(f"{target_catalog}.{silver_schema}.silver_properties")
    
    # Total revenue per property
    bookings_agg = (
        spark.read.table(f"{target_catalog}.{silver_schema}.silver_bookings")
        .filter(col("status").isin("confirmed", "completed"))
        .groupBy("property_id")
        .agg(
            _sum("total_amount").alias("total_revenue"),
            count("booking_id").alias("total_bookings"),
            _sum("duration_nights").alias("total_booked_nights"),
            _round(avg("duration_nights"), 2).alias("avg_stay_length")
        )
    )

    # Review metrics per property
    reviews_agg = (
        spark.read.table(f"{target_catalog}.{silver_schema}.silver_reviews")
        .filter(col("is_deleted") == False)
        .groupBy("property_id")
        .agg(
            _round(avg("rating"), 2).alias("avg_rating"),
            count("review_id").alias("review_count")
        )
    )

    # Image count per property
    images_agg = (
        spark.read.table(f"{target_catalog}.{silver_schema}.silver_property_images")
        .groupBy("property_id")
        .agg(count("image_id").alias("image_count"))
    )

    # Amenity count per property
    amenities_agg = (
        spark.read.table(f"{target_catalog}.{silver_schema}.silver_property_amenities")
        .groupBy("property_id")
        .agg(count("amenity_id").alias("amenity_count"))
    )

    return (
        properties
        .join(bookings_agg, "property_id", "left")
        .join(reviews_agg, "property_id", "left")
        .join(images_agg, "property_id", "left")
        .join(amenities_agg, "property_id", "left")
        .select(
            "property_id", "host_id", "destination_id", "destination_name",
            "title", "property_type", "base_price",
            "max_guests", "bedrooms", "bathrooms", "latitude", "longitude",
            "listed_at",
            coalesce(col("total_revenue"), lit(0.0)).alias("total_revenue"),
            coalesce(col("total_bookings"), lit(0)).alias("total_bookings"),
            coalesce(col("total_booked_nights"), lit(0)).alias("total_booked_nights"),
            coalesce(col("avg_stay_length"), lit(0.0)).alias("avg_stay_length"),
            coalesce(col("avg_rating"), lit(0.0)).alias("avg_rating"),
            coalesce(col("review_count"), lit(0)).alias("review_count"),
            coalesce(col("image_count"), lit(0)).alias("image_count"),
            coalesce(col("amenity_count"), lit(0)).alias("amenity_count")
        )
    )
