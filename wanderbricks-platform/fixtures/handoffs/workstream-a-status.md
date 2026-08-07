---
status: COMPLETE
branch: mg-genie-wb-ws-a-pipeline
started_at: 2026-08-06T00:00:00Z
completed_at: 2026-08-06T18:30:00Z
output_tables:
  - hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.bronze_bookings
  - hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.bronze_properties
  - hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.bronze_reviews
  - hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.bronze_users
  - hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.bronze_hosts
  - hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.bronze_destinations
  - hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.bronze_payments
  - hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.bronze_countries
  - hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.bronze_amenities
  - hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.bronze_property_amenities
  - hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.bronze_property_images
  - hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.bronze_booking_updates
  - hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.bronze_customer_support_logs
  - hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.bronze_clickstream
  - hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.bronze_page_views
  - hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.bronze_employees
  - hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.silver_bookings
  - hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.silver_properties
  - hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.silver_reviews
  - hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.silver_users
  - hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.silver_hosts
  - hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.silver_payments
  - hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.silver_destinations
  - hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.silver_countries
  - hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.silver_amenities
  - hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.silver_property_amenities
  - hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.silver_property_images
  - hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.gold_revenue_daily
  - hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.gold_occupancy_monthly
  - hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.gold_guest_satisfaction
  - hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.gold_host_performance
  - hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.gold_property_summary
validation: PASSED
bundle_deployed: true
tests_passed: true
---

# Workstream A — SDP Pipeline (Bronze → Silver → Gold)

**Status:** COMPLETE

## Upstream Dependencies
- WS-0 COMPLETE (schema must be deployed)

## Expected Output
- Full Spark Declarative Pipeline with bronze, silver, and gold layers
- Bronze: streaming tables ingesting from `samples.wanderbricks`
- Silver: cleaned/conformed tables (deduped, typed, null-handled)
- Gold: business-ready aggregates (revenue, occupancy, satisfaction)
- Pipeline resource YAML in `resources/`
- All tables populated and queryable

## Validation Criteria
- Pipeline deploys without errors
- Pipeline runs successfully (full refresh)
- Bronze tables: row counts match source (`samples.wanderbricks.*`)
- Silver tables: no nulls in PK columns, correct types
- Gold tables: at least 3 aggregate tables (revenue, occupancy, satisfaction)
- All tables in target schema

## What Was Built

- Full Spark Declarative Pipeline (pipeline ID: `95d3cae3-9bd5-4780-9021-7d1dafc16fc3`)
- **Bronze layer** (16 streaming tables): Raw ingestion from all `samples.wanderbricks` tables with ingestion timestamps and PK not-null expectations
- **Silver layer** (11 materialized views): Deduplication, type casting, null handling, dimension joins (properties+destinations), duration calculations, status standardization
- **Gold layer** (5 materialized views): Revenue daily (GBV/net revenue), occupancy monthly (ADR/ALOS), guest satisfaction (recency-weighted GSS), host performance (superhost qualification), property summary (denormalized)
- Pipeline resource YAML, bronze.py, silver.py, gold.py source notebooks created
- All tables in schema: `hls_fde_dev.dev_matthew_giglia_wanderbricks_ai`

## Validation Results

| Check | Result |
| --- | --- |
| Bronze bookings count matches source | 72,247 = 72,247 PASS |
| Silver bookings (no dup inflation) | 72,247 PASS |
| Gold revenue daily has rows + positive GBV | 17,860 rows, $9.9M GBV PASS |
| Gold occupancy covers properties | 13,695 distinct properties PASS |
| GSS average in valid range (1-5) | 2.97 PASS |
| Gold host performance populated | 19,384 rows PASS |
| Gold property summary populated | 18,163 rows PASS |

## Notes for Downstream Sessions

- **All tables in**: `hls_fde_dev.dev_matthew_giglia_wanderbricks_ai`
- **Gold tables for WS-B metric views**:
  - `gold_revenue_daily` — columns: booking_date, property_id, destination_id, destination_name, property_type, gbv, net_revenue, booking_count, total_nights, total_guests
  - `gold_occupancy_monthly` — columns: booking_month, property_id, destination_id, destination_name, property_type, booked_nights, booking_count, total_revenue, adr, alos, occupancy_rate
  - `gold_guest_satisfaction` — columns: property_id, destination_id, destination_name, gss, review_count, simple_avg_rating, negative_review_count, negative_review_rate
  - `gold_host_performance` — columns: host_id, host_name, country, is_verified, is_active, completed_bookings, host_cancellations, total_bookings, cancellation_rate, avg_rating_90d, review_count_90d, qualifies_superhost
  - `gold_property_summary` — columns: property_id, host_id, destination_id, destination_name, title, property_type, base_price, max_guests, bedrooms, bathrooms, latitude, longitude, listed_at, total_revenue, total_bookings, total_booked_nights, avg_stay_length, avg_rating, review_count, image_count, amenity_count
- **Silver tables for WS-D feature engineering**:
  - `silver_bookings` (booking_id, user_id, property_id, check_in, check_out, duration_nights, guests_count, total_amount, status, created_at, updated_at)
  - `silver_properties` (property_id, host_id, destination_id, destination_name, destination_country, title, base_price, property_type, max_guests, bedrooms, bathrooms, latitude, longitude, listed_at)
  - `silver_reviews` (review_id, booking_id, property_id, user_id, rating, review_text, is_deleted, reviewed_at, updated_at)
  - `silver_hosts` (host_id, host_name, is_verified, is_active, host_rating, country, joined_at)
- **Pipeline ID**: `95d3cae3-9bd5-4780-9021-7d1dafc16fc3` (serverless, photon)
- **Query pattern**: `SELECT * FROM hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.<table_name>`
- **Analytics Handbook compliance**: All gold metrics follow exact handbook definitions (GBV=confirmed only, Net Revenue=15% commission, GSS=recency-weighted, Superhost=4 criteria)

## File Isolation (this workstream touches ONLY)
- `src/pipelines/` (all pipeline notebooks)
- `fixtures/config/` (pipeline configuration)
- `resources/wanderbricks_pipeline.pipeline.yml`
