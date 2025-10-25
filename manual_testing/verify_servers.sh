#!/bin/bash
# Verify all MCP servers can be imported and list their tools

echo "================================================================================"
echo "Spatial MCP POC - Server Verification"
echo "================================================================================"
echo ""

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_ROOT"

SERVERS=(
    "mcp-fgbio"
    "mcp-spatialtools"
    "mcp-openimagedata"
    "mcp-seqera"
    "mcp-huggingface"
    "mcp-deepcell"
    "mcp-mockepic"
    "mcp-tcga"
)

SUCCESS_COUNT=0
TOTAL_TOOLS=0

for server in "${SERVERS[@]}"; do
    echo "Testing: $server"

    cd "servers/$server"

    if [ ! -d "venv" ]; then
        echo "  ❌ No venv found - run ./setup_and_test_servers.sh --install"
        cd "$REPO_ROOT"
        continue
    fi

    source venv/bin/activate

    # Test import and count tools
    RESULT=$(python3 << EOF
import sys
sys.path.insert(0, "src")

try:
    module_name = "${server}".replace("-", "_")
    server_module = __import__(f"{module_name}.server", fromlist=["mcp"])
    mcp = server_module.mcp

    # Count tools by checking for @mcp.tool() decorated functions
    tools = []
    if hasattr(mcp, '_tools'):
        tools = list(mcp._tools.keys())

    print(f"OK|{len(tools)}")
    if tools:
        for tool in sorted(tools):
            print(f"  - {tool}")
except Exception as e:
    print(f"ERROR|{e}")
EOF
)

    STATUS=$(echo "$RESULT" | head -1 | cut -d'|' -f1)

    if [ "$STATUS" == "OK" ]; then
        TOOL_COUNT=$(echo "$RESULT" | head -1 | cut -d'|' -f2)
        echo "  ✅ OK - $TOOL_COUNT tools"
        echo "$RESULT" | tail -n +2
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        TOTAL_TOOLS=$((TOTAL_TOOLS + TOOL_COUNT))
    else
        ERROR=$(echo "$RESULT" | head -1 | cut -d'|' -f2)
        echo "  ❌ FAILED - $ERROR"
    fi

    deactivate
    cd "$REPO_ROOT"
    echo ""
done

echo "================================================================================"
echo "Summary"
echo "================================================================================"
echo ""
echo "Servers working: $SUCCESS_COUNT/8"
echo "Total tools: $TOTAL_TOOLS"
echo ""

if [ $SUCCESS_COUNT -eq 8 ]; then
    echo "🎉 All MCP servers are operational!"
    echo ""
    echo "Next steps:"
    echo "1. Test a single server:"
    echo "   cd servers/mcp-fgbio"
    echo "   source venv/bin/activate"
    echo "   python -m mcp_fgbio"
    echo ""
    echo "2. Configure for Claude Desktop:"
    echo "   - Edit configs/claude_desktop_config_complete.json"
    echo "   - Update all paths to absolute paths"
    echo "   - Copy to: ~/Library/Application Support/Claude/claude_desktop_config.json"
    echo "   - Restart Claude Desktop"
    echo ""
    echo "3. Try example prompts from: docs/MCP_POC_Example_Prompts.md"
else
    echo "⚠️  Some servers failed. Check errors above."
fi
echo ""
