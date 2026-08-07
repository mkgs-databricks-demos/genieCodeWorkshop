-- Metric View: Host Performance
-- Handbook Section: 4.1 (Superhost Status)
-- Grain: Per host_id
-- Source: silver_hosts, silver_bookings, silver_reviews, silver_properties
--
-- Note: Criterion 4 (response rate >= 90%) requires the booking_updates table
-- which is not in scope for this pipeline. The qualifies_superhost flag evaluates
-- criteria 1-3 only. See WS-A status notes for details.

CREATE WIDGET TEXT catalog_use DEFAULT "";
CREATE WIDGET TEXT schema_use DEFAULT "";

USE CATALOG IDENTIFIER(:catalog_use);
USE SCHEMA IDENTIFIER(:schema_use);

CREATE OR REPLACE MATERIALIZED VIEW mv_host_performance
COMMENT 'Host performance with Superhost qualification. Criteria: avg_rating >= 4.5 (90d), completed >= 10 (90d), cancellation < 2%. Response rate criterion omitted (requires booking_updates table).'
AS
WITH host_bookings AS (
  SELECT
    p.host_id,
    -- Handbook 4.1 criterion 2: Completed bookings >= 10 (trailing 90 days)
    COUNT(CASE WHEN b.status IN ('confirmed', 'completed')
               AND b.created_at >= DATE_ADD(CURRENT_DATE(), -90) THEN 1 END) AS completed_bookings_90d,
    -- Handbook 4.1 criterion 3: Cancellation rate < 2%
    COUNT(CASE WHEN b.status = 'cancelled' THEN 1 END) AS host_cancellations,
    COUNT(CASE WHEN b.status IN ('confirmed', 'completed', 'cancelled') THEN 1 END) AS total_eligible_bookings
  FROM silver_bookings b
  INNER JOIN silver_properties p ON b.property_id = p.property_id
  GROUP BY p.host_id
),
host_ratings AS (
  SELECT
    p.host_id,
    -- Handbook 4.1 criterion 1: Average rating >= 4.5 (trailing 90 days)
    AVG(CASE WHEN r.created_at >= DATE_ADD(CURRENT_DATE(), -90) THEN r.rating END) AS avg_rating_90d,
    COUNT(CASE WHEN r.created_at >= DATE_ADD(CURRENT_DATE(), -90) THEN 1 END) AS review_count_90d
  FROM silver_reviews r
  INNER JOIN silver_properties p ON r.property_id = p.property_id
  WHERE r.rating IS NOT NULL
    AND r.is_deleted = false
  GROUP BY p.host_id
)
SELECT
  h.host_id,
  h.name AS host_name,
  h.country,
  h.is_verified,
  h.is_active,
  h.joined_at,
  COALESCE(hb.completed_bookings_90d, 0) AS completed_bookings_90d,
  COALESCE(hb.host_cancellations, 0) AS host_cancellations,
  COALESCE(hb.total_eligible_bookings, 0) AS total_eligible_bookings,
  CASE
    WHEN COALESCE(hb.total_eligible_bookings, 0) > 0
    THEN CAST(COALESCE(hb.host_cancellations, 0) AS DOUBLE) / hb.total_eligible_bookings
    ELSE 0.0
  END AS cancellation_rate,
  hr.avg_rating_90d,
  COALESCE(hr.review_count_90d, 0) AS review_count_90d,
  -- Superhost qualification (criteria 1-3; criterion 4 unavailable)
  CASE
    WHEN COALESCE(hr.avg_rating_90d, 0) >= 4.5
     AND COALESCE(hb.completed_bookings_90d, 0) >= 10
     AND (COALESCE(hb.total_eligible_bookings, 0) = 0
          OR CAST(COALESCE(hb.host_cancellations, 0) AS DOUBLE) / hb.total_eligible_bookings < 0.02)
    THEN TRUE
    ELSE FALSE
  END AS qualifies_superhost
FROM silver_hosts h
LEFT JOIN host_bookings hb ON h.host_id = hb.host_id
LEFT JOIN host_ratings hr ON h.host_id = hr.host_id;
