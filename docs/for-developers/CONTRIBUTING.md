# Contributing to Precision Medicine MCP

Thank you for your interest in contributing! This guide will help you get started.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Workflow](#development-workflow)
4. [Pull Request Process](#pull-request-process)
5. [Coding Standards](#coding-standards)
6. [Testing Requirements](#testing-requirements)
7. [Documentation Requirements](#documentation-requirements)

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors, regardless of experience level, background, or identity.

### Expected Behavior

- Be respectful and constructive in discussions
- Welcome newcomers and help them get started
- Give and receive feedback gracefully
- Focus on what's best for the project and community

### Unacceptable Behavior

- Harassment, discrimination, or personal attacks
- Trolling or deliberately derailing discussions
- Publishing others' private information without consent

**Report issues to:** [maintainer email placeholder]

---

## Getting Started

### Prerequisites

- Python 3.11+
- Git
- GCP account (for Cloud Run deployments, optional)
- Claude Desktop or Claude API access

### Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/precision-medicine-mcp.git
cd precision-medicine-mcp

# Add upstream remote
git remote add upstream https://github.com/lynnlangit/precision-medicine-mcp.git
```

### Development Setup

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e "servers/mcp-{server}[dev]"

# Run tests to verify setup
pytest tests/unit/mcp-{server} -v
```

---

## Development Workflow

### 1. Create a Feature Branch

```bash
# Sync with upstream
git fetch upstream
git checkout main
git merge upstream/main

# Create feature branch
git checkout -b feature/your-feature-name
```

**Branch naming conventions:**
- `feature/` - New features or enhancements
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `test/` - Test additions or improvements
- `refactor/` - Code refactoring

**Examples:**
- `feature/add-metabolomics-server`
- `fix/spatial-pathway-enrichment-bug`
- `docs/update-deployment-guide`

### 2. Make Your Changes

**For new servers:**
- Follow [ADD_NEW_MODALITY_SERVER.md](ADD_NEW_MODALITY_SERVER.md) guide
- Use boilerplate template: `/servers/mcp-server-boilerplate/`
- Include tests (≥50% coverage for production, ≥35% for demo)
- Add documentation (README + architecture doc)

**For bug fixes:**
- Write a test that reproduces the bug first
- Fix the bug
- Verify test now passes
- Update documentation if needed

**For documentation:**
- Keep language clear and concise
- Include examples where helpful
- Update table of contents if needed
- Check for broken links

### 3. Write Tests

**Required tests:**
- **Smoke tests:** Server imports, tool registration
- **DRY_RUN tests:** All tools work in synthetic mode
- **Unit tests:** Individual tool functionality
- **Integration tests:** Multi-tool workflows (optional)

**Example test structure:**
```python
# tests/unit/mcp-{server}/test_server.py

import pytest

def test_server_imports():
    """Test server module imports successfully."""
    from mcp_{server} import server
    assert server.mcp is not None

@pytest.mark.asyncio
async def test_tool_dry_run():
    """Test tool works in DRY_RUN mode."""
    from mcp_{server}.server import my_tool

    result = await my_tool._impl(param="test")

    assert result["status"] == "DRY_RUN"
    assert "data" in result
```

### 4. Run Tests Locally

```bash
# Run tests for your server
cd tests/unit/mcp-{server}
pytest -v --cov=../../../servers/mcp-{server}/src/mcp_{server}

# Check coverage (target: ≥50% for production, ≥35% for demo)
pytest --cov-report=term-missing

# Run all tests
pytest tests/unit/ -v
```

### 5. Update Documentation

**Required updates:**

For new servers:
- [ ] Create `/servers/mcp-{server}/README.md`
- [ ] Create `/architecture/{modality}/README.md`
- [ ] Add row to `/servers/README.md#-server-status`
- [ ] Add section to `/architecture/README.md`
- [ ] Update `/docs/for-developers/README.md` if needed

For bug fixes:
- [ ] Update CHANGELOG.md (if exists)
- [ ] Update server README if behavior changed
- [ ] Add troubleshooting note if applicable

For new features:
- [ ] Update relevant README files
- [ ] Add usage examples
- [ ] Update architecture diagrams if needed

---

## Pull Request Process

### 1. Commit Your Changes

**Commit message format:**
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation changes
- `test` - Test additions/changes
- `refactor` - Code refactoring
- `chore` - Maintenance tasks

**Examples:**
```
feat(metabolomics): Add LC-MS data loading tool

- Implement load_metabolomics_data tool
- Support CSV and mzML formats
- Add DRY_RUN mode with synthetic data
- Include unit tests (68% coverage)

Closes #123
```

```
fix(spatialtools): Correct Moran's I calculation for edge cases

Fixed bug where Moran's I would fail when spatial graph had
isolated nodes. Now handles edge cases gracefully.

Fixes #456
```

```
docs(deployment): Update GCP Cloud Run deployment guide

- Add environment variable configuration
- Include troubleshooting section
- Update screenshots for new UI
```

### 2. Push to Your Fork

```bash
git add .
git commit -m "feat(server): Your descriptive message"
git push origin feature/your-feature-name
```

### 3. Create Pull Request

**On GitHub:**
1. Go to your fork
2. Click "Pull Request"
3. Select your feature branch
4. Fill out PR template:

**PR Title Format:**
```
[Type] Brief description (e.g., "[Feature] Add metabolomics server")
```

**PR Description Template:**
```markdown
## Description
Brief description of changes and motivation.

## Type of Change
- [ ] New feature (non-breaking change adding functionality)
- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] Breaking change (fix or feature causing existing functionality to change)
- [ ] Documentation update

## Testing
- [ ] All existing tests pass
- [ ] New tests added (coverage: X%)
- [ ] Tested locally with Claude Desktop
- [ ] Tested deployed to GCP (if applicable)

## Documentation
- [ ] Updated server README
- [ ] Updated architecture documentation
- [ ] Updated central server tables
- [ ] Added usage examples

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added to complex code
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests added and passing

## Related Issues
Closes #XXX
Fixes #YYY

## Screenshots (if applicable)
[Add screenshots here]
```

### 4. Code Review

**What reviewers look for:**
- Code quality and style
- Test coverage (≥50% for production, ≥35% for demo)
- Documentation completeness
- Breaking changes clearly documented
- Error handling and edge cases
- Performance considerations

**Responding to feedback:**
- Address all comments
- Push new commits to same branch (PR auto-updates)
- Mark conversations as resolved after addressing
- Be open to suggestions and alternatives

### 5. Merge

Once approved:
- Reviewer will merge PR
- Your branch will be deleted (automatically or manually)
- Changes will be in `main` branch

---

## Coding Standards

### Python Style

**Follow PEP 8 with these preferences:**
- Line length: 100 characters (not 79)
- Indentation: 4 spaces (no tabs)
- Imports: Absolute imports preferred
- Type hints: Required for all function parameters

**Example:**
```python
from typing import Optional
import pandas as pd


async def load_data(
    file_path: str,
    normalization: Optional[str] = None
) -> dict:
    """
    Load and optionally normalize data.

    Args:
        file_path: Path to input CSV file
        normalization: Normalization method ("log2", "quantile", None)

    Returns:
        Dictionary with loaded data and metadata
    """
    data = pd.read_csv(file_path)

    if normalization == "log2":
        data = np.log2(data + 1)

    return {
        "data": data.to_dict(),
        "shape": data.shape,
        "normalization": normalization
    }
```

### FastMCP Patterns

**Tool decorator:**
```python
@mcp.tool()
async def tool_name(param1: str, param2: int = 10) -> dict:
    """Clear description visible to Claude."""
    pass
```

**DRY_RUN mode:**
```python
if DRY_RUN:
    return {
        "status": "DRY_RUN",
        "message": "Simulated data returned",
        "data": synthetic_data()
    }

# Real implementation
return {"status": "success", "data": real_data()}
```

**Error handling:**
```python
try:
    result = process_data(input_file)
except FileNotFoundError:
    return {
        "status": "error",
        "error": "File not found",
        "message": f"Could not find {input_file}. Check path and try again.",
        "suggestion": "Use list_available_files() to see available data."
    }
```

### Documentation Standards

**Docstrings (Google style):**
```python
async def my_tool(param1: str, param2: int = 10) -> dict:
    """
    One-line summary of what this tool does.

    Longer description if needed. Explain the purpose, algorithm,
    and any important details Claude should know.

    Args:
        param1: Description of param1 with type info
        param2: Description of param2 (default: 10)

    Returns:
        Dictionary containing:
        - result: The computed result
        - metadata: Additional context
        - status: "success" or "error"

    Raises:
        ValueError: If param1 is empty string
        FileNotFoundError: If referenced file doesn't exist

    Example:
        >>> result = await my_tool(param1="test", param2=20)
        >>> print(result["result"])
        42
    """
```

---

## Testing Requirements

### Coverage Targets

| Server Type | Minimum Coverage | Recommended |
|-------------|-----------------|-------------|
| **Production** | 50% | 65%+ |
| **Demo/Mocked** | 35% | 50%+ |

### Test Categories

1. **Smoke tests** (required)
   - Server imports successfully
   - Tools registered with MCP
   - DRY_RUN mode enabled by default

2. **Unit tests** (required)
   - Each tool tested individually
   - DRY_RUN mode works
   - Input validation catches errors
   - Error messages are actionable

3. **Integration tests** (recommended)
   - Multi-tool workflows
   - Cross-server integration
   - Real data processing (if applicable)

### Running Tests

```bash
# Run tests with coverage
pytest tests/unit/mcp-{server} -v --cov=servers/mcp-{server}/src/mcp_{server}

# See missing coverage
pytest --cov-report=term-missing

# Run specific test
pytest tests/unit/mcp-{server}/test_server.py::test_my_function -v

# Run with real data (not DRY_RUN)
SERVER_DRY_RUN=false pytest tests/unit/mcp-{server}
```

---

## Documentation Requirements

### Server README

**Location:** `/servers/mcp-{server}/README.md`

**Required sections:**
```markdown
# mcp-{server}

Brief description

## Status
- Production ready / Partial / Mocked
- Coverage: X%
- Last updated: YYYY-MM-DD

## Tools
List of tools with descriptions

## Installation
Setup instructions

## Usage
Example prompts for Claude Desktop

## Testing
How to run tests

## Dependencies
List of key libraries
```

### Architecture Documentation

**Location:** `/architecture/{modality}/README.md`

**Required sections:**
```markdown
# {Modality} Architecture

## Overview
What this modality covers

## Workflow Diagram
Mermaid diagram showing data flow

## Integration Points
How it connects to other servers

## Data Formats
Expected input/output formats

## Example Use Case
PatientOne integration example
```

---

## Questions?

**Technical questions:**
- Check [README.md](README.md) and [ARCHITECTURE.md](ARCHITECTURE.md)
- Review existing servers: [/servers](../../servers/)
- Open GitHub Discussion

**Process questions:**
- Review this guide again
- Check GitHub Issues for similar questions
- Ask in GitHub Discussions

**Bug reports:**
- Open GitHub Issue with:
  - Clear description of bug
  - Steps to reproduce
  - Expected vs. actual behavior
  - Environment details (OS, Python version, etc.)

---

**Thank you for contributing to precision medicine! 🎉**

---

## Contributing educational content

New notebooks must follow the cell order in `notebooks/PAT001_walkthrough.ipynb`:
explain (markdown) → code call → assert against canonical values from `tests/fixtures/pat001_canonical.py`.

To update the glossary, edit `docs/for-educators/GLOSSARY.md` and increment the
"Last reviewed" date at the bottom.

To propose a new lecture module, open a GitHub issue with the `education` label.
Maintainers will respond to education PRs within 14 days.

---

**Last Updated:** 2026-04-21
