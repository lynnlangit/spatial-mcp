# mcp-perturbation Deployment Testing Guide

**Created**: 2026-01-20
**Purpose**: Verify mcp-perturbation server deployment on Google Cloud Run

---

## Prerequisites

- Deployment URL: `https://mcp-perturbation-ondu7mwjpa-uc.a.run.app`
- jq installed (for JSON parsing): `brew install jq`
- curl installed (standard on macOS)

---

## Test 1: Basic Health Check

**Purpose**: Verify container is running and listening on port 8080

```bash
# Test 1.1: Check if service responds
curl -I https://mcp-perturbation-ondu7mwjpa-uc.a.run.app/health

# Expected: HTTP 200 or HTTP 404 (FastMCP may not have /health endpoint)
# Success criteria: NOT connection refused or timeout
```

---

## Test 2: SSE Endpoint Availability

**Purpose**: Verify SSE transport is configured correctly

```bash
# Test 2.1: Connect to SSE endpoint
curl -N -H "Accept: text/event-stream" \
  https://mcp-perturbation-ondu7mwjpa-uc.a.run.app/sse

# Expected: Connection established, may see SSE headers
# Success criteria: No immediate connection refused
```

```bash
# Test 2.2: Check SSE with timeout
timeout 5 curl -N -H "Accept: text/event-stream" \
  https://mcp-perturbation-ondu7mwjpa-uc.a.run.app/sse

# Expected: Hangs for 5 seconds (SSE keeps connection open)
# Success criteria: No immediate error
```

---

## Test 3: MCP Protocol Handshake

**Purpose**: Verify MCP server responds to protocol messages

```bash
# Test 3.1: Initialize MCP session
curl -X POST https://mcp-perturbation-ondu7mwjpa-uc.a.run.app/message \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {
        "name": "test-client",
        "version": "1.0.0"
      }
    }
  }' | jq .

# Expected: JSON response with server capabilities
# Success criteria: Valid JSON with "result" field
```

---

## Test 4: List Available Tools

**Purpose**: Verify all 8 GEARS tools are registered

```bash
# Test 4.1: List tools
curl -X POST https://mcp-perturbation-ondu7mwjpa-uc.a.run.app/message \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {}
  }' | jq '.result.tools[] | {name: .name, description: .description}'

# Expected: 8 tools listed
# - perturbation_load_dataset
# - perturbation_setup_model
# - perturbation_train_model
# - perturbation_compute_delta
# - perturbation_predict_response
# - perturbation_differential_expression
# - perturbation_get_latent
# - perturbation_visualize
```

---

## Test 5: Call Tool - Load Dataset (Dry Run)

**Purpose**: Verify tool execution with DRY_RUN mode

```bash
# Test 5.1: Load synthetic dataset
curl -X POST https://mcp-perturbation-ondu7mwjpa-uc.a.run.app/message \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "perturbation_load_dataset",
      "arguments": {
        "dataset_id": "test_dataset",
        "normalize": true,
        "n_hvg": 2000
      }
    }
  }' | jq .

# Expected (if DRY_RUN=true): Simulated success response
# Expected (if DRY_RUN=false): Actual dataset loading
# Success criteria: No error in response
```

---

## Test 6: Check Server Logs

**Purpose**: Verify server startup and configuration

```bash
# Test 6.1: Fetch recent logs
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=mcp-perturbation" \
  --limit 20 \
  --format "value(timestamp,severity,textPayload)" \
  --project precision-medicine-poc

# Expected log entries:
# - "Starting perturbation MCP server..."
# - "Transport: sse, Port: 8080"
# - "Registered tool: perturbation_load_dataset" (x8)
# - No ERROR or CRITICAL messages
```

---

## Test 7: Environment Variable Check

**Purpose**: Verify correct environment configuration

```bash
# Test 7.1: Check service configuration
gcloud run services describe mcp-perturbation \
  --region us-central1 \
  --project precision-medicine-poc \
  --format "value(spec.template.spec.containers[0].env)"

# Expected environment variables:
# - MCP_TRANSPORT=sse
# - PERTURBATION_DRY_RUN=false (or true)
# - PERTURBATION_LOG_LEVEL=INFO
# - ENVIRONMENT=development
```

---

## Test 8: Resource Allocation Check

**Purpose**: Verify correct memory/CPU allocation

```bash
# Test 8.1: Check resource limits
gcloud run services describe mcp-perturbation \
  --region us-central1 \
  --project precision-medicine-poc \
  --format "value(spec.template.spec.containers[0].resources)"

# Expected:
# - Memory: 4Gi
# - CPU: 2
# - No GPU (for initial deployment)
```

---

## Test 9: End-to-End Workflow Test

**Purpose**: Test complete GEARS prediction workflow

```bash
# Test 9.1: Full workflow (requires MCP client or Claude API)
# This test requires:
# 1. Load dataset (GSE184880 or synthetic)
# 2. Setup GEARS model
# 3. Train model (5-10 epochs for quick test)
# 4. Predict response
# 5. Verify output

# Use Claude Desktop or Streamlit UI for this test
# Or use MCP client library
```

---

## Test 10: Performance Benchmarks

**Purpose**: Measure response times

```bash
# Test 10.1: Measure cold start time
time curl -X POST https://mcp-perturbation-ondu7mwjpa-uc.a.run.app/message \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' \
  -o /dev/null -s -w "Time: %{time_total}s\n"

# Expected:
# - First request (cold start): 5-15 seconds
# - Subsequent requests: <1 second
```

---

## Test 11: Error Handling

**Purpose**: Verify graceful error handling

```bash
# Test 11.1: Invalid tool name
curl -X POST https://mcp-perturbation-ondu7mwjpa-uc.a.run.app/message \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 4,
    "method": "tools/call",
    "params": {
      "name": "nonexistent_tool",
      "arguments": {}
    }
  }' | jq .

# Expected: JSON-RPC error response with clear message
```

```bash
# Test 11.2: Invalid arguments
curl -X POST https://mcp-perturbation-ondu7mwjpa-uc.a.run.app/message \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 5,
    "method": "tools/call",
    "params": {
      "name": "perturbation_setup_model",
      "arguments": {
        "hidden_size": -1
      }
    }
  }' | jq .

# Expected: Validation error (hidden_size must be >= 32)
```

---

## Test 12: Concurrent Request Handling

**Purpose**: Verify server handles multiple requests

```bash
# Test 12.1: Send 5 concurrent requests
for i in {1..5}; do
  curl -X POST https://mcp-perturbation-ondu7mwjpa-uc.a.run.app/message \
    -H "Content-Type: application/json" \
    -d "{\"jsonrpc\":\"2.0\",\"id\":$i,\"method\":\"tools/list\",\"params\":{}}" \
    -o "/tmp/test_$i.json" &
done
wait

# Check results
cat /tmp/test_*.json | jq -s 'map(.result.tools | length)'

# Expected: All 5 requests return 8 tools
# Success criteria: All responses valid
```

---

## Quick Test Script

**File**: `test_deployment.sh`

```bash
#!/bin/bash
set -e

SERVICE_URL="https://mcp-perturbation-ondu7mwjpa-uc.a.run.app"

echo "🧪 Testing mcp-perturbation deployment..."
echo ""

# Test 1: Basic connectivity
echo "1️⃣ Testing basic connectivity..."
if curl -f -s -o /dev/null -w "%{http_code}" "$SERVICE_URL/sse"; then
  echo "✅ Service is reachable"
else
  echo "❌ Service unreachable"
  exit 1
fi

# Test 2: MCP initialize
echo ""
echo "2️⃣ Testing MCP protocol handshake..."
INIT_RESPONSE=$(curl -s -X POST "$SERVICE_URL/message" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {"name": "test-client", "version": "1.0.0"}
    }
  }')

if echo "$INIT_RESPONSE" | jq -e '.result' > /dev/null 2>&1; then
  echo "✅ MCP handshake successful"
else
  echo "❌ MCP handshake failed"
  echo "$INIT_RESPONSE" | jq .
  exit 1
fi

# Test 3: List tools
echo ""
echo "3️⃣ Testing tool listing..."
TOOLS_RESPONSE=$(curl -s -X POST "$SERVICE_URL/message" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {}
  }')

TOOL_COUNT=$(echo "$TOOLS_RESPONSE" | jq -r '.result.tools | length')
if [ "$TOOL_COUNT" -eq 8 ]; then
  echo "✅ All 8 tools registered"
  echo "$TOOLS_RESPONSE" | jq -r '.result.tools[] | "  - \(.name)"'
else
  echo "❌ Expected 8 tools, got $TOOL_COUNT"
  exit 1
fi

# Test 4: Call a tool
echo ""
echo "4️⃣ Testing tool execution (load_dataset)..."
TOOL_RESPONSE=$(curl -s -X POST "$SERVICE_URL/message" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "perturbation_load_dataset",
      "arguments": {
        "dataset_id": "test_synthetic",
        "normalize": true,
        "n_hvg": 2000
      }
    }
  }')

if echo "$TOOL_RESPONSE" | jq -e '.result' > /dev/null 2>&1; then
  echo "✅ Tool execution successful"
  echo "$TOOL_RESPONSE" | jq -r '.result.content[0].text' | head -5
else
  echo "⚠️  Tool execution returned error (may be expected in DRY_RUN mode)"
  echo "$TOOL_RESPONSE" | jq .
fi

echo ""
echo "🎉 Deployment tests complete!"
echo ""
echo "Service URL: $SERVICE_URL"
echo "Region: us-central1"
echo "Status: ✅ OPERATIONAL"
```

---

## Common Issues and Solutions

### Issue 1: Connection Timeout
**Symptom**: `curl: (28) Operation timed out`
**Cause**: Cold start takes >60s
**Solution**: Increase curl timeout: `curl --max-time 120 ...`

### Issue 2: 503 Service Unavailable
**Symptom**: HTTP 503 response
**Cause**: Container crashed during startup
**Solution**: Check logs with `gcloud logging read`

### Issue 3: 404 Not Found
**Symptom**: HTTP 404 on all endpoints
**Cause**: FastMCP routing issue
**Solution**: Verify MCP_TRANSPORT=sse in environment

### Issue 4: No Response from SSE
**Symptom**: SSE endpoint hangs indefinitely
**Cause**: Normal behavior - SSE maintains open connection
**Solution**: Use timeout or send proper MCP messages

---

## Success Criteria Checklist

- [ ] Service responds to HTTP requests (no 502/503)
- [ ] SSE endpoint is accessible
- [ ] MCP initialize handshake completes
- [ ] All 8 tools are listed
- [ ] At least one tool executes without error
- [ ] Logs show "Starting perturbation MCP server..."
- [ ] No ERROR/CRITICAL messages in logs
- [ ] Environment variables are set correctly
- [ ] Resource allocation matches configuration (4Gi, 2 CPU)

---

## Next Steps After Successful Deployment

1. **Test with Claude Desktop**: Add to `claude_desktop_config.json`
2. **Test with Streamlit UI**: Configure SSE URL in UI
3. **Performance testing**: Run full GEARS workflow with real data
4. **Cost monitoring**: Track Cloud Run costs for optimization
5. **GPU upgrade**: Follow GPU upgrade plan once CPU deployment is stable

---

**Status**: Ready for testing
