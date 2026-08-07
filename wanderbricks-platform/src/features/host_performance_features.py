# Databricks notebook source
# DBTITLE 1,Install Feature Engineering Client
# MAGIC %pip install databricks-feature-engineering
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# DBTITLE 1,Configuration and Imports
"""Host Performance Feature Table

Computes per-host ML features from silver layer tables:
- avg_rating_90d: Average review rating (trailing 90 days)
- completed_bookings_90d: Completed booking count (trailing 90 days)
- cancellation_rate: Overall cancellation rate
- response_rate: NULL (requires booking_updates, not in scope)
- is_superhost: Boolean per Handbook 4.1 criteria 1-3
- superhost_score: Composite score 0.0-1.0
"""
from databricks.feature_engineering import FeatureEngineeringClient
from pyspark.sql import SparkSession, functions as F, Window
from datetime import date, timedelta

spark = SparkSession.builder.getOrCreate()
fe = FeatureEngineeringClient()

# Configuration - parameterised via widgets for bundle flexibility
dbutils.widgets.text("catalog", "hls_fde_dev")
dbutils.widgets.text("schema", "dev_matthew_giglia_wanderbricks_ai")

catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")

FQ = f"{catalog}.{schema}"
FEATURE_TABLE = f"{FQ}.feature_host_performance"
print(f"Target: {FEATURE_TABLE}")

# COMMAND ----------

# DBTITLE 1,Compute Host Performance Features
# Load silver tables
bookings = spark.table(f"{FQ}.silver_bookings")
reviews = spark.table(f"{FQ}.silver_reviews")
hosts = spark.table(f"{FQ}.silver_hosts")
properties_df = spark.table(f"{FQ}.silver_properties").select("property_id", "host_id")

# Reference date for trailing windows — use data max date for historical data
# This ensures features are meaningful even when source data is not real-time
max_date_row = spark.sql(f"SELECT GREATEST(MAX(created_at), (SELECT MAX(created_at) FROM {FQ}.silver_reviews)) as max_dt FROM {FQ}.silver_bookings").collect()[0]
ref_date = max_date_row[0].date() if hasattr(max_date_row[0], 'date') else date.today()
date_90d_ago = ref_date - timedelta(days=90)

# --- avg_rating_90d ---
# Join reviews -> properties to get host_id, filter to last 90 days, non-deleted
host_ratings_90d = (
    reviews
    .filter((F.col("is_deleted") == False) & (F.col("created_at") >= F.lit(date_90d_ago)))
    .join(properties_df, "property_id")
    .groupBy("host_id")
    .agg(F.avg("rating").alias("avg_rating_90d"))
)

# --- completed_bookings_90d ---
completed_90d = (
    bookings
    .filter((F.col("status") == "completed") & (F.col("created_at") >= F.lit(date_90d_ago)))
    .join(properties_df, "property_id")
    .groupBy("host_id")
    .agg(F.count("booking_id").alias("completed_bookings_90d"))
)

# --- cancellation_rate (overall, not time-windowed) ---
# Per WS-A caveat: no booking_updates table, so this is overall booking-cancellation proxy
booking_stats = (
    bookings
    .filter(F.col("status").isin("confirmed", "completed", "cancelled"))
    .join(properties_df, "property_id")
    .groupBy("host_id")
    .agg(
        F.count("booking_id").alias("total_bookings"),
        F.sum(F.when(F.col("status") == "cancelled", 1).otherwise(0)).alias("cancelled_bookings")
    )
)
cancellation_df = booking_stats.withColumn(
    "cancellation_rate",
    F.when(F.col("total_bookings") > 0, F.col("cancelled_bookings") / F.col("total_bookings"))
     .otherwise(0.0)
).select("host_id", "cancellation_rate")

# --- Assemble features ---
features = (
    hosts.select("host_id")
    .join(host_ratings_90d, "host_id", "left")
    .join(completed_90d, "host_id", "left")
    .join(cancellation_df, "host_id", "left")
    .fillna({"avg_rating_90d": 0.0, "completed_bookings_90d": 0, "cancellation_rate": 0.0})
    .withColumn("response_rate", F.lit(None).cast("double"))  # Not computable
)

# --- is_superhost (Handbook 4.1 criteria 1-3, excluding response_rate) ---
features = features.withColumn(
    "is_superhost",
    (F.col("avg_rating_90d") >= 4.5) &
    (F.col("completed_bookings_90d") >= 10) &
    (F.col("cancellation_rate") < 0.02)
)

# --- superhost_score (composite 0-1) ---
# Weighted: 40% rating, 30% volume, 30% low-cancellation
features = features.withColumn(
    "superhost_score",
    F.least(
        F.lit(1.0),
        F.greatest(
            F.lit(0.0),
            (
                # Rating: (avg_rating - 1) / 4 * 0.4  (maps 1-5 to 0-0.4)
                ((F.col("avg_rating_90d") - 1.0) / 4.0) * 0.4 +
                # Volume: min(completed/10, 1) * 0.3
                F.least(F.col("completed_bookings_90d") / 10.0, F.lit(1.0)) * 0.3 +
                # Low-cancellation: (1 - cancellation_rate) * 0.3
                (1.0 - F.col("cancellation_rate")) * 0.3
            )
        )
    )
)

# Select final columns
feature_df = features.select(
    "host_id", "avg_rating_90d", "completed_bookings_90d",
    "cancellation_rate", "response_rate", "is_superhost", "superhost_score"
)

print(f"Feature rows: {feature_df.count()}")
feature_df.show(5)

# COMMAND ----------

# DBTITLE 1,Write Feature Table
# Create table with PK constraint (feature table in Unity Catalog)
# Uses CREATE OR REPLACE + INSERT OVERWRITE for idempotent reruns
feature_df.createOrReplaceTempView("_host_features_staging")

spark.sql(f"""
CREATE TABLE IF NOT EXISTS {FEATURE_TABLE} (
    host_id BIGINT NOT NULL,
    avg_rating_90d DOUBLE,
    completed_bookings_90d INT,
    cancellation_rate DOUBLE,
    response_rate DOUBLE,
    is_superhost BOOLEAN,
    superhost_score DOUBLE,
    CONSTRAINT feature_host_performance_pk PRIMARY KEY (host_id)
)
COMMENT 'Host performance features for ML models. Computed daily from silver layer.'
""")

spark.sql(f"""
INSERT OVERWRITE {FEATURE_TABLE}
SELECT host_id, avg_rating_90d, CAST(completed_bookings_90d AS INT),
       cancellation_rate, response_rate, is_superhost, superhost_score
FROM _host_features_staging
""")

print(f"Feature table written: {FEATURE_TABLE}")
print(f"Rows: {spark.table(FEATURE_TABLE).count()}")
print("Host performance features complete.")