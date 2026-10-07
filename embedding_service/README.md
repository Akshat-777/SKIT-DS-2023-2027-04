# CareerLens Embedding Service

Standalone FastAPI microservice for resume and job embeddings. It uses `sentence-transformers/all-MiniLM-L6-v2` by default: a compact English model with a 384-dimensional output and 256-token default sequence length. This is a good fit for CPU deployment and short career text; `EMBEDDING_MODEL` can select another compatible SentenceTransformer model. Model weights are fetched once and kept in the Hugging Face cache volume.

## Install and run locally

From the repository root:

```powershell
python -m pip install -r embedding_service/requirements.txt
$env:EMBEDDING_DEVICE = "cpu"
python -m uvicorn embedding_service.app.main:app --host 0.0.0.0 --port 8000
```

At startup, the service loads the model once, selects CPU/GPU from `EMBEDDING_DEVICE`, and runs a warm-up embedding. `auto` prefers CUDA, then Apple MPS, then CPU. Set `EMBEDDING_MODEL` to change the encoder. Set `HF_HOME` to a persistent model cache directory.

## Docker

Build from the repository root and start with a named volume for downloaded weights:

```powershell
docker build -f embedding_service/Dockerfile -t careerlens-embedding .
docker run --rm -p 8000:8000 -v careerlens-model-cache:/models/hf careerlens-embedding
```

The container loads the configured model on its first start; the volume keeps the model cached for later starts. To use a different model or a larger request batch, configure `EMBEDDING_MODEL` and `EMBEDDING_MAX_BATCH_SIZE` with Docker's `-e` option. `EMBEDDING_DEVICE=cpu` is the container default; GPU deployment requires a CUDA-enabled image/runtime and compatible PyTorch installation.

## API

All vector endpoints return the model name, vector dimension, and float vectors. `/embed` returns one vector in the `vectors` array. `/embed/batch` returns one vector per input, with up to 64 texts by default. Both split long text into model-token windows with overlap, mean-pool the window embeddings, and L2-normalize each result. `EMBEDDING_MAX_BATCH_SIZE`, `EMBEDDING_ENCODER_BATCH_SIZE`, `EMBEDDING_CPU_THREADS`, `EMBEDDING_CACHE_SIZE`, and `EMBEDDING_CHUNK_OVERLAP` configure runtime behavior. CPU thread count defaults to 2 to limit transformer thread oversubscription on small batches.

`POST /embed/resume` accepts the shared `ParsedResume` object and returns `summary`, `experience_bullets`, `skills`, `projects`, and `whole_resume` vectors when those sections exist. Experience bullets return one vector each. `POST /embed/job` accepts `title`, `skills_required`, and `description` and returns available section vectors plus `whole_job`. `POST /similarity` accepts either two text fields or two same-dimension vectors. Whitespace-only/empty inputs receive HTTP 422 in the shared `{"error":{"code":...,"message":...}}` format.

| Endpoint | Example request |
|---|---|
| `GET /health` | Reports model readiness and observed request latency/throughput metrics. |
| `GET /model-info` | Returns model name, dimension, max tokens, device, and overlap. |
| `POST /embed` | `{"text":"Python developer with SQL experience"}` |
| `POST /embed/batch` | `{"texts":["Python engineer","Data analyst"]}` |
| `POST /embed/resume` | Shared `ParsedResume` JSON contract. |
| `POST /embed/job` | `{"title":"ML Engineer","skills_required":["Python","PyTorch"],"description":"Build and deploy machine learning services."}` |
| `POST /similarity` | `{"text_a":"Python developer","text_b":"Python engineer"}` |

Interactive API docs are available at `http://localhost:8000/docs`.

## Backend client

Akshat's backend can import `EmbeddingClient` from `embedding_service.client` when it has the repository on its Python path:

```python
from embedding_service.client import EmbeddingClient

client = EmbeddingClient(base_url="http://embedding-service:8000")
resume_vectors = client.embed_resume(parsed_resume)
job_vectors = client.embed_job(job_posting)
similarity = client.similarity("Python developer", "Python engineer")
```

The helper retries connection/timeouts, HTTP 429, and server-side 5xx responses with exponential backoff.

## Tests and performance measurement

The pytest suite uses a deterministic fake encoder, so it does not need model downloads:

```powershell
python -m pytest embedding_service/tests -q
```

After model weights are available, measure warmed CPU inference locally:

```powershell
$env:EMBEDDING_DEVICE = "cpu"
python -m embedding_service.benchmark --iterations 30
```

To measure concurrent HTTP traffic against a running service:

```powershell
python embedding_service/load_test.py --url http://127.0.0.1:8000 --requests 100 --workers 8
```

The service reports recent average/p95 request latency and effective text throughput in `GET /health`. Benchmark numbers depend on CPU, thread scheduling, model cache state, and resume size; record the local output in `BENCHMARK.md` instead of assuming the 300 ms target is met on every host.
