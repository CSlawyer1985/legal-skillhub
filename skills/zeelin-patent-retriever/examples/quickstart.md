# Quickstart

## Basic Flow

```bash
python3 -m pip install -r requirements.txt

RUN_ID="demo_$(date +%Y%m%d_%H%M%S)"
RUN_DIR="results/${RUN_ID}"
mkdir -p "$RUN_DIR"

python3 scripts/patent_search.py \
  --keywords "ai sentiment analysis" \
  --limit 80 \
  --output "$RUN_DIR/seed_raw.json"

python3 scripts/build_query_plan.py \
  --topic "Public Opinion + AI" \
  --keywords "public opinion ai sentiment" \
  --task-id "$RUN_ID" \
  --seed-raw "$RUN_DIR/seed_raw.json" \
  --concept-output "$RUN_DIR/concept_scan.json" \
  --plan-output "$RUN_DIR/query_plan.json"

python3 scripts/patent_search_plan.py \
  --plan "$RUN_DIR/query_plan.json" \
  --output-raw "$RUN_DIR/retriever_raw.json" \
  --output-retriever "$RUN_DIR/retriever_result.json" \
  --min-results 20
```

## Advanced: Explicit Year + Country Constraints

Goal: retrieve patents related to the US between 2021 and 2023 only.

```bash
RUN_ID="demo_us_2021_2023_$(date +%Y%m%d_%H%M%S)"
RUN_DIR="results/${RUN_ID}"
mkdir -p "$RUN_DIR"

python3 scripts/patent_search.py \
  --keywords "public opinion sentiment risk ai" \
  --limit 80 \
  --country US \
  --output "$RUN_DIR/seed_raw.json"

python3 scripts/build_query_plan.py \
  --topic "AI Public Opinion Early Warning" \
  --keywords "public opinion sentiment risk ai" \
  --task-id "$RUN_ID" \
  --years-back 8 \
  --country-in "US" \
  --seed-raw "$RUN_DIR/seed_raw.json" \
  --concept-output "$RUN_DIR/concept_scan.json" \
  --plan-output "$RUN_DIR/query_plan.json"

python3 - "$RUN_DIR/query_plan.json" <<'PY'
import json
import pathlib
import sys

p = pathlib.Path(sys.argv[1])
plan = json.loads(p.read_text(encoding="utf-8"))
for r in plan.get("query_rounds", []):
    f = r.setdefault("filters", {})
    f["country_in"] = ["US"]
    f["pub_date_from"] = 20210101
    f["pub_date_to"] = 20231231
p.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
print("updated", p)
PY

python3 scripts/patent_search_plan.py \
  --plan "$RUN_DIR/query_plan.json" \
  --output-raw "$RUN_DIR/retriever_raw.json" \
  --output-retriever "$RUN_DIR/retriever_result.json" \
  --min-results 20
```
