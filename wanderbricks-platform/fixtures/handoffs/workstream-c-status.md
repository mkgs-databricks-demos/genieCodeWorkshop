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

# Workstream C — Genie Agent (Space)

**Status:** NOT_STARTED

## Upstream Dependencies
- WS-B COMPLETE (metric views must be queryable)

## Expected Output
- Genie space resource configured with:
  - All gold tables and metric views as data sources
  - Business context instructions (from Analytics Handbook definitions)
  - Sample questions demonstrating each metric
- Genie space deployed and functional

## Validation Criteria
- Genie space deploys successfully
- At least 5 tables/views registered as data sources
- Instructions reference correct metric definitions
- Sample questions cover revenue, occupancy, satisfaction, and host metrics

## File Isolation (this workstream touches ONLY)
- `resources/wanderbricks_genie_space.yml`
