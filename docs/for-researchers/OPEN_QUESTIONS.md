# Open Research Questions

These are questions the HGSOC precision oncology platform is positioned to help answer,
pending access to real clinical cohort data.

1. **Does HRD score >= 42 predict PARP inhibitor response in HGSOC patients with BRCA1/2 wild-type tumors?**
   This matters clinically because most PARP inhibitor approvals target BRCA-mutant tumors, but HRD-high wild-type patients may also benefit. Servers: `genomic-results` (`calculate_hr_deficiency_score`), `mocktcga` (`get_survival_data`). Data needed: real TCGA HGSOC cohort with treatment outcomes.

2. **Which MHC-I neoantigen binding thresholds (IC50 cutoffs) best predict CD8+ T cell infiltration in HGSOC?**
   Clinically, identifying the IC50 value that correlates with actual immune response would improve neoantigen vaccine design. Servers: `neoantigen` (`predict_mhc1_binding`), `cell-classify` (`classify_cell_states`). Data needed: paired neoantigen and TIL data from HGSOC tumor bank.

3. **Does spatial clustering of CD8+ T cells (Moran's I > 0.1) predict checkpoint immunotherapy response?**
   Clustered vs dispersed immune infiltration may predict which patients benefit from PD-1/PD-L1 blockade. Servers: `spatialtools` (`calculate_spatial_autocorrelation`, `deconvolve_cell_types`). Data needed: spatial transcriptomics plus treatment response data from a treated HGSOC cohort.

4. **Can GEARS perturbation modeling identify synthetic lethal combinations with PARP inhibitors in HRD-high HGSOC?**
   Identifying gene knockdowns that sensitize cells to olaparib could reveal new combination strategies. Servers: `perturbation` (`perturbation_predict_response`), `genomic-results`. Data needed: GEARS model retrained on real HGSOC perturbation screen data.

5. **What is the concordance between this platform's therapeutic hypotheses and actual tumor board decisions in a retrospective HGSOC cohort?**
   This is the core validation question for clinical deployment. Servers: all 18. Data needed: 50+ de-identified retrospective HGSOC cases with documented tumor board decisions.

6. **Does high TMB (> 10 mut/Mb) in HGSOC correlate with neoantigen burden and predict immunotherapy benefit independently of HRD?**
   TMB and HRD may act as independent or synergistic predictors. Servers: `genomic-results` (`parse_somatic_variants`), `neoantigen`. Data needed: TCGA HGSOC WES plus immunotherapy response data.

7. **Can spatial cell neighborhood composition (macrophage-to-CD8 ratio) predict platinum resistance in HGSOC?**
   Platinum resistance is the primary cause of HGSOC mortality; early spatial biomarkers could guide second-line therapy selection. Servers: `spatialtools` (`generate_region_composition_chart`, `perform_differential_expression`). Data needed: pre-treatment spatial transcriptomics from platinum-sensitive vs resistant HGSOC patients.

8. **Does multi-modal integration (HRD + neoantigen + spatial + perturbation) outperform single-modality prediction for HGSOC outcomes?**
   The core scientific premise of this platform needs formal validation against clinical outcomes data. Servers: `multiomics` (`integrate_omics_data`). Data needed: complete multi-modal dataset for >= 100 HGSOC patients with survival outcomes.

9. **Can the quantum server's cell-state embedding improve deconvolution accuracy over classical methods for low-cellularity HGSOC biopsies?**
   Low-cellularity biopsies are common in recurrent HGSOC; quantum approaches may outperform classical methods on sparse data. Servers: `quantum-celltype-fidelity`, `cell-classify`. Data needed: paired low- and high-cellularity biopsies from the same patient with known ground-truth composition.

10. **What is the minimum viable biopsy size (number of spatial spots) needed for reliable deconvolution and Moran's I calculation?**
    Smaller biopsies are clinically preferable; understanding the floor for reliable AI analysis informs biopsy protocol design. Servers: `spatialtools` (`filter_quality`, `calculate_spatial_autocorrelation`). Data needed: titration experiment with biopsies of known composition at varying spot counts.

---
Researchers interested in collaborating: open a GitHub issue with the `research-question`
label or email {{RESEARCH_CONTACT}}.
