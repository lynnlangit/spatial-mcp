#!/usr/bin/env python3
"""
Test script to verify all 8 MCP servers can be imported and their tools are accessible.
This validates the POC is properly set up for manual testing.
"""

import sys
import os
from pathlib import Path

# Add server paths to PYTHONPATH
repo_root = Path(__file__).parent
servers = [
    "mcp-fgbio",
    "mcp-spatialtools",
    "mcp-openimagedata",
    "mcp-seqera",
    "mcp-huggingface",
    "mcp-deepcell",
    "mcp-mockepic",
    "mcp-tcga"
]

print("=" * 80)
print("Spatial MCP POC - Server Verification Test")
print("=" * 80)
print()

# Test each server
results = {}
total_tools = 0

for server_name in servers:
    server_path = repo_root / "servers" / server_name / "src"
    sys.path.insert(0, str(server_path))

    try:
        # Import the server module
        module_name = server_name.replace("-", "_")
        server_module = __import__(f"{module_name}.server", fromlist=["mcp"])

        # Get the MCP instance
        mcp = server_module.mcp

        # Count tools
        tools = [name for name in dir(mcp) if not name.startswith('_')]
        tool_count = len([t for t in tools if hasattr(getattr(mcp, t), 'fn') or hasattr(getattr(mcp, t), '__wrapped__')])

        # Try to access tools more directly
        if hasattr(mcp, '_tools'):
            tool_count = len(mcp._tools)
        elif hasattr(mcp, 'list_tools'):
            # For FastMCP, tools are registered internally
            tool_count = "Available"

        results[server_name] = {
            "status": "✅ OK",
            "tools": tool_count,
            "module": module_name
        }

        print(f"✅ {server_name:25s} - Loaded successfully")

    except ImportError as e:
        results[server_name] = {
            "status": "❌ IMPORT ERROR",
            "error": str(e)
        }
        print(f"❌ {server_name:25s} - Import failed: {e}")

    except Exception as e:
        results[server_name] = {
            "status": "❌ ERROR",
            "error": str(e)
        }
        print(f"❌ {server_name:25s} - Error: {e}")

print()
print("=" * 80)
print("Summary")
print("=" * 80)

success_count = sum(1 for r in results.values() if r["status"] == "✅ OK")
print(f"\nServers loaded: {success_count}/{len(servers)}")

if success_count == len(servers):
    print("\n🎉 All MCP servers loaded successfully!")
    print("\nNext steps:")
    print("1. Install each server's dependencies if needed:")
    print("   cd servers/<server-name>")
    print("   pip install -e .")
    print("\n2. Configure Claude Desktop with configs/claude_desktop_config_complete.json")
    print("\n3. Test with example prompts from docs/MCP_POC_Example_Prompts.md")
else:
    print("\n⚠️  Some servers failed to load. Check dependencies.")
    print("\nFailed servers:")
    for name, result in results.items():
        if result["status"] != "✅ OK":
            print(f"  - {name}: {result.get('error', 'Unknown error')}")

print()
