"""Comprehensive PyTest Suite for CareerLens Two-Layer Skill Extraction.
Tests:
- Skill Taxonomy Loader & Lookups (300+ skills, aliases, categories, exemplars)
- Explicit Skill Extraction (case-insensitivity, normalization, punctuation variants)
- Contextual Ambiguity Disambiguation (Go, R, Spring, Word, Excel)
- Implicit Skill Detection (bullets, embedding cosine matching, exclusion of explicit skills)
- Two-Layer Merged Contract Compliance (ParsedResume.skills schema)
- Performance Latency Target (< 2.0s per resume)
"""

import sys
import os
import pytest
import time

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from careerlens.nlp.taxonomy_loader import SkillTaxonomy, normalize_lookup_key
from careerlens.nlp.explicit_matcher import ExplicitSkillMatcher, is_valid_token_boundary
from careerlens.nlp.implicit_matcher import ImplicitSkillMatcher, extract_resume_bullets
from careerlens.nlp.skill_extractor import TwoLayerSkillExtractor
from careerlens.nlp.evaluation import compute_metrics, LABELED_RESUMES


@pytest.fixture(scope="module")
def taxonomy():
    return SkillTaxonomy()


@pytest.fixture(scope="module")
def extractor(taxonomy):
    return TwoLayerSkillExtractor(taxonomy=taxonomy)


# ==================== DELIVERABLE 1 TESTS: TAXONOMY LOADER ====================

def test_taxonomy_loader_size(taxonomy):
    """Verify that taxonomy contains at least 300 canonical skills."""
    assert taxonomy.total_skills_count >= 300, f"Expected >= 300 skills, found {taxonomy.total_skills_count}"


def test_taxonomy_canonical_resolution(taxonomy):
    """Verify alias to canonical resolution for various skills."""
    assert taxonomy.get_canonical("js") == "JavaScript"
    assert taxonomy.get_canonical("k8s") == "Kubernetes"
    assert taxonomy.get_canonical("py") == "Python"
    assert taxonomy.get_canonical("cpp") == "C++"
    assert taxonomy.get_canonical("cplusplus") == "C++"
    assert taxonomy.get_canonical("scikit learn") == "Scikit-learn"
    assert taxonomy.get_canonical("postgres") == "PostgreSQL"
    assert taxonomy.get_canonical("ts") == "TypeScript"
    assert taxonomy.get_canonical("tf") == "TensorFlow"


def test_taxonomy_metadata_and_exemplars(taxonomy):
    """Verify that skills contain categories, parents, and exemplar phrases."""
    py_info = taxonomy.get_skill_info("Python")
    assert py_info is not None
    assert py_info["category"] == "Programming Languages"
    assert len(py_info["exemplars"]) > 0

    all_exemplars = taxonomy.get_all_exemplars()
    assert len(all_exemplars) >= 300, "Exemplar database should have extensive coverage"


# ==================== DELIVERABLE 2 TESTS: EXPLICIT EXTRACTION ====================

def test_token_boundary_checks():
    """Verify punctuation boundary rules for C++, Node.js, and JS inside words."""
    # Valid C++
    assert is_valid_token_boundary("Proficient in C++ and Python.", 14, 17, "c++") is True
    # C++ followed by symbol should not match if inside identifier
    assert is_valid_token_boundary("abc C+++ def", 4, 7, "c++") is False

    # Valid Node.js
    assert is_valid_token_boundary("Experience with Node.js backend.", 16, 23, "node.js") is True

    # JS must NOT match inside JSON
    assert is_valid_token_boundary("Parsing JSON payloads.", 8, 10, "js") is False


def test_explicit_extraction_aliasing_and_punctuation(taxonomy):
    """Verify extraction of aliases and punctuation variants."""
    matcher = ExplicitSkillMatcher(taxonomy=taxonomy)
    text = "Core skills: C++, C#, Node.js, scikit-learn, JS, and k8s."
    results = matcher.extract_from_text(text, section_name="Skills")
    detected = {r["name"]: r["confidence"] for r in results}

    assert "C++" in detected
    assert "C#" in detected
    assert "Node.js" in detected
    assert "Scikit-learn" in detected
    assert "JavaScript" in detected
    assert "Kubernetes" in detected


def test_ambiguity_go_disambiguation(taxonomy):
    """Verify 'Go' in tech context is accepted, while action verb 'go' is rejected."""
    matcher = ExplicitSkillMatcher(taxonomy=taxonomy)

    # Valid tech context
    res_valid = matcher.extract_from_text("Built concurrent microservices in Go using Docker.", section_name="Exp")
    assert any(r["name"] == "Go" for r in res_valid)

    # Invalid action verb
    res_invalid = matcher.extract_from_text("Let us go to the market next week.", section_name="General")
    assert not any(r["name"] == "Go" for r in res_invalid)


def test_ambiguity_spring_disambiguation(taxonomy):
    """Verify 'Spring Boot' is accepted, while 'Spring 2022' (academic term) is rejected."""
    matcher = ExplicitSkillMatcher(taxonomy=taxonomy)

    # Valid Spring Boot
    res_boot = matcher.extract_from_text("Architected Java Spring Boot REST microservices.", section_name="Exp")
    assert any(r["name"] == "Spring Boot" for r in res_boot)

    # Invalid semester
    res_term = matcher.extract_from_text("Graduated from SKIT Jaipur in Spring 2022.", section_name="Education")
    assert not any(r["name"] == "Spring" for r in res_term)


def test_ambiguity_r_disambiguation(taxonomy):
    """Verify R programming is accepted in tech/data context, while middle initials are rejected."""
    matcher = ExplicitSkillMatcher(taxonomy=taxonomy)

    # Valid R programming list
    res_valid = matcher.extract_from_text("Analyzed clinical trial data with Python, R, and SQL.", section_name="Exp")
    assert any(r["name"] == "R" for r in res_valid)

    # Invalid middle initial
    res_initial = matcher.extract_from_text("Author: John R. Smith, Research Lead.", section_name="Header")
    assert not any(r["name"] == "R" for r in res_initial)


def test_ambiguity_excel_disambiguation(taxonomy):
    """Verify Excel tool is accepted, while English verb 'excelled' is rejected."""
    matcher = ExplicitSkillMatcher(taxonomy=taxonomy)

    # Valid Excel tool
    res_tool = matcher.extract_from_text("Proficient in advanced Microsoft Excel spreadsheets and pivot tables.", section_name="Skills")
    assert any(r["name"] == "Excel" for r in res_tool)

    # Invalid English verb
    res_verb = matcher.extract_from_text("Consistently excelled in all previous academic coursework.", section_name="Summary")
    assert not any(r["name"] == "Excel" for r in res_verb)


# ==================== DELIVERABLE 3 TESTS: IMPLICIT EXTRACTION ====================

def test_extract_resume_bullets():
    """Verify bullet splitting from parsed objects and raw text."""
    sample = {
        "experience": [{
            "bullets": [
                "Built asynchronous REST APIs using FastAPI and PostgreSQL.",
                "Containerized microservices using Docker."
            ]
        }],
        "sections": {
            "Projects": "- Implemented token classification using PyTorch.\n- Automated deployment via GitHub Actions."
        }
    }
    bullets = extract_resume_bullets(sample)
    assert len(bullets) >= 4
    assert any("REST APIs" in b for b in bullets)
    assert any("PyTorch" in b for b in bullets)


def test_implicit_detection_and_explicit_exclusion(taxonomy):
    """Verify implicit skill detection and that explicit skills are excluded."""
    matcher = ImplicitSkillMatcher(taxonomy=taxonomy)
    bullets = "Architected high-throughput microservices and configured round-robin load balancing."
    
    # Run with explicit exclusion of 'Microservices'
    implicit_skills = matcher.detect_implicit_skills(
        resume_data=bullets,
        explicit_skills={"Microservices"},
        threshold=0.45
    )
    detected_names = {s["name"] for s in implicit_skills}

    # 'Microservices' was explicitly known, so it MUST NOT be in implicit output
    assert "Microservices" not in detected_names
    # 'Load Balancing' or related latent skills should be detected
    for s in implicit_skills:
        assert s["type"] == "implicit"
        assert s["confidence"] >= 0.45
        assert len(s["evidence"]) > 0


# ==================== DELIVERABLE 4 TESTS: MERGED CONTRACT ====================

def test_merged_contract_adherence(extractor):
    """Verify that enhance_parsed_resume complies with the shared JSON ParsedResume contract."""
    sample_resume = {
        "resume_id": "test_uuid_123",
        "name": "Aishani Billore",
        "email": "aishani@example.com",
        "education": [{"degree": "B.Tech", "institution": "SKIT Jaipur", "year": "2024"}],
        "experience": [{
            "title": "Software Engineer Intern",
            "company": "EduTech",
            "start": "2023",
            "end": "2024",
            "bullets": [
                "Architected asynchronous RESTful APIs using Python and PostgreSQL.",
                "Containerized microservices using Docker."
            ]
        }],
        "skills": [],
        "sections": {
            "Skills": "Python, React, Docker, JavaScript"
        },
        "raw_text": "Aishani Billore. Python, React, Docker, JavaScript. Built RESTful APIs."
    }

    enhanced = extractor.enhance_parsed_resume(sample_resume)

    # Check shared contract keys
    assert "resume_id" in enhanced
    assert "name" in enhanced
    assert "email" in enhanced
    assert "education" in enhanced
    assert "experience" in enhanced
    assert "skills" in enhanced
    assert "sections" in enhanced
    assert "raw_text" in enhanced

    # Check skills structure
    skills_list = enhanced["skills"]
    assert len(skills_list) > 0

    for s in skills_list:
        assert "name" in s
        assert s["type"] in ["explicit", "implicit"]
        assert 0.0 <= s["confidence"] <= 1.0
        assert isinstance(s["evidence"], str) and len(s["evidence"]) > 0

    # Ensure no duplicates
    names = [s["name"].lower() for s in skills_list]
    assert len(names) == len(set(names)), "Skills list must be deduplicated by canonical name"


# ==================== DELIVERABLE 5 TESTS: EVALUATION SUITE ====================

def test_evaluation_metric_computation():
    """Verify computation of Precision, Recall, and F1."""
    preds = {"Python", "React", "Docker"}
    truth = {"Python", "React", "Node.js"}
    metrics = compute_metrics(preds, truth)
    
    # TP = 2 (Python, React), FP = 1 (Docker), FN = 1 (Node.js)
    assert metrics["tp"] == 2
    assert metrics["fp"] == 1
    assert metrics["fn"] == 1
    assert round(metrics["precision"], 2) == 0.67
    assert round(metrics["recall"], 2) == 0.67
    assert round(metrics["f1"], 2) == 0.67


def test_labeled_dataset_size():
    """Verify that labeled benchmark dataset contains 20 resumes."""
    assert len(LABELED_RESUMES) == 20


# ==================== DELIVERABLE 6 TESTS: PERFORMANCE LATENCY ====================

def test_performance_under_two_seconds(extractor):
    """Verify that end-to-end extraction executes under 2 seconds per resume."""
    sample_text = """
    Akshat Agarwal
    Email: akshat@example.com
    [EXPERIENCE]
    - Architected scalable microservices handling 20,000 requests per second in Go.
    - Automated CI/CD pipelines deploying to Amazon EKS clusters.
    - Balanced HTTP requests using Nginx reverse proxy and cached data in Redis.
    [SKILLS]
    Go, Kubernetes, Redis, Docker, Git, AWS
    """
    bench = extractor.benchmark_latency(sample_text, n_runs=3)
    assert bench["total_ms"] < 2000.0, f"Latency {bench['total_ms']} ms exceeded 2000 ms target"
    assert bench["status"] == "PASS"
