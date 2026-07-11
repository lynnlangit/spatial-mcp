# FastMCP Patterns for This Project

Shared patterns and conventions used across all custom MCP servers (see [Server Registry](../reference/shared/server-registry.md) for current counts).

---

## 1. Optional dict/list parameters

**Problem:** FastMCP 2.x transports Optional[Dict] and Optional[List] parameters
as JSON strings over the MCP wire protocol. Pydantic rejects these with
`"Input should be a valid dictionary"` or `"Input should be a valid list"` before
the function body ever runs.

**Fix:** Use Pydantic `BeforeValidator` to coerce JSON strings at the model
layer, not in the tool body. Define reusable type aliases:

```python
import json
from typing import Annotated, Dict, List, Optional
from pydantic import BeforeValidator

def _coerce_dict(val):
    """Coerce JSON-string dicts for BeforeValidator."""
    if val is None or isinstance(val, dict):
        return val
    if isinstance(val, str):
        return json.loads(val)
    return val

def _coerce_list(val):
    """Coerce JSON-string lists for BeforeValidator."""
    if val is None or isinstance(val, list):
        return val
    if isinstance(val, str):
        parsed = json.loads(val)
        if isinstance(parsed, list):
            return parsed
    return val

_CoerceDict = BeforeValidator(_coerce_dict)
_CoerceList = BeforeValidator(_coerce_list)
```

Then annotate tool parameters:

```python
@mcp.tool()
async def my_tool(
    data: Annotated[Optional[Dict], _CoerceDict] = None,
    tags: Annotated[Optional[List[str]], _CoerceList] = None,
) -> dict:
    ...
```

**Testing:** Call `tool.run(arguments={...})` (not `.fn()`) to exercise the
Pydantic validation path. `.fn()` bypasses Pydantic and only tests native
Python types.

**Servers using this pattern:** mcp-neoantigen, mcp-multiomics.

---

## 2. DRY_RUN mode contract

Every tool that respects `DRY_RUN` mode must follow these rules:

1. **Same schema** -- DRY_RUN responses use the identical top-level keys as
   live responses. Clients must be able to parse both without branching.

2. **`dry_run` flag** -- Add `"dry_run": true` at the top level of the
   returned dict so callers can detect synthetic data programmatically.

3. **Warning text** -- Use the shared `add_dry_run_warning()` helper to
   prepend a human-readable warning:

   ```python
   from common.dry_run import add_dry_run_warning as _shared_add_dry_run_warning

   DRY_RUN = os.getenv("MYSERVER_DRY_RUN", "true").lower() in ("true", "1", "yes")

   def add_dry_run_warning(result):
       return _shared_add_dry_run_warning(result, dry_run=DRY_RUN, env_var="MYSERVER_DRY_RUN")
   ```

4. **Pure computation tools** should run real logic even in DRY_RUN mode --
   only add the warning wrapper. Do not short-circuit with mock data if the
   tool computes from its input parameters (e.g., pathway scoring).

5. **Mock data triggers** should only fire for exact "PatientOne default"
   input scenarios, not broadly.

**Environment variable pattern:** `<SERVERNAME>_DRY_RUN` defaults to `"true"`.
Set to `"false"` for live mode.

---

## 3. Error response schema

All tools must return errors in a consistent shape so clients can detect
failures programmatically:

```json
{
  "error": "Human-readable error message explaining what went wrong",
  "code": "machine_readable_slug"
}
```

**Common error codes:**

| Code | Meaning |
|------|---------|
| `invalid_input` | Malformed or missing required parameter |
| `not_found` | Requested resource does not exist |
| `api_error` | Upstream API returned an error |
| `timeout` | Operation exceeded time limit |
| `auth_error` | Missing or invalid credentials |

Tools should **never** raise unhandled exceptions through the MCP transport.
Wrap external calls in try/except and return the error dict:

```python
try:
    result = await external_api_call(params)
except httpx.HTTPStatusError as exc:
    return {"error": f"API returned {exc.response.status_code}", "code": "api_error"}
except TimeoutError:
    return {"error": "Request timed out after 60s", "code": "timeout"}
```

---

## 4. Versioning policy

Each server's version lives in its `pyproject.toml` under `[project] version`.

| Bump | When | Example |
|------|------|---------|
| **Patch** (0.1.x) | Bug fixes, doc updates, DRY_RUN data tweaks | Fix typo in mock data |
| **Minor** (0.x.0) | New tools added, new optional parameters | Add `search_by_funder` tool |
| **Major** (x.0.0) | Breaking schema changes, removed tools, renamed keys | Rename `result` key to `data` |

**Rules:**

- Adding a new tool is always a **minor** bump (backwards-compatible).
- Adding an optional parameter to an existing tool is a **patch** bump.
- Removing or renaming a tool, or changing the shape of its return dict in a
  way that breaks existing callers, is a **major** bump.
- The FastMCP framework version floor (`fastmcp>=2.13`) is pinned
  project-wide; individual servers should not lower it.
