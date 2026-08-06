# Workstream Isolation — Architecture Proposal

> **Status:** PROPOSAL (for review)  
> **Date:** 2026-08-06  
> **Context:** Lessons learned from WS-A rebuild session

---

## Problem Statement

The current two-folder pattern (orchestration hub + working clone) introduces friction:

1. **Drift** — Files must exist in both the orchestration hub (for bundle deploy) and
   the working clone (for git push). They get out of sync.
2. **Tool restrictions** — `editAsset` only works within the bundle root. `runGit` only
   works in the clone. No tool bridges both paths.
3. **No-op commits** — Can't push a branch from the clone if no *new* edits are made there,
   even though the branch has valuable code history from prior sessions.
4. **Double maintenance** — Creating a resource YAML in the clone doesn't deploy it;
   you must also create it in the orchestration hub.

### Root Cause

The system binds three concerns to a single filesystem path (the "bundle root"):
- Bundle CLI execution (`databricks bundle validate/deploy/run`)
- File editing (`editAsset` path restriction)
- Source-linked deployment (pipeline notebooks resolved from this path)

But git operations require a *separate* path because the shared folder can't safely
have branches switched (concurrent workstreams would clobber each other).

---

## Proposed Pattern: "Hub-Lite + PR-on-Complete"

### Core Idea

The bundle root is the single working directory for EVERYTHING during a session.
Git push happens once at the end, as a one-way sync from the bundle root to a
dedicated push clone.

### Architecture

```
/Users/{user}/genieCodeWorkshop/
├── wanderbricks-platform/              ← BUNDLE ROOT (source of truth)
│   ├── databricks.yml
│   ├── resources/
│   ├── src/pipelines/
│   ├── fixtures/
│   │   ├── handoffs/                   ← Status files (workspace-managed)
│   │   ├── sessions/
│   │   └── architecture/
│   └── ...
│
└── .git-push-clone/                    ← GIT CLONE (push-only, NOT for editing)
    └── wanderbricks-platform/          ← Full repo checkout
```

### Lifecycle

```
┌─────────────────────────────────────────────────────────┐
│  SESSION START                                          │
│                                                         │
│  1. Gate check (read status files from bundle root)     │
│  2. Set status = IN_PROGRESS                            │
│  3. All work happens in bundle root:                    │
│     - editAsset (code, YAML, status files)              │
│     - runDatabricksCli (validate, deploy, run)          │
│     - executeCode (validation queries)                  │
│  4. Set status = COMPLETE                               │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  SESSION END — Git Sync                                 │
│                                                         │
│  5. In .git-push-clone:                                 │
│     a. Pull latest from base branch                     │
│     b. Create/checkout workstream branch                │
│     c. Copy changed files from bundle root → clone      │
│     d. Commit + push                                    │
│                                                         │
│  This is a ONE-WAY sync. Clone is never edited directly.│
└─────────────────────────────────────────────────────────┘
```

### Key Differences from Current Pattern

| Concern | Current (Two-Folder) | Proposed (Hub-Lite) |
| --- | --- | --- |
| Where code is authored | Working clone | Bundle root |
| Where bundle CLI runs | Bundle root (orchestration hub) | Bundle root (same place as code) |
| Where status files live | Bundle root | Bundle root |
| Where git push happens | Working clone | Push clone (post-session only) |
| File sync required? | Yes (bidirectional, manual) | Yes (one-way, scripted, end-of-session) |
| editAsset works? | Only in bundle root | Yes (everything is there) |
| Risk of drift | High (continuous) | None during session (sync is atomic) |

---

## How the Git Sync Works

The sync step at session end is mechanical and can be scripted:

```python
# Pseudocode for end-of-session sync
# Runs in .git-push-clone/ via runGit

# 1. Ensure on the right branch
runGit(operation="checkout", branchName="mg-genie-wb-ws-a-pipeline-v2")
runGit(operation="pull")  # get latest

# 2. Copy changed files from bundle root
#    (executeCode with a targeted file-copy script)
files_to_sync = [
    "resources/wanderbricks_pipeline.pipeline.yml",
    "src/pipelines/bronze_pipeline.py",
    "src/pipelines/silver_pipeline.py",
    "src/pipelines/gold_pipeline.py",
    "fixtures/handoffs/workstream-a-status.md",
]
for f in files_to_sync:
    copy(src=f"{BUNDLE_ROOT}/{f}", dst=f"{PUSH_CLONE}/{f}")

# 3. Commit + push
runGit(operation="commit_and_push", commitMessage="WS-A: pipeline complete")
```

### Why One-Way Sync Is Safe

- The bundle root is authoritative during a session. No one else edits it
  concurrently (workstreams are serialized by the gate check / status protocol).
- The push clone is never read FROM — it's a write-only sink for git history.
- If a future session starts, it reads from the bundle root (not the clone).

---

## Handling Concurrent Workstreams

Workstreams A and B can't truly run in parallel on the same bundle root if they
touch overlapping files. But they CAN coexist because:

1. **File isolation** — Each workstream declares which paths it touches
   (e.g., WS-A owns `src/pipelines/`, WS-B owns `src/metric_views/`).
2. **Gate checks** — WS-B gates on WS-A's gold tables existing, so it won't start
   until WS-A is COMPLETE.
3. **Non-overlapping resources** — Each workstream adds its own resource YAML;
   they don't modify each other's files.

If true parallelism is needed (e.g., WS-B and WS-D both gate only on WS-A),
the current pattern works because their file scopes don't overlap. The bundle root
supports multiple resource YAMLs being added concurrently.

---

## What Changes in Workstream Prompts

### Remove

- All references to "working clone" paths
- `runGit clone` / `checkout` / `pull` steps at session start
- The "GIT FOLDER ISOLATION" section (replaced by simpler rules)
- Any instruction to create files in both locations

### Replace With

```markdown
== GIT SYNC (end of session only) ==

After setting status = COMPLETE:
1. In push clone at /Workspace/.../genie-code-workstream-orchestration/:
   a. Checkout/create branch: mg-genie-wb-ws-{x}-{description}
   b. Copy all files declared in "File Isolation" section from bundle root → clone
   c. Commit: "WS-{X}: {summary}"
   d. Push

Do NOT edit files in the push clone. It is write-only.
```

### Simplify

```markdown
== WORKING DIRECTORY ==

All work happens in the bundle root:
  /Users/{user}/genieCodeWorkshop/wanderbricks-platform/

- editAsset: creates/modifies files here
- runDatabricksCli: bundle validate/deploy/run here
- Status files: editAsset on fixtures/handoffs/ here
- No separate clone needed during the session.
```

---

## The File-Copy Constraint

The one remaining friction point: copying files from bundle root → push clone
requires `executeCode` (Python file I/O or SDK workspace API). This is currently
blocked by the "never use executeCode to edit files" instruction.

### Options

1. **Relax the rule for git-sync only** — Allow `executeCode` for the one-way
   copy operation since it's writing to the CLONE (not the bundle root), and
   it's a mechanical sync step (not creative authoring).

2. **Use the workspace SDK** — `w.workspace.get_status()` + `w.workspace.export()`
   from source, then `w.workspace.import_()` to destination. This is a "file copy"
   not a "file edit".

3. **Skip git entirely for status files** — Only sync CODE files (resources/,
   src/). Status files don't need git history since they're coordination artifacts.
   This reduces the sync surface.

4. **Scheduled-task-aware tooling** — Future Genie Code improvements could allow
   `editAsset` to target any workspace path (removing the bundle-root restriction),
   or add a native `runGit push` operation that doesn't require a new commit.

---

## Comparison Summary

| | Current | Proposed |
| --- | --- | --- |
| Folders per workstream | 2 (hub + clone) | 1 (bundle root) + shared push clone |
| Where drift can happen | Continuously (any file) | Never during session |
| Git push timing | Incremental (bronze→silver→gold) | Once at session end |
| editAsset coverage | Partial (bundle root only) | Complete (all files here) |
| Bundle CLI coverage | Full | Full (same path) |
| Complexity for prompts | High (7c, 7d, 8a-8e) | Low (single working dir) |
| Code review quality | Per-layer commits | Single cohesive commit per workstream |

---

## Recommendation

Adopt **Hub-Lite + PR-on-Complete** for the next iteration of workstream prompts.
The single biggest improvement is eliminating the "file must exist in both places"
problem — which was the exact failure mode in the WS-A rebuild.

For the file-copy step, use Option 2 (workspace SDK) with a helper function that
the workstream prompt calls at completion. This keeps the "never executeCode to edit"
rule intact for the bundle root while allowing mechanical sync to the push clone.

---

## Migration Steps

1. [ ] Update `README.md` in this directory with new architecture diagram
2. [ ] Revise workstream prompts (ws-a through ws-d) to remove two-folder pattern
3. [ ] Add "Git Sync" section template to each prompt
4. [ ] Create helper: `fixtures/scripts/sync_to_git.py` (workspace SDK file copy)
5. [ ] Test with one workstream (suggest WS-B as next candidate)
6. [ ] Document in `PROJECT_MEMORY.md`
