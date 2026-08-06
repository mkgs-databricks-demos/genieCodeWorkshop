---
status: IN_PROGRESS
branch: mg-genie-wb-ws-a-pipeline
started_at: 2026-08-07T14:00:00Z
completed_at:
output_tables: []
validation: N/A
bundle_deployed: N/A
tests_passed: N/A
---

# Workstream A — SDP Pipeline (Bronze → Silver → Gold)

**Status:** NOT_STARTED

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
- All tables in `hls_fde_dev.dev_matthew_giglia_wanderbricks_ai`

## What Was Built

A complete Spark Declarative Pipeline (SDP) with three layers:

**Bronze (16 streaming tables):** Raw ingestion from `samples.wanderbricks` with ingestion timestamps and PK not-null expectations. Tables: properties, bookings, reviews, users, hosts, destinations, payments, countries, amenities, property_amenities, property_images, booking_updates, page_views, employees, customer_support_logs, clickstream.

**Silver (16 materialized views):** Cleaned and conformed with deduplication, type casting, null handling, name standardization, and dimension joins. Key transforms: reviews filtered (is_deleted=false), bookings get duration_nights, destinations joined with countries, status fields lowered/trimmed.

**Gold (5 materialized views):** Business-ready aggregates following the Analytics Handbook:
- `gold_revenue_daily` — GBV, net revenue (15% commission), booking count by property/destination/date
- `gold_occupancy_monthly` — Occupancy rate, ADR, ALOS by property/destination/month
- `gold_guest_satisfaction` — Recency-weighted GSS (30d=3.0, 90d=2.0, 365d=1.0, >365d=0.5)
- `gold_host_performance` — Superhost qualification metrics (rating, bookings, cancellation rate)
- `gold_property_summary` — Denormalized property view with revenue, reviews, amenities, images

**Pipeline:** Serverless, ADVANCED edition, PREVIEW channel. Pipeline ID: `02069e0f-b913-4631-ae6c-a9447fb0b911`

## Validation Results

- Bronze bookings: 72,247 rows (matches source exactly)
- Silver bookings: 72,247 rows (no null PKs)
- Gold revenue_daily: 17,860 rows, GBV = $9.9M, Net Revenue = $1.49M
- Gold occupancy_monthly: 21,124 rows, 13,695 distinct properties
- Gold guest_satisfaction: 962 rows, avg GSS = 2.97 (range 1.0-5.0)
- Gold host_performance: 19,384 rows
- Gold property_summary: 18,163 rows

## Notes for Downstream Sessions

### For WS-B (Metric Views + Orchestration)

**Gold tables to expose as metric views:**
- `gold_revenue_daily` — Key columns: booking_date, property_id, destination_id, destination_name, gbv, net_revenue, booking_count, total_nights
- `gold_occupancy_monthly` — Key columns: month, property_id, destination_id, booked_nights, adr, alos, occupancy_rate
- `gold_guest_satisfaction` — Key columns: property_id, destination_id, host_id, gss, review_count, negative_review_rate
- `gold_host_performance` — Key columns: host_id, host_name, completed_bookings_90d, avg_rating_90d, cancellation_rate, qualifies_superhost
- `gold_property_summary` — Key columns: property_id, destination_name, property_type, base_price, total_gbv, total_bookings, avg_rating, amenity_count

**How to query:** Fully qualified names: `hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.<table_name>`

### For WS-D (Feature Tables)

**Silver tables for feature engineering:**
- `silver_bookings` — booking_id, property_id, user_id, duration_nights, total_amount, status, created_at
- `silver_reviews` — review_id, property_id, user_id, rating, comment, created_at
- `silver_properties` — property_id, host_id, destination_id, base_price, property_type, bedrooms, bathrooms
- `silver_clickstream` — user_id, property_id, event_type, device, referrer, event_timestamp
- `silver_page_views` — view_id, user_id, property_id, device_type, referrer, view_timestamp

### Pipeline Management

- Pipeline ID: `02069e0f-b913-4631-ae6c-a9447fb0b911`
- Pipeline name: `[dev matthew_giglia] wanderbricks_pipeline`
- Notebooks: `src/pipelines/{bronze,silver,gold}_pipeline`
- To refresh: `w.pipelines.start_update(pipeline_id=..., full_refresh=True)`

## File Isolation (this workstream touches ONLY)
- `src/pipelines/` (all pipeline notebooks)
- `fixtures/config/` (pipeline configuration)
- `resources/wanderbricks_pipeline.pipeline.yml`
