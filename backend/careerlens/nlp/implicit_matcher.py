"""Implicit Skill Detection Engine for CareerLens.
Extracts experience & project bullets, computes semantic vector embeddings using
sentence-transformers (all-MiniLM-L6-v2), Aryan's embedding service, or TF-IDF vectorizer,
matches against cached exemplar skill embeddings using vectorized cosine similarity,
and infers latent skills with evidence while excluding explicit matches.
"""

from __future__ import annotations

import os
import sys

# Prevent broken protobuf / tensorflow collisions in Windows Python environment
os.environ["USE_TF"] = "0"
os.environ["USE_TORCH"] = "1"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"
if "tensorflow" not in sys.modules:
    sys.modules["tensorflow"] = None  # type: ignore

import hashlib
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

from careerlens.nlp.taxonomy_loader import SkillTaxonomy

LOG = logging.getLogger("careerlens.nlp.implicit")

DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"
DEFAULT_SIMILARITY_THRESHOLD = 0.52
DEFAULT_TOP_K_PER_BULLET = 3


def extract_resume_bullets(
    resume_data: Dict[str, Any] | str
) -> List[str]:
    """
    Extracts informative bullet statements from resume experience/projects.
    Handles parsed resume objects, raw sections, and bullet markers (-, *, •, numbers).
    """
    raw_bullets: List[str] = []

    if isinstance(resume_data, dict):
        # 1. From experience object
        for exp in resume_data.get("experience", []):
            if isinstance(exp, dict) and "bullets" in exp:
                for b in exp["bullets"]:
                    if isinstance(b, str) and len(b.strip()) > 15:
                        raw_bullets.append(b.strip())

        # 2. From projects object if present
        for proj in resume_data.get("projects", []):
            if isinstance(proj, dict) and "bullets" in proj:
                for b in proj["bullets"]:
                    if isinstance(b, str) and len(b.strip()) > 15:
                        raw_bullets.append(b.strip())

        # 3. From sections dict
        sections = resume_data.get("sections", {})
        if isinstance(sections, dict):
            for sec_name, sec_text in sections.items():
                if any(k in sec_name.lower() for k in ["experience", "project", "work", "employment"]):
                    lines = sec_text.split("\n")
                    for line in lines:
                        cleaned = re.sub(r"^[\s\-\*\•\–\—\d\.]+", "", line).strip()
                        if len(cleaned) > 20 and not cleaned.startswith("["):
                            raw_bullets.append(cleaned)

        # 4. Fallback to raw text if no bullets found yet
        if not raw_bullets and "raw_text" in resume_data:
            text = resume_data["raw_text"]
            for line in text.split("\n"):
                cleaned = re.sub(r"^[\s\-\*\•\–\—\d\.]+", "", line).strip()
                if len(cleaned) > 25 and not cleaned.startswith("["):
                    raw_bullets.append(cleaned)

    elif isinstance(resume_data, str):
        for line in resume_data.split("\n"):
            cleaned = re.sub(r"^[\s\-\*\•\–\—\d\.]+", "", line).strip()
            if len(cleaned) > 25 and not cleaned.startswith("["):
                raw_bullets.append(cleaned)

    # Clean and deduplicate bullets while preserving order
    deduped_bullets: List[str] = []
    seen: Set[str] = set()

    for b in raw_bullets:
        clean_b = re.sub(r"\s+", " ", b).strip()
        # Filter headers or date strings
        if len(clean_b) < 20 or re.match(r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|20\d\d)\b", clean_b):
            continue
        norm_key = clean_b.lower()
        if norm_key not in seen:
            seen.add(norm_key)
            deduped_bullets.append(clean_b)

    return deduped_bullets


class ImplicitSkillMatcher:
    """
    Embedding-based implicit skill detector with on-disk embedding caching,
    vectorized cosine similarity matching, and graceful offline fallback.
    """

    def __init__(
        self,
        taxonomy: Optional[SkillTaxonomy] = None,
        model_name: str = DEFAULT_MODEL_NAME,
        cache_dir: Optional[str] = None
    ):
        self.taxonomy = taxonomy or SkillTaxonomy()
        self.model_name = model_name
        self._model = None
        self._tfidf_vectorizer = None
        self._tfidf_matrix = None
        
        # Setup cache directory
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path(__file__).resolve().parent / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_path = self.cache_dir / "skill_exemplar_embeddings.npz"

        # Cached exemplar vectors and mappings
        self.exemplar_texts: List[str] = []
        self.exemplar_skills: List[str] = []
        self.exemplar_embeddings: Optional[np.ndarray] = None  # Normalized (N, D)

        self._load_or_build_exemplar_embeddings()

    def _get_model(self):
        """Lazy load sentence-transformers model with TF-IDF fallback."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                LOG.info(f"Loading embedding model: {self.model_name}")
                self._model = SentenceTransformer(self.model_name)
            except Exception as e:
                LOG.warning(f"Could not load SentenceTransformer ({e}). Using scikit-learn TF-IDF engine.")
                self._model = "TFIDF"
        return self._model

    def _compute_taxonomy_hash(self, exemplars: List[Tuple[str, str]]) -> str:
        """Computes hash of exemplar text and skill pairs for cache invalidation."""
        serialized = json.dumps(exemplars, sort_keys=True)
        return hashlib.md5(serialized.encode("utf-8")).hexdigest()

    def _load_or_build_exemplar_embeddings(self) -> None:
        """Loads cached exemplar embeddings from disk or computes and persists them."""
        all_exemplars = self.taxonomy.get_all_exemplars()
        current_hash = self._compute_taxonomy_hash(all_exemplars)

        if self.cache_path.exists():
            try:
                data = np.load(self.cache_path, allow_pickle=True)
                cached_hash = str(data["taxonomy_hash"])
                if cached_hash == current_hash:
                    self.exemplar_embeddings = data["embeddings"]
                    self.exemplar_skills = list(data["skills"])
                    self.exemplar_texts = list(data["texts"])
                    LOG.info(f"Loaded {len(self.exemplar_skills)} cached skill exemplar embeddings from {self.cache_path}")
                    return
                else:
                    LOG.info("Taxonomy changed; rebuilding exemplar embeddings cache.")
            except Exception as e:
                LOG.warning(f"Failed to load cache from {self.cache_path}: {e}")

        # Compute embeddings for all exemplars
        LOG.info(f"Computing embeddings for {len(all_exemplars)} skill exemplars...")
        texts = [ex[0] for ex in all_exemplars]
        skills = [ex[1] for ex in all_exemplars]

        model = self._get_model()
        if model != "TFIDF":
            try:
                embeddings = model.encode(texts, batch_size=64, show_progress_bar=False, normalize_embeddings=True)
                embeddings = np.asarray(embeddings, dtype=np.float32)

                self.exemplar_embeddings = embeddings
                self.exemplar_skills = skills
                self.exemplar_texts = texts

                # Persist to disk
                np.savez_compressed(
                    self.cache_path,
                    embeddings=self.exemplar_embeddings,
                    skills=np.array(self.exemplar_skills),
                    texts=np.array(self.exemplar_texts),
                    taxonomy_hash=current_hash
                )
                LOG.info(f"Saved {len(skills)} skill exemplar embeddings to cache at {self.cache_path}")
                return
            except Exception as e:
                LOG.warning(f"Error encoding with SentenceTransformer: {e}. Falling back to TF-IDF.")

        # Fallback to TF-IDF
        self._init_tfidf_engine(texts, skills)

    def _init_tfidf_engine(self, texts: List[str], skills: List[str]) -> None:
        """Fallback lightweight vectorizer when transformer models are unavailable."""
        from sklearn.feature_extraction.text import TfidfVectorizer
        self._tfidf_vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)
        self._tfidf_matrix = self._tfidf_vectorizer.fit_transform(texts)
        self.exemplar_skills = skills
        self.exemplar_texts = texts

    def detect_implicit_skills(
        self,
        resume_data: Dict[str, Any] | str,
        explicit_skills: Optional[Set[str]] = None,
        threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
        top_k_per_bullet: int = DEFAULT_TOP_K_PER_BULLET
    ) -> List[Dict[str, Any]]:
        """
        Embeds resume bullets and performs cosine similarity matching against
        exemplar database. Skills already detected explicitly are excluded.
        """
        bullets = extract_resume_bullets(resume_data)
        if not bullets:
            return []

        explicit_set = {s.lower() for s in (explicit_skills or set())}
        implicit_candidates: Dict[str, Dict[str, Any]] = {}

        model = self._get_model()

        # Branch 1: Sentence-Transformers (Dense embeddings)
        if model != "TFIDF" and self.exemplar_embeddings is not None:
            try:
                bullet_embeddings = model.encode(
                    bullets,
                    batch_size=32,
                    show_progress_bar=False,
                    normalize_embeddings=True
                )
                bullet_embeddings = np.asarray(bullet_embeddings, dtype=np.float32)

                # Vectorized cosine similarity: (M_bullets, N_exemplars)
                similarity_matrix = np.dot(bullet_embeddings, self.exemplar_embeddings.T)

                for bullet_idx, bullet_text in enumerate(bullets):
                    sim_scores = similarity_matrix[bullet_idx]
                    top_indices = np.argsort(sim_scores)[::-1][:top_k_per_bullet]

                    for idx in top_indices:
                        score = float(sim_scores[idx])
                        if score < threshold:
                            continue

                        canonical_name = self.exemplar_skills[idx]
                        if canonical_name.lower() in explicit_set:
                            continue

                        if canonical_name in implicit_candidates:
                            if score > implicit_candidates[canonical_name]["confidence"]:
                                implicit_candidates[canonical_name]["confidence"] = round(score, 4)
                                implicit_candidates[canonical_name]["evidence"] = bullet_text
                        else:
                            implicit_candidates[canonical_name] = {
                                "name": canonical_name,
                                "type": "implicit",
                                "confidence": round(score, 4),
                                "evidence": bullet_text
                            }

                return sorted(implicit_candidates.values(), key=lambda s: s["confidence"], reverse=True)
            except Exception as e:
                LOG.warning(f"Dense vector similarity failed ({e}); falling back to TF-IDF.")

        # Branch 2: TF-IDF fallback
        if self._tfidf_vectorizer is None:
            all_exemplars = self.taxonomy.get_all_exemplars()
            self._init_tfidf_engine([ex[0] for ex in all_exemplars], [ex[1] for ex in all_exemplars])

        if self._tfidf_vectorizer is not None and self._tfidf_matrix is not None:
            bullet_vecs = self._tfidf_vectorizer.transform(bullets)
            sim_sparse = (bullet_vecs * self._tfidf_matrix.T).toarray()
            # Scaled threshold for TF-IDF (TF-IDF cosine is sparser than dense vectors)
            adjusted_thresh = max(0.20, threshold - 0.20)

            for bullet_idx, bullet_text in enumerate(bullets):
                sim_scores = sim_sparse[bullet_idx]
                top_indices = np.argsort(sim_scores)[::-1][:top_k_per_bullet]

                for idx in top_indices:
                    score = float(sim_scores[idx])
                    if score < adjusted_thresh:
                        continue

                    canonical_name = self.exemplar_skills[idx]
                    if canonical_name.lower() in explicit_set:
                        continue

                    calibrated_score = min(1.0, round(score + 0.20, 4))
                    if canonical_name in implicit_candidates:
                        if calibrated_score > implicit_candidates[canonical_name]["confidence"]:
                            implicit_candidates[canonical_name]["confidence"] = calibrated_score
                            implicit_candidates[canonical_name]["evidence"] = bullet_text
                    else:
                        implicit_candidates[canonical_name] = {
                            "name": canonical_name,
                            "type": "implicit",
                            "confidence": calibrated_score,
                            "evidence": bullet_text
                        }

        return sorted(implicit_candidates.values(), key=lambda s: s["confidence"], reverse=True)
