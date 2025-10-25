#!/bin/bash
# Install dependencies for all MCP servers

echo "================================================================================"
echo "Installing Dependencies for All MCP Servers"
echo "================================================================================"
echo ""

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_ROOT"

# Common dependencies for all servers
COMMON_DEPS="fastmcp httpx aiofiles pydantic numpy pandas"

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

for server in "${SERVERS[@]}"; do
    echo "Installing dependencies for: $server"

    cd "servers/$server"

    # Create venv if needed (use Python 3.11)
    if [ ! -d "venv" ]; then
        echo "  Creating venv with Python 3.11..."
        python3.11 -m venv venv
    fi

    source venv/bin/activate

    # Upgrade pip
    pip install --upgrade pip -q

    # Install common dependencies
    echo "  Installing common dependencies..."
    pip install -q $COMMON_DEPS

    # Install from pyproject.toml if it exists
    if [ -f "pyproject.toml" ]; then
        echo "  Installing from pyproject.toml..."
        # Use pip install with --config-settings for PEP 660
        pip install -q --upgrade setuptools wheel
        pip install -q . || pip install -q -e . --config-settings editable_mode=compat || true
    fi

    echo "  ✅ Complete"

    deactivate
    cd "$REPO_ROOT"
    echo ""
done

echo "================================================================================"
echo "✅ All dependencies installed!"
echo "================================================================================"
echo ""
echo "Run './verify_servers.sh' to test all servers"
echo ""
