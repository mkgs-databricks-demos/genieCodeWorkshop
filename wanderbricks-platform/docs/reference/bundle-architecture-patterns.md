# Bundle Architecture Patterns

> **Source repos:** [lakeLoom](https://github.com/mkgs-databricks-demos/lakeLoom) | [cleanRooms](https://github.com/mkgs-databricks-demos/cleanRooms)  
> **Purpose:** Reference patterns for structuring Declarative Automation Bundles. Students with GitHub MCP can browse the source repos for full implementation details.

---

## 1. Multi-Bundle Architecture

**Pattern:** Split infrastructure from application into separate bundles deployed in dependency order.

```
project-root/
├── deploy.sh                    # Orchestrates both bundles
├── <project>-infra/             # Deploy FIRST
│   ├── databricks.yml
│   ├── resources/               # One file per resource
│   └── src/                     # Bootstrap/setup notebooks
└── <project>-app/               # Deploy SECOND (depends on infra)
    ├── databricks.yml
    ├── resources/
    └── src/                     # Application code
```

**Why separate:**
- Infra changes rarely; app changes often
- Different permission models (infra needs admin-level grants)
- Clear dependency ordering (app references infra outputs)
- Destroy safety — can tear down app without losing infra

**lakeLoom example:**
- `lakeloom-infra/` — UC schema, volumes, SQL warehouse, Lakebase project, secret scope, bootstrap job
- `lakeloom-ai/` — AppKit application (React + Node.js), app permissions, env var bindings

---

## 2. Resource File Conventions

### One Resource Per File

Each resource gets its own YAML file in a `resources/` directory:

```
resources/
├── brick_support.schema.yml
├── support_warehouse.sql_warehouse.yml
├── brick_support.lakebase.yml
├── brick_support.secret_scope.yml
├── raw_data.volume.yml
├── platform_bootstrap.job.yml
└── support_pipeline.pipeline.yml
```

### Naming Convention

```
<logical_name>.<resource_type>.yml
```

Examples: `lakeloom.schema.yml`, `infra_warehouse.sql_warehouse.yml`, `documents.volume.yml`

### Include Globs in databricks.yml

```yaml
bundle:
  name: "my-bundle"

include:
  - resources/*.schema.yml
  - resources/*.secret_scope.yml
  - resources/*.sql_warehouse.yml
  - resources/*.job.yml
  - resources/*.yml
  - resources/*/*.yml
```

---

## 3. Schema Reference Convention

**Rule:** Only the schema resource file references `${var.catalog}` and `${var.schema}` directly. ALL other resources reference the schema through deployed-resource substitutions.

### Schema Resource (the ONLY place vars are used directly)

```yaml
# resources/brick_support.schema.yml
resources:
  schemas:
    brick_support_schema:
      name: ${var.schema}
      catalog_name: ${var.catalog}
      comment: "Support operations schema for WanderBricks."
      grants:
        - principal: account users
          privileges:
            - USE_SCHEMA
```

### Every Other Resource (uses deployed-resource refs)

```yaml
# Correct — bound to actual deployed object
warehouse_id: ${resources.sql_warehouses.support_warehouse.id}
catalog_name: ${resources.schemas.brick_support_schema.catalog_name}
schema_name: ${resources.schemas.brick_support_schema.name}

# WRONG — loosely coupled, can drift
warehouse_id: ${var.warehouse_id}
catalog_name: ${var.catalog}
schema_name: ${var.schema}
```

**Why:** Guarantees references are bound to actual deployed objects. Enforces dependency ordering — DABs knows the schema must deploy before resources that reference it.

---

## 4. Metric Views via Dynamic SQL

**Pattern:** Define metric views as YAML files in `fixtures/metric_views/`, deploy them with a notebook that reads, templates, and executes `CREATE OR REPLACE VIEW ... WITH METRICS`.

### Directory Structure

```
<bundle>/
├── fixtures/
│   └── metric_views/
│       ├── mv_support_tickets.metric_view.yml
│       ├── mv_resolution_time.metric_view.yml
│       └── mv_agent_performance.metric_view.yml
└── src/
    └── metric_views/
        └── create-metric-views.ipynb
```

### Metric View YAML Format

Filename: `<view_name>.metric_view.yml`

```yaml
version: 1.1
source: "{catalog}.{schema}.support_tickets_gold"
joins:
  - name: agents
    source: "{catalog}.{schema}.support_agents"
    "on": source.agent_id = agents.agent_id
comment: "Support ticket analytics metric view"
dimensions:
  - name: ticket_date
    expr: created_date
    comment: Date when the support ticket was created
    display_name: Ticket Date
    format:
      type: date
      date_format: locale_short_month
      leading_zeros: false
    synonyms:
      - date of ticket
      - support date
  - name: issue_category
    expr: category
    comment: Type of support issue
    display_name: Issue Category
    synonyms:
      - ticket type
      - issue type
measures:
  - name: total_tickets
    expr: count(ticket_id)
    comment: Total number of support tickets
    display_name: Total Tickets
    format:
      type: number
      decimal_places:
        type: exact
        places: 0
      abbreviation: compact
    synonyms:
      - ticket count
      - number of tickets
  - name: avg_resolution_hours
    expr: avg(resolution_time_hours)
    comment: Average time to resolve tickets in hours
    display_name: Avg Resolution Time (hrs)
    format:
      type: number
      decimal_places:
        type: max
        places: 1
    synonyms:
      - average resolution time
      - mean time to resolve
  - name: tickets_per_agent
    expr: MEASURE(total_tickets) / count(distinct agent_id)
    comment: Average tickets handled per agent
    display_name: Tickets per Agent
    format:
      type: number
      decimal_places:
        type: max
        places: 1
materialization:
  schedule: EVERY 1 DAY
  mode: relaxed
  materialized_views:
    - name: daily_summary
      type: aggregated
      dimensions:
        - ticket_date
        - issue_category
      measures:
        - total_tickets
        - avg_resolution_hours
```

**Key elements:**
- `{catalog}.{schema}` placeholders in `source` and `joins` (Python `.format()` at runtime)
- `dimensions` with `expr`, `comment`, `display_name`, `format`, `synonyms`
- `measures` with aggregate expressions; derived measures use `MEASURE(other_measure)`
- `materialization` with schedule, mode, and pre-aggregated materialized views

### Deployment Notebook Pattern

The notebook receives `catalog_use` and `schema_use` as widget parameters from the job:

```python
# Cell 1: Get parameters
catalog_use = dbutils.widgets.get("catalog_use")
schema_use = dbutils.widgets.get("schema_use")
```

```python
# Cell 2: Find and process YAML metric view definitions
import os
from pathlib import Path

metric_views_path = Path(os.path.abspath("../../fixtures/metric_views"))
yml_files = list(metric_views_path.glob("*.yml"))

for yml_file in yml_files:
    with open(yml_file, 'r') as f:
        yaml_content = f.read()

    # Substitute catalog/schema placeholders
    yaml_content = yaml_content.format(
        catalog=catalog_use,
        schema=schema_use
    )

    # Extract view name from filename (remove .metric_view.yml)
    view_name = yml_file.stem.replace(".metric_view", "")
    full_view_name = f"{catalog_use}.{schema_use}.{view_name}"

    # Execute CREATE OR REPLACE
    create_sql = f"""CREATE OR REPLACE VIEW {full_view_name}
WITH METRICS
LANGUAGE YAML
AS $
{yaml_content}
$"""
    spark.sql(create_sql)
    print(f"  ✓ Created {full_view_name}")
```

### Job Task for Metric Views

```yaml
# In the job resource YAML
- task_key: deploy_metric_views
  depends_on:
    - task_key: pipeline_complete
  notebook_task:
    notebook_path: ../src/metric_views/create-metric-views.ipynb
    source: WORKSPACE
    warehouse_id: ${resources.sql_warehouses.support_warehouse.id}
    base_parameters:
      catalog_use: "{{job.parameters.catalog_use}}"
      schema_use: "{{job.parameters.schema_use}}"
  environment_key: default
```

---

## 5. Lakebase Project Resource

```yaml
# resources/brick_support.lakebase.yml
resources:
  postgres_projects:
    brick_support_lakebase:
      project_id: ${var.lakebase_project_id}
      display_name: "BrickSupport [${bundle.target}]"
      description: "OLTP database for support app state and ticket management."
      postgres_version: POSTGRES_17
      default_endpoint_settings:
        autoscaling:
          min_capacity_cu: 0.5
          max_capacity_cu: 4
```

**Post-deploy manual steps (no DAB resource type):**
1. Enable Data API (optional — for external REST clients)
2. Register in Unity Catalog (optional — enables SQL warehouse queries)

**Connection model:** AppKit's Lakebase plugin connects via direct Postgres wire protocol (port 5432) using OAuth token rotation. Platform injects `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER` env vars automatically.

---

## 6. Secret Scope Resource

```yaml
# resources/brick_support.secret_scope.yml
resources:
  secret_scopes:
    brick_support_secret_scope:
      name: ${var.secret_scope_name}
      backend_type: DATABRICKS
      lifecycle:
        prevent_destroy: true

targets:
  dev:
    resources:
      secret_scopes:
        brick_support_secret_scope:
          permissions:
            - user_name: ${var.run_as_user}
              level: MANAGE
```

**Key conventions:**
- Secret key names are schema-qualified to avoid collisions (e.g., `client_id_dev_matthew_giglia_brick_support`)
- `prevent_destroy: true` prevents accidental deletion
- Per-target permissions (dev gets user MANAGE, prod gets SPN MANAGE)

---

## 7. SQL Warehouse Resource

```yaml
# resources/support_warehouse.sql_warehouse.yml
resources:
  sql_warehouses:
    support_warehouse:
      name: "BrickSupport Infra [${bundle.target}]"
      cluster_size: "2X-Small"
      warehouse_type: PRO
      enable_serverless_compute: true
      enable_photon: true
      channel:
        name: CHANNEL_NAME_PREVIEW
      auto_stop_mins: 10
      min_num_clusters: 1
      max_num_clusters: 1
```

**Referenced by other resources as:** `${resources.sql_warehouses.support_warehouse.id}`

---

## 8. Volume Resource

```yaml
# resources/raw_data.volume.yml
resources:
  volumes:
    raw_data:
      catalog_name: ${resources.schemas.brick_support_schema.catalog_name}
      schema_name: ${resources.schemas.brick_support_schema.name}
      name: raw_data
      volume_type: MANAGED
      comment: "Raw support data files for Auto Loader ingestion."
```

---

## 9. Bootstrap Job Pattern

A job that sets up prerequisites after bundle deploy — idempotent and safe to re-run:

```yaml
# resources/platform_bootstrap.job.yml
resources:
  jobs:
    platform_bootstrap:
      name: "BrickSupport — Platform Bootstrap [${bundle.target}]"
      description: "Bootstraps platform prerequisites. Idempotent."
      parameters:
        - name: catalog_use
          default: ${resources.schemas.brick_support_schema.catalog_name}
        - name: schema_use
          default: ${resources.schemas.brick_support_schema.name}
      environments:
        - environment_key: default
          spec:
            environment_version: "5"
      tasks:
        - task_key: create_tables
          notebook_task:
            notebook_path: ../src/platform_bootstrap/target-tables-ddl.ipynb
            source: WORKSPACE
            warehouse_id: ${resources.sql_warehouses.support_warehouse.id}
            base_parameters:
              catalog_use: "{{job.parameters.catalog_use}}"
              schema_use: "{{job.parameters.schema_use}}"
        - task_key: deploy_metric_views
          depends_on:
            - task_key: create_tables
          notebook_task:
            notebook_path: ../src/metric_views/create-metric-views.ipynb
            source: WORKSPACE
            warehouse_id: ${resources.sql_warehouses.support_warehouse.id}
            base_parameters:
              catalog_use: "{{job.parameters.catalog_use}}"
              schema_use: "{{job.parameters.schema_use}}"
        - task_key: grant_volume_access
          depends_on:
            - task_key: create_tables
          for_each_task:
            inputs: '["raw_data", "checkpoints"]'
            concurrency: 3
            task:
              task_key: grant_single_volume
              notebook_task:
                notebook_path: ../src/platform_bootstrap/grant-volume-access.ipynb
                source: WORKSPACE
                warehouse_id: ${resources.sql_warehouses.support_warehouse.id}
                base_parameters:
                  catalog_use: "{{job.parameters.catalog_use}}"
                  schema_use: "{{job.parameters.schema_use}}"
                  volume_name: "{{input}}"
      max_concurrent_runs: 1
      timeout_seconds: 900
```

**Key patterns:**
- Job-level `parameters` with defaults from resource refs
- Tasks reference params via `{{job.parameters.*}}`
- `for_each_task` for iterating over volumes/resources
- `warehouse_id` on SQL notebook tasks
- `environment_key` for serverless Python tasks

---

## 10. databricks.yml Master Template

```yaml
bundle:
  name: "wanderbricks-platform"

include:
  - resources/*.yml
  - resources/*/*.yml

variables:
  catalog:
    description: "Unity Catalog catalog for WanderBricks resources."
  schema:
    description: "Schema name (used ONLY by the schema resource)."
    default: brick_support
  run_as_user:
    description: "User or SPN for job execution."
  secret_scope_name:
    description: "Secret scope for app credentials."
    default: brick_support_credentials
  lakebase_project_id:
    description: "Lakebase project ID (target-specific)."
    default: brick-support
  serverless_environment_version:
    description: "Serverless environment version."
    default: "5"

targets:
  dev:
    mode: development
    default: true
    workspace:
      host: https://<workspace-url>
      root_path: /Workspace/Users/${var.run_as_user}/.bundle/${bundle.name}/${bundle.target}
    variables:
      catalog: ""        # Set per student
      schema: brick_support
      run_as_user: ""    # Set per student
      lakebase_project_id: dev-<initials>-brick-support
```

---

## GitHub MCP Quick Reference

Students can browse the full source repos for additional implementation details:

```
# Multi-bundle pattern (infra + app + deploy.sh)
Repo: mkgs-databricks-demos/lakeLoom
Key paths:
  - lakeloom-infra/databricks.yml
  - lakeloom-infra/resources/   (schema, lakebase, secret_scope, warehouse, volumes, job)
  - deploy.sh

# Metric views with dynamic SQL
Repo: mkgs-databricks-demos/cleanRooms
Key paths:
  - basic_clean_room/fixtures/metric_views/mv_visits.metric_view.yml
  - basic_clean_room/src/sample_data_generation/create metric views.ipynb
  - basic_clean_room/resources/basic_clean_room_generate_sample_data.job.yml
```