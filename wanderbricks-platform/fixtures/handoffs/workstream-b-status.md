---
status: NOT_STARTED
branch:
started_at:
completed_at:
output_tables: []
validation: PENDING
bundle_deployed: false
tests_passed: false
---

# Workstream B — Metric Views + Orchestration Job

**Status:** NOT_STARTED

## Upstream Dependencies
- WS-A COMPLETE (gold tables must be populated)

## Expected Output
- Metric views implementing definitions from the Analytics Handbook:
  - Revenue: GBV, Net Revenue, ADR
  - Occupancy: Occupancy Rate, ALOS, Booking Lead Time
  - Guest Satisfaction: GSS (with recency weighting), Review Response Rate
  - Host Performance: Superhost qualification
- Orchestration job to refresh pipeline + metric views on schedule
- All metric views queryable with correct results

## Validation Criteria
- Metric view definitions match Analytics Handbook exactly
- Metric views return non-null, non-zero results
- GBV calculation uses only status='confirmed' bookings
- Net Revenue = GBV × 0.15
- GSS uses recency weighting (30d=3.0, 90d=2.0, 365d=1.0, >365d=0.5)
- Orchestration job deploys and validates

## File Isolation (this workstream touches ONLY)
- `src/sql/` (metric view SQL definitions)
- `resources/wanderbricks_metrics.yml` (metric view resources)
- `resources/wanderbricks_orchestration.job.yml` (refresh job)
