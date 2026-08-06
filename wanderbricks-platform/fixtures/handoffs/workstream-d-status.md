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
- Feature table(s) computing host and property quality signals:
  - Superhost score (composite of rating, booking count, cancellation rate, response rate)
  - Property quality score (review sentiment, occupancy, repeat guest rate)
- Feature engineering notebook
- Feature table resource YAML
- Tables populated and registered with Feature Store

## Validation Criteria
- Feature tables deploy and populate
- Superhost score correctly implements 4-criteria logic from Analytics Handbook
- Property quality score combines multiple signals
- No null feature values for entities with sufficient history
- Tables registered in Unity Catalog with proper comments

## File Isolation (this workstream touches ONLY)
- `src/features/` (feature engineering notebooks)
- `resources/wanderbricks_features.yml` (feature table resources)
