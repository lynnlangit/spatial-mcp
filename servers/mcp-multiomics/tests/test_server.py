"""Regression tests for mcp-multiomics Fix 1 (FastMCP 2.x JSON-string coercion).

Tests that tools accept Optional[Dict] / Optional[List] parameters both as
native Python types and as JSON-encoded strings, which FastMCP 2.x may deliver
from some LLM clients before Pydantic validation.
"""
import json
import os

import pytest

# Ensure dry-run so tests don't hit real pipelines
os.environ.setdefault("MULTIOMICS_DRY_RUN", "true")

from mcp_multiomics.server import (  # noqa: E402
    _coerce_dict,
    _coerce_list,
)
from mcp_multiomics.server import calculate_stouffer_meta as _stouffer_tool  # noqa: E402
from mcp_multiomics.server import create_multiomics_heatmap as _heatmap_tool  # noqa: E402
from mcp_multiomics.server import (  # noqa: E402
    predict_upstream_regulators as _regulators_tool,
)
from mcp_multiomics.server import run_multiomics_pca as _pca_tool  # noqa: E402
from mcp_multiomics.server import (  # noqa: E402
    visualize_data_quality as _visualize_tool,
)

# FastMCP wraps @mcp.tool() functions in FunctionTool; .fn exposes the underlying
# callable so tests exercise the full coercion path.
calculate_stouffer_meta = _stouffer_tool.fn
create_multiomics_heatmap = _heatmap_tool.fn
predict_upstream_regulators = _regulators_tool.fn
run_multiomics_pca = _pca_tool.fn
visualize_data_quality = _visualize_tool.fn


# ---------------------------------------------------------------------------
# Pure helper tests
# ---------------------------------------------------------------------------


class TestCoerceDict:
    def test_none_passthrough(self):
        assert _coerce_dict(None) is None

    def test_native_dict_passthrough(self):
        d = {"a": 1, "b": [2, 3]}
        assert _coerce_dict(d) is d

    def test_json_string_decoded(self):
        s = '{"rna": [0.01, 0.05], "protein": [0.02, 0.04]}'
        out = _coerce_dict(s)
        assert out == {"rna": [0.01, 0.05], "protein": [0.02, 0.04]}

    def test_invalid_json_raises(self):
        with pytest.raises(ValueError, match="unparseable"):
            _coerce_dict("{not valid json")

    def test_non_dict_json_raises(self):
        with pytest.raises(ValueError, match="Expected dict"):
            _coerce_dict("[1, 2, 3]")

    def test_wrong_type_raises(self):
        with pytest.raises(ValueError, match="Cannot coerce"):
            _coerce_dict(42)


class TestCoerceList:
    def test_none_passthrough(self):
        assert _coerce_list(None) is None

    def test_native_list_passthrough(self):
        lst = ["kinase", "transcription_factor"]
        assert _coerce_list(lst) is lst

    def test_json_string_decoded(self):
        out = _coerce_list('["kinase", "drug"]')
        assert out == ["kinase", "drug"]

    def test_invalid_json_raises(self):
        with pytest.raises(ValueError, match="unparseable"):
            _coerce_list("[not, valid")

    def test_non_list_json_raises(self):
        with pytest.raises(ValueError, match="Expected list"):
            _coerce_list('{"a": 1}')


# ---------------------------------------------------------------------------
# Tool-level regression tests (native + JSON-string inputs both succeed)
# ---------------------------------------------------------------------------


class TestStoufferMetaCoercion:
    def test_native_dict_params(self):
        result = calculate_stouffer_meta(
            p_values_dict={
                "rna": [0.001, 0.05, 0.3],
                "protein": [0.002, 0.04, 0.25],
            },
            effect_sizes_dict={
                "rna": [2.5, 1.2, -0.3],
                "protein": [1.8, 1.5, -0.2],
            },
            weights={"rna": 1.0, "protein": 1.0},
            use_directionality=True,
        )
        assert result["status"].startswith("success")

    def test_json_string_params(self):
        result = calculate_stouffer_meta(
            p_values_dict=json.dumps({
                "rna": [0.001, 0.05, 0.3],
                "protein": [0.002, 0.04, 0.25],
            }),
            effect_sizes_dict=json.dumps({
                "rna": [2.5, 1.2, -0.3],
                "protein": [1.8, 1.5, -0.2],
            }),
            weights=json.dumps({"rna": 1.0, "protein": 1.0}),
            use_directionality=True,
        )
        assert result["status"].startswith("success")

    def test_none_optional_params(self):
        result = calculate_stouffer_meta(
            p_values_dict={"rna": [0.001, 0.05], "protein": [0.002, 0.04]},
            effect_sizes_dict=None,
            weights=None,
        )
        assert result["status"].startswith("success")


class TestPredictUpstreamRegulatorsCoercion:
    def test_native_params(self):
        result = predict_upstream_regulators(
            differential_genes={
                "AKT1": {"log2fc": 2.5, "p_value": 0.0001},
                "TP53": {"log2fc": -2.1, "p_value": 0.0005},
            },
            regulator_types=["kinase", "transcription_factor"],
        )
        assert result["status"].startswith("success")

    def test_json_string_params(self):
        result = predict_upstream_regulators(
            differential_genes=json.dumps({
                "AKT1": {"log2fc": 2.5, "p_value": 0.0001},
                "TP53": {"log2fc": -2.1, "p_value": 0.0005},
            }),
            regulator_types=json.dumps(["kinase", "drug"]),
        )
        assert result["status"].startswith("success")


class TestBlastRadiusCoercion:
    """The three blast-radius candidates should also accept JSON-string inputs."""

    def test_visualize_data_quality_json_dicts(self):
        result = visualize_data_quality(
            data_paths=json.dumps({
                "rna": "/data/rna_preprocessed.csv",
                "protein": "/data/protein_preprocessed.csv",
            }),
            before_data_paths=json.dumps({"rna": "/data/rna_raw.csv"}),
            compare_before_after=True,
        )
        assert result["status"].startswith("success")

    def test_create_multiomics_heatmap_json_list(self):
        result = create_multiomics_heatmap(
            data_path="/cache/integrated.pkl",
            features='["TP53", "MYC", "EGFR"]',
        )
        assert result["status"].startswith("success")

    def test_run_multiomics_pca_json_list(self):
        result = run_multiomics_pca(
            data_path="/cache/integrated.pkl",
            modalities='["rna", "protein"]',
            n_components=3,
        )
        assert result["status"].startswith("success")
