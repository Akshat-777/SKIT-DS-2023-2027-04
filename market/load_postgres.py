"""Load processed CSV rows into PostgreSQL's job_postings table."""

import argparse
import csv
import json
import os
from pathlib import Path

from dotenv import load_dotenv


CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS job_postings (
    job_id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT NOT NULL,
    remote_flag BOOLEAN NOT NULL DEFAULT FALSE,
    experience_min NUMERIC,
    experience_max NUMERIC,
    salary_min NUMERIC,
    salary_max NUMERIC,
    currency TEXT NOT NULL DEFAULT 'INR',
    salary_unit TEXT NOT NULL DEFAULT 'INR LPA',
    skills_required JSONB NOT NULL DEFAULT '[]'::jsonb,
    description TEXT NOT NULL DEFAULT '',
    posted_at TEXT,
    url TEXT NOT NULL DEFAULT '',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)
"""
UPSERT = """
INSERT INTO job_postings (job_id, source, title, company, location, remote_flag,
 experience_min, experience_max, salary_min, salary_max, currency, salary_unit,
 skills_required, description, posted_at, url)
VALUES (%(job_id)s, %(source)s, %(title)s, %(company)s, %(location)s, %(remote_flag)s,
 %(experience_min)s, %(experience_max)s, %(salary_min)s, %(salary_max)s, %(currency)s, %(salary_unit)s,
 %(skills_required)s::jsonb, %(description)s, %(posted_at)s, %(url)s)
ON CONFLICT (job_id) DO UPDATE SET source=EXCLUDED.source, title=EXCLUDED.title,
 company=EXCLUDED.company, location=EXCLUDED.location, remote_flag=EXCLUDED.remote_flag,
 experience_min=EXCLUDED.experience_min, experience_max=EXCLUDED.experience_max,
 salary_min=EXCLUDED.salary_min, salary_max=EXCLUDED.salary_max, currency=EXCLUDED.currency,
 salary_unit=EXCLUDED.salary_unit, skills_required=EXCLUDED.skills_required,
 description=EXCLUDED.description, posted_at=EXCLUDED.posted_at, url=EXCLUDED.url, updated_at=NOW()
"""


def load_csv(path: Path, database_url: str | None = None) -> int:
    database_url = database_url or os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("Set DATABASE_URL, e.g. postgresql://user:password@localhost:5432/careerlens")
    try:
        import psycopg
    except ImportError as exc:
        raise RuntimeError("PostgreSQL loading requires psycopg[binary]; install requirements.txt") from exc
    count = 0
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cursor:
            cursor.execute(CREATE_TABLE)
            with path.open(newline="", encoding="utf-8-sig") as stream:
                for row in csv.DictReader(stream):
                    row["remote_flag"] = row["remote_flag"].strip().lower() == "true"
                    for key in ("experience_min", "experience_max", "salary_min", "salary_max"):
                        row[key] = float(row[key]) if row.get(key) else None
                    row["skills_required"] = json.dumps(json.loads(row.get("skills_required") or "[]"), ensure_ascii=False)
                    cursor.execute(UPSERT, row)
                    count += 1
    return count


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=Path(__file__).resolve().parent.parent / "data" / "processed" / "job_postings.csv")
    parser.add_argument("--database-url", default=None)
    args = parser.parse_args()
    print(f"Upserted {load_csv(args.csv, args.database_url)} rows into job_postings")


if __name__ == "__main__":
    main()
