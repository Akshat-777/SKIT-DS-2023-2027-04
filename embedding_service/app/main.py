"""FastAPI embedding service for CareerLens resume and job vectors."""

from contextlib import asynccontextmanager
from typing import Any

import numpy as np
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .config import settings
from .engine import EmbeddingEngine
from .resume import job_texts, resume_texts
from .schemas import BatchEmbedRequest, EmbedRequest, EmbeddingResponse, SimilarityRequest

LOG = logging.getLogger("careerlens.embedding")


def create_app(engine: EmbeddingEngine | None = None, load_model_on_startup: bool = True) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if engine is not None:
            app.state.engine = engine
        elif load_model_on_startup:
            LOG.info("Loading embedding model %s", settings.model_name)
            loaded = await run_in_threadpool(EmbeddingEngine)
            app.state.engine = loaded
            await run_in_threadpool(loaded.warmup)
            LOG.info("Embedding model ready: %s", loaded.model_info())
        else:
            app.state.engine = None
        yield

    app = FastAPI(title="CareerLens Embedding Service", version="1.0.0", lifespan=lifespan)

    def get_engine(request: Request) -> EmbeddingEngine:
        active = getattr(request.app.state, "engine", None)
        if active is None:
            raise HTTPException(status_code=503, detail={"error": {"code": "MODEL_NOT_READY",
                "message": "Embedding model has not been loaded"}})
        return active

    def response(active: EmbeddingEngine, vectors: Any):
        return {"model": active.model_name, "dim": active.dimension, "vectors": vectors}

    @app.exception_handler(HTTPException)
    async def http_error_handler(_request: Request, exc: HTTPException):
        detail = exc.detail
        if isinstance(detail, dict) and "error" in detail:
            content = detail
        else:
            content = {"error": {"code": "HTTP_ERROR", "message": str(detail)}}
        return JSONResponse(status_code=exc.status_code, content=content)

    @app.exception_handler(ValueError)
    async def value_error_handler(_request: Request, exc: ValueError):
        return JSONResponse(status_code=422, content={"error": {"code": "INVALID_INPUT", "message": str(exc)}})

    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(_request: Request, exc: RequestValidationError):
        errors = exc.errors()
        message = "; ".join(str(item.get("msg", "Invalid request")) for item in errors)
        return JSONResponse(status_code=422, content={"error": {"code": "INVALID_INPUT", "message": message}})

    @app.get("/health")
    async def health(request: Request):
        active = getattr(request.app.state, "engine", None)
        if active is None:
            return JSONResponse(status_code=503, content={"status": "loading", "model_loaded": False})
        return {"status": "ok", "model_loaded": True, "device": str(active.device),
                "performance": active.performance_info()}

    @app.get("/model-info")
    async def model_info(request: Request):
        active = get_engine(request)
        return active.model_info()

    @app.post("/embed", response_model=EmbeddingResponse)
    async def embed(body: EmbedRequest, request: Request):
        active = get_engine(request)
        vectors = await run_in_threadpool(active.embed_text, body.text)
        return response(active, [vectors])

    @app.post("/embed/batch", response_model=EmbeddingResponse)
    async def embed_batch(body: BatchEmbedRequest, request: Request):
        active = get_engine(request)
        if len(body.texts) > active.config.max_batch_size:
            raise HTTPException(status_code=413, detail={"error": {"code": "BATCH_TOO_LARGE",
                "message": f"Batch has {len(body.texts)} texts; configured maximum is {active.config.max_batch_size}"}})
        vectors = await run_in_threadpool(active.embed_texts, body.texts)
        return response(active, vectors)

    @app.post("/embed/resume", response_model=EmbeddingResponse)
    async def embed_resume(payload: dict[str, Any], request: Request):
        active = get_engine(request)
        whole, parts = resume_texts(payload)
        labels, texts = [], []
        for section, value in parts.items():
            section_values = value if isinstance(value, list) else ([value] if value else [])
            for index, text in enumerate(section_values):
                labels.append((section, index if isinstance(value, list) else None))
                texts.append(text)
        labels.append(("whole_resume", None))
        texts.append(whole)
        vectors = await run_in_threadpool(active.embed_texts, texts)
        structured = {}
        for (section, index), vector in zip(labels, vectors):
            if index is None:
                structured[section] = vector
            else:
                structured.setdefault(section, []).append(vector)
        return response(active, structured)

    @app.post("/embed/job", response_model=EmbeddingResponse)
    async def embed_job(payload: dict[str, Any], request: Request):
        active = get_engine(request)
        whole, parts = job_texts(payload)
        labels = [key for key, text in parts.items() if text]
        texts = [parts[key] for key in labels] + [whole]
        vectors = await run_in_threadpool(active.embed_texts, texts)
        structured = {label: vector for label, vector in zip(labels, vectors)}
        structured["whole_job"] = vectors[-1]
        return response(active, structured)

    @app.post("/similarity")
    async def similarity(body: SimilarityRequest, request: Request):
        active = get_engine(request)
        if body.text_a is not None:
            left, right = await run_in_threadpool(active.embed_texts, [body.text_a, body.text_b])
        else:
            left = np.asarray(body.vector_a, dtype=np.float64)
            right = np.asarray(body.vector_b, dtype=np.float64)
            if left.size != active.dimension or right.size != active.dimension:
                raise HTTPException(status_code=422, detail={"error": {"code": "DIMENSION_MISMATCH",
                    "message": f"Vectors must both have model dimension {active.dimension}"}})
        left_norm, right_norm = float(np.linalg.norm(left)), float(np.linalg.norm(right))
        if not np.isfinite(left_norm) or not np.isfinite(right_norm) or left_norm == 0 or right_norm == 0:
            raise HTTPException(status_code=422, detail={"error": {"code": "INVALID_VECTOR",
                "message": "Cosine similarity requires finite, non-zero vectors"}})
        cosine = float(np.dot(left, right) / (left_norm * right_norm))
        return {"similarity": max(-1.0, min(1.0, cosine)), "model": active.model_name}

    return app


app = create_app()
