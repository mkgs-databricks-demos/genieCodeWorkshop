-- Databricks notebook source
-- Revenue Metric View: GBV, Net Revenue, ADR
-- Grain: daily by property_id, destination_id
-- Source of truth: WanderBricks Analytics Handbook Section 1

CREATE WIDGET TEXT catalog_name DEFAULT "hls_fde_dev";
CREATE WIDGET TEXT schema_name DEFAULT "dev_matthew_giglia_wanderbricks_ai";

-- COMMAND ----------

CREATE OR REPLACE MATERIALIZED VIEW IDENTIFIER(:catalog_name || '.' || :schema_name || '.mv_revenue_metrics')
COMMENT 'Daily revenue metrics per property and destination. GBV = SUM(total_amount) WHERE confirmed. Net Revenue = GBV x 0.15 (platform commission). ADR = revenue per booked night (confirmed + completed).'
AS
SELECT
  DATE(b.created_at) AS booking_date,
  b.property_id,
  p.destination_id,
  p.destination_name,
  p.property_type,
  SUM(CASE WHEN b.status = 'confirmed' THEN b.total_amount ELSE 0 END) AS gbv,
  SUM(CASE WHEN b.status = 'confirmed' THEN b.total_amount * 0.15 ELSE 0 END) AS net_revenue,
  CASE
    WHEN SUM(CASE WHEN b.status IN ('confirmed', 'completed') THEN b.duration_nights ELSE 0 END) > 0
    THEN SUM(CASE WHEN b.status IN ('confirmed', 'completed') THEN b.total_amount ELSE 0 END)
       / SUM(CASE WHEN b.status IN ('confirmed', 'completed') THEN b.duration_nights ELSE 0 END)
    ELSE NULL
  END AS adr,
  COUNT(CASE WHEN b.status = 'confirmed' THEN 1 END) AS confirmed_booking_count,
  SUM(CASE WHEN b.status = 'confirmed' THEN b.duration_nights ELSE 0 END) AS total_nights,
  SUM(CASE WHEN b.status = 'confirmed' THEN b.guests_count ELSE 0 END) AS total_guests
FROM IDENTIFIER(:catalog_name || '.' || :schema_name || '.silver_bookings') b
JOIN IDENTIFIER(:catalog_name || '.' || :schema_name || '.silver_properties') p
  ON b.property_id = p.property_id
GROUP BY
  DATE(b.created_at),
  b.property_id,
  p.destination_id,
  p.destination_name,
  p.property_type;
