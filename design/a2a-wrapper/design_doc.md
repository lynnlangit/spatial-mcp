# A2A Wrapper Design Document

## 1. Introduction
The **A2A (Agent-to-Agent) Wrapper** is intended to provide a standardized interface for interaction between autonomous agents within the Precision Medicine MCP ecosystem. This wrapper will encapsulate the complexities of multi-agent communication, discovery, and protocol negotiation.

## 2. Problem Statement
Currently, agents communicate directly through MCP tools, but there is no unified "handshake" or "governance" layer that allows an agent (e.g., a Genomic Researcher AI) to seamlessly request services from another (e.g., a Compliance Auditor AI) without hardcoding endpoint knowledge.

## 3. Goals
- Standardize agent-to-agent capability discovery.
- Implement a consistent "context-sharing" protocol via constrained JWT delegation.
- Integrate clinical compliance guardrails (OPA/ABAC) into every cross-agent call.
- Ensure non-repudiation through HMAC-signed bilateral audit trails.
- Prevent replay attacks using JTI nonce tracking in Redis.

## 4. Proposed Architecture
The A2A Wrapper is a modular middleware layer implemented as a shared library in `shared/common/` that interfaces with central infrastructure (Vault, OPA, Redis).

### The A2A Security Stack
- **Identity**: OIDC / JWT-based identity provided by the **Agent Identity Service (AIS)**.
- **Authorization**: **OPA (Open Policy Agent)** using Rego/ABAC policies for fine-grained tool access.
- **Integrity**: **HashiCorp Vault** for PKI and dynamic credential management.
- **Reliability**: **Redis** for JTI nonce caching (anti-replay) and distributed rate limiting.

### 10-Step Secure Invocation Lifecycle
1. **Extract JWT**: Parse the inbound Bearer token.
2. **Verify Signature**: Validate against the AIS public key (JWKS).
3. **Check Expiry + JTI**: Verify `exp` and check Redis to ensure `jti` is not a replay.
4. **OPA Policy Check**: POST to OPA for ABAC authorization (Agent -> Tool -> Data Class).
5. **Rate Limit Check**: Verify tool usage hasn't exceeded hospital quotas.
6. **Sanitize Inputs**: Validate arguments against JSON Schema.
7. **Inject Trace ID**: Propagate `X-Trace-ID` for bilateral auditing.
8. **Execute Tool**: Perform the actual logic via the underlying MCP server.
9. **Emit Audit Event**: Send signed metadata to SIEM/OTEL.
10. **Return Result**: Return sanitized output to the calling agent.

### Component Diagram & Security Layer
![A2A Security Layer](file:///Volumes/T7/projects/precision-medicine-mcp/design/a2a-wrapper/a2a_security_layer.png)
![MCP Platform Component Architecture](file:///Volumes/T7/projects/precision-medicine-mcp/design/a2a-wrapper/mcp_platform_architecture.png)

### Core Sequence Flows
![Single-Server Secure Tool Invocation](file:///Volumes/T7/projects/precision-medicine-mcp/design/a2a-wrapper/secure_tool_invocation_seq.png)
![Cross-Server A2A Token Exchange](file:///Volumes/T7/projects/precision-medicine-mcp/design/a2a-wrapper/cross_server_token_exchange_seq.png)

### Wrapper Logic Flowchart
![A2A Wrapper Flowchart](file:///Volumes/T7/projects/precision-medicine-mcp/design/a2a-wrapper/a2a_wrapper_flowchart.png)

### Component Diagram (Planned)
- **Discovery Layer**: Using the MCP `resources` protocol to broadcast capabilities.
- **Messaging Layer**: Standardized Pydantic models for agent prompts and responses.
- **Audit Layer**: Automatic logging of all cross-agent calls.

## 5. Stakeholder Review (Paul Owner)
- [ ] Review proposed discovery mechanism.
- [ ] Validate multi-tenant security model.
- [ ] Approve storage location (Shared Lib vs Orchestrator Server).

## 6. Design Observations & Risks

### ✅ Architectural Strengths
- **Delegated Security**: The constrained JWT exchange (JWT A -> JWT B) implements the **Principle of Least Privilege**, ensuring sub-agents only possess the scopes required for their specific task.
- **Clinical Compliance**: Automatic JTI nonce tracking and OPA policy enforcement meet the high standards for HIPAA data protection.
- **Non-Repudiation**: The bilateral audit trail ensures that if a data leak occurs, the entire call chain (Caller -> Wrapper -> Target) is logged and signed.

### ⚠️ Potential Risks & Optimization Opportunities
- **Performance Latency**: The 10-step lifecycle involves multiple external network hops (AIS, OPA, Redis). For high-throughput bioinformatics pipelines, we should investigate **JWT caching** and **OPA policy pre-fetching**.
- **Maintenance Overhead**: Implementing the wrapper as a Shared Library (as proposed in ADR-0003) means every security patch requires rebuilding and redeploying all 15+ MCP servers. We should consider a **Sidecar or Gateway** pattern for easier governance.
- **Vault Connectivity**: The dependency on HashiCorp Vault for dynamic credentials must be robust; a Vault outage would effectively paralyze the entire agent fleet.

## 7. Next Steps
1. Finalize ADR-0003.
2. Implement first prototype in a mock environment.
