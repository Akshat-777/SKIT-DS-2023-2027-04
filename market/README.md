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
