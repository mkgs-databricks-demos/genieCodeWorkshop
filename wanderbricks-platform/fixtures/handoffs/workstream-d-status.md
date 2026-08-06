---
status: COMPLETE
branch: mg-genie-wb-ws-d-features
started_at: 2026-08-06T18:00:00Z
completed_at: 2026-08-06T18:50:00Z
output_tables:
  - hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.feature_host_performance
  - hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.feature_property_quality
validation: PASSED
bundle_deployed: false
tests_passed: true
---

# Workstream D — Feature Tables

**Status:** COMPLETE

## Upstream Dependencies
- WS-A COMPLETE (silver/gold tables must be populated)

## What Was Built

### feature_host_performance (19,384 rows)
Primary Keys: host_id, computed_at. Features: avg_rating, total_completed_bookings, cancellation_rate, response_rate, is_superhost, superhost_score, total_revenue, avg_occupancy_rate, property_count. Superhost: strict 4-criteria AND per Analytics Handbook S4.1. Score: composite 0-1.

### feature_property_quality (18,163 rows)
Primary Keys: property_id, computed_at. Features: avg_rating, review_count, gss, occupancy_rate, avg_daily_rate, repeat_guest_rate, negative_review_rate, property_quality_score, booking_lead_time_avg, revenue_per_available_night. GSS: recency-weighted (30d=3.0, 90d=2.0, 365d=1.0, older=0.5).

### Job: wanderbricks_feature_computation
Two parallel tasks. Daily 6 AM Pacific. Deploy blocked by unrelated WS-B YAML error.

## Validation Results
- host: 19,384 rows, score [0.0, 0.60], 0 superhosts (correct for data)
- property: 18,163 rows, score [0.0, 0.57], no null violations

## Notes for Downstream Sessions
- FeatureLookup: lookup_key=host_id or property_id, timestamp_lookup_key=computed_at
- Key columns: superhost_score, property_quality_score, gss, is_superhost
- Data limitation: 0 superhosts (synthetic data doesn't produce 4-criteria intersection)

## File Isolation (this workstream touches ONLY)
- `src/features/` (feature engineering notebooks)
- `resources/wanderbricks_features.yml` (feature table resources)
