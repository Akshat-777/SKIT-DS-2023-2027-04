# ATS scoring foundation (User Story 4)

`ats_weights.json` is the single source of truth for the composite score. Each
component is scored from 0 to 100 and the weighted sum is rounded and clamped to
0–100.

| Component | Weight | Current first-slice formula |
| --- | ---: | --- |
| `keyword_match` | 0.30 | Sum of market `demand_pct` for canonical matched skills divided by total demand for the role. |
| `semantic_similarity` | 0.20 | Cosine similarity between resume text and a target-role profile from the embedding service, expressed as a percentage. |
| `section_completeness` | 0.15 | Detected expected sections (education, experience, skills, contact, summary) divided by five. |
| `formatting` | 0.10 | Existing length heuristic: strongest in the 200–1,200 word range, with penalties outside it. |
| `experience_relevance` | 0.15 | Share of experience entries containing bullets. |
| `quantified_impact` | 0.10 | Existing evidence-count heuristic for numeric impact in resume text. |

Demand rows are loaded from `data/processed/skill_demand.json`, filtered to the
role's `All` seniority bucket, and cached per role. If the index is not available
or contains no matching role, the existing starter role demand table is used.
Skill names and aliases are read from `data/processed/skills_taxonomy.json`.

The scorer emits one reason and one improvement tip for each factor. When the
embedding service cannot be reached, semantic similarity uses a neutral 50 score
and explains that fallback in the reason. The matching alias-aware skill gap is
also updated to use the processed demand index.

This is an incremental foundation. A dedicated `/score` route, salary-lift
ordering, Aishani's quantified-impact/depth fields, calibration fixtures, and
nearest-role handling are still pending.
