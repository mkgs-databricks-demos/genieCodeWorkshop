# Lesson 01: Foundations

> **Topics:** 1–5 | **Duration:** ~50 minutes | **Type:** Setup + Conceptual + Architecture

---

## What You'll Learn

This lesson covers the foundational skills and patterns that make Genie Code effective. These aren't coding tasks — they're the setup and mental models that determine whether your Genie Code sessions produce great results or mediocre ones.

## Topics

### Topic 1: Resetting Genie Code (10 min)

**Goal:** Start with a clean, intentional Genie Code environment.

**Activities:**
- Audit your current skills (`~/.assistant/skills/`)
- Remove stale or irrelevant skills
- Add skills relevant to this workshop
- Configure MCP servers (GitHub, Slack, Google Drive)

**Key Insight:** Skills inject context into EVERY session. Stale skills = stale advice.

---

### Topic 2: Databricks Editors for Context (10 min)

**Goal:** Understand that the editor you're in determines Genie Code's capabilities.

**Key Concepts:**
- Each editor gives Genie Code different tools
- The Bundle Editor is the most important for building data products
- Navigate between editors intentionally (don't force everything through notebooks)

**Reference:** [Editor Choice Table](../conventions/genie-code-best-practices.md#choosing-the-right-editor)

---

### Topic 3: Sharing Genie Code Sessions (5 min)

**Goal:** Learn to use sessions as documentation and collaboration tools.

**Key Concepts:**
- A well-structured session IS documentation
- Share button → read-only view for colleagues
- Start with intent, make decisions explicit, end with summary

---

### Topic 4: Proper Declarative Automation Bundle Setup (15 min)

**Goal:** Understand how bundles give Genie Code architectural context.

**Activities:**
- Open `databricks.yml` in the Bundle Editor
- Understand variables, resource references, and targets
- See how `${resources.schemas.*}` creates dependency ordering

**Key Insight:** The Bundle Editor + `databricks.yml` gives Genie Code more architectural context than a dozen separate files.

**Reference:** [DAB Conventions](../conventions/genie-code-best-practices.md#declarative-automation-bundle-conventions)

---

### Topic 5: Architectural Plans, Project Memory & Session Summaries (10 min)

**Goal:** Eliminate cold-start problems across sessions.

**Activities:**
- Review `PROJECT_MEMORY.md` structure and purpose
- Understand `.assistant_instructions.md` vs `PROJECT_MEMORY.md`
- Create your first session summary

**Key Insight:** If you find yourself re-explaining something to Genie Code, that information should live in a file it can read.

**Reference:** [Project Memory](../conventions/genie-code-best-practices.md#project-memory) | [Session Summaries](../conventions/genie-code-best-practices.md#session-summaries)

---

## Next Steps

After completing Lesson 01, you'll move to `lesson/02-vibe-infra` where you'll start building infrastructure with Genie Code in the Bundle Editor.

```
git checkout lesson/02-vibe-infra
git checkout -b <your-name>-genie-vibe-infra
```
