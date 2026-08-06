# Scheduled Task Orchestration — WanderBricks Platform

## Overview

Six Genie Code workstreams execute the WanderBricks Platform build in dependency
order, coordinated via status files and the Hub-Lite execution pattern.

WS-0 is already complete (bundle scaffold). WS-A through WS-D build the platform.
WS-FINAL summarizes all work and provides merge instructions.

## Architecture: Hub-Lite + PR-on-Complete

All workstreams execute in the **bundle root** — the single source of truth during
a session. Git push happens once at the end as a one-way sync to a push clone.

```
/Workspace/Users/matthew.giglia@databricks.com/genieCodeWorkshop/
├── wanderbricks-platform/                  ← BUNDLE ROOT (all work here)
│   ├── databricks.yml
│   ├── resources/                          ← Resource YAMLs (editAsset)
│   ├── src/                                ← Code files (editAsset)
│   ├── fixtures/
│   │   ├── handoffs/                       ← Status files (editAsset)
│   │   └── architecture/scheduled-tasks/   ← This directory
│   └── docs/
│
└── .git-push-clone/                        ← PUSH CLONE (one-way git sync, end-of-session)
    └── genieCodeWorkshop/                  ← Full repo checkout
```

**Rules:**
- ALL code work happens in the bundle root via `editAsset`/`createAsset`
- ALL deploys use `runDatabricksCli` (`bundle validate/deploy/run`) in the bundle root
- Status files are read/written via `editAsset` (immediate, no git needed)
- NO `runGit` operations during execution — only at session end for archival
- Git sync is ONE-WAY: bundle root → push clone → GitHub. Never read from the clone.

## Conflict Safety

Workstreams don't conflict because:

1. **Gate checks serialize execution** — B waits for A, C waits for B, etc.
2. **File scope isolation** — Each workstream owns specific directories (no overlap)
3. **Self-pause** — Each fires exactly once via SINGLE-FIRE GUARD
4. **Bundle deploy is additive** — Adding resource B doesn't remove resource A
5. **No git during execution** — Zero branch operations = zero race conditions

## Branch Stacking (Git Sync)

At session end, each workstream pushes its code to a branch stacked on its upstream:

```
mg-genie-L02-wanderbricks-scaffold (base)
    └→ mg-genie-wb-ws-a-pipeline (WS-A's pipeline code)
        ├→ mg-genie-wb-ws-b-metrics (WS-B's metric views)
        │       └→ mg-genie-wb-ws-c-genie-agent (WS-C's genie space)
        └→ mg-genie-wb-ws-d-features (WS-D's feature tables)
```

This means:
- WS-B inherits WS-A's code naturally (it's already in the bundle root)
- WS-C inherits A + B's code
- WS-D inherits A's code (parallel with B, no conflict)

## Task Summary

| Task | Title | Cron | Gates On | File Scope | Git Branch |
| --- | --- | --- | --- | --- | --- |
| WS-0 | WanderBricks WS-0 Scaffold | N/A (complete) | None | Bundle scaffold | `mg-genie-L02-wanderbricks-scaffold` |
| WS-A | WanderBricks WS-A Pipeline | `0 */3 * * * ?` | WS-0 COMPLETE | `src/pipelines/`, `resources/wanderbricks_pipeline.pipeline.yml` | `mg-genie-wb-ws-a-pipeline` |
| WS-B | WanderBricks WS-B Metrics | `0 */15 * * * ?` | WS-A COMPLETE | `src/sql/`, `resources/wanderbricks_metrics.*` | `mg-genie-wb-ws-b-metrics` |
| WS-C | WanderBricks WS-C Genie Agent | `0 */15 * * * ?` | WS-B COMPLETE | `resources/wanderbricks_genie.*` | `mg-genie-wb-ws-c-genie-agent` |
| WS-D | WanderBricks WS-D Features | `0 */15 * * * ?` | WS-A COMPLETE | `src/features/`, `resources/wanderbricks_features.*` | `mg-genie-wb-ws-d-features` |
| WS-FINAL | WanderBricks WS-FINAL Summary | `0 */15 * * * ?` | ALL COMPLETE | `fixtures/sessions/` (summary only) | N/A |

## Execution Flow

```
T+0:       All tasks created. WS-A fires within 3 min.
           WS-A: Gate passes → self-pauses → builds pipeline in bundle root (~45-60 min)
           WS-B, WS-D, WS-C, WS-FINAL: Gate check fails → exit (<10s)

T+~1 hr:   WS-A completes. Git sync (one-way push). Writes COMPLETE to status file.

T+next 15: WS-B: Gate passes → self-pauses → builds metric views in bundle root (~30 min)
           WS-D: Gate passes → self-pauses → builds feature tables in bundle root (~30 min)
           [PARALLEL — non-overlapping file scopes, additive deploys]
           WS-C, WS-FINAL: Gate check fails → exit

T+~1.5 hr: WS-B and WS-D complete (roughly same time). Git sync. Write COMPLETE.

T+next 15: WS-C: Gate passes → self-pauses → builds genie space in bundle root (~15 min)
           WS-FINAL: Gate check fails (WS-C not done) → exit

T+~2 hr:   WS-C completes. Git sync. Writes COMPLETE.

T+next 15: WS-FINAL: All gates pass → writes summary, PR descriptions, merge instructions.
```

## Naming Conventions

- **Task titles:** `WanderBricks WS-{X} {Description}`
- **Branches:** `mg-genie-wb-ws-{x}-{description}`
- **Status files:** `workstream-{x}-status.md` (in bundle root `fixtures/handoffs/`)
- **Prompt files:** `ws-{x}-{description}-prompt.md`
- **Push clone:** `/Workspace/Users/<username>/genie-code-workstream-orchestration/<project>/push-clone/`

## Prompt Files

- `ws-0-bundle-scaffold-prompt.md` — Retrospective (WS-0 already complete)
- `ws-a-pipeline-prompt.md` — Full SDP pipeline (bronze→silver→gold)
- `ws-b-metrics-prompt.md` — Metric views + orchestration job
- `ws-c-genie-agent-prompt.md` — Genie space over gold layer
- `ws-d-features-prompt.md` — Feature tables (superhost, property quality)
- `ws-final-summary-prompt.md` — Summary + PR instructions for human

## Key Design Decisions

1. **Hub-Lite pattern** — All work happens in the bundle root. No separate clones
   during execution. This eliminates drift between "where editAsset works" and
   "where bundle CLI runs." Git is just an archival step at the end.

2. **One-way git sync** — At session end, changed files are copied bundle root →
   push clone → commit + push. The push clone is write-only (never read from).
   This decouples execution from version control entirely.

3. **Branch stacking via git sync** — Each workstream's push checks out its upstream's
   branch, then adds its own files. Downstream inherits upstream code naturally
   (it's already in the bundle root from prior workstream runs).

4. **SINGLE-FIRE GUARD** — Every workstream self-pauses its cron immediately on start.
   Combined with IN_PROGRESS status gate, prevents duplicate execution.

5. **File scope isolation** — Each workstream declares which paths it owns.
   No workstream modifies another's files. Combined with gate serialization,
   this makes concurrent execution safe without locking.

6. **WS-FINAL as merge guide** — The final workstream gates on ALL others, then
   produces a complete summary with PR titles, descriptions, merge order, and
   post-merge validation steps. The human reviews and executes the merge plan.

7. **Fast-start first workstream** — The first workstream (no upstream dependency)
   polls every 3 minutes (`0 */3 * * * ?`). All others poll every 15 minutes.
   Users see progress within minutes; downstream tasks don't waste resources.

8. **Table-gated deploys** — Gate checks verify OUTPUT TABLES via SQL COUNT
   (decouples from PR review). Downstream workstreams confirm upstream's tables
   exist before starting their own work.

9. **Bundle-First Rule** — ALL infrastructure goes through `databricks bundle deploy`.
   No hardcoded catalogs/schemas. Variables and resource references only.

## Merge Plan (produced by WS-FINAL)

The branch stack means PRs merge cleanly in this order:

```
1. mg-genie-wb-ws-a-pipeline      → mg-genie-L02-wanderbricks-scaffold  (A's pipeline code)
2. mg-genie-wb-ws-b-metrics       → mg-genie-L02-wanderbricks-scaffold  (B's metric views)
3. mg-genie-wb-ws-d-features      → mg-genie-L02-wanderbricks-scaffold  (D's feature tables)
4. mg-genie-wb-ws-c-genie-agent   → mg-genie-L02-wanderbricks-scaffold  (C's genie space)
```

Each PR shows ONLY that workstream's delta because the upstream is already
in the target branch by merge time.

## After All Merges

1. Delete push clone (`genie-code-workstream-orchestration/` tree)
2. Pause/delete all scheduled tasks
3. Deploy full bundle from `mg-genie-L02-wanderbricks-scaffold` to confirm complete resource DAG
4. Merge scaffold → `lesson/02-vibe-infra`, then cut `lesson/03-vibe-ai` from that state
5. Begin Vibe Session 2 workstreams (Vector Search)
