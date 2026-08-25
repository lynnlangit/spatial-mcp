"""Copy-number and governance tooling for tumour-only panel data.

Every public entry point here returns a `GradedResult` (see
`shared/common/graded_result.py`). A bare number does not leave this package.

Order of operations, which is also the dependency order:

    detect_library_chemistry     the gate — required input to everything below
      -> extract_heterozygous_sites
        -> qc_heterozygous_sites
          -> estimate_tumor_purity / assess_cnv_detectability
            -> test_allelic_imbalance
              -> compare_cnv_architectures
                -> assess_um_prognostic_class
"""

from .chemistry import ChemistryGateError, PysamUnavailable, require_chemistry

__all__ = ["ChemistryGateError", "PysamUnavailable", "require_chemistry"]
