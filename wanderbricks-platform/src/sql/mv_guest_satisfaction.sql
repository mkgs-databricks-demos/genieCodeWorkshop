-- Databricks notebook source
-- Guest Satisfaction Metric View: GSS with recency weighting
-- Grain: per property_id
-- Source of truth: WanderBricks Analytics Handbook Section 3

CREATE WIDGET TEXT catalog_name DEFAULT "hls_fde_dev";
CREATE WIDGET TEXT schema_name DEFAULT "dev_matthew_giglia_wanderbricks_ai";

-- COMMAND ----------

CREATE OR REPLACE MATERIALIZED VIEW IDENTIFIER(:catalog_name || '.' || :schema_name || '.mv_guest_satisfaction')
COMMENT 'Guest Satisfaction Score (GSS) per property with recency weighting. Weights: 30d=3.0, 90d=2.0, 365d=1.0, older=0.5. Scale: 1.0-5.0. Target: platform-wide GSS >= 4.2.'
AS
WITH weighted_reviews AS (
  SELECT
    r.property_id, r.rating, r.created_at AS reviewed_at,
    CASE
      WHEN DATEDIFF(CURRENT_DATE(), DATE(r.created_at)) <= 30 THEN 3.0
      WHEN DATEDIFF(CURRENT_DATE(), DATE(r.created_at)) <= 90 THEN 2.0
      WHEN DATEDIFF(CURRENT_DATE(), DATE(r.created_at)) <= 365 THEN 1.0
      ELSE 0.5
    END AS recency_weight
  FROM IDENTIFIER(:catalog_name || '.' || :schema_name || '.silver_reviews') r
  WHERE r.rating IS NOT NULL AND r.rating BETWEEN 1.0 AND 5.0
)
SELECT
  wr.property_id, p.destination_id, p.destination_name,
  SUM(wr.rating * wr.recency_weight) / SUM(wr.recency_weight) AS gss,
  AVG(wr.rating) AS simple_avg_rating,
  COUNT(*) AS review_count,
  COUNT(CASE WHEN wr.rating < 3.0 THEN 1 END) AS negative_review_count,
  CAST(COUNT(CASE WHEN wr.rating < 3.0 THEN 1 END) AS DOUBLE) / COUNT(*) AS negative_review_rate
FROM weighted_reviews wr
JOIN IDENTIFIER(:catalog_name || '.' || :schema_name || '.silver_properties') p ON wr.property_id = p.property_id
GROUP BY wr.property_id, p.destination_id, p.destination_name;
