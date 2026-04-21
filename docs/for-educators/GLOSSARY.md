# HGSOC Platform Glossary

For educators and students. Each term includes a plain-English definition followed by a technical note.

Last reviewed: April 21, 2026. Suggest corrections via GitHub issue.

---

## HRD

**Plain English:** Homologous Recombination Deficiency is a measure of how broken a cancer cell's DNA-repair machinery is. A higher score means the cell has more trouble fixing its own DNA, which paradoxically makes it more vulnerable to certain drugs (PARP inhibitors) that exploit this weakness.

**Technical note:** HRD score is a composite of three genomic scar signatures (LOH, TAI, LST); a score above 42 is generally considered clinically significant for PARP inhibitor sensitivity.

## TMB

**Plain English:** Tumor Mutational Burden counts how many mutations exist in a region of the cancer's DNA. Cancers with lots of mutations sometimes respond better to immunotherapy because the immune system has more "targets" to recognize.

**Technical note:** TMB is expressed as mutations per megabase (mut/Mb) of sequenced DNA; thresholds vary by assay, but 10 mut/Mb is a common cutoff for "TMB-high."

## Neoantigen

**Plain English:** A neoantigen is a tiny piece of a mutated protein that appears on the surface of a cancer cell. Because it comes from a mutation, the immune system can potentially recognize it as foreign and attack the cancer cell.

**Technical note:** Neoantigens are peptide fragments (typically 8-11 amino acids for MHC-I) generated from somatic mutations, presented via MHC molecules, and recognized by T-cell receptors.

## IC50

**Plain English:** IC50 tells you how tightly a molecule (like a neoantigen peptide) binds to its target. A lower number means stronger binding. For cancer vaccines, lower IC50 values mean the immune system is more likely to notice and attack that peptide.

**Technical note:** IC50 is the half-maximal inhibitory concentration in nM; for MHC-I binding predictions, IC50 < 50 nM is typically classified as a strong binder, 50-500 nM as weak, and > 500 nM as non-binder.

## MHC-I

**Plain English:** Major Histocompatibility Complex class I is a display shelf on the surface of every cell in your body. It holds up small pieces of proteins for immune cells to inspect. If an immune cell sees a foreign fragment (like a neoantigen), it can trigger an attack on that cell.

**Technical note:** MHC-I molecules (encoded by HLA-A, -B, -C genes in humans) present endogenous peptides to CD8+ cytotoxic T lymphocytes; allele-specific binding affinity determines which peptides are presented.

## Spatial transcriptomics

**Plain English:** Spatial transcriptomics is a technique that measures which genes are active in a tissue sample while preserving the physical location of each measurement. Think of it as creating a map where each pin shows what genes are turned on at that exact spot in the tissue.

**Technical note:** Technologies like 10x Visium capture mRNA at spatially barcoded spots (~55 um diameter, ~5,000 spots per capture area), enabling spatially resolved gene expression profiling.

## Moran's I

**Plain English:** Moran's I is a number that tells you whether nearby spots in a tissue have similar gene activity (clustered), different activity (dispersed), or no pattern (random). Values near zero mean random; positive means clustered; negative means dispersed.

**Technical note:** Moran's I is a spatial autocorrelation statistic ranging from -1 (perfect dispersion) to +1 (perfect clustering), with an expected value of -1/(n-1) under the null hypothesis of spatial randomness.

## Deconvolution

**Plain English:** Deconvolution is a computational technique that takes a mixed signal from a tissue sample and figures out what cell types are present and in what proportions. It is like hearing a choir and working out how many sopranos, altos, tenors, and basses are singing.

**Technical note:** Immune deconvolution (e.g., CIBERSORTx with LM22 signature matrix) uses constrained linear regression or support vector regression to infer cell-type fractions from bulk or spatial gene expression data.

## Perturbation

**Plain English:** A perturbation is a deliberate change made to a biological system to see what happens. In this platform, we simulate what would happen if specific genes were knocked down (turned off) in cancer cells, to predict whether that change would make the cancer more treatable.

**Technical note:** In silico perturbation prediction uses graph neural networks (e.g., GEARS) trained on Perturb-seq data to predict post-perturbation gene expression shifts without wet-lab experiments.

## GEARS

**Plain English:** GEARS is a machine-learning model that predicts how cells will behave when specific genes are knocked out. It can forecast the effect of gene combinations that have never been tested in a lab, helping researchers prioritize which experiments to run.

**Technical note:** GEARS (Graph-Enhanced Gene Activation and Repression Simulator) is a GNN model by Roohani et al. (2023) that leverages gene-gene interaction graphs to predict combinatorial perturbation outcomes from single-gene training data.

## Quantum circuit

**Plain English:** A quantum circuit is a sequence of operations on quantum bits (qubits) that processes information using quantum physics. In this platform, quantum circuits are used to classify cell types, potentially offering advantages for certain pattern-recognition tasks.

**Technical note:** Parameterized quantum circuits (PQCs) use tunable rotation gates (RY, RZ) and entangling gates (CNOT) to embed classical feature vectors into Hilbert space for supervised classification via variational optimization.

## Variational autoencoder

**Plain English:** A variational autoencoder (VAE) is an AI model that learns to compress complex data into a compact summary and then reconstruct it. In biology, VAEs can learn meaningful representations of gene expression data, revealing hidden patterns like cell subtypes.

**Technical note:** A VAE consists of an encoder q(z|x) and decoder p(x|z) trained by maximizing the evidence lower bound (ELBO); the latent space z provides a low-dimensional, continuous embedding of high-dimensional input data.

## FastMCP

**Plain English:** FastMCP is a Python framework that makes it easy to build MCP servers. Developers write a Python function, add a decorator, and FastMCP handles all the networking and protocol details so AI assistants like Claude can call that function.

**Technical note:** FastMCP wraps the Model Context Protocol Python SDK, providing `@mcp.tool()` decorators, automatic Pydantic validation, and transport auto-detection (stdio, SSE) for rapid server development.

## MCP server

**Plain English:** An MCP server is a small program that exposes specific analysis tools over the Model Context Protocol. Each server in this platform handles one domain (genomics, imaging, spatial analysis, etc.) and can be called by an AI assistant using natural language.

**Technical note:** MCP servers implement the Model Context Protocol specification (2025-06-18), exposing tools as JSON-RPC endpoints with typed input/output schemas, discoverable by any MCP-compatible client.

## DRY_RUN mode

**Plain English:** DRY_RUN mode makes every server return realistic-looking but entirely synthetic results, without connecting to external databases or running heavy computations. It is the safe default for teaching, testing, and development.

**Technical note:** Controlled by per-server environment variables (e.g., `FGBIO_DRY_RUN=true`), DRY_RUN mode returns mock payloads that match the live schema, with a `"dry_run": true` flag so callers can distinguish synthetic from real results.
