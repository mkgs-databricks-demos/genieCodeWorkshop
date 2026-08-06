# Workstream Handoffs — Inter-Session Communication Protocol

## Purpose

This folder enables asynchronous coordination between Genie Code scheduled task
sessions executing the WanderBricks Platform workstreams (0, A, B, C, D).

Each session reads its upstream status file as a gate check before starting work,
and writes its own status file upon completion.

## Protocol

### Status File Contract

Each file uses YAML frontmatter for machine-parseable status, followed by
human-readable notes for downstream sessions:

```markdown
---
status: NOT_STARTED | IN_PROGRESS | COMPLETE | BLOCKED
branch: mg-genie-wb-ws-{x}-{description}
started_at: ISO8601 timestamp (set when IN_PROGRESS)
completed_at: ISO8601 timestamp (set when COMPLETE)
output_tables: list of fully qualified table/resource names
validation: PASSED | FAILED | PENDING
bundle_deployed: true | false
tests_passed: true | false | N/A
---

# Workstream {X} — {Title}

## What Was Built
...

## Notes for Downstream Sessions
...

## Validation Results
...

## Next Steps (for human)
...
```

### Gate Check Logic (each session run)

```
1. Read OWN status file
   → If status == COMPLETE: exit immediately (already done)

2. Read UPSTREAM status file(s)
   → If ANY upstream status != COMPLETE: write own status as "NOT_STARTED", exit

3. All upstreams COMPLETE → proceed with work
   → Write own status as IN_PROGRESS
   → Do the work
   → Validate output (deploy bundle, run pipelines/jobs)
   → Write own status as COMPLETE with metadata
```

### Dependency Graph

```
WS-0 (Bundle Scaffold) [COMPLETE]
    → WS-A (SDP Pipeline: bronze→silver→gold)
        ├→ WS-B (Metric Views + Orchestration Job) [gates on WS-A]
        │       → WS-C (Genie Agent) [gates on WS-B]
        └→ WS-D (Feature Tables) [gates on WS-A, parallel with WS-B]
```

- **WS-0** has no upstream dependency — creates the bundle foundation (ALREADY COMPLETE)
- **WS-A** gates on WS-0 (schema must be deployed)
- **WS-B** gates on WS-A (gold tables must be populated)
- **WS-C** gates on WS-B (metric views must be queryable)
- **WS-D** gates on WS-A (silver/gold tables must exist) — runs parallel with WS-B

### Branch Strategy

Each workstream creates its own feature branch off `lesson/02-vibe-infra`:
- They operate on **different source directories** (no merge conflicts)
- The gate check verifies **output tables** exist and are populated
- Code merging happens after human review (PR per branch)

| Workstream | Branch | Source Directory | Output |
| --- | --- | --- | --- |
| 0 | `mg-genie-L02-wanderbricks-scaffold` | `resources/`, `src/notebooks/` | Schema + Volumes + Lakebase deployed |
| A | `mg-genie-wb-ws-a-pipeline` | `src/pipelines/`, `fixtures/config/`, `resources/wanderbricks_pipeline.*` | Gold tables populated |
| B | `mg-genie-wb-ws-b-metrics` | `src/sql/`, `resources/wanderbricks_metrics.*`, `resources/wanderbricks_orchestration.*` | Metric views queryable |
| C | `mg-genie-wb-ws-c-genie-agent` | `resources/wanderbricks_genie_space.*` | Genie space functional |
| D | `mg-genie-wb-ws-d-features` | `src/features/`, `resources/wanderbricks_features.*` | Feature tables populated |

### Self-Termination

Scheduled tasks poll every 15 minutes. Once a session writes COMPLETE to its own
status file, subsequent runs exit immediately on step 1 (idempotent). The human
operator pauses or deletes the scheduled tasks once all workstreams show COMPLETE.

### Bundle Deployment & Testing

Every workstream session MUST:
1. Deploy the bundle to dev: `databricks bundle deploy --target dev`
2. Fix any validation/deployment errors before marking COMPLETE
3. Run any net-new pipelines, jobs, or notebooks created in that session
4. Verify outputs via SQL validation queries
5. Only then write COMPLETE status

## Files

| File | Written By | Read By |
| --- | --- | --- |
| `workstream-0-status.md` | WS-0 session | WS-A session |
| `workstream-a-status.md` | WS-A session | WS-B, WS-D sessions |
| `workstream-b-status.md` | WS-B session | WS-C session |
| `workstream-c-status.md` | WS-C session | Human (final status) |
| `workstream-d-status.md` | WS-D session | Human (final status) |
