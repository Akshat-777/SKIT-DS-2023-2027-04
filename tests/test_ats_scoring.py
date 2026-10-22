"""Focused tests for the first ATS scoring slice."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

BACKEND_ROOT = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services import scorer
from app.services.embedding_client import embedding_client
from app.schemas.resume import ScoreResult


class ATSScoringTests(unittest.TestCase):
    def setUp(self):
        self.skills = [
            {"name": "JS", "confidence": 0.95, "evidence": "Built React interfaces"},
            {"name": "Postgres", "confidence": 0.65, "evidence": "Used in project"},
        ]
        self.education = [{"degree": "B.Tech", "institution": "SKIT", "year": 2026}]
        self.experience = [{"title": "Backend Engineer", "company": "Example",
                            "start": "2024", "end": "2025",
                            "bullets": ["Improved API response time by 30%"]}]
        self.sections = {"education": True, "experience": True, "skills": True,
                         "contact": True, "summary": False}
        self.raw_text = "Backend Engineer Python PostgreSQL JavaScript API improved response time by 30% " * 35

    def test_weights_are_configured_and_total_one(self):
        weights = scorer._scoring_weights()
        self.assertEqual(set(weights), {
            "keyword_match", "semantic_similarity", "section_completeness",
            "formatting", "experience_relevance", "quantified_impact",
        })
        self.assertAlmostEqual(sum(weights.values()), 1.0)

    def test_keyword_score_uses_market_demand_and_skill_aliases(self):
        with patch.object(embedding_client, "get_service_embeddings_batch", return_value=None):
            result = scorer.compute_ats_score(
                self.skills, self.education, self.experience, self.sections,
                self.raw_text, "Backend Developer",
            )
        market_rows = scorer._role_market_demand("Backend Developer")
        expected = sum(value for skill, value in market_rows.items()
                       if scorer._canonical_skill(skill).casefold() in {"javascript", "postgresql"})
        self.assertGreater(expected, 0)
        self.assertEqual(result["breakdown"]["keyword_match"], round(100 * expected / sum(market_rows.values()), 1))
        gap = scorer.compute_skill_gap(self.skills, self.raw_text, "Backend Developer")
        self.assertIn("JavaScript", gap["matched"])
        self.assertIn("PostgreSQL", gap["matched"])

    def test_semantic_component_uses_embedding_service_cosine(self):
        with patch.object(embedding_client, "get_service_embeddings_batch",
                          return_value=[[1.0, 0.0], [0.8, 0.6]]) as embed:
            result = scorer.compute_ats_score(
                self.skills, self.education, self.experience, self.sections,
                self.raw_text, "Backend Developer",
            )
        self.assertEqual(result["breakdown"]["semantic_similarity"], 80.0)
        self.assertEqual(len(embed.call_args.args[0]), 2)
        semantic_reason = next(item for item in result["reasons"]
                               if item["factor"] == "semantic_similarity")
        self.assertIn("embedding service", semantic_reason["reason"])

    def test_offline_embedding_is_neutral_and_explained(self):
        with patch.object(embedding_client, "get_service_embeddings_batch", return_value=None):
            result = scorer.compute_ats_score(
                self.skills, self.education, self.experience, self.sections,
                self.raw_text, "Backend Developer",
            )
        self.assertEqual(result["breakdown"]["semantic_similarity"], 50.0)
        self.assertIn("unavailable", next(item["reason"] for item in result["reasons"]
                                           if item["factor"] == "semantic_similarity"))

    def test_score_is_bounded_and_each_factor_has_explanation(self):
        with patch.object(embedding_client, "get_service_embeddings_batch", return_value=None):
            result = scorer.compute_ats_score(
                self.skills, self.education, self.experience, self.sections,
                self.raw_text, "Backend Developer",
            )
        self.assertGreaterEqual(result["ats_score"], 0)
        self.assertLessEqual(result["ats_score"], 100)
        self.assertEqual(len(result["reasons"]), 6)
        self.assertTrue(all(item.get("reason") and item.get("how_to_improve")
                            for item in result["reasons"]))
        result_contract = ScoreResult(
            resume_id="resume-test", target_role="Backend Developer",
            ats_score=result["ats_score"], breakdown=result["breakdown"],
            skill_gap=scorer.compute_skill_gap(self.skills, self.raw_text, "Backend Developer"),
            reasons=result["reasons"],
        )
        self.assertEqual(result_contract.resume_id, "resume-test")


if __name__ == "__main__":
    unittest.main()
