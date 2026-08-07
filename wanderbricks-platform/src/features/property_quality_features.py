# Databricks notebook source
# DBTITLE 1,Install Feature Engineering Client
# MAGIC %pip install databricks-feature-engineering
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# DBTITLE 1,Configuration and Imports
"""Property Quality Feature Table

Computes per-property ML features from silver layer tables:
- avg_rating: Average review rating (all time, non-deleted)
- review_count: Count of non-deleted reviews
- recent_gss: Recency-weighted Guest Satisfaction Score (Handbook 3.1)
- occupancy_rate_30d: Occupancy rate in trailing 30 days
- price_percentile: Price rank within destination
- quality_tier: Categorical tier (gold/silver/bronze/standard)
"""
from databricks.feature_engineering import FeatureEngineeringClient
from pyspark.sql import SparkSession, functions as F, Window
from datetime import date, timedelta

spark = SparkSession.builder.getOrCreate()
fe = FeatureEngineeringClient()

# Configuration
dbutils.widgets.text("catalog", "hls_fde_dev")
dbutils.widgets.text("schema", "dev_matthew_giglia_wanderbricks_ai")

catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")

FQ = f"{catalog}.{schema}"
FEATURE_TABLE = f"{FQ}.feature_property_quality"
print(f"Target: {FEATURE_TABLE}")

# COMMAND ----------

# DBTITLE 1,Compute Property Quality Features
# Load silver tables
bookings = spark.table(f"{FQ}.silver_bookings")
reviews = spark.table(f"{FQ}.silver_reviews")
properties_df = spark.table(f"{FQ}.silver_properties")

# Reference date - use data max date for historical data
max_date_row = spark.sql(f"SELECT GREATEST(MAX(created_at), (SELECT MAX(created_at) FROM {FQ}.silver_reviews)) as max_dt FROM {FQ}.silver_bookings").collect()[0]
ref_date = max_date_row[0].date() if hasattr(max_date_row[0], 'date') else date.today()
date_30d_ago = ref_date - timedelta(days=30)
date_90d_ago = ref_date - timedelta(days=90)
date_365d_ago = ref_date - timedelta(days=365)

# --- avg_rating and review_count ---
rating_features = (
    reviews
    .filter(F.col("is_deleted") == False)
    .groupBy("property_id")
    .agg(
        F.avg("rating").alias("avg_rating"),
        F.count("review_id").alias("review_count")
    )
)

# --- recent_gss (Handbook 3.1: recency-weighted) ---
# Weight: 30d=3.0, 90d=2.0, 365d=1.0, older=0.5
reviews_with_weight = (
    reviews
    .filter(F.col("is_deleted") == False)
    .withColumn(
        "recency_weight",
        F.when(F.col("created_at") >= F.lit(date_30d_ago), 3.0)
         .when(F.col("created_at") >= F.lit(date_90d_ago), 2.0)
         .when(F.col("created_at") >= F.lit(date_365d_ago), 1.0)
         .otherwise(0.5)
    )
)

gss_features = (
    reviews_with_weight
    .groupBy("property_id")
    .agg(
        (F.sum(F.col("rating") * F.col("recency_weight")) / F.sum("recency_weight")).alias("recent_gss")
    )
)

# --- occupancy_rate_30d ---
# Booked nights in last 30 days / 30 available days
booked_nights_30d = (
    bookings
    .filter(
        (F.col("status").isin("confirmed", "completed")) &
        (F.col("check_in") >= F.lit(date_30d_ago))
    )
    .groupBy("property_id")
    .agg(F.sum("duration_nights").alias("booked_nights_30d"))
)

occupancy_features = booked_nights_30d.withColumn(
    "occupancy_rate_30d",
    F.least(F.col("booked_nights_30d") / 30.0, F.lit(1.0))
).select("property_id", "occupancy_rate_30d")

# --- price_percentile (within destination) ---
w_dest = Window.partitionBy("destination_id")
price_features = (
    properties_df
    .select("property_id", "destination_id", "base_price")
    .withColumn(
        "price_percentile",
        F.percent_rank().over(w_dest.orderBy("base_price"))
    )
    .select("property_id", "price_percentile")
)

# --- Assemble features ---
features = (
    properties_df.select("property_id")
    .join(rating_features, "property_id", "left")
    .join(gss_features, "property_id", "left")
    .join(occupancy_features, "property_id", "left")
    .join(price_features, "property_id", "left")
    .fillna({
        "avg_rating": 0.0, "review_count": 0,
        "recent_gss": 0.0, "occupancy_rate_30d": 0.0,
        "price_percentile": 0.5
    })
)

# --- quality_tier (composite classification) ---
# Score = 0.4*normalized_gss + 0.3*occupancy + 0.3*review_volume
features = features.withColumn(
    "quality_score",
    ((F.col("recent_gss") - 1.0) / 4.0) * 0.4 +  # GSS 1-5 -> 0-1
    F.col("occupancy_rate_30d") * 0.3 +
    F.least(F.col("review_count") / 20.0, F.lit(1.0)) * 0.3  # 20+ reviews = max
).withColumn(
    "quality_tier",
    F.when(F.col("quality_score") >= 0.75, "gold")
     .when(F.col("quality_score") >= 0.50, "silver")
     .when(F.col("quality_score") >= 0.25, "bronze")
     .otherwise("standard")
)

# Select final columns
feature_df = features.select(
    "property_id", "avg_rating", "review_count", "recent_gss",
    "occupancy_rate_30d", "price_percentile", "quality_tier"
)

print(f"Feature rows: {feature_df.count()}")
feature_df.show(5)

# COMMAND ----------

# DBTITLE 1,Write Feature Table
# Create table with PK constraint (feature table in Unity Catalog)
# Uses CREATE TABLE IF NOT EXISTS + INSERT OVERWRITE for idempotent reruns
feature_df.createOrReplaceTempView("_prop_features_staging")

spark.sql(f"""
CREATE TABLE IF NOT EXISTS {FEATURE_TABLE} (
    property_id BIGINT NOT NULL,
    avg_rating DOUBLE,
    review_count INT,
    recent_gss DOUBLE,
    occupancy_rate_30d DOUBLE,
    price_percentile DOUBLE,
    quality_tier STRING,
    CONSTRAINT feature_property_quality_pk PRIMARY KEY (property_id)
)
COMMENT 'Property quality features for ML models. Computed daily from silver layer.'
""")

spark.sql(f"""
INSERT OVERWRITE {FEATURE_TABLE}
SELECT property_id, avg_rating, CAST(review_count AS INT),
       recent_gss, occupancy_rate_30d, price_percentile, quality_tier
FROM _prop_features_staging
""")

print(f"Feature table written: {FEATURE_TABLE}")
print(f"Rows: {spark.table(FEATURE_TABLE).count()}")
print("Property quality features complete.")