---
name: precision-a2a-protocol
description: >
  Technical guide for implementing and consuming the A2A (Agent-to-Agent) wrapper.
  Enforces the 10-step security lifecycle and constrained JWT exchange.
---

# Precision A2A Protocol Skill

This skill ensures that all cross-agent communication follows the project's secure "A2A Wrapper" architectural patterns.

## 🛡️ The 10-Step Security Lifecycle

Every A2A invocation MUST implement or verify the following steps:
1. **JWT Extraction**: Parse the inbound Bearer token.
2. **Signature Verification**: Validate against the Agent Identity Service (AIS).
3. **Replay Protection**: Check the `jti` nonce in Redis.
4. **Authorization (OPA)**: ABAC check (Agent -> Tool -> Data Class).
5. **Rate Limiting**: Verify hospital/user quotas in Redis.
6. **Input Sanitization**: Pydantic/JSON Schema validation.
7. **Trace Injection**: Propagate `X-Trace-ID` for bilateral auditing.
8. **Logic Execution**: Call the underlying MCP tool.
9. **Audit Emission**: Emit signed events to SIEM/OTEL.
10. **Result Sanitization**: Return scrubbed data to the caller.

## 🔐 Token Delegation Pattern

When Agent A calls Agent B, use the **Constrained JWT Exchange**:
- **Constraint**: The new token must possess a narrower scope and shorter TTL (e.g., 300s).
- **Verification**: Agent B must independently verify the delegated token.
- **Auditing**: Both ends must log the `caller_jwt_sub` and `target_server_id`.

## 🛠️ Implementation Specs

- **Middleware**: Always use the components in `shared/common/a2a/`.
- **Error Handling**: Use the standardized `A2ASecurityException` for rejection (401/403).
- **Testing**: Use the `A2AMockProtocol` in `tests/` to simulate token exchange.

---

**Use this skill when:**
- Implementing the A2A wrapper middleware.
- Adding "sub-agent" capabilities to an existing server.
- Reviewing PRs for cross-server communication security.
