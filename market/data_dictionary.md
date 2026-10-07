# CareerLens job-market dataset

The processed dataset is UTF-8 CSV at `data/processed/job_postings.csv`; the optional Parquet export is `job_postings.parquet`. Each run stores source-native payload snapshots as timestamped JSON under `data/raw/`. `quality_report.json`, `role_distribution.svg`, `skills_frequency.svg`, and `skills_frequency.csv` are generated beside the processed dataset.

| Field | Type | Meaning and missing-value rule |
|---|---|---|
| `job_id` | string | Source plus provider ID; if absent, a stable hash of title/company/location. |
| `source` | string | Provider adapter name (`mock`, `adzuna`, `jsearch`, `remotive`, `linkedin`). |
| `title` | string | Job title; falls back to query role, then `Unknown`. |
| `company` | string | Employer; falls back to `Unknown`. |
| `location` | string | Display location; falls back to `Unknown`. |
| `remote_flag` | boolean | True when provider marks remote or location/title says remote. |
| `experience_min` | number/null | Minimum years parsed from description; null when absent. |
| `experience_max` | number/null | Maximum years parsed; null for unspecified range. |
| `salary_min` | number/null | Lower annual salary bound, normalized to INR LPA; null if unavailable/unconvertible. |
| `salary_max` | number/null | Upper annual salary bound, normalized to INR LPA; null if unavailable/unconvertible. |
| `currency` | string | `INR` for converted values; original currency if unsupported. |
| `salary_unit` | string | Normalized output unit: `INR LPA`. |
| `skills_required` | array of strings | Provider skills plus case-insensitive starter-vocabulary matches in description. |
| `description` | string | HTML-stripped, entity-decoded, whitespace-normalized description. |
| `posted_at` | string/null | Provider posting timestamp as received; null if absent. |
| `url` | string | Provider posting/apply URL; empty string if absent. |

Deduplication keeps the first record for a provider ID and for a case-insensitive title + company + location key. The latter is global across sources. Salary range extraction uses provider numeric fields when present; the supported currency conversion is INR only. Unknown salaries and experience remain null and are counted in the quality report.

The PostgreSQL loader creates/upserts `job_postings` with JSONB skills. Coordinate with the API owner before merging schema changes into the shared database migration; the table columns match this dictionary and can be changed to fit the agreed central migration.
