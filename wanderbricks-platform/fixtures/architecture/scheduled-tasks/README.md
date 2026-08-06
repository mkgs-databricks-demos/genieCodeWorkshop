# Scheduled Task Orchestration — WanderBricks Platform

## Overview

Five Genie Code workstreams execute the WanderBricks Platform build in dependency
order, coordinated via the `fixtures/handoffs/` status file protocol.

WS-0 is already complete (bundle scaffold). The remaining four are created as
paused scheduled tasks, then unpaused in sequence. WS-A starts immediately;
WS-B and WS-D auto-start when WS-A completes (parallel); WS-C waits for WS-B.

## Task Summary

| Task | Title | Cron | Gates On | Source Directory |
| --- | --- | --- | --- | --- |
| WS-0 | WanderBricks WS-0 Scaffold | N/A (complete) | None | `resources/`, `src/notebooks/` |
| WS-A | WanderBricks WS-A Pipeline | `0 */15 * * * ?` | WS-0 COMPLETE | `src/pipelines/`, `fixtures/config/` |
| WS-B | WanderBricks WS-B Metrics | `0 */15 * * * ?` | WS-A COMPLETE | `src/sql/`, `resources/wanderbricks_metrics.*` |
| WS-C | WanderBricks WS-C Genie Agent | `0 */15 * * * ?` | WS-B COMPLETE | `resources/wanderbricks_genie_space.*` |
| WS-D | WanderBricks WS-D Features | `0 */15 * * * ?` | WS-A COMPLETE | `src/features/`, `resources/wanderbricks_features.*` |

## Execution Flow

```
T+0:       WS-A unpaused. Reads WS-0 = COMPLETE → starts work (~45-60 min)
           WS-B, WS-D: Read WS-A = NOT_STARTED → exit
           WS-C: Read WS-B = NOT_STARTED → exit

T+~1 hr:   WS-A completes, writes COMPLETE

T+next 15: WS-B reads WS-A = COMPLETE → starts work (~30 min)
           WS-D reads WS-A = COMPLETE → starts work (~30 min) [PARALLEL]
           WS-C reads WS-B = NOT_STARTED → exit

T+~1.5 hr: WS-B and WS-D complete (roughly same time)

T+next 15: WS-C reads WS-B = COMPLETE → starts work (~15 min)

T+~2 hr:   All five status files show COMPLETE.
           Operator pauses all scheduled tasks.
```

## Naming Conventions

- **Task titles:** `WanderBricks WS-{X} {Description}`
- **Branches:** `mg-genie-wb-ws-{x}-{description}`
- **Status files:** `workstream-{x}-status.md`
- **Prompt files:** `ws-{x}-{description}-prompt.md`

## Prompt Files

- `ws-0-bundle-scaffold-prompt.md` — Retrospective (WS-0 already complete)
- `ws-a-pipeline-prompt.md` — Full SDP pipeline (bronze→silver→gold)
- `ws-b-metrics-prompt.md` — Metric views + orchestration job
- `ws-c-genie-agent-prompt.md` — Genie space over gold layer
- `ws-d-features-prompt.md` — Feature tables (superhost, property quality)

## Key Design Decisions

1. **WS-0 as retrospective** — Documents what WOULD have been the scheduled task
   prompt for the already-completed scaffold. Teaches the full pattern from step 0.

2. **Parallel fan-out after WS-A** — WS-B (metrics) and WS-D (features) both gate
   only on WS-A, so they run concurrently. Different source directories = no conflicts.

3. **Table-gated, not code-gated** — Gate checks verify OUTPUT TABLES are populated
   (via SQL COUNT), not that code is merged. Decouples execution from PR review.

4. **Bundle deploy as validation** — Every workstream must `databricks bundle deploy`
   and fix errors before marking COMPLETE. This catches resource reference issues early.

5. **Independent branches** — Each workstream creates its own feature branch off
   `lesson/02-vibe-infra`. They touch isolated directories, so no merge conflicts.
   Merge order: 0 → A → B + D (parallel) → C.

## After Completion

1. Pause all scheduled tasks
2. Review each feature branch and create PRs
3. Merge in order: A → B + D → C (into `lesson/02-vibe-infra`)
4. Deploy full bundle to confirm complete resource DAG
5. This state becomes the `lesson/03-vibe-ai` branch cut point
6. Begin Vibe Session 2 workstreams (Vector Search)
