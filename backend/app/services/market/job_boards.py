from abc import ABC, abstractmethod
import logging
import httpx
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from app.core.config import settings

logger = logging.getLogger("careerlens.job_boards")

def generate_job_dedup_hash(title: str, company: str, date_str: str) -> str:
    """Generates deterministic deduplication hash from title, company, and date."""
    key = f"{title.strip().lower()}|{company.strip().lower()}|{date_str.strip()}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:32]


class JobBoardClient(ABC):
    """Abstract Base Class for job board API adapters."""

    @abstractmethod
    async def fetch_jobs(
        self,
        role: str,
        location: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Fetches postings for a target role. Returns list of normalized dicts:
        {
            "external_id": str,
            "title": str,
            "company": str,
            "location": str,
            "target_role": str,
            "skills": List[str],
            "experience": str,
            "salary_min": float,
            "salary_max": float,
            "currency": str,
            "unit": str,
            "description": str,
            "posted_at": datetime,
            "source": str,
            "dedup_hash": str
        }
        """
        pass


class MockJobBoardClient(JobBoardClient):
    """
    Mock Job Board Client generating realistic job postings across key tech domains.
    Serves as default offline fallback and robust testing source.
    """
    RAW_TEMPLATES = {
        "Software Engineer": [
            {
                "title": "Senior Software Engineer - Backend",
                "company": "TechCorp Innovations",
                "location": "Bengaluru, India",
                "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "Redis", "REST APIs"],
                "experience": "3-5 years",
                "salary_min": 18.0,
                "salary_max": 28.0,
                "description": "Seeking an experienced Backend Engineer to architect high-throughput microservices using FastAPI, PostgreSQL, and Redis."
            },
            {
                "title": "Software Development Engineer (SDE-II)",
                "company": "FlipKart Cloud Services",
                "location": "Bengaluru, India",
                "skills": ["Java", "Spring Boot", "Kafka", "PostgreSQL", "Kubernetes", "Microservices"],
                "experience": "2-4 years",
                "salary_min": 22.0,
                "salary_max": 34.0,
                "description": "Join our platform team building distributed backend systems for millions of concurrent web users."
            }
        ],
        "Data Scientist": [
            {
                "title": "Data Scientist - Predictive Analytics",
                "company": "DataLens Analytics",
                "location": "Gurugram, India",
                "skills": ["Python", "scikit-learn", "LightGBM", "Pandas", "SQL", "ChromaDB", "NLP"],
                "experience": "2-4 years",
                "salary_min": 16.0,
                "salary_max": 26.0,
                "description": "Build production predictive machine learning models using LightGBM and scikit-learn for market risk & candidate scoring."
            },
            {
                "title": "AI/ML Engineer - NLP & RAG",
                "company": "Cognitive AI Labs",
                "location": "Hyderabad, India",
                "skills": ["Python", "Hugging Face Transformers", "PyTorch", "ChromaDB", "LangChain", "FastAPI"],
                "experience": "1-3 years",
                "salary_min": 15.0,
                "salary_max": 24.0,
                "description": "Implement state-of-the-art vector similarity search and transformer-based Named Entity Recognition (NER) models."
            }
        ],
        "Full Stack Developer": [
            {
                "title": "Full Stack Engineer (React + Node.js / Python)",
                "company": "NextGen Digital Solutions",
                "location": "Pune, India",
                "skills": ["React.js", "Node.js", "TypeScript", "Tailwind CSS", "PostgreSQL", "REST APIs"],
                "experience": "2-5 years",
                "salary_min": 14.0,
                "salary_max": 22.0,
                "description": "Develop modern responsive web dashboards with React.js, Tailwind CSS, and resilient Node/Python backend APIs."
            }
        ],
        "DevOps Engineer": [
            {
                "title": "Cloud & DevOps Infrastructure Engineer",
                "company": "CloudScale Operations",
                "location": "Noida, India",
                "skills": ["Docker", "Kubernetes", "AWS", "Terraform", "CI/CD", "Linux", "Prometheus"],
                "experience": "3-6 years",
                "salary_min": 18.0,
                "salary_max": 30.0,
                "description": "Manage containerized deployments, cloud server infrastructure, and CI/CD automated pipelines."
            }
        ],
        "Data Analyst": [
            {
                "title": "Product Data Analyst",
                "company": "MetricsIQ India",
                "location": "Jaipur, India",
                "skills": ["SQL", "Python", "Tableau", "Power BI", "Statistics", "Excel"],
                "experience": "1-3 years",
                "salary_min": 8.0,
                "salary_max": 14.0,
                "description": "Perform exploratory analysis on customer engagement and market intelligence data using SQL and Python."
            }
        ]
    }

    async def fetch_jobs(
        self,
        role: str,
        location: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        normalized_role = role.strip()
        templates = self.RAW_TEMPLATES.get(normalized_role)
        
        if not templates:
            # Fallback template if exact role match isn't pre-defined
            templates = [
                {
                    "title": f"Specialist - {normalized_role}",
                    "company": "Apex Global Solutions",
                    "location": location or "Remote, India",
                    "skills": ["Python", "SQL", "Git", "Problem Solving", "Cloud Computing"],
                    "experience": "1-3 years",
                    "salary_min": 10.0,
                    "salary_max": 18.0,
                    "description": f"Key technical role in {normalized_role} executing industry-standard software engineering workflows."
                }
            ]

        results = []
        now = datetime.now(timezone.utc)
        for idx, t in enumerate(templates[:limit]):
            ext_id = f"mock_{hashlib.md5((t['title'] + t['company']).encode()).hexdigest()[:10]}"
            posted_date_str = now.strftime("%Y-%m-%d")
            dedup_hash = generate_job_dedup_hash(t["title"], t["company"], posted_date_str)
            
            results.append({
                "external_id": ext_id,
                "title": t["title"],
                "company": t["company"],
                "location": t["location"] if not location else location,
                "target_role": normalized_role,
                "skills": t["skills"],
                "experience": t["experience"],
                "salary_min": t["salary_min"],
                "salary_max": t["salary_max"],
                "currency": "INR",
                "unit": "LPA",
                "description": t["description"],
                "posted_at": now,
                "source": "mock_board",
                "dedup_hash": dedup_hash
            })
        
        logger.info(f"MockJobBoardClient generated {len(results)} postings for role '{role}'")
        return results


class AdzunaJobBoardAdapter(JobBoardClient):
    """
    Adzuna Real Job Board API Adapter.
    Handles rate limits, pagination, HTTP error codes, and field normalization.
    """
    def __init__(self, app_id: Optional[str] = None, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.app_id = app_id or settings.JOB_BOARD_APP_ID
        self.api_key = api_key or settings.JOB_BOARD_API_KEY
        self.base_url = base_url or settings.JOB_BOARD_API_URL

    async def fetch_jobs(
        self,
        role: str,
        location: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        if not self.app_id or not self.api_key:
            logger.info("Adzuna API credentials not configured. Skipping live Adzuna fetch.")
            return []

        url = f"{self.base_url}/{page}"
        params = {
            "app_id": self.app_id,
            "app_key": self.api_key,
            "results_per_page": limit,
            "what": role,
            "content-type": "application/json"
        }
        if location:
            params["where"] = location

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(url, params=params)
                if resp.status_code == 429:
                    logger.warning("Adzuna API Rate limit reached (429).")
                    return []
                elif resp.status_code != 200:
                    logger.warning(f"Adzuna API returned status {resp.status_code}: {resp.text}")
                    return []
                
                data = resp.json()
                raw_results = data.get("results", [])
                postings = []
                now = datetime.now(timezone.utc)

                for item in raw_results:
                    title = item.get("title", "Software Role")
                    company = item.get("company", {}).get("display_name", "Tech Company")
                    loc = item.get("location", {}).get("display_name", location or "India")
                    desc = item.get("description", "")
                    ext_id = str(item.get("id", ""))
                    posted_str = item.get("created", now.strftime("%Y-%m-%d"))
                    dedup_hash = generate_job_dedup_hash(title, company, str(posted_str)[:10])

                    # Basic skill extraction from title/description
                    skills = [s for s in ["Python", "Java", "React", "Node.js", "SQL", "AWS", "Docker", "FastAPI", "C++", "ML"] if s.lower() in desc.lower() or s.lower() in title.lower()]
                    if not skills:
                        skills = ["Software Engineering", "Problem Solving"]

                    sal_min = float(item.get("salary_min", 800000)) / 100000.0  # Convert to LPA
                    sal_max = float(item.get("salary_max", 1800000)) / 100000.0

                    postings.append({
                        "external_id": ext_id or f"adz_{dedup_hash[:8]}",
                        "title": title,
                        "company": company,
                        "location": loc,
                        "target_role": role,
                        "skills": skills,
                        "experience": "2+ years",
                        "salary_min": round(sal_min, 1),
                        "salary_max": round(sal_max, 1),
                        "currency": "INR",
                        "unit": "LPA",
                        "description": desc,
                        "posted_at": now,
                        "source": "adzuna_api",
                        "dedup_hash": dedup_hash
                    })
                
                logger.info(f"AdzunaJobBoardAdapter fetched {len(postings)} real job postings for '{role}'")
                return postings

        except Exception as exc:
            logger.error(f"Error fetching live job postings from Adzuna: {exc}")
            return []


class LinkedInJobBoardAdapter(JobBoardClient):
    """
    LinkedIn Jobs Adapter.
    As specified in system constraints, LinkedIn API access is restricted.
    This adapter is config-driven: skips gracefully when not authorized or disabled.
    """
    def __init__(self):
        self.enabled = settings.LINKEDIN_ENABLED
        self.token = settings.LINKEDIN_ACCESS_TOKEN

    async def fetch_jobs(
        self,
        role: str,
        location: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        if not self.enabled or not self.token:
            logger.info("LinkedIn Job API is disabled or not authorized. Gracefully skipping LinkedIn ingestion.")
            return []

        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            # Placeholder for authenticated LinkedIn endpoint if token is provided
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get("https://api.linkedin.com/v2/jobSearch", headers=headers, params={"keywords": role})
                if resp.status_code != 200:
                    logger.warning(f"LinkedIn API returned status {resp.status_code}, skipping.")
                    return []
                # If authorized response received, parse results...
                return []
        except Exception as ex:
            logger.warning(f"LinkedIn Job ingestion failed gracefully: {ex}")
            return []
