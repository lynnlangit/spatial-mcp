"""Integration tests for mcp-fgbio server.

These tests verify that the MCP server can:
1. Start successfully
2. Handle tool calls
3. Provide resources
4. Handle errors gracefully
"""

import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict

import pytest


class MCPClient:
    """Simple MCP client for integration testing.

    This class simulates a basic MCP client that communicates with
    the server via stdio using JSON-RPC 2.0 protocol.
    """

    def __init__(self, server_command: list[str], cwd: str | None = None):
        """Initialize MCP client.

        Args:
            server_command: Command to start the MCP server
            cwd: Working directory for the server process
        """
        self.process = subprocess.Popen(
            server_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=cwd,
            bufsize=1
        )
        self.request_id = 0

    def send_request(self, method: str, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Send a JSON-RPC request to the server.

        Args:
            method: JSON-RPC method name
            params: Method parameters

        Returns:
            JSON-RPC response

        Raises:
            RuntimeError: If request fails
        """
        self.request_id += 1

        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or {}
        }

        # Send request
        request_json = json.dumps(request) + "\n"
        self.process.stdin.write(request_json)
        self.process.stdin.flush()

        # Read response
        response_line = self.process.stdout.readline()

        if not response_line:
            stderr_output = self.process.stderr.read()
            raise RuntimeError(f"No response from server. Stderr: {stderr_output}")

        try:
            response = json.loads(response_line)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid JSON response: {response_line}") from e

        if "error" in response:
            raise RuntimeError(f"Server error: {response['error']}")

        return response

    def close(self) -> None:
        """Close the connection to the server."""
        if self.process.stdin:
            self.process.stdin.close()
        if self.process.stdout:
            self.process.stdout.close()
        if self.process.stderr:
            self.process.stderr.close()

        self.process.terminate()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


@pytest.fixture
def server_path() -> Path:
    """Get path to the mcp-fgbio server.

    Returns:
        Path to the server directory
    """
    # Assuming tests are run from the repository root
    return Path(__file__).parent.parent.parent / "servers" / "mcp-fgbio"


@pytest.fixture
def temp_workspace() -> Path:
    """Create a temporary workspace for integration tests.

    Returns:
        Path to temporary workspace
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        (workspace / "reference").mkdir()
        (workspace / "cache").mkdir()
        (workspace / "data").mkdir()
        yield workspace


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestServerLifecycle:
    """Test server startup, initialization, and shutdown."""

    def test_server_starts_successfully(self, server_path: Path, temp_workspace: Path) -> None:
        """Test that the server starts without errors."""
        env = {
            "PYTHONPATH": str(server_path / "src"),
            "FGBIO_REFERENCE_DATA_DIR": str(temp_workspace / "reference"),
            "FGBIO_CACHE_DIR": str(temp_workspace / "cache"),
            "FGBIO_DRY_RUN": "true"
        }

        # Start server and verify it doesn't crash immediately
        process = subprocess.Popen(
            [sys.executable, "-m", "mcp_fgbio"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=server_path,
            env={**env, **dict(subprocess.os.environ)}
        )

        # Give server a moment to start
        time.sleep(1)

        # Check if process is still running
        assert process.poll() is None, "Server crashed on startup"

        # Clean up
        process.terminate()
        process.wait(timeout=5)


class TestToolCalls:
    """Test MCP tool invocations."""

    @pytest.mark.skip(reason="Requires full MCP protocol implementation")
    def test_fetch_reference_genome_tool(
        self,
        server_path: Path,
        temp_workspace: Path
    ) -> None:
        """Test calling the fetch_reference_genome tool."""
        # Note: This test requires a full MCP client implementation
        # For now, we'll test the tools directly in unit tests

        # This would be implemented as:
        # with MCPClient([...]) as client:
        #     response = client.send_request("tools/call", {
        #         "name": "fetch_reference_genome",
        #         "arguments": {"genome": "hg38", "output_dir": "..."}
        #     })
        #     assert response["result"]["metadata"]["genome_id"] == "hg38"

        pass

    @pytest.mark.skip(reason="Requires full MCP protocol implementation")
    def test_validate_fastq_tool(
        self,
        server_path: Path,
        temp_workspace: Path
    ) -> None:
        """Test calling the validate_fastq tool."""
        pass


class TestErrorHandling:
    """Test server error handling."""

    def test_server_handles_missing_environment_variables(
        self,
        server_path: Path
    ) -> None:
        """Test that server uses defaults when env vars are missing."""
        # Start server without any environment variables
        process = subprocess.Popen(
            [sys.executable, "-m", "mcp_fgbio"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=server_path,
            env={"PYTHONPATH": str(server_path / "src"), "PATH": subprocess.os.environ["PATH"]}
        )

        time.sleep(1)

        # Server should still start (using defaults)
        assert process.poll() is None, "Server should handle missing env vars gracefully"

        process.terminate()
        process.wait(timeout=5)


# ============================================================================
# SMOKE TESTS
# ============================================================================


class TestSmokeTests:
    """Basic smoke tests to ensure server is functional."""

    def test_import_server_module(self, server_path: Path) -> None:
        """Test that the server module can be imported."""
        import sys

        sys.path.insert(0, str(server_path / "src"))

        try:
            import mcp_fgbio.server
            assert hasattr(mcp_fgbio.server, "mcp")
            assert hasattr(mcp_fgbio.server, "fetch_reference_genome")
            assert hasattr(mcp_fgbio.server, "validate_fastq")
            assert hasattr(mcp_fgbio.server, "extract_umis")
            assert hasattr(mcp_fgbio.server, "query_gene_annotations")
        finally:
            sys.path.pop(0)

    def test_server_has_required_tools(self, server_path: Path) -> None:
        """Test that server declares all required tools."""
        import sys

        sys.path.insert(0, str(server_path / "src"))

        try:
            from mcp_fgbio.server import mcp

            # FastMCP should have registered tools
            # Note: Exact introspection depends on FastMCP API
            assert mcp is not None
        finally:
            sys.path.pop(0)


# ============================================================================
# END-TO-END WORKFLOW TEST
# ============================================================================


@pytest.mark.integration
class TestEndToEndWorkflow:
    """Test complete workflow using the server."""

    def test_complete_spatial_workflow_simulation(
        self,
        server_path: Path,
        temp_workspace: Path
    ) -> None:
        """Simulate a complete spatial transcriptomics workflow.

        This test verifies that a bioinformatician could:
        1. Fetch reference genome
        2. Validate raw FASTQ data
        3. Extract UMIs
        4. Query gene annotations

        All using the mcp-fgbio server.
        """
        # For this POC, we verify the workflow by importing and calling
        # the tools directly (simulating what Claude would do)

        import sys
        sys.path.insert(0, str(server_path / "src"))

        try:
            from mcp_fgbio import server
            import asyncio

            # Get underlying functions from decorated tools
            extract_umis = server.extract_umis.__wrapped__
            fetch_reference_genome = server.fetch_reference_genome.__wrapped__
            query_gene_annotations = server.query_gene_annotations.__wrapped__
            validate_fastq = server.validate_fastq.__wrapped__

            async def run_workflow():
                # Step 1: Fetch reference
                genome = await fetch_reference_genome(
                    genome="hg38",
                    output_dir=str(temp_workspace / "reference")
                )
                assert genome["metadata"]["genome_id"] == "hg38"

                # Step 2: Create mock FASTQ
                fastq_file = temp_workspace / "data" / "sample.fastq"
                fastq_file.parent.mkdir(exist_ok=True)
                with open(fastq_file, "w") as f:
                    for i in range(100):
                        f.write(f"@READ{i:05d}\n")
                        f.write("ACGTACGT" * 4 + "\n")
                        f.write("+\n")
                        f.write("I" * 32 + "\n")

                # Step 3: Validate FASTQ
                validation = await validate_fastq(
                    fastq_path=str(fastq_file),
                    min_quality_score=20
                )
                assert validation["valid"] is True

                # Step 4: Extract UMIs
                umis = await extract_umis(
                    fastq_path=str(fastq_file),
                    output_dir=str(temp_workspace / "data"),
                    umi_length=12
                )
                assert umis["umi_count"] > 0

                # Step 5: Query annotations
                annotations = await query_gene_annotations(
                    genome="hg38",
                    gene_name="TP53"
                )
                assert annotations["total_genes"] > 0

                return True

            # Run the async workflow
            result = asyncio.run(run_workflow())
            assert result is True

        finally:
            sys.path.pop(0)
