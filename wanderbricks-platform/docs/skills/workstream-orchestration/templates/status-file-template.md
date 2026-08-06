# Status File Template

Copy this for each workstream. Replace `<X>` and `<Description>` with your values.

---

```markdown
---
status: NOT_STARTED
branch:
started_at:
completed_at:
output_tables: []
validation: N/A
bundle_deployed: N/A
tests_passed: N/A
---

# Workstream <X> — <Description>

**Status:** NOT_STARTED

## Upstream Dependencies
- WS-<upstream> COMPLETE
- (Optional) Table: <catalog.schema.table> must have rows

## Expected Output
- <List what this workstream will produce>
- <Tables, resources, files>

## What Was Built
(Filled in by the session when marking COMPLETE)

## Notes for Downstream Sessions
(Filled in by the session — anything the next workstream needs to know)
```
