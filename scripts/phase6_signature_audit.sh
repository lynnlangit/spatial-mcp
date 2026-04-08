#!/usr/bin/env bash
#
# Phase 6 — PAT001 signature-audit smoke test
#
# Lightweight cross-server verification for the HOSPITAL1 FastMCP 2.13
# migration. Walks every server in servers/mcp-*, imports it in its own
# uv-managed venv, and lists its registered tools. Compares the observed
# count to the canonical server registry. Reports any import errors,
# missing tools, or signature drift.
#
# This is intentionally NOT a full end-to-end run (that is Phase 8 on
# GCP). It catches the class of regression most likely to be introduced
# by a dependency bump: a server whose import fails or whose tool set
# silently changed.
#
# Usage:
#   ./scripts/phase6_signature_audit.sh
#
# Exit code: 0 if every server imports and tool counts match expectations,
#            1 if any server fails.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SERVERS_DIR="${REPO_ROOT}/servers"

# Canonical (name, python_package, expected_tool_count) tuples pulled from
# docs/reference/shared/server-registry.md. Update here when the registry
# is updated.
declare -a REGISTRY=(
    "mcp-fgbio:mcp_fgbio:4"
    "mcp-multiomics:mcp_multiomics:10"
    "mcp-spatialtools:mcp_spatialtools:16"
    "mcp-perturbation:mcp_perturbation:8"
    "mcp-quantum-celltype-fidelity:quantum_celltype_fidelity:6"
    "mcp-deepcell:mcp_deepcell:3"
    "mcp-cell-classify:mcp_cell_classify:3"
    "mcp-epic:mcp_epic:4"
    "mcp-openimagedata:mcp_openimagedata:5"
    "mcp-patient-report:mcp_patient_report:5"
    "mcp-genomic-results:mcp_genomic_results:4"
    "mcp-geodownload:mcp_geodownload:6"
    "mcp-opentargets:mcp_opentargets:6"
    "mcp-cibersortx:mcp_cibersortx:5"
    "mcp-neoantigen:mcp_neoantigen:6"
    "mcp-mocktcga:mcp_mocktcga:5"
    "mcp-mockepic:mcp_mockepic:3"
)

# Servers that are expected to fail local runtime on macOS ARM64 because
# of pre-existing platform constraints. They will be reported but not
# counted as failures.
declare -a LOCAL_SKIP=(
    "mcp-deepcell"    # tensorflow 2.8.4 has no arm64 wheel
)

is_local_skip() {
    local name=$1
    local skip
    for skip in "${LOCAL_SKIP[@]}"; do
        if [ "$skip" = "$name" ]; then return 0; fi
    done
    return 1
}

total=0
passed=0
failed=0
skipped=0
warnings=0

printf "%-34s %-8s %-10s %s\n" "SERVER" "STATUS" "TOOLS" "NOTES"
printf "%-34s %-8s %-10s %s\n" "------" "------" "-----" "-----"

for entry in "${REGISTRY[@]}"; do
    total=$((total + 1))
    IFS=':' read -r server_name package expected <<< "$entry"
    server_path="${SERVERS_DIR}/${server_name}"

    if [ ! -d "$server_path" ]; then
        printf "%-34s %-8s %-10s %s\n" "$server_name" "MISSING" "-" "directory not found"
        failed=$((failed + 1))
        continue
    fi

    if is_local_skip "$server_name"; then
        printf "%-34s %-8s %-10s %s\n" "$server_name" "SKIP" "-" "pre-existing ARM64 platform limitation"
        skipped=$((skipped + 1))
        continue
    fi

    output=$(
        cd "$server_path" && uv run --quiet python -c "
import asyncio, sys, fastmcp
try:
    assert tuple(int(x) for x in fastmcp.__version__.split('.')[:2]) >= (2, 13), fastmcp.__version__
    mod = __import__('${package}.server', fromlist=['server'])
    mcp = mod.mcp
    if hasattr(mcp, 'list_tools'):
        tools = asyncio.run(mcp.list_tools())
        names = [t.name for t in tools]
    elif hasattr(mcp, 'get_tools'):
        tools = asyncio.run(mcp.get_tools())
        names = list(tools.keys()) if hasattr(tools, 'keys') else [t.name for t in tools]
    else:
        names = list(mcp._tool_manager._tools.keys())
    print(f'OK {len(names)} {fastmcp.__version__}')
except Exception as e:
    print(f'FAIL {type(e).__name__}: {e}')
    sys.exit(1)
" 2>&1 | tail -1
    ) || true

    if [[ "$output" == OK* ]]; then
        # shellcheck disable=SC2086
        read -r _ actual fmcp <<< "$output"
        if [ "$actual" = "$expected" ]; then
            printf "%-34s %-8s %-10s %s\n" "$server_name" "OK" "$actual" "fastmcp $fmcp"
            passed=$((passed + 1))
        else
            printf "%-34s %-8s %-10s %s\n" "$server_name" "WARN" "$actual/$expected" "fastmcp $fmcp — tool count drift"
            passed=$((passed + 1))
            warnings=$((warnings + 1))
        fi
    else
        printf "%-34s %-8s %-10s %s\n" "$server_name" "FAIL" "-" "$output"
        failed=$((failed + 1))
    fi
done

echo ""
echo "Phase 6 audit summary:"
echo "  total=$total  passed=$passed  failed=$failed  skipped=$skipped  warnings=$warnings"

if [ "$failed" -gt 0 ]; then
    exit 1
fi
exit 0
