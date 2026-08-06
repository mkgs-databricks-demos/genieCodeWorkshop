# Databricks notebook source
# MAGIC %md
# MAGIC # Property Quality Feature Table
# MAGIC 
# MAGIC Computes property-level quality features including GSS (recency-weighted),
# MAGIC occupancy, revenue metrics, and composite quality score.
# MAGIC Uses the Databricks Feature Engineering client for proper feature table registration.

# COMMAND ----------

# MAGIC %pip install --upgrade databricks-sdk databricks-feature-engineering
# MAGIC %restart_python

# COMMAND ----------

from datetime import datetime, timedelta
from pyspark.sql import functions as F
from pyspark.sql.window import Window
from databricks.feature_engineering import FeatureEngineeringClient

# COMMAND ----------

# Configuration
CATALOG = "hls_fde_dev"
SCHEMA = "dev_matthew_giglia_wanderbricks_ai"
FEATURE_TABLE_NAME = f"{CATALOG}.{SCHEMA}.feature_property_quality"

# Reference date: use the max date in the data for trailing window calculations
REFERENCE_DATE = "2025-07-30"
TRAILING_DAYS = 90
WINDOW_START = (datetime(2025, 7, 30) - timedelta(days=TRAILING_DAYS)).strftime("%Y-%m-%d")

print(f"Reference date: {REFERENCE_DATE}")
print(f"90-day window start: {WINDOW_START}")
print(f"Feature table: {FEATURE_TABLE_NAME}")

# COMMAND ----------

# Load silver tables
bookings = spark.table(f"{CATALOG}.{SCHEMA}.silver_bookings")
reviews = spark.table(f"{CATALOG}.{SCHEMA}.silver_reviews")
properties = spark.table(f"{CATALOG}.{SCHEMA}.silver_properties")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Compute Property Features

# COMMAND ----------

# 1. Average rating (trailing 90 days)
property_ratings_90d = reviews.filter(
    F.col("created_at") >= F.lit(WINDOW_START)
).groupBy("property_id").agg(
    F.avg("rating").alias("avg_rating"),
    F.count("review_id").alias("review_count")
)

# COMMAND ----------

# 2. Guest Satisfaction Score (GSS) - recency-weighted per Analytics Handbook S3.1
# Weights: 30d=3.0, 90d=2.0, 365d=1.0, >365d=0.5
ref_date = F.lit(REFERENCE_DATE).cast("date")

reviews_weighted = reviews.withColumn(
    "days_since_review",
    F.datediff(ref_date, F.col("created_at").cast("date"))
).withColumn(
    "recency_weight",
    F.when(F.col("days_since_review") <= 30, 3.0)
     .when(F.col("days_since_review") <= 90, 2.0)
     .when(F.col("days_since_review") <= 365, 1.0)
     .otherwise(0.5)
)

property_gss = reviews_weighted.groupBy("property_id").agg(
    (F.sum(F.col("rating") * F.col("recency_weight")) / F.sum("recency_weight")).alias("gss")
)

# COMMAND ----------

# 3. Occupancy rate (trailing 90 days)
# booked_nights / available_nights
property_bookings_90d = bookings.filter(
    (F.col("created_at") >= F.lit(WINDOW_START)) &
    (F.col("status").isin("confirmed", "completed"))
)

property_occupancy = property_bookings_90d.groupBy("property_id").agg(
    F.sum("duration_nights").alias("booked_nights")
).withColumn(
    "occupancy_rate",
    F.least(F.col("booked_nights").cast("double") / F.lit(TRAILING_DAYS), F.lit(1.0))
).select("property_id", "occupancy_rate")

# COMMAND ----------

# 4. Average daily rate (ADR) - trailing 90 days
property_adr = property_bookings_90d.filter(
    F.col("duration_nights") > 0
).groupBy("property_id").agg(
    (F.sum("total_amount") / F.sum("duration_nights")).alias("avg_daily_rate")
)

# COMMAND ----------

# 5. Repeat guest rate
# Guests who booked this property more than once / total unique guests
property_guests = bookings.filter(
    F.col("status").isin("confirmed", "completed")
).groupBy("property_id", "user_id").agg(
    F.count("booking_id").alias("booking_count")
)

repeat_guests = property_guests.groupBy("property_id").agg(
    F.count(F.when(F.col("booking_count") > 1, 1)).alias("repeat_guests"),
    F.count("user_id").alias("total_unique_guests")
).withColumn(
    "repeat_guest_rate",
    F.when(F.col("total_unique_guests") > 0,
           F.col("repeat_guests").cast("double") / F.col("total_unique_guests")
    ).otherwise(0.0)
).select("property_id", "repeat_guest_rate")

# COMMAND ----------

# 6. Negative review rate (reviews with rating < 3.0)
property_negative = reviews.groupBy("property_id").agg(
    F.count(F.when(F.col("rating") < 3.0, 1)).alias("negative_reviews"),
    F.count("review_id").alias("total_reviews_all")
).withColumn(
    "negative_review_rate",
    F.when(F.col("total_reviews_all") > 0,
           F.col("negative_reviews").cast("double") / F.col("total_reviews_all")
    ).otherwise(0.0)
).select("property_id", "negative_review_rate")

# COMMAND ----------

# 7. Booking lead time average (days between booking creation and check-in)
property_lead_time = bookings.filter(
    F.col("status").isin("confirmed", "completed")
).withColumn(
    "lead_time_days",
    F.datediff(F.col("check_in"), F.col("created_at").cast("date"))
).filter(
    F.col("lead_time_days") >= 0
).groupBy("property_id").agg(
    F.avg("lead_time_days").alias("booking_lead_time_avg")
)

# COMMAND ----------

# 8. Revenue Per Available Night (RevPAN)
# Net Revenue (15% commission) / available nights in period
property_revpan = bookings.filter(
    (F.col("created_at") >= F.lit(WINDOW_START)) &
    (F.col("status").isin("confirmed", "completed"))
).groupBy("property_id").agg(
    (F.sum("total_amount") * 0.15 / F.lit(TRAILING_DAYS)).alias("revenue_per_available_night")
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Assemble Feature DataFrame

# COMMAND ----------

# Start with all properties
property_features = properties.select("property_id") \
    .join(property_ratings_90d, on="property_id", how="left") \
    .join(property_gss, on="property_id", how="left") \
    .join(property_occupancy, on="property_id", how="left") \
    .join(property_adr, on="property_id", how="left") \
    .join(repeat_guests, on="property_id", how="left") \
    .join(property_negative, on="property_id", how="left") \
    .join(property_lead_time, on="property_id", how="left") \
    .join(property_revpan, on="property_id", how="left")

# Fill nulls with defaults
property_features = property_features.fillna({
    "avg_rating": 0.0,
    "review_count": 0,
    "gss": 0.0,
    "occupancy_rate": 0.0,
    "avg_daily_rate": 0.0,
    "repeat_guest_rate": 0.0,
    "negative_review_rate": 0.0,
    "booking_lead_time_avg": 0.0,
    "revenue_per_available_night": 0.0
})

# COMMAND ----------

# 9. Property quality score (composite 0-1)
# Normalize each metric: higher is better (except negative_review_rate)
property_features = property_features.withColumn(
    "rating_norm", F.col("avg_rating") / 5.0
).withColumn(
    "gss_norm", F.col("gss") / 5.0
).withColumn(
    "occupancy_norm", F.col("occupancy_rate")  # already 0-1
).withColumn(
    "repeat_norm", F.col("repeat_guest_rate")  # already 0-1
).withColumn(
    "negative_norm", F.lit(1.0) - F.col("negative_review_rate")  # invert: lower negative is better
).withColumn(
    "property_quality_score",
    (F.col("rating_norm") + F.col("gss_norm") + F.col("occupancy_norm") +
     F.col("repeat_norm") + F.col("negative_norm")) / 5.0
).drop("rating_norm", "gss_norm", "occupancy_norm", "repeat_norm", "negative_norm")

# COMMAND ----------

# Add timestamp key for point-in-time correctness
property_features = property_features.withColumn(
    "computed_at", F.lit(REFERENCE_DATE).cast("timestamp")
)

# Cast to correct types and select final columns
property_features = property_features.select(
    F.col("property_id").cast("long"),
    F.col("computed_at"),
    F.col("avg_rating").cast("double"),
    F.col("review_count").cast("int"),
    F.col("gss").cast("double"),
    F.col("occupancy_rate").cast("double"),
    F.col("avg_daily_rate").cast("double"),
    F.col("repeat_guest_rate").cast("double"),
    F.col("negative_review_rate").cast("double"),
    F.col("property_quality_score").cast("double"),
    F.col("booking_lead_time_avg").cast("double"),
    F.col("revenue_per_available_night").cast("double")
)

print(f"Property features count: {property_features.count()}")
property_features.show(5, truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Write Feature Table

# COMMAND ----------

fe = FeatureEngineeringClient()

# Drop existing table if it exists (for idempotent reruns)
try:
    spark.sql(f"DROP TABLE IF EXISTS {FEATURE_TABLE_NAME}")
except Exception as e:
    print(f"Note: {e}")

# Create feature table with point-in-time support
fe.create_table(
    name=FEATURE_TABLE_NAME,
    primary_keys=["property_id", "computed_at"],
    timeseries_columns="computed_at",
    df=property_features,
    description="Property quality features including recency-weighted GSS, occupancy, "
                "revenue metrics, and composite quality score. Per Analytics Handbook S3.1."
)

print(f"Feature table created: {FEATURE_TABLE_NAME}")
print(f"Rows written: {spark.table(FEATURE_TABLE_NAME).count()}")
