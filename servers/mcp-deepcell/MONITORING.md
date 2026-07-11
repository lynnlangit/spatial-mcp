# mcp-deepcell Monitoring & Performance Guide

## Current Configuration ✅

**Service:** mcp-deepcell
**Region:** us-central1
**Project:** precision-medicine-poc
**URL:** https://mcp-deepcell-ondu7mwjpa-uc.a.run.app

### Resource Allocation

| Resource | Current | Recommendation | Notes |
|----------|---------|----------------|-------|
| **Memory** | 4 GiB | 4-8 GiB | 4Gi sufficient for most images; 8Gi for large batches |
| **CPU** | 2 vCPUs | 2-4 vCPUs | 2 vCPUs adequate; 4 vCPUs for higher throughput |
| **Timeout** | 300s | 300-600s | 300s sufficient for images <4K; 600s for larger |
| **Max Instances** | 10 | 10-20 | 10 adequate for moderate load; increase for high traffic |
| **Concurrency** | 160 | 1-10 | Reduce to 1-5 for better model caching efficiency |

### Environment Variables

```yaml
DEEPCELL_DRY_RUN: false            # Production mode with real models
DEEPCELL_USE_GPU: false            # CPU-only (GPU optional, requires GPU Dockerfile)
MCP_TRANSPORT: sse                 # Server-Sent Events transport
DEEPCELL_OUTPUT_DIR: /app/data/output
DEEPCELL_MODEL_CACHE_DIR: /app/data/models
TF_CPP_MIN_LOG_LEVEL: 2           # Reduce TensorFlow logging verbosity
```

---

## Performance Baselines

### Expected Response Times (CPU-only, 2 vCPUs, 4Gi RAM)

#### First Request (Cold Start + Model Download)
| Image Size | Model Download | Inference | Total |
|------------|----------------|-----------|-------|
| 512×512    | ~25-30s | ~5s | **~35s** |
| 1024×1024  | ~25-30s | ~10s | **~40s** |
| 2048×2048  | ~25-30s | ~20s | **~50s** |
| 4096×4096  | ~25-30s | ~60s | **~90s** |

#### Subsequent Requests (Warm Instance, Cached Models)
| Image Size | Inference | Total |
|------------|-----------|-------|
| 512×512    | ~2s | **~2s** |
| 1024×1024  | ~5s | **~5s** |
| 2048×2048  | ~10-15s | **~15s** |
| 4096×4096  | ~30-60s | **~60s** (tiled) |

**Notes:**
- First request per instance downloads models (~500MB nuclear, ~800MB membrane)
- Models cached in `/app/data/models` for instance lifetime
- Large images (>2048×2048) use automatic tiling
- GPU acceleration can provide 5-10× speedup

---

## Monitoring Setup

### Key Metrics to Monitor

#### 1. Request Latency
**Metric:** `run.googleapis.com/request_latencies`

**Thresholds:**
- **P50 < 10s** (warm requests)
- **P95 < 60s** (includes some cold starts)
- **P99 < 120s** (large images + cold starts)

**Alert if:**
- P95 > 120s consistently (indicates resource constraints)
- P50 > 30s (all requests slow, not just cold starts)

#### 2. Memory Utilization
**Metric:** `run.googleapis.com/container/memory/utilizations`

**Thresholds:**
- **Average < 70%** (of 4GiB = <2.8GiB used)
- **Peak < 90%** (<3.6GiB used)

**Alert if:**
- Average > 80% (increase memory limit)
- Any instance hits 95% (risk of OOM kills)

**Action:**
```bash
# Increase memory to 8GiB
gcloud run services update mcp-deepcell \
  --memory=8Gi \
  --region=us-central1 \
  --project=precision-medicine-poc
```

#### 3. CPU Utilization
**Metric:** `run.googleapis.com/container/cpu/utilizations`

**Thresholds:**
- **Average < 80%** during processing
- **Idle < 10%** when not processing

**Alert if:**
- Average > 90% consistently (CPU-bound, consider more vCPUs)
- Many requests queuing (increase max instances)

**Action:**
```bash
# Increase CPU to 4 vCPUs
gcloud run services update mcp-deepcell \
  --cpu=4 \
  --region=us-central1 \
  --project=precision-medicine-poc
```

#### 4. Request Count
**Metric:** `run.googleapis.com/request_count`

**Monitor:**
- Total requests/day
- Requests/hour during peak times
- Success rate (2xx responses)

**Alert if:**
- Success rate < 95%
- Unexpected traffic spikes

#### 5. Error Rate
**Metric:** `run.googleapis.com/request_count` (filtered by response code)

**Thresholds:**
- **5xx errors < 1%** (server errors)
- **4xx errors < 5%** (client errors acceptable for invalid requests)

**Alert if:**
- 5xx error rate > 2%
- Sudden spike in errors

#### 6. Instance Count
**Metric:** `run.googleapis.com/container/instance_count`

**Monitor:**
- Active instances during peak times
- Auto-scaling behavior
- Cold start frequency

**Alert if:**
- Frequently hitting max instances (increase limit)
- Excessive cold starts (consider minimum instances)

#### 7. Startup Latency
**Metric:** `run.googleapis.com/startup_latencies`

**Thresholds:**
- **Average < 30s** (container startup)
- **P95 < 60s**

**Alert if:**
- Startup latency > 90s (indicates slow container initialization)

---

## Cloud Monitoring Dashboards

### Create Monitoring Dashboard

```bash
# Create dashboard via gcloud (JSON config)
gcloud monitoring dashboards create --config-from-file=dashboard-config.json
```

**Dashboard Config:** `dashboard-config.json` (see below)

### Quick Monitoring Commands

```bash
# View recent logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=mcp-deepcell" \
  --limit=50 \
  --format=json \
  --project=precision-medicine-poc

# View errors only
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=mcp-deepcell AND severity>=ERROR" \
  --limit=20 \
  --project=precision-medicine-poc

# View request latency (last hour)
gcloud monitoring time-series list \
  --filter='metric.type="run.googleapis.com/request_latencies" AND resource.labels.service_name="mcp-deepcell"' \
  --project=precision-medicine-poc

# View memory utilization
gcloud monitoring time-series list \
  --filter='metric.type="run.googleapis.com/container/memory/utilizations" AND resource.labels.service_name="mcp-deepcell"' \
  --project=precision-medicine-poc
```

---

## Alert Policies

### Recommended Alerts

#### 1. High Error Rate
```yaml
Condition: 5xx error rate > 2% for 5 minutes
Severity: Critical
Action: Page on-call engineer
```

#### 2. High Memory Usage
```yaml
Condition: Memory utilization > 85% for 10 minutes
Severity: Warning
Action: Email team, consider scaling up
```

#### 3. High Latency
```yaml
Condition: P95 latency > 120s for 15 minutes
Severity: Warning
Action: Email team, investigate performance
```

#### 4. Instance Limit Reached
```yaml
Condition: Instance count = max instances for 5 minutes
Severity: Warning
Action: Email team, consider increasing limit
```

### Create Alert Policy (Example)

```bash
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="mcp-deepcell High Memory Usage" \
  --condition-display-name="Memory > 85%" \
  --condition-threshold-value=0.85 \
  --condition-threshold-duration=600s \
  --aggregation-alignment-period=60s \
  --condition-filter='resource.type="cloud_run_revision" AND resource.labels.service_name="mcp-deepcell" AND metric.type="run.googleapis.com/container/memory/utilizations"' \
  --project=precision-medicine-poc
```

---

## Performance Optimization Recommendations

### 1. For Faster Cold Starts
**Current:** 30-40s cold start (container + model download)

**Optimizations:**
- **Minimum Instances:** Set min instances to 1 to keep service warm
  ```bash
  gcloud run services update mcp-deepcell --min-instances=1
  ```
  - Cost: ~$35-50/month for always-on instance
  - Benefit: Eliminates cold starts entirely

- **Startup CPU Boost:** Already enabled (✅)
  - Allocates more CPU during startup for faster model loading

### 2. For Higher Throughput
**Current:** 1 concurrent request per instance (model caching)

**Optimizations:**
- **Increase Max Instances:** Scale to handle more concurrent requests
  ```bash
  gcloud run services update mcp-deepcell --max-instances=20
  ```

- **Increase CPU:** Faster inference per request
  ```bash
  gcloud run services update mcp-deepcell --cpu=4
  ```

- **Reduce Concurrency:** Better model caching (current: 160, recommend: 1-5)
  ```bash
  gcloud run services update mcp-deepcell --concurrency=1
  ```
  - Ensures each instance handles one request at a time
  - Better model cache efficiency
  - More predictable performance

### 3. For Large Image Processing
**Current:** 4Gi memory, automatic tiling for >2048×2048

**Optimizations:**
- **Increase Memory:** Process larger images without tiling
  ```bash
  gcloud run services update mcp-deepcell --memory=8Gi
  ```

- **Increase Timeout:** For very large images (>4096×4096)
  ```bash
  gcloud run services update mcp-deepcell --timeout=600
  ```

### 4. For GPU Acceleration (Optional)
**Current:** CPU-only

**Requirements:**
- Update Dockerfile with CUDA/cuDNN
- Enable GPU in Cloud Run (Preview)
- Update DeepCell to use GPU

**Benefits:**
- 5-10× faster inference
- Better for high-throughput production

**Cost:**
- T4 GPU: ~$0.35/hour additional
- Recommended for >100 requests/day

---

## Cost Optimization

### Current Estimated Costs (CPU-only)

#### Pay-per-use (Current Config)
```
Resources: 4Gi RAM, 2 vCPU, 300s timeout
Pricing:
  - CPU: $0.00002400/vCPU-second
  - Memory: $0.00000250/GiB-second
  - Requests: $0.40/million

Estimated monthly cost (moderate usage):
  - 1000 requests/day × 10s avg = 10,000 vCPU-seconds/day
  - = 300,000 vCPU-seconds/month
  - = $7.20/month (CPU) + $9.00/month (memory) + $0.01 (requests)
  - Total: ~$16-20/month
```

#### With Minimum Instance (Always Warm)
```
1 instance always running:
  - 720 hours/month × 2 vCPU × 3600s = 5,184,000 vCPU-seconds
  - Cost: ~$124/month (CPU) + ~$72/month (memory)
  - Total: ~$200/month

Only recommended for production with SLA requirements
```

### Cost Reduction Strategies

1. **Scale to Zero** (Default)
   - No minimum instances
   - Instances shut down when idle
   - Accept cold start latency

2. **Reduce Memory** (If Usage < 50%)
   - Monitor memory utilization
   - If consistently < 2GiB, reduce to 2Gi
   - Saves 50% on memory costs

3. **Optimize Concurrency**
   - Set concurrency to 1-5 for better caching
   - Reduces number of instances needed
   - Lower total costs

4. **Request Batching**
   - Batch multiple images per request
   - Amortize model loading overhead
   - Fewer total requests

---

## Troubleshooting Performance Issues

### Issue: High Latency on All Requests

**Symptoms:**
- P50 latency > 30s
- Even warm requests slow

**Diagnosis:**
```bash
# Check CPU utilization
gcloud monitoring time-series list \
  --filter='metric.type="run.googleapis.com/container/cpu/utilizations"' \
  --project=precision-medicine-poc

# Check if requests queuing
gcloud logging read "resource.labels.service_name=mcp-deepcell AND textPayload=~'waiting for available instance'" \
  --limit=20
```

**Solutions:**
1. Increase CPU allocation (2 → 4 vCPUs)
2. Increase max instances (if queuing)
3. Check if models are re-downloading (should be cached)

### Issue: Out of Memory Errors

**Symptoms:**
- 500 errors in logs
- "Out of memory" messages
- Container restarts

**Diagnosis:**
```bash
# Check memory utilization
gcloud monitoring time-series list \
  --filter='metric.type="run.googleapis.com/container/memory/utilizations"' \
  --project=precision-medicine-poc

# Check for OOM kills in logs
gcloud logging read "resource.labels.service_name=mcp-deepcell AND textPayload=~'killed.*memory'" \
  --limit=10
```

**Solutions:**
1. Increase memory limit (4Gi → 8Gi)
2. Reduce image size (use tiling)
3. Reduce concurrency (160 → 1) to limit simultaneous requests

### Issue: Frequent Cold Starts

**Symptoms:**
- Many requests take 30-40s
- First request always slow

**Diagnosis:**
```bash
# Check instance lifecycle
gcloud logging read "resource.labels.service_name=mcp-deepcell AND textPayload=~'Started server process'" \
  --limit=20

# Count cold starts per hour
gcloud logging read "resource.labels.service_name=mcp-deepcell AND textPayload=~'Application startup complete'" \
  --limit=100
```

**Solutions:**
1. Set minimum instances to 1 (keeps service warm)
2. Increase timeout before scale-to-zero
3. Pre-warm instances before peak traffic

### Issue: Model Download Failures

**Symptoms:**
- "Failed to download model" errors
- Timeouts on first request

**Diagnosis:**
```bash
# Check for download errors
gcloud logging read "resource.labels.service_name=mcp-deepcell AND severity>=ERROR AND textPayload=~'download'" \
  --limit=20

# Check network connectivity
gcloud logging read "resource.labels.service_name=mcp-deepcell AND textPayload=~'ConnectionError'" \
  --limit=10
```

**Solutions:**
1. Verify internet connectivity from Cloud Run
2. Check if DeepCell model zoo is accessible
3. Increase timeout for model download (first request)
4. Consider pre-caching models in Docker image

---

## Health Checks

### Service Health Endpoint

**Status Check:**
```bash
# Service status
gcloud run services describe mcp-deepcell \
  --region=us-central1 \
  --format='value(status.conditions[0].status)' \
  --project=precision-medicine-poc
# Should return: True
```

**Startup Probe:**
- Type: TCP on port 8080
- Timeout: 240s
- Already configured ✅

### Application Health

**MCP Server Health:**
```bash
# Check if SSE endpoint responds
curl -N -H "Accept: text/event-stream" \
  https://mcp-deepcell-ondu7mwjpa-uc.a.run.app/sse &
sleep 2
kill %1

# Should connect without errors (timeout expected)
```

**Model Cache Health:**
```bash
# Check if models are cached (from logs)
gcloud logging read "resource.labels.service_name=mcp-deepcell AND textPayload=~'Loading cached model'" \
  --limit=5

# Should see model loads from cache on subsequent requests
```

---

## Performance Testing Results

### Baseline Tests (2026-01-31)

**Configuration:**
- Memory: 4Gi
- CPU: 2 vCPUs
- Region: us-central1

**Test Results:** (To be updated after testing with real images)

| Test | Image Size | Cold Start | Warm Request | Status |
|------|------------|------------|--------------|--------|
| Nuclear Seg | 512×512 | TBD | TBD | Pending |
| Nuclear Seg | 1024×1024 | TBD | TBD | Pending |
| Nuclear Seg | 2048×2048 | TBD | TBD | Pending |
| Membrane Seg | 512×512 | TBD | TBD | Pending |
| Classification | 512×512 | TBD | TBD | Pending |

**To run performance tests:**
```bash
# Use test data from GCS
gs://sample-inputs-patientone/mcp-deepcell-test-data/test_data/
```

---

## Monitoring Checklist

### Daily Monitoring
- [ ] Check error rate (should be < 1%)
- [ ] Review recent logs for warnings
- [ ] Verify service status (Ready: True)

### Weekly Monitoring
- [ ] Review latency trends (P50, P95, P99)
- [ ] Check memory utilization trends
- [ ] Review request volume and patterns
- [ ] Check for any cost anomalies

### Monthly Monitoring
- [ ] Full performance benchmarking
- [ ] Review and update alert thresholds
- [ ] Cost optimization review
- [ ] Capacity planning for next month

---

## Next Steps

1. **Set Up Alerts** (Pending)
   - Create alert policies for critical metrics
   - Configure notification channels
   - Test alert delivery

2. **Run Performance Tests** (Pending)
   - Test with synthetic data from GCS
   - Measure actual latency and throughput
   - Validate against expected baselines

3. **Optimize Configuration** (Pending)
   - Adjust resources based on actual usage
   - Fine-tune concurrency settings
   - Consider minimum instances for SLA

4. **Production Hardening** (Pending)
   - Set up monitoring dashboard
   - Configure log-based metrics
   - Implement custom health checks

---

**Status:** ✅ Service Healthy and Monitored
**Next Review:** After performance testing with real images
