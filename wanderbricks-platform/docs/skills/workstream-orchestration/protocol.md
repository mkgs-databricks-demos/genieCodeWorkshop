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

## Clone Structure

### Path Convention

```
~/genie-code-workstream-orchestration/<project-name>/<ws-letter>-<description>/
```

Examples:
```
~/genie-code-workstream-orchestration/myProject/a-pipeline/
~/genie-code-workstream-orchestration/myProject/b-metrics/
~/genie-code-workstream-orchestration/myProject/c-agent/
```

### Why Separate Clones?

A workspace git folder is a single working copy. Only one branch can be checked
out at a time. If two scheduled tasks fire simultaneously and both try to checkout
different branches in the same folder, one wins and the other corrupts its state.

Separate clones solve this completely:
- Each clone has its own branch checkout
- No race conditions on git operations
- True parallel execution with full isolation

### Clone Lifecycle

1. **Created** on first run of a workstream (idempotent — if exists, reuse)
2. **Used** for all code work during execution
3. **Preserved** across retries (if a workstream fails and re-fires, it resumes)
4. **Disposable** after all merges complete (entire tree can be safely removed)

### Idempotent Clone Logic

Every prompt includes this pattern:

```
a. Check if <clone-path> exists.
b. If NOT: Clone the repo to <clone-path>.
c. Checkout <upstream-branch>, pull latest.
d. Create new branch <own-branch>.
e. If EXISTS: checkout <own-branch> (resume prior run).
```

This handles:
- First run (clone + branch create)
- Retry after failure (reuse clone, resume branch)
- Re-fire after COMPLETE (caught by gate check before reaching clone logic)

## Branch Stacking

### The Problem It Solves

Downstream workstreams often need upstream code for:
- Bundle validation (resource YAMLs reference each other)
- Import statements (Python modules created upstream)
- Config files (created by upstream, consumed by downstream)

Without branch stacking, downstream would branch from the base (which doesn't
have upstream's code), and bundle validate would fail on missing references.

### How It Works

```
base-branch
    └→ ws-a-branch (branches from base)
        ├→ ws-b-branch (branches from ws-a-branch)
        └→ ws-d-branch (branches from ws-a-branch)
            └→ ws-c-branch (branches from ws-b-branch)
```

Each workstream checks out its upstream's PUSHED branch (from remote), then
creates its own branch from that point. This gives it all upstream code.

### Merge Plan Consequence

Branch stacking means PRs merge in dependency order:

1. ws-a → base (only A's changes)
2. ws-b → base (only B's changes — A already merged)
3. ws-d → base (only D's changes — A already merged)
4. ws-c → base (only C's changes — B already merged)

Each PR shows ONLY that workstream's delta because its upstream is already
in the target branch by merge time.

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
