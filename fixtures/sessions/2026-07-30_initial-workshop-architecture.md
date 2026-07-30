# Session Summary: Initial Workshop Architecture & Planning

**Date:** 2026-07-30  
**Branch:** `mg-genie-main-project-plan`  
**PR Target:** `main`

---

## What We Accomplished

Built the entire foundational architecture for the "Genie Code: Building Data Products from A to Z" workshop (120 min, August 6, 2026). Starting from a bare repo (just README stub + LICENSE), we planned, decided, and scaffolded all core documents and structures.

## Decisions Made

1. **Use case:** WanderBricks Intelligence Platform (`samples.wanderbricks`, 16 tables, vacation rental domain)
2. **Branch strategy:** Long-lived `lesson/*` branches as student starting points, feature branches for authoring (`mg-genie-L0X-*`), periodic reconciliation
3. **Student bundle name:** `wanderbricks-platform` (grows across all vibe sessions, distinct from `workshop-infra`)
4. **Flywheel concept:** Three tools (Analytics Handbook, Support Corpus, Data Dictionary) PLUS the centerpiece — the AI Search endpoint built in Vibe Session 2 becomes Genie Code's design partner in Vibe Session 3
5. **Bundle Editor emphasis:** The Bundle Editor is the most important editor for this training — every vibe session starts there (define WHAT as resources) before moving to other editors (write HOW in code)
6. **Repo-level session summaries:** `fixtures/sessions/` at repo root tracks the BUILD of the workshop (our authoring memory), separate from bundle-level `fixtures/sessions/` that students create during the workshop
7. **`main` = complete answer key** — students never work on it, always branch from `lesson/*`

## Files Created

| File | Purpose |
| --- | --- |
| `PROJECT_MEMORY.md` | Comprehensive architectural plan (agenda, use case, flywheel, branches, folder structure, pre-reqs, decisions, open questions) |
| `README.md` (expanded) | Full workshop landing page (title, description, takeaways, timed agenda, use case, pre-reqs checklist, branch guide, repo structure, blog link) |
| `docs/conventions/genie-code-best-practices.md` | All conventions reference (context principle, git workflow, project memory, session summaries, editor choice, skills, MCP, DAB, SDP, flywheel, anti-patterns) |
| `docs/reference/wanderbricks-analytics-handbook.md` | 10-section business definitions doc (revenue, occupancy, satisfaction, host performance, operations, engagement, inventory, geo, DQ rules, reporting cadence) |
| `workshop-infra/databricks.yml` | Minimal instructor pre-setup bundle (catalog var, schema resource) |
| `workshop-infra/README.md` | Bundle purpose and deployment docs |
| `workshop-infra/src/.gitkeep` | Placeholder for future notebooks |
| `fixtures/sessions/INDEX.md` | This session index |
| `fixtures/sessions/2026-07-30_initial-workshop-architecture.md` | This file |

## Key Insights from This Session

* **The "aha moment" is not the handbook** (static definitions). It's the AI Search endpoint — a live production data product that becomes Genie Code's design partner. The thing you build IS the context for building the next thing.
* **`samples.wanderbricks` is ideal** because it has: nested/complex types (support logs, clickstream), free text (descriptions, reviews, messages), geo data, temporal data, and a universally understood domain.
* **The Analytics Handbook is dual-purpose:** It's both workshop reference material AND the actual artifact students ingest/index to demonstrate the tool-building flywheel.
* **Blog validation:** The July 2026 Databricks AI Research blog (400+ tasks, most accurate + cheapest) directly supports Takeaway #1 with real data.

## Open Items for Next Session

* Create `lesson/01-foundations` branch (first long-lived branch)
* Decide: AppKit app variant for Vibe Session 3 (property search? host dashboard? support agent?)
* Plan support corpus indexing approach (how to flatten/chunk `customer_support_logs`)
* Consider: do we need sample files in a Volume for Auto Loader demos?
* Write `docs/01-foundations/` lesson content (resetting skills, editor context, sharing sessions)

## Commits (7 total on `mg-genie-main-project-plan`)

1. `docs: add PROJECT_MEMORY.md with comprehensive workshop plan`
2. `docs: add conventions guide, expanded README, and analytics handbook`
3. `docs: add Databricks AI Research blog link to README`
4. `docs: add 'Centerpiece' section to PROJECT_MEMORY flywheel`
5. `infra: stub workshop-infra bundle`
6. `docs: add Bundle Editor to editor choice table`
7. `docs: elevate Bundle Editor as central editor for workshop`
