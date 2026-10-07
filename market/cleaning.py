"""Normalize source records into the CareerLens job_postings schema."""

import hashlib
import html
import re
import unicodedata
from datetime import datetime, timezone
from typing import Any

from .models import JobPosting

SKILL_TERMS = [
    "Python", "R", "SQL", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Node.js", "React",
    "Next.js", "HTML", "CSS", "FastAPI", "Django", "Flask", "REST API", "GraphQL", "PostgreSQL", "MySQL",
    "MongoDB", "Redis", "Machine Learning", "Deep Learning", "Scikit-learn", "TensorFlow", "PyTorch", "NLP",
    "Computer Vision", "Pandas", "NumPy", "Statistics", "Data Visualization", "Power BI", "Tableau", "Excel",
    "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform", "Linux", "Git", "CI/CD", "MLOps", "Spark",
    "Hadoop", "Airflow", "Kafka", "Communication", "Problem Solving", "Agile", "Monitoring", "Data Analysis",
]
SKILL_PATTERNS = {term: re.compile(r"(?<![\w+#.])" + re.escape(term) + r"(?![\w+#.])", re.I) for term in SKILL_TERMS}


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = html.unescape(str(value))
    text = re.sub(r"<\s*br\s*/?\s*>|</p\s*>|</li\s*>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = unicodedata.normalize("NFKC", text)
    text = text.encode("utf-8", "replace").decode("utf-8", "replace")
    return re.sub(r"\s+", " ", text).strip()


def _get(obj: dict, *keys, default=None):
    for key in keys:
        value = obj.get(key)
        if value is not None and value != "":
            return value
    return default


def _location(raw: Any) -> str:
    if isinstance(raw, dict):
        return clean_text(_get(raw, "display_name", "name", "city", default="Unknown")) or "Unknown"
    return clean_text(raw) or "Unknown"


def extract_experience(description: str) -> tuple[float | None, float | None]:
    patterns = [r"(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)\s*\+?\s*years?\s+(?:of\s+)?experience",
                r"(?:at least|minimum|min\.?|over)\s*(\d+(?:\.\d+)?)\s*\+?\s*years?"]
    match = re.search(patterns[0], description, re.I)
    if match:
        return float(match.group(1)), float(match.group(2))
    match = re.search(patterns[1], description, re.I)
    if match:
        return float(match.group(1)), None
    return None, None


def extract_skills(description: str, explicit: Any = None) -> list[str]:
    found = set()
    if isinstance(explicit, list):
        for item in explicit:
            term = item.get("name") if isinstance(item, dict) else item
            if term:
                found.add(clean_text(term))
    for term, pattern in SKILL_PATTERNS.items():
        if pattern.search(description):
            found.add(term)
    return sorted(found, key=str.casefold)


def _salary(raw: dict, description: str) -> tuple[float | None, float | None, str]:
    low = _get(raw, "salary_min", "salary_min_amount", "min_salary")
    high = _get(raw, "salary_max", "salary_max_amount", "max_salary")
    currency = str(_get(raw, "salary_currency", "currency", default="INR")).upper()
    interval = str(_get(raw, "salary_period", "salary_unit", "interval", default="year")).lower()
    if low is None and high is None:
        match = re.search(r"(?:(?:₹|INR)\s*)?([\d,.]+)\s*(?:-|to)\s*(?:(?:₹|INR)\s*)?([\d,.]+)\s*(lpa|lakhs?|per\s+month|monthly|per\s+year|annually)", description, re.I)
        if match:
            low, high = (float(match.group(1).replace(",", "")), float(match.group(2).replace(",", "")))
            unit_text = (match.group(3) or "").lower()
            if unit_text in ("lpa", "lakh", "lakhs"):
                low, high = low * 100000, high * 100000
                interval = "year"
            elif "month" in unit_text:
                low, high = low * 12, high * 12
                interval = "year"
    try:
        low = float(low) if low is not None else None
        high = float(high) if high is not None else None
    except (TypeError, ValueError):
        return None, None, "INR"
    # All salary outputs are normalized to annual INR LPA; unknown currencies stay uncovered.
    if currency in ("INR", "RS", "₹"):
        if any(unit in interval for unit in ("month", "monthly")):
            multiplier = 12 / 100000
        elif any(unit in interval for unit in ("lpa", "lakh")):
            multiplier = 1
        else:
            # Common boards report annual rupees, while compact feeds may send annual thousands.
            multiplier = (1 / 100000) if (low or 0) >= 10000 or (high or 0) >= 10000 else 1
        if low is not None:
            low *= multiplier
        if high is not None:
            high *= multiplier
        return low, high, "INR"
    return None, None, currency


def normalize_job(raw: dict, source: str, role_hint: str = "") -> JobPosting:
    title = clean_text(_get(raw, "title", "job_title", "position", default=role_hint)) or role_hint or "Unknown"
    company_raw = _get(raw, "company", "employer_name", "company_name", default="Unknown")
    company = clean_text(company_raw.get("display_name", company_raw.get("name", "Unknown")) if isinstance(company_raw, dict) else company_raw) or "Unknown"
    loc = _location(_get(raw, "location", "job_city", "city", default="Unknown"))
    description = clean_text(_get(raw, "description", "job_description", "snippet", default=""))
    remote = bool(_get(raw, "remote", "remote_flag", "job_is_remote", default=False)) or "remote" in loc.lower() or "remote" in title.lower()
    exp_min, exp_max = extract_experience(description)
    sal_min, sal_max, currency = _salary(raw, description)
    skills = extract_skills(description, _get(raw, "skills_required", "skills"))
    source_id = _get(raw, "id", "job_id", "reference")
    identity = f"{title.casefold()}|{company.casefold()}|{loc.casefold()}"
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:20]
    job_id = f"{source}:{source_id}" if source_id else f"{source}:{digest}"
    posted = _get(raw, "created", "posted_at", "date", "job_posted_at_datetime_utc")
    if posted:
        posted = clean_text(posted)
    url = clean_text(_get(raw, "redirect_url", "url", "job_apply_link", default=""))
    return JobPosting(job_id, source, title, company, loc, remote, exp_min, exp_max,
                      sal_min, sal_max, currency, "INR LPA", skills, description, posted, url)


def deduplicate(rows: list[JobPosting]) -> list[JobPosting]:
    kept, seen_ids, seen_identity = [], set(), set()
    for row in rows:
        identity = (row.title.casefold(), row.company.casefold(), row.location.casefold())
        if row.job_id in seen_ids or identity in seen_identity:
            continue
        seen_ids.add(row.job_id)
        seen_identity.add(identity)
        kept.append(row)
    return kept
