# Databricks notebook source
# MAGIC %md
# MAGIC # Property Quality Feature Table
# MAGIC
# MAGIC Computes ML-ready features for property ranking, pricing optimization, and tier classification.
# MAGIC Features: avg_rating, review_count, recent_gss, occupancy_rate_30d, price_percentile, quality_tier

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
properties_df = spark.table(f"{catalog}.{schema}.silver_properties")

# Use data-relative reference dates (handles historical datasets)
review_ref = reviews.agg(F.max(F.to_date("created_at"))).collect()[0][0]
booking_ref = bookings.agg(F.max(F.to_date("created_at"))).collect()[0][0]
print(f"Reference dates - reviews: {review_ref}, bookings: {booking_ref}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Feature: avg_rating & review_count

# COMMAND ----------

avg_rating = (
    reviews
    .groupBy("property_id")
    .agg(
        F.avg("rating").alias("avg_rating"),
        F.count("review_id").alias("review_count")
    )
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Feature: recent_gss (recency-weighted Guest Satisfaction Score)
# MAGIC Per handbook: 30d weight=3.0, 90d=2.0, 365d=1.0, older=0.5

# COMMAND ----------

reviews_weighted = reviews.withColumn(
    "recency_weight",
    F.when(F.to_date("created_at") >= F.date_sub(F.lit(review_ref), 30), 3.0)
    .when(F.to_date("created_at") >= F.date_sub(F.lit(review_ref), 90), 2.0)
    .when(F.to_date("created_at") >= F.date_sub(F.lit(review_ref), 365), 1.0)
    .otherwise(0.5)
)

recent_gss = (
    reviews_weighted
    .groupBy("property_id")
    .agg(
        (F.sum(F.col("rating") * F.col("recency_weight")) / F.sum("recency_weight")).alias("recent_gss")
    )
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Feature: occupancy_rate_30d
# MAGIC Booked nights in last 30 days / 30 (capped at 1.0)

# COMMAND ----------

occupancy_30d = (
    bookings
    .filter(
        (F.col("status").isin("confirmed", "completed")) &
        (F.col("check_in") >= F.date_sub(F.lit(booking_ref), 30))
    )
    .groupBy("property_id")
    .agg(
        F.sum("duration_nights").alias("booked_nights_30d"),
        F.count("booking_id").alias("bookings_30d")
    )
    .withColumn(
        "occupancy_rate_30d",
        F.least(F.col("booked_nights_30d") / 30.0, F.lit(1.0))
    )
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Feature: price_percentile
# MAGIC PERCENT_RANK of base_price within destination

# COMMAND ----------

w_dest = Window.partitionBy("destination_id").orderBy("base_price")
properties_ranked = properties_df.withColumn(
    "price_percentile", F.percent_rank().over(w_dest)
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Assemble Feature Table

# COMMAND ----------

property_features = (
    properties_ranked
    .select(
        "property_id", "host_id", "destination_id", "destination_name",
        "title", "property_type", "base_price", "max_guests",
        "bedrooms", "bathrooms", "price_percentile", "listed_at"
    )
    .join(avg_rating, on="property_id", how="left")
    .join(recent_gss, on="property_id", how="left")
    .join(
        occupancy_30d.select("property_id", "occupancy_rate_30d", "booked_nights_30d", "bookings_30d"),
        on="property_id", how="left"
    )
    .fillna({
        "avg_rating": 0.0,
        "review_count": 0,
        "recent_gss": 0.0,
        "occupancy_rate_30d": 0.0,
        "booked_nights_30d": 0,
        "bookings_30d": 0
    })
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Feature: quality_tier
# MAGIC platinum: avg_rating >= 4.5 AND review_count >= 20
# MAGIC gold: avg_rating >= 4.0 AND review_count >= 10
# MAGIC silver: avg_rating >= 3.5 AND review_count >= 5
# MAGIC bronze: everything else

# COMMAND ----------

property_features = property_features.withColumn(
    "quality_tier",
    F.when(
        (F.col("avg_rating") >= 4.5) & (F.col("review_count") >= 20), "platinum"
    ).when(
        (F.col("avg_rating") >= 4.0) & (F.col("review_count") >= 10), "gold"
    ).when(
        (F.col("avg_rating") >= 3.5) & (F.col("review_count") >= 5), "silver"
    ).otherwise("bronze")
)

# Add computation timestamp
property_features = property_features.withColumn("computed_at", F.current_timestamp())

# COMMAND ----------

# MAGIC %md
# MAGIC ## Write Feature Table

# COMMAND ----------

property_features.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(
    f"{catalog}.{schema}.feature_property_quality"
)

spark.sql(f"ALTER TABLE {catalog}.{schema}.feature_property_quality SET TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true')")
spark.sql(f"COMMENT ON TABLE {catalog}.{schema}.feature_property_quality IS 'ML feature table: property quality features for ranking, pricing, and tier classification'")
print(f"✓ Feature table written: {catalog}.{schema}.feature_property_quality")
