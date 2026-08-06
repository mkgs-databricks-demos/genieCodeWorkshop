# Databricks notebook source
# MAGIC %md
# MAGIC # Host Performance Feature Table
# MAGIC 
# MAGIC Computes host-level features for superhost qualification and scoring.
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
FEATURE_TABLE_NAME = f"{CATALOG}.{SCHEMA}.feature_host_performance"

# Reference date: use the max date in the data for trailing window calculations
# The source data ends at 2025-07-30
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
booking_updates = spark.table(f"{CATALOG}.{SCHEMA}.silver_booking_updates")
hosts = spark.table(f"{CATALOG}.{SCHEMA}.silver_hosts")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Compute Host Features

# COMMAND ----------

# Get host_id for each booking via properties
bookings_with_host = bookings.join(
    properties.select("property_id", "host_id"),
    on="property_id",
    how="inner"
)

# Filter to trailing 90 days for time-windowed metrics
bookings_90d = bookings_with_host.filter(
    F.col("created_at") >= F.lit(WINDOW_START)
)

# COMMAND ----------

# 1. Average rating (trailing 90 days)
# Join reviews to properties to get host_id
reviews_with_host = reviews.join(
    properties.select("property_id", "host_id"),
    on="property_id",
    how="inner"
).filter(
    F.col("created_at") >= F.lit(WINDOW_START)
)

host_ratings = reviews_with_host.groupBy("host_id").agg(
    F.avg("rating").alias("avg_rating"),
    F.count("review_id").alias("review_count_90d")
)

# COMMAND ----------

# 2. Total completed bookings (trailing 90 days)
host_completed = bookings_90d.filter(
    F.col("status") == "completed"
).groupBy("host_id").agg(
    F.count("booking_id").alias("total_completed_bookings")
)

# COMMAND ----------

# 3. Cancellation rate
# Per Analytics Handbook S4.3: cancelled / (confirmed + completed + cancelled)
host_cancellations = bookings_90d.filter(
    F.col("status").isin("confirmed", "completed", "cancelled")
).groupBy("host_id").agg(
    F.count(F.when(F.col("status") == "cancelled", 1)).alias("cancellation_count"),
    F.count("booking_id").alias("eligible_bookings")
).withColumn(
    "cancellation_rate",
    F.when(F.col("eligible_bookings") > 0,
           F.col("cancellation_count") / F.col("eligible_bookings")
    ).otherwise(0.0)
).select("host_id", "cancellation_rate")

# COMMAND ----------

# 4. Response rate
# Approximate: bookings that transitioned from 'pending' to 'confirmed' within 24 hours
# Using booking_updates to find the first status change timing
booking_response = booking_updates.join(
    properties.select("property_id", "host_id"),
    on="property_id",
    how="inner"
).filter(
    F.col("created_at") >= F.lit(WINDOW_START)
)

# Find first confirmation per booking (approximates host response)
first_confirm = booking_response.filter(
    F.col("status") == "confirmed"
).groupBy("host_id", "booking_id").agg(
    F.min("created_at").alias("confirmed_at")
)

# Join back to get original booking creation time
response_times = first_confirm.join(
    bookings_with_host.select("booking_id", "host_id", "created_at").alias("b"),
    on=["booking_id", "host_id"],
    how="inner"
).withColumn(
    "response_hours",
    (F.unix_timestamp("confirmed_at") - F.unix_timestamp(F.col("created_at"))) / 3600.0
)

# Total booking requests per host in window
total_requests = bookings_90d.groupBy("host_id").agg(
    F.count("booking_id").alias("total_requests")
)

# Responded within 24h
responded_24h = response_times.filter(
    (F.col("response_hours") >= 0) & (F.col("response_hours") <= 24)
).groupBy("host_id").agg(
    F.count("booking_id").alias("responded_within_24h")
)

host_response_rate = total_requests.join(
    responded_24h, on="host_id", how="left"
).withColumn(
    "responded_within_24h", F.coalesce(F.col("responded_within_24h"), F.lit(0))
).withColumn(
    "response_rate",
    F.when(F.col("total_requests") > 0,
           F.col("responded_within_24h") / F.col("total_requests")
    ).otherwise(0.0)
).select("host_id", "response_rate")

# COMMAND ----------

# 5. Total revenue (lifetime GBV - confirmed bookings)
host_revenue = bookings_with_host.filter(
    F.col("status").isin("confirmed", "completed")
).groupBy("host_id").agg(
    F.sum("total_amount").alias("total_revenue")
)

# COMMAND ----------

# 6. Average occupancy rate across all host properties
# Occupancy = booked nights / available nights per property in the 90d window
property_occupancy = bookings_90d.filter(
    F.col("status").isin("confirmed", "completed")
).groupBy("host_id", "property_id").agg(
    F.sum("duration_nights").alias("booked_nights")
).withColumn(
    "available_nights", F.lit(TRAILING_DAYS)
).withColumn(
    "occupancy_rate",
    F.least(F.col("booked_nights") / F.col("available_nights"), F.lit(1.0))
)

host_occupancy = property_occupancy.groupBy("host_id").agg(
    F.avg("occupancy_rate").alias("avg_occupancy_rate")
)

# COMMAND ----------

# 7. Property count (active listings)
host_property_count = properties.groupBy("host_id").agg(
    F.countDistinct("property_id").alias("property_count")
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Assemble Feature DataFrame

# COMMAND ----------

# Start with ALL hosts (not just those with properties)
host_features = hosts.select("host_id") \
    .join(host_property_count, on="host_id", how="left") \
    .join(host_completed, on="host_id", how="left") \
    .join(host_cancellations, on="host_id", how="left") \
    .join(host_response_rate, on="host_id", how="left") \
    .join(host_revenue, on="host_id", how="left") \
    .join(host_occupancy, on="host_id", how="left")

# Fill nulls with defaults
host_features = host_features.fillna({
    "avg_rating": 0.0,
    "total_completed_bookings": 0,
    "cancellation_rate": 0.0,
    "response_rate": 0.0,
    "total_revenue": 0.0,
    "avg_occupancy_rate": 0.0,
    "property_count": 0
})

# COMMAND ----------

# 8. Superhost qualification (Analytics Handbook S4.1)
# ALL four criteria must be met:
#   1. Average rating >= 4.5 (trailing 90 days)
#   2. Completed bookings >= 10 (trailing 90 days)
#   3. Cancellation rate < 2% (host-initiated)
#   4. Response rate >= 90% (within 24 hours)

host_features = host_features.withColumn(
    "is_superhost",
    (F.col("avg_rating") >= 4.5) &
    (F.col("total_completed_bookings") >= 10) &
    (F.col("cancellation_rate") < 0.02) &
    (F.col("response_rate") >= 0.90)
)

# COMMAND ----------

# 9. Superhost score (composite 0-1)
# Normalize each metric to 0-1, then average
host_features = host_features.withColumn(
    "rating_score", F.least(F.col("avg_rating") / 5.0, F.lit(1.0))
).withColumn(
    "bookings_score", F.least(F.col("total_completed_bookings").cast("double") / 10.0, F.lit(1.0))
).withColumn(
    "cancel_score", F.greatest(F.lit(1.0) - (F.col("cancellation_rate") / 0.02), F.lit(0.0))
).withColumn(
    "response_score", F.least(F.col("response_rate") / 0.90, F.lit(1.0))
).withColumn(
    "superhost_score",
    (F.col("rating_score") + F.col("bookings_score") + F.col("cancel_score") + F.col("response_score")) / 4.0
).drop("rating_score", "bookings_score", "cancel_score", "response_score")

# COMMAND ----------

# Add timestamp key for point-in-time correctness
host_features = host_features.withColumn(
    "computed_at", F.lit(REFERENCE_DATE).cast("timestamp")
)

# Cast to correct types
host_features = host_features.select(
    F.col("host_id").cast("long"),
    F.col("computed_at"),
    F.col("avg_rating").cast("double"),
    F.col("total_completed_bookings").cast("int"),
    F.col("cancellation_rate").cast("double"),
    F.col("response_rate").cast("double"),
    F.col("is_superhost").cast("boolean"),
    F.col("superhost_score").cast("double"),
    F.col("total_revenue").cast("double"),
    F.col("avg_occupancy_rate").cast("double"),
    F.col("property_count").cast("int")
)

print(f"Host features count: {host_features.count()}")
host_features.show(5, truncate=False)

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
    primary_keys=["host_id", "computed_at"],
    timeseries_columns="computed_at",
    df=host_features,
    description="Host performance features for superhost qualification and scoring. "
                "Trailing 90-day window. Superhost criteria per Analytics Handbook S4.1."
)

print(f"Feature table created: {FEATURE_TABLE_NAME}")
print(f"Rows written: {spark.table(FEATURE_TABLE_NAME).count()}")
