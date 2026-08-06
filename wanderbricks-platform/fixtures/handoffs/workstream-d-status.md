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

# Workstream D — Feature Tables

**Status:** NOT_STARTED

## Upstream Dependencies
- WS-A COMPLETE (silver/gold tables must be populated)

## Expected Output
- Feature tables for host performance and property quality
- Feature computation job (daily schedule)
- Feature tables queryable with correct values

## Validation Criteria
- Feature tables populated with correct row counts
- Scores in valid ranges (0-1)
- No null violations in key columns
- Job deploys and validates

## File Isolation (this workstream touches ONLY)
- `src/features/` (feature engineering notebooks)
- `resources/wanderbricks_features.yml` (feature table resources)
