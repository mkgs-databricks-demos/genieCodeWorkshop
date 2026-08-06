# Orchestration README Template

Copy this into `fixtures/architecture/scheduled-tasks/README.md` for your project.
Replace all `<placeholders>` with your values.

---

```markdown
# Scheduled Task Orchestration — <Project Name>

## Overview

<N> Genie Code workstreams execute the <Project> build in dependency order,
coordinated via status files and isolated git folder clones.

## Clone Structure

~/genie-code-workstream-orchestration/
└── <project-name>/
    ├── <a-description>/    ← WS-A clone
    ├── <b-description>/    ← WS-B clone
    └── ...                 ← one per workstream

~/<project-repo>/              ← orchestration hub (status files)

## Branch Stacking

<base-branch>
    └→ <ws-a-branch> (branches from base)
        ├→ <ws-b-branch> (branches from WS-A)
        └→ <ws-d-branch> (branches from WS-A, parallel)

## Task Summary

| Task | Title | Cron | Gates On | Clone Path | Branches From |
| --- | --- | --- | --- | --- | --- |
| WS-A | <Project> WS-A <Desc> | 0 */3 * * * ? | <upstream> COMPLETE | <a-desc>/ | <base-branch> |
| WS-B | <Project> WS-B <Desc> | 0 */15 * * * ? | WS-A COMPLETE | <b-desc>/ | <ws-a-branch> |
| WS-FINAL | <Project> WS-FINAL Summary | 0 */15 * * * ? | ALL COMPLETE | hub | N/A |

## Execution Flow

T+0:       All tasks created. WS-A fires within 3 min.
T+~1 hr:   WS-A completes. Downstream unblocked.
T+~1.5 hr: Parallel workstreams complete.
T+~2 hr:   All done. WS-FINAL writes merge plan.

## Naming Conventions

- Task titles: <Project> WS-{X} {Description}
- Branches: <prefix>-ws-{x}-{description}
- Status files: workstream-{x}-status.md
- Prompt files: ws-{x}-{description}-prompt.md
- Clone paths: ~/genie-code-workstream-orchestration/<project>/<x>-<description>/

## Key Design Decisions

1. Isolated git folder clones (parallel execution)
2. Branch stacking (upstream code access without merges)
3. Orchestration hub for status (single source of truth)
4. WS-FINAL as merge guide (mandatory bookend)
5. Fast-start first workstream (3-min poll)
6. Table-gated + branch-stacked (decoupled from PR review)

## Merge Plan (produced by WS-FINAL)

1. <ws-a-branch> → <base-branch>
2. <ws-b-branch> → <base-branch> (after #1)
3. ...

## After All Merges

1. Remove ~/genie-code-workstream-orchestration/<project>/ (disposable)
2. Pause all scheduled tasks
3. Deploy full bundle, validate
4. Cut next branch from this state
```
