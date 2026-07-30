# Genie Code: Building Data Products from A to Z

> **Date:** August 6, 2026  
> **Duration:** ~120 minutes  
> **Instructor:** Matt Giglia (matthew.giglia@databricks.com)  
> **Product Area:** Genie

---

## Overview

Genie Code is so much more than just a single coding agent like Claude or Codex. Furthermore, for many of our customers it may be the first and only tool they'll use to start vibe coding due to cost or regulation. Learn the right way to use Genie Code including using the appropriate Databricks Editor, when to use skills, sharing sessions, creating session summaries for long term project memory, MCP servers, providing business context and using the power of Unity Catalog to enhance the vibe coding experience.

**We'll build a complete data product from start to finish using only Genie Code.**

## Three Takeaways

1. **Genie Code is the best tool to use for building in Databricks** — it's not just a coding agent, it's a platform-aware partner with deep Unity Catalog integration
2. **Learn how to effectively use Genie Code** so that you can better demo with it and teach it to your customers
3. **Context is the most important part of Genie Code** — use the power of Databricks to build tools that Genie Code itself can use

---

## Agenda

| # | Topic | Duration | Type |
| --- | --- | --- | --- |
| 1 | Resetting Genie Code (skills evaluation, MCP server setup) | 10 min | Setup |
| 2 | Databricks Editors for Genie Code Context | 10 min | Conceptual |
| 3 | Sharing Genie Code Sessions | 5 min | Conceptual |
| 4 | Proper Declarative Automation Bundle Setup | 15 min | Architecture |
| 5 | Architectural Plans, Project Memory & Session Summaries | 10 min | Architecture |
| 6 | **Vibe Session 1:** Infrastructure for AI and Apps | 30 min | Hands-on |
| 7 | **Vibe Session 2:** AI Search Endpoints | 15 min | Hands-on |
| 8 | Introduction to Databricks AppKit | 5 min | Conceptual |
| 9 | **Vibe Session 3:** Databricks Apps with Genie Code | 20 min | Hands-on |

---

## The Use Case: WanderBricks Intelligence Platform

We'll build a complete data + AI + app stack for **WanderBricks**, a vacation rental platform. The source data lives in `samples.wanderbricks` (available on all Databricks workspaces — no setup required).

**What we're building:**

| Session | Deliverable |
| --- | --- |
| Vibe Session 1 | Schemas, Volumes, SDP Pipelines (bronze→silver→gold), Metric Views, Genie Agent, Lakebase Project, Feature Tables |
| Vibe Session 2 | Vector Search index on property descriptions + reviews for semantic discovery |
| Vibe Session 3 | AppKit application (property search, host dashboard, or support agent) |

**The Flywheel:** Along the way, we'll build tools that Genie Code uses to build *better* things — a business definitions index, a support resolution search, and an auto-generated data dictionary.

---

## Pre-requisites

Before the workshop, ensure you have:

- [ ] **Dev catalog** with `USE CATALOG` and `CREATE SCHEMA` permissions
- [ ] **Serverless compute** enabled on your workspace
- [ ] **Git credentials** configured in Databricks (Settings → Developer → Git credentials)
- [ ] **Read access** to the `samples` catalog
- [ ] **Model serving** permissions (for AI Search endpoint)
- [ ] **Databricks Apps** permissions (for Vibe Session 3)
- [ ] **Lakebase access** (for app state persistence)
- [ ] **Vector Search** endpoint access

---

## Getting Started: Branch Guide

This repo uses **long-lived lesson branches** as starting points. Each branch represents a clean state for that section of the workshop.

### For Students

1. Clone this repo to your Databricks workspace
2. Checkout the branch for your current lesson:
   ```
   git checkout lesson/01-foundations
   ```
3. Create your personal feature branch:
   ```
   git checkout -b <your-name>-genie-<session>
   ```
   Example: `jane-genie-vibe-infra`
4. Work with Genie Code from there!

### Branch Map

| Branch | Start Here For | What's Already Done |
| --- | --- | --- |
| `lesson/01-foundations` | Topics 1–5 (setup, editors, sharing, bundles, project memory) | Documentation only |
| `lesson/02-vibe-infra` | Topic 6 (Vibe Session 1: Infrastructure) | Empty bundle scaffold + PROJECT_MEMORY.md |
| `lesson/03-vibe-ai` | Topic 7 (Vibe Session 2: AI Search) | Infra fully built + deployed |
| `lesson/04-vibe-apps` | Topics 8–9 (AppKit + Vibe Session 3: Apps) | AI search endpoint running |
| `main` | Reference only | Complete answer key — everything finished |

> **Never work directly on `main` or the `lesson/*` branches.** Always create a personal feature branch.

---

## Repository Structure

```
genieCodeWorkshop/
├── README.md                          # This file
├── PROJECT_MEMORY.md                  # Architectural decisions & workshop plan
├── LICENSE                            # MIT
├── docs/
│   ├── conventions/                   # Best practices reference
│   │   └── genie-code-best-practices.md
│   ├── 01-foundations/                # Lesson 1 guides
│   ├── 02-vibe-infra/                 # Lesson 2 guides
│   ├── 03-vibe-ai/                    # Lesson 3 guides
│   ├── 04-vibe-apps/                  # Lesson 4 guides
│   └── reference/
│       └── wanderbricks-analytics-handbook.md
├── media/
│   ├── screenshots/
│   │   ├── setup/
│   │   ├── editors/
│   │   ├── bundles/
│   │   └── vibe-sessions/
│   └── diagrams/
├── workshop-infra/                    # Instructor pre-setup (deploy before class)
│   ├── databricks.yml
│   └── src/
└── wanderbricks-platform/             # Student bundle (grows across sessions)
    ├── databricks.yml
    ├── src/
    └── fixtures/
        └── sessions/
```

---

## Reference Materials

- [Best Practices & Conventions](docs/conventions/genie-code-best-practices.md) — comprehensive guide to all patterns taught in this workshop
- [WanderBricks Analytics Handbook](docs/reference/wanderbricks-analytics-handbook.md) — business definitions and KPIs (also used as the "tool-building" demo)
- [PROJECT_MEMORY.md](PROJECT_MEMORY.md) — all architectural decisions for this workshop

---

## License

MIT — see [LICENSE](LICENSE)
