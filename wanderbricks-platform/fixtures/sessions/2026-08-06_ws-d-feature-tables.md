# Session: WS-D Feature Tables

**Date:** 2026-08-06
**Branch:** mg-genie-wb-ws-d-features
**Duration:** ~50 minutes

## Summary

Created two feature tables using Databricks Feature Engineering client for host performance scoring and property quality scoring.

## Problems Encountered

1. **FeatureEngineeringClient requires timestamp_keys in primary_keys** - Initial attempt with `primary_keys=["host_id"]` and `timestamp_keys=["computed_at"]` failed. Fixed by including computed_at in primary_keys.

2. **Bundle deploy blocked by WS-B error** - `wanderbricks_orchestration.job.yml` references a SQL file as `sql_task.file.path` but it's actually a notebook. Not our workstream; noted as known issue.

3. **editAsset tool cannot modify .py files in git folder** - The workspace API doesn't find files created via createAsset in git-managed directories. Notebooks were created correctly on filesystem but couldn't be updated via editAsset afterward.

4. **0 qualifying superhosts** - Synthetic data doesn't produce any hosts meeting ALL 4 strict criteria simultaneously. This is correct behavior confirmed by gold_host_performance table (WS-A) showing same result.

## Root Causes

- Data sparsity: Only 1000 reviews total, 784 in 90-day window across 18,163 properties
- Response rate approximation: booking_updates timing doesn't reliably indicate 24h host response
- Cancellation attribution: No explicit host vs guest cancellation distinction in data
- Strict intersection: The 4 superhost criteria rarely overlap in this synthetic dataset

## Changes Made

| File | Action |
| --- | --- |
| `src/features/host_features.py` | Created - host performance feature computation |
| `src/features/property_features.py` | Created - property quality feature computation |
| `resources/wanderbricks_features.yml` | Created - job resource for scheduled computation |
| `fixtures/handoffs/workstream-d-status.md` | Updated to COMPLETE |

## Decisions

- Used MAX(created_at) from silver_bookings as reference date (not CURRENT_DATE) to ensure 90-day window captures actual data
- Superhost score weighted: 30% rating + 25% bookings + 20% low-cancel + 25% response
- Property quality score weighted: 30% GSS + 20% occupancy + 20% repeat guests + 15% low negatives + 15% ADR
- GSS follows Analytics Handbook exactly: recency weights 3.0/2.0/1.0/0.5
- Feature tables use composite PKs (entity_id + computed_at) for point-in-time lookup support

## Output Tables

- `hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.feature_host_performance` (19,384 rows)
- `hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.feature_property_quality` (18,163 rows)
