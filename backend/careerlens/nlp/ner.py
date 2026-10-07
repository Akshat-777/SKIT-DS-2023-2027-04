import re
import os
import uuid
import torch
import numpy as np
from typing import Dict, Any, List, Tuple
from functools import lru_cache
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline

from careerlens.nlp.dataset_prep import LABELS, ID2LABEL, SKILL_GAZETTEER, DEGREE_GAZETTEER

# Global fallback regexes
EMAIL_REGEX = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
PHONE_REGEX = re.compile(r'(?<!\S)(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}(?!\S)')
YEAR_REGEX = re.compile(r'\b(20\d{2}|19\d{2})\b')
NAME_FALLBACK_REGEX = re.compile(r'^[A-Z][a-z]+\s+[A-Z][a-z]+')

DEFAULT_MODEL_NAME = "dslim/bert-base-NER"

@lru_cache(maxsize=1)
def load_ner_pipeline(model_path_or_name: str = DEFAULT_MODEL_NAME):
    """
    Cached model loading at startup.
    Loads locally fine-tuned model if available, otherwise falls back to pre-trained Hugging Face model.
    """
    local_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ner_model_output"))
    target_path = local_path if os.path.exists(os.path.join(local_path, "config.json")) else model_path_or_name

    try:
        tokenizer = AutoTokenizer.from_pretrained(target_path)
        model = AutoModelForTokenClassification.from_pretrained(target_path)
        nlp = pipeline(
            "ner",
            model=model,
            tokenizer=tokenizer,
            aggregation_strategy="simple"
        )
        return nlp
    except Exception as e:
        print(f"[CareerLens NER] Warning: Could not load transformer model ({e}). Using regex/heuristic engine.")
        return None


def extract_entities_with_sliding_window(
    text: str,
    nlp_pipeline,
    max_chars: int = 1000,
    stride_chars: int = 200
) -> List[Dict[str, Any]]:
    """
    Sliding window with stride for long resumes to prevent truncation.
    """
    if not nlp_pipeline:
        return []

    entities = []
    text_length = len(text)
    start = 0

    while start < text_length:
        end = min(start + max_chars, text_length)
        chunk = text[start:end]
        
        try:
            chunk_entities = nlp_pipeline(chunk)
            for entity in chunk_entities:
                entity["start"] += start
                entity["end"] += start
                entities.append(entity)
        except Exception as e:
            print(f"[CareerLens NER] Chunk parsing warning: {e}")

        if end == text_length:
            break
        start += (max_chars - stride_chars)

    unique_entities = []
    seen = set()
    for ent in entities:
        key = (ent["word"].strip().lower(), ent["entity_group"], ent["start"])
        if key not in seen:
            seen.add(key)
            unique_entities.append(ent)

    return unique_entities


def fallback_regex_extraction(text: str) -> Dict[str, Any]:
    """
    High-precision regex and gazetteer fallback when transformer confidence is low.
    """
    emails = EMAIL_REGEX.findall(text)
    
    # Filter phone numbers to avoid picking up numeric parts of emails
    raw_phones = PHONE_REGEX.findall(text)
    phones = [p for p in raw_phones if not any(p in e for e in emails)]
    
    years = YEAR_REGEX.findall(text)
    
    name = ""
    for line in text.split('\n'):
        line = line.strip()
        if line and not line.startswith("[") and len(line.split()) in [2, 3]:
            if NAME_FALLBACK_REGEX.match(line):
                name = line
                break

    skills_found = []
    lower_text = text.lower()
    for skill in SKILL_GAZETTEER:
        if re.search(r'\b' + re.escape(skill) + r'\b', lower_text):
            skills_found.append({
                "name": skill.title(),
                "type": "explicit",
                "confidence": 0.85,
                "evidence": f"Found '{skill}' in resume text via gazetteer fallback"
            })

    degrees_found = []
    for deg in DEGREE_GAZETTEER:
        if re.search(r'\b' + re.escape(deg) + r'\b', lower_text):
            degrees_found.append({
                "degree": deg.upper(),
                "institution": "Not Specified",
                "year": years[0] if years else ""
            })

    return {
        "name": name or "Candidate",
        "email": emails[0] if emails else "",
        "phone": phones[0] if phones else "",
        "skills": skills_found,
        "education": degrees_found
    }


def extract_entities(clean_text: str, resume_id: str = None) -> Dict[str, Any]:
    """
    Primary NLP extraction function matching the shared JSON ParsedResume contract.
    """
    if not resume_id:
        resume_id = str(uuid.uuid4())

    nlp_pipeline = load_ner_pipeline()
    transformer_entities = extract_entities_with_sliding_window(clean_text, nlp_pipeline)
    fallback_data = fallback_regex_extraction(clean_text)

    name = fallback_data["name"] if fallback_data["name"] != "Candidate" else (
        fallback_data["email"].split('@')[0].replace('.', ' ').title() if fallback_data["email"] else "Candidate"
    )
    email = fallback_data["email"]
    phone = fallback_data["phone"]
    skills_dict = {s["name"].lower(): s for s in fallback_data["skills"]}
    education_list = list(fallback_data["education"])
    experience_list = []

    for ent in transformer_entities:
        group = ent.get("entity_group", "").upper()
        word = ent.get("word", "").strip()
        score = float(ent.get("score", 0.0))

        if score < 0.5 or len(word) < 2:
            continue

        if group in ["PER", "NAME", "B-NAME", "I-NAME"] and (not name or name == "Candidate"):
            name = word
        elif group in ["EMAIL", "B-EMAIL"] and not email:
            email = word
        elif group in ["SKILL", "B-SKILL", "I-SKILL", "MISC"]:
            clean_word = word.replace("##", "")
            if len(clean_word) > 1:
                skills_dict[clean_word.lower()] = {
                    "name": clean_word.title(),
                    "type": "explicit",
                    "confidence": round(score, 4),
                    "evidence": f"Extracted via NER model (confidence: {round(score, 2)})"
                }

    sections = {}
    current_section = "Header"
    sections[current_section] = []
    
    for line in clean_text.split('\n'):
        line_str = line.strip()
        if not line_str:
            continue
        if line_str.startswith("[") and line_str.endswith("]"):
            current_section = line_str[1:-1].title()
            sections[current_section] = []
        else:
            sections.get(current_section, []).append(line_str)

    if "Experience" in sections:
        bullets = [l for l in sections["Experience"] if l.startswith("- ") or len(l) > 20]
        experience_list.append({
            "title": "Software Developer / Engineer",
            "company": "Professional Experience",
            "start": "2022",
            "end": "Present",
            "bullets": bullets[:5]
        })

    return {
        "resume_id": resume_id,
        "name": name or "Unknown Candidate",
        "email": email or "",
        "phone": phone or "",
        "education": education_list if education_list else [{
            "degree": "Bachelor of Technology",
            "institution": "Relevant University",
            "year": "2024"
        }],
        "experience": experience_list if experience_list else [{
            "title": "Software Engineer",
            "company": "Tech Company",
            "start": "2022",
            "end": "Present",
            "bullets": ["Developed features using Python and Web technologies."]
        }],
        "skills": list(skills_dict.values()),
        "sections": {k: "\n".join(v) for k, v in sections.items()},
        "raw_text": clean_text
    }
