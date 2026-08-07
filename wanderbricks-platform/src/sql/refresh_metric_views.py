# Databricks notebook source
# DBTITLE 1,Parameters
dbutils.widgets.text("catalog_use", "")
dbutils.widgets.text("schema_use", "")

catalog_use = dbutils.widgets.get("catalog_use")
schema_use = dbutils.widgets.get("schema_use")

assert catalog_use, "catalog_use parameter is required"
assert schema_use, "schema_use parameter is required"

print(f"Target: {catalog_use}.{schema_use}")

# COMMAND ----------

# DBTITLE 1,Set catalog and schema context
# MAGIC %sql
# MAGIC USE CATALOG IDENTIFIER(:catalog_use);
# MAGIC USE SCHEMA IDENTIFIER(:schema_use);

# COMMAND ----------

# DBTITLE 1,mv_revenue_metrics — Handbook 1.1-1.3
# MAGIC %sql
# MAGIC CREATE OR REPLACE MATERIALIZED VIEW mv_revenue_metrics
# MAGIC COMMENT 'Daily revenue metrics per property and destination. GBV = SUM(total_amount) WHERE confirmed. Net Revenue = GBV x 0.15. ADR = revenue per booked night.'
# MAGIC AS
# MAGIC SELECT
# MAGIC   DATE(b.created_at) AS booking_date,
# MAGIC   b.property_id,
# MAGIC   p.destination_id,
# MAGIC   p.destination_name,
# MAGIC   p.property_type,
# MAGIC   SUM(CASE WHEN b.status = 'confirmed' THEN b.total_amount ELSE 0 END) AS gbv,
# MAGIC   SUM(CASE WHEN b.status = 'confirmed' THEN b.total_amount * 0.15 ELSE 0 END) AS net_revenue,
# MAGIC   SUM(CASE WHEN b.status = 'confirmed' THEN b.total_amount * 0.85 ELSE 0 END) AS host_payout,
# MAGIC   COUNT(CASE WHEN b.status = 'confirmed' THEN 1 END) AS confirmed_booking_count,
# MAGIC   CASE
# MAGIC     WHEN SUM(CASE WHEN b.status IN ('confirmed', 'completed') THEN b.duration_nights ELSE 0 END) > 0
# MAGIC     THEN SUM(CASE WHEN b.status IN ('confirmed', 'completed') THEN b.total_amount ELSE 0 END)
# MAGIC        / SUM(CASE WHEN b.status IN ('confirmed', 'completed') THEN b.duration_nights ELSE 0 END)
# MAGIC     ELSE NULL
# MAGIC   END AS adr,
# MAGIC   SUM(CASE WHEN b.status = 'confirmed' THEN b.duration_nights ELSE 0 END) AS total_nights,
# MAGIC   SUM(CASE WHEN b.status = 'confirmed' THEN b.guests_count ELSE 0 END) AS total_guests
# MAGIC FROM silver_bookings b
# MAGIC INNER JOIN silver_properties p ON b.property_id = p.property_id
# MAGIC GROUP BY
# MAGIC   DATE(b.created_at), b.property_id, p.destination_id, p.destination_name, p.property_type

# COMMAND ----------

# DBTITLE 1,mv_occupancy_metrics — Handbook 2.1-2.3
# MAGIC %sql
# MAGIC CREATE OR REPLACE MATERIALIZED VIEW mv_occupancy_metrics
# MAGIC COMMENT 'Monthly occupancy metrics. Occupancy = booked_nights / available_nights. ALOS = avg stay length. Lead time = days between booking and check-in.'
# MAGIC AS
# MAGIC WITH booking_metrics AS (
# MAGIC   SELECT
# MAGIC     DATE_TRUNC('MONTH', b.check_in) AS booking_month,
# MAGIC     b.property_id,
# MAGIC     p.destination_id,
# MAGIC     p.destination_name,
# MAGIC     p.property_type,
# MAGIC     SUM(CASE WHEN b.status IN ('confirmed', 'completed') THEN b.duration_nights ELSE 0 END) AS booked_nights,
# MAGIC     COUNT(CASE WHEN b.status IN ('confirmed', 'completed') THEN 1 END) AS booking_count,
# MAGIC     SUM(CASE WHEN b.status IN ('confirmed', 'completed') THEN b.total_amount ELSE 0 END) AS total_revenue,
# MAGIC     AVG(CASE WHEN b.status IN ('confirmed', 'completed') THEN CAST(b.duration_nights AS DOUBLE) END) AS alos,
# MAGIC     AVG(CASE WHEN b.status IN ('confirmed', 'completed')
# MAGIC         THEN CAST(DATEDIFF(b.check_in, DATE(b.created_at)) AS DOUBLE) END) AS avg_lead_time_days
# MAGIC   FROM silver_bookings b
# MAGIC   INNER JOIN silver_properties p ON b.property_id = p.property_id
# MAGIC   WHERE b.check_in IS NOT NULL
# MAGIC   GROUP BY DATE_TRUNC('MONTH', b.check_in), b.property_id, p.destination_id, p.destination_name, p.property_type
# MAGIC )
# MAGIC SELECT
# MAGIC   bm.booking_month, bm.property_id, bm.destination_id, bm.destination_name, bm.property_type,
# MAGIC   bm.booked_nights,
# MAGIC   DATEDIFF(LAST_DAY(bm.booking_month), bm.booking_month) + 1 AS available_nights,
# MAGIC   CASE
# MAGIC     WHEN DATEDIFF(LAST_DAY(bm.booking_month), bm.booking_month) + 1 > 0
# MAGIC     THEN bm.booked_nights / CAST(DATEDIFF(LAST_DAY(bm.booking_month), bm.booking_month) + 1 AS DOUBLE)
# MAGIC     ELSE NULL
# MAGIC   END AS occupancy_rate,
# MAGIC   bm.booking_count, bm.total_revenue,
# MAGIC   CASE WHEN bm.booked_nights > 0 THEN bm.total_revenue / bm.booked_nights ELSE NULL END AS adr,
# MAGIC   bm.alos,
# MAGIC   bm.avg_lead_time_days
# MAGIC FROM booking_metrics bm

# COMMAND ----------

# DBTITLE 1,mv_guest_satisfaction — Handbook 3.1, 3.3
# MAGIC %sql
# MAGIC CREATE OR REPLACE MATERIALIZED VIEW mv_guest_satisfaction
# MAGIC COMMENT 'Guest Satisfaction Score per property with recency weighting (30d=3.0, 90d=2.0, 365d=1.0, older=0.5). Scale: 1.0-5.0.'
# MAGIC AS
# MAGIC WITH weighted_reviews AS (
# MAGIC   SELECT
# MAGIC     r.property_id, r.rating,
# MAGIC     CASE
# MAGIC       WHEN DATEDIFF(CURRENT_DATE(), DATE(r.created_at)) <= 30 THEN 3.0
# MAGIC       WHEN DATEDIFF(CURRENT_DATE(), DATE(r.created_at)) <= 90 THEN 2.0
# MAGIC       WHEN DATEDIFF(CURRENT_DATE(), DATE(r.created_at)) <= 365 THEN 1.0
# MAGIC       ELSE 0.5
# MAGIC     END AS recency_weight
# MAGIC   FROM silver_reviews r
# MAGIC   WHERE r.is_deleted = false
# MAGIC     AND r.rating IS NOT NULL
# MAGIC     AND r.rating BETWEEN 1.0 AND 5.0
# MAGIC )
# MAGIC SELECT
# MAGIC   wr.property_id, p.destination_id, p.destination_name,
# MAGIC   SUM(wr.rating * wr.recency_weight) / SUM(wr.recency_weight) AS gss,
# MAGIC   AVG(wr.rating) AS simple_avg_rating,
# MAGIC   COUNT(*) AS review_count,
# MAGIC   COUNT(CASE WHEN wr.rating < 3.0 THEN 1 END) AS negative_review_count,
# MAGIC   CAST(COUNT(CASE WHEN wr.rating < 3.0 THEN 1 END) AS DOUBLE) / COUNT(*) AS negative_review_rate
# MAGIC FROM weighted_reviews wr
# MAGIC INNER JOIN silver_properties p ON wr.property_id = p.property_id
# MAGIC GROUP BY wr.property_id, p.destination_id, p.destination_name

# COMMAND ----------

# DBTITLE 1,mv_host_performance — Handbook 4.1
# MAGIC %sql
# MAGIC CREATE OR REPLACE MATERIALIZED VIEW mv_host_performance
# MAGIC COMMENT 'Host performance with Superhost qualification. Criteria: avg_rating >= 4.5 (90d), completed >= 10 (90d), cancellation < 2%. Response rate criterion unavailable.'
# MAGIC AS
# MAGIC WITH host_bookings AS (
# MAGIC   SELECT p.host_id,
# MAGIC     COUNT(CASE WHEN b.status IN ('confirmed', 'completed') AND b.created_at >= DATE_ADD(CURRENT_DATE(), -90) THEN 1 END) AS completed_bookings_90d,
# MAGIC     COUNT(CASE WHEN b.status = 'cancelled' THEN 1 END) AS host_cancellations,
# MAGIC     COUNT(CASE WHEN b.status IN ('confirmed', 'completed', 'cancelled') THEN 1 END) AS total_eligible_bookings
# MAGIC   FROM silver_bookings b
# MAGIC   INNER JOIN silver_properties p ON b.property_id = p.property_id
# MAGIC   GROUP BY p.host_id
# MAGIC ),
# MAGIC host_ratings AS (
# MAGIC   SELECT p.host_id,
# MAGIC     AVG(CASE WHEN r.created_at >= DATE_ADD(CURRENT_DATE(), -90) THEN r.rating END) AS avg_rating_90d,
# MAGIC     COUNT(CASE WHEN r.created_at >= DATE_ADD(CURRENT_DATE(), -90) THEN 1 END) AS review_count_90d
# MAGIC   FROM silver_reviews r
# MAGIC   INNER JOIN silver_properties p ON r.property_id = p.property_id
# MAGIC   WHERE r.rating IS NOT NULL AND r.is_deleted = false
# MAGIC   GROUP BY p.host_id
# MAGIC )
# MAGIC SELECT h.host_id, h.name AS host_name, h.country, h.is_verified, h.is_active, h.joined_at,
# MAGIC   COALESCE(hb.completed_bookings_90d, 0) AS completed_bookings_90d,
# MAGIC   COALESCE(hb.host_cancellations, 0) AS host_cancellations,
# MAGIC   COALESCE(hb.total_eligible_bookings, 0) AS total_eligible_bookings,
# MAGIC   CASE WHEN COALESCE(hb.total_eligible_bookings, 0) > 0
# MAGIC     THEN CAST(COALESCE(hb.host_cancellations, 0) AS DOUBLE) / hb.total_eligible_bookings ELSE 0.0 END AS cancellation_rate,
# MAGIC   hr.avg_rating_90d,
# MAGIC   COALESCE(hr.review_count_90d, 0) AS review_count_90d,
# MAGIC   CASE WHEN COALESCE(hr.avg_rating_90d, 0) >= 4.5
# MAGIC     AND COALESCE(hb.completed_bookings_90d, 0) >= 10
# MAGIC     AND (COALESCE(hb.total_eligible_bookings, 0) = 0
# MAGIC          OR CAST(COALESCE(hb.host_cancellations, 0) AS DOUBLE) / hb.total_eligible_bookings < 0.02)
# MAGIC     THEN TRUE ELSE FALSE END AS qualifies_superhost
# MAGIC FROM silver_hosts h
# MAGIC LEFT JOIN host_bookings hb ON h.host_id = hb.host_id
# MAGIC LEFT JOIN host_ratings hr ON h.host_id = hr.host_id

# COMMAND ----------

