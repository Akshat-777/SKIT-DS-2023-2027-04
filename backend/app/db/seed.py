import sys
import os
import random
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db.database import SessionLocal, Base, engine
from app.models.models import (
    User, Skill, JobPosting, RoleTaxonomy, SkillDemand, generate_id, utc_now
)
from app.core.security_privacy import encrypt_pii

def seed_database():
    print("Initializing Database tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Seed Users
        print("Seeding Users...")
        sample_users = [
            ("Akshat Agarwal", "akshat@example.com", "user"),
            ("Akshat Goyal", "goyal@example.com", "user"),
            ("Aishani Billore", "aishani@example.com", "user"),
            ("Aryan Rathore", "aryan@example.com", "user"),
            ("Admin User", "admin@careerlens.ai", "admin")
        ]

        for name, email, role in sample_users:
            existing = db.query(User).all()
            if not any(u.email == email or u.email == encrypt_pii(email) for u in existing):
                db.add(User(
                    id=generate_id("usr"),
                    name=name,
                    email=encrypt_pii(email),
                    password_hash="$2a$10$7qY3w8F8m1mXkF8vH.7mue5.Q1eZ.N0lW.N0lW.N0lW.N0lW",  # password123
                    role=role,
                    consent_given=True,
                    retention_days=365,
                    created_at=utc_now(),
                    updated_at=utc_now()
                ))
        db.commit()

        # 2. Seed Master Skills
        print("Seeding Master Skills...")
        skills_data = [
            ("Python", "Programming Languages", ["py", "python3"]),
            ("FastAPI", "Backend Frameworks", ["fast-api", "fastapi-framework"]),
            ("PostgreSQL", "Databases", ["postgres", "pgsql", "postgres-db"]),
            ("React.js", "Frontend", ["react", "reactjs"]),
            ("Tailwind CSS", "Frontend Styling", ["tailwind", "tailwindcss"]),
            ("Docker", "DevOps & Cloud", ["docker-container", "containers"]),
            ("ChromaDB", "Vector Databases", ["chroma", "vector-store"]),
            ("LightGBM", "Machine Learning", ["lgb", "light-gbm"]),
            ("Hugging Face Transformers", "NLP / AI", ["transformers", "huggingface"]),
            ("Kubernetes", "DevOps & Cloud", ["k8s", "kuber"]),
            ("Apache Kafka", "Data Engineering", ["kafka", "event-stream"]),
            ("Redis", "Caching & NoSQL", ["redis-cache"]),
            ("Node.js", "Backend Runtime", ["node", "nodejs", "expressjs"]),
            ("GraphQL", "API Architectures", ["gql"]),
            ("Scikit-learn", "Machine Learning", ["sklearn"]),
            ("PyTorch", "Deep Learning", ["torch"]),
            ("System Design", "Architecture", ["hld", "lld"]),
            ("REST APIs", "API Architectures", ["rest", "restful"]),
            ("CI/CD", "DevOps", ["github-actions", "jenkins"]),
            ("Alembic", "Database Migrations", ["sqlalchemy-migrations"])
        ]

        for s_name, cat, aliases in skills_data:
            existing_skill = db.query(Skill).filter(Skill.name == s_name).first()
            if not existing_skill:
                db.add(Skill(
                    id=generate_id("skl"),
                    name=s_name,
                    category=cat,
                    aliases=aliases,
                    description=f"{s_name} technical skill category {cat}",
                    created_at=utc_now()
                ))
        db.commit()

        # 3. Seed Role Taxonomy & Skill Demand
        print("Seeding Role Taxonomy & Demand Metrics...")
        roles_data = [
            ("Full Stack Data Engineer", "Data Engineering", ["Python", "PostgreSQL", "FastAPI", "Apache Kafka", "Docker"]),
            ("Backend Developer", "Software Engineering", ["Python", "FastAPI", "PostgreSQL", "Redis", "Docker"]),
            ("AI / ML Engineer", "Artificial Intelligence", ["Python", "PyTorch", "LightGBM", "Hugging Face Transformers", "ChromaDB"]),
            ("Frontend Engineer", "Web Development", ["React.js", "Tailwind CSS", "JavaScript", "REST APIs"])
        ]

        for r_name, cat, req_skills in roles_data:
            existing_role = db.query(RoleTaxonomy).filter(RoleTaxonomy.role_name == r_name).first()
            if not existing_role:
                db.add(RoleTaxonomy(
                    id=generate_id("rt"),
                    role_name=r_name,
                    category=cat,
                    required_skills=req_skills,
                    description=f"Standard taxonomy profile for {r_name}"
                ))

            # Add sample skill demand entries
            for sk in req_skills:
                demand_val = round(random.uniform(65.0, 95.0), 1)
                existing_sd = db.query(SkillDemand).filter(
                    SkillDemand.role == r_name,
                    SkillDemand.skill == sk,
                    SkillDemand.month == "2026-10"
                ).first()
                if not existing_sd:
                    db.add(SkillDemand(
                        id=generate_id("sd"),
                        role=r_name,
                        skill=sk,
                        demand_pct=demand_val,
                        month="2026-10",
                        created_at=utc_now()
                    ))
        db.commit()

        # 4. Seed 50 Job Postings
        print("Seeding 50 Sample Job Postings...")
        companies = [
            "TechCorp Solutions", "InnoData Systems", "CloudScale India", "Jaipur AI Labs",
            "DataMind Innovations", "Apex Cybernetics", "InfraSoft Global", "Vanguard Analytics",
            "NextGen Devs", "ByteStream Tech"
        ]

        roles = [
            "Full Stack Data Engineer",
            "Backend Developer",
            "AI / ML Engineer",
            "Frontend Engineer",
            "Python Backend Engineer",
            "Data Systems Architect"
        ]

        locations = ["Jaipur, RJ", "Bengaluru, KA", "Gurgaon, HR", "Remote", "Pune, MH", "Hyderabad, TS"]
        skill_pool = ["Python", "FastAPI", "PostgreSQL", "Docker", "React.js", "Tailwind CSS", "ChromaDB", "LightGBM", "Kubernetes", "Apache Kafka", "Redis", "Node.js"]

        existing_jobs_count = db.query(JobPosting).count()
        if existing_jobs_count < 50:
            to_create = 50 - existing_jobs_count
            for i in range(to_create):
                target_role = random.choice(roles)
                company = random.choice(companies)
                loc = random.choice(locations)
                selected_skills = random.sample(skill_pool, random.randint(3, 6))
                sal_min = round(random.uniform(6.0, 14.0), 1)
                sal_max = round(sal_min + random.uniform(3.0, 8.0), 1)
                days_ago = random.randint(0, 30)
                posted_time = utc_now() - timedelta(days=days_ago)

                db.add(JobPosting(
                    id=generate_id("job"),
                    title=f"{target_role} ({company})",
                    company=company,
                    location=loc,
                    target_role=target_role,
                    skills=selected_skills,
                    experience=f"{random.randint(0, 3)}+ years",
                    salary_min=sal_min,
                    salary_max=sal_max,
                    currency="INR",
                    unit="LPA",
                    description=f"We are looking for a skilled {target_role} at {company} to build scalable microservices and data pipelines. Key skills required: {', '.join(selected_skills)}.",
                    posted_at=posted_time,
                    source="live_market_feed",
                    created_at=utc_now()
                ))
            db.commit()

        total_postings = db.query(JobPosting).count()
        print(f"Database seeded successfully! Total job postings in database: {total_postings}")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
