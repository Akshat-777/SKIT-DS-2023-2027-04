import pytest
import os
import shutil
from app.services.vector_store import VectorStoreService, vector_store_service
from app.services.embedding_client import EmbeddingClient, embedding_client

def test_embedding_client_fallback():
    """Verify EmbeddingClient generates valid float embedding vectors."""
    text = "Software Engineer with Python and FastAPI experience"
    vec = embedding_client.get_embedding(text)
    assert isinstance(vec, list)
    assert len(vec) > 0
    assert all(isinstance(val, float) for val in vec)

def test_embedding_client_batch():
    """Verify EmbeddingClient batch embedding extraction."""
    texts = ["Python Developer", "Data Scientist NLP"]
    vecs = embedding_client.get_embeddings_batch(texts)
    assert isinstance(vecs, list)
    assert len(vecs) == 2
    assert len(vecs[0]) > 0

def test_vector_store_crud():
    """Verify ChromaDB persistent store collection creation, upsert, query, count, and delete."""
    test_db_dir = "./tests/test_chroma_db"
    if os.path.exists(test_db_dir):
        shutil.rmtree(test_db_dir, ignore_errors=True)
        
    vs = VectorStoreService(db_dir=test_db_dir)
    
    # Test count initial
    assert vs.count(vs.JOB_COLLECTION) == 0
    
    # Upsert test items
    ids = ["job_test_1", "job_test_2"]
    docs = [
        "Senior Backend Engineer Python FastAPI PostgreSQL Docker",
        "Data Analyst SQL Tableau Business Intelligence"
    ]
    metas = [
        {"job_id": "job_test_1", "role": "Software Engineer", "company": "Acme Inc"},
        {"job_id": "job_test_2", "role": "Data Analyst", "company": "Metrics Co"}
    ]
    
    success = vs.upsert(
        collection_name=vs.JOB_COLLECTION,
        ids=ids,
        documents=docs,
        metadatas=metas
    )
    assert success is True
    assert vs.count(vs.JOB_COLLECTION) == 2
    
    # Query test items
    results = vs.query(
        collection_name=vs.JOB_COLLECTION,
        query_text="Python FastAPI backend developer",
        n_results=1
    )
    assert len(results) == 1
    assert results[0]["id"] == "job_test_1"
    assert "score" in results[0]
    assert results[0]["metadata"]["company"] == "Acme Inc"
    
    # Delete test item
    del_success = vs.delete(vs.JOB_COLLECTION, ids=["job_test_1"])
    assert del_success is True
    assert vs.count(vs.JOB_COLLECTION) == 1
