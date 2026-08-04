---
name: zeelin-patent-retriever
description: |
  Team ZeeLin’s production-grade patent evidence retrieval skill for Google Patents BigQuery.
  Converts natural-language research intent into auditable multi-round retrieval plans with explicit filters (keywords, country, date, assignee/inventor, IPC/CPC), and outputs validated JSON artifacts for downstream analysis and drafting.
  Triggers: patent search, prior art, google patents, bigquery patent, 专利检索, 专利查新, 技术情报.
homepage: https://github.com/yangyuwen-bri/patent-retriever-bigquery
user-invocable: true
emoji: 🔎
tags:
  - patent
  - patent-search
  - prior-art
  - bigquery
  - google-patents
  - openclaw
metadata:
  openclaw:
    homepage: https://github.com/yangyuwen-bri/patent-retriever-bigquery
    requires:
      bins:
        - python3
      env:
        - GOOGLE_APPLICATION_CREDENTIALS
        - GOOGLE_CLOUD_PROJECT
---

# ZeeLin Patent Retriever

Team ZeeLin skill for Google Patents retrieval via BigQuery.
This skill performs patent retrieval and structured output generation only. It does not provide legal conclusions.

## 30-Second Quickstart Card

Purpose:
- Fetch, deduplicate, and structure patent evidence from Google Patents BigQuery for downstream analysis.

Required env:
- `GOOGLE_APPLICATION_CREDENTIALS`
- `GOOGLE_CLOUD_PROJECT`

Run this:

```bash
python3 -m pip install -r requirements.txt
RUN_ID="quick_$(date +%Y%m%d_%H%M%S)"; RUN_DIR="results/${RUN_ID}"; mkdir -p "$RUN_DIR"
python3 scripts/patent_search.py --keywords "ai sentiment analysis" --limit 80 --output "$RUN_DIR/seed_raw.json"
python3 scripts/build_query_plan.py --topic "Public Opinion + AI" --keywords "public opinion ai sentiment" --task-id "$RUN_ID" --seed-raw "$RUN_DIR/seed_raw.json" --concept-output "$RUN_DIR/concept_scan.json" --plan-output "$RUN_DIR/query_plan.json"
python3 scripts/patent_search_plan.py --plan "$RUN_DIR/query_plan.json" --output-raw "$RUN_DIR/retriever_raw.json" --output-retriever "$RUN_DIR/retriever_result.json" --min-results 20
```

Expected outputs:
- `$RUN_DIR/concept_scan.json`
- `$RUN_DIR/query_plan.json`
- `$RUN_DIR/retriever_raw.json`
- `$RUN_DIR/retriever_result.json`

If it fails:
- Missing env vars: configure Google credentials first.
- Too few results: keep filters and increase limits/expansion rounds before relaxing constraints.

## 1. Execution Rules

1. Use the three-stage flow by default: `seed -> build_plan -> execute_plan`.
2. Default minimum result count is `20` unless the user explicitly requests another value.
3. If the user specifies hard constraints (year, country, assignee, inventor, IPC/CPC), they must be applied in `query_plan.json` (`filters`) before execution.
4. Before execution, echo planned filters. After execution, echo effective filters, result size, and output file paths.

## 2. Pre-Run Checks

Required environment variables:

- `GOOGLE_APPLICATION_CREDENTIALS`
- `GOOGLE_CLOUD_PROJECT`

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Optional environment check:

```bash
python3 - <<'PY'
import os
required = ["GOOGLE_APPLICATION_CREDENTIALS", "GOOGLE_CLOUD_PROJECT"]
missing = [k for k in required if not os.getenv(k)]
print({"ok": not missing, "missing": missing})
PY
```

## 3. Capability Boundary and Parameter Sources

### 3.1 Supported filter dimensions

- Text: `keywords_all` / `keywords_any` / `keywords_anchor_any` / `keywords_not`
- Taxonomy: `ipc_prefix_any` / `cpc_prefix_any`
- Entities: `assignee_any` / `inventor_any`
- Geography: `country_in`
- Date ranges: `pub_date_from` / `pub_date_to` / `filing_date_from` / `filing_date_to`

Field source: `query_plan.json` (schema: `schemas/query_plan.schema.json`).

### 3.2 Default behavior for missing inputs

- `min_results`: default `20`
- Country unspecified: default `US,CN,WO,EP,JP,KR`
- Date range unspecified: default `years_back=8`
- Keywords missing: ask for clarification and do not run

### 3.3 Year-to-date mapping rules

- Single year (e.g. `2021`) => `from=20210101`, `to=20211231`
- Year range (e.g. `2021-2023`) => `from=20210101`, `to=20231231`
- Relative window (e.g. “last N years”) => use `--years-back N`

## 4. Standard Flow (Command Templates)

Create a run directory first:

```bash
RUN_ID="run_$(date +%Y%m%d_%H%M%S)"
RUN_DIR="results/${RUN_ID}"
mkdir -p "$RUN_DIR"
```

### Step 1: Seed retrieval

```bash
python3 scripts/patent_search.py \
  --keywords "<keywords>" \
  --limit 80 \
  --output "$RUN_DIR/seed_raw.json"
```

### Step 2: Build query plan

```bash
python3 scripts/build_query_plan.py \
  --topic "<topic>" \
  --keywords "<keywords>" \
  --task-id "$RUN_ID" \
  --years-back 8 \
  --country-in "US,CN,WO,EP,JP,KR" \
  --seed-raw "$RUN_DIR/seed_raw.json" \
  --concept-output "$RUN_DIR/concept_scan.json" \
  --plan-output "$RUN_DIR/query_plan.json"
```

### Step 3: Apply explicit user constraints (critical)

When the user explicitly requests country/year/assignee filters, patch `query_plan.json` before execution.

```bash
python3 - <<'PY'
import json
import os
from pathlib import Path

plan_path = Path(os.environ["RUN_DIR"]) / "query_plan.json"
plan = json.loads(plan_path.read_text(encoding="utf-8"))

# Example override: 2021-2023 + US + keyword constraints
for r in plan.get("query_rounds", []):
    f = r.setdefault("filters", {})
    f["country_in"] = ["US"]
    f["pub_date_from"] = 20210101
    f["pub_date_to"] = 20231231
    f.setdefault("keywords_any", [])
    f["keywords_any"] = list(dict.fromkeys(f["keywords_any"] + ["sentiment", "public opinion", "risk"]))

plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
print({"updated": str(plan_path)})
PY
```

### Step 4: Execute planned retrieval

```bash
python3 scripts/patent_search_plan.py \
  --plan "$RUN_DIR/query_plan.json" \
  --output-raw "$RUN_DIR/retriever_raw.json" \
  --output-retriever "$RUN_DIR/retriever_result.json" \
  --min-results 20
```

### Step 5: Validate outputs

```bash
python3 scripts/schema_check.py --input "$RUN_DIR/concept_scan.json" --schema schemas/concept_scan.schema.json
python3 scripts/schema_check.py --input "$RUN_DIR/query_plan.json" --schema schemas/query_plan.schema.json
python3 scripts/schema_check.py --input "$RUN_DIR/retriever_result.json" --schema schemas/retriever_result.schema.json
```

## 5. Natural Language to Parameter Mapping Examples

Example A:

- User input: `Find US patents on AI public-opinion early warning from 2021 to 2023, at least 30 results`
- Mapping:
  - `topic="AI public opinion early warning"`
  - `keywords="ai public opinion early warning sentiment"`
  - Plan override: `country_in=["US"]`, `pub_date_from=20210101`, `pub_date_to=20231231`
  - Execution arg: `--min-results 30`

Example B:

- User input: `Search multimodal emotion recognition patents in CN/JP/KR over the last 5 years, focus on Tencent and ByteDance`
- Mapping:
  - `--years-back 5`
  - `country_in=["CN","JP","KR"]`
  - `assignee_any=["Tencent","ByteDance"]`

## 6. Post-Execution Response Template (required)

```text
Retrieval completed.
Effective filters:
- Countries: ...
- Publication date range: ...
- Filing date range: ...
- Keywords (any/all/not): ...
- Assignee/Inventor filters: ...

Results:
- Patent count: ...
- Country distribution: ...
- Latest publication date: ...

Files:
- concept_scan: ...
- query_plan: ...
- retriever_raw: ...
- retriever_result: ...
```

## 7. Common Failures and Recovery

- Missing environment variables: instruct user to configure Google credentials first.
- Insufficient retrieval volume:
  1. Keep constraints, increase per-round limits.
  2. Increase expansion rounds.
  3. If still insufficient, ask whether to relax country/date constraints.
- Cost risk: prioritize narrower date windows and country scopes before broad scans.

## 8. Output Contract

Required output files:

- `concept_scan.json`
- `query_plan.json`
- `retriever_raw.json`
- `retriever_result.json`

`retriever_result.json` minimum requirements:

- `patents` count `>= min_results` (default 20)
- each item includes `publication_number` and `title`

## 9. References

- Methodology: `references/methodology.md`
- Quick examples: `examples/quickstart.md`
