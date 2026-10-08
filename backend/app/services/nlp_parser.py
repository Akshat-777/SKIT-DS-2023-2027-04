"""
CareerLens NLP Resume Parser
Extracts structured entities from PDF and DOCX resume files using:
  - pdfplumber for PDF text extraction
  - python-docx for DOCX text extraction
  - Regex + heuristics for NER (name, email, education, experience, skills)

No external API or heavy model required — works fully offline.
"""

import re
import os
import logging
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger("careerlens.nlp_parser")

# ---------------------------------------------------------------------------
# Curated skills taxonomy (explicit keyword matching)
# ---------------------------------------------------------------------------
SKILLS_TAXONOMY = {
    # Languages
    "Python": ["python"],
    "JavaScript": ["javascript", "js"],
    "TypeScript": ["typescript", "ts"],
    "Java": ["java"],
    "C++": ["c++", "cpp"],
    "C": [r"\bc\b"],
    "Go": [r"\bgo\b", "golang"],
    "Rust": ["rust"],
    "SQL": ["sql"],
    "R": [r"\br\b"],
    "Kotlin": ["kotlin"],
    "Swift": ["swift"],
    "Scala": ["scala"],
    "PHP": ["php"],
    "Ruby": ["ruby"],
    "Shell": ["bash", "shell", r"\bzsh\b"],

    # ML / AI
    "Machine Learning": ["machine learning", r"\bml\b"],
    "Deep Learning": ["deep learning", r"\bdl\b"],
    "NLP": [r"\bnlp\b", "natural language processing"],
    "Computer Vision": ["computer vision", r"\bcv\b"],
    "PyTorch": ["pytorch"],
    "TensorFlow": ["tensorflow"],
    "Keras": ["keras"],
    "Scikit-learn": ["scikit-learn", "sklearn"],
    "XGBoost": ["xgboost"],
    "LightGBM": ["lightgbm"],
    "Hugging Face": ["hugging face", "huggingface", "transformers"],
    "LangChain": ["langchain"],
    "spaCy": ["spacy"],
    "NLTK": ["nltk"],
    "OpenAI": ["openai", "gpt"],
    "RAG": [r"\brag\b", "retrieval augmented"],
    "MLOps": ["mlops", "mlflow", "kubeflow"],

    # Data
    "Pandas": ["pandas"],
    "NumPy": ["numpy"],
    "Matplotlib": ["matplotlib"],
    "Seaborn": ["seaborn"],
    "Plotly": ["plotly"],
    "Power BI": ["power bi", "powerbi"],
    "Tableau": ["tableau"],
    "Apache Spark": ["apache spark", "pyspark"],
    "Kafka": ["kafka"],
    "Airflow": ["airflow"],
    "dbt": [r"\bdbt\b"],

    # Backend / APIs
    "FastAPI": ["fastapi"],
    "Django": ["django"],
    "Flask": ["flask"],
    "Node.js": ["node.js", "nodejs"],
    "Express.js": ["express.js", "expressjs", "express"],
    "Spring Boot": ["spring boot", "spring"],
    "REST API": ["rest api", "restful", "rest"],
    "GraphQL": ["graphql"],
    "gRPC": ["grpc"],

    # Frontend
    "React": ["react"],
    "Vue.js": ["vue.js", "vue"],
    "Angular": ["angular"],
    "Next.js": ["next.js", "nextjs"],
    "HTML": ["html"],
    "CSS": [r"\bcss\b"],
    "Tailwind CSS": ["tailwind"],

    # Databases
    "PostgreSQL": ["postgresql", "postgres"],
    "MySQL": ["mysql"],
    "MongoDB": ["mongodb", "mongo"],
    "Redis": ["redis"],
    "SQLite": ["sqlite"],
    "ChromaDB": ["chromadb", "chroma"],
    "Pinecone": ["pinecone"],
    "Elasticsearch": ["elasticsearch"],
    "Cassandra": ["cassandra"],

    # DevOps / Cloud
    "Docker": ["docker"],
    "Kubernetes": ["kubernetes", r"\bk8s\b"],
    "AWS": [r"\baws\b", "amazon web services"],
    "GCP": [r"\bgcp\b", "google cloud"],
    "Azure": ["azure"],
    "CI/CD": ["ci/cd", "github actions", "gitlab ci", "jenkins"],
    "Terraform": ["terraform"],
    "Linux": ["linux", "ubuntu", "debian"],
    "Git": [r"\bgit\b", "github", "gitlab"],

    # General CS
    "Data Structures": ["data structures", r"\bdsa\b"],
    "Algorithms": ["algorithms"],
    "System Design": ["system design"],
    "OOP": ["object oriented", r"\boop\b"],
    "Microservices": ["microservices", "microservice"],
    "Agile": ["agile", "scrum"],
    "Unit Testing": ["unit testing", "pytest", "jest", "junit"],
}

# Role-specific required skills for ATS gap analysis
ROLE_SKILL_DEMAND: Dict[str, Dict[str, float]] = {
    "Data Scientist": {
        "Python": 97, "Machine Learning": 95, "SQL": 90, "Pandas": 88,
        "Scikit-learn": 85, "Deep Learning": 80, "NLP": 75, "PyTorch": 72,
        "TensorFlow": 70, "MLOps": 65, "Docker": 60, "Git": 85, "Tableau": 55,
    },
    "ML Engineer": {
        "Python": 98, "Machine Learning": 97, "PyTorch": 88, "TensorFlow": 85,
        "MLOps": 82, "Docker": 80, "Kubernetes": 75, "FastAPI": 72,
        "SQL": 70, "Git": 90, "Deep Learning": 88, "LightGBM": 65,
    },
    "Data Analyst": {
        "SQL": 97, "Python": 85, "Pandas": 88, "Tableau": 80,
        "Power BI": 78, "Excel": 90, "Matplotlib": 70, "NumPy": 72,
        "Statistics": 85, "Git": 70,
    },
    "Backend Developer": {
        "Python": 90, "Node.js": 85, "REST API": 95, "SQL": 88,
        "Docker": 82, "Git": 92, "PostgreSQL": 80, "MongoDB": 72,
        "Redis": 68, "Kubernetes": 65, "FastAPI": 70, "Django": 65, "Flask": 60,
    },
    "Full Stack Developer": {
        "JavaScript": 95, "React": 90, "Node.js": 88, "REST API": 92,
        "SQL": 80, "Git": 92, "Docker": 75, "TypeScript": 82, "CSS": 85,
        "MongoDB": 70, "PostgreSQL": 68,
    },
    "DevOps Engineer": {
        "Docker": 97, "Kubernetes": 95, "AWS": 90, "CI/CD": 92,
        "Linux": 90, "Terraform": 85, "Git": 95, "Python": 80,
        "Shell": 88, "GCP": 70, "Azure": 68,
    },
    "Software Engineer": {
        "Python": 85, "Java": 80, "Data Structures": 90, "Algorithms": 90,
        "Git": 92, "REST API": 85, "SQL": 80, "Docker": 72,
        "OOP": 88, "System Design": 78, "Unit Testing": 75,
    },
}

# Trending skills (always included in gap regardless of role)
TRENDING_SKILLS = [
    "RAG", "LangChain", "OpenAI", "Hugging Face", "Kubernetes",
    "MLOps", "Apache Spark", "GraphQL", "Kafka", "Terraform",
]

# Section header patterns
SECTION_HEADERS = {
    "education": re.compile(r"\b(education|academic|qualification|degree)\b", re.I),
    "experience": re.compile(r"\b(experience|work history|employment|internship)\b", re.I),
    "skills": re.compile(r"\b(skills|technologies|tech stack|competencies|proficiencies)\b", re.I),
    "projects": re.compile(r"\b(projects?|portfolio|personal projects)\b", re.I),
    "summary": re.compile(r"\b(summary|objective|profile|about)\b", re.I),
    "contact": re.compile(r"\b(contact|address|phone|email)\b", re.I),
    "certifications": re.compile(r"\b(certif|licens|credential)\b", re.I),
    "achievements": re.compile(r"\b(achievement|award|honor|recognition)\b", re.I),
}


# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------

def extract_text_from_pdf(file_path: str) -> str:
    """Extract raw text from a PDF file using pdfplumber."""
    try:
        import pdfplumber
        text_parts = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n".join(text_parts)
    except Exception as e:
        logger.warning(f"pdfplumber failed for {file_path}: {e}. Trying PyMuPDF fallback.")
        return _extract_pdf_pymupdf(file_path)


def _extract_pdf_pymupdf(file_path: str) -> str:
    """Fallback PDF extraction using PyMuPDF (fitz)."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(file_path)
        return "\n".join(page.get_text() for page in doc)
    except Exception as e:
        logger.error(f"PyMuPDF also failed for {file_path}: {e}")
        return ""


def extract_text_from_docx(file_path: str) -> str:
    """Extract raw text from a DOCX file using python-docx."""
    try:
        from docx import Document
        doc = Document(file_path)
        return "\n".join(para.text for para in doc.paragraphs if para.text.strip())
    except Exception as e:
        logger.error(f"python-docx failed for {file_path}: {e}")
        return ""


def extract_text(file_path: str) -> str:
    """Route text extraction based on file extension."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext in (".docx", ".doc"):
        return extract_text_from_docx(file_path)
    else:
        logger.warning(f"Unsupported file extension: {ext}")
        return ""


# ---------------------------------------------------------------------------
# Entity extraction helpers
# ---------------------------------------------------------------------------

def extract_email(text: str) -> Optional[str]:
    """Extract the first valid email address from text."""
    pattern = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
    match = pattern.search(text)
    return match.group(0).lower() if match else None


def extract_phone(text: str) -> Optional[str]:
    """Extract the first phone number from text."""
    pattern = re.compile(r"(\+?\d[\d\s\-().]{7,}\d)")
    match = pattern.search(text)
    return match.group(0).strip() if match else None


def extract_name(text: str) -> str:
    """
    Heuristic name extraction:
    - Look at the first 10 non-empty lines
    - Pick the first line that looks like a proper name (2-4 capitalised words, no digits/special chars)
    """
    name_pattern = re.compile(r"^[A-Z][a-zA-Z'-]+(?:\s+[A-Z][a-zA-Z'-]+){1,3}$")
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()][:15]
    for line in lines:
        # Skip lines that contain common non-name words
        skip_words = {"resume", "curriculum", "vitae", "cv", "portfolio", "profile",
                      "objective", "summary", "contact", "email", "phone", "linkedin",
                      "github", "address", "mobile", "tel", "page"}
        if any(sw in line.lower() for sw in skip_words):
            continue
        if name_pattern.match(line) and len(line) <= 50:
            return line
    # Fallback: try to find "Name: John Doe" pattern
    labeled = re.search(r"(?:name|full name)\s*[:\-]\s*([A-Za-z\s]+)", text, re.I)
    if labeled:
        return labeled.group(1).strip().title()
    return "Candidate"


def extract_skills(text: str) -> List[Dict[str, Any]]:
    """
    Match skills from SKILLS_TAXONOMY against the resume text.
    Returns list of SkillItem-compatible dicts with confidence scores.
    """
    text_lower = text.lower()
    found: List[Dict[str, Any]] = []
    seen: set = set()

    for skill_name, patterns in SKILLS_TAXONOMY.items():
        for pat in patterns:
            try:
                if re.search(pat, text_lower):
                    if skill_name not in seen:
                        seen.add(skill_name)
                        # Higher confidence if mentioned multiple times
                        count = len(re.findall(pat, text_lower))
                        confidence = min(0.99, 0.75 + (count - 1) * 0.05)
                        # Determine explicit vs implicit
                        skill_type = "explicit"
                        # Check if the skill appears in a skills section context
                        skill_section = re.search(
                            r"(skills?|technologies?|tech stack)[^\n]*\n(.*?)(\n\n|\Z)",
                            text, re.I | re.DOTALL
                        )
                        if skill_section and skill_name.lower() not in skill_section.group(0).lower():
                            skill_type = "implicit"
                        found.append({
                            "name": skill_name,
                            "type": skill_type,
                            "confidence": round(confidence, 2),
                            "evidence": f"Found {count} time(s) in resume text",
                        })
                    break
            except re.error:
                continue

    return sorted(found, key=lambda s: s["confidence"], reverse=True)


def extract_education(text: str) -> List[Dict[str, Any]]:
    """
    Extract education entries using keyword + pattern matching.
    Looks for degree keywords followed by institution names and years.
    """
    results = []

    degree_pattern = re.compile(
        r"(B\.?Tech|B\.?E|B\.?Sc|M\.?Tech|M\.?Sc|M\.?B\.?A|Ph\.?D|Bachelor|Master|Diploma|B\.?Com|BCA|MCA)"
        r"[\w\s,.()\-&/]*?"
        r"(?:from|at|,|\n|\|)?\s*"
        r"([A-Z][A-Za-z\s,.()'&\-]{5,60})"
        r"(?:[\s,\-]*(\d{4}[\s\-–]+\d{4}|\d{4}|\(\d{4}\)))?",
        re.I,
    )

    for match in degree_pattern.finditer(text):
        degree = match.group(0).split("\n")[0].strip()
        institution = match.group(2).strip().rstrip(",.")
        year_match = re.search(r"(\d{4})", match.group(0))
        year = int(year_match.group(1)) if year_match else None

        if len(institution) > 5:
            results.append({
                "degree": degree[:120],
                "institution": institution[:120],
                "year": year,
            })
        if len(results) >= 4:
            break

    return results if results else []


def extract_experience(text: str) -> List[Dict[str, Any]]:
    """
    Extract work experience / internship entries.
    Looks for job title + company + date range + bullet points.
    """
    results = []

    # Find the experience section block
    exp_section = re.search(
        r"(experience|work history|employment|internship)[s]?\s*\n(.*?)(?=\n(?:education|skills?|projects?|certif|achievement|\Z))",
        text, re.I | re.DOTALL
    )
    block = exp_section.group(2) if exp_section else text

    # Split into potential entries separated by blank lines or role-like lines
    entries = re.split(r"\n{2,}", block)

    date_pat = re.compile(
        r"(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
        r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
        r"[\s.]*\d{4}",
        re.I
    )

    for entry in entries:
        entry = entry.strip()
        if not entry or len(entry) < 20:
            continue

        lines = [l.strip() for l in entry.splitlines() if l.strip()]
        if not lines:
            continue

        # Need at least a date range to be an experience entry
        if not date_pat.search(entry):
            continue

        title = lines[0] if lines else "Role"
        company = lines[1] if len(lines) > 1 else "Company"

        # Extract date range
        dates = date_pat.findall(entry)
        start_str = dates[0][0].capitalize() + re.search(r"\d{4}", entry).group(0) if dates else "N/A"
        # look for end date
        end_match = re.search(r"(present|current|ongoing|\d{4})\b", entry, re.I)
        end_str = end_match.group(0).capitalize() if end_match else "Present"

        # Extract bullet points
        bullets = [
            re.sub(r"^[\-•*▪▸◦◆➢►\s]+", "", l).strip()
            for l in lines[2:]
            if l.startswith(("-", "•", "*", "▪", "▸", "◦", "◆", "➢", "►")) or re.match(r"^[A-Z]", l)
        ]
        bullets = [b for b in bullets if len(b) > 15][:5]

        results.append({
            "title": title[:80],
            "company": company[:80],
            "start": start_str,
            "end": end_str,
            "bullets": bullets or ["Contributed to team projects and deliverables."],
        })

        if len(results) >= 5:
            break

    return results


def detect_sections(text: str) -> Dict[str, bool]:
    """Detect which resume sections are present."""
    result = {}
    for section, pattern in SECTION_HEADERS.items():
        result[section] = bool(pattern.search(text))
    return result


# ---------------------------------------------------------------------------
# Master parse function
# ---------------------------------------------------------------------------

def parse_resume(file_path: str) -> Dict[str, Any]:
    """
    Full pipeline: extract text -> run all entity extractors.
    Returns a dict matching the ParsedResume schema.
    """
    raw_text = extract_text(file_path)
    if not raw_text.strip():
        logger.warning(f"No text extracted from {file_path}. Returning minimal result.")
        raw_text = ""

    name = extract_name(raw_text)
    email = extract_email(raw_text) or f"{name.lower().replace(' ', '.')}@resume.careerlens.ai"
    skills = extract_skills(raw_text)
    education = extract_education(raw_text)
    experience = extract_experience(raw_text)
    sections = detect_sections(raw_text)

    logger.info(
        f"Parsed resume: name={name!r}, email={email!r}, "
        f"skills={len(skills)}, edu={len(education)}, exp={len(experience)}"
    )

    return {
        "name": name,
        "email": email,
        "education": education,
        "experience": experience,
        "skills": skills,
        "sections": sections,
        "raw_text": raw_text[:4000],  # cap stored raw text
    }
