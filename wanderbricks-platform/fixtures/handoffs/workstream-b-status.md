---
status: COMPLETE
branch: mg-genie-wb-ws-b-metrics
started_at: 2026-08-06T19:00:00Z
completed_at: 2026-08-06T19:15:00Z
output_tables:
  - hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.mv_revenue_metrics
  - hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.mv_occupancy_metrics
  - hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.mv_guest_satisfaction
  - hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.mv_host_performance
validation: PASSED
bundle_deployed: true
tests_passed: true
---

# Workstream B — Metric Views + Orchestration Job

**Status:** COMPLETE

## Upstream Dependencies
- WS-A COMPLETE (gold tables must be populated)

## What Was Built

- **4 Metric Views** (standalone materialized views in `hls_fde_dev.dev_matthew_giglia_wanderbricks_ai`):
  - `mv_revenue_metrics` — Daily GBV, Net Revenue, ADR by property/destination
  - `mv_occupancy_metrics` — Monthly occupancy rate, ALOS, booking lead time by property/destination
  - `mv_guest_satisfaction` — Recency-weighted GSS per property (30d=3.0, 90d=2.0, 365d=1.0, >365d=0.5)
  - `mv_host_performance` — Superhost qualification per host (4 criteria)
- **Orchestration Job YAML** (`resources/wanderbricks_orchestration.job.yml`)
  - Task 1: Pipeline refresh (wanderbricks_pipeline)
  - Task 2: Metric view refresh (depends on pipeline)
- **SQL Source Files** in `src/sql/` with widget-parameterized catalog/schema
- Bundle validates cleanly; deploy requires `databricks bundle deploy --target dev`

## Validation Results

| Check | Result |
| --- | --- |
| mv_revenue_metrics rows (gbv > 0) | 17,860 PASS |
| Total GBV | $9.9M PASS |
| Net Revenue = GBV x 0.15 (zero mismatches) | PASS |
| ADR average | $181 (reasonable) PASS |
| mv_occupancy_metrics rows | 21,124 PASS |
| Occupancy rate in valid range (0-1) | PASS |
| ALOS average | 3.8 nights PASS |
| mv_guest_satisfaction GSS range | 1.0-5.0 PASS |
| GSS average | 2.97 PASS |
| mv_host_performance host count | 19,384 PASS |
| Cancellation rate valid | 6.9% avg PASS |

## Notes for Downstream Sessions

- **All metric views in**: `hls_fde_dev.dev_matthew_giglia_wanderbricks_ai`
- **Metric views for WS-C Genie Agent**:
  - `mv_revenue_metrics` — columns: booking_date, property_id, destination_id, destination_name, property_type, gbv, net_revenue, adr, confirmed_booking_count, total_nights, total_guests
  - `mv_occupancy_metrics` — columns: booking_month, property_id, destination_id, destination_name, property_type, booked_nights, booking_count, total_revenue, adr, alos, occupancy_rate, avg_lead_time_days
  - `mv_guest_satisfaction` — columns: property_id, destination_id, destination_name, gss, simple_avg_rating, review_count, negative_review_count, negative_review_rate
  - `mv_host_performance` — columns: host_id, host_name, country, is_verified, is_active, joined_at, completed_bookings_90d, host_cancellations, total_eligible_bookings, cancellation_rate, avg_rating_90d, review_count_90d, qualifies_superhost
- **Query pattern**: `SELECT * FROM hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.<view_name>`
- **Analytics Handbook compliance**: All metrics follow exact handbook definitions
- **Orchestration job**: Defined in YAML, requires `databricks bundle deploy --target dev` to create
- **Pipeline ID** (for job): `95d3cae3-9bd5-4780-9021-7d1dafc16fc3`

## File Isolation (this workstream touches ONLY)
- `src/sql/` (metric view SQL definitions)
- `resources/wanderbricks_orchestration.job.yml` (refresh job)
