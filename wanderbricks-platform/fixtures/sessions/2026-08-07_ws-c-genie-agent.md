# Session: WS-C Genie Agent (Space)

**Date:** 2026-08-07
**Workstream:** C — Genie AI/BI Space
**Branch:** mg-genie-wb-ws-c-genie-agent
**Duration:** ~15 minutes

## Problem

Create a Genie AI/BI space over the gold/metric layer so business users can ask natural language questions about WanderBricks analytics.

## Root Cause / Context

- WS-B metric views were populated (69K+ rows in mv_revenue_metrics) despite the WS-B status file still showing NOT_STARTED
- Genie space API has strict serialization requirements: tables sorted by identifier, column_configs sorted by column_name, text_instructions limited to 1 item, all IDs must be 32-hex UUIDs without hyphens
- The `engine: direct` setting is required in databricks.yml for genie_spaces resource type

## Changes Made

| File | Change |
| --- | --- |
| `databricks.yml` | Added `engine: direct` under `bundle:` |
| `resources/wanderbricks_genie_space.yml` | New — Genie space resource definition |
| `wanderbricks_genie.geniespace.json` | New — Serialized space config (6 tables, 8 questions, 7 instruction sections consolidated into 1) |
| `fixtures/handoffs/workstream-c-status.md` | Updated to COMPLETE |

## Decisions

1. **Tables included:** All 4 metric views (mv_*) + 2 feature tables (feature_*) = 6 data sources. Gold tables from the SDP pipeline are not directly queryable outside the pipeline context.
2. **Instructions format:** Consolidated all business context into a single text_instruction entry (API limit: max 1 item). Content array preserves logical sections.
3. **Sample questions:** 8 questions covering all 4 metric domains (revenue, occupancy, satisfaction, host performance) plus cross-cutting analysis.
4. **Hardcoded identifiers:** Table identifiers use the full `hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.*` path since the .geniespace.json doesn't support bundle variable substitution.

## Validation Results

- Bundle validate: PASSED
- Bundle deploy: PASSED
- GBV by destination query: PASSED (correct SQL, 5 results returned)
- Superhost qualification query: PASSED (multi-query deep research, correct criteria application)

## Files Modified

- `databricks.yml`
- `resources/wanderbricks_genie_space.yml` (new)
- `wanderbricks_genie.geniespace.json` (new)
- `fixtures/handoffs/workstream-c-status.md`
- `fixtures/sessions/2026-08-07_ws-c-genie-agent.md` (this file)
