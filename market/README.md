# CareerLens market intelligence pipeline

## Install

From the repository root, create and activate a Python virtual environment, then install the dependencies:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Copy `.env.example` to `.env` when configuring external API keys or PostgreSQL. The mock provider needs no credentials.

## Collect and prove the acceptance case

From the repository root, this scheduler-ready command creates 1,200 unique postings (6 roles × 4 locations × 5 pages × 10 postings):

```powershell
python -m market.collect --source mock --roles "Data Scientist" "ML Engineer" "Backend Developer" "Frontend Developer" "Data Analyst" "DevOps Engineer" --locations "Jaipur, India" "Bengaluru, India" "Pune, India" "Remote, India" --pages 5 --per-page 10
```

Artifacts appear in `data/raw/` and `data/processed/`. To verify the row count and generated data-quality charts/report:

```powershell
python -c "import csv,json,pathlib; p=pathlib.Path('data/processed'); n=sum(1 for _ in csv.DictReader((p/'job_postings.csv').open(encoding='utf-8-sig'))); q=json.loads((p/'quality_report.json').read_text(encoding='utf-8')); assert n >= 1000 and q['row_count'] == n and (p/'role_distribution.svg').exists() and (p/'skills_frequency.svg').exists(); print(f'PASS: {n} clean rows; quality report and charts generated')"
```

The mock IDs are unique across role, location, and page and the job content varies while remaining reproducible. A repeat run has different timestamped raw snapshots and rewrites the latest processed output.

## External sources and PostgreSQL

Adapters: `mock`, `adzuna`, `jsearch`, `remotive`, and an optional authorized `linkedin` endpoint. Select several with `--source adzuna remotive`; one provider failure is logged and does not stop the other source loops. Providers are paginated, requests have finite timeouts, retries, exponential backoff/429 handling, and a per-client minimum request interval. LinkedIn access stays disabled until an authorized proxy endpoint is configured.

```powershell
python -m market.collect --source adzuna --roles "Data Scientist" --locations "Jaipur, India" --pages 2
python -m market.collect --source mock --pages 2 --per-page 25 --parquet
python -m market.load_postgres --csv data/processed/job_postings.csv
```

The optional PostgreSQL loader reads `DATABASE_URL`, creates `job_postings` if needed, and upserts by `job_id`. Its schema follows `market/data_dictionary.md`; align that table with the central migration maintained by Akshat before deploying shared-database changes.

Run as a scheduled task by invoking `python -m market.collect` from the repository root. Override role/location/page/source arguments to set the collection window and coverage.

## Role taxonomy and skill demand

The shared taxonomy API is `from market.taxonomy import normalize_skill`. It maps common aliases (`JS`, `ML`, `Postgres`) to canonical skill labels. Exact/fuzzy suggestions and low-confidence unmatched input are recorded for manual review when building the index.

Build taxonomy and skill-demand outputs from the processed jobs CSV:

```powershell
python -m market.build_taxonomy --input data/processed/job_postings.csv --minimum-postings 5 --as-of 2026-10-07
```

Outputs include `skills_taxonomy.json` and `.csv`, `roles.json`, `role_taxonomy.csv`, `title_role_mapping.csv`, `skill_demand.json` and `.csv`, `uncertain_skill_matches.csv`, `unmapped_skills.json`, `taxonomy_validation.json`, and one SVG per role/seniority under `role_charts/`. Demand rows are computed separately for each seniority and for `All` seniority. The index reports posting share, tie-aware rank, top co-occurring skills, average observed salary in LPA, and trend across the most recent 30 days versus the preceding 30 days. Missing dates or missing salary bounds remain excluded from that calculation.

When `DATABASE_URL` is set (or passed with `--database-url`), the command also creates/upserts `role_taxonomy` and `skill_demand`. The FastAPI router reads the generated JSON artifacts and can be mounted by the API service:

```python
from fastapi import FastAPI
from market.router import router as market_router

app = FastAPI()
app.include_router(market_router)
```

Endpoints: `GET /market/roles`, `GET /market/skill-demand?role=Data%20Scientist&top_n=15`, `GET /market/skill-demand?role=Data%20Scientist&seniority=Senior&top_n=15`, and `GET /market/skills/ML`.

Focused tests:

```powershell
python -m unittest discover -s tests -v
```

The sample three-role top-15 output is in `market/taxonomy_demo.md`.
