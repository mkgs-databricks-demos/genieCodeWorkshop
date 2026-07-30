# Genie Code Best Practices & Conventions

> These conventions have been developed through extensive production use of Genie Code across multiple Databricks projects. They represent patterns that maximize Genie Code's effectiveness by providing consistent context, reducing re-explanation, and enabling long-term project continuity.

---

## Table of Contents

1. [The Context Principle](#the-context-principle)
2. [Git Workflow](#git-workflow)
3. [Project Memory](#project-memory)
4. [Session Summaries](#session-summaries)
5. [Choosing the Right Editor](#choosing-the-right-editor)
6. [Skills Management](#skills-management)
7. [MCP Servers](#mcp-servers)
8. [Declarative Automation Bundle Conventions](#declarative-automation-bundle-conventions)
9. [Spark Declarative Pipeline Conventions](#spark-declarative-pipeline-conventions)
10. [The Flywheel: Building Tools for Genie Code](#the-flywheel-building-tools-for-genie-code)

---

## The Context Principle

The single most important factor in Genie Code's effectiveness is **context**. Every convention in this document exists to give Genie Code better context — whether that's through file structure, naming, documentation, or Unity Catalog metadata.

**Why context matters more than prompting skill:**
- Genie Code has deep integration with Unity Catalog — table schemas, column comments, lineage, and governance metadata are all visible to it
- The editor you're in determines what tools Genie Code has access to
- Long-term memory (project files, session summaries) eliminates the cold-start problem
- Well-structured bundles let Genie Code understand dependencies and make correct architectural decisions

> **Rule of thumb:** If you find yourself re-explaining something to Genie Code, that information should live in a file it can read.

---

## Git Workflow

### Never Commit to Main

All work must be done in feature branches. This is non-negotiable.

```
# Branch naming convention
mg-genie-<short-description>

# Examples
mg-genie-phase6-shutdown-polish
mg-genie-add-metrics-pipeline
mg-genie-fix-auth-flow
```

**Why this matters for Genie Code:**
- Genie Code can commit and push from feature branches safely
- You maintain a clean review process (PR → review → merge)
- If Genie Code makes a mistake, it's isolated to a branch you can discard
- The branch name gives Genie Code context about what it's working on

### Feature Branch Workflow

1. **Create branch** from the appropriate base (main, or a long-lived branch)
2. **Work with Genie Code** — let it commit incrementally as work progresses
3. **Push the branch** when ready for review
4. **Create PR** with a clear title and description
5. **Merge** after review (squash or merge commit, your preference)

### Long-Lived Branches (for workshops/phased projects)

When a project has distinct phases or modules:

```
lesson/01-foundations      # Phase 1 starting point
lesson/02-implementation   # Phase 2 starting point (includes phase 1 completed)
lesson/03-advanced         # Phase 3 starting point (includes phases 1+2 completed)
```

Authoring branches target specific long-lived branches:

```
mg-genie-L01-<description>   → PR into lesson/01-*
mg-genie-L02-<description>   → PR into lesson/02-*
mg-genie-main-<description>  → PR into main
```

---

## Project Memory

### What Is PROJECT_MEMORY.md?

A living document at the root of your project (same level as `databricks.yml` or `README.md`) that captures:
- Architectural decisions and rationale
- Naming conventions specific to the project
- Resource IDs and references
- Target/environment mappings
- Integration points and dependencies
- Open questions and known issues

### Why It Exists

Genie Code sessions are ephemeral. Without project memory:
- Every new session starts cold — you re-explain architecture, naming, decisions
- Genie Code may make inconsistent decisions across sessions
- Onboarding a new team member (or a new Genie Code session) requires verbal knowledge transfer

With project memory:
- Genie Code reads it at session start and immediately has full context
- Decisions are consistent because they're documented
- Any team member (or any Genie Code session) can pick up where you left off

### Structure

```markdown
# PROJECT_MEMORY.md — [Project Name]

> Last updated: YYYY-MM-DD
> Owner: email@databricks.com

## Project Identity
[What is this? Who is it for? What does it do?]

## Architecture
[Key decisions, patterns, dependencies]

## Targets & Environments
[dev/staging/prod mappings, resource IDs]

## Conventions
[Project-specific naming, patterns]

## Open Questions
[Things still being decided]
```

### Placement

- **Single-bundle project:** Same directory as `databricks.yml`
- **Monorepo with multiple bundles:** At the repo root (shared between bundles)
- **Never** in `.assistant_instructions.md` — that file is for cross-project user preferences

---

## Session Summaries

### What Are They?

A record of what happened in a Genie Code session — problems encountered, decisions made, files changed, and why.

### Where They Live

```
<bundle-root>/
├── fixtures/
│   └── sessions/
│       ├── INDEX.md              # Reverse-chronological index
│       ├── 2026-08-01_initial-pipeline-setup.md
│       ├── 2026-08-02_fix-auth-and-add-metrics.md
│       └── 2026-08-03_app-deployment.md
```

### Format

**Filename:** `YYYY-MM-DD_short-description.md`  
**Always use** `datetime.now()` for dates (never hardcode)

**Content:**

```markdown
# Session Summary: [Short Description]

**Date:** YYYY-MM-DD  
**Branch:** mg-genie-<branch-name>

## Problems Encountered
- [What went wrong or was unclear]

## Root Causes
- [Why it happened]

## Changes Made
- [Files modified, resources created]

## Decisions
- [Architectural choices and rationale]

## Files Modified
- `path/to/file.py` — [what changed]
```

### INDEX.md

Maintain in **reverse-chronological** order (newest first):

```markdown
# Session Index

| Date | Summary | Branch |
| --- | --- | --- |
| 2026-08-03 | App deployment and OAuth fix | mg-genie-app-deploy |
| 2026-08-02 | Auth flow fix + metrics pipeline | mg-genie-fix-auth |
| 2026-08-01 | Initial pipeline setup | mg-genie-initial-setup |
```

### Why This Matters

- **Continuity across sessions:** Next session, Genie Code reads the last summary and knows exactly where you left off
- **Debugging history:** When something breaks, you can trace what changed and when
- **Knowledge transfer:** Another engineer can understand the project's evolution
- **Pattern recognition:** Over time, you see recurring issues and can address root causes

---

## Choosing the Right Editor

Genie Code's capabilities change based on which editor/page you're on. Choosing the right editor is choosing the right toolset.

| Editor | Genie Code Has Access To | Best For |
| --- | --- | --- |
| **Notebook** | Cell execution, iterative debugging, DataFrame inspection, library installation | Data exploration, pipeline development, prototyping |
| **SQL Editor** | SQL warehouse execution, query results, schema browsing | SQL development, query optimization, DDL |
| **Git Folder** | File creation/editing, git operations (commit, push, branch) | Project scaffolding, multi-file changes, documentation |
| **Pipeline Editor** | Pipeline-specific tools, dataset inspection, run history | SDP development, pipeline debugging |
| **Dashboard** | Widget creation, dataset binding, layout tools | Dashboard building and editing |
| **Jobs Page** | Job configuration, task editing, run history | Job setup, scheduling, debugging failures |
| **Apps Page** | App scaffolding, deployment, permission management | App development and deployment |
| **Bundle Editor** | Bundle YAML editing, resource definitions, variable configuration, target management | DAB configuration, resource wiring, multi-target setup |

### Key Insight: Navigate to Get the Right Tools

If you're in a notebook and want to create a job, **ask Genie Code to navigate you to the Jobs page** — it has better tools there. Don't try to force everything through one editor.

### Editor-Context Patterns

**Starting a new project?** → Git folder (scaffold structure, create files)  
**Exploring data?** → Notebook (execute queries, inspect results)  
**Configuring a bundle?** → Bundle editor (resource definitions, variables, targets)  
**Building a pipeline?** → Pipeline editor (specialized SDP tools)  
**Creating a dashboard?** → Dashboard page (widget tools)  
**Setting up a job?** → Jobs page (task configuration tools)  

---

## Skills Management

### What Are Skills?

Skills are curated knowledge files that Genie Code loads on-demand for domain-specific expertise. They live in `~/.assistant/skills/<skill-name>/`.

### When to Create a Skill

- You have domain knowledge that applies across multiple projects
- You find yourself repeatedly explaining the same patterns
- There's a library or API that Genie Code doesn't know well
- You want to encode team standards (brand guidelines, coding conventions)

### When to Remove/Evaluate a Skill

- The skill contains outdated information (APIs changed, libraries updated)
- The skill conflicts with current best practices
- The skill is too broad and loads unnecessary context
- You're starting fresh and want a clean baseline

### Skill Structure

```
~/.assistant/skills/
├── my-custom-skill/
│   ├── SKILL.md           # Entry point — loaded first
│   ├── reference.md       # Additional detail (loaded on demand)
│   └── scripts/           # Executable scripts (optional)
│       └── setup.sh
```

### Best Practice: Periodic Skill Audit

Before starting a major new project:
1. List your current skills
2. Evaluate each: Is it current? Is it relevant to this project?
3. Remove stale skills that might inject incorrect context
4. Add new skills for the project's domain

---

## MCP Servers

### What Are MCP Servers?

Model Context Protocol (MCP) servers connect Genie Code to external services — Slack, GitHub, Google Drive, Jira, etc. They give Genie Code the ability to search and read from these services.

### Why They Matter

- **Slack:** Find team discussions about requirements, decisions, blockers
- **GitHub:** Search code, review PRs, check issues without leaving Databricks
- **Google Drive:** Access design docs, requirements, specifications
- **Jira/Confluence:** Pull ticket context, architecture docs

### Setup Approach

1. Open Assistant Settings (gear icon in Genie Code panel)
2. Navigate to MCP Connectors section
3. Enable connectors relevant to your workflow
4. Authenticate with each service

### Best Practice: Connect Before You Code

Set up MCP servers at the START of a project. When Genie Code can access:
- Your team's Slack channels → it understands requirements and decisions
- Your GitHub repos → it sees existing patterns and code
- Your Google Docs → it reads specifications and design docs

This is context that would otherwise live only in your head.

---

## Declarative Automation Bundle Conventions

### Notebook Paths in Bundle YAML

The file extension determines language and compute compatibility:

```yaml
# Python notebook — runs on serverless or clusters
- task_key: etl-task
  notebook_task:
    notebook_path: ./src/my_etl.ipynb

# SQL notebook — runs on SQL warehouse (requires warehouse_id)
- task_key: ddl-task
  notebook_task:
    notebook_path: ./src/my_ddl.sql
    warehouse_id: ${var.warehouse_id}
```

**Rules:**
- Default to `.ipynb` for all notebooks
- Use `.sql` ONLY when the task has a `warehouse_id` (SQL warehouse execution)
- `.py` works for Python-only (serverless/clusters)
- `.r` / `.scala` require classic clusters (not serverless)

### Schema References

Always use resource references — never raw variables in resource definitions:

```yaml
# CORRECT — ensures dependency ordering
resources:
  schemas:
    my_schema:
      catalog_name: ${var.catalog}
      name: ${var.schema}
  
  jobs:
    my_job:
      tasks:
        - task_key: setup
          notebook_task:
            base_parameters:
              catalog: ${resources.schemas.my_schema.catalog_name}
              schema: ${resources.schemas.my_schema.name}
```

```yaml
# WRONG — no dependency guarantee
jobs:
  my_job:
    tasks:
      - task_key: setup
        base_parameters:
          catalog: ${var.catalog}
          schema: ${var.schema}
```

### SDK Install Pattern

For notebooks that use the Databricks SDK, the FIRST code cell (before widgets/imports) must be:

**Cell title:** "Install latest Databricks SDK"

```python
%pip install --upgrade databricks-sdk
dbutils.library.restartPython()
```

**Important:** On serverless, use `dbutils.library.restartPython()` (the function), NOT `%restart_python` (the magic) — the magic breaks local `src/` imports.

Add `mlflow` only if the notebook actually uses it:

```python
%pip install --upgrade databricks-sdk mlflow
dbutils.library.restartPython()
```

### Bundle Structure Pattern

A well-structured bundle for Genie Code context:

```
my-project/
├── databricks.yml              # Bundle definition
├── PROJECT_MEMORY.md           # Architectural decisions
├── README.md                   # Project overview
├── src/
│   ├── pipelines/              # SDP notebooks
│   ├── notebooks/              # Job task notebooks
│   └── includes/               # Shared Python modules
├── fixtures/
│   ├── sessions/               # Session summaries
│   │   ├── INDEX.md
│   │   └── YYYY-MM-DD_*.md
│   └── config/                 # Environment configs (YAML)
└── tests/                      # Validation notebooks
```

---

## Spark Declarative Pipeline Conventions

### Terminology

- **Always:** "Spark Declarative Pipelines" or "SDP"
- **Never:** "Delta Live Tables" or "DLT"
- CDC API = **AUTO CDC**

### Modern API (current)

```python
from pyspark import pipelines as dp

@dp.table(...)                 # streaming table
@dp.materialized_view(...)     # materialized view
@dp.temporary_view()           # internal view (NOT @dp.view)

# Expectations (data quality)
@dp.expect("description", "condition")
@dp.expect_or_drop("description", "condition")
@dp.expect_or_fail("description", "condition")
@dp.expect_all({...})
@dp.expect_all_or_drop({...})
@dp.expect_all_or_fail({...})

# Programmatic table creation
dp.create_streaming_table("target")
dp.create_auto_cdc_flow(
    target=..., 
    source=..., 
    keys=..., 
    sequence_by=..., 
    stored_as_scd_type=1
)

# Reading data
spark.readStream.table("catalog.schema.table")  # NOT dlt.readStream()
spark.read.table("catalog.schema.table")        # NOT dlt.read()
```

### Architecture: Metadata-Driven

- **Logic** in reusable Python classes
- **Configuration** in YAML files (`fixtures/config/`)
- **Notebooks** read config and invoke classes

This pattern means:
- Genie Code can modify config without touching logic
- New sources/targets are config additions, not code changes
- Testing is straightforward (swap config, same logic)

### Legacy Migration Reference

| Legacy | Modern |
| --- | --- |
| `import dlt` | `from pyspark import pipelines as dp` |
| `@dlt.table(...)` | `@dp.table(...)` |
| `@dlt.view(...)` | `@dp.temporary_view()` |
| `dlt.readStream("t")` | `spark.readStream.table("t")` |
| `dlt.read("t")` | `spark.read.table("t")` |
| `dlt.apply_changes(...)` | `dp.create_auto_cdc_flow(...)` |

---

## The Flywheel: Building Tools for Genie Code

### The Concept

The most powerful pattern in Genie Code isn't a prompt technique — it's building artifacts that Genie Code can later use as tools:

```
Raw context → Ingest → Index → UC Function → Genie Code tool → Builds smarter things
```

### Example: Business Definitions

1. You have a PDF/doc with metric definitions and business rules
2. Ingest it into a Unity Catalog Volume
3. Chunk and create a Vector Search index
4. Wrap the index in a UC function: `lookup_business_definition(query)`
5. Now Genie Code can query your business definitions when building metric views, dashboards, or reports

### Example: Resolution Patterns

1. You have a table of resolved support tickets
2. ETL to flatten and chunk the conversations
3. Create a Vector Search index over the resolutions
4. Wrap in a UC function: `search_resolution_patterns(query)`
5. Genie Code uses this when building support agents or writing prompt templates

### Example: Data Dictionary

1. Unity Catalog already has table/column metadata
2. Extract and consolidate into a searchable document
3. Index it for semantic search
4. Now Genie Code can answer "which table has X?" semantically instead of scanning every schema

### Why This Is Uniquely Powerful in Databricks

- Unity Catalog functions ARE the tool interface — no external API needed
- Vector Search is a managed service — no infra to maintain
- Genie Code automatically sees UC functions as available tools
- The governance model means tools are permissioned and auditable

---

## Sharing Genie Code Sessions

### When to Share

- You've solved a complex problem and want to show the approach
- You're pairing asynchronously — share the session for a colleague to continue
- You want to document a demo flow that others can reproduce
- You've built something and want stakeholder review of the process

### How to Share

Use the share button in the thread header. Shared viewers see:
- Full message history
- All tool outputs and results
- The reasoning and approach

Shared viewers **cannot** send new messages or modify the thread.

### Best Practice: Session as Documentation

A well-structured Genie Code session IS documentation. If you:
- Start with clear intent ("I'm building X because Y")
- Make decisions explicit ("I chose A over B because...")
- End with a session summary

...then sharing that session teaches others both the *what* and the *why*.

---

## Quick Reference: CLI Gotchas

### Secrets (Positional Arguments)

```bash
# CORRECT — positional
databricks secrets put-secret my-scope my-key --string-value "my-value"

# WRONG — these flags don't exist
databricks secrets put-secret --scope my-scope --key my-key

# Alternative — JSON body
databricks secrets put-secret --json '{"scope":"my-scope","key":"my-key","string_value":"my-value"}'
```

### Lakebase (Full Resource Paths)

```bash
# Always full resource path
databricks postgres get-project projects/<project-id>
databricks postgres list-endpoints projects/<project-id>/branches/production
```

---

## Anti-Patterns to Avoid

| Anti-Pattern | Why It Fails | Better Approach |
| --- | --- | --- |
| Putting everything in `.assistant_instructions.md` | Bloated, cross-project conflicts | Use PROJECT_MEMORY.md per project |
| Working directly on `main` | No review, hard to undo mistakes | Always feature branch |
| Re-explaining architecture every session | Wastes time, inconsistent | Write it once in PROJECT_MEMORY.md |
| Using notebook editor for file creation | Wrong toolset, no git integration | Use git folder editor |
| Ignoring column comments in UC | Genie Code can't understand your schema | Always add comments to tables/columns |
| Skipping session summaries | Cold start every session | 2 minutes now saves 10 minutes next time |
| Loading all skills always | Noise, potential conflicts | Audit skills per project |
| Hardcoding values in bundle YAML | Breaks across environments | Use variables and resource references |
