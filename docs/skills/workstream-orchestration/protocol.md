# Protocol: Status Files, Clones, Branch Stacking & Scheduling

## Status File Protocol

### State Machine

```
NOT_STARTED → IN_PROGRESS → COMPLETE
                         → BLOCKED (needs human intervention)
```

- `NOT_STARTED` — Initial state. Gate checks read this as "upstream not ready."
- `IN_PROGRESS` — Set at the START of execution (after gate passes). Prevents duplicate runs.
- `COMPLETE` — Set at the END after validation passes. Signals downstream to proceed.
- `BLOCKED` — Unrecoverable error. Human must intervene, fix, and reset to NOT_STARTED.

### YAML Frontmatter Contract

Every status file has machine-readable YAML frontmatter:

```yaml
---
status: NOT_STARTED | IN_PROGRESS | COMPLETE | BLOCKED
branch: <branch-name-when-known>
started_at: <ISO-8601-UTC>
completed_at: <ISO-8601-UTC>
output_tables:
  - catalog.schema.table_1
  - catalog.schema.table_2
validation: PASSED | FAILED | N/A
bundle_deployed: true | false | N/A
tests_passed: true | false | N/A
---
```

Gate checks parse ONLY the `status` field. Other fields are for human review.

### Status File Location

**ALWAYS in the orchestration hub** (main project folder). Never in a working clone.

Path convention: `<project>/fixtures/handoffs/workstream-<x>-status.md`

### Write Rules

- Each workstream writes ONLY to its own status file
- Multiple workstreams can READ the same status file simultaneously (no conflict)
- Status transitions are one-way (never go backwards except human BLOCKED → NOT_STARTED reset)

## Working Directory & Git Strategy (Hub-Lite)

### Core Principle

The **bundle root** is the single working directory for everything during a session.
All code editing, bundle CLI operations, and status file updates happen here.
Git push is a one-way sync at the END of the session — never during.

### Why Not Separate Clones?

The original two-folder pattern (orchestration hub + working clone) caused drift:
- `editAsset` only works within the bundle root path
- `runGit` only works in a git folder
- No tool bridges both paths seamlessly
- Files must exist in BOTH places for bundle CLI + git push → they get out of sync

**Hub-Lite eliminates this** by making the bundle root the single source of truth.
Git is just an archival artifact produced at session end.

### Architecture

```
/Workspace/Users/{user}/{project}/
├── {bundle-name}/                      ← BUNDLE ROOT (source of truth)
│   ├── databricks.yml
│   ├── resources/                      ← Create/edit code here
│   ├── src/                            ← Create/edit code here
│   ├── fixtures/
│   │   ├── handoffs/                   ← Status files (editAsset)
│   │   └── sessions/                   ← Session summaries (editAsset)
│   └── ...
│
└── .git-push-clone/                    ← PUSH CLONE (write-only, end-of-session)
    └── {project}/                      ← Full repo checkout
```

### Session Lifecycle

```
┌─────────────────────────────────────────────────────────┐
│  SESSION START                                          │
│                                                         │
│  1. Gate check (read status files from bundle root)     │
│  2. Set status = IN_PROGRESS (editAsset)                │
│  3. Self-pause (SINGLE-FIRE GUARD)                      │
│  4. All work happens in bundle root:                    │
│     - editAsset / createAsset (code, YAML, configs)     │
│     - runDatabricksCli (validate, deploy, run)          │
│     - executeCode (validation queries)                  │
│  5. Validate outputs                                    │
│  6. Set status = COMPLETE (editAsset)                   │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  SESSION END — Git Sync (one-way)                       │
│                                                         │
│  7. Ensure push clone exists (runGit clone if needed)   │
│  8. In push clone: checkout/create workstream branch    │
│  9. Copy changed files: bundle root → push clone        │
│     (executeCode with workspace SDK file copy)          │
│ 10. Commit + push from push clone                       │
│                                                         │
│  Push clone is WRITE-ONLY. Never read from it.          │
└─────────────────────────────────────────────────────────┘
```

### Push Clone Path Convention

```
/Workspace/Users/{user}/genie-code-workstream-orchestration/{project}/push-clone/
```

One push clone per project (shared across workstreams). Each workstream creates
its own branch within it at session end.

### Conflict Safety (Why This Works)

Workstreams don't conflict because:

1. **Gate checks serialize execution** — B can't start until A = COMPLETE,
   C can't start until B = COMPLETE, etc.
2. **File scope isolation** — Each workstream owns specific directories
   (A: `src/pipelines/`, B: `src/sql/`, D: `src/features/`). No overlap.
3. **Self-pause** — Each workstream fires exactly once. No concurrent instances.
4. **Bundle deploy is additive** — Adding resource B doesn't remove resource A.
   Multiple deploys converge to the desired state regardless of order.
5. **No git during execution** — Zero branch operations means zero race conditions.

For the rare parallel case (B and D both gate only on A): their file scopes
don't overlap, and `bundle deploy` is idempotent, so both can run safely.

### Bundle-First Rule (MANDATORY)

ALL infrastructure changes MUST go through the Declarative Automation Bundle:

1. **Resources** — Pipelines, jobs, schemas, volumes, Lakebase projects — MUST be
   defined in `resources/*.yml` files. Never create them via SDK calls, raw SQL
   (`CREATE SCHEMA`), or CLI commands outside of `bundle deploy`.

2. **Variables** — Use `${var.catalog}`, `${var.schema}`, etc. NEVER hardcode
   catalog or schema names (e.g., never write `hls_fde_dev` literally in resource
   YAML or pipeline code). The bundle's dev mode adds user prefixes automatically.

3. **Resource References** — Use `${resources.schemas.<schema_name>.catalog_name}`
   and `${resources.schemas.<schema_name>.name}` for cross-resource dependencies.
   Never raw `${var.schema}` except in the schema resource definition itself.

4. **Deploy** — `databricks bundle deploy --target dev` is the ONLY way to create or
   update infrastructure. Never call `w.pipelines.create()`, `CREATE TABLE` outside a
   pipeline notebook, or any other direct provisioning.

5. **Validation** — `databricks bundle validate --target dev` MUST pass before deploy.
   Fix all errors. A resource that deploys without bundle awareness (no prefix, wrong
   catalog) is INCORRECT even if it technically runs.

**Why:** Dev mode prefixes (`[dev matthew_giglia]`) and schema prefixes
(`dev_matthew_giglia_*`) are applied automatically by the bundle. Resources created
outside this flow won't have them, will collide with other users, and won't be
tracked in bundle state.

## Branch Stacking (Git Sync)

### Why Branches Still Matter

Even though all work happens in the bundle root, git branches serve as:
- Code review artifacts (PR per workstream)
- Audit trail (what each workstream produced)
- Rollback points (if something breaks post-merge)

### How It Works with Hub-Lite

Since all workstreams work in the same bundle root sequentially, each one
inherits the prior workstream's files naturally. At session end, the git sync
creates a branch that captures that workstream's delta:

```
base-branch (scaffold)
    └→ ws-a-branch (A's code: pipelines, resource YAML)
        ├→ ws-b-branch (B's code: metric views, orchestration job)
        └→ ws-d-branch (D's code: feature tables)
            └→ ws-c-branch (C's code: genie space config)
```

The push clone handles this: each workstream checks out its upstream's branch
(which exists from the prior workstream's push), then adds its own files.

### Merge Plan

PRs merge in dependency order:

1. ws-a → base (A's pipeline code)
2. ws-b → base (B's metric views — A already merged)
3. ws-d → base (D's feature tables — A already merged)
4. ws-c → base (C's genie space — B already merged)

Each PR shows ONLY that workstream's delta.

## Scheduling Strategy

### Cron Rules

| Workstream Type | Cron | Rationale |
| --- | --- | --- |
| First (no upstream, or upstream COMPLETE) | `0 */3 * * * ?` | User sees progress within 3 min |
| All downstream | `0 */15 * * * ?` | Built-in wait time; don't waste resources |
| WS-FINAL | `0 */15 * * * ?` | Only fires once; 15 min is fine |

### Why These Intervals?

- **3 min for first:** Maximizes perceived responsiveness. The user creates all tasks
  and sees the first one start working almost immediately.
- **15 min for others:** These have guaranteed wait time (upstream must complete first,
  which takes 15-60 min). Polling more often just wastes gate-check cycles.

### Self-Termination

Once a workstream marks COMPLETE, every subsequent fire exits in <10 seconds:

```
Fire → Read own status → COMPLETE → "Already complete." → Exit
```

This means all tasks can stay active indefinitely without harm. But best practice
is to pause them after WS-FINAL completes (less noise in the automations panel).

### Self-Pause (Single-Fire Guard)

A workstream MUST deactivate its own cron immediately after setting IN_PROGRESS.
This prevents re-firing while work is in progress (which could read stale state
from a prior run and incorrectly mark COMPLETE).

**API Pattern:**

```python
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()
me = w.current_user.me()

# 1. List all scheduled insights
resp = w.api_client.do(
    "GET", "/api/2.0/alerts-internal/scheduled-insights-list/GENIE_CODE",
    query={"parent_asset_name": f"users/{me.id}"}
)

# 2. Find your own task by display_name
for task in resp.get("scheduled_insights", []):
    if task.get("display_name") == "<YOUR TASK TITLE>":
        auto_id = task["name"].split("/")[-1]

        # 3. PATCH to set paused=true
        w.api_client.do(
            "PATCH",
            f"/api/2.0/alerts-internal/scheduled-insights/{auto_id}",
            body={
                "scheduled_insight": {
                    "name": task["name"],
                    "schedule": {"paused": True}
                },
                "etag": task["etag"],
                "update_mask": "schedule.paused"
            }
        )
        break
```

**Key details:**
- `task["name"]` is the full resource path: `genie_code/users/{user_id}/scheduled_insights/{automation_id}`
- `etag` is required (optimistic concurrency) — get it from the list response
- `update_mask` tells the API which fields to update — without it, the call fails
- The body wraps the mutation inside `scheduled_insight` with `etag` and `update_mask` at the top level
- If self-pause fails, the IN_PROGRESS gate check provides backup protection

**Delete pattern** (for manual cleanup):

```python
w.api_client.do(
    "DELETE",
    f"/api/2.0/alerts-internal/scheduled-insights/{auto_id}",
    body={"name": task["name"]}  # full resource path required in body
)
```

## WS-FINAL: The Mandatory Bookend

### Rule: Every Orchestration MUST Have a WS-FINAL

WS-FINAL is non-negotiable. Without it:
- The human doesn't know what was built
- There's no merge plan
- PR titles/descriptions must be manually written
- The "done" signal is ambiguous

### What WS-FINAL Produces

1. **Executive summary** — workstream count, total duration, resources created
2. **Per-workstream recap** — branch, what was built, outputs, duration
3. **Merge plan** — exact PR titles, descriptions, merge order, dependency notes
4. **Post-merge steps** — validation commands, deploy, cleanup
5. **Cleanup list** — tasks to pause, clones to remove

### WS-FINAL Gate Logic

Gates on ALL other workstreams (not just direct upstreams):

```
Read workstream-a-status.md → must be COMPLETE
Read workstream-b-status.md → must be COMPLETE
Read workstream-c-status.md → must be COMPLETE
Read workstream-d-status.md → must be COMPLETE
```

If ANY is not COMPLETE, exit with a report of what's still pending.

### WS-FINAL Does NOT:
- Write code
- Create branches
- Deploy anything
- Modify resource YAMLs

It ONLY reads status files and writes documentation.

## Status Files & the Workspace Layer

### How Status Updates Work

Status files live in the bundle root at `fixtures/handoffs/workstream-*-status.md`.
They are updated via `editAsset` — which persists immediately to the workspace
filesystem layer, independent of git state.

**Key insight:** `editAsset` writes are readable instantly by all sessions.
No git commit is needed for status coordination. Git is only for archival.

### Rules

- **During execution:** Update status via `editAsset` (immediate, no git needed)
- **At completion:** Status is included in the end-of-session git sync
- **Race avoidance:** Only ONE workstream writes to each status file (enforced
  by gate checks and file scope isolation)
- **No runGit on the hub:** The bundle root is a shared git folder. NEVER run
  `runGit checkout`, `commit_and_push`, or any branch operation on it.
  Git operations happen ONLY in the push clone at session end.

## Error Recovery

### When a Workstream Fails

If a workstream hits an unrecoverable error:

1. It sets its own status to `BLOCKED` with a description of the error
2. Downstream workstreams continue to gate-check and exit (they see non-COMPLETE)
3. WS-FINAL never fires (it requires ALL COMPLETE)

### Human Recovery Steps

1. **Read the BLOCKED status file** — understand what failed
2. **Fix the issue** (manually or by editing the prompt)
3. **Reset status to NOT_STARTED** — this re-arms the workstream
4. **The next scheduled fire picks it up** — gate passes, work resumes

### Common Failure Modes

| Failure | Cause | Fix |
| --- | --- | --- |
| Clone fails | Auth/network issue | Retry (idempotent clone handles it) |
| Bundle validate fails | Missing resource reference | Fix the resource YAML, reset status |
| Table not created | Pipeline error | Check pipeline logs, fix, reset |
| Session timeout | Workstream too large | Split into smaller workstreams |
| Branch already exists | Prior partial run | Clone-if-exists logic handles it |

### The "Stuck" Case

If a workstream is IN_PROGRESS but the scheduled task is no longer running
(e.g., the session timed out without updating status):

1. Manually set status back to NOT_STARTED
2. The next fire will re-enter the clone (exists) and resume from the branch state
3. If the branch has partial work, the agent picks up where it left off

## Testing Checklist

Before going live with a full orchestration run:

- [ ] All status files are NOT_STARTED
- [ ] Orchestration hub is on the correct branch (scaffold/base)
- [ ] No stale clones in ~/genie-code-workstream-orchestration/<project>/
- [ ] All scheduled tasks are paused (create paused, unpause together)
- [ ] PROJECT_MEMORY.md and architecture docs are committed and pushed
- [ ] Prompt files reference correct absolute paths
- [ ] Gate check tables don't already exist (or clean them first)
- [ ] Bundle validates clean on the base branch
