# Scheduled Task Prompt — Workstream C: Genie Agent (Space)

## scheduleAgentTool Parameters

- **title:** `WanderBricks WS-C Genie Agent`
- **cronExpression:** `0 */15 * * * ?`

## Instructions (copy verbatim into scheduleAgentTool)

```
You are executing Workstream C of the WanderBricks Platform: creating a Genie Space (AI agent) over the gold layer and metric views.

Project: /Users/matthew.giglia@databricks.com/genieCodeWorkshop/wanderbricks-platform/
Git repo: /Users/matthew.giglia@databricks.com/genieCodeWorkshop

== GATE CHECK ==

1. Read /Users/matthew.giglia@databricks.com/genieCodeWorkshop/wanderbricks-platform/fixtures/handoffs/workstream-c-status.md
2. Parse YAML frontmatter. If status is "COMPLETE": respond "WS-C already complete." and stop.

3. Read /Users/matthew.giglia@databricks.com/genieCodeWorkshop/wanderbricks-platform/fixtures/handoffs/workstream-b-status.md
4. Parse YAML frontmatter. If status != "COMPLETE":
   - Respond "Upstream WS-B not complete. Waiting." and stop.

5. Verify metric views exist:
   SHOW VIEWS IN hls_fde_dev.dev_matthew_giglia_wanderbricks_ai
   - If no metric views found: respond "Metric views not created. Waiting." and stop.

== CONTEXT ==

Read these files:
- /Users/matthew.giglia@databricks.com/genieCodeWorkshop/wanderbricks-platform/PROJECT_MEMORY.md
- /Users/matthew.giglia@databricks.com/genieCodeWorkshop/wanderbricks-platform/fixtures/handoffs/workstream-b-status.md (read "Notes for Downstream Sessions" for metric view details and sample questions)
- /Users/matthew.giglia@databricks.com/genieCodeWorkshop/docs/reference/wanderbricks-analytics-handbook.md

== EXECUTE ==

6. Update workstream-c-status.md to status: IN_PROGRESS, set started_at.

7. Create git branch: mg-genie-wb-ws-c-genie-agent (from lesson/02-vibe-infra).

8. Create the Genie Space resource:

   Create resources/wanderbricks_genie_space.yml:

   The Genie Space should:
   - Name: "WanderBricks Intelligence"
   - Description: "AI-powered analytics agent for the WanderBricks vacation rental platform. Ask questions about revenue, occupancy, guest satisfaction, and host performance."
   - Include ALL gold tables and metric views as data sources
   - Have comprehensive instructions that include:
     * Business context (WanderBricks is a vacation rental platform)
     * Metric definitions (from Analytics Handbook — especially commission rate, GSS formula, superhost criteria)
     * Table relationships and join keys
     * Common query patterns
     * Naming conventions (what each table/view contains)
   - Sample questions covering each domain:
     * Revenue: "What was the total GBV last month?" "Which destinations generate the most net revenue?"
     * Occupancy: "What's the platform-wide occupancy rate?" "Which properties have the highest ADR?"
     * Satisfaction: "Show me properties with GSS below 4.0" "What's our review response rate?"
     * Host: "How many superhosts do we have?" "Which hosts are at risk of losing superhost status?"
     * Cross-domain: "Show me high-revenue properties with low satisfaction scores"

   Resource YAML structure:
   ```yaml
   resources:
     quality_monitors:  # or genie_spaces: depending on bundle support
       wanderbricks_genie:
         display_name: "WanderBricks Intelligence"
         description: "..."
         catalog_name: ${resources.schemas.wanderbricks_schema.catalog_name}
         schema_name: ${resources.schemas.wanderbricks_schema.name}
         table_identifiers:
           - gold_revenue_daily
           - gold_occupancy_monthly
           - gold_guest_satisfaction
           - gold_host_performance
           - gold_property_summary
           - mv_revenue_metrics (if exists)
           - mv_occupancy_metrics (if exists)
           - mv_guest_satisfaction (if exists)
           - mv_host_performance (if exists)
         instructions: |
           ...
         sample_questions:
           - ...
   ```

   NOTE: If Genie spaces are not supported as bundle resources in the current CLI version, create the space via the Databricks SDK in a setup notebook (src/notebooks/create_genie_space.py) and add it as a job task. Document the space ID in the status file.

9. VALIDATE:
   - Run: databricks bundle validate --target dev
   - Run: databricks bundle deploy --target dev (or run the setup notebook)
   - Verify the Genie space is accessible
   - Test at least 2 sample questions manually (describe expected vs actual)

10. COMPLETE:
    - Update fixtures/handoffs/workstream-c-status.md:
      - status: COMPLETE, completed_at, output_tables (Genie space name/ID), validation: PASSED
      - "What Was Built" section
      - "Notes for Downstream Sessions": Genie space ID, how to access, what questions it handles
    - Write session summary to fixtures/sessions/
    - Commit and push branch

IMPORTANT: Never commit to main or lesson branches directly. The Genie Space instructions should be detailed enough that someone unfamiliar with the data can ask meaningful questions and get correct answers.
```
