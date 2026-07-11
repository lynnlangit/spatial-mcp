# GCP MCP Server Test Plan

Simple functional tests for all deployed MCP servers ([Server Registry](../shared/server-registry.md)).

---

## Prerequisites

```bash
# Set your Anthropic API key
export ANTHROPIC_API_KEY=your_key_here

# Install dependencies
pip install anthropic
```

---

## Quick Health Check

Test all servers respond to HTTP requests:

```bash
# Run the automated health check
./tests/integration/test_gcp_servers.sh
```

**Expected:** All servers return HTTP 200 or 405 (both indicate server is running)

---

## 1. mcp-fgbio - FASTQ Validation

**Test:** Validate a FASTQ file format

```python
import anthropic

client = anthropic.Anthropic()

response = client.beta.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": "List the available tools from the fgbio MCP server."
    }],
    mcp_servers=[{
        "type": "url",
        "url": "https://mcp-fgbio-ondu7mwjpa-uc.a.run.app/sse",
        "name": "fgbio",
    }],
    tools=[{"type": "mcp_toolset", "mcp_server_name": "fgbio"}],
    betas=["mcp-client-2025-11-20"]
)

print(response.content[0].text)
```

**Expected:** List of genomic tools (validate_fastq, validate_vcf, get_reference_genome_info)

---

## 2. mcp-multiomics - Data Integration

**Test:** Check multi-omics integration capabilities

```python
response = client.beta.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": "What multi-omics analysis tools are available?"
    }],
    mcp_servers=[{
        "type": "url",
        "url": "https://mcp-multiomics-ondu7mwjpa-uc.a.run.app/sse",
        "name": "multiomics",
    }],
    tools=[{"type": "mcp_toolset", "mcp_server_name": "multiomics"}],
    betas=["mcp-client-2025-11-20"]
)

print(response.content[0].text)
```

**Expected:** Tools for RNA/protein/phosphorylation integration, HAllA, Stouffer's meta-analysis

---

## 3. mcp-spatialtools - Spatial Analysis

**Test:** Check spatial transcriptomics tools

```python
response = client.beta.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": "What spatial transcriptomics analysis tools do you provide?"
    }],
    mcp_servers=[{
        "type": "url",
        "url": "https://mcp-spatialtools-ondu7mwjpa-uc.a.run.app/sse",
        "name": "spatialtools",
    }],
    tools=[{"type": "mcp_toolset", "mcp_server_name": "spatialtools"}],
    betas=["mcp-client-2025-11-20"]
)

print(response.content[0].text)
```

**Expected:** Tools for alignment, QC filtering, batch correction, differential expression, pathway enrichment

---

## 4. mcp-mocktcga - Cancer Genomics Data

**Test:** Access TCGA data

```python
response = client.beta.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": "What TCGA cancer types can you access?"
    }],
    mcp_servers=[{
        "type": "url",
        "url": "https://mcp-mocktcga-ondu7mwjpa-uc.a.run.app/sse",
        "name": "mocktcga",
    }],
    tools=[{"type": "mcp_toolset", "mcp_server_name": "tcga"}],
    betas=["mcp-client-2025-11-20"]
)

print(response.content[0].text)
```

**Expected:** List of TCGA project codes (TCGA-OV, TCGA-BRCA, etc.)

---

## 5. mcp-openimagedata - Medical Imaging

**Test:** Check available imaging datasets

```python
response = client.beta.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": "What medical imaging datasets are available?"
    }],
    mcp_servers=[{
        "type": "url",
        "url": "https://mcp-openimagedata-ondu7mwjpa-uc.a.run.app/sse",
        "name": "openimagedata",
    }],
    tools=[{"type": "mcp_toolset", "mcp_server_name": "openimagedata"}],
    betas=["mcp-client-2025-11-20"]
)

print(response.content[0].text)
```

**Expected:** Imaging datasets (pathology, radiology, microscopy)

---

## 6. mcp-deepcell - Cell Segmentation

**Test:** Cell segmentation capabilities

```python
response = client.beta.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": "What cell segmentation tools are available?"
    }],
    mcp_servers=[{
        "type": "url",
        "url": "https://mcp-deepcell-ondu7mwjpa-uc.a.run.app/sse",
        "name": "deepcell",
    }],
    tools=[{"type": "mcp_toolset", "mcp_server_name": "deepcell"}],
    betas=["mcp-client-2025-11-20"]
)

print(response.content[0].text)
```

**Expected:** DeepCell segmentation models, nuclear/cytoplasm segmentation

---

## 9. mcp-mockepic - EHR Data

**Test:** Access EPIC EHR data (mock)

```python
response = client.beta.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": "What patient EHR data can you access?"
    }],
    mcp_servers=[{
        "type": "url",
        "url": "https://mcp-mockepic-ondu7mwjpa-uc.a.run.app/sse",
        "name": "mockepic",
    }],
    tools=[{"type": "mcp_toolset", "mcp_server_name": "mockepic"}],
    betas=["mcp-client-2025-11-20"]
)

print(response.content[0].text)
```

**Expected:** Mock patient data access (demographics, conditions, medications)

---

## Automated Test Script

Create `tests/integration/test_all_gcp_servers.py`:

```python
#!/usr/bin/env python3
"""
Simple functional test for all 14 GCP-deployed MCP servers.
Tests that each server responds and lists available tools.
"""

import anthropic
import os
import sys

SERVERS = {
    "fgbio": "https://mcp-fgbio-ondu7mwjpa-uc.a.run.app/sse",
    "multiomics": "https://mcp-multiomics-ondu7mwjpa-uc.a.run.app/sse",
    "spatialtools": "https://mcp-spatialtools-ondu7mwjpa-uc.a.run.app/sse",
    "mocktcga": "https://mcp-mocktcga-ondu7mwjpa-uc.a.run.app/sse",
    "openimagedata": "https://mcp-openimagedata-ondu7mwjpa-uc.a.run.app/sse",
    "deepcell": "https://mcp-deepcell-ondu7mwjpa-uc.a.run.app/sse",
    "mockepic": "https://mcp-mockepic-ondu7mwjpa-uc.a.run.app/sse",
}

def test_server(name, url):
    """Test a single MCP server."""
    print(f"Testing {name}...", end=" ", flush=True)

    try:
        client = anthropic.Anthropic()

        response = client.beta.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=512,
            messages=[{
                "role": "user",
                "content": f"List the available tools from the {name} MCP server."
            }],
            mcp_servers=[{
                "type": "url",
                "url": url,
                "name": name,
            }],
            tools=[{"type": "mcp_toolset", "mcp_server_name": name}],
            betas=["mcp-client-2025-11-20"]
        )

        if response.content:
            print("✓ PASS")
            return True
        else:
            print("✗ FAIL (no response)")
            return False

    except Exception as e:
        print(f"✗ FAIL: {str(e)[:50]}")
        return False

def main():
    """Test all servers."""
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY not set")
        sys.exit(1)

    print(f"Testing {len(SERVERS)} MCP servers...\n")

    results = {}
    for name, url in SERVERS.items():
        results[name] = test_server(name, url)

    print(f"\nResults: {sum(results.values())}/{len(results)} servers passed")

    return 0 if all(results.values()) else 1

if __name__ == "__main__":
    sys.exit(main())
```

**Run with:**
```bash
export ANTHROPIC_API_KEY=your_key_here
python tests/integration/test_all_gcp_servers.py
```

---

## Success Criteria

✅ **All tests pass if:**
1. Each server responds to HTTP requests (405 or 200)
2. Each server lists its available MCP tools
3. Tool descriptions match expected functionality
4. No timeout or connection errors

---

## Troubleshooting

**If a server fails:**

1. Check Cloud Run logs:
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=mcp-<name>" \
  --limit=50 --project=precision-medicine-poc
```

2. Check service status:
```bash
gcloud run services describe mcp-<name> \
  --region=us-central1 --project=precision-medicine-poc
```

3. Test with curl:
```bash
curl https://mcp-<name>-ondu7mwjpa-uc.a.run.app/sse
# Should return SSE event stream or 405
```
