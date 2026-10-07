"""Skill and role taxonomy plus role-wise skill-demand index.

The public ``normalize_skill`` function is safe for other CareerLens modules to import.
Run ``python -m market.build_taxonomy`` to build artifacts from processed job postings.
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

try:
    from rapidfuzz import fuzz, process
except ImportError:  # A clear fallback keeps imports usable before optional deps are installed.
    from difflib import SequenceMatcher

    class _Fuzz:
        @staticmethod
        def WRatio(a: str, b: str) -> float:
            return SequenceMatcher(None, a, b).ratio() * 100

    class _Process:
        @staticmethod
        def extractOne(query, choices, scorer=None, score_cutoff=0):
            results = [(choice, (scorer or _Fuzz.WRatio)(query, choice), index)
                       for index, choice in enumerate(choices)]
            results = [row for row in results if row[1] >= score_cutoff]
            return max(results, key=lambda row: row[1]) if results else None

    fuzz, process = _Fuzz(), _Process()

try:
    from sklearn.cluster import KMeans
    from sklearn.feature_extraction.text import TfidfVectorizer
except ImportError:  # Rules still work if scikit-learn has not yet been installed.
    KMeans = TfidfVectorizer = None


SKILL_TAXONOMY: list[dict[str, Any]] = [
    {"name": "Python", "aliases": ["py", "python3"], "category": "language", "parent": None},
    {"name": "R", "aliases": ["r language", "r programming"], "category": "language", "parent": None},
    {"name": "Java", "aliases": ["java programming"], "category": "language", "parent": None},
    {"name": "JavaScript", "aliases": ["js", "javascript", "ecmascript"], "category": "language", "parent": None},
    {"name": "TypeScript", "aliases": ["ts", "typescript"], "category": "language", "parent": "JavaScript"},
    {"name": "C++", "aliases": ["cpp", "cplusplus"], "category": "language", "parent": None},
    {"name": "C#", "aliases": ["c sharp", "c-sharp"], "category": "language", "parent": None},
    {"name": "Go", "aliases": ["golang"], "category": "language", "parent": None},
    {"name": "SQL", "aliases": ["structured query language"], "category": "language", "parent": None},
    {"name": "HTML", "aliases": ["html5"], "category": "language", "parent": None},
    {"name": "CSS", "aliases": ["css3"], "category": "language", "parent": None},
    {"name": "React", "aliases": ["react.js", "reactjs"], "category": "framework", "parent": "JavaScript"},
    {"name": "Next.js", "aliases": ["nextjs", "next js"], "category": "framework", "parent": "React"},
    {"name": "Node.js", "aliases": ["node", "nodejs"], "category": "framework", "parent": "JavaScript"},
    {"name": "FastAPI", "aliases": ["fast api"], "category": "framework", "parent": "Python"},
    {"name": "Django", "aliases": ["django framework"], "category": "framework", "parent": "Python"},
    {"name": "Flask", "aliases": ["flask framework"], "category": "framework", "parent": "Python"},
    {"name": "PostgreSQL", "aliases": ["postgres", "postgre", "psql"], "category": "database", "parent": "SQL"},
    {"name": "MySQL", "aliases": ["mysql db"], "category": "database", "parent": "SQL"},
    {"name": "MongoDB", "aliases": ["mongo", "mongodb database"], "category": "database", "parent": "NoSQL"},
    {"name": "Redis", "aliases": ["redis cache"], "category": "database", "parent": "NoSQL"},
    {"name": "Machine Learning", "aliases": ["ml", "machine-learning", "machine learning"], "category": "ML/AI", "parent": "Artificial Intelligence"},
    {"name": "Deep Learning", "aliases": ["dl", "deep-learning"], "category": "ML/AI", "parent": "Machine Learning"},
    {"name": "Natural Language Processing", "aliases": ["nlp", "natural language processing"], "category": "ML/AI", "parent": "Machine Learning"},
    {"name": "Computer Vision", "aliases": ["cv", "computer-vision"], "category": "ML/AI", "parent": "Machine Learning"},
    {"name": "Scikit-learn", "aliases": ["sklearn", "scikit learn"], "category": "ML/AI", "parent": "Machine Learning"},
    {"name": "TensorFlow", "aliases": ["tensorflow 2", "tf"], "category": "ML/AI", "parent": "Deep Learning"},
    {"name": "PyTorch", "aliases": ["torch"], "category": "ML/AI", "parent": "Deep Learning"},
    {"name": "Pandas", "aliases": ["pandas library"], "category": "tool", "parent": "Python"},
    {"name": "NumPy", "aliases": ["numpy library"], "category": "tool", "parent": "Python"},
    {"name": "Statistics", "aliases": ["statistical analysis", "applied statistics"], "category": "ML/AI", "parent": "Data Science"},
    {"name": "Data Analysis", "aliases": ["data analytics", "analytics"], "category": "tool", "parent": "Data Science"},
    {"name": "Data Visualization", "aliases": ["data viz", "visualization"], "category": "tool", "parent": "Data Science"},
    {"name": "Power BI", "aliases": ["powerbi", "power bi"], "category": "tool", "parent": "Business Intelligence"},
    {"name": "Tableau", "aliases": ["tableau desktop"], "category": "tool", "parent": "Business Intelligence"},
    {"name": "Excel", "aliases": ["microsoft excel", "ms excel"], "category": "tool", "parent": "Office Tools"},
    {"name": "Apache Spark", "aliases": ["spark", "pyspark"], "category": "tool", "parent": "Data Engineering"},
    {"name": "Hadoop", "aliases": ["apache hadoop"], "category": "tool", "parent": "Data Engineering"},
    {"name": "Apache Airflow", "aliases": ["airflow"], "category": "tool", "parent": "Data Engineering"},
    {"name": "Apache Kafka", "aliases": ["kafka"], "category": "tool", "parent": "Data Engineering"},
    {"name": "AWS", "aliases": ["amazon web services", "amazon aws"], "category": "cloud", "parent": "Cloud Computing"},
    {"name": "Microsoft Azure", "aliases": ["azure", "ms azure"], "category": "cloud", "parent": "Cloud Computing"},
    {"name": "Google Cloud", "aliases": ["gcp", "google cloud platform"], "category": "cloud", "parent": "Cloud Computing"},
    {"name": "Docker", "aliases": ["docker containers", "containerization"], "category": "tool", "parent": "DevOps"},
    {"name": "Kubernetes", "aliases": ["k8s", "kube"], "category": "tool", "parent": "DevOps"},
    {"name": "Terraform", "aliases": ["tf infrastructure", "hashicorp terraform"], "category": "tool", "parent": "Infrastructure as Code"},
    {"name": "Linux", "aliases": ["gnu linux"], "category": "tool", "parent": "Operating Systems"},
    {"name": "Git", "aliases": ["version control", "git scm"], "category": "tool", "parent": "Developer Tools"},
    {"name": "CI/CD", "aliases": ["cicd", "continuous integration", "continuous delivery", "continuous deployment"], "category": "tool", "parent": "DevOps"},
    {"name": "MLOps", "aliases": ["ml ops", "machine learning operations"], "category": "ML/AI", "parent": "Machine Learning"},
    {"name": "REST API", "aliases": ["restful api", "rest apis"], "category": "framework", "parent": "API Development"},
    {"name": "GraphQL", "aliases": ["graphql api"], "category": "framework", "parent": "API Development"},
    {"name": "Communication", "aliases": ["communication skills", "written communication"], "category": "soft skill", "parent": "Interpersonal Skills"},
    {"name": "Problem Solving", "aliases": ["problem-solving", "analytical thinking"], "category": "soft skill", "parent": "Interpersonal Skills"},
    {"name": "Agile", "aliases": ["agile methodology", "scrum"], "category": "tool", "parent": "Software Delivery"},
    {"name": "Monitoring", "aliases": ["observability", "application monitoring"], "category": "tool", "parent": "DevOps"},
]

ROLE_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("Data Scientist", ("data scientist", "data science", "research scientist")),
    ("ML Engineer", ("machine learning engineer", "ml engineer", "ai engineer", "applied scientist", "mlops engineer")),
    ("Data Analyst", ("data analyst", "business intelligence analyst", "bi analyst", "reporting analyst")),
    ("Data Engineer", ("data engineer", "analytics engineer", "etl developer", "big data engineer")),
    ("Backend Developer", ("backend", "back-end", "server-side", "api developer")),
    ("Frontend Developer", ("frontend", "front-end", "ui developer", "web designer developer")),
    ("DevOps Engineer", ("devops", "site reliability", "sre", "platform engineer", "release engineer")),
    ("Cloud Engineer", ("cloud engineer", "cloud architect", "cloud administrator")),
    ("QA Engineer", ("quality assurance", "qa engineer", "test engineer", "software tester", "automation tester")),
    ("Security Engineer", ("security engineer", "cybersecurity", "information security", "application security")),
    ("Business Analyst", ("business analyst", "product analyst", "systems analyst")),
    ("Product Manager", ("product manager", "product owner")),
    ("Software Engineer", ("software engineer", "software developer", "application developer", "full stack", "full-stack")),
]
SENIORITY_RULES = [
    ("Intern", re.compile(r"\b(intern|internship|trainee)\b", re.I)),
    ("Entry", re.compile(r"\b(junior|jr\.?|entry[- ]level|graduate|associate)\b", re.I)),
    ("Senior", re.compile(r"\b(senior|sr\.?)\b", re.I)),
    ("Lead", re.compile(r"\b(lead|principal|staff|architect)\b", re.I)),
    ("Manager", re.compile(r"\b(manager|director|head of)\b", re.I)),
]


def _key(text: str) -> str:
    return re.sub(r"[^a-z0-9+#]+", " ", str(text).casefold()).strip()


_CANONICAL = {item["name"] for item in SKILL_TAXONOMY}
_ALIAS_TO_CANONICAL = {}
for _item in SKILL_TAXONOMY:
    for _alias in [_item["name"], *_item["aliases"]]:
        _ALIAS_TO_CANONICAL[_key(_alias)] = _item["name"]
_FUZZY_CHOICES = sorted(_ALIAS_TO_CANONICAL)


def match_skill(raw: str) -> dict[str, Any]:
    """Return a canonical match and confidence/status for indexing or review."""
    value = re.sub(r"\s+", " ", str(raw or "")).strip()
    if not value:
        return {"raw": value, "canonical": None, "confidence": 0.0, "status": "unmatched"}
    key = _key(value)
    if key in _ALIAS_TO_CANONICAL:
        canonical = _ALIAS_TO_CANONICAL[key]
        return {"raw": value, "canonical": canonical, "confidence": 1.0, "status": "exact"}
    candidate = process.extractOne(key, _FUZZY_CHOICES, scorer=fuzz.WRatio)
    if candidate:
        alias, score = candidate[0], float(candidate[1])
        canonical = _ALIAS_TO_CANONICAL[alias]
        confidence = score / 100
        if confidence >= 0.86:
            return {"raw": value, "canonical": canonical, "confidence": confidence, "status": "fuzzy"}
        if confidence >= 0.68:
            return {"raw": value, "canonical": canonical, "confidence": confidence, "status": "review"}
    return {"raw": value, "canonical": None, "confidence": float(candidate[1]) / 100 if candidate else 0.0,
            "status": "unmatched"}


def normalize_skill(raw: str) -> str:
    """Normalize a skill alias to its canonical label; retain unknown text for review."""
    result = match_skill(raw)
    return result["canonical"] or re.sub(r"\s+", " ", str(raw or "")).strip()


def categorize_skill(canonical: str) -> str | None:
    return next((item["category"] for item in SKILL_TAXONOMY if item["name"] == canonical), None)


def classify_seniority(title: str, experience: Any = None) -> str:
    title = str(title or "")
    for label, pattern in SENIORITY_RULES:
        if pattern.search(title):
            return label
    try:
        years = float(experience)
    except (TypeError, ValueError):
        years = None
    if years is not None:
        if years < 1:
            return "Intern"
        if years < 3:
            return "Entry"
        if years >= 8:
            return "Lead"
        if years >= 5:
            return "Senior"
    return "Mid"


def classify_role_rule(title: str) -> str | None:
    normalized = re.sub(r"[^a-z0-9+#. -]+", " ", str(title or "").casefold())
    # Resolve specialization before generic software-engineering title rules.
    if re.search(r"\b(software|data|platform) engineer\b.*\b(ml|machine learning|ai)\b", normalized):
        return "ML Engineer"
    for role, phrases in ROLE_RULES:
        if any(phrase in normalized for phrase in phrases):
            return role
    return None


def _cluster_unknown_titles(titles: list[str], clusters: int = 4) -> dict[str, str]:
    """Group rule-unmatched titles using TF-IDF and KMeans; gracefully return Other."""
    unique = sorted(set(titles))
    if len(unique) < 3 or TfidfVectorizer is None or KMeans is None:
        return {title: "Other" for title in unique}
    count = min(clusters, len(unique))
    try:
        matrix = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=1).fit_transform(unique)
        labels = KMeans(n_clusters=count, random_state=23, n_init=10).fit_predict(matrix)
        return {title: f"Other / Title Cluster {int(label) + 1}" for title, label in zip(unique, labels)}
    except ValueError:
        return {title: "Other" for title in unique}


def normalize_role(title: str, experience: Any = None, unknown_clusters: dict[str, str] | None = None) -> tuple[str, str]:
    role = classify_role_rule(title)
    if role is None:
        role = (unknown_clusters or {}).get(title, "Other")
    return role, classify_seniority(title, experience)


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item.get("name", "")) if isinstance(item, dict) else str(item) for item in value if item]
    if not value:
        return []
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return [str(item.get("name", "")) if isinstance(item, dict) else str(item) for item in parsed if item]
    except (TypeError, json.JSONDecodeError):
        pass
    return [piece.strip() for piece in re.split(r"[,;|]", str(value)) if piece.strip()]


def _parse_date(value: Any) -> date | None:
    if not value:
        return None
    text = str(value).strip()
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return date.fromisoformat(text[:10])
        except ValueError:
            return None


def _mid_salary(row: dict[str, Any]) -> float | None:
    for low_key, high_key in (("salary_min", "salary_max"), ("salary", "salary")):
        low, high = row.get(low_key), row.get(high_key)
        try:
            low = float(low) if low not in (None, "") else None
            high = float(high) if high not in (None, "") else None
        except (TypeError, ValueError):
            continue
        if low is not None and high is not None:
            return (low + high) / 2
        if low is not None:
            return low
        if high is not None:
            return high
    return None


def _experience(row: dict[str, Any]) -> float | None:
    for key in ("experience_min", "experience"):
        try:
            if row.get(key) not in (None, ""):
                return float(row[key])
        except (TypeError, ValueError):
            continue
    return None


def _normalise_post(row: dict[str, Any]) -> dict[str, Any]:
    title = str(row.get("title") or "Unknown")
    raw_skills = _as_list(row.get("skills_required"))
    skill_matches = [match_skill(skill) for skill in raw_skills]
    skills = sorted({item["canonical"] for item in skill_matches if item["canonical"]}, key=str.casefold)
    return {"job_id": str(row.get("job_id") or ""), "title": title,
            "skills": skills, "matches": skill_matches, "salary": _mid_salary(row),
            "experience": _experience(row), "posted": _parse_date(row.get("posted_at"))}


def build_skill_demand(rows: list[dict[str, Any]], minimum_postings: int = 5,
                       as_of: date | None = None) -> dict[str, Any]:
    """Compute role/seniority demand percentages, co-skills, salary and recent trend."""
    normalized = [_normalise_post(row) for row in rows]
    unmatched_counts: Counter[str] = Counter()
    review_counts: Counter[tuple[str, str, str | None, float]] = Counter()
    for post in normalized:
        for match in post["matches"]:
            if match["status"] in ("unmatched", "review"):
                review_counts[(match["raw"], match["status"], match["canonical"], round(match["confidence"], 4))] += 1
            if match["status"] == "unmatched":
                unmatched_counts[match["raw"]] += 1

    unmatched_titles = [post["title"] for post in normalized if classify_role_rule(post["title"]) is None]
    title_clusters = _cluster_unknown_titles(unmatched_titles)
    for post in normalized:
        post["role"], post["seniority"] = normalize_role(post["title"], post["experience"], title_clusters)

    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    role_grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for post in normalized:
        grouped[(post["role"], post["seniority"])].append(post)
        role_grouped[post["role"]].append(post)

    today = as_of or datetime.now(timezone.utc).date()
    recent_start = today - timedelta(days=30)
    previous_start = today - timedelta(days=60)
    output = []
    metric_groups = [(role, seniority, group) for (role, seniority), group in grouped.items()]
    metric_groups.extend((role, "All", group) for role, group in role_grouped.items())
    for role, seniority, group in sorted(metric_groups, key=lambda item: (item[0], item[1])):
        total = len(group)
        counts = Counter(skill for post in group for skill in set(post["skills"]))
        salary_for = defaultdict(list)
        for post in group:
            if post["salary"] is not None:
                for skill in set(post["skills"]):
                    salary_for[skill].append(post["salary"])
        ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0].casefold()))
        previous_count = None
        rank = 0
        for position, (skill, count) in enumerate(ranked, start=1):
            if count != previous_count:
                rank = position
                previous_count = count
            recent_posts = [p for p in group if p["posted"] and recent_start <= p["posted"] <= today]
            previous_posts = [p for p in group if p["posted"] and previous_start <= p["posted"] < recent_start]
            recent_total = len(recent_posts)
            previous_total = len(previous_posts)
            recent_n = sum(skill in p["skills"] for p in recent_posts)
            previous_n = sum(skill in p["skills"] for p in previous_posts)
            recent_pct = 100 * recent_n / recent_total if recent_total else None
            previous_pct = 100 * previous_n / previous_total if previous_total else None
            if recent_pct is None or previous_pct is None:
                trend = "stable"
            elif recent_pct - previous_pct >= 5:
                trend = "rising"
            elif recent_pct - previous_pct <= -5:
                trend = "falling"
            else:
                trend = "stable"
            co = Counter(other for post in group if skill in post["skills"]
                         for other in set(post["skills"]) if other != skill)
            salaries = salary_for[skill]
            output.append({"role": role, "seniority": seniority, "skill": skill,
                           "category": categorize_skill(skill), "posting_count": count,
                           "total_postings": total, "demand_pct": round(100 * count / total, 2),
                           "rank": rank, "co_occurring_skills": [name for name, _ in co.most_common(5)],
                           "average_salary_lpa": round(sum(salaries) / len(salaries), 2) if salaries else None,
                           "trend": trend, "recent_demand_pct": round(recent_pct, 2) if recent_pct is not None else None,
                           "previous_demand_pct": round(previous_pct, 2) if previous_pct is not None else None,
                           "low_sample": total < minimum_postings, "minimum_postings": minimum_postings})
    roles = [{"role": role, "seniority": seniority, "posting_count": len(group),
              "low_sample": len(group) < minimum_postings}
             for (role, seniority), group in sorted(grouped.items())]
    roles.extend({"role": role, "seniority": "All", "posting_count": len(group),
                  "low_sample": len(group) < minimum_postings}
                 for role, group in sorted(role_grouped.items()))
    title_mapping = [{"title": post["title"], "role": post["role"], "seniority": post["seniority"],
                     "job_id": post["job_id"]} for post in normalized]
    return {"roles": roles, "skill_demand": output, "title_mapping": title_mapping,
            "review_matches": [{"raw": raw, "status": status, "suggested_canonical": canonical,
                                "confidence": confidence, "count": count}
                               for (raw, status, canonical, confidence), count in sorted(review_counts.items())],
            "unmatched_skills": dict(unmatched_counts), "posting_count": len(rows),
            "minimum_postings": minimum_postings, "as_of": today.isoformat()}


def validate_index(index: dict[str, Any]) -> list[str]:
    errors = []
    for item in index["skill_demand"]:
        if not 0 <= item["demand_pct"] <= 100:
            errors.append(f"Invalid demand_pct for {item['role']}/{item['skill']}: {item['demand_pct']}")
    top_unmapped = sorted(index["unmatched_skills"].items(), key=lambda item: -item[1])[:100]
    if top_unmapped:
        errors.append("Unmapped top-100 input skills require review: " + ", ".join(name for name, _ in top_unmapped))
    return errors


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8-sig")
        return
    with path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else value
                             for key, value in row.items()})


def export_taxonomy(output_dir: Path, index: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "skills_taxonomy.json").write_text(json.dumps(SKILL_TAXONOMY, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_csv(output_dir / "skills_taxonomy.csv", SKILL_TAXONOMY)
    (output_dir / "roles.json").write_text(json.dumps(index["roles"], ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "skill_demand.json").write_text(json.dumps(index["skill_demand"], ensure_ascii=False, indent=2), encoding="utf-8")
    _write_csv(output_dir / "role_taxonomy.csv", index["roles"])
    _write_csv(output_dir / "skill_demand.csv", index["skill_demand"])
    _write_csv(output_dir / "title_role_mapping.csv", index["title_mapping"])
    _write_csv(output_dir / "uncertain_skill_matches.csv", index["review_matches"])
    (output_dir / "unmapped_skills.json").write_text(json.dumps(index["unmatched_skills"], ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "taxonomy_validation.json").write_text(json.dumps({"valid": not validate_index(index),
        "errors": validate_index(index), "posting_count": index["posting_count"]}, indent=2), encoding="utf-8")
    _write_role_charts(output_dir, index["skill_demand"])


def _write_role_charts(output_dir: Path, demand: list[dict[str, Any]]) -> None:
    grouped = defaultdict(list)
    for row in demand:
        grouped[(row["role"], row["seniority"])].append(row)
    chart_dir = output_dir / "role_charts"
    chart_dir.mkdir(exist_ok=True)
    for (role, seniority), rows in grouped.items():
        safe = re.sub(r"[^a-z0-9]+", "_", f"{role}_{seniority}".casefold()).strip("_")
        top = sorted(rows, key=lambda row: row["rank"])[:15]
        width, label_w, bar_w, row_h = 850, 230, 500, 26
        height = 70 + row_h * len(top)
        parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
                 '<rect width="100%" height="100%" fill="white"/>',
                 f'<text x="16" y="30" font-family="Arial" font-size="20">{role} ({seniority}) — skill demand %</text>']
        for i, item in enumerate(top):
            y = 50 + i * row_h
            bar = int(bar_w * item["demand_pct"] / 100)
            label = item["skill"].replace("&", "&amp;").replace("<", "&lt;")
            parts += [f'<text x="16" y="{y+17}" font-family="Arial" font-size="13">{label}</text>',
                      f'<rect x="{label_w}" y="{y+3}" width="{bar}" height="16" fill="#4776c5"/>',
                      f'<text x="{label_w+bar+6}" y="{y+16}" font-family="Arial" font-size="12">{item["demand_pct"]}%</text>']
        parts.append("</svg>")
        (chart_dir / f"{safe}.svg").write_text("\n".join(parts), encoding="utf-8")
