"""Quality summaries, CSV reports, and dependency-free SVG charts."""

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from .models import JobPosting


def _svg_bar_chart(title: str, values: dict[str, int], path: Path, limit: int = 15) -> None:
    entries = sorted(values.items(), key=lambda pair: (-pair[1], pair[0]))[:limit]
    width, row_h, label_w, chart_w = 900, 28, 210, 620
    height = 70 + len(entries) * row_h
    max_value = max((value for _, value in entries), default=1)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             '<rect width="100%" height="100%" fill="#ffffff"/>',
             f'<text x="20" y="30" font-family="Arial" font-size="20" font-weight="bold">{title}</text>']
    for index, (label, value) in enumerate(entries):
        y = 48 + index * row_h
        bar_width = max(1, int(chart_w * value / max_value))
        safe_label = (label.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
        parts.extend([f'<text x="20" y="{y+17}" font-family="Arial" font-size="13">{safe_label}</text>',
                      f'<rect x="{label_w}" y="{y+3}" width="{bar_width}" height="17" fill="#4776c5"/>',
                      f'<text x="{label_w+bar_width+8}" y="{y+17}" font-family="Arial" font-size="12">{value}</text>'])
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def build_quality_report(rows: list[JobPosting], path: Path) -> dict[str, Any]:
    total = len(rows)
    fields = ["job_id", "source", "title", "company", "location", "remote_flag", "experience_min",
              "experience_max", "salary_min", "salary_max", "currency", "salary_unit", "skills_required",
              "description", "posted_at", "url"]
    missing = {}
    for field in fields:
        count = sum(1 for row in rows if getattr(row, field) in (None, "", []))
        missing[field] = {"count": count, "percent": round(100 * count / total, 2) if total else 0.0}
    salary_rows = [r for r in rows if r.salary_min is not None or r.salary_max is not None]
    salaries = [x for r in salary_rows for x in (r.salary_min, r.salary_max) if x is not None]
    if salaries:
        sorted_salaries = sorted(salaries)
        q1 = sorted_salaries[len(sorted_salaries) // 4]
        q3 = sorted_salaries[(3 * len(sorted_salaries)) // 4]
        iqr = q3 - q1
        outliers = [x for x in salaries if x < q1 - 1.5 * iqr or x > q3 + 1.5 * iqr]
    else:
        q1 = q3 = None
        outliers = []
    roles = Counter(r.title for r in rows)
    skills = Counter(skill for row in rows for skill in row.skills_required)
    sources = Counter(r.source for r in rows)
    report = {"generated_at_utc": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
              "row_count": total, "source_counts": dict(sources), "missing_values": missing,
              "salary_coverage": {"rows_with_salary": len(salary_rows),
                                  "percent": round(100 * len(salary_rows) / total, 2) if total else 0.0,
                                  "outlier_value_count": len(outliers), "q1_lpa": q1, "q3_lpa": q3,
                                  "outlier_values_lpa": outliers[:100]},
              "role_distribution": dict(roles.most_common()),
              "skills_frequency": dict(skills.most_common()),
              "charts": ["role_distribution.svg", "skills_frequency.svg"]}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    _svg_bar_chart("Job posting count by title", dict(roles), path.parent / "role_distribution.svg")
    _svg_bar_chart("Required skill frequency", dict(skills), path.parent / "skills_frequency.svg")
    with (path.parent / "skills_frequency.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.writer(stream)
        writer.writerow(["skill", "posting_count"])
        writer.writerows(skills.most_common())
    return report
