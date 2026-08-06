---
name: workstream-orchestration
triggers:
  - break this into workstreams
  - decompose this project
  - run these in parallel
  - autonomous execution
  - set up workstream orchestration
  - scheduled task orchestration
---

# Workstream Orchestration

Decompose a project into autonomous, parallel workstreams that self-coordinate
via status files and Genie Code scheduled tasks. Each workstream runs unattended
in its own git folder clone, with dependency gating and branch stacking.

## When to Use This Pattern

- Project has 3+ distinct deliverables that can be built independently
- Deliverables have clear dependency order (some must finish before others start)
- Each deliverable touches different files (no merge conflicts)
- You want hands-off execution with human review only at the end
- Total estimated work exceeds what one session can accomplish (~60 min limit)

## When NOT to Use

- Single deliverable that takes <60 min (just do it in one session)
- Highly interdependent code (every piece touches the same files)
- Exploratory work where requirements aren't yet clear
- Work that requires continuous human feedback at each step

## Prerequisites

- A git-linked workspace folder (the "orchestration hub")
- A PROJECT_MEMORY.md or equivalent architecture doc
- Unity Catalog schema deployed (for table-gated checks)
- Clear understanding of what "done" looks like for each deliverable

## Quick Start (5 Steps)

1. **Plan** — Read `planning.md`. Decompose your project into workstreams.
   Map dependencies. Verify file isolation.

2. **Write prompts** — Read `writing-prompts.md`. Write one prompt file per
   workstream using the 5-section template (GATE → CONTEXT → EXECUTE → VALIDATE → COMPLETE).

3. **Set up protocol** — Read `protocol.md`. Create status files, configure
   clone paths, define branch stacking order.

4. **Create scheduled tasks** — Use `scheduleAgentTool` with each prompt.
   First workstream: 3-min cron. All others: 15-min cron.

5. **Walk away** — Monitor via status files. WS-FINAL produces the merge plan
   when everything completes.

## Skill Files

| File | Purpose |
| --- | --- |
| `planning.md` | How to decompose a project into workstreams |
| `writing-prompts.md` | The 5-section prompt template and anti-patterns |
| `protocol.md` | Status files, clones, branch stacking, cron strategy |
| `templates/status-file-template.md` | Copy-paste status file starter |
| `templates/prompt-template.md` | Copy-paste prompt skeleton |
| `templates/orchestration-readme-template.md` | README for the scheduled-tasks folder |
| `templates/ws-final-template.md` | The mandatory final summary workstream |

## Key Concepts (Summary)

- **Orchestration hub** — Main project folder. Holds status files, architecture docs. Never moves branches.
- **Working clones** — Isolated git folder per workstream at `~/genie-code-workstream-orchestration/<project>/<ws>/`.
- **Branch stacking** — Downstream branches from upstream's pushed branch (not the base). Gets upstream code without merging.
- **Table-gated** — Gate checks verify output tables exist via SQL COUNT. Decouples from PR review.
- **Self-terminating** — COMPLETE status → immediate exit on next fire. Idempotent and safe.
- **WS-FINAL** — Mandatory last workstream. Gates on ALL. Produces PR titles, descriptions, merge order.
