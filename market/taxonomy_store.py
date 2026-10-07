"""PostgreSQL persistence for the generated role and skill-demand index."""

import json
import os


CREATE_ROLE_TABLE = """
CREATE TABLE IF NOT EXISTS role_taxonomy (
    role TEXT NOT NULL,
    seniority TEXT NOT NULL,
    posting_count INTEGER NOT NULL,
    low_sample BOOLEAN NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (role, seniority)
)
"""
CREATE_DEMAND_TABLE = """
CREATE TABLE IF NOT EXISTS skill_demand (
    role TEXT NOT NULL,
    seniority TEXT NOT NULL,
    skill TEXT NOT NULL,
    category TEXT,
    posting_count INTEGER NOT NULL,
    total_postings INTEGER NOT NULL,
    demand_pct NUMERIC(5,2) NOT NULL CHECK (demand_pct >= 0 AND demand_pct <= 100),
    rank INTEGER NOT NULL,
    co_occurring_skills JSONB NOT NULL DEFAULT '[]'::jsonb,
    average_salary_lpa NUMERIC,
    trend TEXT NOT NULL,
    recent_demand_pct NUMERIC(5,2),
    previous_demand_pct NUMERIC(5,2),
    low_sample BOOLEAN NOT NULL,
    minimum_postings INTEGER NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (role, seniority, skill),
    FOREIGN KEY (role, seniority) REFERENCES role_taxonomy(role, seniority) ON DELETE CASCADE
)
"""
UPSERT_ROLE = """
INSERT INTO role_taxonomy(role, seniority, posting_count, low_sample)
VALUES (%(role)s, %(seniority)s, %(posting_count)s, %(low_sample)s)
ON CONFLICT (role, seniority) DO UPDATE SET posting_count=EXCLUDED.posting_count,
 low_sample=EXCLUDED.low_sample, updated_at=NOW()
"""
UPSERT_DEMAND = """
INSERT INTO skill_demand(role, seniority, skill, category, posting_count, total_postings, demand_pct, rank,
 co_occurring_skills, average_salary_lpa, trend, recent_demand_pct, previous_demand_pct, low_sample, minimum_postings)
VALUES (%(role)s, %(seniority)s, %(skill)s, %(category)s, %(posting_count)s, %(total_postings)s, %(demand_pct)s, %(rank)s,
 %(co_occurring_skills)s::jsonb, %(average_salary_lpa)s, %(trend)s, %(recent_demand_pct)s, %(previous_demand_pct)s,
 %(low_sample)s, %(minimum_postings)s)
ON CONFLICT (role, seniority, skill) DO UPDATE SET category=EXCLUDED.category,
 posting_count=EXCLUDED.posting_count, total_postings=EXCLUDED.total_postings,
 demand_pct=EXCLUDED.demand_pct, rank=EXCLUDED.rank, co_occurring_skills=EXCLUDED.co_occurring_skills,
 average_salary_lpa=EXCLUDED.average_salary_lpa, trend=EXCLUDED.trend,
 recent_demand_pct=EXCLUDED.recent_demand_pct, previous_demand_pct=EXCLUDED.previous_demand_pct,
 low_sample=EXCLUDED.low_sample, minimum_postings=EXCLUDED.minimum_postings, updated_at=NOW()
"""


def write_taxonomy(index: dict, database_url: str | None = None) -> int:
    url = database_url or os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("Provide --database-url or set DATABASE_URL")
    try:
        import psycopg
    except ImportError as exc:
        raise RuntimeError("Install psycopg[binary] from requirements.txt") from exc
    with psycopg.connect(url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(CREATE_ROLE_TABLE)
            cursor.execute(CREATE_DEMAND_TABLE)
            for row in index["roles"]:
                cursor.execute(UPSERT_ROLE, row)
            for row in index["skill_demand"]:
                values = dict(row)
                values["co_occurring_skills"] = json.dumps(values["co_occurring_skills"])
                cursor.execute(UPSERT_DEMAND, values)
    return len(index["roles"]) + len(index["skill_demand"])
