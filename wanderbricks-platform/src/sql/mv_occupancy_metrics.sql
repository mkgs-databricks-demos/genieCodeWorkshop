-- Metric View: Occupancy Metrics
-- Handbook Sections: 2.1 (Occupancy Rate), 2.3 (ALOS), 2.2 (Booking Lead Time)
-- Grain: Monthly by property_id, destination_id
-- Source: silver_bookings JOIN silver_properties

CREATE WIDGET TEXT catalog_use DEFAULT "";
CREATE WIDGET TEXT schema_use DEFAULT "";

USE CATALOG IDENTIFIER(:catalog_use);
USE SCHEMA IDENTIFIER(:schema_use);

CREATE OR REPLACE MATERIALIZED VIEW mv_occupancy_metrics
COMMENT 'Monthly occupancy metrics per property and destination. Occupancy = booked_nights / available_nights. ALOS = avg nights per stay. Lead time = days between booking creation and check-in.'
AS
WITH booking_metrics AS (
  SELECT
    DATE_TRUNC('MONTH', b.check_in) AS booking_month,
    b.property_id,
    p.destination_id,
    p.destination_name,
    p.property_type,
    -- Handbook 2.1: Booked Nights = SUM(DATEDIFF(check_out, check_in)) WHERE confirmed/completed
    SUM(CASE WHEN b.status IN ('confirmed', 'completed') THEN b.duration_nights ELSE 0 END) AS booked_nights,
    -- Booking count
    COUNT(CASE WHEN b.status IN ('confirmed', 'completed') THEN 1 END) AS booking_count,
    -- Total revenue for ADR
    SUM(CASE WHEN b.status IN ('confirmed', 'completed') THEN b.total_amount ELSE 0 END) AS total_revenue,
    -- Handbook 2.3: ALOS = AVG(DATEDIFF(check_out, check_in)) WHERE confirmed/completed
    AVG(CASE WHEN b.status IN ('confirmed', 'completed') THEN CAST(b.duration_nights AS DOUBLE) END) AS alos,
    -- Handbook 2.2: Booking Lead Time = DATEDIFF(check_in, DATE(created_at))
    AVG(CASE WHEN b.status IN ('confirmed', 'completed')
        THEN CAST(DATEDIFF(b.check_in, DATE(b.created_at)) AS DOUBLE) END) AS avg_lead_time_days
  FROM silver_bookings b
  INNER JOIN silver_properties p ON b.property_id = p.property_id
  WHERE b.check_in IS NOT NULL
  GROUP BY
    DATE_TRUNC('MONTH', b.check_in),
    b.property_id,
    p.destination_id,
    p.destination_name,
    p.property_type
)
SELECT
  bm.booking_month,
  bm.property_id,
  bm.destination_id,
  bm.destination_name,
  bm.property_type,
  bm.booked_nights,
  -- Handbook 2.1: Available Nights = days_in_month (per property)
  DATEDIFF(LAST_DAY(bm.booking_month), bm.booking_month) + 1 AS available_nights,
  -- Handbook 2.1: Occupancy Rate = Booked Nights / Available Nights
  CASE
    WHEN DATEDIFF(LAST_DAY(bm.booking_month), bm.booking_month) + 1 > 0
    THEN bm.booked_nights / CAST(DATEDIFF(LAST_DAY(bm.booking_month), bm.booking_month) + 1 AS DOUBLE)
    ELSE NULL
  END AS occupancy_rate,
  bm.booking_count,
  bm.total_revenue,
  -- ADR = total_revenue / booked_nights
  CASE WHEN bm.booked_nights > 0 THEN bm.total_revenue / bm.booked_nights ELSE NULL END AS adr,
  bm.alos,
  bm.avg_lead_time_days
FROM booking_metrics bm;
