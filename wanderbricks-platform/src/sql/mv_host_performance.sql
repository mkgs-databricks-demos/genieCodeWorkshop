-- Databricks notebook source
-- Host Performance Metric View: Superhost qualification
-- Grain: per host_id
-- Source of truth: WanderBricks Analytics Handbook Section 4

CREATE WIDGET TEXT catalog_name DEFAULT "hls_fde_dev";
CREATE WIDGET TEXT schema_name DEFAULT "dev_matthew_giglia_wanderbricks_ai";

-- COMMAND ----------

CREATE OR REPLACE MATERIALIZED VIEW IDENTIFIER(:catalog_name || '.' || :schema_name || '.mv_host_performance')
COMMENT 'Host performance with Superhost qualification. Criteria (ALL required): avg_rating >= 4.5 (90d), completed_bookings >= 10 (90d), cancellation_rate < 2%, response_rate >= 90%.'
AS
WITH host_bookings AS (
  SELECT p.host_id,
    COUNT(CASE WHEN b.status IN ('confirmed', 'completed') AND b.created_at >= DATE_ADD(CURRENT_DATE(), -90) THEN 1 END) AS completed_bookings_90d,
    COUNT(CASE WHEN b.status = 'cancelled' THEN 1 END) AS host_cancellations,
    COUNT(CASE WHEN b.status IN ('confirmed', 'completed', 'cancelled') THEN 1 END) AS total_eligible_bookings
  FROM IDENTIFIER(:catalog_name || '.' || :schema_name || '.silver_bookings') b
  JOIN IDENTIFIER(:catalog_name || '.' || :schema_name || '.silver_properties') p ON b.property_id = p.property_id
  GROUP BY p.host_id
),
host_ratings AS (
  SELECT p.host_id,
    AVG(CASE WHEN r.created_at >= DATE_ADD(CURRENT_DATE(), -90) THEN r.rating END) AS avg_rating_90d,
    COUNT(CASE WHEN r.created_at >= DATE_ADD(CURRENT_DATE(), -90) THEN 1 END) AS review_count_90d
  FROM IDENTIFIER(:catalog_name || '.' || :schema_name || '.silver_reviews') r
  JOIN IDENTIFIER(:catalog_name || '.' || :schema_name || '.silver_properties') p ON r.property_id = p.property_id
  WHERE r.rating IS NOT NULL
  GROUP BY p.host_id
)
SELECT h.host_id, h.host_name, h.country, h.is_verified, h.is_active, h.joined_at,
  COALESCE(hb.completed_bookings_90d, 0) AS completed_bookings_90d,
  COALESCE(hb.host_cancellations, 0) AS host_cancellations,
  COALESCE(hb.total_eligible_bookings, 0) AS total_eligible_bookings,
  CASE WHEN COALESCE(hb.total_eligible_bookings, 0) > 0
    THEN CAST(COALESCE(hb.host_cancellations, 0) AS DOUBLE) / hb.total_eligible_bookings ELSE 0.0 END AS cancellation_rate,
  hr.avg_rating_90d,
  COALESCE(hr.review_count_90d, 0) AS review_count_90d,
  CASE WHEN COALESCE(hr.avg_rating_90d, 0) >= 4.5
    AND COALESCE(hb.completed_bookings_90d, 0) >= 10
    AND (COALESCE(hb.total_eligible_bookings, 0) = 0
         OR CAST(COALESCE(hb.host_cancellations, 0) AS DOUBLE) / hb.total_eligible_bookings < 0.02)
    THEN TRUE ELSE FALSE END AS qualifies_superhost
FROM IDENTIFIER(:catalog_name || '.' || :schema_name || '.silver_hosts') h
LEFT JOIN host_bookings hb ON h.host_id = hb.host_id
LEFT JOIN host_ratings hr ON h.host_id = hr.host_id;
