-- Metric View: Revenue Metrics
-- Handbook Sections: 1.1 (GBV), 1.2 (Net Revenue), 1.3 (ADR)
-- Grain: Daily by property_id, destination_id
-- Source: silver_bookings JOIN silver_properties

CREATE WIDGET TEXT catalog_use DEFAULT "";
CREATE WIDGET TEXT schema_use DEFAULT "";

USE CATALOG IDENTIFIER(:catalog_use);
USE SCHEMA IDENTIFIER(:schema_use);

CREATE OR REPLACE MATERIALIZED VIEW mv_revenue_metrics
COMMENT 'Daily revenue metrics per property and destination. GBV = SUM(total_amount) WHERE confirmed. Net Revenue = GBV x 0.15 (platform commission). ADR = revenue per booked night (confirmed + completed).'
AS
SELECT
  DATE(b.created_at) AS booking_date,
  b.property_id,
  p.destination_id,
  p.destination_name,
  p.property_type,
  -- Handbook 1.1: GBV = SUM(total_amount) WHERE status = 'confirmed'
  SUM(CASE WHEN b.status = 'confirmed' THEN b.total_amount ELSE 0 END) AS gbv,
  -- Handbook 1.2: Net Revenue = GBV * 0.15
  SUM(CASE WHEN b.status = 'confirmed' THEN b.total_amount * 0.15 ELSE 0 END) AS net_revenue,
  -- Host payout = GBV * 0.85
  SUM(CASE WHEN b.status = 'confirmed' THEN b.total_amount * 0.85 ELSE 0 END) AS host_payout,
  -- Confirmed booking count
  COUNT(CASE WHEN b.status = 'confirmed' THEN 1 END) AS confirmed_booking_count,
  -- Handbook 1.3: ADR = SUM(total_amount) / SUM(duration_nights) WHERE status IN ('confirmed','completed')
  CASE
    WHEN SUM(CASE WHEN b.status IN ('confirmed', 'completed') THEN b.duration_nights ELSE 0 END) > 0
    THEN SUM(CASE WHEN b.status IN ('confirmed', 'completed') THEN b.total_amount ELSE 0 END)
       / SUM(CASE WHEN b.status IN ('confirmed', 'completed') THEN b.duration_nights ELSE 0 END)
    ELSE NULL
  END AS adr,
  -- Supporting metrics
  SUM(CASE WHEN b.status = 'confirmed' THEN b.duration_nights ELSE 0 END) AS total_nights,
  SUM(CASE WHEN b.status = 'confirmed' THEN b.guests_count ELSE 0 END) AS total_guests
FROM silver_bookings b
INNER JOIN silver_properties p ON b.property_id = p.property_id
GROUP BY
  DATE(b.created_at),
  b.property_id,
  p.destination_id,
  p.destination_name,
  p.property_type;
