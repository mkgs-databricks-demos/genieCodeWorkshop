"""WanderBricks Platform — Silver layer.

Materialized views that clean, dedupe, type, and conform the bronze tables:
  * silver_properties  — destination name/country joined in
  * silver_bookings    — duration_nights computed, status standardized
  * silver_reviews     — booking context joined in
  * silver_users, silver_hosts, silver_payments — typed + deduped
"""

from pyspark import pipelines as dp
from pyspark.sql import functions as F
from pyspark.sql.window import Window


def _dedup(df, pk_cols: list[str], order_col: str):
    """Keep exactly one row per natural key, preferring the most recent record."""
    w = Window.partitionBy(*pk_cols).orderBy(F.col(order_col).desc())
    return (
        df.withColumn("_rn", F.row_number().over(w))
        .filter(F.col("_rn") == 1)
        .drop("_rn")
    )


@dp.materialized_view(
    name="silver_properties",
    comment="Silver: deduped properties with destination name/country joined in and null business fields defaulted.",
)
@dp.expect_all_or_drop(
    {
        "property_id_not_null": "property_id IS NOT NULL",
        "destination_id_not_null": "destination_id IS NOT NULL",
        "base_price_non_negative": "base_price >= 0",
    }
)
def silver_properties():
    props = _dedup(spark.read.table("bronze_properties"), ["property_id"], "_ingested_at")
    dests = spark.read.table("bronze_destinations").select(
        "destination_id",
        F.col("destination").alias("destination_name"),
        F.col("country").alias("destination_country"),
        "state_or_province",
    )
    return (
        props.join(dests, "destination_id", "left")
        .withColumn("max_guests", F.coalesce(F.col("max_guests"), F.lit(1)))
        .withColumn("bedrooms", F.coalesce(F.col("bedrooms"), F.lit(0)))
        .withColumn("bathrooms", F.coalesce(F.col("bathrooms"), F.lit(0)))
        .withColumn("property_type", F.trim(F.col("property_type")))
        .withColumn("base_price", F.col("base_price").cast("double"))
        .select(
            "property_id",
            "host_id",
            "destination_id",
            "destination_name",
            "destination_country",
            "state_or_province",
            "title",
            "description",
            "base_price",
            "property_type",
            "max_guests",
            "bedrooms",
            "bathrooms",
            "property_latitude",
            "property_longitude",
            "created_at",
        )
    )


@dp.materialized_view(
    name="silver_bookings",
    comment="Silver: deduped bookings with computed duration_nights and standardized status.",
)
@dp.expect_all_or_drop(
    {
        "booking_id_not_null": "booking_id IS NOT NULL",
        "property_id_not_null": "property_id IS NOT NULL",
        "user_id_not_null": "user_id IS NOT NULL",
        "valid_date_range": "check_out > check_in",
    }
)
@dp.expect("non_negative_amount", "total_amount >= 0")
def silver_bookings():
    df = _dedup(spark.read.table("bronze_bookings"), ["booking_id"], "updated_at")
    return (
        df.withColumn("status", F.lower(F.trim(F.col("status"))))
        .withColumn("duration_nights", F.datediff(F.col("check_out"), F.col("check_in")))
        .withColumn("total_amount", F.col("total_amount").cast("double"))
        .select(
            "booking_id",
            "user_id",
            "property_id",
            "check_in",
            "check_out",
            "duration_nights",
            "guests_count",
            "total_amount",
            "status",
            "created_at",
            "updated_at",
        )
    )


@dp.materialized_view(
    name="silver_reviews",
    comment="Silver: deduped reviews joined with their booking's stay dates for context.",
)
@dp.expect_all_or_drop(
    {
        "review_id_not_null": "review_id IS NOT NULL",
        "property_id_not_null": "property_id IS NOT NULL",
        "rating_range": "rating >= 1.0 AND rating <= 5.0",
    }
)
def silver_reviews():
    r = _dedup(spark.read.table("bronze_reviews"), ["review_id"], "updated_at")
    b = spark.read.table("bronze_bookings").select(
        "booking_id",
        F.col("check_in").alias("booking_check_in"),
        F.col("check_out").alias("booking_check_out"),
    )
    return r.join(b, "booking_id", "left").select(
        "review_id",
        "booking_id",
        "property_id",
        "user_id",
        "rating",
        "comment",
        "is_deleted",
        "booking_check_in",
        "booking_check_out",
        "created_at",
        "updated_at",
    )


@dp.materialized_view(name="silver_users", comment="Silver: deduped, typed user profiles.")
@dp.expect_or_drop("user_id_not_null", "user_id IS NOT NULL")
def silver_users():
    df = _dedup(spark.read.table("bronze_users"), ["user_id"], "_ingested_at")
    return df.withColumn("user_type", F.lower(F.trim(F.col("user_type"))))


@dp.materialized_view(name="silver_hosts", comment="Silver: deduped, typed host profiles.")
@dp.expect_all_or_drop(
    {
        "host_id_not_null": "host_id IS NOT NULL",
        "rating_range": "rating IS NULL OR (rating >= 1.0 AND rating <= 5.0)",
    }
)
def silver_hosts():
    return _dedup(spark.read.table("bronze_hosts"), ["host_id"], "_ingested_at")


@dp.materialized_view(name="silver_payments", comment="Silver: deduped, typed payment records.")
@dp.expect_all_or_drop(
    {
        "payment_id_not_null": "payment_id IS NOT NULL",
        "booking_id_not_null": "booking_id IS NOT NULL",
    }
)
@dp.expect("non_negative_amount", "amount >= 0")
def silver_payments():
    df = _dedup(spark.read.table("bronze_payments"), ["payment_id"], "_ingested_at")
    return df.withColumn("payment_method", F.lower(F.trim(F.col("payment_method")))).withColumn(
        "status", F.lower(F.trim(F.col("status")))
    )
