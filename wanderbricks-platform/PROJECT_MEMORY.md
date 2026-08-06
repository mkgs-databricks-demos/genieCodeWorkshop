# PROJECT_MEMORY.md — WanderBricks Platform

> Last updated: 2026-07-31
> Owner: <your-email>@databricks.com

## Project Identity

**What:** A complete data + AI + app platform for the WanderBricks vacation rental business.
**Who:** Built during the "Genie Code: Building Data Products from A to Z" workshop.
**How:** Entirely with Genie Code across three vibe sessions (Infrastructure → AI Search → Apps).

## Architecture

### Data Source

All source data comes from `samples.wanderbricks` (16 tables, available on all workspaces):

| Table | Description | Notable Columns |
| --- | --- | --- |
| `properties` | Rental listings | property_id, host_id, destination_id, nightly_rate |
| `bookings` | Reservations | booking_id, property_id, user_id, total_amount, status |
| `reviews` | Guest reviews | review_id, booking_id, rating, review_text |
| `customer_support_logs` | Support tickets | ticket_id, interactions (ARRAY<STRUCT>) |
| `clickstream` | User behavior | session_id, events (STRUCT with nested arrays) |
| `users` | Guest profiles | user_id, membership_tier |
| `hosts` | Property owners | host_id, superhost_status |
| `destinations` | Locations | destination_id, country_id, city |
| `countries` | Country reference | country_id, country_name, region |
| `amenities` | Amenity catalog | amenity_id, amenity_name, category |
| `property_amenities` | Junction table | property_id, amenity_id |
| `property_images` | Image URLs | property_id, image_url, is_primary |
| `payments` | Payment records | payment_id, booking_id, method, amount |
| `booking_updates` | Status changes | booking_id, old_status, new_status, updated_at |
| `page_views` | Page analytics | user_id, page_path, timestamp |
| `employees` | Internal staff | employee_id, department, role |

### Medallion Architecture

```
samples.wanderbricks (source)
    ↓ Bronze: Raw ingestion (streaming tables, append-only)
    ↓ Silver: Cleaned + conformed (deduped, typed, null-handled)
    ↓ Gold: Business-ready (metric views, aggregates, features)
```

### Resource Dependency Graph

```
variables (catalog, schema_prefix, warehouse_id)
    → schemas (bronze, silver, gold)
        → volumes (raw_data, checkpoints)
        → pipelines (depend on schemas for target tables)
            → jobs (orchestrate pipeline refreshes)
                → metric views (query gold tables)
                    → genie space (reads metric views)
```

Always reference schemas via `${resources.schemas.<name>.*}` to enforce ordering.

## Targets & Environments

| Target | Catalog | Schema Prefix | Notes |
| --- | --- | --- | --- |
| dev | (set per student) | wanderbricks | Default target |

## Conventions

- **Schema refs:** Always `${resources.schemas.bronze.name}`, never `${var.schema_prefix}_bronze`
- **Notebook paths:** `.ipynb` default, `.sql` only with `warehouse_id`
- **Pipeline architecture:** Metadata-driven (config in `fixtures/config/`, logic in `src/includes/`)
- **Session summaries:** After each work session, write to `fixtures/sessions/`
- **Branch naming:** `<your-initials>-genie-<description>` (never commit to lesson branches directly)

## Workstream Orchestration (Scheduled Tasks)

The Vibe Session 1 answer key is built autonomously via Genie Code Scheduled Tasks.
Each workstream is a paused task with comprehensive instructions, gate checks, and
validation criteria. Status files in `fixtures/handoffs/` coordinate dependencies.

### Dependency Graph

```
WS-0 (Bundle Scaffold) [COMPLETE]
    → WS-A (SDP Pipeline: bronze→silver→gold)
        ├→ WS-B (Metric Views + Orchestration Job) [gates on WS-A]
        │       → WS-C (Genie Agent) [gates on WS-B]
        └→ WS-D (Feature Tables) [gates on WS-A, parallel with WS-B]
```

### Key Files

- `fixtures/architecture/scheduled-tasks/README.md` — Orchestration overview
- `fixtures/architecture/scheduled-tasks/ws-{0,a,b,c,d}-*-prompt.md` — Full task prompts
- `fixtures/handoffs/README.md` — Protocol documentation
- `fixtures/handoffs/workstream-{0,a,b,c,d}-status.md` — State machine files

### Conventions

- **Task titles:** `WanderBricks WS-{X} {Description}`
- **Branches:** `mg-genie-wb-ws-{x}-{description}`
- **Gate checks:** Table-gated (SQL COUNT on output tables), not code-gated
- **Self-termination:** COMPLETE status → immediate exit on subsequent fires
- **Validation:** Every session must `databricks bundle deploy` + run/test before COMPLETE

## Open Questions

- [ ] Which AppKit variant for Vibe Session 3? (property search, host dashboard, or support agent)
- [ ] Lakebase schema design for app state
- [ ] Feature table selection (which features to compute for the gold layer)
- [ ] Should we add a Topic 5b to the agenda for teaching the workstream orchestration pattern?
