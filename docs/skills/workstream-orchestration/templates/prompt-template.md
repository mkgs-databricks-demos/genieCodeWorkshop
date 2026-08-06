# Workstream Prompt Template

Copy and customize for each workstream. Replace all `<placeholders>`.

---

```markdown
# Scheduled Task Prompt — Workstream <X>: <Description>

## scheduleAgentTool Parameters

- **title:** `<Project> WS-<X> <Description>`
- **cronExpression:** `0 */3 * * * ?` (first workstream) OR `0 */15 * * * ?` (downstream)

## Instructions

You are executing workstream <X> of the <Project> orchestration: <one-sentence summary>.

Orchestration hub (status files): <absolute path to project root>
Working clone: /Workspace/Users/<username>/genie-code-workstream-orchestration/<project>/<x>-<description>/
Git remote: (same repo as orchestration hub)
Branch from: <upstream-branch-name>

### GATE CHECK

1. Read <own-status-file>. If COMPLETE, stop.
2. Read <upstream-status-file(s)>. If not COMPLETE, report and stop.
3. (Optional) SQL: SELECT COUNT(*) FROM <prerequisite_table> — must be > 0.

### CONTEXT

Read these files:
- PROJECT_MEMORY.md
- fixtures/architecture/scheduled-tasks/README.md
- <upstream-status-file> ("Notes for Downstream" section)
- <any config/convention files relevant to this workstream>

Also: Review the current state of the source code in the working clone to understand
what the project does and where it is currently. Read key files (README, existing
resources, src/ structure) before writing new code.

### EXECUTE

1. Set own status to IN_PROGRESS, set started_at.
   Use workspace file tools (editAsset) — do NOT use git for status files.

1b. SINGLE-FIRE GUARD: Deactivate your own cron schedule immediately.
    List scheduled insights (GET alerts-internal/scheduled-insights-list/GENIE_CODE,
    query: parent_asset_name=users/{your_id}). Find entry by display_name.
    Extract automation_id from name field (last path segment). Then PATCH:
    body: {"scheduled_insight": {"name": <full_name>, "schedule": {"paused": true}},
    "etag": <etag>, "update_mask": "schedule.paused"}.
    If this fails, continue — IN_PROGRESS gate provides backup.

1c. GIT FOLDER ISOLATION (CRITICAL):
    - The orchestration hub is a SHARED git folder. NEVER run runGit on it.
    - Status files are edited via workspace file tools only (no git needed).
    - ALL git operations (clone, checkout, commit, push) go to the WORKING CLONE.
    - Before any runGit call, verify repoPath starts with the clone base path.

1d. BUNDLE-FIRST RULE (CRITICAL):
    - ALL resources (pipelines, jobs, schemas, volumes) MUST be defined in
      resources/*.yml files and deployed via `databricks bundle deploy --target dev`.
    - NEVER hardcode catalog/schema names. Use ${var.catalog}, ${var.schema},
      ${resources.schemas.<name>.catalog_name}, ${resources.schemas.<name>.name}.
    - NEVER create resources via SDK calls or raw SQL outside of bundle deploy.
    - `databricks bundle validate --target dev` MUST pass before deploying.
    - A resource deployed without the bundle (no dev prefix, hardcoded names)
      is INCORRECT even if it technically works.

2. SET UP WORKING CLONE:
   a. Check if working clone path exists.
   b. If NOT: runGit clone (url: <remote>, path: <clone-path>, provider: gitHub).
   c. In CLONE: checkout <upstream-branch>, pull latest.
   d. Create new branch <own-branch> from <upstream-branch>.
   e. If EXISTS: checkout <own-branch> (resume).
   f. ALL code work in clone via editAsset on clone path files.
   g. ALL git commits use repoPath = clone path. NEVER the orchestration hub.

3. <Step-by-step work description>
   - Be specific about WHAT (table names, resource types, directories)
   - Reference conventions from PROJECT_MEMORY.md
   - Let the agent decide HOW to implement
   - When in doubt about the best way to implement something, use your available
     tools (docSearch, spark APIs, skill files) to check the latest Databricks
     best practices before proceeding.

4. databricks bundle validate --target dev. Fix errors.
5. databricks bundle deploy --target dev.

### VALIDATE

- SQL: SELECT COUNT(*) FROM <output_table_1> — expect > 0
- SQL: SELECT COUNT(*) FROM <output_table_2> — expect > 0
- databricks bundle validate --target dev — expect clean

### COMPLETE

1. Update own status file: COMPLETE, completed_at, output_tables, branch.
2. Add "What Was Built" section.
3. Add "Notes for Downstream Sessions" with context for next workstream.
4. Write session summary to fixtures/sessions/YYYY-MM-DD_ws-<x>-<description>.md
5. Commit and push code changes (working clone).
6. Status files are already saved (editAsset writes to workspace immediately).
   They will be committed as part of a human-triggered batch commit on the hub.
```
