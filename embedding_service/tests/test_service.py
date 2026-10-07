"""Offline tests for vector shape, normalization, inputs, and semantic similarity."""

import math
import re

import numpy as np
from fastapi.testclient import TestClient

from embedding_service.app.config import Settings
from embedding_service.app.engine import EmbeddingEngine
from embedding_service.app.main import create_app


class WhitespaceTokenizer:
    def __init__(self):
        self.id_to_token = {}

    def encode(self, text, add_special_tokens=False):
        tokens = text.split()
        self.id_to_token = {index: token for index, token in enumerate(tokens)}
        return list(range(len(tokens)))

    def decode(self, token_ids, skip_special_tokens=True, clean_up_tokenization_spaces=True):
        return " ".join(self.id_to_token[token] for token in token_ids)


class SemanticFakeModel:
    tokenizer = WhitespaceTokenizer()
    max_seq_length = 8
    device = "cpu"

    def __init__(self):
        self.calls = 0

    def get_sentence_embedding_dimension(self):
        return 4

    def encode(self, texts, **_kwargs):
        self.calls += 1
        result = []
        for text in texts:
            vector = np.zeros(4, dtype=np.float32)
            for token in re.findall(r"[a-z]+", text.lower()):
                if token == "python":
                    vector += [1, 0, 0, 0]
                elif token in ("developer", "engineer"):
                    vector += [0, 1, 0, 0]
                elif token == "chef":
                    vector += [0, 0, 1, 0]
                else:
                    vector += [0, 0, 0, 1]
            result.append(vector if np.linalg.norm(vector) else np.array([0, 0, 0, 1], dtype=np.float32))
        return np.asarray(result)


def make_client():
    model = SemanticFakeModel()
    config = Settings(model_name="test-semantic-model", device="cpu", max_batch_size=64,
                      encoder_batch_size=8, cache_size=32, chunk_overlap=1, hf_home="")
    engine = EmbeddingEngine(model=model, config=config)
    app = create_app(engine=engine, load_model_on_startup=False)
    app.state.engine = engine
    return TestClient(app), engine


def test_vectors_have_expected_dimension_and_unit_norm():
    client, _engine = make_client()
    response = client.post("/embed", json={"text": "Python developer"})
    assert response.status_code == 200
    data = response.json()
    assert data["dim"] == 4
    vector = data["vectors"][0]
    assert len(vector) == 4
    assert math.isclose(math.sqrt(sum(value * value for value in vector)), 1.0, rel_tol=1e-6)


def test_related_job_titles_are_closer_than_unrelated_title():
    client, _engine = make_client()
    related = client.post("/similarity", json={"text_a": "Python developer", "text_b": "Python engineer"}).json()["similarity"]
    unrelated = client.post("/similarity", json={"text_a": "Python developer", "text_b": "chef"}).json()["similarity"]
    assert related > unrelated


def test_batch_and_lru_cache():
    client, engine = make_client()
    batch = client.post("/embed/batch", json={"texts": ["Python developer", "Python engineer"]})
    assert batch.status_code == 200
    assert len(batch.json()["vectors"]) == 2
    calls_after_batch = engine.model.calls
    again = client.post("/embed", json={"text": "Python developer"})
    assert again.status_code == 200
    assert engine.model.calls == calls_after_batch
    too_many = client.post("/embed/batch", json={"texts": ["text"] * 65})
    assert too_many.status_code == 413
    assert too_many.json()["error"]["code"] == "BATCH_TOO_LARGE"


def test_empty_input_uses_shared_error_contract():
    client, _engine = make_client()
    response = client.post("/embed", json={"text": "   "})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_INPUT"
    batch = client.post("/embed/batch", json={"texts": [""]})
    assert batch.status_code == 422


def test_resume_and_job_return_section_vectors():
    client, _engine = make_client()
    resume = {
        "resume_id": "r-1", "name": "Example", "raw_text": "Additional experience text",
        "sections": {"summary": "Python engineer summary", "projects": "A Python project"},
        "experience": [{"title": "Engineer", "company": "Example Co", "bullets": ["Built APIs"]}],
        "skills": [{"name": "Python", "evidence": "Built scripts"}],
    }
    response = client.post("/embed/resume", json=resume)
    assert response.status_code == 200
    vectors = response.json()["vectors"]
    assert all(key in vectors for key in ("summary", "experience_bullets", "skills", "projects", "whole_resume"))
    assert len(vectors["experience_bullets"]) == 1

    job = client.post("/embed/job", json={"title": "Python Engineer", "skills_required": ["Python", "SQL"],
                                         "description": "Build services"})
    assert job.status_code == 200
    assert set(job.json()["vectors"]) == {"title", "skills", "description", "whole_job"}


def test_long_text_is_chunked_and_vectors_are_normalized():
    client, engine = make_client()
    long_text = " ".join(["Python developer"] * 60)
    response = client.post("/embed", json={"text": long_text})
    assert response.status_code == 200
    vector = response.json()["vectors"][0]
    assert engine.model.calls == 1
    assert math.isclose(math.sqrt(sum(value * value for value in vector)), 1.0, rel_tol=1e-6)


def test_model_info_and_health_include_runtime_metrics():
    client, _engine = make_client()
    assert client.get("/health").json()["model_loaded"] is True
    info = client.get("/model-info").json()
    assert info["name"] == "test-semantic-model"
    assert info["dimension"] == 4
    assert info["max_tokens"] == 8
