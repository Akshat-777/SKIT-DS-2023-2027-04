import os
import logging
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_, and_, desc, asc
from datetime import datetime, timezone

from app.models.models import (
    User, Resume, ParsedEntities, Skill, ResumeSkill, JobPosting,
    RoleTaxonomy, SkillDemand, Analysis, MarketFit, Roadmap, Critique, AuditLog,
    generate_id, utc_now
)
from app.core.security_privacy import encrypt_pii, decrypt_pii

logger = logging.getLogger("careerlens.repositories")

def create_audit_log(db: Session, user_id: Optional[str], action: str, target_type: str, target_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> AuditLog:
    """Creates an immutable audit log entry for privacy & compliance tracking."""
    log_entry = AuditLog(
        id=generate_id("aud"),
        user_id=user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        timestamp=utc_now(),
        details=details or {}
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry


class UserRepository:
    @staticmethod
    def get_by_id(db: Session, user_id: str) -> Optional[User]:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.email = decrypt_pii(user.email)
        return user

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        normalized_email = email.strip().lower()
        # Search decrypted matching or plain email
        users = db.query(User).all()
        for u in users:
            decrypted = decrypt_pii(u.email)
            if decrypted.lower() == normalized_email:
                u.email = decrypted
                return u
        return None

    @staticmethod
    def create(db: Session, name: str, email: str, password_hash: str, role: str = "user", consent_given: bool = True, retention_days: int = 365, user_id: Optional[str] = None) -> User:
        normalized_email = email.strip().lower()
        encrypted_email = encrypt_pii(normalized_email)
        uid = user_id or generate_id("usr")
        user = User(
            id=uid,
            name=name,
            email=encrypted_email,
            password_hash=password_hash,
            role=role,
            consent_given=consent_given,
            retention_days=retention_days,
            created_at=utc_now(),
            updated_at=utc_now()
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        user.email = normalized_email
        create_audit_log(db, user.id, "USER_REGISTER", "USER", user.id, {"email": normalized_email})
        return user


    @staticmethod
    def update(db: Session, user_id: str, data: Dict[str, Any]) -> Optional[User]:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        if "email" in data and data["email"]:
            data["email"] = encrypt_pii(data["email"].strip().lower())
        for key, value in data.items():
            if value is not None and hasattr(user, key):
                setattr(user, key, value)
        user.updated_at = utc_now()
        db.commit()
        db.refresh(user)
        user.email = decrypt_pii(user.email)
        return user

    @staticmethod
    def list_users(db: Session, page: int = 1, page_size: int = 20) -> Tuple[List[User], int]:
        total = db.query(User).count()
        users = db.query(User).offset((page - 1) * page_size).limit(page_size).all()
        for u in users:
            u.email = decrypt_pii(u.email)
        return users, total


class ResumeRepository:
    @staticmethod
    def create(db: Session, user_id: str, file_name: str, file_type: str, file_path: str, consent_given: bool = True, retention_days: int = 365) -> Resume:
        resume = Resume(
            id=generate_id("res"),
            user_id=user_id,
            file_name=file_name,
            file_type=file_type,
            file_path=file_path,
            status="uploaded",
            ocr_used=False,
            consent_given=consent_given,
            retention_days=retention_days,
            is_deleted=False,
            uploaded_at=utc_now(),
            updated_at=utc_now()
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)
        create_audit_log(db, user_id, "RESUME_UPLOAD", "RESUME", resume.id, {"file_name": file_name})
        return resume

    @staticmethod
    def get_by_id(db: Session, resume_id: str, include_deleted: bool = False) -> Optional[Resume]:
        query = db.query(Resume).filter(Resume.id == resume_id)
        if not include_deleted:
            query = query.filter(Resume.is_deleted == False)
        return query.first()

    @staticmethod
    def list_user_resumes(db: Session, user_id: str, page: int = 1, page_size: int = 20, status: Optional[str] = None) -> Tuple[List[Resume], int]:
        query = db.query(Resume).filter(Resume.user_id == user_id, Resume.is_deleted == False)
        if status:
            query = query.filter(Resume.status == status)
        total = query.count()
        resumes = query.order_by(desc(Resume.uploaded_at)).offset((page - 1) * page_size).limit(page_size).all()
        return resumes, total

    @staticmethod
    def update_status(db: Session, resume_id: str, status: str, ocr_used: Optional[bool] = None) -> Optional[Resume]:
        resume = db.query(Resume).filter(Resume.id == resume_id, Resume.is_deleted == False).first()
        if not resume:
            return None
        resume.status = status
        if ocr_used is not None:
            resume.ocr_used = ocr_used
        resume.updated_at = utc_now()
        db.commit()
        db.refresh(resume)
        return resume

    @staticmethod
    def soft_delete(db: Session, resume_id: str, user_id: str) -> bool:
        resume = db.query(Resume).filter(Resume.id == resume_id, Resume.user_id == user_id, Resume.is_deleted == False).first()
        if not resume:
            return False
        resume.is_deleted = True
        resume.soft_deleted_at = utc_now()
        db.commit()
        create_audit_log(db, user_id, "RESUME_SOFT_DELETE", "RESUME", resume_id, {"file_name": resume.file_name})
        return True

    @staticmethod
    def hard_delete(db: Session, resume_id: str, user_id: str) -> bool:
        resume = db.query(Resume).filter(Resume.id == resume_id, Resume.user_id == user_id).first()
        if not resume:
            return False
        file_path = resume.file_path
        # Remove physical file if it exists
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                logger.warning(f"Could not delete physical file {file_path}: {e}")

        db.delete(resume)
        db.commit()
        create_audit_log(db, user_id, "RESUME_HARD_DELETE", "RESUME", resume_id, {"file_path": file_path})
        return True


class ParsedEntitiesRepository:
    @staticmethod
    def create_or_update(db: Session, resume_id: str, name: Optional[str] = None, email: Optional[str] = None, education: Optional[List] = None, experience: Optional[List] = None, skills: Optional[List] = None, sections: Optional[Dict] = None, raw_text: Optional[str] = None) -> ParsedEntities:
        pe = db.query(ParsedEntities).filter(ParsedEntities.resume_id == resume_id).first()
        if not pe:
            pe = ParsedEntities(
                id=generate_id("pe"),
                resume_id=resume_id,
                name=name,
                email=email,
                education=education or [],
                experience=experience or [],
                skills=skills or [],
                sections=sections or {},
                raw_text=raw_text or "",
                created_at=utc_now()
            )
            db.add(pe)
        else:
            if name is not None: pe.name = name
            if email is not None: pe.email = email
            if education is not None: pe.education = education
            if experience is not None: pe.experience = experience
            if skills is not None: pe.skills = skills
            if sections is not None: pe.sections = sections
            if raw_text is not None: pe.raw_text = raw_text

        db.commit()
        db.refresh(pe)
        return pe

    @staticmethod
    def get_by_resume_id(db: Session, resume_id: str) -> Optional[ParsedEntities]:
        return db.query(ParsedEntities).filter(ParsedEntities.resume_id == resume_id).first()


class SkillRepository:
    @staticmethod
    def create(db: Session, name: str, category: Optional[str] = None, description: Optional[str] = None, aliases: Optional[List[str]] = None) -> Skill:
        skill = Skill(
            id=generate_id("skl"),
            name=name.strip(),
            category=category,
            description=description,
            aliases=aliases or [],
            created_at=utc_now()
        )
        db.add(skill)
        db.commit()
        db.refresh(skill)
        return skill

    @staticmethod
    def get_by_id(db: Session, skill_id: str) -> Optional[Skill]:
        return db.query(Skill).filter(Skill.id == skill_id).first()

    @staticmethod
    def get_by_name(db: Session, name: str) -> Optional[Skill]:
        return db.query(Skill).filter(func.lower(Skill.name) == name.strip().lower()).first()

    @staticmethod
    def list_skills(db: Session, query_str: Optional[str] = None, category: Optional[str] = None, page: int = 1, page_size: int = 50) -> Tuple[List[Skill], int]:
        q = db.query(Skill)
        if query_str:
            q = q.filter(Skill.name.ilike(f"%{query_str}%"))
        if category:
            q = q.filter(Skill.category == category)
        total = q.count()
        items = q.order_by(Skill.name).offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    @staticmethod
    def update(db: Session, skill_id: str, data: Dict[str, Any]) -> Optional[Skill]:
        skill = db.query(Skill).filter(Skill.id == skill_id).first()
        if not skill:
            return None
        for k, v in data.items():
            if v is not None and hasattr(skill, k):
                setattr(skill, k, v)
        db.commit()
        db.refresh(skill)
        return skill

    @staticmethod
    def delete(db: Session, skill_id: str) -> bool:
        skill = db.query(Skill).filter(Skill.id == skill_id).first()
        if not skill:
            return False
        db.delete(skill)
        db.commit()
        return True


class JobPostingRepository:
    @staticmethod
    def create(
        db: Session,
        title: str,
        company: str,
        target_role: str,
        skills: List[str],
        location: Optional[str] = None,
        experience: Optional[str] = None,
        salary_min: Optional[float] = None,
        salary_max: Optional[float] = None,
        currency: str = "INR",
        unit: str = "LPA",
        description: Optional[str] = None,
        source: str = "live_api",
        external_id: Optional[str] = None,
        dedup_hash: Optional[str] = None,
        posted_at: Optional[datetime] = None
    ) -> JobPosting:
        posting = JobPosting(
            id=generate_id("job"),
            title=title,
            company=company,
            target_role=target_role,
            skills=skills,
            location=location,
            experience=experience,
            salary_min=salary_min,
            salary_max=salary_max,
            currency=currency,
            unit=unit,
            description=description,
            source=source,
            external_id=external_id,
            dedup_hash=dedup_hash,
            posted_at=posted_at or utc_now(),
            created_at=utc_now()
        )
        db.add(posting)
        db.commit()
        db.refresh(posting)
        return posting

    @staticmethod
    def get_by_external_id(db: Session, external_id: str, source: str) -> Optional[JobPosting]:
        return db.query(JobPosting).filter(
            JobPosting.external_id == external_id,
            JobPosting.source == source
        ).first()

    @staticmethod
    def get_by_dedup_hash(db: Session, dedup_hash: str) -> Optional[JobPosting]:
        return db.query(JobPosting).filter(JobPosting.dedup_hash == dedup_hash).first()

    @staticmethod
    def get_by_id(db: Session, job_id: str) -> Optional[JobPosting]:
        return db.query(JobPosting).filter(JobPosting.id == job_id).first()

    @staticmethod
    def list_job_postings(
        db: Session,
        role: Optional[str] = None,
        skill: Optional[str] = None,
        company: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        sort_by: str = "posted_at",
        order: str = "desc",
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[JobPosting], int]:
        q = db.query(JobPosting)
        if role:
            q = q.filter(JobPosting.target_role.ilike(f"%{role}%"))
        if company:
            q = q.filter(JobPosting.company.ilike(f"%{company}%"))
        if start_date:
            q = q.filter(JobPosting.posted_at >= start_date)
        if end_date:
            q = q.filter(JobPosting.posted_at <= end_date)
        if skill:
            # Filter postings containing skill in JSON or text
            q = q.filter(func.lower(cast(JobPosting.skills, Text)).contains(skill.lower()))

        total = q.count()

        # Sorting
        sort_attr = getattr(JobPosting, sort_by, JobPosting.posted_at)
        if order.lower() == "asc":
            q = q.order_by(asc(sort_attr))
        else:
            q = q.order_by(desc(sort_attr))

        items = q.offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    @staticmethod
    def update(db: Session, job_id: str, data: Dict[str, Any]) -> Optional[JobPosting]:
        jp = db.query(JobPosting).filter(JobPosting.id == job_id).first()
        if not jp:
            return None
        for k, v in data.items():
            if v is not None and hasattr(jp, k):
                setattr(jp, k, v)
        db.commit()
        db.refresh(jp)
        return jp

    @staticmethod
    def delete(db: Session, job_id: str) -> bool:
        jp = db.query(JobPosting).filter(JobPosting.id == job_id).first()
        if not jp:
            return False
        db.delete(jp)
        db.commit()
        return True


class AnalysisRepository:
    @staticmethod
    def create(db: Session, resume_id: str, target_role: str, ats_score: float, breakdown: Dict[str, float], skill_gap: Dict[str, Any]) -> Analysis:
        analysis = Analysis(
            id=generate_id("ans"),
            resume_id=resume_id,
            target_role=target_role,
            ats_score=ats_score,
            breakdown=breakdown,
            skill_gap=skill_gap,
            created_at=utc_now()
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        return analysis

    @staticmethod
    def get_by_id(db: Session, analysis_id: str) -> Optional[Analysis]:
        return db.query(Analysis).filter(Analysis.id == analysis_id).first()

    @staticmethod
    def get_latest_by_resume_id(db: Session, resume_id: str) -> Optional[Analysis]:
        return db.query(Analysis).filter(Analysis.resume_id == resume_id).order_by(desc(Analysis.created_at)).first()

    @staticmethod
    def list_analyses(db: Session, resume_id: Optional[str] = None, target_role: Optional[str] = None, page: int = 1, page_size: int = 20) -> Tuple[List[Analysis], int]:
        q = db.query(Analysis)
        if resume_id:
            q = q.filter(Analysis.resume_id == resume_id)
        if target_role:
            q = q.filter(Analysis.target_role.ilike(f"%{target_role}%"))
        total = q.count()
        items = q.order_by(desc(Analysis.created_at)).offset((page - 1) * page_size).limit(page_size).all()
        return items, total


from sqlalchemy import cast
