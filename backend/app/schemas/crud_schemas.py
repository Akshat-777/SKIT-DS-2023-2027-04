from typing import List, Dict, Any, Optional, Generic, TypeVar
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from app.schemas.resume import ParsedResume, ScoreResult, MarketFit, Roadmap, Critique

T = TypeVar("T")

class PaginationMeta(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    meta: PaginationMeta

# User Schemas
class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: str = "user"
    consent_given: bool = True
    retention_days: int = 365

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    consent_given: Optional[bool] = None
    retention_days: Optional[int] = None

class UserResponse(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Resume Schemas
class ResumeCreate(BaseModel):
    file_name: str
    file_type: str
    consent_given: bool = True
    retention_days: int = 365

class ResumeUpdate(BaseModel):
    status: Optional[str] = None
    ocr_used: Optional[bool] = None
    consent_given: Optional[bool] = None
    retention_days: Optional[int] = None

class ResumeResponse(BaseModel):
    id: str
    user_id: str
    file_name: str
    file_type: str
    file_path: str
    status: str
    ocr_used: bool
    consent_given: bool
    retention_days: int
    is_deleted: bool
    uploaded_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Parsed Entities Schemas
class ParsedEntitiesUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    education: Optional[List[Dict[str, Any]]] = None
    experience: Optional[List[Dict[str, Any]]] = None
    skills: Optional[List[Dict[str, Any]]] = None
    sections: Optional[Dict[str, Any]] = None
    raw_text: Optional[str] = None

class ParsedEntitiesResponse(BaseModel):
    id: str
    resume_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    education: Optional[List[Dict[str, Any]]] = None
    experience: Optional[List[Dict[str, Any]]] = None
    skills: Optional[List[Dict[str, Any]]] = None
    sections: Optional[Dict[str, Any]] = None
    raw_text: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Skill Master Schemas
class SkillBase(BaseModel):
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    aliases: Optional[List[str]] = []

class SkillCreate(SkillBase):
    pass

class SkillUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    aliases: Optional[List[str]] = None

class SkillResponse(SkillBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True

# Job Posting Schemas
class JobPostingBase(BaseModel):
    title: str
    company: str
    location: Optional[str] = None
    target_role: str
    skills: List[str] = []
    experience: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    currency: str = "INR"
    unit: str = "LPA"
    description: Optional[str] = None
    source: str = "live_api"

class JobPostingCreate(JobPostingBase):
    posted_at: Optional[datetime] = None

class JobPostingUpdate(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    target_role: Optional[str] = None
    skills: Optional[List[str]] = None
    experience: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    currency: Optional[str] = None
    unit: Optional[str] = None
    description: Optional[str] = None
    posted_at: Optional[datetime] = None

class JobPostingResponse(JobPostingBase):
    id: str
    posted_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True

# Role Taxonomy Schemas
class RoleTaxonomyBase(BaseModel):
    role_name: str
    category: str
    required_skills: List[str] = []
    description: Optional[str] = None

class RoleTaxonomyCreate(RoleTaxonomyBase):
    pass

class RoleTaxonomyResponse(RoleTaxonomyBase):
    id: str

    class Config:
        from_attributes = True

# Skill Demand Schemas
class SkillDemandBase(BaseModel):
    role: str
    skill: str
    demand_pct: float
    month: str

class SkillDemandCreate(SkillDemandBase):
    pass

class SkillDemandResponse(SkillDemandBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True

# Analysis Schemas
class AnalysisCreate(BaseModel):
    resume_id: str
    target_role: str
    ats_score: float
    breakdown: Dict[str, float]
    skill_gap: Dict[str, Any]

class AnalysisResponse(BaseModel):
    id: str
    resume_id: str
    target_role: str
    ats_score: float
    breakdown: Dict[str, float]
    skill_gap: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True

# Audit Log Schemas
class AuditLogResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    action: str
    target_type: str
    target_id: Optional[str] = None
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
