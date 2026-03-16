# vhidushak — Distributed LLM Inference System

A production-grade distributed inference service built on FastAPI, Redis, vLLM, with full observability via OpenTelemetry, Prometheus, and Grafana.

---

## Architecture

```
Client
  │
  ▼
FastAPI API Gateway (port 8000)
  │  ← emits traces, metrics
  ▼
Redis Job Queue (port 6379)
  │
  ▼
Worker Processes (metrics port 8002)
  │  ← emits traces, metrics, GPU stats
  ▼
vLLM Runtime (port 8001)
  │
  ▼
GPU

Observability Stack:
  Jaeger     (port 16686)  ← distributed traces
  Prometheus (port 9090)   ← metrics scraper
  Grafana    (port 3000)   ← dashboards
```

---

## Project Structure

```
src/
  inference_systems/
    api/
      server.py          # FastAPI gateway — accepts requests, pushes to queue
    workers/
      worker.py          # Pulls jobs, runs inference, stores results
    job_queue/
      redis_client.py    # push_job / pop_job / store_result / get_result
    tracing.py           # OpenTelemetry tracer factory
    metrics.py           # Shared Prometheus metrics definitions
  llm_inference_server/
    server.py            # Standalone FastAPI → vLLM proxy (single-process mode)
prometheus.yml           # Prometheus scrape config
docker-compose.yml       # Full stack orchestration
Dockerfile.api
Dockerfile.worker
```

---

## Installation

```bash
python -m venv venv
source venv/bin/activate
pip install fastapi uvicorn redis requests \
  opentelemetry-api opentelemetry-sdk \
  opentelemetry-exporter-otlp-proto-grpc \
  prometheus-client
```

---


**Services:**

| Service | Port | Description |
|---------|------|-------------|
| api | 8000 | FastAPI gateway |
| worker | 8002 | Worker Prometheus metrics |
| redis | 6379 | Job queue |
| jaeger | 16686 | Trace UI |
| prometheus | 9090 | Metrics UI |
| grafana | 3000 | Dashboards (admin/admin) |

---

## API Reference

### `POST /generate?prompt=<text>`
Enqueues an inference job.

```json
{"status": "queued", "request_id": "uuid"}
```

### `GET /result/{request_id}`
Polls for a completed result.

```json
{"status": "processing"}
```
or the full vLLM completion response when done.

### `GET /metrics`
Prometheus metrics endpoint (API gateway).

---

## Key Design Decisions

**Why Redis as a queue?**
Decouples API latency from GPU latency. API returns immediately; clients poll for results. The queue absorbs traffic spikes without dropping requests or blocking.

**Why OTLP over Jaeger Thrift?**
`opentelemetry-exporter-jaeger` is deprecated. OTLP is the modern OpenTelemetry wire protocol, supported natively by Jaeger, Grafana Tempo, and every major trace backend.

**Why expose worker metrics on a separate port (8002)?**
Workers are long-running loop processes, not web servers. `prometheus_client.start_http_server()` spins a background thread, keeping the inference loop unblocked.

**Why separate vLLM from docker-compose?**
vLLM requires GPU device passthrough which varies across container runtimes (Docker, Podman, Kubernetes). Running it directly on the host avoids runtime-specific GPU configuration.
