from sqlalchemy import (
    Column, String, Boolean, Integer, Float, Text, DateTime, ForeignKey, Index, UniqueConstraint, JSON
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.database import Base
import uuid

def generate_id(prefix: str = "") -> str:
    val = str(uuid.uuid4()).replace("-", "")[:12]
    return f"{prefix}_{val}" if prefix else val

def utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True, default=lambda: generate_id("usr"))
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="user")
    consent_given = Column(Boolean, nullable=False, default=True)
    retention_days = Column(Integer, nullable=False, default=365)
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(String(64), primary_key=True, default=lambda: generate_id("res"))
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    file_path = Column(String(512), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, default="uploaded")
    ocr_used = Column(Boolean, nullable=False, default=False)
    consent_given = Column(Boolean, nullable=False, default=True)
    retention_days = Column(Integer, nullable=False, default=365)
    is_deleted = Column(Boolean, nullable=False, default=False, index=True)
    soft_deleted_at = Column(DateTime, nullable=True)
    uploaded_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="resumes")
    parsed_entities = relationship("ParsedEntities", back_populates="resume", uselist=False, cascade="all, delete-orphan")
    resume_skills = relationship("ResumeSkill", back_populates="resume", cascade="all, delete-orphan")
    analyses = relationship("Analysis", back_populates="resume", cascade="all, delete-orphan")
    market_fit = relationship("MarketFit", back_populates="resume", cascade="all, delete-orphan")
    roadmaps = relationship("Roadmap", back_populates="resume", cascade="all, delete-orphan")
    critiques = relationship("Critique", back_populates="resume", cascade="all, delete-orphan")


class ParsedEntities(Base):
    __tablename__ = "parsed_entities"

    id = Column(String(64), primary_key=True, default=lambda: generate_id("pe"))
    resume_id = Column(String(64), ForeignKey("resumes.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    education = Column(JSON, nullable=True)
    experience = Column(JSON, nullable=True)
    skills = Column(JSON, nullable=True)
    sections = Column(JSON, nullable=True)
    raw_text = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)

    resume = relationship("Resume", back_populates="parsed_entities")


class Skill(Base):
    __tablename__ = "skills"

    id = Column(String(64), primary_key=True, default=lambda: generate_id("skl"))
    name = Column(String(255), unique=True, index=True, nullable=False)
    category = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    aliases = Column(JSON, nullable=True, default=list)
    created_at = Column(DateTime, nullable=False, default=utc_now)


class ResumeSkill(Base):
    __tablename__ = "resume_skills"

    id = Column(String(64), primary_key=True, default=lambda: generate_id("rsk"))
    resume_id = Column(String(64), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id = Column(String(64), ForeignKey("skills.id", ondelete="SET NULL"), nullable=True, index=True)
    skill_name = Column(String(255), nullable=False, index=True)
    type = Column(String(50), nullable=False, default="explicit")  # explicit / implicit
    confidence = Column(Float, nullable=False, default=1.0)
    evidence = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)

    resume = relationship("Resume", back_populates="resume_skills")


class JobPosting(Base):
    __tablename__ = "job_postings"

    id = Column(String(64), primary_key=True, default=lambda: generate_id("job"))
    title = Column(String(255), nullable=False, index=True)
    company = Column(String(255), nullable=False, index=True)
    location = Column(String(255), nullable=True)
    target_role = Column(String(255), nullable=False, index=True)
    skills = Column(JSON, nullable=False, default=list)
    experience = Column(String(100), nullable=True)
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    currency = Column(String(10), nullable=False, default="INR")
    unit = Column(String(20), nullable=False, default="LPA")
    description = Column(Text, nullable=True)
    posted_at = Column(DateTime, nullable=False, default=utc_now, index=True)
    source = Column(String(50), nullable=False, default="live_api")
    external_id = Column(String(255), nullable=True, index=True)
    dedup_hash = Column(String(64), nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)


class RoleTaxonomy(Base):
    __tablename__ = "role_taxonomy"

    id = Column(String(64), primary_key=True, default=lambda: generate_id("rt"))
    role_name = Column(String(255), unique=True, index=True, nullable=False)
    category = Column(String(100), nullable=False)
    required_skills = Column(JSON, nullable=False, default=list)
    description = Column(Text, nullable=True)


class SkillDemand(Base):
    __tablename__ = "skill_demand"

    id = Column(String(64), primary_key=True, default=lambda: generate_id("sd"))
    role = Column(String(255), nullable=False, index=True)
    skill = Column(String(255), nullable=False, index=True)
    demand_pct = Column(Float, nullable=False)
    month = Column(String(20), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)

    __table_args__ = (
        UniqueConstraint("role", "skill", "month", name="uix_skill_demand_role_skill_month"),
    )


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(String(64), primary_key=True, default=lambda: generate_id("ans"))
    resume_id = Column(String(64), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    target_role = Column(String(255), nullable=False, index=True)
    ats_score = Column(Float, nullable=False)
    breakdown = Column(JSON, nullable=False)
    skill_gap = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, default=utc_now)

    resume = relationship("Resume", back_populates="analyses")


class MarketFit(Base):
    __tablename__ = "market_fit"

    id = Column(String(64), primary_key=True, default=lambda: generate_id("mf"))
    resume_id = Column(String(64), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    fit_score = Column(Float, nullable=False)
    salary_min = Column(Float, nullable=False)
    salary_max = Column(Float, nullable=False)
    currency = Column(String(10), nullable=False, default="INR")
    unit = Column(String(20), nullable=False, default="LPA")
    top_factors = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, nullable=False, default=utc_now)

    resume = relationship("Resume", back_populates="market_fit")


class Roadmap(Base):
    __tablename__ = "roadmaps"

    id = Column(String(64), primary_key=True, default=lambda: generate_id("rd"))
    resume_id = Column(String(64), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    target_role = Column(String(255), nullable=False)
    phases = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, nullable=False, default=utc_now)

    resume = relationship("Resume", back_populates="roadmaps")


class Critique(Base):
    __tablename__ = "critiques"

    id = Column(String(64), primary_key=True, default=lambda: generate_id("crt"))
    resume_id = Column(String(64), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    agents = Column(JSON, nullable=False, default=list)
    merged = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, default=utc_now)

    resume = relationship("Resume", back_populates="critiques")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(64), primary_key=True, default=lambda: generate_id("aud"))
    user_id = Column(String(64), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False)
    target_type = Column(String(100), nullable=False)
    target_id = Column(String(64), nullable=True)
    timestamp = Column(DateTime, nullable=False, default=utc_now, index=True)
    details = Column(JSON, nullable=True)

    user = relationship("User", back_populates="audit_logs")
