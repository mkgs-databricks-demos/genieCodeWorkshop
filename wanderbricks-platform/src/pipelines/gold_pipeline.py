# Databricks notebook source
# MAGIC %md
# MAGIC # Gold Layer — Business Aggregates
# MAGIC
# MAGIC Materialized views following the WanderBricks Analytics Handbook definitions.
# MAGIC
# MAGIC ## Metrics implemented:
# MAGIC - **GBV**: SUM(total_amount) WHERE status = 'confirmed'
# MAGIC - **Net Revenue**: GBV x 0.15 (15% platform commission)
# MAGIC - **ADR**: SUM(total_amount) / SUM(DATEDIFF(check_out, check_in)) for confirmed/completed
# MAGIC - **ALOS**: AVG(DATEDIFF(check_out, check_in)) for confirmed/completed
# MAGIC - **GSS**: Recency-weighted rating (30d=3.0, 90d=2.0, 365d=1.0, >365d=0.5), is_deleted=false
# MAGIC - **Superhost**: avg_rating>=4.5 AND completed_bookings>=10 AND cancellation_rate<0.02

# COMMAND ----------

from pyspark import pipelines as dp
from pyspark.sql.functions import (
    col, sum as spark_sum, count, countDistinct, avg,
    when, datediff, date_trunc, current_date, trunc,
    coalesce, lit, round as spark_round,
    max as spark_max
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## gold_revenue_daily
# MAGIC
# MAGIC Daily GBV, net revenue (15% commission), and booking count by property/destination.
# MAGIC Source: Analytics Handbook §1.1 (GBV), §1.2 (Net Revenue)

# COMMAND ----------

@dp.materialized_view(
    name="gold_revenue_daily",
    comment="Daily GBV and net revenue (15% commission) by property and destination. Grain: booking_date x property_id x destination_id."
)
def gold_revenue_daily():
    bookings = spark.read.table("silver_bookings")
    props = spark.read.table("silver_properties")
    dests = spark.read.table("silver_destinations")

    confirmed = (
        bookings
        .filter(col("status") == "confirmed")
        .select(
            date_trunc("day", col("created_at")).cast("date").alias("booking_date"),
            col("property_id"),
            col("total_amount"),
            col("duration_nights")
        )
    )

    with_dims = (
        confirmed
        .join(props.select("property_id", "destination_id", "property_type"), "property_id", "left")
        .join(dests.select("destination_id", "destination_name", "country", "continent"), "destination_id", "left")
    )

    return (
        with_dims
        .groupBy(
            "booking_date", "property_id", "destination_id",
            "destination_name", "country", "continent", "property_type"
        )
        .agg(
            spark_sum("total_amount").alias("gbv"),
            (spark_sum("total_amount") * 0.15).alias("net_revenue"),
            count("*").alias("booking_count"),
            spark_sum("duration_nights").alias("total_nights")
        )
        .withColumn("gbv", spark_round(col("gbv"), 2))
        .withColumn("net_revenue", spark_round(col("net_revenue"), 2))
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## gold_occupancy_monthly
# MAGIC
# MAGIC Occupancy rate, ADR, and ALOS by property/destination/month.
# MAGIC Source: Analytics Handbook §2.1 (Occupancy Rate), §1.3 (ADR), §2.3 (ALOS)

# COMMAND ----------

@dp.materialized_view(
    name="gold_occupancy_monthly",
    comment="Monthly occupancy rate, ADR, and ALOS by property and destination. Grain: month x property_id x destination_id."
)
def gold_occupancy_monthly():
    bookings = spark.read.table("silver_bookings")
    props = spark.read.table("silver_properties")
    dests = spark.read.table("silver_destinations")

    # Confirmed + completed bookings for occupancy/ADR/ALOS
    active = (
        bookings
        .filter(col("status").isin("confirmed", "completed"))
        .select(
            trunc(col("check_in"), "month").alias("month"),
            col("property_id"),
            col("duration_nights"),
            col("total_amount")
        )
    )

    with_dims = (
        active
        .join(props.select("property_id", "destination_id", "property_type"), "property_id", "left")
        .join(dests.select("destination_id", "destination_name", "country", "continent"), "destination_id", "left")
    )

    agg = (
        with_dims
        .groupBy(
            "month", "property_id", "destination_id",
            "destination_name", "country", "continent", "property_type"
        )
        .agg(
            spark_sum("duration_nights").alias("booked_nights"),
            (spark_sum("total_amount") / spark_sum("duration_nights")).alias("adr"),
            avg("duration_nights").alias("alos"),
            count("*").alias("booking_count")
        )
    )

    # Occupancy rate = booked_nights / available_nights_in_month
    # Available nights = days in the month (approximated as 30 per Analytics Handbook)
    return (
        agg
        .withColumn(
            "occupancy_rate",
            spark_round(col("booked_nights") / lit(30.0), 4)
        )
        .withColumn("adr", spark_round(col("adr"), 2))
        .withColumn("alos", spark_round(col("alos"), 2))
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## gold_guest_satisfaction
# MAGIC
# MAGIC Recency-weighted GSS per property.
# MAGIC Formula (Analytics Handbook §3.1):
# MAGIC - 30d weight = 3.0, 90d weight = 2.0, 365d weight = 1.0, >365d weight = 0.5
# MAGIC - WHERE is_deleted = false (already filtered in silver)

# COMMAND ----------

@dp.materialized_view(
    name="gold_guest_satisfaction",
    comment="Recency-weighted Guest Satisfaction Score (GSS) per property. Weights: 30d=3.0, 90d=2.0, 365d=1.0, >365d=0.5. Range 1.0-5.0."
)
def gold_guest_satisfaction():
    reviews = spark.read.table("silver_reviews")
    props = spark.read.table("silver_properties")
    dests = spark.read.table("silver_destinations")
    hosts = spark.read.table("silver_hosts")

    reviews_weighted = (
        reviews
        .withColumn(
            "days_ago",
            datediff(current_date(), col("created_at").cast("date"))
        )
        .withColumn(
            "recency_weight",
            when(col("days_ago") <= 30, 3.0)
            .when(col("days_ago") <= 90, 2.0)
            .when(col("days_ago") <= 365, 1.0)
            .otherwise(0.5)
        )
        .withColumn("weighted_rating", col("rating") * col("recency_weight"))
    )

    gss_agg = (
        reviews_weighted
        .groupBy("property_id")
        .agg(
            (spark_sum("weighted_rating") / spark_sum("recency_weight")).alias("gss"),
            count("*").alias("review_count"),
            (count(when(col("rating") < 3.0, True)) / count("*")).alias("negative_review_rate")
        )
    )

    with_dims = (
        gss_agg
        .join(props.select("property_id", "host_id", "destination_id", "property_type"), "property_id", "left")
        .join(dests.select("destination_id", "destination_name", "country"), "destination_id", "left")
        .join(hosts.select("host_id", "host_name"), "host_id", "left")
    )

    return (
        with_dims.select(
            "property_id", "host_id", "host_name",
            "destination_id", "destination_name", "country",
            "property_type",
            spark_round(col("gss"), 4).alias("gss"),
            "review_count",
            spark_round(col("negative_review_rate"), 4).alias("negative_review_rate")
        )
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## gold_host_performance
# MAGIC
# MAGIC Superhost qualification metrics per host (trailing 90 days).
# MAGIC Source: Analytics Handbook §4.1:
# MAGIC - avg_rating >= 4.5 (trailing 90 days)
# MAGIC - completed_bookings >= 10 (trailing 90 days)
# MAGIC - cancellation_rate < 2% (host-initiated)

# COMMAND ----------

@dp.materialized_view(
    name="gold_host_performance",
    comment="Host superhost qualification metrics. Trailing 90-day window. Grain: one row per host."
)
def gold_host_performance():
    bookings = spark.read.table("silver_bookings")
    reviews = spark.read.table("silver_reviews")
    props = spark.read.table("silver_properties")
    hosts = spark.read.table("silver_hosts")
    booking_updates = spark.read.table("silver_booking_updates")

    cutoff_90d = datediff(current_date(), lit(90))

    # Bookings in trailing 90 days per property
    recent_bookings = (
        bookings
        .filter(
            (col("created_at").cast("date") >= cutoff_90d) &
            col("status").isin("confirmed", "completed", "cancelled")
        )
        .join(props.select("property_id", "host_id"), "property_id", "left")
    )

    booking_stats = (
        recent_bookings
        .groupBy("host_id")
        .agg(
            count(when(col("status") == "completed", True)).alias("completed_bookings_90d"),
            count("*").alias("total_bookings_90d")
        )
    )

    # Host-initiated cancellations (status = 'cancelled_by_host' in updates)
    host_cancellations = (
        booking_updates
        .filter(col("status") == "cancelled_by_host")
        .join(props.select("property_id", "host_id"), "property_id", "left")
        .groupBy("host_id")
        .agg(count("*").alias("host_cancelled_count"))
    )

    # Reviews in trailing 90 days per host via property
    recent_reviews = (
        reviews
        .filter(
            datediff(current_date(), col("created_at").cast("date")) <= 90
        )
        .join(props.select("property_id", "host_id"), "property_id", "left")
    )

    review_stats = (
        recent_reviews
        .groupBy("host_id")
        .agg(
            avg("rating").alias("avg_rating_90d"),
            count("*").alias("review_count_90d")
        )
    )

    result = (
        hosts
        .join(booking_stats, "host_id", "left")
        .join(host_cancellations, "host_id", "left")
        .join(review_stats, "host_id", "left")
        .withColumn("completed_bookings_90d", coalesce(col("completed_bookings_90d"), lit(0)))
        .withColumn("total_bookings_90d", coalesce(col("total_bookings_90d"), lit(0)))
        .withColumn("host_cancelled_count", coalesce(col("host_cancelled_count"), lit(0)))
        .withColumn(
            "cancellation_rate",
            when(col("total_bookings_90d") > 0,
                col("host_cancelled_count") / col("total_bookings_90d"))
            .otherwise(lit(0.0))
        )
        .withColumn("avg_rating_90d", coalesce(col("avg_rating_90d"), lit(0.0)))
        .withColumn(
            "qualifies_superhost",
            (col("avg_rating_90d") >= 4.5) &
            (col("completed_bookings_90d") >= 10) &
            (col("cancellation_rate") < 0.02)
        )
    )

    return result.select(
        "host_id", "host_name", "country", "is_verified", "is_active",
        spark_round(col("avg_rating_90d"), 4).alias("avg_rating_90d"),
        "completed_bookings_90d", "total_bookings_90d",
        spark_round(col("cancellation_rate"), 4).alias("cancellation_rate"),
        "review_count_90d",
        "qualifies_superhost"
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## gold_property_summary
# MAGIC
# MAGIC Denormalized property view combining revenue, reviews, amenity count, and image availability.
# MAGIC Useful as a single-row-per-property hub for downstream analytics.

# COMMAND ----------

@dp.materialized_view(
    name="gold_property_summary",
    comment="Denormalized property summary with total GBV, booking count, avg rating, and amenity/image counts. Grain: one row per property."
)
def gold_property_summary():
    props = spark.read.table("silver_properties")
    dests = spark.read.table("silver_destinations")
    hosts = spark.read.table("silver_hosts")
    bookings = spark.read.table("silver_bookings")
    reviews = spark.read.table("silver_reviews")
    amenities_jn = spark.read.table("silver_property_amenities")
    images = spark.read.table("silver_property_images")

    # Booking aggregates
    booking_agg = (
        bookings
        .filter(col("status") == "confirmed")
        .groupBy("property_id")
        .agg(
            spark_sum("total_amount").alias("total_gbv"),
            count("*").alias("total_bookings")
        )
    )

    # Review aggregates
    review_agg = (
        reviews
        .groupBy("property_id")
        .agg(
            avg("rating").alias("avg_rating"),
            count("*").alias("review_count")
        )
    )

    # Amenity counts
    amenity_counts = (
        amenities_jn
        .groupBy("property_id")
        .agg(count("*").alias("amenity_count"))
    )

    # Image counts
    image_counts = (
        images
        .groupBy("property_id")
        .agg(
            count("*").alias("image_count"),
            spark_max(when(col("is_primary"), col("image_url"))).alias("primary_image_url")
        )
    )

    return (
        props
        .join(dests.select("destination_id", "destination_name", "country", "continent"), "destination_id", "left")
        .join(hosts.select("host_id", "host_name", "is_verified"), "host_id", "left")
        .join(booking_agg, "property_id", "left")
        .join(review_agg, "property_id", "left")
        .join(amenity_counts, "property_id", "left")
        .join(image_counts, "property_id", "left")
        .select(
            "property_id", "host_id", "host_name", "is_verified",
            "destination_id", "destination_name", "country", "continent",
            "title", "property_type",
            spark_round(col("base_price"), 2).alias("base_price"),
            "bedrooms", "bathrooms", "max_guests",
            "latitude", "longitude",
            spark_round(coalesce(col("total_gbv"), lit(0.0)), 2).alias("total_gbv"),
            coalesce(col("total_bookings"), lit(0)).alias("total_bookings"),
            spark_round(coalesce(col("avg_rating"), lit(0.0)), 4).alias("avg_rating"),
            coalesce(col("review_count"), lit(0)).alias("review_count"),
            coalesce(col("amenity_count"), lit(0)).alias("amenity_count"),
            coalesce(col("image_count"), lit(0)).alias("image_count"),
            col("primary_image_url"),
            "created_at"
        )
    )
