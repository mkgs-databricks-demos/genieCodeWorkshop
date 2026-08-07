---
status: IN_PROGRESS
branch: mg-genie-wb-ws-c-genie-agent
started_at: 2026-08-07T00:00:00Z
completed_at:
output_tables: []
validation: PENDING
bundle_deployed: false
tests_passed: false
---

# Workstream C — Genie Agent (Space)

**Status:** IN_PROGRESS

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

## What Was Built

### Genie AI/BI Space: "WanderBricks Analytics Agent"
- **Space ID:** `01f1921c721613cf8ef3c491a47a5eef`
- **URL:** https://fevm-hls-fde.cloud.databricks.com/genie/rooms/01f1921c721613cf8ef3c491a47a5eef
- **Data Sources (6 tables/views):**
  - `mv_revenue_metrics` — daily GBV, net revenue, ADR by property/destination
  - `mv_occupancy_metrics` — monthly occupancy rate, ALOS, lead time
  - `mv_guest_satisfaction` — recency-weighted GSS per property
  - `mv_host_performance` — trailing-90d superhost qualification signals
  - `feature_host_performance` — enriched host data with superhost_score
  - `feature_property_quality` — per-property quality metrics and tier
- **Sample Questions (8):** Revenue by destination, occupancy trends, GSS distribution, Superhost count, ADR by property type, quality tier analysis, cross-property-type revenue, lead time by destination
- **Instructions:** Business context from Analytics Handbook covering all metric definitions, calculation rules, join guidance

### Files Created
- `resources/wanderbricks_genie_space.yml` — Bundle resource definition
- `wanderbricks_genie.geniespace.json` — Serialized space config (data sources, instructions, sample questions)
- `databricks.yml` — Added `engine: direct` (required for genie_spaces)

### Validation
- Bundle validate: PASSED
- Bundle deploy: PASSED
- Query test (GBV by destination): PASSED — correct SQL generated, results returned
- Query test (Superhost qualification): PASSED — multi-query deep research with criteria breakdown

## Notes for Downstream Sessions

This is the terminal workstream before FINAL orchestration. No downstream sessions depend on WS-C output.

## File Isolation (this workstream touches ONLY)
- `resources/wanderbricks_genie_space.yml`
- `wanderbricks_genie.geniespace.json`
- `databricks.yml` (added `engine: direct`)
