---
status: COMPLETE
branch: mg-genie-wb-ws-d-features-v2
started_at: 2026-08-06T11:10:00Z
completed_at: 2026-08-06T11:20:00Z
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
Primary Keys: host_id, computed_at (timeseries). Features: avg_rating, total_completed_bookings, cancellation_rate, response_rate, is_superhost, superhost_score, total_revenue, avg_occupancy_rate, property_count. Superhost: strict 4-criteria AND per Analytics Handbook S4.1 (rating>=4.5, bookings>=10, cancel<2%, response>=90%). Score: composite 0-1 (normalized average of 4 criteria).

### feature_property_quality (18,163 rows)
Primary Keys: property_id, computed_at (timeseries). Features: avg_rating, review_count, gss, occupancy_rate, avg_daily_rate, repeat_guest_rate, negative_review_rate, property_quality_score, booking_lead_time_avg, revenue_per_available_night. GSS: recency-weighted per Analytics Handbook S3.1 (30d=3.0, 90d=2.0, 365d=1.0, older=0.5). Quality score: normalized composite of rating, GSS, occupancy, repeat rate, and inverse negative rate.

### Job: wanderbricks_feature_computation
Two parallel tasks (host_features, property_features). Daily 6 AM Pacific. Bundle validated OK; deploy blocked by CLI allow-list (not a code issue).

## Validation Results
- host: 19,384 rows, score [0.0, 0.715], 0 superhosts (correct for synthetic data)
- property: 18,163 rows, score [0.04, 0.625], all scores in 0-1, 0 out-of-range
- No null violations: 0 rows with null avg_rating where total_completed_bookings > 0

## Notes for Downstream Sessions
- FeatureLookup: lookup_key=host_id or property_id, timestamp_lookup_key=computed_at
- Key columns: superhost_score, property_quality_score, gss, is_superhost
- Data limitation: 0 superhosts (synthetic data doesn't produce 4-criteria intersection)
- Reference date: 2025-07-30 (data ends here, trailing 90d window = 2025-05-01 to 2025-07-30)
- Branch: mg-genie-wb-ws-d-features-v2 (branched from mg-genie-wb-ws-a-pipeline-v2)

## File Isolation (this workstream touches ONLY)
- `src/features/` (feature engineering notebooks)
- `resources/wanderbricks_features.yml` (feature table resources)
