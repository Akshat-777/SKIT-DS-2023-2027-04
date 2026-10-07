"""Focused tests for CareerLens skill normalization and market demand calculations."""

import unittest
from datetime import date

from market.taxonomy import build_skill_demand, match_skill, normalize_role, normalize_skill, validate_index


class SkillNormalizationTests(unittest.TestCase):
    def test_aliases_normalize_to_canonical_names(self):
        self.assertEqual(normalize_skill("JS"), "JavaScript")
        self.assertEqual(normalize_skill("ML"), "Machine Learning")
        self.assertEqual(normalize_skill("Postgres"), "PostgreSQL")

    def test_fuzzy_near_match_and_unknown_review(self):
        self.assertEqual(normalize_skill("PostgreSql"), "PostgreSQL")
        self.assertEqual(match_skill("Kubernets")["status"], "fuzzy")
        self.assertEqual(match_skill("LangChain")["status"], "review")
        self.assertEqual(match_skill("Quantum Basket Weaving")["status"], "unmatched")

    def test_title_role_and_seniority_rules(self):
        self.assertEqual(normalize_role("Sr. Software Engineer - ML"), ("ML Engineer", "Senior"))
        self.assertEqual(normalize_role("Data Science Intern"), ("Data Scientist", "Intern"))


class SkillDemandTests(unittest.TestCase):
    def test_share_rank_salary_and_cooccurrence(self):
        rows = [
            {"job_id": "1", "title": "Senior Data Scientist", "skills_required": ["Python", "ML", "SQL"],
             "salary_min": 10, "salary_max": 14, "posted_at": "2026-09-20"},
            {"job_id": "2", "title": "Data Scientist", "skills_required": ["Python", "Postgres"],
             "salary_min": 12, "salary_max": 16, "posted_at": "2026-08-20"},
            {"job_id": "3", "title": "Data Scientist", "skills_required": ["SQL"],
             "salary_min": 8, "salary_max": 10, "posted_at": "2026-09-25"},
            {"job_id": "4", "title": "Data Science Intern", "skills_required": ["Python"],
             "posted_at": "2026-09-28"},
        ]
        index = build_skill_demand(rows, minimum_postings=2, as_of=date(2026, 9, 30))
        python_senior = next(row for row in index["skill_demand"]
                             if row["role"] == "Data Scientist" and row["seniority"] == "Senior" and row["skill"] == "Python")
        self.assertEqual(python_senior["demand_pct"], 100.0)
        self.assertEqual(python_senior["rank"], 1)
        self.assertEqual(python_senior["average_salary_lpa"], 12.0)
        self.assertIn("Machine Learning", python_senior["co_occurring_skills"])
        self.assertTrue(python_senior["low_sample"])
        self.assertEqual(validate_index(index), [])

    def test_demand_is_posting_share_and_bounded(self):
        rows = [
            {"title": "Backend Developer", "skills_required": ["Python"]},
            {"title": "Backend Developer", "skills_required": ["SQL"]},
            {"title": "Backend Developer", "skills_required": ["Python", "SQL"]},
        ]
        index = build_skill_demand(rows, minimum_postings=1, as_of=date(2026, 9, 30))
        python = next(row for row in index["skill_demand"] if row["skill"] == "Python")
        self.assertEqual(python["demand_pct"], 66.67)
        self.assertTrue(all(0 <= row["demand_pct"] <= 100 for row in index["skill_demand"]))

    def test_monthly_trend_compares_recent_and_previous_periods(self):
        rows = [
            {"title": "Backend Developer", "skills_required": ["Python"], "posted_at": "2026-09-05"},
            {"title": "Backend Developer", "skills_required": ["Python"], "posted_at": "2026-09-10"},
            {"title": "Backend Developer", "skills_required": ["Python"], "posted_at": "2026-09-15"},
            {"title": "Backend Developer", "skills_required": ["SQL"], "posted_at": "2026-09-20"},
            {"title": "Backend Developer", "skills_required": ["SQL"], "posted_at": "2026-08-10"},
            {"title": "Backend Developer", "skills_required": ["SQL"], "posted_at": "2026-08-20"},
        ]
        index = build_skill_demand(rows, minimum_postings=2, as_of=date(2026, 9, 30))
        python = next(row for row in index["skill_demand"]
                      if row["role"] == "Backend Developer" and row["seniority"] == "All" and row["skill"] == "Python")
        self.assertEqual(python["trend"], "rising")


if __name__ == "__main__":
    unittest.main()
