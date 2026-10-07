"""Scheduler-ready CLI for acquiring, cleaning, reporting, and exporting jobs."""

import argparse
import csv
import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from .cleaning import deduplicate, normalize_job
from .clients import JobBoardClient, client_from_name, raw_json
from .models import JobPosting
from .quality import build_quality_report

DEFAULT_ROLES = ["Data Scientist", "ML Engineer", "Backend Developer", "Frontend Developer",
                 "Data Analyst", "DevOps Engineer"]
DEFAULT_LOCATIONS = ["Jaipur, India", "Bengaluru, India", "Pune, India", "Remote, India"]
LOG = logging.getLogger("market")


def _safe_name(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", value).strip("_") or "source"


def _extract(client: JobBoardClient, payload: Any) -> list[dict[str, Any]]:
    return client.extract_jobs(payload)


def collect(roles: list[str], locations: list[str], pages: int, per_page: int,
            sources: list[str], output_dir: Path, include_parquet: bool = False) -> list[JobPosting]:
    """Collect pages; failures are logged per source/location/role without stopping others."""
    if pages < 1 or per_page < 1:
        raise ValueError("pages and per-page must be positive integers")
    raw_dir = output_dir.parent / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    collected: list[JobPosting] = []
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for source_name in sources:
        try:
            client = client_from_name(source_name)
        except ValueError as exc:
            LOG.error("%s", exc)
            continue
        for role in roles:
            for location in locations:
                for page in range(1, pages + 1):
                    try:
                        payload = client.fetch_page(role, location, page, per_page)
                        raw_path = raw_dir / f"{stamp}_{_safe_name(source_name)}_{_safe_name(role)}_{_safe_name(location)}_p{page}.json"
                        raw_path.write_text(raw_json({"collected_at": datetime.now(timezone.utc).isoformat(),
                                                      "source": source_name, "role_query": role,
                                                      "location_query": location, "page": page,
                                                      "response": payload}), encoding="utf-8")
                        native_jobs = _extract(client, payload)
                        LOG.info("%s: %s / %s page %s returned %s postings", source_name, role, location, page, len(native_jobs))
                        collected.extend(normalize_job(job, source_name, role) for job in native_jobs)
                        if not native_jobs:
                            break
                    except Exception as exc:
                        LOG.error("Skipping %s %s / %s page %s: %s", source_name, role, location, page, exc)
                        break
    rows = deduplicate(collected)
    if not rows:
        raise RuntimeError("No jobs were collected. Use --source mock or configure a valid provider API key.")
    _write_csv(rows, output_dir / "job_postings.csv")
    if include_parquet:
        _write_parquet(rows, output_dir / "job_postings.parquet")
    build_quality_report(rows, output_dir / "quality_report.json")
    LOG.info("Saved %d unique jobs to %s", len(rows), output_dir)
    return rows


def _write_csv(rows: list[JobPosting], path: Path) -> None:
    fields = list(rows[0].to_dict().keys())
    with path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            item = row.to_dict()
            item["skills_required"] = json.dumps(item["skills_required"], ensure_ascii=False)
            writer.writerow(item)


def _write_parquet(rows: list[JobPosting], path: Path) -> None:
    try:
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError("Parquet output needs pandas and pyarrow; install requirements.txt") from exc
    frame = pd.DataFrame([row.to_dict() for row in rows])
    frame.to_parquet(path, index=False)


def main(argv: list[str] | None = None) -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Collect and prepare CareerLens job-market data")
    parser.add_argument("--roles", nargs="+", default=DEFAULT_ROLES, help="Role search queries")
    parser.add_argument("--locations", nargs="+", default=DEFAULT_LOCATIONS, help="Locations, including Remote, India")
    parser.add_argument("--pages", type=int, default=2, help="Pages requested per role/location/source")
    parser.add_argument("--per-page", type=int, default=25, help="Postings requested per page")
    parser.add_argument("--source", nargs="+", default=[os.getenv("JOB_BOARD_SOURCE", "mock")],
                        choices=["mock", "adzuna", "jsearch", "remotive", "linkedin"], help="Provider adapters to run")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent.parent / "data" / "processed")
    parser.add_argument("--parquet", action="store_true", help="Also write Parquet; requires pyarrow")
    parser.add_argument("--log-level", default=os.getenv("LOG_LEVEL", "INFO"))
    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO),
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    collect(args.roles, args.locations, args.pages, args.per_page, args.source, args.output_dir, args.parquet)


if __name__ == "__main__":
    main()
