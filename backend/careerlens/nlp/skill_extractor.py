"""Two-Layer Skill Extraction Pipeline for CareerLens.
Combines:
- Layer 1: Explicit matching (Aho-Corasick, alias normalization, ambiguity resolution)
- Layer 2: Implicit inference (bullet extraction, sentence-transformers semantic matching)
Merges both layers, eliminates duplicates, and formats according to the ParsedResume.skills contract.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from careerlens.nlp.explicit_matcher import ExplicitSkillMatcher
from careerlens.nlp.implicit_matcher import ImplicitSkillMatcher
from careerlens.nlp.taxonomy_loader import SkillTaxonomy

LOG = logging.getLogger("careerlens.nlp.pipeline")


class TwoLayerSkillExtractor:
    """
    Two-layer skill extractor integrating explicit taxonomy keyword matching
    and implicit bullet embedding inference into the shared ParsedResume schema.
    """

    def __init__(
        self,
        taxonomy: Optional[SkillTaxonomy] = None,
        explicit_matcher: Optional[ExplicitSkillMatcher] = None,
        implicit_matcher: Optional[ImplicitSkillMatcher] = None,
        default_implicit_threshold: float = 0.52
    ):
        self.taxonomy = taxonomy or SkillTaxonomy()
        self.explicit_matcher = explicit_matcher or ExplicitSkillMatcher(taxonomy=self.taxonomy)
        self.implicit_matcher = implicit_matcher or ImplicitSkillMatcher(taxonomy=self.taxonomy)
        self.default_implicit_threshold = default_implicit_threshold

    def extract_skills(
        self,
        resume_data: Dict[str, Any] | str,
        implicit_threshold: Optional[float] = None,
        include_implicit: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Executes the two-layer skill extraction pipeline:
        1. Explicit Layer: Extracts direct skills, aliases, and disambiguates edge cases.
        2. Implicit Layer: Extracts bullets, computes embeddings, and infers latent skills.
        3. Merge & Deduplicate: Ensures no duplicates and adheres to the shared contract.
        """
        threshold = implicit_threshold if implicit_threshold is not None else self.default_implicit_threshold

        # --- Layer 1: Explicit Extraction ---
        explicit_skills: List[Dict[str, Any]] = []

        if isinstance(resume_data, dict):
            # Check if sections dict is available
            sections = resume_data.get("sections")
            if isinstance(sections, dict) and sections:
                explicit_skills = self.explicit_matcher.extract_from_sections(sections)
            elif "raw_text" in resume_data:
                explicit_skills = self.explicit_matcher.extract_from_text(resume_data["raw_text"], section_name="FullText")
            elif "text" in resume_data:
                explicit_skills = self.explicit_matcher.extract_from_text(resume_data["text"], section_name="FullText")
        elif isinstance(resume_data, str):
            explicit_skills = self.explicit_matcher.extract_from_text(resume_data, section_name="FullText")

        # Explicit canonical names set for deduplication & exclusion
        explicit_canonical_set = {s["name"].lower() for s in explicit_skills}

        # --- Layer 2: Implicit Extraction ---
        implicit_skills: List[Dict[str, Any]] = []
        if include_implicit:
            implicit_skills = self.implicit_matcher.detect_implicit_skills(
                resume_data=resume_data,
                explicit_skills=explicit_canonical_set,
                threshold=threshold
            )

        # --- Layer 3: Merge & Deduplicate ---
        # Explicit skills take precedence. Implicit skills provide latent capabilities.
        merged_dict: Dict[str, Dict[str, Any]] = {}

        # Add explicit skills first
        for s in explicit_skills:
            cname = s["name"]
            merged_dict[cname.lower()] = {
                "name": cname,
                "type": "explicit",
                "confidence": round(float(s.get("confidence", 1.0)), 4),
                "evidence": str(s.get("evidence", ""))
            }

        # Add implicit skills if not present
        for s in implicit_skills:
            cname = s["name"]
            key = cname.lower()
            if key not in merged_dict:
                merged_dict[key] = {
                    "name": cname,
                    "type": "implicit",
                    "confidence": round(float(s.get("confidence", 0.5)), 4),
                    "evidence": str(s.get("evidence", ""))
                }

        # Return list sorted by confidence descending
        final_skills = sorted(merged_dict.values(), key=lambda x: x["confidence"], reverse=True)
        return final_skills

    def enhance_parsed_resume(
        self,
        parsed_resume: Dict[str, Any],
        implicit_threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Enriches a ParsedResume object from NER / OCR with the two-layer skills extraction.
        Maintains complete adherence to the shared JSON ParsedResume contract:
        {resume_id, name, email, education, experience, skills:[{name, type, confidence, evidence}], sections, raw_text}
        """
        enriched_skills = self.extract_skills(
            resume_data=parsed_resume,
            implicit_threshold=implicit_threshold
        )
        parsed_resume["skills"] = enriched_skills
        return parsed_resume

    def benchmark_latency(
        self,
        resume_data: Dict[str, Any] | str,
        n_runs: int = 3
    ) -> Dict[str, Any]:
        """
        Measures processing latency across explicit and implicit layers.
        Verifies latency target of under 2 seconds per resume.
        """
        # Warmup
        _ = self.extract_skills(resume_data, include_implicit=True)

        explicit_times: List[float] = []
        implicit_times: List[float] = []
        total_times: List[float] = []

        for _ in range(n_runs):
            t0 = time.perf_counter()
            # Explicit
            t_exp_0 = time.perf_counter()
            explicit_res = self.extract_skills(resume_data, include_implicit=False)
            t_exp_1 = time.perf_counter()

            # Implicit
            t_imp_0 = time.perf_counter()
            _ = self.implicit_matcher.detect_implicit_skills(
                resume_data=resume_data,
                explicit_skills={s["name"].lower() for s in explicit_res}
            )
            t_imp_1 = time.perf_counter()
            t_total_1 = time.perf_counter()

            explicit_times.append((t_exp_1 - t_exp_0) * 1000)
            implicit_times.append((t_imp_1 - t_imp_0) * 1000)
            total_times.append((t_total_1 - t0) * 1000)

        avg_explicit_ms = sum(explicit_times) / len(explicit_times)
        avg_implicit_ms = sum(implicit_times) / len(implicit_times)
        avg_total_ms = sum(total_times) / len(total_times)

        return {
            "explicit_ms": round(avg_explicit_ms, 2),
            "implicit_ms": round(avg_implicit_ms, 2),
            "total_ms": round(avg_total_ms, 2),
            "target_under_2_seconds": avg_total_ms < 2000.0,
            "status": "PASS" if avg_total_ms < 2000.0 else "FAIL"
        }
