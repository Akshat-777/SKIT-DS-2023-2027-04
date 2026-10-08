"""
CareerLens Resume Scorer
Computes ATS score, skill gap, market fit, roadmap, and critique
from parsed resume data — all user-specific, no hardcoded values.
"""

import re
import logging
from typing import List, Dict, Any, Optional

from app.services.nlp_parser import ROLE_SKILL_DEMAND, TRENDING_SKILLS

logger = logging.getLogger("careerlens.scorer")

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
    role_demand = ROLE_SKILL_DEMAND.get(target_role, ROLE_SKILL_DEMAND["Software Engineer"])
    extracted_skill_names = {s["name"].lower() for s in skills}

    # 1. Keyword match: what % of high-demand skills appear
    matched_required = [
        sk for sk in role_demand
        if sk.lower() in extracted_skill_names
    ]
    keyword_match = round(min(100.0, (len(matched_required) / max(len(role_demand), 1)) * 100), 1)

    # 2. Semantic similarity proxy: avg skill confidence of matched skills
    matched_confidences = [
        s["confidence"] for s in skills if s["name"] in matched_required
    ]
    semantic_sim = round(
        (sum(matched_confidences) / max(len(matched_confidences), 1)) * 100,
        1
    ) if matched_confidences else 50.0

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

    # Weighted composite ATS score
    ats_score = round(
        keyword_match * 0.30
        + semantic_sim * 0.20
        + section_completeness * 0.15
        + formatting * 0.10
        + experience_relevance * 0.15
        + quantified_impact * 0.10
    )

    return {"ats_score": max(1, min(100, ats_score)), "breakdown": breakdown}


def compute_skill_gap(
    skills: List[Dict[str, Any]],
    raw_text: str,
    target_role: str,
) -> Dict[str, Any]:
    """Compute matched/missing/weak/trending skill gap for the target role."""
    role_demand = ROLE_SKILL_DEMAND.get(target_role, ROLE_SKILL_DEMAND["Software Engineer"])
    extracted_skill_names = {s["name"].lower(): s["name"] for s in skills}

    matched: List[str] = []
    missing: List[Dict[str, Any]] = []

    for sk, demand_pct in sorted(role_demand.items(), key=lambda x: -x[1]):
        if sk.lower() in extracted_skill_names:
            matched.append(sk)
        else:
            missing.append({"skill": sk, "demand_pct": demand_pct})

    # Weak: matched skills with low confidence
    weak = [
        s["name"] for s in skills
        if s["name"] in matched and s["confidence"] < 0.80
    ]

    # Trending: skills not in their resume and trending in industry
    trending = [
        t for t in TRENDING_SKILLS
        if t.lower() not in extracted_skill_names
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
