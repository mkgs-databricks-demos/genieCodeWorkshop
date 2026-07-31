# WanderBricks Platform

A Databricks Asset Bundle (DAB) that manages the complete WanderBricks data platform — from raw ingestion through gold-layer analytics, AI search, and a user-facing application.

## Quick Start

```bash
# 1. Set your catalog in databricks.yml (targets.dev.variables.catalog)
# 2. Validate the bundle
databricks bundle validate

# 3. Deploy schemas
databricks bundle deploy

# 4. Start building with Genie Code!
```

## Structure

```
wanderbricks-platform/
├── databricks.yml          # Bundle definition (start here)
├── PROJECT_MEMORY.md       # Architecture & decisions
├── README.md               # This file
├── src/
│   ├── pipelines/          # SDP pipeline notebooks
│   ├── notebooks/          # Job task notebooks
│   └── includes/           # Shared Python modules
└── fixtures/
    ├── sessions/           # Genie Code session summaries
    └── config/             # Pipeline configs (YAML)
```

## Building This Bundle

This bundle is built incrementally across three Vibe Sessions:

1. **Vibe Session 1 (Infrastructure):** Schemas → Volumes → Pipelines → Jobs → Metric Views → Genie Space
2. **Vibe Session 2 (AI Search):** Vector Search endpoint over properties + reviews
3. **Vibe Session 3 (Apps):** AppKit application using the AI Search endpoint

Open `databricks.yml` in the **Bundle Editor** to get started. Genie Code has maximum context when it can see the full resource topology.

## Key Principle

> Define WHAT in `databricks.yml` (resources, variables, targets), then write HOW in `src/` (notebooks, pipelines, modules).

The Bundle Editor is your architectural starting point. Other editors (Notebook, Pipeline, Apps) are for implementation.
