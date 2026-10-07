# Embedding service benchmark

Measured locally on 7 October 2026 with `all-MiniLM-L6-v2`, PyTorch CPU, Intel CPU (Windows reports `Intel64 Family 6 Model 142 Stepping 11`), and 30 iterations per case. The script warmed the model through FastAPI lifespan before timing; payload text varied to avoid measuring LRU cache hits.

| Request | Mean latency (ms) | p95 latency (ms) |
|---|---:|---:|
| Single text | 17.14 | 40.49 |
| Batch of 16 | 16.54 | 28.27 |
| ParsedResume | 197.55 | 254.42 |

The CPU target for this representative resume was met (p95 254.42 ms). Model download and first-start warm-up are excluded from request latency. Results vary with CPU and resume size.

Concurrent HTTP load check against local Uvicorn: 30 distinct single-text requests with 2 workers completed in 1.64 seconds (18.24 requests/second), mean client-observed latency 107.63 ms, p95 192.50 ms. Requests used different text to avoid cache-hit throughput inflation.

Real-model similarity sanity check: cosine(`Python developer`, `Python engineer`) = 0.8628; cosine(`Python developer`, `chef`) = 0.1486.
