#!/bin/bash
#
# Setup script for Spatial MCP POC
# This script sets up the development environment for all MCP servers
#

set -e  # Exit on error

echo "=================================="
echo "Spatial MCP POC - Environment Setup"
echo "=================================="
echo ""

# Get the project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Project root: $PROJECT_ROOT"
echo ""

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.11"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"; then
    echo "❌ ERROR: Python 3.11+ required. Found: $PYTHON_VERSION"
    exit 1
fi

echo "✓ Python $PYTHON_VERSION detected"
echo ""

# Create necessary directories
echo "Creating directory structure..."
mkdir -p "$PROJECT_ROOT/data/reference"
mkdir -p "$PROJECT_ROOT/data/test_data"
mkdir -p "$PROJECT_ROOT/data/cache"
mkdir -p "$PROJECT_ROOT/tests/integration"
mkdir -p "$PROJECT_ROOT/tests/e2e"

echo "✓ Directories created"
echo ""

# Setup mcp-fgbio server
echo "Setting up mcp-fgbio server..."
cd "$PROJECT_ROOT/servers/mcp-fgbio"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "  Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "  Installing dependencies..."
source venv/bin/activate

# Upgrade pip
pip install --quiet --upgrade pip

# Install the package in development mode
pip install --quiet -e ".[dev]"

echo "✓ mcp-fgbio installed"
echo ""

# Create .env file if it doesn't exist
ENV_FILE="$PROJECT_ROOT/servers/mcp-fgbio/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "Creating .env file for mcp-fgbio..."
    cat > "$ENV_FILE" << EOF
# Data directories
FGBIO_REFERENCE_DATA_DIR=$PROJECT_ROOT/data/reference
FGBIO_CACHE_DIR=$PROJECT_ROOT/data/cache

# Development settings
FGBIO_DRY_RUN=true
FGBIO_LOG_LEVEL=INFO

# Performance
FGBIO_TIMEOUT_SECONDS=300
FGBIO_MAX_DOWNLOAD_SIZE_GB=10
EOF
    echo "✓ .env file created"
else
    echo "✓ .env file already exists"
fi

# Deactivate virtual environment
deactivate

echo ""

# Update Claude Desktop configuration
CONFIG_FILE="$PROJECT_ROOT/configs/claude_desktop_config.json"
echo "Updating Claude Desktop configuration..."

# Use Python to update the config with absolute paths
python3 << EOF
import json
import os

config_file = "$CONFIG_FILE"
project_root = "$PROJECT_ROOT"

# Read the existing config
with open(config_file, 'r') as f:
    config = json.load(f)

# Update paths to be absolute
config["mcpServers"]["fgbio"]["cwd"] = os.path.join(project_root, "servers/mcp-fgbio")
config["mcpServers"]["fgbio"]["env"]["PYTHONPATH"] = os.path.join(project_root, "servers/mcp-fgbio/src")
config["mcpServers"]["fgbio"]["env"]["FGBIO_REFERENCE_DATA_DIR"] = os.path.join(project_root, "data/reference")
config["mcpServers"]["fgbio"]["env"]["FGBIO_CACHE_DIR"] = os.path.join(project_root, "data/cache")

# Write back
with open(config_file, 'w') as f:
    json.dump(config, f, indent=2)

print("✓ Configuration updated")
EOF

echo ""

# Run tests to verify installation
echo "Running tests to verify installation..."
cd "$PROJECT_ROOT/servers/mcp-fgbio"
source venv/bin/activate

if pytest --quiet --tb=short; then
    echo "✓ All tests passed"
else
    echo "⚠ Some tests failed - this may be expected during development"
fi

deactivate

echo ""
echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Configure Claude Desktop:"
echo "   Copy $CONFIG_FILE"
echo "   to ~/Library/Application Support/Claude/claude_desktop_config.json"
echo ""
echo "2. Restart Claude Desktop"
echo ""
echo "3. Test the server:"
echo "   cd servers/mcp-fgbio"
echo "   source venv/bin/activate"
echo "   python -m mcp_fgbio"
echo ""
echo "4. Try these prompts in Claude Desktop:"
echo "   - What MCP servers are available?"
echo "   - Tell me about the hg38 reference genome"
echo ""
echo "For more information, see docs/setup_guide.md"
echo ""
