# Writing Autonomous Session Prompts

Every workstream prompt follows the same 5-section structure. This consistency
makes prompts predictable, debuggable, and safe to run unattended.

## The 5-Section Template

### Section 1: GATE CHECK

**Purpose:** Determine whether to proceed or exit immediately.

```
== GATE CHECK ==

1. Read <own-status-file> from orchestration hub.
2. If status is COMPLETE: respond "Already complete." and STOP.
3. Read <upstream-status-file(s)>.
4. If upstream status != COMPLETE: respond "Waiting on <upstream>." and STOP.
5. (Optional) Verify preconditions:
   - SQL: SELECT COUNT(*) FROM <expected_table> — must be > 0
   - CLI: databricks bundle summary (schema deployed?)
```

**Rules:**
- Own-status check FIRST (self-termination on re-fire)
- Upstream check SECOND (dependency gating)
- Table/resource checks THIRD (belt-and-suspenders validation)
- Exit messages should be informative (name what's pending)
- Total gate check time: <10 seconds

### Section 2: CONTEXT

**Purpose:** Give the session enough architectural awareness to make good decisions.

```
== CONTEXT ==

Read these files for full project context:
- <project>/PROJECT_MEMORY.md
- <project>/fixtures/architecture/scheduled-tasks/README.md
- <upstream-status-file> ("Notes for Downstream" section)
- <any config files this workstream needs>
```

**Rules:**
- List EVERY file the session needs to read. Don't assume prior knowledge.
- Include the PROJECT_MEMORY.md (it has table inventory, conventions, architecture)
- Include upstream status files (they contain "Notes for Downstream Sessions")
- Include relevant config files (pipeline config, schema definitions)
- The session starts with ZERO context. If it's not listed here, it won't be read.
- ALWAYS include an instruction to review the current source state (read README,
  existing resources, src/ directory) to understand what the project does and
  where it is before writing new code.

### Section 3: EXECUTE

**Purpose:** The actual work. Specific enough to be unambiguous, not so prescriptive
that it blocks the agent's problem-solving.

```
== EXECUTE ==

1. Set own status to IN_PROGRESS (editAsset on bundle root status file).

2. SINGLE-FIRE GUARD (self-pause via alerts-internal API).

3. ALL WORK IN BUNDLE ROOT:
   - Code: editAsset/createAsset for src/, resources/, fixtures/config/
   - Deploy: runDatabricksCli for bundle validate/deploy/run
   - Status: editAsset for fixtures/handoffs/
   - NO runGit operations until GIT SYNC at the end.

4. [Describe the work in 5-15 numbered steps]
   - Be specific about WHAT to build (table names, resource types)
   - Be specific about WHERE files go (directories, naming)
   - Let the agent decide HOW to implement
   - Reference conventions from PROJECT_MEMORY.md

5. Bundle validate: databricks bundle validate --target dev
   Fix any errors before proceeding.

6. Bundle deploy: databricks bundle deploy --target dev
```

**Rules:**
- All work happens in the bundle root (no separate clone during execution)
- Git sync is ALWAYS the last step (after COMPLETE, one-way push)
- Describe WHAT, not HOW (the agent picks implementation details)
- Reference existing conventions ("follow the pattern in PROJECT_MEMORY.md")
- Include bundle validate + deploy (catches errors early)
- 5-15 execution steps is the sweet spot
- ALL workspace paths MUST use the `/Workspace/Users/...` prefix — never
  `/Users/...` (missing `/Workspace/`), never `~/` shorthand. Tools like
  `runGit`, `readAssetById`, and `editAsset` require the full prefix.
  This applies to EVERY path in the prompt: header fields, push clone paths,
  bundle root paths, and file read paths.
- ALWAYS include: "When in doubt about the best way to implement something,
  use your available tools (docSearch, spark APIs, skill files) to check the
  latest Databricks best practices before proceeding."

### Section 4: VALIDATE

**Purpose:** Verify the work actually produced correct results.

```
== VALIDATE ==

Run these checks:
- SQL: SELECT COUNT(*) FROM <output_table_1> — expect > 0
- SQL: SELECT COUNT(*) FROM <output_table_2> — expect > 0
- CLI: databricks bundle validate --target dev — expect clean
- (Optional) Query specific data quality checks
```

**Rules:**
- SQL COUNT queries for every output table
- Bundle validate for resource correctness
- Concrete expected values ("expect > 0", "expect no errors")
- If validation fails, the prompt should say what to do (fix and retry, or mark BLOCKED)

### Section 5: COMPLETE

**Purpose:** Clean exit with full state capture.

```
== COMPLETE ==

1. Update <own-status-file>:
   - status: COMPLETE
   - completed_at: current UTC timestamp
   - output_tables: [list of tables created]
   - validation: PASSED
   - branch: <own-branch>

2. Add "What Was Built" section to status file.
3. Add "Notes for Downstream Sessions" with anything the next workstream needs to know.
4. Write session summary to fixtures/sessions/YYYY-MM-DD_<description>.md
5. Commit and push all changes (in the working clone).
6. Commit status file update (in the orchestration hub).
```

**Rules:**
- Status file update is the LAST thing (ensures work is done before signaling)
- "Notes for Downstream" is critical — this is how workstreams communicate
- Session summary captures decisions for human review
- Two commits: one in clone (code), one in hub (status)

## Anti-Patterns

### Too Vague
```
❌ "Build a pipeline for the data."
```
The agent doesn't know which tables, what schema, what layers, or what conventions to follow.

### Too Prescriptive
```
❌ "Write this exact code: [50 lines of Python]"
```
If you're writing the code yourself, you don't need a scheduled task. Let the agent solve problems.

### Missing Context Files
```
❌ [No CONTEXT section]
```
The agent starts with zero knowledge. Without explicit file reads, it'll guess wrong.

### No Validation
```
❌ [EXECUTE ends with "commit and push"]
```
Without validation, a workstream can mark COMPLETE with broken output, poisoning downstream.

### Cadence Language in Instructions
```
❌ "Every 15 minutes, check if WS-A is done and then..."
```
The agent reads this as a new scheduling request. Cadence lives in cronExpression ONLY.

### Referencing Relative Time Without Anchoring
```
❌ "Process yesterday's data"
✅ "Process data from the most recent full UTC day"
```

### Incorrect Workspace Path Prefix
```
❌ Working clone: /Users/matthew.giglia@databricks.com/genie-code-workstream-orchestration/...
❌ Working clone: ~/genie-code-workstream-orchestration/...
✅ Working clone: /Workspace/Users/matthew.giglia@databricks.com/genie-code-workstream-orchestration/...
```
The `runGit` tool requires `/Workspace/Users/...` — without the `/Workspace/` prefix, clone/checkout/commit
operations fail silently or target the wrong path. Use the full prefix for ALL paths in the prompt:
header metadata, clone paths, status file paths, and file-read paths.

## The "Goldilocks Zone" for Specificity

| Too Vague | Just Right | Too Prescriptive |
| --- | --- | --- |
| "Make a pipeline" | "Create SDP pipeline with bronze (raw ingest), silver (cleaned/typed), gold (business aggregates) for the 16 tables in samples.wanderbricks" | "Write @dp.table with spark.readStream..." |
| "Add metrics" | "Create metric views for revenue, occupancy, and satisfaction over the gold tables" | "CREATE MATERIALIZED VIEW gold_revenue AS SELECT..." |
| "Set up features" | "Create feature tables for host_performance and property_quality using FeatureEngineeringClient" | [full Python implementation] |

The prompt defines the WHAT and the BOUNDARIES. The agent figures out the HOW.
