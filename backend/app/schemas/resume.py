from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field, EmailStr

# Standard Error Contract
class ErrorDetail(BaseModel):
    code: str
    message: str

class ErrorResponse(BaseModel):
    error: ErrorDetail

# Upload Response & Status Contract
class ResumeUploadResponse(BaseModel):
    resume_id: str
    filename: str
    status: Literal["uploaded", "extracting", "parsing", "scoring", "ready", "failed"]
    message: str

class ResumeStatusResponse(BaseModel):
    resume_id: str
    status: Literal["uploaded", "extracting", "parsing", "scoring", "ready", "failed"]
    updated_at: str

# Shared Contract 1: ParsedResume
class EducationItem(BaseModel):
    degree: str
    institution: str
    year: Optional[int] = None

class ExperienceItem(BaseModel):
    title: str
    company: str
    start: str
    end: str
    bullets: List[str]

class SkillItem(BaseModel):
    name: str
    type: Literal["explicit", "implicit"]
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: str

class ParsedResume(BaseModel):
    resume_id: str
    name: str
    email: str
    education: List[EducationItem]
    experience: List[ExperienceItem]
    skills: List[SkillItem]
    sections: Dict[str, Any]
    raw_text: str

# Shared Contract 2: ScoreResult
class ScoreBreakdown(BaseModel):
    keyword_match: float
    semantic_similarity: float
    section_completeness: float
    formatting: float
    experience_relevance: float
    quantified_impact: float

class MissingSkillItem(BaseModel):
    skill: str
    demand_pct: float

class SkillGap(BaseModel):
    matched: List[str]
    missing: List[MissingSkillItem]
    weak: List[str]
    trending: List[str]

class ScoreResult(BaseModel):
    resume_id: str
    target_role: str
    ats_score: int = Field(ge=0, le=100)
    breakdown: ScoreBreakdown
    skill_gap: SkillGap

# Shared Contract 3: MarketFit
class MarketFit(BaseModel):
    resume_id: str
    fit_score: int = Field(ge=0, le=100)
    salary_min: float
    salary_max: float
    currency: str = "INR"
    unit: str = "LPA"
    top_factors: List[str]

# Shared Contract 4: Roadmap
class ResourceItem(BaseModel):
    title: str
    url: str
    type: str

class RoadmapPhase(BaseModel):
    phase: str
    weeks: int
    skills: List[str]
    resources: List[ResourceItem]
    project: str
    linked_gap_skill: str

class Roadmap(BaseModel):
    resume_id: str
    target_role: str
    phases: List[RoadmapPhase]

# Shared Contract 5: Critique
class RewriteItem(BaseModel):
    before: str
    after: str

class AgentCritique(BaseModel):
    persona: Literal["Recruiter", "HR", "Hiring Manager"]
    score: int = Field(ge=0, le=100)
    verdict: str
    strengths: List[str]
    concerns: List[str]
    rewrites: List[RewriteItem]

class MergedCritique(BaseModel):
    verdict: str
    consensus_score: int = Field(ge=0, le=100)
    agreements: List[str]
    disagreements: List[str]

class Critique(BaseModel):
    resume_id: str
    agents: List[AgentCritique]
    merged: MergedCritique
