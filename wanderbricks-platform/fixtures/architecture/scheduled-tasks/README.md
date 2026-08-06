# Scheduled Task Orchestration — WanderBricks Platform

## Overview

Six Genie Code workstreams execute the WanderBricks Platform build in dependency
order, coordinated via status files and isolated git folder clones.

WS-0 is already complete (bundle scaffold). WS-A through WS-D build the platform.
WS-FINAL summarizes all work and provides merge instructions.

Each workstream runs in its **own git folder clone**, enabling true parallel execution
with branch stacking (downstream workstreams branch from their upstream's pushed branch).

## Clone Structure

```
~/genie-code-workstream-orchestration/
└── genieCodeWorkshop/                    ← project-level grouping
    ├── a-pipeline/                       ← WS-A clone (branch: mg-genie-wb-ws-a-pipeline)
    ├── b-metrics/                        ← WS-B clone (branch: mg-genie-wb-ws-b-metrics)
    ├── c-genie-agent/                    ← WS-C clone (branch: mg-genie-wb-ws-c-genie-agent)
    └── d-features/                       ← WS-D clone (branch: mg-genie-wb-ws-d-features)

~/genieCodeWorkshop/                      ← orchestration hub (status files, architecture docs)
                                            stays on scaffold branch, shared read/write for status
```

**Rules:**
- Each workstream clones to its own path as part of its first run (idempotent)
- Status files are ALWAYS read/written in the **orchestration hub** (main project folder)
- Code is written in the workstream's **own clone**
- Clones are disposable — delete the entire `genie-code-workstream-orchestration/` tree after merge

## Branch Stacking

Downstream workstreams branch from their upstream's pushed branch, giving them
access to all upstream code without requiring merges during execution:

```
lesson/02-vibe-infra (base)
    └→ mg-genie-wb-ws-a-pipeline (WS-A branches from base)
        ├→ mg-genie-wb-ws-b-metrics (WS-B branches from WS-A)
        │       └→ mg-genie-wb-ws-c-genie-agent (WS-C branches from WS-B)
        └→ mg-genie-wb-ws-d-features (WS-D branches from WS-A, parallel with B)
```

This means:
- WS-B has all of WS-A's pipeline code when it starts
- WS-C has all of WS-A + WS-B's code
- WS-D has all of WS-A's code (parallel with B, no conflict)

## Task Summary

| Task | Title | Cron | Gates On | Clone Path | Branches From |
| --- | --- | --- | --- | --- | --- |
| WS-0 | WanderBricks WS-0 Scaffold | N/A (complete) | None | orchestration hub | `lesson/02-vibe-infra` |
| WS-A | WanderBricks WS-A Pipeline | `0 */3 * * * ?` | WS-0 COMPLETE | `a-pipeline/` | `lesson/02-vibe-infra` |
| WS-B | WanderBricks WS-B Metrics | `0 */15 * * * ?` | WS-A COMPLETE | `b-metrics/` | `mg-genie-wb-ws-a-pipeline` |
| WS-C | WanderBricks WS-C Genie Agent | `0 */15 * * * ?` | WS-B COMPLETE | `c-genie-agent/` | `mg-genie-wb-ws-b-metrics` |
| WS-D | WanderBricks WS-D Features | `0 */15 * * * ?` | WS-A COMPLETE | `d-features/` | `mg-genie-wb-ws-a-pipeline` |
| WS-FINAL | WanderBricks WS-FINAL Summary | `0 */15 * * * ?` | ALL COMPLETE | orchestration hub | N/A (no code changes) |

## Execution Flow

```
T+0:       All tasks created. WS-A fires within 3 min.
           WS-A: Clones repo → checks out lesson/02 → creates branch → starts work (~45-60 min)
           WS-B, WS-D, WS-C, WS-FINAL: Gate check fails → exit (<10s)

T+~1 hr:   WS-A completes. Pushes branch. Writes COMPLETE to status file in orchestration hub.

T+next 15: WS-B: Clones repo → checks out WS-A's branch → creates own branch → starts (~30 min)
           WS-D: Clones repo → checks out WS-A's branch → creates own branch → starts (~30 min)
           [TRUE PARALLEL — separate git folders, no conflicts]
           WS-C, WS-FINAL: Gate check fails → exit

T+~1.5 hr: WS-B and WS-D complete (roughly same time). Push branches. Write COMPLETE.

T+next 15: WS-C: Clones repo → checks out WS-B's branch → creates own branch → starts (~15 min)
           WS-FINAL: Gate check fails (WS-C not done) → exit

T+~2 hr:   WS-C completes. Writes COMPLETE.

T+next 15: WS-FINAL: All gates pass → writes summary, PR descriptions, merge instructions.
           Operator pauses all scheduled tasks.
```

## Naming Conventions

- **Task titles:** `WanderBricks WS-{X} {Description}`
- **Branches:** `mg-genie-wb-ws-{x}-{description}`
- **Status files:** `workstream-{x}-status.md` (in orchestration hub)
- **Prompt files:** `ws-{x}-{description}-prompt.md`
- **Clone paths:** `~/genie-code-workstream-orchestration/<project>/<ws-letter>-<description>/`

## Prompt Files

- `ws-0-bundle-scaffold-prompt.md` — Retrospective (WS-0 already complete)
- `ws-a-pipeline-prompt.md` — Full SDP pipeline (bronze→silver→gold)
- `ws-b-metrics-prompt.md` — Metric views + orchestration job
- `ws-c-genie-agent-prompt.md` — Genie space over gold layer
- `ws-d-features-prompt.md` — Feature tables (superhost, property quality)
- `ws-final-summary-prompt.md` — Summary + PR instructions for human

## Key Design Decisions

1. **Isolated git folder clones** — Each workstream gets its own clone at
   `~/genie-code-workstream-orchestration/<project>/<ws>/`. Enables true parallel
   execution with different branches checked out simultaneously. No race conditions.

2. **Branch stacking** — Downstream workstreams branch from their upstream's pushed
   branch (not the base). This gives each workstream access to all upstream code
   without requiring merge operations during execution.

3. **Orchestration hub for status** — Status files live in the main project folder
   (not in the clones). All workstreams read/write status from one location.
   Each workstream only writes to its OWN status file — no conflicts.

4. **WS-FINAL as merge guide** — The final workstream gates on ALL others, then
   produces a complete summary with PR titles, descriptions, merge order, and
   post-merge validation steps. The human reviews and executes the merge plan.

5. **Fast-start first workstream** — The first workstream (no upstream dependency)
   polls every 3 minutes (`0 */3 * * * ?`). All others poll every 15 minutes.
   Users see progress within minutes; downstream tasks don't waste resources.

6. **Table-gated + branch-stacked** — Gate checks verify OUTPUT TABLES via SQL COUNT
   (decouples from PR review). Branch stacking ensures code availability for bundle
   validation (downstream has upstream's resource YAMLs).

7. **WS-0 as retrospective** — Documents what WOULD have been the scheduled task
   prompt for the already-completed scaffold. Teaches the full pattern from step 0.

8. **Clone-if-not-exists** — Each prompt includes idempotent clone logic. If the
   clone directory already exists (from a previous failed run), it reuses it.
   This handles the re-fire case gracefully.

## Merge Plan (produced by WS-FINAL)

The branch stack means PRs merge cleanly in this order:

```
1. mg-genie-wb-ws-a-pipeline      → lesson/02-vibe-infra  (base changes only)
2. mg-genie-wb-ws-b-metrics       → lesson/02-vibe-infra  (B's changes only, A already merged)
3. mg-genie-wb-ws-d-features      → lesson/02-vibe-infra  (D's changes only, A already merged)
4. mg-genie-wb-ws-c-genie-agent   → lesson/02-vibe-infra  (C's changes only, B already merged)
```

Each PR shows ONLY that workstream's delta (not its upstream's code), because the
upstream is already in the target branch by the time the PR is reviewed.

## After All Merges

1. Delete `~/genie-code-workstream-orchestration/genieCodeWorkshop/` (clones are disposable)
2. Pause/delete all scheduled tasks
3. Deploy full bundle from `lesson/02-vibe-infra` to confirm complete resource DAG
4. This state becomes the `lesson/03-vibe-ai` branch cut point
5. Begin Vibe Session 2 workstreams (Vector Search)
