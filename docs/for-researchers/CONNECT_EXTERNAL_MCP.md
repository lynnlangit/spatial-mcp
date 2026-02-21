# Connect: External MCP Servers for Life Sciences

Add literature search, clinical trials, preprint access, and ML model discovery to your precision medicine workflow. These run alongside our custom servers — no changes to existing platform configuration.

```mermaid
graph LR
    subgraph Anthropic Connectors — toggle on, no install
        CT[ClinicalTrials.gov<br/>6 tools]
        BIO[bioRxiv & medRxiv<br/>9 tools]
        PM[PubMed<br/>5 capabilities]
        SQ[Seqera<br/>7 tools]
    end
    subgraph Community Servers — install locally
        CB[cBioPortal · TCGA<br/>12 tools]
        HF[Hugging Face<br/>7 tools]
    end
    style CT fill:#e8f4e8,stroke:#4a9
    style BIO fill:#e8f4e8,stroke:#4a9
    style PM fill:#e8f4e8,stroke:#4a9
    style SQ fill:#e8f4e8,stroke:#4a9
    style CB fill:#e8eaf4,stroke:#49a
    style HF fill:#e8eaf4,stroke:#49a
```

| | Anthropic Connectors (hosted) | Community MCP Servers (self-hosted) |
|---|---|---|
| **What** | Remote servers hosted by Anthropic | Open source servers you run locally |
| **Setup** | Toggle on in Settings > Connectors | Add config JSON or use `claude mcp add` CLI |
| **Install** | Nothing to install | Requires Node.js, Python, or similar |
| **Auth** | Handled by Anthropic | You manage API keys and tokens |
| **Examples below** | ClinicalTrials.gov, bioRxiv, PubMed, Seqera | cBioPortal (TCGA), Hugging Face |

---

## Anthropic Connectors (hosted)

Remote MCP servers hosted by Anthropic. Enable with a toggle — no install, no config files, no API keys. Anthropic manages the infrastructure.

**Setup (same for all connectors):** Claude Desktop > Settings > Connectors > find the connector > click Connect

### ClinicalTrials.gov

Search 500,000+ FDA-regulated clinical studies. Find trials by condition, sponsor, phase, or patient eligibility. Analyze endpoints across trials.

#### Available Tools (6)

| Tool | What it does | Example use |
|------|-------------|-------------|
| `search_trials` | Search by condition, intervention, location, status, phase | Find recruiting ovarian cancer trials |
| `get_trial_details` | Full protocol for a specific NCT ID | Get eligibility criteria for NCT04567890 |
| `search_by_sponsor` | All trials by a company or institution | Analyze AstraZeneca's PARP inhibitor pipeline |
| `search_investigators` | Find PIs and research sites | Identify ovarian cancer investigators at Dana-Farber |
| `analyze_endpoints` | Compare outcome measures across trials | Aggregate Phase 3 ovarian cancer endpoints |
| `search_by_eligibility` | Match patient criteria to open trials | Find trials for 65yo female with BRCA1+ HGSOC |

#### Example Prompts

```
"Search ClinicalTrials.gov for recruiting Phase 2/3 trials testing PARP inhibitors
in platinum-resistant ovarian cancer."

"Find all trials sponsored by AstraZeneca for ovarian cancer and summarize their
primary endpoints by phase."

"What recruiting trials could a 58-year-old female with BRCA1-mutated, Stage IV
HGSOC, ECOG 1, who has failed two prior lines of platinum therapy, be eligible for?"
```

### bioRxiv & medRxiv

Access 260,000+ preprints across 27 bioRxiv and 40+ medRxiv categories. Find the latest research before peer review, track which preprints have been published, and analyze submission trends.

#### Available Tools (9)

| Tool | What it does | Example use |
|------|-------------|-------------|
| `search_preprints` | Search by date range, subject, or recent submissions | Find spatial transcriptomics preprints from last month |
| `get_preprint` | Full metadata, abstract, author info, publication status | Get details for a specific preprint DOI |
| `get_categories` | List all 27 bioRxiv subject categories | Browse available disciplines |
| `search_published_articles` | Track preprints that became peer-reviewed papers | Check if a preprint was published in a journal |
| `search_biorxiv_publications` | Simplified bioRxiv publication tracking | Quick publication status lookup |
| `search_publisher_articles` | Filter by specific journals or publishers | Find preprints published in Nature Cancer |
| `search_by_funder` | Discover research by funding organization | Find NCI-funded ovarian cancer preprints |
| `get_content_statistics` | Platform submission volumes and growth | Analyze preprint trends in oncology |
| `get_usage_statistics` | Abstract views, full-text views, PDF downloads | Gauge research impact before publication |

#### Example Prompts

```
"Search bioRxiv for preprints on tumor microenvironment spatial transcriptomics
in ovarian cancer from the last 6 months."

"Find recent medRxiv preprints about PARP inhibitor combinations and platinum
resistance mechanisms."

"Look up preprints on single-cell RNA sequencing of high-grade serous ovarian
cancer and check which ones have been published in peer-reviewed journals."
```

### PubMed

Search 36M+ biomedical citations from the NLM. Find articles by keyword, author, or journal. Retrieve abstracts, full text (when available via PMC), and related articles. Convert between PMID, PMC ID, and DOI formats.

#### Capabilities

| Capability | Example use |
|------------|-------------|
| Article search | Find ovarian cancer immunotherapy papers by keyword, author, or MeSH term |
| Metadata retrieval | Get abstracts, authors, publication dates, citations for a PMID |
| Full-text access | Retrieve complete articles from PubMed Central (when available) |
| Related articles | Discover similar research across NCBI databases |
| Citation matching | Convert between PMID, PMC ID, and DOI formats |

#### Example Prompts

```
"Search PubMed for recent papers on PARP inhibitor resistance in BRCA1-mutated
ovarian cancer, then summarize the top 3 findings."

"Find publications about PIK3CA H1047R mutation and targeted therapy response
in high-grade serous ovarian cancer."

"Search for spatial transcriptomics studies of the tumor microenvironment in
ovarian cancer published since 2023."
```

### Seqera

Nextflow workflow orchestration via Seqera Platform. Launch nf-core pipelines, monitor runs, search modules, and troubleshoot failures via natural language. Free for all Seqera users.

> **Cost:** The Seqera connector itself is free. Seqera Platform has a free Cloud Basic tier (250 runs, 3 users). Academic institutions can apply for free Cloud Pro. Compute (if using Seqera Cloud): $0.10/CPU-hour, $0.025/GiB-hour. See [seqera.io/pricing](https://seqera.io/pricing/).

#### Available Tools (7)

| Tool | What it does | Example use |
|------|-------------|-------------|
| `call_seqera_api` | Call Seqera Platform API endpoints | Get details on a specific workflow run |
| `search_seqera_api` | Search across Seqera Platform resources | Find recent failed runs in your workspace |
| `call_data_tool` | Manage and access datasets in Seqera | List datasets available for a pipeline |
| `search_data_tool` | Search for data tools and resources | Find data tools for spatial transcriptomics |
| `describe_nfcore_module` | Get details on a specific nf-core module | Describe the STAR alignment module |
| `search_nfcore_module` | Search the nf-core module registry | Find modules for variant calling |
| `nfcore_suggest_analysis` | Suggest nf-core pipelines for your analysis | Recommend a pipeline for RNA-seq of HGSOC samples |

#### Example Prompts

```
"What nf-core pipelines are available for spatial transcriptomics analysis?"

"Search Seqera for my recent workflow runs and tell me if any failed.
If so, what went wrong?"

"Suggest an analysis pipeline for bulk RNA-seq of platinum-resistant
high-grade serous ovarian cancer samples, and describe the key modules."
```

---

## Community MCP Servers (self-hosted)

Open source servers you install and run locally. Configure via `claude_desktop_config.json` or `claude mcp add` CLI. The server process runs on your machine (or connects to a remote endpoint).

### cBioPortal (TCGA & Cancer Genomics)

Query cancer genomics data from [cBioPortal](https://www.cbioportal.org/) — the open-access platform hosting all 33 TCGA cancer types plus 200+ additional studies. Search mutations, gene expression, copy number, clinical data, and molecular profiles. No authentication required for the public portal.

> **Why cBioPortal for TCGA?** Research hospitals access TCGA data two ways: ~50% query the public databases, ~50% use on-premise snapshots loaded into local cBioPortal instances. This server supports both — point it at the public portal or your hospital's instance via `CBIOPORTAL_BASE_URL`.

> **Cost:** Free. The public cBioPortal API has no authentication, no rate limits, and no usage fees. Local instances require your own infrastructure.

#### Setup

**Claude Code CLI:**

```bash
git clone https://github.com/pickleton89/cbioportal-mcp.git
cd cbioportal-mcp
uv sync
```

Then add to Claude Code:

```bash
claude mcp add cbioportal-mcp -s local \
  -- uv run cbioportal-mcp
```

**For a hospital's local cBioPortal instance**, set the base URL:

```bash
export CBIOPORTAL_BASE_URL=https://cbioportal.yourhospital.org/api
```

**Claude Desktop:** Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "cbioportal": {
      "command": "uv",
      "args": ["run", "cbioportal-mcp"],
      "cwd": "/path/to/cbioportal-mcp"
    }
  }
}
```

#### Available Tools (12)

| Tool | What it does | Example use |
|------|-------------|-------------|
| `get_cancer_studies` | List available cancer studies with pagination | Browse all TCGA cohorts |
| `search_studies` | Keyword-based study discovery | Find ovarian cancer studies |
| `get_study_details` | Comprehensive study metadata | Get details on TCGA-OV (ovarian) |
| `get_samples_in_study` | Sample data within a study | List all TCGA-OV tumor samples |
| `get_genes` | Gene information by ID or symbol | Look up TP53, BRCA1, PIK3CA |
| `search_genes` | Keyword search for genes | Find genes in the PI3K pathway |
| `get_mutations_in_gene` | Mutation details within a study | Get TP53 mutations across TCGA-OV |
| `get_clinical_data` | Patient clinical information | Retrieve survival, stage, treatment data |
| `get_molecular_profiles` | Available molecular data types per study | List expression, mutation, CNV profiles |
| `get_gene_panels_for_study` | Gene panel information | Check which genes were sequenced |
| `get_multiple_studies` | Concurrent multi-study fetch | Compare TCGA-OV, TCGA-BRCA, TCGA-LUAD |
| `get_multiple_genes` | Concurrent batched gene retrieval | Batch lookup of DNA repair pathway genes |

#### Example Prompts

```
"Search cBioPortal for TCGA ovarian cancer studies and show me TP53 mutation
frequency compared to other TCGA cohorts."

"Get clinical data for TCGA-OV including survival outcomes and platinum
sensitivity status."

"What are the most frequently mutated genes in TCGA high-grade serous
ovarian cancer samples? Compare to TCGA breast cancer."

"Look up PIK3CA, PTEN, and AKT1 mutations in TCGA-OV and show the
mutation types (missense, nonsense, frameshift)."
```

---

### Hugging Face

Search and explore ML models, datasets, Spaces, and papers on the Hugging Face Hub. Run community tools via MCP-compatible Gradio apps. Useful for finding genomic foundation models, biomedical NLP models, and relevant datasets.

#### Setup

**Claude Desktop:** Add via Settings > Connectors > find "Hugging Face" > click Connect. Or configure manually — visit [huggingface.co/settings/mcp](https://huggingface.co/settings/mcp), select your client, and copy the config snippet.

**Claude Code CLI:**

```bash
claude mcp add hf-mcp-server -t http https://huggingface.co/mcp?login
```

Then start `claude` and follow the authentication prompt. Or use an explicit token:

```bash
claude mcp add hf-mcp-server \
  -t http https://huggingface.co/mcp \
  -H "Authorization: Bearer <YOUR_HF_TOKEN>"
```

**Get a free HF token:** [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)

#### Built-in Tools (7)

| Tool | What it does | Example use |
|------|-------------|-------------|
| Spaces Semantic Search | Find AI apps via natural language | Find a tool that can segment cell images |
| Papers Semantic Search | Find ML research papers | Search for papers on genomic foundation models |
| Model Search | Search models with filters for task, library | Find biomedical text classification models |
| Dataset Search | Search datasets with filters for author, tags | Find single-cell RNA-seq datasets |
| Documentation Semantic Search | Search HF docs using natural language | How do I fine-tune with PEFT? |
| Run and Manage Jobs | Run and monitor jobs on HF infrastructure | Schedule a model training job |
| Hub Repository Details | Get details about models, datasets, Spaces | Get info on a specific model card |

You can also add community Gradio Spaces as extra tools at [huggingface.co/settings/mcp](https://huggingface.co/settings/mcp).

#### Example Prompts

```
"Search Hugging Face for biomedical language models fine-tuned on PubMed data."

"Find datasets related to ovarian cancer gene expression on Hugging Face."

"Search Hugging Face papers for recent work on spatial transcriptomics
foundation models."
```

---

## References

**Anthropic connectors:**
- [ClinicalTrials.gov connector tutorial](https://claude.com/resources/tutorials/using-the-clinicaltrials-gov-connector-in-claude)
- [bioRxiv connector tutorial](https://claude.com/resources/tutorials/using-the-biorxiv-and-medrxiv-connector-in-claude)
- [PubMed connector tutorial](https://claude.com/resources/tutorials/using-the-pubmed-connector-in-claude)
- [Seqera MCP blog post](https://seqera.io/blog/seqera-mcp/) (announcement and overview)
- [Seqera MCP page](https://seqera.io/mcp/) (setup instructions)
- [Seqera pricing](https://seqera.io/pricing/) (free tier and compute costs)
- [All connectors overview](https://claude.com/connectors)

**Community servers:**
- [pickleton89/cbioportal-mcp](https://github.com/pickleton89/cbioportal-mcp) (cBioPortal MCP server, 12 tools)
- [cBioPortal public portal](https://www.cbioportal.org/) (free, no auth required)
- [cBioPortal API docs](https://www.cbioportal.org/api/swagger-ui/index.html) (Swagger/OpenAPI)
- [huggingface/hf-mcp-server](https://github.com/huggingface/hf-mcp-server) (official HF MCP server)
- [HF MCP settings](https://huggingface.co/settings/mcp) (configure tools and Spaces)
- [HF MCP docs](https://huggingface.co/docs/hub/en/hf-mcp-server)
