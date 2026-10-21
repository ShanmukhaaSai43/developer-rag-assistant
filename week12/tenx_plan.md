# 10× Scaling Plan & Production Economics (50,000 Queries/Day)

**Module:** Week 12 Capstone  
**Baseline Metric:** Measured per-query economics from end-to-end telemetry [`week12/trace_sample.json`](file:///c:/Users/Admin/Documents/GenAi/Demo/week12/trace_sample.json)

---

## 1. Unit Economics: Cost per Query

| Cost Component | Measured Consumption | Unit Price | Cost per Query (USD) |
|:---|:---:|:---:|:---:|
| **LLM Input Tokens** | 3,653 tokens / query | $0.075 / 1M tokens | $0.000274 |
| **LLM Output Tokens** | 157 tokens / query | $0.300 / 1M tokens | $0.000047 |
| **MCP Tool Execution Spans** | 2 spans / query | In-memory SQLite | $0.000020 |
| **Total Cost per Query** | — | — | **$0.000341 USD** |

### Projected Daily & Monthly Budgets:
* **Current Scale (5,000 queries/day):** $1.71 USD / day ($51.30 / month)
* **Target Scale (50,000 queries/day):** **$17.05 USD / day** ($511.50 / month)
* **Stress Scale (500,000 queries/day):** **$170.50 USD / day** ($5,115.00 / month)

---

## 2. What Breaks First at 50,000 Queries a Day?

### Bottleneck #1: SQLite File Lock Contention (Breaks at ~12 QPS)
* **The Math:** 50,000 queries distributed over 24 hours averages 0.58 QPS. However, kitchen apps experience heavy meal-time peak bursts (6:00 PM – 8:30 PM), concentrating 40% of traffic into 2.5 hours:
  $$\text{Peak Traffic} = \frac{50,000 \times 0.40}{2.5 \times 3600\text{ sec}} \approx \mathbf{2.2\text{ QPS average, peaking at 15–20 QPS}}$$
* **The Failure:** `sqlite3` uses file-level locking. When telemetry logger writes concurrent audit spans while searches execute, queries stall with `sqlite3.OperationalError: database is locked`.
* **Fix & Architecture Evolution:**
  1. Immediate: Enable SQLite WAL (Write-Ahead Logging) mode (`PRAGMA journal_mode=WAL;`).
  2. 50k+ Target: Migrate catalog to **PostgreSQL with 2 Read Replicas**; offload telemetry writes asynchronously to Redis queue or Pub/Sub.

### Bottleneck #2: MCP Stdio Subprocess Exhaustion (Breaks at ~25 Concurrent Users)
* **The Failure:** Spawning a dedicated Python subprocess over stdio pipes for every incoming web request exhausts OS process tables and file descriptors (`EMFILE: too many open files`).
* **Fix & Architecture Evolution:**
  * Transition MCP server transport from `stdio` to persistent **Streamed HTTP / SSE (Server-Sent Events)** or **gRPC** with connection pooling.

### Bottleneck #3: Upstream LLM Provider Rate Limits
* **The Failure:** Standard free-tier quota (15 RPM) fails immediately. At 20 peak QPS (1,200 RPM), unmanaged requests receive HTTP 429 errors.
* **Fix & Architecture Evolution:**
  * Provision Google Cloud Vertex AI / Gemini Enterprise quota tier.
  * Implement client-side exponential backoff with jitter and a semantic cache for top-100 pantry recipe queries (e.g. "pasta in 20 min" served directly from Redis cache at $0.00 cost).
