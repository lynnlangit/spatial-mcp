# ADR-0003: A2A Wrapper Architecture Selection

## Status
Proposed (2026-02-21)

## Context
We need to determine the best architectural approach for the Agent-to-Agent (A2A) wrapper to ensure scalability across 16+ MCP servers and multiple clinical use cases.

## Decision
We propose implementing the A2A Wrapper as a **Modular Shared Library** combined with an **Optional Orchestrator Server**.

### Rationale:
- **Shared Library**: Allows any MCP server to become "A2A capable" by simply importing the wrapper.
- **Orchestrator Server**: Provides a central registry if needed, but the primary logic remains distributed to avoid a single point of failure.

## Alternatives Considered
- **Centralized API Proxy**: Rejected due to latency and the "bottleneck" risk in high-throughput genomic data processing.
- **Ad-hoc JSON-RPC calls**: Rejected due to lack of type safety and documentation drift.

## Consequences
- **Positive**: High flexibility; follows established project patterns (`shared/common`).
- **Negative**: Requires all servers to update their dependencies to benefit from new A2A features.
