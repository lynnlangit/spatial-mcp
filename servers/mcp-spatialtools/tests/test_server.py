"""Regression tests for Phase 8a.6 Fix 5 (mcp-spatialtools Moran's I auto-scale).

Covers:
1. Distance-threshold auto-scale fires for non-pixel (unit-scale) coordinates.
2. Moran's I DIFFERS between a clustered gene and a random gene on the same
   coordinate grid (would be identical under the old degenerate uniform-weights
   behaviour).
3. Spot-ID alignment between expression and coordinate files.
"""
import os
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Force real-calculation mode so the auto-scale branch runs
os.environ["SPATIAL_DRY_RUN"] = "false"

from mcp_spatialtools.server import (  # noqa: E402
    _calculate_morans_i,
    calculate_spatial_autocorrelation as _autocorr_tool,
)

# FastMCP wraps @mcp.tool() in FunctionTool; .fn is the underlying coroutine
calculate_spatial_autocorrelation = _autocorr_tool.fn


# ---------------------------------------------------------------------------
# Helpers — build a synthetic unit-scale spatial grid
# ---------------------------------------------------------------------------


def _make_unit_grid(side: int = 10) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (expression_df, coordinates_df) for an NxN unit-scale grid.

    Coordinates are in [0, side/10] (e.g. 0..1 for side=10), mimicking the
    PAT001 spatial fixture that exposed the auto-scale bug.
    """
    n = side * side
    # Unit-scale coordinates (0..1)
    xs = np.tile(np.linspace(0.0, 1.0, side), side)
    ys = np.repeat(np.linspace(0.0, 1.0, side), side)
    spot_ids = [f"spot_{i:04d}" for i in range(n)]

    coord_df = pd.DataFrame(
        {"x_coord": xs, "y_coord": ys},
        index=spot_ids,
    )

    # Clustered gene: high expression in the top-left quadrant, low elsewhere
    clustered = np.zeros(n)
    for i, (x, y) in enumerate(zip(xs, ys)):
        if x < 0.5 and y < 0.5:
            clustered[i] = 10.0 + np.random.default_rng(i).normal(0, 0.1)
        else:
            clustered[i] = 0.1 + np.random.default_rng(i + 10000).normal(0, 0.1)

    # Random gene: independent noise everywhere (seeded for determinism)
    rng = np.random.default_rng(42)
    random_gene = rng.normal(5.0, 1.0, size=n)

    expr_df = pd.DataFrame(
        {"CLUSTERED": clustered, "RANDOM": random_gene},
        index=spot_ids,
    )
    return expr_df, coord_df


# ---------------------------------------------------------------------------
# _calculate_morans_i unit tests
# ---------------------------------------------------------------------------


class TestMoransIDirectly:
    def test_clustered_gene_has_higher_morans_i_than_random(self):
        """On the same coordinate grid, a clustered gene should have a
        higher Moran's I than a random gene when the distance_threshold is
        chosen correctly for the coordinate scale."""
        expr_df, coord_df = _make_unit_grid(side=10)
        coords = coord_df[["x_coord", "y_coord"]].values

        # Use a threshold that gives each spot ~4-8 neighbors on the unit grid
        threshold = 0.2

        i_clustered, _, _ = _calculate_morans_i(
            expr_df["CLUSTERED"].values, coords, threshold
        )
        i_random, _, _ = _calculate_morans_i(
            expr_df["RANDOM"].values, coords, threshold
        )

        assert i_clustered > i_random, (
            f"Clustered gene Moran's I ({i_clustered:.4f}) should exceed "
            f"random gene Moran's I ({i_random:.4f})"
        )
        assert i_clustered > 0.3, (
            f"Clustered gene Moran's I ({i_clustered:.4f}) should indicate "
            f"strong positive spatial autocorrelation"
        )

    def test_old_bug_would_produce_identical_results(self):
        """With an oversized distance_threshold (pre-fix behaviour), every
        gene collapses to -1/(n-1). This test documents the old bug — with
        the new auto-scale logic, callers should never hit this path unless
        they explicitly opt-in with a non-sentinel value."""
        expr_df, coord_df = _make_unit_grid(side=10)
        coords = coord_df[["x_coord", "y_coord"]].values

        # Oversized threshold — every pair is a neighbor
        huge_threshold = 100.0

        i_clustered, _, _ = _calculate_morans_i(
            expr_df["CLUSTERED"].values, coords, huge_threshold
        )
        i_random, _, _ = _calculate_morans_i(
            expr_df["RANDOM"].values, coords, huge_threshold
        )

        # Both should collapse to ≈ -1/(n-1) = -1/99 ≈ -0.0101
        expected = -1.0 / (len(coords) - 1)
        assert abs(i_clustered - expected) < 1e-6
        assert abs(i_random - expected) < 1e-6


# ---------------------------------------------------------------------------
# Tool-level regression tests
# ---------------------------------------------------------------------------


class TestAutoScaleThreshold:
    @pytest.mark.asyncio
    async def test_auto_scale_threshold_unit_range(self, tmp_path):
        """With default distance_threshold=100.0 and unit-scale coordinates,
        the tool should auto-scale the threshold (Phase 8a.6 Fix 5) rather
        than leaving it at 100.0 and producing degenerate Moran's I."""
        expr_df, coord_df = _make_unit_grid(side=10)
        expr_path = tmp_path / "expr.csv"
        coord_path = tmp_path / "coords.csv"
        expr_df.to_csv(expr_path)
        coord_df.to_csv(coord_path)

        result = await calculate_spatial_autocorrelation(
            expression_file=str(expr_path),
            coordinates_file=str(coord_path),
            genes=["CLUSTERED", "RANDOM"],
            method="morans_i",
            # Leave distance_threshold at default to trigger auto-scale
        )

        assert result["status"] == "success"
        # Auto-scale should have kicked in and produced a tiny threshold
        assert result["distance_threshold"] != 100.0, (
            "distance_threshold remained at sentinel default — auto-scale "
            "did not fire"
        )
        assert result["distance_threshold"] < 1.0, (
            f"Auto-scaled threshold {result['distance_threshold']} should be "
            f"within the unit coordinate range (0-1)"
        )

    @pytest.mark.asyncio
    async def test_morans_i_differs_between_genes_with_unit_scale_coords(
        self, tmp_path
    ):
        """The headline regression: with unit-scale PAT001-like coordinates
        and default distance_threshold, Moran's I MUST differ between a
        clustered gene and a random gene. The old gate left threshold=100.0
        and every gene collapsed to the same -1/(n-1) value."""
        expr_df, coord_df = _make_unit_grid(side=10)
        expr_path = tmp_path / "expr.csv"
        coord_path = tmp_path / "coords.csv"
        expr_df.to_csv(expr_path)
        coord_df.to_csv(coord_path)

        result = await calculate_spatial_autocorrelation(
            expression_file=str(expr_path),
            coordinates_file=str(coord_path),
            genes=["CLUSTERED", "RANDOM"],
            method="morans_i",
        )

        assert result["status"] == "success"
        results_by_gene = {r["gene"]: r for r in result["results"]}
        i_clustered = results_by_gene["CLUSTERED"]["morans_i"]
        i_random = results_by_gene["RANDOM"]["morans_i"]

        assert i_clustered != i_random, (
            "Moran's I should differ between clustered and random genes; "
            "identical values indicate the degenerate uniform-weights bug"
        )
        assert i_clustered > i_random, (
            f"Clustered gene Moran's I ({i_clustered}) should exceed random "
            f"({i_random})"
        )
        assert i_clustered > 0.1, (
            f"Clustered gene should show meaningful spatial clustering, got "
            f"Moran's I = {i_clustered}"
        )


class TestSpotIdAlignment:
    @pytest.mark.asyncio
    async def test_expression_and_coordinates_subset_to_intersection(
        self, tmp_path
    ):
        """If expression and coordinates have partially overlapping indices,
        the tool should subset both to the intersection rather than
        computing on misaligned rows."""
        expr_df, coord_df = _make_unit_grid(side=5)
        # Drop a few spots from the coordinates file so the indices don't
        # match perfectly
        coord_df_partial = coord_df.iloc[:20]

        expr_path = tmp_path / "expr.csv"
        coord_path = tmp_path / "coords_partial.csv"
        expr_df.to_csv(expr_path)
        coord_df_partial.to_csv(coord_path)

        result = await calculate_spatial_autocorrelation(
            expression_file=str(expr_path),
            coordinates_file=str(coord_path),
            genes=["CLUSTERED"],
            method="morans_i",
        )

        assert result["status"] == "success"
        # num_spots should reflect the intersection size (20), not 25
        assert result["num_spots"] == 20

    @pytest.mark.asyncio
    async def test_disjoint_spot_ids_returns_error(self, tmp_path):
        """Completely disjoint indices should surface a clear error, not
        silently compute garbage."""
        expr_df, coord_df = _make_unit_grid(side=5)
        # Rename coordinate index to something completely disjoint
        coord_df_disjoint = coord_df.copy()
        coord_df_disjoint.index = [f"other_{i}" for i in range(len(coord_df))]

        expr_path = tmp_path / "expr.csv"
        coord_path = tmp_path / "coords_disjoint.csv"
        expr_df.to_csv(expr_path)
        coord_df_disjoint.to_csv(coord_path)

        result = await calculate_spatial_autocorrelation(
            expression_file=str(expr_path),
            coordinates_file=str(coord_path),
            genes=["CLUSTERED"],
            method="morans_i",
        )

        assert result["status"] == "error"
        assert "spot" in result["error"].lower() or "match" in result["error"].lower()
