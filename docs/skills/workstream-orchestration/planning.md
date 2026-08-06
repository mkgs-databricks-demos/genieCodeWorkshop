# Planning: Project Decomposition for Autonomous Execution

## The Decomposition Process

### Step 1: Identify Deliverables

List every distinct artifact the project produces. These are your candidate workstreams:
- Pipelines (bronze/silver/gold layers)
- Metric views or aggregate tables
- ML feature tables
- Genie spaces or AI agents
- Dashboard resources
- App scaffolds
- Infrastructure (schemas, volumes, secrets)

### Step 2: Map Dependencies

For each deliverable, ask: "What must exist BEFORE this can run?"

Dependencies fall into three types:

| Type | Signal | Example |
| --- | --- | --- |
| Table-gated | Output table exists with rows (SQL COUNT > 0) | Gold tables before metric views |
| Resource-gated | Bundle resource deployed successfully | Schema before pipeline |
| Status-gated | Upstream status file says COMPLETE | Any sequential dependency |

**Prefer table-gated** when possible. It decouples execution from code review
and is the most reliable signal (a table either has rows or it doesn't).

### Step 3: Draw the DAG

Visualize as a directed acyclic graph:

```
WS-0 (foundation)
    └→ WS-A (data layer)
        ├→ WS-B (analytics)      ← these are parallel
        │       └→ WS-C (consumer)
        └→ WS-D (ML features)    ← these are parallel
```

Rules:
- Single root node (the foundation workstream)
- Fan-out after the root = parallelism opportunity
- Fan-in before a consumer = sequential dependency
- Terminal node = WS-FINAL (always)

### Step 4: Verify File Isolation

The **non-negotiable rule**: two parallel workstreams CANNOT edit the same file.

Check by listing each workstream's output directories:

| Workstream | Creates/Modifies |
| --- | --- |
| WS-A | `src/pipelines/`, `resources/pipeline.yml` |
| WS-B | `src/sql/`, `resources/metrics.yml` |
| WS-D | `src/features/`, `resources/features.yml` |

If two workstreams touch the same file, either:
1. Make them sequential (add a dependency edge)
2. Restructure so each owns different files
3. Merge them into one workstream

### Step 5: Size Each Workstream

**Target: 15–60 minutes of agent work per workstream.**

| Too Small (<15 min) | Right Size (15–60 min) | Too Large (>60 min) |
| --- | --- | --- |
| Create one YAML file | Build a 3-layer pipeline | Build entire platform |
| Add one table | Create metric views + job | Pipeline + metrics + features |
| Overhead dominates | Good balance | Session timeout risk |

If a workstream is too large, split it along natural boundaries:
- Pipeline: split by layer (bronze, silver, gold)
- Large model: split by training vs. serving
- Complex app: split by backend vs. frontend

If too small, merge with an adjacent workstream that shares the same dependency.

## Concurrency Identification

Two workstreams can run in parallel when:
1. They share the same upstream dependency (fan-out)
2. They touch different files (no merge conflicts)
3. Neither produces tables the other needs as INPUT

In the DAG, parallel workstreams appear as siblings under the same parent.

## Naming Your Workstreams

Use letter codes for ordering, descriptions for clarity:

```
WS-A: Pipeline (bronze→silver→gold)
WS-B: Metric Views
WS-C: Genie Agent
WS-D: Feature Tables
WS-FINAL: Summary & Merge Instructions
```

The letter determines execution priority (A before B) and makes the
dependency graph easy to discuss verbally.

## Common Patterns

### The "Data Platform" Pattern
```
WS-0 (infra: schema, volumes, secrets)
    └→ WS-A (pipeline: ingest → transform → serve)
        ├→ WS-B (analytics: metrics, dashboards)
        ├→ WS-C (AI: agents, Genie spaces)
        └→ WS-D (ML: feature tables, models)
```

### The "Microservices" Pattern
```
WS-0 (shared infra: API gateway, auth)
    ├→ WS-A (service 1)
    ├→ WS-B (service 2)
    └→ WS-C (service 3)
        └→ WS-D (integration tests across all)
```

### The "Migration" Pattern
```
WS-0 (schema setup + source analysis)
    └→ WS-A (convert batch 1: tables 1–10)
    └→ WS-B (convert batch 2: tables 11–20)
    └→ WS-C (convert batch 3: tables 21–30)
        └→ WS-D (validation + reconciliation)
```

## Decision Tree: "Should These Be Separate Workstreams?"

```
Do they touch the same files?
    YES → Same workstream (or make sequential)
    NO → 
        Does one need the other's output tables?
            YES → Sequential (downstream gates on upstream)
            NO →
                Combined work > 60 min?
                    YES → Separate workstreams (parallel)
                    NO → Consider merging (less overhead)
```
