"""Demo and Acceptance Verification for CareerLens Two-Layer Skill Extraction.
Demonstrates:
1. Two-layer skill extraction on 3 distinct candidate resumes:
   - Full-Stack NLP Engineer (Aishani Billore)
   - Backend & Distributed Systems Lead (Akshat Agarwal)
   - ML & Market Scoring Engineer (Aryan Rathore)
2. Detailed side-by-side breakdown: Explicit vs Implicit skills with evidence.
3. Verification of Aliasing normalization (JS -> JavaScript, k8s -> Kubernetes, etc.).
4. Verification of Ambiguity disambiguation (Go, R, Spring, Excel, etc.).
5. End-to-end latency benchmark (< 2 seconds per resume).
"""

from __future__ import annotations

import os
import sys

# Ensure backend root is on sys.path
backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

import json
import time
from typing import Any, Dict, List

from careerlens.nlp.skill_extractor import TwoLayerSkillExtractor

# 3 Acceptance Demo Resumes
RESUME_AISHANI = """
Aishani Billore
Email: aishani.billore@skit.ac.in
Phone: +91 9876543210

[EDUCATION]
B.Tech in Computer Science (Data Science)
SKIT Jaipur, Graduated 2024

[EXPERIENCE]
Full Stack & NLP Engineer at EduTech Labs (2023 - 2024)
- Architected asynchronous RESTful APIs using Python, FastAPI, and PostgreSQL with connection pooling.
- Built accessible responsive single-page interfaces with dynamic state management in React and Tailwind CSS.
- Containerized frontend, backend, and vector database microservices using Docker and docker-compose.
- Fine-tuned transformer models for token-level Named Entity Recognition on scanned documents.

[SKILLS]
Python, React, FastAPI, Docker, PostgreSQL, Tailwind CSS, JavaScript
"""

RESUME_AKSHAT = """
Akshat Agarwal
Email: akshat.agarwal@careerlens.io
Phone: +91 9123456789

[EDUCATION]
Bachelor of Technology in Computer Science
RTU Kota, 2023

[EXPERIENCE]
Backend Tech Lead at CloudScale Systems (2022 - Present)
- Engineered high-throughput microservices in Go handling over 30,000 requests per second.
- Orchestrated container clusters on Kubernetes (Amazon EKS) and automated CI/CD deployment pipelines.
- Distributed incoming HTTP traffic using Nginx reverse proxying and Redis cache layers.
- Led an engineering squad of 5 developers and facilitated bi-weekly sprint retrospectives.

[SKILLS]
Go, Kubernetes, Redis, Microservices, CI/CD, Nginx, AWS, Git
"""

RESUME_ARYAN = """
Aryan Rathore
Email: aryan.rathore@skit.ac.in
Phone: +91 9988776655

[EDUCATION]
B.Tech in Computer Science (Data Science)
SKIT Jaipur, 2024

[EXPERIENCE]
Machine Learning Engineer at MarketIntelligence AI (2022 - Present)
- Trained gradient boosted LightGBM models predicting job market fit and salary compensation ranges.
- Engineered interaction features and cross-validated predictive models using Scikit-learn.
- Authored automated ETL data pipelines in PySpark aggregating millions of live job market records.
- Tracked hyperparameter sweeps and logged model registry artifacts using MLflow.

[SKILLS]
Python, LightGBM, Scikit-learn, PySpark, Machine Learning, MLflow, SQL
"""

DEMO_RESUMES = [
    ("Aishani Billore (Full Stack NLP Developer)", RESUME_AISHANI),
    ("Akshat Agarwal (Backend & Cloud Lead)", RESUME_AKSHAT),
    ("Aryan Rathore (Machine Learning & Data Engineer)", RESUME_ARYAN)
]


def run_demo() -> None:
    print("=" * 80)
    print(" CAREERLENS TWO-LAYER SKILL EXTRACTION DEMO ")
    print("=" * 80)
    print("Initializing TwoLayerSkillExtractor (loading 340+ taxonomy and cached embeddings)...")
    
    t_init_0 = time.perf_counter()
    extractor = TwoLayerSkillExtractor(default_implicit_threshold=0.50)
    t_init_1 = time.perf_counter()
    print(f"Loaded successfully in {(t_init_1 - t_init_0)*1000:.1f} ms.\n")

    # Part 1: Demo on 3 Resumes
    for title, resume_text in DEMO_RESUMES:
        print("-" * 80)
        print(f" CANDIDATE: {title}")
        print("-" * 80)

        t0 = time.perf_counter()
        extracted_skills = extractor.extract_skills(resume_text, implicit_threshold=0.50)
        latency_ms = (time.perf_counter() - t0) * 1000

        explicit_list = [s for s in extracted_skills if s["type"] == "explicit"]
        implicit_list = [s for s in extracted_skills if s["type"] == "implicit"]

        print(f"Total Skills Extracted: {len(extracted_skills)} (Latency: {latency_ms:.1f} ms)")
        print(f"  Explicit: {len(explicit_list)} | Implicit: {len(implicit_list)}\n")

        print("  [LAYER 1: EXPLICIT SKILLS]")
        for s in explicit_list:
            print(f"    - {s['name']:<25} (conf: {s['confidence']:.2f}) | Evidence: {s['evidence'][:65]}...")

        print("\n  [LAYER 2: IMPLICIT SKILLS (Latent capabilities inferred from experience bullets)]")
        for s in implicit_list:
            print(f"    * {s['name']:<25} (conf: {s['confidence']:.2f}) | Inferred from bullet: \"{s['evidence'][:60]}...\"")

        print(f"\n  Shared JSON Contract Sample (Top 3):")
        print(json.dumps(extracted_skills[:3], indent=4))
        print()

    # Part 2: Aliasing Verification
    print("=" * 80)
    print(" ACCEPTANCE TEST 1: ALIASING TO CANONICAL NORMALIZATION ")
    print("=" * 80)
    test_aliases = [
        ("JS", "JavaScript"),
        ("k8s", "Kubernetes"),
        ("py", "Python"),
        ("cpp", "C++"),
        ("scikit learn", "Scikit-learn"),
        ("postgres", "PostgreSQL"),
        ("ts", "TypeScript"),
        ("cicd", "CI/CD"),
        ("tf", "TensorFlow")
    ]
    all_alias_pass = True
    for raw_alias, expected_canonical in test_aliases:
        resolved = extractor.taxonomy.get_canonical(raw_alias)
        matched = (resolved == expected_canonical)
        if not matched:
            all_alias_pass = False
        status = "PASS [OK]" if matched else f"FAIL [got {resolved}]"
        print(f"  '{raw_alias}' -> '{resolved}' (Expected: '{expected_canonical}') : {status}")
    print(f"Aliasing Suite Result: {'PASS' if all_alias_pass else 'FAIL'}\n")

    # Part 3: Ambiguity Disambiguation
    print("=" * 80)
    print(" ACCEPTANCE TEST 2: CONTEXTUAL AMBIGUITY DISAMBIGUATION ")
    print("=" * 80)
    ambiguity_cases = [
        ("Built backend microservices in Go with Docker.", "Go", True, "Tech context with Docker"),
        ("Let us go to the market next week.", "Go", False, "Common action verb"),
        ("Architected Java Spring Boot REST microservices.", "Spring Boot", True, "Java Spring tech stack"),
        ("Graduated from university in Spring 2022.", "Spring", False, "Academic semester date"),
        ("Analyzed data with Python, R, and SQL.", "R", True, "Stats programming list"),
        ("Contact John R. Smith for more information.", "R", False, "Middle initial false positive"),
        ("Proficient in advanced Microsoft Excel spreadsheets.", "Excel", True, "Office spreadsheet tool"),
        ("Consistently excelled in all previous academic coursework.", "Excel", False, "English verb 'excelled'")
    ]
    all_ambiguity_pass = True
    for text, target_skill, should_detect, explanation in ambiguity_cases:
        res = extractor.extract_skills(text, include_implicit=False)
        detected_names = {s["name"] for s in res}
        is_detected = (target_skill in detected_names)
        passed = (is_detected == should_detect)
        if not passed:
            all_ambiguity_pass = False
        outcome = "PASS [OK]" if passed else "FAIL"
        print(f"  Snippet: \"{text}\"")
        print(f"    Target: '{target_skill}' | Detected: {is_detected} | Expected: {should_detect} ({explanation}) : {outcome}\n")
    print(f"Ambiguity Suite Result: {'PASS' if all_ambiguity_pass else 'FAIL'}\n")

    # Part 4: Performance Latency Benchmark (< 2 Seconds Target)
    print("=" * 80)
    print(" ACCEPTANCE TEST 3: LATENCY BENCHMARK (< 2.0 SECONDS TARGET) ")
    print("=" * 80)
    bench_result = extractor.benchmark_latency(RESUME_AISHANI, n_runs=5)
    print(f"  Average Explicit Latency : {bench_result['explicit_ms']} ms")
    print(f"  Average Implicit Latency : {bench_result['implicit_ms']} ms")
    print(f"  Average Total Latency    : {bench_result['total_ms']} ms")
    print(f"  Target (< 2000 ms)       : {bench_result['status']} ({bench_result['total_ms']} ms < 2000 ms)")
    print("=" * 80)


if __name__ == "__main__":
    run_demo()
