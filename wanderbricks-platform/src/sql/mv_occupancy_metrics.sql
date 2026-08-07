-- Databricks notebook source
-- Occupancy Metric View: Occupancy Rate, ALOS, Booking Lead Time
-- Grain: monthly by property_id, destination_id
-- Source of truth: WanderBricks Analytics Handbook Section 2

CREATE WIDGET TEXT catalog_name DEFAULT "hls_fde_dev";
CREATE WIDGET TEXT schema_name DEFAULT "dev_matthew_giglia_wanderbricks_ai";

-- COMMAND ----------

CREATE OR REPLACE MATERIALIZED VIEW IDENTIFIER(:catalog_name || '.' || :schema_name || '.mv_occupancy_metrics')
COMMENT 'Monthly occupancy and utilization metrics per property and destination. Occupancy Rate = booked_nights / available_nights. ALOS = avg nights per booking. Booking Lead Time = days between creation and check-in.'
AS
WITH booking_metrics AS (
  SELECT
    DATE_TRUNC('MONTH', b.check_in) AS booking_month,
    b.property_id,
    p.destination_id,
    p.destination_name,
    p.property_type,
    SUM(CASE WHEN b.status IN ('confirmed', 'completed') THEN b.duration_nights ELSE 0 END) AS booked_nights,
    COUNT(CASE WHEN b.status IN ('confirmed', 'completed') THEN 1 END) AS booking_count,
    SUM(CASE WHEN b.status IN ('confirmed', 'completed') THEN b.total_amount ELSE 0 END) AS total_revenue,
    AVG(CASE WHEN b.status IN ('confirmed', 'completed') THEN CAST(b.duration_nights AS DOUBLE) END) AS alos,
    AVG(CASE WHEN b.status IN ('confirmed', 'completed') THEN CAST(DATEDIFF(b.check_in, DATE(b.created_at)) AS DOUBLE) END) AS avg_lead_time_days
  FROM IDENTIFIER(:catalog_name || '.' || :schema_name || '.silver_bookings') b
  JOIN IDENTIFIER(:catalog_name || '.' || :schema_name || '.silver_properties') p ON b.property_id = p.property_id
  WHERE b.check_in IS NOT NULL
  GROUP BY DATE_TRUNC('MONTH', b.check_in), b.property_id, p.destination_id, p.destination_name, p.property_type
)
SELECT
  bm.booking_month, bm.property_id, bm.destination_id, bm.destination_name, bm.property_type,
  bm.booked_nights, bm.booking_count, bm.total_revenue,
  CASE WHEN bm.booked_nights > 0 THEN bm.total_revenue / bm.booked_nights ELSE NULL END AS adr,
  bm.alos,
  CASE WHEN DATEDIFF(LAST_DAY(bm.booking_month), bm.booking_month) + 1 > 0
    THEN bm.booked_nights / CAST(DATEDIFF(LAST_DAY(bm.booking_month), bm.booking_month) + 1 AS DOUBLE)
    ELSE NULL END AS occupancy_rate,
  bm.avg_lead_time_days
FROM booking_metrics bm;
