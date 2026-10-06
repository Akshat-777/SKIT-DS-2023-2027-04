"""Job board client interface and mock, Adzuna, JSearch, Remotive adapters."""

import json
import logging
import os
import random
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import quote_plus

import requests

LOG = logging.getLogger(__name__)


class JobBoardClient(ABC):
    """Adapter interface. Each page returns source-native response JSON."""

    source = "unknown"

    @abstractmethod
    def fetch_page(self, role: str, location: str, page: int, per_page: int) -> Any:
        raise NotImplementedError

    @abstractmethod
    def extract_jobs(self, payload: Any) -> list[dict[str, Any]]:
        raise NotImplementedError


class RetryingHTTPClient(JobBoardClient):
    base_url = ""

    def __init__(self, api_key: str | None = None, timeout: float = 15,
                 retries: int = 3, min_interval: float = 0.25):
        self.api_key = api_key
        self.timeout = timeout
        self.retries = retries
        self.min_interval = min_interval
        self._last_request = 0.0
        self.session = requests.Session()

    def request_json(self, url: str, params: dict[str, Any], headers: dict[str, str] | None = None):
        delay = max(0.0, self.min_interval - (time.monotonic() - self._last_request))
        if delay:
            time.sleep(delay)
        for attempt in range(self.retries + 1):
            self._last_request = time.monotonic()
            try:
                response = self.session.get(url, params=params, headers=headers or {}, timeout=self.timeout)
                if response.status_code == 429 or response.status_code >= 500:
                    if attempt < self.retries:
                        wait = float(response.headers.get("Retry-After", min(2 ** attempt, 20)))
                        LOG.warning("%s returned %s; retrying in %.1fs", self.source, response.status_code, wait)
                        time.sleep(wait)
                        continue
                response.raise_for_status()
                response.encoding = response.apparent_encoding or "utf-8"
                return response.json()
            except (requests.RequestException, ValueError) as exc:
                if attempt >= self.retries:
                    raise RuntimeError(f"{self.source} request failed: {exc}") from exc
                wait = min(2 ** attempt + random.random() * 0.25, 20)
                LOG.warning("%s request error; retrying in %.1fs: %s", self.source, wait, exc)
                time.sleep(wait)
        raise RuntimeError(f"{self.source} request failed after retries")


class AdzunaClient(RetryingHTTPClient):
    source = "adzuna"

    def __init__(self, app_id: str | None = None, api_key: str | None = None, country: str = "in", **kwargs):
        super().__init__(api_key or os.getenv("ADZUNA_API_KEY"), **kwargs)
        self.app_id = app_id or os.getenv("ADZUNA_APP_ID")
        self.country = country

    def fetch_page(self, role, location, page, per_page):
        if not self.app_id or not self.api_key:
            raise RuntimeError("Set ADZUNA_APP_ID and ADZUNA_API_KEY to use Adzuna")
        url = f"https://api.adzuna.com/v1/api/jobs/{self.country}/search/{page}"
        return self.request_json(url, {"app_id": self.app_id, "app_key": self.api_key,
                                        "what": role, "where": location, "results_per_page": per_page})

    def extract_jobs(self, payload):
        return payload.get("results", [])


class JSearchClient(RetryingHTTPClient):
    source = "jsearch"

    def __init__(self, api_key: str | None = None, country: str = "in", **kwargs):
        super().__init__(api_key or os.getenv("JSEARCH_API_KEY"), **kwargs)
        self.country = country

    def fetch_page(self, role, location, page, per_page):
        if not self.api_key:
            raise RuntimeError("Set JSEARCH_API_KEY to use JSearch")
        query = f"{role} in {location}"
        return self.request_json("https://jsearch.p.rapidapi.com/search", {
            "query": query, "page": str(page), "num_pages": "1", "country": self.country,
            "date_posted": "all"}, {"X-RapidAPI-Key": self.api_key,
                                      "X-RapidAPI-Host": "jsearch.p.rapidapi.com"})

    def extract_jobs(self, payload):
        return payload.get("data", [])


class RemotiveClient(RetryingHTTPClient):
    source = "remotive"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def fetch_page(self, role, location, page, per_page):
        if page > 1:
            return {"jobs": []}
        return self.request_json("https://remotive.com/api/remote-jobs", {
            "search": role, "limit": per_page})

    def extract_jobs(self, payload):
        return payload.get("jobs", [])


class LinkedInClient(RetryingHTTPClient):
    """Optional compatible proxy adapter; direct LinkedIn access is restricted."""
    source = "linkedin"

    def __init__(self, endpoint: str | None = None, api_key: str | None = None, **kwargs):
        super().__init__(api_key or os.getenv("LINKEDIN_API_KEY"), **kwargs)
        self.endpoint = endpoint or os.getenv("LINKEDIN_JOBS_ENDPOINT")

    def fetch_page(self, role, location, page, per_page):
        if not self.endpoint:
            raise RuntimeError("LinkedIn adapter skipped: configure LINKEDIN_JOBS_ENDPOINT for an authorized provider")
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        return self.request_json(self.endpoint, {"keywords": role, "location": location,
                                                 "page": page, "limit": per_page}, headers)

    def extract_jobs(self, payload):
        if isinstance(payload, list):
            return payload
        return payload.get("jobs", payload.get("data", []))


class MockJobBoardClient(JobBoardClient):
    """Deterministic realistic source that can generate thousands of postings."""
    source = "mock"
    SKILLS = {
        "data scientist": ["Python", "SQL", "Machine Learning", "Pandas", "Scikit-learn", "Statistics", "TensorFlow", "NLP"],
        "ml engineer": ["Python", "PyTorch", "Machine Learning", "Docker", "Kubernetes", "FastAPI", "MLOps", "SQL"],
        "backend developer": ["Python", "Java", "Node.js", "PostgreSQL", "REST API", "Docker", "Redis", "AWS"],
        "frontend developer": ["JavaScript", "React", "TypeScript", "HTML", "CSS", "REST API", "Git", "Next.js"],
        "data analyst": ["SQL", "Excel", "Python", "Power BI", "Tableau", "Statistics", "Pandas", "Data Visualization"],
        "devops engineer": ["Linux", "Docker", "Kubernetes", "AWS", "Terraform", "CI/CD", "Python", "Monitoring"],
    }
    COMPANIES = ["Jaipur Analytics", "Northstar Technologies", "BluePine Systems", "Saffron Labs",
                 "Kiteworks India", "Aster Digital", "Mosaic Cloud", "Horizon Data"]
    LOCATIONS = ["Jaipur, India", "Bengaluru, India", "Pune, India", "Hyderabad, India",
                 "Delhi NCR, India", "Remote, India"]

    def fetch_page(self, role, location, page, per_page):
        seed = f"{role}|{location}|{page}"
        rng = random.Random(seed)
        jobs = []
        skills = self.SKILLS.get(role.lower(), ["Python", "SQL", "Communication", "Problem Solving"])
        for index in range(per_page):
            global_index = (page - 1) * per_page + index
            # Retain recognizable mock employers while ensuring distinct source postings survive
            # the production title+company+location duplicate rule.
            company = f"{rng.choice(self.COMPANIES)} {global_index + 1}"
            loc = location if location.lower() != "all" else rng.choice(self.LOCATIONS)
            selected = rng.sample(skills, k=min(len(skills), rng.randint(3, min(6, len(skills)))))
            exp_min = rng.choice([0, 1, 2, 3, 4, 5])
            exp_max = exp_min + rng.choice([1, 2, 3])
            low = rng.randrange(4, 28)
            desc = (f"We are hiring a {role} with {exp_min}-{exp_max} years of experience. "
                    f"Required skills: {', '.join(selected)}. Build reliable products, collaborate with teams, "
                    "and communicate results. Experience with cloud platforms is a plus.")
            jobs.append({"id": f"mock-{role.lower().replace(' ', '-')}-{location.lower().replace(' ', '-')}-{global_index}",
                         "title": role, "company": company, "location": {"display_name": loc},
                         "description": desc, "salary_min": low * 100000,
                         "salary_max": (low + rng.randrange(3, 12)) * 100000, "currency": "INR",
                         "salary_is_predicted": False, "created": (datetime.now(timezone.utc)-timedelta(days=rng.randrange(0, 45))).isoformat(),
                         "redirect_url": f"https://jobs.example.test/{global_index}",
                         "contract_time": "full_time", "remote": "remote" in loc.lower()})
        return {"results": jobs, "mock_page": page}

    def extract_jobs(self, payload):
        return payload.get("results", [])


def client_from_name(name: str) -> JobBoardClient:
    choices = {"mock": MockJobBoardClient, "adzuna": AdzunaClient,
               "jsearch": JSearchClient, "remotive": RemotiveClient, "linkedin": LinkedInClient}
    if name not in choices:
        raise ValueError(f"Unknown job board {name!r}; choose from {', '.join(choices)}")
    return choices[name]()


def raw_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, default=str)
