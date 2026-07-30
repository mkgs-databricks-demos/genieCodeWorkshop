# workshop-infra

Instructor-deployed infrastructure for the Genie Code Workshop.

## Purpose

This bundle provisions shared resources that students need but shouldn't build themselves. Deploy this **before** the workshop begins.

## What It Creates

- Shared schema for workshop artifacts
- Volume for reference documents (Analytics Handbook PDF, sample files)
- Any grants or permissions that require elevated privileges

## Deployment

```bash
# Set your catalog in the target variables first
databricks bundle deploy -t dev
```

## When to Add Resources Here

Add to this bundle when:
- A resource requires admin/elevated permissions to create
- A resource is shared across ALL students (not per-student)
- A resource needs to exist BEFORE students start their work

Do NOT add here:
- Anything students should learn to create themselves
- Per-student resources (those go in `wanderbricks-platform`)
