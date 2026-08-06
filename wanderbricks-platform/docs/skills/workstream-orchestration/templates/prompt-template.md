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
Working clone: ~/genie-code-workstream-orchestration/<project>/<x>-<description>/
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

### EXECUTE

1. Set own status to IN_PROGRESS, set started_at.

2. SET UP WORKING CLONE:
   a. Check if working clone path exists.
   b. If NOT: Clone repo to that path.
   c. Checkout <upstream-branch>, pull latest.
   d. Create new branch <own-branch> from <upstream-branch>.
   e. If EXISTS: checkout <own-branch> (resume).
   f. ALL code work in clone. Status files in orchestration hub.

3. <Step-by-step work description>
   - Be specific about WHAT (table names, resource types, directories)
   - Reference conventions from PROJECT_MEMORY.md
   - Let the agent decide HOW to implement

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
6. Commit and push status update (orchestration hub).
```
