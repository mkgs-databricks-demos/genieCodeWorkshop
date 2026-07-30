# Genie Code Best Practices & Conventions

> These conventions have been developed through extensive production use of Genie Code across multiple Databricks projects. They represent patterns that maximize Genie Code's effectiveness by providing consistent context, reducing re-explanation, and enabling long-term project continuity.

---

## Table of Contents

**Foundations**
1. [The Context Principle](#the-context-principle)
2. [Git Workflow](#git-workflow)
3. [Project Memory](#project-memory)
4. [`.assistant_instructions.md` vs `PROJECT_MEMORY.md`](#assistant_instructionsmd-vs-project_memorymd)
5. [Session Summaries](#session-summaries)
6. [Sharing Genie Code Sessions](#sharing-genie-code-sessions)

**Editors & Context**
7. [Choosing the Right Editor](#choosing-the-right-editor)
8. [Unity Catalog as Context](#unity-catalog-as-context)
9. [Naming for Discoverability](#naming-for-discoverability)
10. [Skills Management](#skills-management)
11. [MCP Servers](#mcp-servers)
12. [Genie Spaces & Agents](#genie-spaces--agents)

**Building**
13. [Declarative Automation Bundle Conventions](#declarative-automation-bundle-conventions)
14. [Deployment Script Conventions](#deployment-script-conventions)
15. [Spark Declarative Pipeline Conventions](#spark-declarative-pipeline-conventions)
16. [The Flywheel: Building Tools for Genie Code](#the-flywheel-building-tools-for-genie-code)

**Collaboration & Patterns**
17. [Cross-Domain Collaboration Folders](#cross-domain-collaboration-folders)
18. [Working with Genie Code: Interaction Patterns](#working-with-genie-code-interaction-patterns)

**Reference**
19. [Platform Gotchas](#platform-gotchas)
20. [Quick Reference: CLI Gotchas](#quick-reference-cli-gotchas)
21. [Anti-Patterns to Avoid](#anti-patterns-to-avoid)

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
# Branch naming pattern
<initials>-genie-<short-description>

# Examples
mg-genie-phase6-shutdown-polish
jd-genie-add-metrics-pipeline
sk-genie-fix-auth-flow
```

Use your own initials. The `-genie-` infix signals this is a Genie Code-assisted branch (useful for team awareness and filtering).

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

## Decisions
- [Architectural choices and rationale]

## Changes Made
- `path/to/file.py` — [what changed and why]
- `path/to/other.yml` — [what changed and why]
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
| **Bundle Editor** | Full DAB topology, resource definitions, variable interpolation, target management, dependency graph awareness | DAB configuration, resource wiring, multi-target setup, architectural decisions |

### Why the Bundle Editor Is the Most Important Editor

For building data products, the Bundle Editor deserves special emphasis. When you open `databricks.yml`, Genie Code gains:

* **Full architectural visibility** — every resource (schemas, jobs, pipelines, volumes, endpoints) and how they relate
* **Dependency graph awareness** — understands that a job depends on a schema, which depends on a catalog variable
* **Variable interpolation context** — sees `${var.*}`, `${resources.*}`, and target overrides as a connected system
* **Multi-target understanding** — knows dev vs. prod configurations and can reason about promotion
* **Resource type expertise** — knows the full YAML schema for each resource type

This is the editor where "context is everything" becomes tangible. A single `databricks.yml` gives Genie Code more architectural context than a dozen separate files ever could. Start here — define WHAT to build (resources in YAML) — then move to other editors to write HOW (code in notebooks, pipelines, apps).

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

## Unity Catalog as Context

Unity Catalog metadata is Genie Code's richest source of automatic context. Every table description, column comment, and governance tag is visible without any extra setup.

### Column Comments Are Not Optional

Column comments are the single highest-ROI action for Genie Code effectiveness:

```sql
ALTER TABLE bookings ALTER COLUMN total_amount COMMENT 'Total amount paid by guest in USD, including cleaning fees and service charges. Does not include platform commission.';
ALTER TABLE bookings ALTER COLUMN status COMMENT 'Booking lifecycle status: pending, confirmed, cancelled_by_guest, cancelled_by_host, completed';
```

**Why:** Genie Code reads these comments when exploring tables. A comment like `'Booking lifecycle status: pending, confirmed, cancelled_by_guest, cancelled_by_host, completed'` eliminates an entire exploration query that a general coding agent would need to run.

### Table Descriptions

```sql
COMMENT ON TABLE gold.host_performance IS 'Aggregated host metrics including superhost status, response time SLA compliance, and cancellation rates. Refreshed daily. Grain: one row per host per evaluation period.';
```

**Include:** What the table contains, the grain, refresh cadence, and key business context.

### Schema-Level Documentation

```sql
COMMENT ON SCHEMA wanderbricks_gold IS 'Business-ready analytics tables for the WanderBricks platform. All tables are metric views or aggregated facts suitable for dashboards and Genie Spaces.';
```

### Tags for Governance AND Context

Unity Catalog tags serve double duty — governance compliance AND Genie Code context:

```sql
ALTER TABLE bookings SET TAGS ('pii' = 'true', 'domain' = 'revenue', 'tier' = 'gold');
```

Genie Code sees these tags and can make informed decisions about data sensitivity, domain ownership, and quality tier without asking.

---

## Naming for Discoverability

Genie Code searches and matches semantically. How you name things directly affects how well it finds and understands them.

### Table Naming

| Pattern | Example | Why |
| --- | --- | --- |
| `<domain>_<entity>` | `revenue_bookings_daily` | Domain prefix groups related tables |
| `<tier>_<entity>` | `gold_host_performance` | Tier prefix signals data quality/readiness |
| Avoid abbreviations | `customer_support_logs` not `cust_supp_logs` | Genie Code matches natural language |
| Pluralize entities | `bookings`, `reviews`, `properties` | Matches how humans describe data |

### Column Naming

* Use `_id` suffix for foreign keys (`property_id`, `user_id`) — Genie Code infers join paths
* Use `_at` suffix for timestamps (`created_at`, `updated_at`) — signals temporal columns
* Use `_count`, `_amount`, `_rate` for measures — signals aggregation intent
* Avoid generic names (`value`, `data`, `info`, `type`) without a prefix

### Schema Naming

* `<project>_bronze` / `<project>_silver` / `<project>_gold` — medallion is universally understood
* Or `<project>_raw` / `<project>_curated` / `<project>_analytics` — alternative that's equally clear
* Per-developer schemas for isolation: `dev_<username>_<project>`

---

## Genie Spaces & Agents

### What Are They?

Genie Spaces (formerly AI/BI Genie) provide natural language analytics over specific tables. They're also the foundation for building domain-specific agents that Genie Code can interact with.

### Setting Up a Genie Space for Best Results

**Table selection:**
* Include ONLY tables relevant to the space's domain (fewer, focused tables > many unfocused tables)
* Prefer gold/analytics tier tables with clear column comments
* Include dimension tables needed for joins

**Instructions text:**
* Define domain vocabulary ("When users say 'superhost', they mean hosts with >=4.5 avg rating AND >=10 bookings in 90 days")
* Specify default behaviors ("Always filter out cancelled bookings unless explicitly asked")
* Declare join paths ("To get destination info, join properties.destination_id = destinations.destination_id")
* Set guardrails ("Never expose guest PII. Aggregate to property or destination level.")

**Example queries:**
* Add 5-10 representative questions with their expected SQL
* Cover the main use cases the space serves
* Include edge cases (date ranges, null handling)

### Genie Spaces as Genie Code Tools

A well-configured Genie Space becomes a tool that Genie Code can use:
* Genie Code queries the space for analytics answers during app development
* The space's instructions encode business logic once, reused everywhere
* Students can test their metric views by querying them through the Genie Space

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

**Why this is powerful with Genie Code:**
- Genie Code reads a YAML config and generates a complete new pipeline source without modifying existing code paths
- Adding a new table to the pipeline is a config addition — Genie Code doesn't need to understand all existing logic
- Config files serve as documentation: Genie Code reads them to understand the full pipeline topology
- Testing is straightforward (swap config, same logic) — Genie Code can generate test configs

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

## Cross-Domain Collaboration Folders

### The Pattern

When collaborating across domains (e.g., Genie Code handles Databricks work while another tool/person handles non-Databricks work like mobile apps, front-end, or external systems), use **shared context folders** as communication channels:

```
project-root/
├── architecture/
│   ├── hi_genie/        # Context FROM collaborator TO Genie Code (read-only for Genie)
│   └── hey_collaborator/ # Progress/replies FROM Genie Code TO collaborator
```

### Rules

- **`hi_genie/`** (or equivalent inbound folder): Read-only context. Always read before substantive work. Never write to it.
- **`hey_<collaborator>/`** (or equivalent outbound folder): Where you share progress, decisions, questions back.
- Each domain owner is the source of truth for their domain.
- Both folders live at the architecture/docs level, NOT inside individual bundle directories.

### Why This Works

- Eliminates context switching — each agent/person reads a folder instead of attending meetings
- Creates an audit trail of decisions and handoffs
- Works asynchronously — no requirement for simultaneous presence
- Each collaborator works in their strongest tool (Genie Code in Databricks, another tool elsewhere)

### When to Use

- Multi-platform projects (Databricks + mobile/web/external)
- Team collaboration where different people own different layers
- Any project where context needs to flow between domains without direct integration

---

## Working with Genie Code: Interaction Patterns

### Review-Before-Commit Principle

Genie Code should show you what it's changing before finalizing edits. Expect this workflow:

1. **Navigate to the file** — so you can see the before/after in the editor
2. **Apply the edit** — changes appear in your editor for review
3. **You confirm** — by continuing the conversation or committing

**Exception:** For trivial single-line fixes on a file you're already viewing, Genie Code can edit directly.

### Guiding Principle: Tell, Don't Surprise

Train your interaction style around visibility:
- Ask Genie Code to "show me the plan" before large refactors
- For multi-file changes, request a summary of what will change
- Use session summaries to capture what DID change after the fact
- If Genie Code edits the wrong file or makes an unwanted change, the feature branch isolates it

---

## `.assistant_instructions.md` vs `PROJECT_MEMORY.md`

### Two Different Files, Two Different Purposes

| File | Scope | Contains | Lives At |
| --- | --- | --- | --- |
| `.assistant_instructions.md` | **You** (cross-project) | Personal preferences, universal conventions, brand knowledge, platform gotchas | `~/.assistant_instructions.md` (home directory) |
| `PROJECT_MEMORY.md` | **One project** | Architecture, decisions, resource IDs, environment mappings, open questions | Bundle root or repo root |

### Rule of Thumb

- If it applies to ALL your projects → `.assistant_instructions.md`
- If it applies to THIS project only → `PROJECT_MEMORY.md`
- If in doubt, put it in PROJECT_MEMORY — it's easier to promote to instructions later than to untangle project-specific info from global prefs

### What Goes Where

**`.assistant_instructions.md` (global):**
- Git workflow conventions (branch naming, never-main rule)
- Editor preferences and interaction patterns
- SDK install patterns
- CLI gotchas you've discovered
- Brand/design system references
- Collaboration folder conventions

**`PROJECT_MEMORY.md` (per-project):**
- Resource IDs and target mappings
- Architecture decisions and rationale
- Integration points and dependencies
- Team-specific naming conventions
- Deployment sequences and dependencies

---

## Deployment Script Conventions

### deploy.sh Patterns

When bundles need shell-based deployment orchestration:

```bash
# safe_url() — minimal encoding for URLs (encodes spaces, preserves structure)
safe_url() {
  echo "$1" | sed 's/ /%20/g'
}

# safe() — full URL-encoding for non-URL values (secret values, names with special chars)
safe() {
  python3 -c "import urllib.parse; print(urllib.parse.quote('$1', safe=''))"
}
```

**When to use which:**
- `safe_url()` for workspace host URLs where you only need to handle spaces (preserves `://`, `/`, etc.)
- `safe()` for values that may contain arbitrary special characters (secret values, schema names)
- Lakebase project ID: extract from `databricks bundle summary`, prepend `projects/` for CLI calls

---

## Platform Gotchas

### Databricks Apps — Authenticated Traffic

The Apps auth sidecar redirects all unauthenticated requests (HTTP 302). This means:
- `executeCode` / `curl` from notebooks **always fail** against app endpoints
- Plain Bearer tokens → 403
- Must use notebook with `WorkspaceClient().config.authenticate()` headers

```python
from databricks.sdk import WorkspaceClient
import requests

wc = WorkspaceClient()
headers = {}
wc.config.authenticate(headers)  # Injects proper auth
response = requests.get(f"{app_url}/api/health", headers=headers)
```

### SQL Editor Queries API

Saved SQL queries are UUID-based, managed via `/api/2.0/sql/queries` (NOT the workspace file API). To relocate a query:
1. POST new query with desired `parent_path`
2. Delete old query

You cannot simply "move" them like workspace files.

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
