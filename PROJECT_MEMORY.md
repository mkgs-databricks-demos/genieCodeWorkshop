# PROJECT_MEMORY.md — Genie Code Workshop

> **Last updated:** 2025-07-30  
> **Owner:** matthew.giglia@databricks.com  
> **Repo:** genieCodeWorkshop  
> **Workshop Date:** August 6, 2026

---

## Workshop Identity

**Title:** Genie Code: Building Data Products from A to Z  
**Duration:** ~120 minutes  
**Audience:** Databricks field engineers (SEs/SAs) who demo to customers  
**Product Area:** Genie

**Description:**  
Genie Code is so much more than just a single coding agent like Claude or Codex. Furthermore, for many of our customers it may be the first and only tool they'll use to start vibe coding due to cost or regulation. Learn the right way to use Genie Code including using the appropriate Databricks Editor, when to use skills, sharing sessions, creating session summaries for long term project memory, MCP servers, providing business context and using the power of Unity Catalog to enhance the vibe coding experience. We'll build a data product completely in Genie Code from start to finish.

**Three Takeaways:**
1. Genie Code is the best tool to use for building in Databricks
2. Learn how to effectively use Genie Code so that you can better demo with it and teach it to your customers
3. Context is the most important part of Genie Code. Use the power of Databricks to build tools to use with Genie Code

---

## Agenda (120 minutes)

| # | Topic | Type |
| --- | --- | --- |
| 1 | Resetting Genie Code (removing/evaluating skills, setting up MCP servers) | Setup |
| 2 | Databricks Editors for Genie Code Context | Conceptual |
| 3 | Sharing Genie Code Sessions | Conceptual |
| 4 | Proper Declarative Automation Bundle Setup for Data Products, AI and Applications | Architecture |
| 5 | Architectural Plans, Project Memory & Session Summaries | Architecture |
| 6 | Vibe Session 1: Infrastructure for AI and Apps (Schemas, Volumes, Data Pipelines, Workflows, Metric Views, Genie Agents, Secrets, Features, Lakebase Projects) | Hands-on |
| 7 | Vibe Session 2: AI Search Endpoints | Hands-on |
| 8 | Introduction to Databricks AppKit | Conceptual |
| 9 | Vibe Session 3: Databricks Apps with Genie Code | Hands-on |

---

## Use Case: WanderBricks Intelligence Platform

**Domain:** Vacation rental platform (Airbnb-style)  
**Source Data:** `samples.wanderbricks` (16 tables, available on all workspaces)

### Why This Dataset

* Rich relationships (star schema: properties → bookings → reviews → users → destinations)
* Complex/nested data types (arrays of structs in `customer_support_logs`, nested structs in `clickstream`)
* Free-text fields perfect for AI Search + vector indexing (descriptions, reviews, support messages)
* Geo data (lat/long on properties)
* Temporal data for time-series, forecasting, metric views
* Universally understood domain — everyone gets "vacation rentals"

### Available Tables

| Table | Key Fields | Workshop Use |
| --- | --- | --- |
| `properties` | property_id, host_id, destination_id, title, description, base_price, lat/long | Core entity, AI search, geo |
| `bookings` | booking_id, user_id, property_id, check_in/out, total_amount, status | Revenue metrics, pipeline |
| `reviews` | review_id, booking_id, property_id, comment, rating | AI search, sentiment |
| `customer_support_logs` | ticket_id, user_id, messages (array of struct), support_agent_id | Tool-building, nested ETL |
| `clickstream` | user_id, property_id, event, metadata (struct), timestamp | Behavioral pipeline |
| `users` | user_id, personal info | Dimension |
| `hosts` | host_id, host details | Dimension |
| `destinations` | destination_id, location info | Dimension |
| `countries` | country info | Dimension |
| `amenities` | amenity definitions | Dimension |
| `property_amenities` | property ↔ amenity mapping | Bridge |
| `property_images` | image URLs/metadata | Enrichment |
| `payments` | payment details | Financial metrics |
| `booking_updates` | change history | CDC/audit |
| `page_views` | page view events | Behavioral |
| `employees` | internal staff | Operational |

### What Students Build

| Vibe Session | What They Build | Key Source Tables |
| --- | --- | --- |
| 1 - Infrastructure | Schema, volumes, SDP pipeline (bronze→silver→gold), metric views (revenue, occupancy, guest satisfaction), Genie agent over gold, Lakebase for app state, feature tables | All 16 tables |
| 2 - AI Search | Vector Search index on property descriptions + review comments → semantic property discovery | `properties`, `reviews`, `destinations` |
| 3 - Apps | AppKit app (property search UI, host dashboard, or support agent) | Gold tables + vector index + Lakebase |

---

## The Flywheel: Building Tools That Make Genie Code Smarter

**Core concept:** Genie Code builds artifacts → those artifacts become tools → Genie Code uses those tools to build better things.

```
Raw context (doc/data) → Ingest → Index → UC Function → Genie Code tool → Builds smarter
```

### Tool A: WanderBricks Analytics Handbook

**What:** A business requirements document (3-5 pages) defining metrics, KPIs, business rules, SLAs.  
**Lives:** `docs/reference/wanderbricks-analytics-handbook.md` (also ingested as PDF into a Volume)  
**Example definitions:**
* Occupancy Rate = confirmed bookings / total bookable nights per property
* Superhost = ≥4.5 avg rating AND ≥10 completed bookings in trailing 90 days
* Host response time SLA = 24 hours for initial reply
* Net Revenue = total_amount − platform_fee (15%) − host_payout

**Flow:** Ingest → chunk → Vector Search index → UC function `lookup_business_definition(query)` → Genie Code tool  
**Demo moment:** Student asks Genie Code to "build the superhost metric view" — it looks up the definition from the handbook and correctly implements the threshold logic without being told.

### Tool B: Support Resolution Corpus

**What:** The `customer_support_logs` table indexed for semantic search over resolution patterns.  
**Flow:** ETL (flatten nested messages) → chunk conversations → Vector Search index → UC function `search_support_resolutions(query)`  
**Demo moment:** When building the app's support agent (Vibe Session 3), Genie Code queries "how are double-booking issues resolved?" and gets real resolution patterns to inform prompt templates.

### Tool C: Auto-Generated Data Dictionary

**What:** UC metadata (column comments, table descriptions) extracted and indexed.  
**Flow:** Query `information_schema` → generate comprehensive doc → index → Genie Code can semantically answer "which table has payment info?"  
**When:** Part of Vibe Session 1 infrastructure setup.

### The Centerpiece: AI Search Endpoint as Design Partner (Vibe Session 2 → 3)

The single biggest "aha moment" of the workshop:

1. In Vibe Session 2, students build a Vector Search endpoint over property descriptions + reviews
2. That endpoint is a **live, production data product** — a real queryable artifact
3. In Vibe Session 3, Genie Code uses that SAME endpoint as a tool to **design the app**
4. Genie Code can query it: "show me luxury properties in Florence," "what do guests complain about in apartments?" — and use the results to inform UX decisions, filtering logic, recommendation patterns

This is NOT the same as the handbook (static definitions). This is a live, evolving data product that becomes its own design partner. **The thing you build IS the context for building the next thing.**

This is the purest expression of the flywheel and Takeaway #3: "Use the power of Databricks to build tools that Genie Code itself can use."

### Layered Sequence

| When | Tool Created | Genie Code Uses It For |
| --- | --- | --- |
| Vibe Session 1 | Analytics Handbook index + Data Dictionary | Correct metric view definitions, finding tables |
| Vibe Session 2 | AI Search endpoint (properties + reviews) + Support Resolution index | Semantic understanding of inventory and issue patterns |
| Vibe Session 3 | **The AI Search endpoint IS the tool** | App design decisions — what to show, how to filter, what users care about |

---

## Branch Strategy

### Long-Lived Branches (Lesson Starting Points)

| Branch | Starting State | Students Start Here For |
| --- | --- | --- |
| `main` | Complete answer key + all docs | Reference only (never work directly on main) |
| `lesson/01-foundations` | Docs + agenda only | Topics 1–5 (setup, editors, sharing, DAB architecture, project memory) |
| `lesson/02-vibe-infra` | Empty `wanderbricks-platform` bundle scaffold + PROJECT_MEMORY.md | Topic 6 (schemas, volumes, pipelines, workflows, metrics, Genie agents, secrets, features, Lakebase) |
| `lesson/03-vibe-ai` | Infra bundle fully built + deployed state documented | Topic 7 (AI search endpoints) |
| `lesson/04-vibe-apps` | AI search ready, AppKit intro docs | Topics 8–9 (AppKit intro + app building) |

**Progression:** `lesson/01 ⊂ lesson/02 ⊂ lesson/03 ⊂ lesson/04 ⊂ main`

Each lesson branch includes all prior content completed. Reconciliation is periodic (not strict forward-merge on every PR).

### Authoring Branches (Us Building the Workshop)

```
mg-genie-L01-<description>   → PR into lesson/01-foundations
mg-genie-L02-<description>   → PR into lesson/02-vibe-infra
mg-genie-L03-<description>   → PR into lesson/03-vibe-ai
mg-genie-L04-<description>   → PR into lesson/04-vibe-apps
mg-genie-main-<description>  → PR into main
```

### Student Branches (During Workshop)

```
<first-name>-genie-<session>
```

Example: `jane-genie-vibe-infra` (branched off `lesson/02-vibe-infra`)

---

## Folder Structure

```
genieCodeWorkshop/
├── README.md                          # Agenda, pre-reqs, branch guide
├── PROJECT_MEMORY.md                  # This file — all architectural decisions
├── LICENSE                            # MIT
├── docs/
│   ├── 01-foundations/                # Lesson 1 content
│   ├── 02-vibe-infra/                 # Lesson 2 content
│   ├── 03-vibe-ai/                    # Lesson 3 content
│   ├── 04-vibe-apps/                  # Lesson 4 content
│   └── reference/
│       └── wanderbricks-analytics-handbook.md
├── media/
│   ├── screenshots/
│   │   ├── setup/
│   │   ├── editors/
│   │   ├── bundles/
│   │   └── vibe-sessions/
│   └── diagrams/
├── workshop-infra/                    # DAB: instructor pre-setup (deploy ahead of time)
│   ├── databricks.yml
│   └── src/
└── wanderbricks-platform/             # DAB: what students build (grows across lessons 2–4)
    ├── databricks.yml
    ├── src/
    └── fixtures/
        └── sessions/
```

---

## Pre-requisites (Running List)

1. Dev catalog with `USE CATALOG` + `CREATE SCHEMA` permissions
2. Workspace with serverless compute enabled
3. Git credentials configured in Databricks
4. Read access to `samples` catalog
5. Model serving permissions (for AI Search endpoint — Vibe Session 2)
6. Databricks Apps permissions (for Vibe Session 3)
7. Lakebase access (for app state persistence)
8. Vector Search endpoint access

---

## Key Naming Decisions

| Item | Name | Rationale |
| --- | --- | --- |
| Student bundle | `wanderbricks-platform` | Grows beyond just infra (pipelines → AI → app). Distinct from `workshop-infra`. |
| Instructor bundle | `workshop-infra` | Pre-setup only. Minimal. Added to as needs arise. |
| Handbook doc | `wanderbricks-analytics-handbook.md` | Clear domain prefix, lives in `docs/reference/` |
| UC functions | `lookup_business_definition()`, `search_support_resolutions()` | Descriptive, tool-oriented naming |

---

## Open Questions

* What AppKit app variant works best for 30-min vibe session? (Property search? Host dashboard? Support agent?)
* Do we need sample files in a Volume for Auto Loader demos, or can we read directly from `samples.wanderbricks`?
* Should Lakebase store app state, user preferences, or both?
* Exact scope of `workshop-infra` — grants only? Or also shared volumes/indexes?
