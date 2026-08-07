-- Metric View: Guest Satisfaction
-- Handbook Section: 3.1 (GSS with recency weighting), 3.3 (Negative Review Rate)
-- Grain: Per property_id
-- Source: silver_reviews JOIN silver_properties

CREATE WIDGET TEXT catalog_use DEFAULT "";
CREATE WIDGET TEXT schema_use DEFAULT "";

USE CATALOG IDENTIFIER(:catalog_use);
USE SCHEMA IDENTIFIER(:schema_use);

CREATE OR REPLACE MATERIALIZED VIEW mv_guest_satisfaction
COMMENT 'Guest Satisfaction Score (GSS) per property with recency weighting. Weights: 30d=3.0, 90d=2.0, 365d=1.0, older=0.5. Scale: 1.0-5.0. Target: platform-wide >= 4.2.'
AS
WITH weighted_reviews AS (
  SELECT
    r.property_id,
    r.rating,
    r.created_at AS reviewed_at,
    -- Handbook 3.1: Recency weights
    CASE
      WHEN DATEDIFF(CURRENT_DATE(), DATE(r.created_at)) <= 30 THEN 3.0
      WHEN DATEDIFF(CURRENT_DATE(), DATE(r.created_at)) <= 90 THEN 2.0
      WHEN DATEDIFF(CURRENT_DATE(), DATE(r.created_at)) <= 365 THEN 1.0
      ELSE 0.5
    END AS recency_weight
  FROM silver_reviews r
  -- Handbook 3.1: WHERE is_deleted = false
  WHERE r.is_deleted = false
    AND r.rating IS NOT NULL
    AND r.rating BETWEEN 1.0 AND 5.0
)
SELECT
  wr.property_id,
  p.destination_id,
  p.destination_name,
  -- Handbook 3.1: GSS = SUM(rating * recency_weight) / SUM(recency_weight)
  SUM(wr.rating * wr.recency_weight) / SUM(wr.recency_weight) AS gss,
  -- Simple average for comparison
  AVG(wr.rating) AS simple_avg_rating,
  -- Review volume
  COUNT(*) AS review_count,
  -- Handbook 3.3: Negative Review Rate = COUNT(rating < 3.0) / COUNT(all)
  COUNT(CASE WHEN wr.rating < 3.0 THEN 1 END) AS negative_review_count,
  CAST(COUNT(CASE WHEN wr.rating < 3.0 THEN 1 END) AS DOUBLE) / COUNT(*) AS negative_review_rate
FROM weighted_reviews wr
INNER JOIN silver_properties p ON wr.property_id = p.property_id
GROUP BY wr.property_id, p.destination_id, p.destination_name;
