"""Build skill taxonomy and role-wise demand artifacts from the processed CSV."""

import argparse
import csv
import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from .taxonomy import build_skill_demand, export_taxonomy, validate_index

LOG = logging.getLogger("market.taxonomy")


def load_postings(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path(__file__).resolve().parent.parent / "data" / "processed" / "job_postings.csv")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent.parent / "data" / "processed")
    parser.add_argument("--minimum-postings", type=int, default=5)
    parser.add_argument("--as-of", help="Override current UTC date (YYYY-MM-DD), useful for reproducible trend reports")
    parser.add_argument("--database-url", help="Optional PostgreSQL URL; defaults to DATABASE_URL")
    args = parser.parse_args()
    if args.minimum_postings < 1:
        parser.error("--minimum-postings must be at least 1")
    rows = load_postings(args.input)
    index = build_skill_demand(rows, minimum_postings=args.minimum_postings,
                               as_of=__import__("datetime").date.fromisoformat(args.as_of) if args.as_of else None)
    export_taxonomy(args.output_dir, index)
    errors = validate_index(index)
    print(json.dumps({"postings": index["posting_count"], "roles": len(index["roles"]),
                      "role_seniority_groups": len(index["roles"]), "skill_demand_rows": len(index["skill_demand"]),
                      "unmapped_skill_count": len(index["unmatched_skills"]), "validation_errors": errors,
                      "output_dir": str(args.output_dir)}, indent=2))
    if args.database_url or os.getenv("DATABASE_URL"):
        from .taxonomy_store import write_taxonomy
        print(f"PostgreSQL rows written: {write_taxonomy(index, args.database_url)}")
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
