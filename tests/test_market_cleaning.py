"""Salary parsing and duplicate handling tests for the market collection pipeline."""

import unittest

from market.cleaning import deduplicate, normalize_job


class SalaryParsingTests(unittest.TestCase):
    def test_lpa_range_in_description_is_normalized_to_inr_lpa(self):
        job = normalize_job({
            "title": "Data Analyst",
            "company": "Example Analytics",
            "location": "Jaipur, India",
            "description": "Salary range INR 12-18 LPA",
        }, "fixture")
        self.assertAlmostEqual(job.salary_min, 12.0)
        self.assertAlmostEqual(job.salary_max, 18.0)
        self.assertEqual(job.currency, "INR")
        self.assertEqual(job.salary_unit, "INR LPA")

    def test_monthly_salary_in_rupees_is_annualized_to_lpa(self):
        job = normalize_job({
            "title": "Backend Developer",
            "company": "Example Systems",
            "location": "Pune, India",
            "description": "Compensation INR 50,000-75,000 per month",
        }, "fixture")
        self.assertAlmostEqual(job.salary_min, 6.0)
        self.assertAlmostEqual(job.salary_max, 9.0)

    def test_provider_annual_rupees_are_converted_to_lpa(self):
        job = normalize_job({
            "id": "annual-salary",
            "title": "ML Engineer",
            "company": "Example AI",
            "location": "Remote, India",
            "salary_min": 1_200_000,
            "salary_max": 1_800_000,
            "currency": "INR",
            "salary_period": "year",
            "description": "Build machine learning systems",
        }, "fixture")
        self.assertAlmostEqual(job.salary_min, 12.0)
        self.assertAlmostEqual(job.salary_max, 18.0)

    def test_unknown_currency_salary_is_left_uncovered(self):
        job = normalize_job({
            "title": "Engineer", "company": "Example", "location": "Remote",
            "salary_min": 80_000, "salary_max": 100_000, "currency": "USD",
            "salary_period": "year", "description": "Build software",
        }, "fixture")
        self.assertIsNone(job.salary_min)
        self.assertIsNone(job.salary_max)
        self.assertEqual(job.currency, "USD")


class DeduplicationTests(unittest.TestCase):
    def test_same_source_id_is_deduplicated(self):
        first = normalize_job({"id": "provider-42", "title": "Data Scientist",
                               "company": "Acme", "location": "Jaipur"}, "adzuna")
        second = normalize_job({"id": "provider-42", "title": "Different title",
                                "company": "Other Co", "location": "Delhi"}, "adzuna")
        self.assertEqual(len(deduplicate([first, second])), 1)

    def test_case_insensitive_title_company_location_duplicate_is_removed(self):
        first = normalize_job({"id": "posting-a", "title": "Data Scientist",
                               "company": "Acme Labs", "location": "Jaipur, India"}, "adzuna")
        second = normalize_job({"id": "posting-b", "title": " data scientist ",
                                "company": "acme labs", "location": "JAIPUR, INDIA"}, "jsearch")
        self.assertEqual(len(deduplicate([first, second])), 1)

    def test_distinct_job_identity_is_kept(self):
        first = normalize_job({"id": "posting-a", "title": "Data Scientist",
                               "company": "Acme Labs", "location": "Jaipur, India"}, "adzuna")
        second = normalize_job({"id": "posting-b", "title": "Data Scientist",
                                "company": "Acme Labs", "location": "Delhi, India"}, "jsearch")
        self.assertEqual(len(deduplicate([first, second])), 2)


if __name__ == "__main__":
    unittest.main()
