# Observability Architecture (Part 1 — Logging, Monitoring, Metrics, Distributed Tracing & Alerting)

**Document Version:** 1.0
**Project:** MindMesh – AI-Powered Knowledge Intelligence System

---

## Purpose
This document defines the complete Observability Architecture of MindMesh. It covers logging formats, metrics targets, distributed trace contexts, alerting rules, and service objectives.

---

## Centralized Structured Logging
Every application service must write structured JSON log entries. Plain console log outputs are prohibited in production:

```json
{
  "timestamp": "2026-06-27T19:46:11Z",
  "level": "INFO",
  "service": "backend-api",
  "trace_id": "8e7a6f...b23",
  "request_id": "req-987d6e",
  "user_id": "usr-12f5a6",
  "workspace_id": "wsp-90d23c",
  "message": "Auth session generated successfully."
}
```

* **Masking**: Sensitive values (OTPs, passwords, tokens, API keys) must be masked.
* **Aggregator**: Loki acts as the log query storage.

---

## Observability Instrumentation Stack
* **Vendor Independence**: Standardized OpenTelemetry metrics and traces endpoints.
* **Collector Engine**:
  * **Metrics**: Prometheus scraper.
  * **Traces**: OpenTelemetry collectors feeding Grafana Tempo.
  * **Dashboards**: Grafana metrics panels.
  * **Alerts**: AlertManager.
  * **Errors**: Sentry Exception Tracker.

---

## Tracing Spans & Correlation
Every client action receives a unique trace propagation header carrying:
* `Request ID`: Correlates single HTTP operations.
* `Trace ID`: Tracks the call path across multi-step processes (e.g. React Frontend -> API Controller -> Service Layer -> DB Query -> Vector Retrieval -> LLM -> Client).
* `Correlation ID`: Links trace spans to Loki log lines.

---

## Service Level Objectives (SLOs)
Operational objectives checked by Prometheus metrics alerts:
* **API Availability**: **99.9%**
* **Search Availability**: **99.9%**
* **AI Engine Availability**: **99.5%**
* **WebSocket Core Availability**: **99.9%**

Every service implements standard endpoints:
* `/health` (general database status)
* `/live` (Liveness checks)
* `/ready` (Readiness checks)
* `/metrics` (Prometheus export endpoint)
