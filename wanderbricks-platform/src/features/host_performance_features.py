# Databricks notebook source
# MAGIC %md
# MAGIC # Host Performance Feature Table
# MAGIC
# MAGIC Computes ML-ready features for host performance prediction and superhost qualification.
# MAGIC Features: avg_rating_90d, completed_bookings_90d, cancellation_rate, response_rate, is_superhost, superhost_score

# COMMAND ----------

dbutils.widgets.text("catalog", "", "Catalog")
dbutils.widgets.text("schema", "", "Schema")

catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.window import Window

# Source tables
bookings = spark.table(f"{catalog}.{schema}.silver_bookings")
reviews = spark.table(f"{catalog}.{schema}.silver_reviews")
hosts = spark.table(f"{catalog}.{schema}.silver_hosts")
properties_df = spark.table(f"{catalog}.{schema}.silver_properties")

# Use data-relative reference dates (handles historical datasets)
ref_date = reviews.agg(F.max(F.to_date("created_at"))).collect()[0][0]
booking_ref = bookings.agg(F.max(F.to_date("created_at"))).collect()[0][0]
print(f"Reference dates - reviews: {ref_date}, bookings: {booking_ref}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Feature: avg_rating_90d
# MAGIC Average rating across all host's properties in trailing 90 days

# COMMAND ----------

recent_reviews = (
    reviews
    .filter(F.to_date("created_at") >= F.date_sub(F.lit(ref_date), 90))
    .join(properties_df.select("property_id", "host_id"), on="property_id")
)

avg_rating_90d = (
    recent_reviews
    .groupBy("host_id")
    .agg(
        F.avg("rating").alias("avg_rating_90d"),
        F.count("review_id").alias("review_count_90d")
    )
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Feature: completed_bookings_90d
# MAGIC Count of completed bookings in trailing 90 days (>=10 for superhost)

# COMMAND ----------

completed_90d = (
    bookings
    .filter(
        (F.col("status") == "completed") &
        (F.to_date("created_at") >= F.date_sub(F.lit(booking_ref), 90))
    )
    .join(properties_df.select("property_id", "host_id"), on="property_id")
    .groupBy("host_id")
    .agg(F.count("booking_id").alias("completed_bookings_90d"))
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Feature: cancellation_rate
# MAGIC Cancelled bookings / total eligible bookings (<2% for superhost)

# COMMAND ----------

cancellation_stats = (
    bookings
    .filter(F.col("status").isin("confirmed", "completed", "cancelled"))
    .join(properties_df.select("property_id", "host_id"), on="property_id")
    .groupBy("host_id")
    .agg(
        F.count(F.when(F.col("status") == "cancelled", 1)).alias("host_cancellations"),
        F.count("booking_id").alias("total_eligible_bookings")
    )
    .withColumn(
        "cancellation_rate",
        F.when(F.col("total_eligible_bookings") > 0,
               F.col("host_cancellations") / F.col("total_eligible_bookings"))
        .otherwise(0.0)
    )
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Feature: response_rate
# MAGIC Proxy: bookings that moved to confirmed/completed vs total bookings (>=90% for superhost)

# COMMAND ----------

response_stats = (
    bookings
    .join(properties_df.select("property_id", "host_id"), on="property_id")
    .groupBy("host_id")
    .agg(
        F.count(F.when(F.col("status").isin("confirmed", "completed"), 1)).alias("responded_bookings"),
        F.count("booking_id").alias("total_bookings")
    )
    .withColumn(
        "response_rate",
        F.when(F.col("total_bookings") > 0,
               F.col("responded_bookings") / F.col("total_bookings"))
        .otherwise(0.0)
    )
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Assemble Feature Table

# COMMAND ----------

host_features = (
    hosts.select("host_id", "host_name", "is_verified", "is_active", "country", "joined_at")
    .join(avg_rating_90d, on="host_id", how="left")
    .join(completed_90d, on="host_id", how="left")
    .join(
        cancellation_stats.select("host_id", "cancellation_rate", "host_cancellations", "total_eligible_bookings"),
        on="host_id", how="left"
    )
    .join(
        response_stats.select("host_id", "response_rate"),
        on="host_id", how="left"
    )
    .fillna({
        "avg_rating_90d": 0.0,
        "review_count_90d": 0,
        "completed_bookings_90d": 0,
        "cancellation_rate": 0.0,
        "response_rate": 0.0,
        "host_cancellations": 0,
        "total_eligible_bookings": 0
    })
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Feature: is_superhost (handbook criteria)
# MAGIC 1. avg_rating_90d >= 4.5
# MAGIC 2. completed_bookings_90d >= 10
# MAGIC 3. cancellation_rate < 0.02
# MAGIC 4. response_rate >= 0.90

# COMMAND ----------

host_features = host_features.withColumn(
    "is_superhost",
    (
        (F.col("avg_rating_90d") >= 4.5) &
        (F.col("completed_bookings_90d") >= 10) &
        (F.col("cancellation_rate") < 0.02) &
        (F.col("response_rate") >= 0.90)
    ).cast("boolean")
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Feature: superhost_score (composite 0-1)
# MAGIC Weighted: 40% rating, 30% bookings volume, 20% low-cancel, 10% response

# COMMAND ----------

host_features = host_features.withColumn(
    "superhost_score",
    F.round(
        (F.least(F.col("avg_rating_90d") / 5.0, F.lit(1.0)) * 0.4) +
        (F.least(F.col("completed_bookings_90d").cast("double") / 20.0, F.lit(1.0)) * 0.3) +
        (F.greatest(F.lit(1.0) - F.col("cancellation_rate") * 10.0, F.lit(0.0)) * 0.2) +
        (F.col("response_rate") * 0.1),
        4
    )
)

# Add computation timestamp
host_features = host_features.withColumn("computed_at", F.current_timestamp())

# COMMAND ----------

# MAGIC %md
# MAGIC ## Write Feature Table

# COMMAND ----------

host_features.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(
    f"{catalog}.{schema}.feature_host_performance"
)

spark.sql(f"ALTER TABLE {catalog}.{schema}.feature_host_performance SET TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true')")
spark.sql(f"COMMENT ON TABLE {catalog}.{schema}.feature_host_performance IS 'ML feature table: host performance features for superhost prediction and ranking'")
print(f"✓ Feature table written: {catalog}.{schema}.feature_host_performance")
