import os
import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.core.config import settings
from app.services.embedding_client import embedding_client

logger = logging.getLogger("careerlens.vector_store")

class VectorStoreService:
    """
    Vector Store Service wrapping persistent ChromaDB client.
    Manages 'resume_embeddings' and 'job_embeddings' collections.
    """
    RESUME_COLLECTION = "resume_embeddings"
    JOB_COLLECTION = "job_embeddings"

    def __init__(self, db_dir: Optional[str] = None):
        self.db_dir = db_dir or settings.CHROMA_DB_DIR
        os.makedirs(self.db_dir, exist_ok=True)
        logger.info(f"Initializing ChromaDB persistent client at: {self.db_dir}")
        self.client = chromadb.PersistentClient(
            path=self.db_dir,
            settings=ChromaSettings(anonymized_telemetry=False, allow_reset=True)
        )
        self._ensure_collections()

    def _ensure_collections(self):
        """Initializes collections if they do not exist."""
        self.resume_collection = self.client.get_or_create_collection(
            name=self.RESUME_COLLECTION,
            metadata={"description": "Vector embeddings for candidate resumes"}
        )
        self.job_collection = self.client.get_or_create_collection(
            name=self.JOB_COLLECTION,
            metadata={"description": "Vector embeddings for job postings"}
        )

    def _get_collection(self, collection_name: str):
        if collection_name == self.RESUME_COLLECTION:
            return self.resume_collection
        elif collection_name == self.JOB_COLLECTION:
            return self.job_collection
        else:
            return self.client.get_or_create_collection(name=collection_name)

    def _clean_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Ensures metadata values are valid ChromaDB primitives (str, int, float, bool)."""
        clean_meta = {}
        for k, v in metadata.items():
            if v is None:
                continue
            if isinstance(v, (str, int, float, bool)):
                clean_meta[k] = v
            elif isinstance(v, list):
                clean_meta[k] = ",".join(str(item) for item in v)
            else:
                clean_meta[k] = str(v)
        return clean_meta

    def upsert(
        self,
        collection_name: str,
        ids: List[str],
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        embeddings: Optional[List[List[float]]] = None
    ) -> bool:
        """
        Upserts documents and metadata into the specified vector collection.
        If embeddings are not provided, generates them via embedding_client.
        """
        if not ids or not documents:
            return False

        if embeddings is None:
            embeddings = embedding_client.get_embeddings_batch(documents)

        clean_metadatas = [self._clean_metadata(m) for m in (metadatas or [{}] * len(ids))]
        collection = self._get_collection(collection_name)

        collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=clean_metadatas,
            embeddings=embeddings
        )
        logger.info(f"Upserted {len(ids)} items into ChromaDB collection '{collection_name}'")
        return True

    def query(
        self,
        collection_name: str,
        query_text: Optional[str] = None,
        query_embedding: Optional[List[float]] = None,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Queries collection by text or embedding vector with optional metadata filter ('where').
        Returns list of structured match records with id, distance, metadata, and document.
        """
        if query_embedding is None and query_text is not None:
            query_embedding = embedding_client.get_embedding(query_text)

        if query_embedding is None:
            raise ValueError("Either query_text or query_embedding must be provided.")

        collection = self._get_collection(collection_name)
        
        # Execute query
        kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": n_results
        }
        if where:
            kwargs["where"] = where

        results = collection.query(**kwargs)

        output = []
        if results and results.get("ids") and len(results["ids"]) > 0:
            ids = results["ids"][0]
            distances = results["distances"][0] if results.get("distances") else [0.0] * len(ids)
            metadatas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(ids)
            documents = results["documents"][0] if results.get("documents") else [""] * len(ids)

            for i in range(len(ids)):
                # Convert distance to similarity score (cosine distance in ChromaDB is 1 - similarity)
                dist = float(distances[i])
                similarity = max(0.0, min(1.0, 1.0 - dist))
                output.append({
                    "id": ids[i],
                    "score": round(similarity, 4),
                    "distance": round(dist, 4),
                    "metadata": metadatas[i],
                    "document": documents[i]
                })

        return output

    def delete(self, collection_name: str, ids: List[str]) -> bool:
        """Deletes items by ID from specified collection."""
        if not ids:
            return False
        collection = self._get_collection(collection_name)
        collection.delete(ids=ids)
        logger.info(f"Deleted {len(ids)} items from collection '{collection_name}'")
        return True

    def count(self, collection_name: str) -> int:
        """Returns total item count in specified collection."""
        collection = self._get_collection(collection_name)
        return collection.count()

vector_store_service = VectorStoreService()
