# Deploy Operations Patterns

> **Source repo:** [lakeLoom](https://github.com/mkgs-databricks-demos/lakeLoom) — see `deploy.sh`  
> **Purpose:** Reference for the `deploy.sh` orchestration script that ties multi-bundle deployments together. Students with GitHub MCP can browse the full 400+ line script.

---

## 1. What deploy.sh Does

A single bash script at the project root that:
1. Validates and deploys bundles in dependency order
2. Runs platform bootstrap jobs (SPN creation, DDL, grants)
3. Performs readiness checks between infra and app deploys
4. Passes runtime-discovered values to downstream bundles
5. Manages app compute lifecycle (start if stopped, push source)

---

## 2. Flag-Based Composition

```bash
./deploy.sh --target dev                    # Deploy all bundles (with readiness checks)
./deploy.sh --target dev --run-setup        # Deploy infra + run platform bootstrap + app
./deploy.sh --target dev --infra            # Deploy only the infra bundle
./deploy.sh --target dev --infra --run-setup # Deploy infra + run platform bootstrap
./deploy.sh --target dev --app              # Deploy only the app bundle (with checks)
./deploy.sh --target dev --app --skip-checks # Deploy app without readiness checks
./deploy.sh --target dev --validate         # Validate only, no deploy
```

**Design principle:** Compose deployment steps via flags. First deploy needs `--run-setup`; subsequent deploys of just the app skip infra entirely.

---

## 3. Deployment Order

```
1. project-infra        -> Schema, secrets, warehouse, Lakebase, volumes
2. Platform bootstrap   -> SPN creation, secret provisioning, table DDL, volume grants
3. Readiness checks     -> Verify: secret keys + bronze table + volumes + Lakebase status
4. project-app          -> AppKit app resource (permissions, env vars, bindings)
5. App source deploy    -> Start compute if stopped, push source code to container
```

---

## 4. FUSE Self-Relocation (Critical for Databricks Web Terminal)

The Databricks web terminal mounts `/Workspace` via FUSE. After long-running CLI commands (2+ minutes), the FUSE mount becomes stale causing "Operation not permitted" errors.

**Fix:** If running from `/Workspace`, copy script to `/tmp` and re-exec from local disk:

```bash
if [[ "${BASH_SOURCE[0]}" == /Workspace/* ]] && [[ "${__DEPLOY_RELOCATED:-}" != "1" ]]; then
    _tmp_script="/tmp/deploy_$.sh"
    cp "${BASH_SOURCE[0]}" "${_tmp_script}"
    chmod +x "${_tmp_script}"
    export __DEPLOY_RELOCATED=1
    export __DEPLOY_ORIG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    exec "${_tmp_script}" "$@"
fi

# Clean up temp script on exit
if [[ "${__DEPLOY_RELOCATED:-}" == "1" ]]; then
    trap 'rm -f "${BASH_SOURCE[0]}"' EXIT
fi
```

Also need a FUSE-aware `cd` helper:

```bash
cd_bundle() {
    local dir="$1"
    for ((i=1; i<=3; i++)); do
        ls "${dir}" >/dev/null 2>&1 || true  # Poke FUSE to refresh
        sleep 0.5
        if cd "${dir}" 2>/dev/null; then return 0; fi
        sleep 2
    done
    cd "${dir}"  # Final attempt - let error propagate
}
```

---

## 5. resolve_infra_vars() Pattern

After deploying infra, extract deployed resource IDs from `bundle summary --output json`:

```bash
resolve_infra_vars() {
    local bundle_dir="${SCRIPT_DIR}/${INFRA_BUNDLE}"
    log "Resolving infrastructure variables (target: ${TARGET})"

    local summary_json
    summary_json=$(cd_bundle "${bundle_dir}" && \
        databricks bundle summary --target "${TARGET}" --output json 2>/dev/null) || {
        fail "Could not read bundle summary. Deploy infra first."
    }

    # Parse with python3 - extract catalog, schema, warehouse_id, etc.
    eval "$(echo "${summary_json}" | python3 << 'PYEOF'
import sys, json
data = json.load(sys.stdin)

vars_block = data.get('variables', {})
def get_var(name, default=''):
    v = vars_block.get(name, {})
    return v.get('value', default) if isinstance(v, dict) else str(v) if v else default

# From resources (authoritative)
resources = data.get('resources', {})
schemas = resources.get('schemas', {})
for name, ws in schemas.items():
    if isinstance(ws, dict):
        print(f'CATALOG="{ws.get("catalog_name", "")}"')
        print(f'SCHEMA="{ws.get("name", "")}"')

wh_block = resources.get('sql_warehouses', {})
for name, wh in wh_block.items():
    if isinstance(wh, dict) and wh.get('id'):
        print(f'SQL_WAREHOUSE_ID="{wh["id"]}"')
        break

# From variables (fallback)
print(f'SCOPE_NAME="{get_var("secret_scope_name")}"')
print(f'LAKEBASE_PROJECT_ID="{get_var("lakebase_project_id")}"')
PYEOF
)"
}
```

**Why:** The app bundle needs real deployed IDs (warehouse ID, schema name) not just variables. `bundle summary` gives the resolved state.

---

## 6. Infrastructure Readiness Checks

Gate between infra deploy and app deploy — verify everything exists:

```bash
# Secret scope keys (all must be present)
check_secret_keys() {
    local keys_json
    keys_json=$(databricks secrets list-secrets "${SCOPE_NAME}" --output json 2>/dev/null)

    for key in "${REQUIRED_SCOPE_KEYS[@]}"; do
        if ! echo "${keys_json}" | grep -q "${key}"; then
            fail "Missing secret key: ${key}"
        fi
    done
    ok "All secret scope keys present"
}

# Target table exists
check_target_table() {
    local fqn="${CATALOG}.${SCHEMA}.${TARGET_TABLE}"
    databricks tables get "${fqn}" >/dev/null 2>&1 || \
        fail "Table '${fqn}' does not exist. Run --run-setup first."
    ok "Target table exists: ${fqn}"
}

# Volumes exist
check_volumes() {
    for vol in "${VOLUMES[@]}"; do
        databricks volumes read "${CATALOG}.${SCHEMA}.${vol}" >/dev/null 2>&1 || \
            fail "Volume '${vol}' not found."
    done
    ok "All volumes present"
}

# Lakebase project active
check_lakebase() {
    local status
    status=$(databricks postgres get-project "projects/${LAKEBASE_PROJECT_ID}" \
        --output json 2>/dev/null | \
        python3 -c "import sys,json; print(json.load(sys.stdin).get('state','UNKNOWN'))")
    [[ "${status}" == "ACTIVE" ]] || warn "Lakebase project state: ${status}"
    ok "Lakebase project: ${LAKEBASE_PROJECT_ID} (${status})"
}
```

---

## 7. deploy_bundle() Helper

Generic function to validate and deploy any bundle:

```bash
deploy_bundle() {
    local bundle_name="$1"
    shift
    local extra_args=("$@")  # e.g., --var overrides
    local bundle_dir="${SCRIPT_DIR}/${bundle_name}"

    if [[ ! -d "${bundle_dir}" ]]; then
        warn "Bundle '${bundle_name}' does not exist yet - skipping."
        return 0
    fi

    log "Validating ${bundle_name} (target: ${TARGET})"
    (cd_bundle "${bundle_dir}" && databricks bundle validate --target "${TARGET}")
    ok "Validation passed: ${bundle_name}"

    if [[ "${VALIDATE_ONLY}" == true ]]; then return 0; fi

    log "Deploying ${bundle_name} (target: ${TARGET})"
    if [[ ${#extra_args[@]} -gt 0 ]]; then
        (cd_bundle "${bundle_dir}" && databricks bundle deploy --target "${TARGET}" "${extra_args[@]}")
    else
        (cd_bundle "${bundle_dir}" && databricks bundle deploy --target "${TARGET}")
    fi
    ok "Deployed: ${bundle_name}"
}
```

---

## 8. App Compute Lifecycle

After deploying the app bundle, ensure compute is ready before pushing source:

```bash
get_app_status() {
    python3 << 'PYEOF'
import sys, json
data = json.load(sys.stdin)
for key in ('compute_status', 'status', 'app_status'):
    val = data.get(key)
    if val:
        state = val.get('state', val) if isinstance(val, dict) else val
        if state:
            print(state.upper())
            sys.exit(0)
print('UNKNOWN')
PYEOF
}

# Start app compute if stopped
app_json=$(databricks apps get "${APP_NAME}" --output json)
status=$(echo "${app_json}" | get_app_status)

if [[ "${status}" == "STOPPED" ]]; then
    log "Starting app compute..."
    databricks apps start "${APP_NAME}"
    # Poll until ACTIVE (with timeout)
fi

# Push source code
databricks apps deploy "${APP_NAME}" --source-code-path "${APP_SOURCE_PATH}"
```

---

## 9. Logging Helpers

```bash
log()  { echo -e "\n\033[1;34m==>\033[0m \033[1m$1\033[0m"; }
warn() { echo -e "\033[1;33m  WARNING: $1\033[0m"; }
ok()   { echo -e "\033[1;32m  PASS: $1\033[0m"; }
fail() { echo -e "\033[1;31m  FAIL: $1\033[0m"; exit 1; }

# Sanitize values for shell interpolation
safe()     { echo "$1" | sed 's/[^a-zA-Z0-9_.\-]//g'; }
safe_url() { echo "$1" | sed 's/[^a-zA-Z0-9_.\-:\/]//g'; }  # Preserves ://
```

`safe_url()` for workspace host URLs (preserves `://`), `safe()` for everything else.

---

## 10. Script Skeleton for WanderBricks

```bash
#!/usr/bin/env bash
# deploy.sh - WanderBricks Platform deployment orchestrator
set -euo pipefail

# FUSE self-relocation (see section 4)
# ...

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_BUNDLE="wanderbricks-platform"  # Single bundle for workshop
# APP_BUNDLE="wanderbricks-app"       # Future: separate app bundle

TARGET=""
VALIDATE_ONLY=false
RUN_SETUP=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --target)       TARGET="$2"; shift 2 ;;
        --run-setup)    RUN_SETUP=true; shift ;;
        --validate)     VALIDATE_ONLY=true; shift ;;
        -h|--help)      usage ;;
        *)              echo "Error: Unknown option '$1'"; usage ;;
    esac
done

[[ -z "${TARGET}" ]] && { echo "Error: --target required."; usage; }

# Deploy infra
deploy_bundle "${INFRA_BUNDLE}"

# Run bootstrap job if requested
if [[ "${RUN_SETUP}" == true ]]; then
    log "Running platform bootstrap..."
    (cd_bundle "${SCRIPT_DIR}/${INFRA_BUNDLE}" && \
        databricks bundle run platform_bootstrap --target "${TARGET}")
    ok "Platform bootstrap complete"
fi
```

---

## GitHub MCP Quick Reference

Students can browse the full deploy.sh for additional patterns:

```
Repo: mkgs-databricks-demos/lakeLoom
Key path: deploy.sh (400+ lines)

Notable sections:
  - Lines 1-50:   FUSE self-relocation
  - Lines 50-100: Constants and argument parsing
  - Lines 100-150: deploy_bundle() helper
  - Lines 150-250: resolve_infra_vars() with python3 JSON parsing
  - Lines 250-350: Readiness checks (secrets, table, volumes, Lakebase)
  - Lines 350-400: App compute lifecycle (start, deploy source)
```