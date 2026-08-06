# Databricks notebook source
# DBTITLE 1,Gold Layer — Overview
# MAGIC %md
# MAGIC # Gold Layer — Business-Ready Aggregates
# MAGIC
# MAGIC Materialized views providing business metrics as defined in the WanderBricks Analytics Handbook.
# MAGIC All calculations follow handbook definitions exactly.

# COMMAND ----------

# DBTITLE 1,Imports
from pyspark import pipelines as dp
from pyspark.sql import functions as F
from pyspark.sql.window import Window

# COMMAND ----------

# DBTITLE 1,gold_revenue_daily
@dp.materialized_view(
    name="gold_revenue_daily",
    comment="Daily revenue metrics: GBV, net revenue, booking count by property and destination. GBV = SUM(total_amount) WHERE status = confirmed. Net Revenue = GBV * 0.15."
)
def gold_revenue_daily():
    bookings = spark.read.table("silver_bookings")
    properties = spark.read.table("silver_properties")
    return (
        bookings
        .filter(F.col("status") == "confirmed")
        .join(properties, "property_id", "left")
        .groupBy(
            bookings.created_at.cast("date").alias("booking_date"),
            bookings.property_id,
            properties.destination_id,
            properties.destination_name,
            properties.destination_country,
            properties.property_type
        )
        .agg(
            F.sum("total_amount").alias("gbv"),
            F.expr("SUM(total_amount) * 0.15").alias("net_revenue"),
            F.expr("SUM(total_amount) * 0.85").alias("host_payout"),
            F.count("booking_id").alias("booking_count"),
            F.sum("duration_nights").alias("total_nights"),
            F.avg("total_amount").alias("avg_booking_value")
        )
    )

# COMMAND ----------

# DBTITLE 1,gold_occupancy_monthly
@dp.materialized_view(
    name="gold_occupancy_monthly",
    comment="Monthly occupancy metrics: occupancy rate, ADR, ALOS by property and destination."
)
def gold_occupancy_monthly():
    bookings = spark.read.table("silver_bookings")
    properties = spark.read.table("silver_properties")
    active_bookings = bookings.filter(F.col("status").isin("confirmed", "completed"))
    return (
        active_bookings
        .join(properties, "property_id", "left")
        .groupBy(
            F.date_trunc("month", F.col("check_in")).alias("month"),
            active_bookings.property_id,
            properties.destination_id,
            properties.destination_name,
            properties.property_type
        )
        .agg(
            F.sum("duration_nights").alias("booked_nights"),
            F.sum("total_amount").alias("total_revenue"),
            F.expr("SUM(total_amount) / NULLIF(SUM(duration_nights), 0)").alias("adr"),
            F.avg("duration_nights").alias("alos"),
            F.count("booking_id").alias("booking_count"),
            F.avg("guests_count").alias("avg_guests")
        )
        .withColumn("occupancy_rate", F.col("booked_nights") / F.lit(30))
    )

# COMMAND ----------

# DBTITLE 1,gold_guest_satisfaction
@dp.materialized_view(
    name="gold_guest_satisfaction",
    comment="GSS per property with recency weighting (30d=3.0, 90d=2.0, 365d=1.0, older=0.5). Scale 1.0-5.0."
)
def gold_guest_satisfaction():
    reviews = spark.read.table("silver_reviews")
    properties = spark.read.table("silver_properties")
    reviews_weighted = reviews.withColumn(
        "days_since_review",
        F.datediff(F.current_date(), F.col("created_at").cast("date"))
    ).withColumn(
        "recency_weight",
        F.when(F.col("days_since_review") <= 30, 3.0)
        .when(F.col("days_since_review") <= 90, 2.0)
        .when(F.col("days_since_review") <= 365, 1.0)
        .otherwise(0.5)
    )
    return (
        reviews_weighted
        .join(properties.select("property_id", "destination_id", "destination_name", "host_id"), "property_id", "left")
        .groupBy("property_id", "destination_id", "destination_name", "host_id")
        .agg(
            F.expr("SUM(rating * recency_weight) / SUM(recency_weight)").alias("gss"),
            F.avg("rating").alias("avg_rating_unweighted"),
            F.count("review_id").alias("review_count"),
            F.sum(F.when(F.col("rating") < 3.0, 1).otherwise(0)).alias("negative_review_count"),
            F.expr("SUM(CASE WHEN rating < 3.0 THEN 1 ELSE 0 END) / COUNT(*)").alias("negative_review_rate"),
            F.min("created_at").alias("first_review_at"),
            F.max("created_at").alias("last_review_at")
        )
    )

# COMMAND ----------

# DBTITLE 1,gold_host_performance
@dp.materialized_view(
    name="gold_host_performance",
    comment="Host performance metrics for superhost qualification per Handbook S4."
)
def gold_host_performance():
    hosts = spark.read.table("silver_hosts")
    properties = spark.read.table("silver_properties")
    bookings = spark.read.table("silver_bookings")
    reviews = spark.read.table("silver_reviews")
    host_bookings = bookings.join(properties.select("property_id", "host_id"), "property_id", "inner")
    recent_bookings = host_bookings.filter(F.col("created_at") >= F.date_sub(F.current_date(), 90))
    host_booking_metrics = (
        recent_bookings.groupBy("host_id").agg(
            F.count(F.when(F.col("status").isin("confirmed", "completed"), 1)).alias("completed_bookings_90d"),
            F.count(F.when(F.col("status") == "cancelled_by_host", 1)).alias("host_cancellations_90d"),
            F.count("booking_id").alias("total_bookings_90d")
        ).withColumn("cancellation_rate", F.col("host_cancellations_90d") / F.greatest(F.col("total_bookings_90d"), F.lit(1)))
    )
    host_reviews = (
        reviews.join(properties.select("property_id", "host_id"), "property_id", "inner")
        .filter(F.col("created_at") >= F.date_sub(F.current_date(), 90))
        .groupBy("host_id").agg(
            F.avg("rating").alias("avg_rating_90d"),
            F.count("review_id").alias("review_count_90d")
        )
    )
    return (
        hosts
        .join(host_booking_metrics, "host_id", "left")
        .join(host_reviews, "host_id", "left")
        .select(
            "host_id", hosts.host_name, hosts.is_verified, hosts.is_active, hosts.joined_at,
            F.coalesce(F.col("completed_bookings_90d"), F.lit(0)).alias("completed_bookings_90d"),
            F.coalesce(F.col("host_cancellations_90d"), F.lit(0)).alias("host_cancellations_90d"),
            F.coalesce(F.col("cancellation_rate"), F.lit(0.0)).alias("cancellation_rate"),
            F.coalesce(F.col("avg_rating_90d"), F.lit(0.0)).alias("avg_rating_90d"),
            F.coalesce(F.col("review_count_90d"), F.lit(0)).alias("review_count_90d"),
            F.when(
                (F.coalesce(F.col("avg_rating_90d"), F.lit(0.0)) >= 4.5) &
                (F.coalesce(F.col("completed_bookings_90d"), F.lit(0)) >= 10) &
                (F.coalesce(F.col("cancellation_rate"), F.lit(1.0)) < 0.02),
                True
            ).otherwise(False).alias("qualifies_superhost")
        )
    )

# COMMAND ----------

# DBTITLE 1,gold_property_summary
@dp.materialized_view(
    name="gold_property_summary",
    comment="Denormalized property view with revenue, satisfaction, amenity count, image count."
)
def gold_property_summary():
    properties = spark.read.table("silver_properties")
    bookings = spark.read.table("silver_bookings")
    reviews = spark.read.table("silver_reviews")
    property_amenities = spark.read.table("silver_property_amenities")
    property_images = spark.read.table("silver_property_images")
    prop_revenue = (
        bookings.filter(F.col("status") == "confirmed")
        .groupBy("property_id").agg(
            F.sum("total_amount").alias("total_gbv"),
            F.count("booking_id").alias("total_bookings"),
            F.sum("duration_nights").alias("total_booked_nights"),
            F.avg("duration_nights").alias("avg_stay_nights")
        )
    )
    prop_reviews = reviews.groupBy("property_id").agg(
        F.avg("rating").alias("avg_rating"),
        F.count("review_id").alias("review_count")
    )
    prop_amenities = property_amenities.groupBy("property_id").agg(F.count("amenity_id").alias("amenity_count"))
    prop_images = property_images.groupBy("property_id").agg(F.count("image_id").alias("image_count"))
    return (
        properties
        .join(prop_revenue, "property_id", "left")
        .join(prop_reviews, "property_id", "left")
        .join(prop_amenities, "property_id", "left")
        .join(prop_images, "property_id", "left")
        .select(
            properties.property_id, properties.host_id, properties.destination_id,
            properties.destination_name, properties.destination_country, properties.continent,
            properties.title, properties.property_type, properties.base_price,
            properties.max_guests, properties.bedrooms, properties.bathrooms,
            properties.property_latitude, properties.property_longitude, properties.created_at,
            F.coalesce(F.col("total_gbv"), F.lit(0.0)).alias("total_gbv"),
            F.coalesce(F.col("total_bookings"), F.lit(0)).alias("total_bookings"),
            F.coalesce(F.col("total_booked_nights"), F.lit(0)).alias("total_booked_nights"),
            F.coalesce(F.col("avg_stay_nights"), F.lit(0.0)).alias("avg_stay_nights"),
            F.coalesce(F.col("avg_rating"), F.lit(0.0)).alias("avg_rating"),
            F.coalesce(F.col("review_count"), F.lit(0)).alias("review_count"),
            F.coalesce(F.col("amenity_count"), F.lit(0)).alias("amenity_count"),
            F.coalesce(F.col("image_count"), F.lit(0)).alias("image_count")
        )
    )