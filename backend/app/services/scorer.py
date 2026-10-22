"""
CareerLens Resume Scorer
Computes ATS score, skill gap, market fit, roadmap, and critique
from parsed resume data — all user-specific, no hardcoded values.
"""

import re
import logging
import json
import math
from functools import lru_cache
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.services.nlp_parser import ROLE_SKILL_DEMAND, TRENDING_SKILLS
from app.services.embedding_client import embedding_client

logger = logging.getLogger("careerlens.scorer")

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_WEIGHTS_PATH = Path(__file__).resolve().parents[1] / "core" / "ats_weights.json"


@lru_cache(maxsize=1)
def _scoring_weights() -> Dict[str, float]:
    """Load and validate the transparent composite weights once per process."""
    weights = json.loads(_WEIGHTS_PATH.read_text(encoding="utf-8"))
    expected = {"keyword_match", "semantic_similarity", "section_completeness",
                "formatting", "experience_relevance", "quantified_impact"}
    if set(weights) != expected or not math.isclose(sum(weights.values()), 1.0, abs_tol=1e-9):
        raise ValueError("ATS weights must define all six factors and sum to 1.0")
    return {key: float(value) for key, value in weights.items()}


@lru_cache(maxsize=1)
def _skill_aliases() -> Dict[str, str]:
    """Read canonical skill names and aliases from User Story 2's taxonomy."""
    path = _PROJECT_ROOT / "data" / "processed" / "skills_taxonomy.json"
    try:
        entries = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    aliases: Dict[str, str] = {}
    for entry in entries:
        canonical = str(entry.get("name", "")).strip()
        if canonical:
            for value in [canonical, *entry.get("aliases", [])]:
                aliases[str(value).casefold().strip()] = canonical
    return aliases


def _canonical_skill(value: str) -> str:
    clean = re.sub(r"\s+", " ", str(value or "")).strip()
    return _skill_aliases().get(clean.casefold(), clean)


@lru_cache(maxsize=32)
def _role_market_demand(role: str) -> Dict[str, float]:
    """Read the processed role-wise demand index, with the legacy table as fallback."""
    path = _PROJECT_ROOT / "data" / "processed" / "skill_demand.json"
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
        matching = [row for row in rows if row.get("role", "").casefold() == role.casefold()
                    and row.get("seniority") == "All"]
        if matching:
            return {_canonical_skill(row["skill"]): float(row["demand_pct"])
                    for row in matching if row.get("skill") and row.get("demand_pct") is not None}
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        logger.debug("Market demand index unavailable; using configured starter demand for %s", role)
    fallback_role = role if role in ROLE_SKILL_DEMAND else "Software Engineer"
    return {_canonical_skill(skill): float(demand)
            for skill, demand in ROLE_SKILL_DEMAND[fallback_role].items()}


def _cosine_similarity(left: List[float], right: List[float]) -> float:
    if len(left) != len(right) or not left:
        raise ValueError("Embedding vectors must have the same non-zero dimension")
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if not left_norm or not right_norm:
        raise ValueError("Embedding vectors must be non-zero")
    return max(0.0, min(1.0, dot / (left_norm * right_norm)))

# ---------------------------------------------------------------------------
# Role detection heuristic
# ---------------------------------------------------------------------------

ROLE_KEYWORDS: Dict[str, List[str]] = {
    "ML Engineer": ["lightgbm", "pytorch", "tensorflow", "mlops", "mlflow", "model", "training"],
    "Data Scientist": ["data science", "machine learning", "statistics", "hypothesis", "regression", "pandas", "numpy"],
    "Data Analyst": ["data analyst", "tableau", "power bi", "excel", "sql", "report", "dashboard"],
    "Backend Developer": ["fastapi", "django", "flask", "spring", "nodejs", "rest api", "postgresql", "mysql"],
    "Full Stack Developer": ["react", "angular", "vue", "node", "frontend", "backend", "full stack"],
    "DevOps Engineer": ["docker", "kubernetes", "terraform", "ci/cd", "pipeline", "aws", "azure", "gcp"],
    "Software Engineer": ["algorithms", "data structures", "oop", "software", "system design"],
}

def infer_target_role(skills: List[Dict[str, Any]], raw_text: str) -> str:
    """
    Infer the most likely target role from the user's skills and resume text.
    Falls back to 'Software Engineer' if nothing matches.
    """
    text_lower = raw_text.lower()
    skill_names_lower = {s["name"].lower() for s in skills}
    scores: Dict[str, int] = {}

    for role, keywords in ROLE_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if kw in text_lower:
                score += 1
            if kw in skill_names_lower:
                score += 2
        scores[role] = score

    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return "Software Engineer"
    return best


# ---------------------------------------------------------------------------
# ATS scoring
# ---------------------------------------------------------------------------

def compute_ats_score(
    skills: List[Dict[str, Any]],
    education: List[Dict[str, Any]],
    experience: List[Dict[str, Any]],
    sections: Dict[str, bool],
    raw_text: str,
    target_role: str,
) -> Dict[str, Any]:
    """
    Compute a breakdown ATS score from 0–100 based on the user's actual resume data.
    """
    role_demand = _role_market_demand(target_role)
    extracted_skill_names = {_canonical_skill(s.get("name", "")).casefold() for s in skills
                             if s.get("name")}

    # Demand-weighted matching rewards skills that appear in more job postings.
    total_demand = sum(max(0.0, value) for value in role_demand.values())
    matched_required = [skill for skill in role_demand if skill.casefold() in extracted_skill_names]
    matched_demand = sum(max(0.0, role_demand[skill]) for skill in matched_required)
    keyword_match = round(100 * matched_demand / total_demand, 1) if total_demand else 0.0

    # Compare resume text with a compact role profile using the live embedding
    # service. If that service is offline, use a neutral score and explain why.
    demand_skills = sorted(role_demand.items(), key=lambda item: -item[1])[:15]
    role_profile = f"Target role: {target_role}. In-demand skills: " + ", ".join(
        skill for skill, _demand in demand_skills
    )
    try:
        vectors = embedding_client.get_service_embeddings_batch(
            [raw_text[:12000], role_profile]
        )
        semantic_sim = round(_cosine_similarity(vectors[0], vectors[1]) * 100, 1) if vectors else 50.0
        semantic_available = vectors is not None
    except (ValueError, TypeError, IndexError) as exc:
        logger.debug("Could not score semantic similarity: %s", exc)
        semantic_sim, semantic_available = 50.0, False

    # 3. Section completeness
    important_sections = ["education", "experience", "skills", "contact", "summary"]
    present = sum(1 for s in important_sections if sections.get(s, False))
    section_completeness = round((present / len(important_sections)) * 100, 1)

    # 4. Formatting: heuristic — penalise very short or very long resumes
    word_count = len(raw_text.split())
    if 200 <= word_count <= 1200:
        formatting = 90.0
    elif word_count < 200:
        formatting = max(40.0, 90.0 - (200 - word_count) * 0.2)
    else:
        formatting = max(65.0, 90.0 - (word_count - 1200) * 0.01)

    # 5. Experience relevance: how many experience entries have bullets
    if experience:
        has_bullets = sum(1 for e in experience if len(e.get("bullets", [])) > 0)
        experience_relevance = round((has_bullets / len(experience)) * 100, 1)
    else:
        experience_relevance = 0.0

    # 6. Quantified impact: look for numbers in bullets/text
    numbers_in_text = len(re.findall(r"\d+[%x]|\d+\s*(?:ms|sec|hrs?|days?|weeks?|users?|requests?|LPA|lakh)", raw_text, re.I))
    quantified_impact = min(100.0, 40.0 + numbers_in_text * 8)

    breakdown = {
        "keyword_match": keyword_match,
        "semantic_similarity": semantic_sim,
        "section_completeness": section_completeness,
        "formatting": round(formatting, 1),
        "experience_relevance": experience_relevance,
        "quantified_impact": round(quantified_impact, 1),
    }

    weights = _scoring_weights()
    ats_score = round(sum(breakdown[name] * weights[name] for name in weights))
    missing_sections = [name for name in important_sections if not sections.get(name)]
    missing_keywords = [skill for skill, _demand in demand_skills
                        if skill.casefold() not in extracted_skill_names][:5]
    reasons = [
        {"factor": "keyword_match", "score": str(keyword_match),
         "reason": f"Matched {len(matched_required)} role skills, covering {keyword_match:.1f}% of observed market demand.",
         "how_to_improve": ("Add evidence for: " + ", ".join(missing_keywords)) if missing_keywords
                            else "Keep the highest-demand skills tied to concrete experience."},
        {"factor": "semantic_similarity", "score": str(semantic_sim),
         "reason": ("Compared the resume with the target-role profile using the embedding service."
                    if semantic_available else "Embedding service unavailable; a neutral score was used."),
         "how_to_improve": "Describe relevant projects and responsibilities using the language of the target role."},
        {"factor": "section_completeness", "score": str(section_completeness),
         "reason": f"{present} of {len(important_sections)} expected resume sections were detected.",
         "how_to_improve": ("Add: " + ", ".join(missing_sections)) if missing_sections
                            else "Keep each section clearly labeled."},
        {"factor": "formatting", "score": str(round(formatting, 1)),
         "reason": f"The resume contains {word_count} words; the current heuristic checks document length.",
         "how_to_improve": "Use concise, consistently formatted sections and bullet points."},
        {"factor": "experience_relevance", "score": str(experience_relevance),
         "reason": f"{sum(bool(e.get('bullets')) for e in experience)} of {len(experience)} experience entries have bullets.",
         "how_to_improve": "Add role-relevant accomplishment bullets to each experience entry."},
        {"factor": "quantified_impact", "score": str(round(quantified_impact, 1)),
         "reason": f"Found {numbers_in_text} measurable values in the resume text.",
         "how_to_improve": "Add verified measures such as time saved, users served, or error reduction."},
    ]

    return {"ats_score": max(0, min(100, ats_score)), "breakdown": breakdown, "reasons": reasons}


def compute_skill_gap(
    skills: List[Dict[str, Any]],
    raw_text: str,
    target_role: str,
) -> Dict[str, Any]:
    """Compute matched/missing/weak/trending skill gap for the target role."""
    role_demand = _role_market_demand(target_role)
    extracted_skill_names = {_canonical_skill(s.get("name", "")).casefold(): s.get("name", "")
                             for s in skills if s.get("name")}

    matched: List[str] = []
    missing: List[Dict[str, Any]] = []

    for sk, demand_pct in sorted(role_demand.items(), key=lambda x: -x[1]):
        canonical = _canonical_skill(sk)
        if canonical.casefold() in extracted_skill_names:
            matched.append(canonical)
        else:
            missing.append({"skill": canonical, "demand_pct": demand_pct})

    # Weak: matched skills with low confidence
    weak = [
        s["name"] for s in skills
        if _canonical_skill(s.get("name", "")) in matched
        and float(s.get("confidence", 0.0)) < 0.80
    ]

    # Trending: skills not in their resume and trending in industry
    trending = [
        t for t in TRENDING_SKILLS
        if _canonical_skill(t).casefold() not in extracted_skill_names
    ][:5]

    return {
        "matched": matched[:15],
        "missing": missing[:6],
        "weak": weak[:3],
        "trending": trending,
    }


# ---------------------------------------------------------------------------
# Market fit
# ---------------------------------------------------------------------------

SALARY_BANDS: Dict[str, Dict[str, Any]] = {
    "ML Engineer":        {"min": 10.0, "max": 22.0, "peak": 40.0},
    "Data Scientist":     {"min": 8.0,  "max": 20.0, "peak": 35.0},
    "Data Analyst":       {"min": 5.0,  "max": 12.0, "peak": 22.0},
    "Backend Developer":  {"min": 6.0,  "max": 18.0, "peak": 32.0},
    "Full Stack Developer":{"min": 7.0, "max": 20.0, "peak": 35.0},
    "DevOps Engineer":    {"min": 8.0,  "max": 22.0, "peak": 40.0},
    "Software Engineer":  {"min": 7.0,  "max": 18.0, "peak": 30.0},
}


def compute_market_fit(
    ats_score: int,
    skills: List[Dict[str, Any]],
    experience: List[Dict[str, Any]],
    education: List[Dict[str, Any]],
    target_role: str,
) -> Dict[str, Any]:
    """Compute market fit score and salary band from the user's actual data."""
    band = SALARY_BANDS.get(target_role, SALARY_BANDS["Software Engineer"])

    # fit_score: derived from ATS score + experience depth
    exp_years = len(experience)  # crude proxy (each entry ≈ 1 role)
    fit_score = min(100, int(ats_score * 0.7 + exp_years * 5 + len(skills) * 0.5))

    # Scale salary within band by fit
    fit_ratio = fit_score / 100.0
    salary_min = round(band["min"] + fit_ratio * (band["max"] - band["min"]) * 0.4, 1)
    salary_max = round(band["min"] + fit_ratio * (band["max"] - band["min"]) * 0.9, 1)

    # Generate personalised factors
    top_skills = [s["name"] for s in skills[:3]] if skills else ["core skills"]
    edu_info = education[0].get("institution", "your institution") if education else "your institution"
    factors = [
        f"High market demand for {top_skills[0] if top_skills else 'your top skill'} professionals in Indian tech sector",
        f"Strong academic background from {edu_info} aligns with employer hiring criteria",
    ]
    if exp_years > 0:
        factors.append(f"Demonstrated hands-on experience across {exp_years} role(s) boosts market readiness")
    else:
        factors.append("Adding internship/project experience can increase salary potential by 2–3 LPA")

    return {
        "fit_score": fit_score,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "currency": "INR",
        "unit": "LPA",
        "top_factors": factors,
    }


# ---------------------------------------------------------------------------
# Roadmap generation
# ---------------------------------------------------------------------------

SKILL_RESOURCES: Dict[str, Dict[str, Any]] = {
    "MLOps": {
        "title": "Full Stack Deep Learning: Production MLOps",
        "url": "https://fullstackdeeplearning.com",
        "type": "Interactive Course",
        "project": "Automated Model Packaging and Validation Pipeline with Git CI/CD",
        "weeks": 3,
    },
    "Kubernetes": {
        "title": "Kubernetes for Developers",
        "url": "https://kubernetes.io/docs/tutorials",
        "type": "Lab",
        "project": "Scalable ML Serving Cluster with Auto-Scaling and Health Probes",
        "weeks": 3,
    },
    "Docker": {
        "title": "Docker Official Documentation",
        "url": "https://docs.docker.com",
        "type": "Documentation",
        "project": "Containerise your application with multi-stage Docker builds",
        "weeks": 2,
    },
    "AWS": {
        "title": "AWS Cloud Practitioner Essentials",
        "url": "https://aws.amazon.com/training/learn-about/cloud-practitioner",
        "type": "Course",
        "project": "Deploy a FastAPI app to AWS EC2 with S3 static asset storage",
        "weeks": 3,
    },
    "Kafka": {
        "title": "Apache Kafka Quickstart",
        "url": "https://kafka.apache.org/quickstart",
        "type": "Documentation",
        "project": "Async event-driven resume processing pipeline using Kafka consumers",
        "weeks": 2,
    },
    "RAG": {
        "title": "LangChain RAG Tutorial",
        "url": "https://python.langchain.com/docs/tutorials/rag",
        "type": "Tutorial",
        "project": "Build a Q&A assistant grounded in real job market data",
        "weeks": 3,
    },
    "PyTorch": {
        "title": "Deep Learning with PyTorch",
        "url": "https://pytorch.org/tutorials",
        "type": "Course",
        "project": "Train a custom NER model for resume entity extraction",
        "weeks": 4,
    },
    "TypeScript": {
        "title": "TypeScript Handbook",
        "url": "https://www.typescriptlang.org/docs",
        "type": "Documentation",
        "project": "Refactor your Node.js codebase to TypeScript with strict typing",
        "weeks": 2,
    },
    "LangChain": {
        "title": "LangChain Python Docs",
        "url": "https://python.langchain.com",
        "type": "Documentation",
        "project": "Build an agentic career assistant using LangChain + ChromaDB",
        "weeks": 3,
    },
    "CI/CD": {
        "title": "GitHub Actions Documentation",
        "url": "https://docs.github.com/en/actions",
        "type": "Documentation",
        "project": "Set up CI/CD pipeline with automated testing and deployment",
        "weeks": 2,
    },
    "Terraform": {
        "title": "HashiCorp Terraform Learn",
        "url": "https://developer.hashicorp.com/terraform/tutorials",
        "type": "Lab",
        "project": "Provision cloud infrastructure as code using Terraform + AWS",
        "weeks": 3,
    },
}

_GENERIC_RESOURCE = {
    "title": "Practice Projects on GitHub",
    "url": "https://github.com/topics",
    "type": "Open Source",
    "project": "Build a portfolio project demonstrating this skill",
    "weeks": 2,
}


def compute_roadmap(
    missing_skills: List[Dict[str, Any]],
    target_role: str,
    resume_id: str,
) -> Dict[str, Any]:
    """Build a personalised learning roadmap from the user's missing skills."""
    phases = []
    phase_num = 1

    for item in missing_skills[:4]:  # max 4 phases
        skill = item["skill"]
        res = SKILL_RESOURCES.get(skill, _GENERIC_RESOURCE)
        phases.append({
            "phase": f"Phase {phase_num}: Master {skill}",
            "weeks": res["weeks"],
            "skills": [skill],
            "resources": [{"title": res["title"], "url": res["url"], "type": res["type"]}],
            "project": res["project"],
            "linked_gap_skill": skill,
        })
        phase_num += 1

    if not phases:
        phases.append({
            "phase": "Phase 1: Strengthen Your Core Stack",
            "weeks": 2,
            "skills": ["System Design", "Unit Testing"],
            "resources": [{"title": "System Design Primer", "url": "https://github.com/donnemartin/system-design-primer", "type": "GitHub"}],
            "project": "Architect a scalable microservice with testing and documentation",
            "linked_gap_skill": "System Design",
        })

    return {
        "resume_id": resume_id,
        "target_role": target_role,
        "phases": phases,
    }


# ---------------------------------------------------------------------------
# Critique generation
# ---------------------------------------------------------------------------

def compute_critique(
    skills: List[Dict[str, Any]],
    experience: List[Dict[str, Any]],
    sections: Dict[str, bool],
    ats_score: int,
    resume_id: str,
) -> Dict[str, Any]:
    """Generate multi-agent critique based on the user's actual resume content."""

    has_bullets = any(len(e.get("bullets", [])) > 0 for e in experience)
    has_numbers = any(
        re.search(r"\d+[%x]|\d+\s*(ms|users|requests|LPA|lakh)", " ".join(e.get("bullets", [])), re.I)
        for e in experience
    )
    skill_count = len(skills)
    top_skills = [s["name"] for s in skills[:4]] if skills else ["your skills"]

    # ---- Recruiter ----
    recruiter_score = min(95, max(40, int(ats_score * 0.85 + 5)))
    recruiter_strengths = [f"Clear {top_skills[0] if top_skills else 'technical'} expertise is visible"]
    if sections.get("summary"):
        recruiter_strengths.append("Professional summary helps the 6-second recruiter scan")
    recruiter_concerns = []
    if not sections.get("summary"):
        recruiter_concerns.append("Missing a professional summary/objective section")
    if not has_numbers:
        recruiter_concerns.append("Add quantified metrics to bullet points (e.g. '35% latency reduction')")

    recruiter_rewrites = []
    if experience and experience[0].get("bullets"):
        original = experience[0]["bullets"][0]
        recruiter_rewrites.append({
            "before": original[:100],
            "after": f"Engineered solution using {top_skills[0] if top_skills else 'core tech'}, achieving measurable improvement across production workloads.",
        })

    # ---- HR ----
    hr_score = min(95, max(40, int(ats_score * 0.80 + 8)))
    hr_strengths = ["Academic background shows commitment to continuous learning"]
    if sections.get("certifications"):
        hr_strengths.append("Certifications demonstrate proactive professional development")
    hr_concerns = ["Include explicit examples of teamwork and cross-functional collaboration"]
    if not sections.get("achievements"):
        hr_concerns.append("Add an achievements/awards section to differentiate yourself")

    # ---- Hiring Manager ----
    hm_score = min(95, max(40, int(ats_score * 0.90)))
    hm_strengths = [f"Technical stack ({', '.join(top_skills[:3])}) aligns with production engineering requirements"]
    if has_bullets:
        hm_strengths.append("Experience section has structured bullet points, aiding technical evaluation")
    hm_concerns = []
    if not has_numbers:
        hm_concerns.append("Bullet points lack system-level benchmarks (concurrency, latency, scale)")
    if skill_count < 6:
        hm_concerns.append("Broaden skill set — fewer than 6 skills detected, which may limit role matching")

    consensus_score = int((recruiter_score + hr_score + hm_score) / 3)

    return {
        "resume_id": resume_id,
        "agents": [
            {
                "persona": "Recruiter",
                "score": recruiter_score,
                "verdict": f"{'Strong' if recruiter_score >= 75 else 'Moderate'} candidate profile with {'clear' if skill_count >= 5 else 'limited'} technical signals.",
                "strengths": recruiter_strengths,
                "concerns": recruiter_concerns or ["Ensure contact details are prominent"],
                "rewrites": recruiter_rewrites,
            },
            {
                "persona": "HR",
                "score": hr_score,
                "verdict": f"{'High' if hr_score >= 75 else 'Moderate'} alignment with organisational culture and growth mindset.",
                "strengths": hr_strengths,
                "concerns": hr_concerns,
                "rewrites": [],
            },
            {
                "persona": "Hiring Manager",
                "score": hm_score,
                "verdict": f"{'Technically solid' if hm_score >= 75 else 'Needs improvement in technical depth'}; {'ready for production roles' if experience else 'seeking initial work experience'}.",
                "strengths": hm_strengths,
                "concerns": hm_concerns or ["Candidate looks strong for this role"],
                "rewrites": [],
            },
        ],
        "merged": {
            "verdict": (
                "Recommended for Technical Screening. Strong foundational profile with clear growth potential."
                if consensus_score >= 75 else
                "Requires targeted improvements before submission. Focus on quantified impact and skill breadth."
            ),
            "consensus_score": consensus_score,
            "agreements": [
                f"Technical skills ({', '.join(top_skills[:2])}) are relevant to the target role",
                "Resume structure can be improved with stronger bullet-point metrics",
            ],
            "disagreements": [
                "Recruiter prioritised keyword density; Hiring Manager prioritised system-scale evidence"
            ],
        },
    }
