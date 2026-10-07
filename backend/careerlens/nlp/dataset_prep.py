import json
import re
import os
from typing import List, Dict, Any, Tuple
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit
from datasets import Dataset, DatasetDict
from transformers import AutoTokenizer

# BIO Label Schema
LABELS = [
    "O",
    "B-NAME", "I-NAME",
    "B-EMAIL", "I-EMAIL",
    "B-PHONE", "I-PHONE",
    "B-DEGREE", "I-DEGREE",
    "B-INSTITUTION", "I-INSTITUTION",
    "B-GRAD_YEAR", "I-GRAD_YEAR",
    "B-JOB_TITLE", "I-JOB_TITLE",
    "B-COMPANY", "I-COMPANY",
    "B-DATE_RANGE", "I-DATE_RANGE",
    "B-SKILL", "I-SKILL"
]

LABEL2ID = {label: i for i, label in enumerate(LABELS)}
ID2LABEL = {i: label for i, label in enumerate(LABELS)}

# Gazetteers for weak labeling bootstrap
SKILL_GAZETTEER = {
    "python", "java", "c++", "javascript", "react", "node.js", "express", "fastapi",
    "postgresql", "mongodb", "docker", "kubernetes", "aws", "git", "machine learning",
    "data science", "nlp", "transformers", "pytorch", "tensorflow", "scikit-learn",
    "lightgbm", "sql", "html", "css", "tailwind", "figma", "rest api", "microservices"
}

DEGREE_GAZETTEER = {
    "b.tech", "b.e.", "b.s.", "bachelor of technology", "bachelor of engineering",
    "m.tech", "m.s.", "master of technology", "ph.d.", "diploma", "bca", "mca"
}

def weak_label_resume(text: str, resume_id: str) -> Dict[str, Any]:
    """
    Generate initial weak labels using gazetteers and regex patterns for bootstrapping.
    Outputs format convertible to Label Studio / Doccano.
    """
    spans = []
    
    # 1. Email pattern
    for match in re.finditer(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text):
        spans.append({"start": match.start(), "end": match.end(), "label": "EMAIL"})

    # 2. Phone pattern
    for match in re.finditer(r'\+?\d{1,4}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}', text):
        if len(match.group(0).strip()) >= 8:
            spans.append({"start": match.start(), "end": match.end(), "label": "PHONE"})

    # 3. Graduation Year pattern
    for match in re.finditer(r'\b(20\d{2}|19\d{2})\b', text):
        spans.append({"start": match.start(), "end": match.end(), "label": "GRAD_YEAR"})

    # 4. Skills gazetteer matching
    lower_text = text.lower()
    for skill in SKILL_GAZETTEER:
        pattern = r'\b' + re.escape(skill) + r'\b'
        for match in re.finditer(pattern, lower_text):
            spans.append({"start": match.start(), "end": match.end(), "label": "SKILL"})

    # 5. Degree gazetteer matching
    for degree in DEGREE_GAZETTEER:
        pattern = r'\b' + re.escape(degree) + r'\b'
        for match in re.finditer(pattern, lower_text):
            spans.append({"start": match.start(), "end": match.end(), "label": "DEGREE"})

    # Sort spans by start index
    spans = sorted(spans, key=lambda x: x["start"])
    
    return {
        "resume_id": resume_id,
        "text": text,
        "label": spans
    }


def convert_spans_to_bio(tokens: List[str], spans: List[Dict[str, Any]], text: str) -> List[str]:
    """
    Convert word-level tokens and character offsets into BIO labels.
    """
    bio_labels = ["O"] * len(tokens)
    
    # Compute character start/end for each token
    token_offsets = []
    idx = 0
    for t in tokens:
        start = text.find(t, idx)
        if start == -1:
            start = idx
        end = start + len(t)
        token_offsets.append((start, end))
        idx = end

    for span in spans:
        s_start, s_end, entity_label = span["start"], span["end"], span["label"]
        is_first = True
        for i, (t_start, t_end) in enumerate(token_offsets):
            # Check overlap
            if t_start >= s_start and t_end <= s_end:
                if is_first:
                    bio_labels[i] = f"B-{entity_label}"
                    is_first = False
                else:
                    bio_labels[i] = f"I-{entity_label}"

    return bio_labels


def align_labels_with_tokens(
    tokens: List[str],
    ner_tags: List[int],
    tokenizer,
    max_length: int = 512
) -> Dict[str, Any]:
    """
    Sub-word token alignment strategy:
    - Label only the FIRST sub-token of a word with its assigned BIO label.
    - Assign -100 to all subsequent sub-tokens and special tokens ([CLS], [SEP], [PAD]).
    Reasoning: PyTorch CrossEntropyLoss ignores index -100, preventing sub-tokenization
    splits from double-counting loss or biasing gradients towards long sub-word tokens.
    """
    tokenized_inputs = tokenizer(
        tokens,
        is_split_into_words=True,
        truncation=True,
        max_length=max_length,
        padding="max_length"
    )

    word_ids = tokenized_inputs.word_ids(batch_index=0)
    previous_word_idx = None
    label_ids = []

    for word_idx in word_ids:
        if word_idx is None:
            # Special tokens ([CLS], [SEP], [PAD]) -> -100
            label_ids.append(-100)
        elif word_idx != previous_word_idx:
            # First sub-token of a word -> keep original BIO tag
            label_ids.append(ner_tags[word_idx])
        else:
            # Subsequent sub-tokens of the same word -> -100
            label_ids.append(-100)
        previous_word_idx = word_idx

    tokenized_inputs["labels"] = label_ids
    return tokenized_inputs


def split_dataset_by_resume(
    records: List[Dict[str, Any]],
    test_size: float = 0.1,
    val_size: float = 0.1,
    random_state: int = 42
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Splits records at the RESUME level (grouped by resume_id) into Train/Val/Test.
    Prevents data leakage where sentences from the same resume leak across splits.
    """
    df = pd.DataFrame(records)
    if "resume_id" not in df.columns:
        df["resume_id"] = [f"res_{i}" for i in range(len(df))]

    gss_test = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
    train_val_idx, test_idx = next(gss_test.split(df, groups=df["resume_id"]))

    train_val_df = df.iloc[train_val_idx]
    test_df = df.iloc[test_idx]

    relative_val_size = val_size / (1.0 - test_size)
    gss_val = GroupShuffleSplit(n_splits=1, test_size=relative_val_size, random_state=random_state)
    train_idx, val_idx = next(gss_val.split(train_val_df, groups=train_val_df["resume_id"]))

    train_df = train_val_df.iloc[train_idx]
    val_df = train_val_df.iloc[val_idx]

    return train_df.to_dict("records"), val_df.to_dict("records"), test_df.to_dict("records")


def prepare_hf_dataset(
    annotated_json_data: List[Dict[str, Any]],
    tokenizer_name: str = "distilbert-base-uncased"
) -> DatasetDict:
    """
    Complete pipeline to convert weak/manual annotated resume data into a Hugging Face DatasetDict.
    """
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
    processed_records = []

    for item in annotated_json_data:
        text = item["text"]
        resume_id = item.get("resume_id", "default_id")
        spans = item.get("label", [])
        tokens = text.split()
        bio_labels = convert_spans_to_bio(tokens, spans, text)
        ner_tags = [LABEL2ID.get(lbl, 0) for lbl in bio_labels]

        aligned = align_labels_with_tokens(tokens, ner_tags, tokenizer)
        aligned["resume_id"] = resume_id
        aligned["tokens"] = tokens
        processed_records.append(aligned)

    train_recs, val_recs, test_recs = split_dataset_by_resume(processed_records)

    def to_hf_ds(recs):
        dict_data = {
            "input_ids": [r["input_ids"] for r in recs],
            "attention_mask": [r["attention_mask"] for r in recs],
            "labels": [r["labels"] for r in recs]
        }
        return Dataset.from_dict(dict_data)

    return DatasetDict({
        "train": to_hf_ds(train_recs),
        "validation": to_hf_ds(val_recs),
        "test": to_hf_ds(test_recs)
    })
