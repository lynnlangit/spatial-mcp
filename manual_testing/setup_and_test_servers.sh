#!/bin/bash
# Setup and test all MCP servers for the Spatial MCP POC

set -e

echo "================================================================================"
echo "Spatial MCP POC - Server Setup and Verification"
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

# Check if we should install dependencies
INSTALL_DEPS=false
if [ "$1" == "--install" ]; then
    INSTALL_DEPS=true
    echo "📦 Installing dependencies for all servers..."
    echo ""
fi

for server in "${SERVERS[@]}"; do
    echo "--- Testing: $server ---"

    if [ ! -d "servers/$server" ]; then
        echo "❌ Server directory not found: servers/$server"
        continue
    fi

    cd "servers/$server"

    if [ "$INSTALL_DEPS" = true ]; then
        echo "  Installing dependencies..."

        # Create venv if it doesn't exist
        if [ ! -d "venv" ]; then
            python3 -m venv venv
        fi

        # Activate venv and install
        source venv/bin/activate

        # Install in editable mode
        if [ -f "pyproject.toml" ]; then
            pip install -q -e . 2>&1 | grep -v "already satisfied" || true
            echo "  ✅ Installed"
        else
            echo "  ⚠️  No pyproject.toml found"
        fi

        deactivate
    else
        # Just check if dependencies are installed
        if [ -d "venv" ]; then
            source venv/bin/activate
            python -c "import ${server//-/_}.server" 2>/dev/null && echo "  ✅ OK - Server can be imported" || echo "  ❌ Import failed - run with --install"
            deactivate
        else
            echo "  ⚠️  No venv found - run with --install"
        fi
    fi

    cd "$REPO_ROOT"
    echo ""
done

echo "================================================================================"
echo "Summary"
echo "================================================================================"
echo ""

if [ "$INSTALL_DEPS" = true ]; then
    echo "✅ Installation complete!"
    echo ""
    echo "To verify all servers are working, run:"
    echo "  ./setup_and_test_servers.sh"
else
    echo "Run './setup_and_test_servers.sh --install' to install all dependencies"
fi

echo ""
echo "Next steps for manual testing:"
echo ""
echo "1. Start a server manually (example - mcp-fgbio):"
echo "   cd servers/mcp-fgbio"
echo "   source venv/bin/activate"
echo "   python -m mcp_fgbio"
echo ""
echo "2. Or configure Claude Desktop:"
echo "   - Copy configs/claude_desktop_config_complete.json"
echo "   - Update paths to absolute paths"
echo "   - Restart Claude Desktop"
echo ""
echo "3. Test with example prompts:"
echo "   - See docs/MCP_POC_Example_Prompts.md"
echo ""
