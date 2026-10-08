import sys
import os
import time
import pytest

# Skip the entire module if PyTorch (or its deps) is not installed.
# These tests require the heavy careerlens NLP sub-package which depends on torch.
torch = pytest.importorskip("torch", reason="PyTorch not installed – skipping NER tests")

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from transformers import AutoTokenizer

from run import app
from careerlens.nlp.dataset_prep import (
    LABELS, LABEL2ID, weak_label_resume, convert_spans_to_bio,
    align_labels_with_tokens, split_dataset_by_resume
)
from careerlens.nlp.ner import extract_entities, fallback_regex_extraction
from careerlens.nlp.train_ner import analyze_errors_and_confusion

client = TestClient(app)

SAMPLE_RESUME_1 = """
Aishani Billore
Email: b230395@skit.ac.in
Phone: +91 9876543210

[EDUCATION]
B.Tech in Computer Science (Data Science)
SKIT Jaipur, Graduated 2024

[EXPERIENCE]
Software Engineer Intern at TechCorp (2023 - 2024)
- Developed real-time data pipelines using Python, FastAPI, and PostgreSQL.
- Built NLP entity extraction models using PyTorch and Transformers.

[SKILLS]
Python, React, Node.js, Docker, Microservices, Machine Learning, SQL
"""

SAMPLE_RESUME_2 = """
Akshat Agarwal
Email: akshat.agarwal@example.com
Phone: 9123456789

[EDUCATION]
Bachelor of Engineering
RTU Kota, 2023

[EXPERIENCE]
Backend Tech Lead at Startup Inc (2022 - Present)
- Architected REST APIs using Node.js, Express, and MongoDB.

[SKILLS]
JavaScript, TypeScript, Express, AWS, C++, Git
"""

SAMPLE_RESUME_3 = """
Aryan Rathore
Email: aryan.rathore@ml.io
Phone: +1 555-0199

[EDUCATION]
M.Tech Artificial Intelligence
IIT Bombay, 2022

[EXPERIENCE]
ML Research Engineer at AI Labs (2022 - 2025)
- Trained LightGBM and scikit-learn models for market scoring.

[SKILLS]
LightGBM, Scikit-learn, PyTorch, Transformers, NLP, Python
"""


def test_bio_label_schema():
    assert "B-NAME" in LABELS
    assert "B-SKILL" in LABELS
    assert "B-DEGREE" in LABELS
    assert LABEL2ID["O"] == 0


def test_weak_label_and_spans():
    text = "Contact Aishani at b230395@skit.ac.in or +91 9876543210. Knows Python and React."
    weak = weak_label_resume(text, "res_1")
    assert any(s["label"] == "EMAIL" for s in weak["label"])
    assert any(s["label"] == "SKILL" for s in weak["label"])
    
    tokens = text.split()
    bios = convert_spans_to_bio(tokens, weak["label"], text)
    assert len(bios) == len(tokens)


def test_subword_alignment():
    tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
    tokens = ["Aishani", "knows", "Python"]
    ner_tags = [LABEL2ID["B-NAME"], LABEL2ID["O"], LABEL2ID["B-SKILL"]]
    aligned = align_labels_with_tokens(tokens, ner_tags, tokenizer)
    
    assert len(aligned["labels"]) == 512
    assert aligned["labels"][0] == -100  # [CLS]


def test_resume_level_split():
    records = [
        {"resume_id": f"res_{i}", "text": f"Resume text {i}"} for i in range(20)
    ]
    train, val, test = split_dataset_by_resume(records, test_size=0.1, val_size=0.1)
    
    train_ids = set(r["resume_id"] for r in train)
    val_ids = set(r["resume_id"] for r in val)
    test_ids = set(r["resume_id"] for r in test)

    assert train_ids.isdisjoint(val_ids)
    assert train_ids.isdisjoint(test_ids)
    assert val_ids.isdisjoint(test_ids)


def test_fallback_regex():
    data = fallback_regex_extraction(SAMPLE_RESUME_1)
    assert data["email"] == "b230395@skit.ac.in"
    assert data["phone"] == "+91 9876543210"
    assert any(s["name"] == "Python" for s in data["skills"])


def test_extract_entities_parsed_resume_schema():
    parsed = extract_entities(SAMPLE_RESUME_1, resume_id="test_id_101")
    
    assert parsed["resume_id"] == "test_id_101"
    assert "name" in parsed
    assert "email" in parsed
    assert "education" in parsed
    assert isinstance(parsed["education"], list)
    assert "experience" in parsed
    assert isinstance(parsed["experience"], list)
    assert "skills" in parsed
    assert isinstance(parsed["skills"], list)
    assert "sections" in parsed
    assert "raw_text" in parsed


def test_inference_latency_benchmark():
    start_time = time.time()
    parsed = extract_entities(SAMPLE_RESUME_1)
    elapsed = time.time() - start_time
    print(f"\n[Benchmarking] CPU Inference latency: {elapsed:.4f} seconds")
    assert elapsed < 1.5


def test_error_analysis_template():
    preds = [["B-NAME", "O", "B-SKILL"]]
    refs = [["B-NAME", "O", "I-SKILL"]]
    analysis = analyze_errors_and_confusion(preds, refs)
    assert analysis["total_errors"] == 1


def test_fastapi_nlp_parse_endpoint():
    response = client.post("/nlp/parse", json={"text": SAMPLE_RESUME_1, "resume_id": "req_123"})
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["resume_id"] == "req_123"
    assert json_data["email"] == "b230395@skit.ac.in"
    assert len(json_data["skills"]) >= 7


def test_fastapi_nlp_parse_empty_input():
    response = client.post("/nlp/parse", json={"text": ""})
    assert response.status_code == 400
    json_data = response.json()
    assert json_data["detail"]["error"]["code"] == "INVALID_INPUT"
