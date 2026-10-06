"""Shared normalized job posting schema used by collection and scoring."""

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class JobPosting:
    job_id: str
    source: str
    title: str
    company: str
    location: str
    remote_flag: bool
    experience_min: float | None
    experience_max: float | None
    salary_min: float | None
    salary_max: float | None
    currency: str
    salary_unit: str
    skills_required: list[str]
    description: str
    posted_at: str | None
    url: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
