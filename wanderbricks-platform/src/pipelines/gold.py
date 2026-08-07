"""WanderBricks Platform — Gold layer.

Business-ready aggregates. All formulas follow the WanderBricks Analytics
Handbook exactly (section references noted per table):
  * gold_revenue_daily      — GBV / Net Revenue, Handbook 1.1-1.2
  * gold_occupancy_monthly  — Occupancy Rate / ADR / ALOS, Handbook 2.1 / 1.3 / 2.3
  * gold_guest_satisfaction — recency-weighted GSS, Handbook 3.1 (+ 3.3 negative rate)
  * gold_host_performance   — superhost qualification metrics, Handbook 4.1
  * gold_property_summary   — denormalized rollup of the above, per property

Note on gold_host_performance: the Superhost "response rate >= 90%" criterion
(Handbook 4.1, item 4) requires the booking_updates table, which is outside
WS-A's bronze scope (see PROJECT_MEMORY.md bronze table list). It is omitted
here and should be added once booking_updates lands in bronze. Similarly,
Handbook 4.3 distinguishes host- vs guest-initiated cancellations via
booking_updates; the cancellation_rate_90d computed here is an overall
booking-level cancellation rate (proxy), not host-attributed.
"""

from pyspark import pipelines as dp
from pyspark.sql import functions as F


@dp.materialized_view(
    name="gold_revenue_daily",
    comment="Gold: daily GBV, net revenue, and host payout by property/destination (Handbook 1.1-1.2). Time dimension is booking created_at, not check-in.",
)
def gold_revenue_daily():
    bookings = spark.read.table("silver_bookings").filter(F.col("status") == "confirmed")
    properties = spark.read.table("silver_properties").select(
        "property_id", "destination_id", "destination_name"
    )
    return (
        bookings.join(properties, "property_id", "left")
        .withColumn("booking_date", F.to_date("created_at"))
        .groupBy("booking_date", "property_id", "destination_id", "destination_name")
        .agg(
            F.sum("total_amount").alias("gbv"),
            (F.sum("total_amount") * F.lit(0.15)).alias("net_revenue"),
            (F.sum("total_amount") * F.lit(0.85)).alias("host_payout"),
            F.count("booking_id").alias("booking_count"),
        )
    )


@dp.materialized_view(
    name="gold_occupancy_monthly",
    comment="Gold: monthly occupancy rate, ADR, and ALOS by property/destination (Handbook 2.1, 1.3, 2.3).",
)
@dp.expect("occupancy_rate_non_negative", "occupancy_rate IS NULL OR occupancy_rate >= 0")
def gold_occupancy_monthly():
    properties = spark.read.table("silver_properties").select(
        "property_id", "destination_id", "destination_name", "created_at"
    )
    stays = spark.read.table("silver_bookings").filter(
        F.col("status").isin("confirmed", "completed")
    ).withColumn("month", F.date_trunc("month", F.col("check_in")))

    booked = stays.groupBy("property_id", "month").agg(
        F.sum("duration_nights").alias("booked_nights"),
        F.sum("total_amount").alias("stay_revenue"),
        F.avg("duration_nights").alias("alos"),
        F.count("booking_id").alias("stay_count"),
    )

    calendar_months = booked.select("month").distinct()

    availability = (
        properties.crossJoin(calendar_months)
        .filter(F.col("created_at") <= F.last_day(F.col("month")))
        .withColumn("days_in_month", F.dayofmonth(F.last_day(F.col("month"))))
        .select("property_id", "destination_id", "destination_name", "month", "days_in_month")
    )

    return (
        availability.join(booked, ["property_id", "month"], "left")
        .withColumn("booked_nights", F.coalesce(F.col("booked_nights"), F.lit(0)))
        .withColumn(
            "occupancy_rate", F.col("booked_nights") / F.col("days_in_month")
        )
        .withColumn(
            "adr",
            F.when(F.col("booked_nights") > 0, F.col("stay_revenue") / F.col("booked_nights")),
        )
        .select(
            "property_id",
            "destination_id",
            "destination_name",
            F.col("month").alias("occupancy_month"),
            "booked_nights",
            "days_in_month",
            "occupancy_rate",
            "adr",
            "alos",
            "stay_count",
        )
    )


@dp.materialized_view(
    name="gold_guest_satisfaction",
    comment="Gold: recency-weighted Guest Satisfaction Score (GSS) per property (Handbook 3.1) plus negative review rate (Handbook 3.3).",
)
@dp.expect("gss_in_range", "gss >= 1.0 AND gss <= 5.0")
def gold_guest_satisfaction():
    reviews = spark.read.table("silver_reviews").filter(F.col("is_deleted") == False)
    age_days = F.datediff(F.current_timestamp(), F.col("created_at"))
    recency_weight = (
        F.when(age_days <= 30, F.lit(3.0))
        .when(age_days <= 90, F.lit(2.0))
        .when(age_days <= 365, F.lit(1.0))
        .otherwise(F.lit(0.5))
    )
    weighted = reviews.withColumn("recency_weight", recency_weight)
    return weighted.groupBy("property_id").agg(
        (F.sum(F.col("rating") * F.col("recency_weight")) / F.sum("recency_weight")).alias("gss"),
        F.count("review_id").alias("review_count"),
        (
            F.sum(F.when(F.col("rating") < 3.0, 1).otherwise(0))
            / F.count("review_id")
        ).alias("negative_review_rate"),
    )


@dp.materialized_view(
    name="gold_host_performance",
    comment="Gold: trailing-90-day superhost qualification signals per host (Handbook 4.1). See module docstring for scope caveats (no response-rate / host-attributed-cancellation signal without booking_updates).",
)
def gold_host_performance():
    properties = spark.read.table("silver_properties").select("property_id", "host_id")
    bookings = spark.read.table("silver_bookings")
    reviews = spark.read.table("silver_reviews").filter(F.col("is_deleted") == False)
    hosts = spark.read.table("silver_hosts").select(
        "host_id", "name", "is_verified", "is_active", "rating", "country"
    )

    cutoff = F.date_sub(F.current_date(), 90)
    host_bookings_90d = bookings.join(properties, "property_id").filter(
        F.col("created_at") >= cutoff
    )

    totals = host_bookings_90d.groupBy("host_id").agg(
        F.count("booking_id").alias("total_bookings_90d")
    )
    completed = (
        host_bookings_90d.filter(F.col("status") == "completed")
        .groupBy("host_id")
        .agg(F.count("booking_id").alias("completed_bookings_90d"))
    )
    cancelled = (
        host_bookings_90d.filter(F.col("status") == "cancelled")
        .groupBy("host_id")
        .agg(F.count("booking_id").alias("cancelled_bookings_90d"))
    )
    host_reviews_90d = (
        reviews.join(properties, "property_id")
        .filter(F.col("created_at") >= cutoff)
        .groupBy("host_id")
        .agg(F.avg("rating").alias("avg_rating_90d"))
    )

    return (
        hosts.join(totals, "host_id", "left")
        .join(completed, "host_id", "left")
        .join(cancelled, "host_id", "left")
        .join(host_reviews_90d, "host_id", "left")
        .withColumn("total_bookings_90d", F.coalesce(F.col("total_bookings_90d"), F.lit(0)))
        .withColumn(
            "completed_bookings_90d", F.coalesce(F.col("completed_bookings_90d"), F.lit(0))
        )
        .withColumn(
            "cancelled_bookings_90d", F.coalesce(F.col("cancelled_bookings_90d"), F.lit(0))
        )
        .withColumn(
            "cancellation_rate_90d",
            F.when(
                F.col("total_bookings_90d") > 0,
                F.col("cancelled_bookings_90d") / F.col("total_bookings_90d"),
            ).otherwise(F.lit(0.0)),
        )
        .withColumn(
            "qualifies_superhost",
            (F.col("avg_rating_90d") >= 4.5)
            & (F.col("completed_bookings_90d") >= 10)
            & (F.col("cancellation_rate_90d") < 0.02),
        )
    )


@dp.materialized_view(
    name="gold_property_summary",
    comment="Gold: denormalized per-property rollup of revenue, occupancy, and satisfaction metrics for downstream metric views / features.",
)
def gold_property_summary():
    properties = spark.read.table("silver_properties")
    hosts = spark.read.table("silver_hosts").select(
        "host_id",
        F.col("name").alias("host_name"),
        F.col("is_verified").alias("host_is_verified"),
    )
    revenue = spark.read.table("gold_revenue_daily").groupBy("property_id").agg(
        F.sum("gbv").alias("lifetime_gbv"),
        F.sum("net_revenue").alias("lifetime_net_revenue"),
        F.sum("booking_count").alias("lifetime_booking_count"),
    )
    occupancy = spark.read.table("gold_occupancy_monthly").groupBy("property_id").agg(
        F.avg("occupancy_rate").alias("avg_occupancy_rate"), F.avg("adr").alias("avg_adr")
    )
    satisfaction = spark.read.table("gold_guest_satisfaction").select(
        "property_id", "gss", "review_count", "negative_review_rate"
    )

    return (
        properties.join(hosts, "host_id", "left")
        .join(revenue, "property_id", "left")
        .join(occupancy, "property_id", "left")
        .join(satisfaction, "property_id", "left")
        .select(
            "property_id",
            "title",
            "property_type",
            "destination_id",
            "destination_name",
            "destination_country",
            "base_price",
            "max_guests",
            "bedrooms",
            "bathrooms",
            "host_id",
            "host_name",
            "host_is_verified",
            F.coalesce(F.col("lifetime_gbv"), F.lit(0.0)).alias("lifetime_gbv"),
            F.coalesce(F.col("lifetime_net_revenue"), F.lit(0.0)).alias("lifetime_net_revenue"),
            F.coalesce(F.col("lifetime_booking_count"), F.lit(0)).alias(
                "lifetime_booking_count"
            ),
            "avg_occupancy_rate",
            "avg_adr",
            "gss",
            F.coalesce(F.col("review_count"), F.lit(0)).alias("review_count"),
            "negative_review_rate",
        )
    )
