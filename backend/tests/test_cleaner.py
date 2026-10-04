import pytest
from careerlens.nlp.cleaner import clean_text_pipeline

def test_hyphenation_fix():
    messy = "Experi-\nence in soft-\nware."
    result = clean_text_pipeline(messy)
    assert "Experience in software." in result["clean_text"]

def test_bullet_standardization():
    messy = "• Developed API\n* Wrote tests"
    result = clean_text_pipeline(messy)
    assert "- Developed API\n- Wrote tests" in result["clean_text"]

def test_heading_normalization():
    messy = "PROFESSIONAL EXPERIENCE\n- Dev"
    result = clean_text_pipeline(messy)
    assert "[EXPERIENCE]" in result["clean_text"]
    assert "Experience" in result["sections_detected"]

def test_idempotency():
    messy = "• Jan 2023 - Present\nPROFESSIONAL EXPERIENCE"
    pass1 = clean_text_pipeline(messy)
    pass2 = clean_text_pipeline(pass1["clean_text"])
    assert pass1["clean_text"] == pass2["clean_text"]
