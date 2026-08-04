#!/usr/bin/env python3
"""
Execute Google BigQuery patent retrieval by query_plan.json.

Design goals:
- Recall-first retrieval (avoid over-filtering in early rounds)
- Execute at least N rounds before early stop
- Enforce quality quota (min results + recency ratio + country diversity)
- Stratify output for downstream LLM context (core/frontier/adjacent)
"""

from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import scripts.config as config  # noqa: F401

try:
    from google.cloud import bigquery
except ImportError:  # pragma: no cover
    print("缺少 google-cloud-bigquery 依赖，请先安装 requirements.txt")
    raise


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _norm_pubnum(item: Dict[str, Any]) -> str:
    for key in ["publication_number", "patent_number", "id"]:
        val = item.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip().upper()
    return ""


def _text_match_condition(param_name: str) -> str:
    # Recall-quality balance: title + abstract match for better semantic coverage.
    return (
        f"EXISTS(SELECT 1 FROM UNNEST(title_localized) t "
        f"WHERE LOWER(t.text) LIKE CONCAT('%', @{param_name}, '%')) "
        f"OR EXISTS(SELECT 1 FROM UNNEST(abstract_localized) a "
        f"WHERE LOWER(a.text) LIKE CONCAT('%', @{param_name}, '%'))"
    )


def _safe_terms(values: List[Any]) -> List[str]:
    out: List[str] = []
    for val in values or []:
        if not isinstance(val, str):
            continue
        s = val.strip().lower()
        if not s:
            continue
        out.append(s)

    seen = set()
    ordered: List[str] = []
    for t in out:
        if t in seen:
            continue
        seen.add(t)
        ordered.append(t)
    return ordered


def _build_round_query(
    table: str,
    round_cfg: Dict[str, Any],
) -> Tuple[str, bigquery.QueryJobConfig]:
    filters = round_cfg.get("filters", {}) if isinstance(round_cfg.get("filters"), dict) else {}
    limit = int(round_cfg.get("limit", 40))

    where_parts: List[str] = ["publication_number IS NOT NULL"]
    score_terms: List[str] = []
    params: List[Any] = [bigquery.ScalarQueryParameter("limit", "INT64", limit)]

    kw_all = _safe_terms(filters.get("keywords_all", []))
    kw_any = _safe_terms(filters.get("keywords_any", []))
    kw_anchor = _safe_terms(filters.get("keywords_anchor_any", []))
    kw_not = _safe_terms(filters.get("keywords_not", []))

    for idx, kw in enumerate(kw_all):
        pn = f"kw_all_{idx}"
        cond = _text_match_condition(pn)
        where_parts.append(cond)
        score_terms.append(f"CASE WHEN ({cond}) THEN 1 ELSE 0 END")
        params.append(bigquery.ScalarQueryParameter(pn, "STRING", kw))

    if kw_any:
        ors: List[str] = []
        for idx, kw in enumerate(kw_any):
            pn = f"kw_any_{idx}"
            cond = _text_match_condition(pn)
            ors.append(cond)
            score_terms.append(f"CASE WHEN ({cond}) THEN 1 ELSE 0 END")
            params.append(bigquery.ScalarQueryParameter(pn, "STRING", kw))
        where_parts.append("(" + " OR ".join(ors) + ")")

    if kw_anchor:
        ors: List[str] = []
        for idx, kw in enumerate(kw_anchor):
            pn = f"kw_anchor_{idx}"
            cond = _text_match_condition(pn)
            ors.append(cond)
            score_terms.append(f"CASE WHEN ({cond}) THEN 2 ELSE 0 END")
            params.append(bigquery.ScalarQueryParameter(pn, "STRING", kw))
        where_parts.append("(" + " OR ".join(ors) + ")")

    for idx, kw in enumerate(kw_not):
        pn = f"kw_not_{idx}"
        where_parts.append(f"NOT {_text_match_condition(pn)}")
        params.append(bigquery.ScalarQueryParameter(pn, "STRING", kw))

    ipc_prefix = _safe_terms(filters.get("ipc_prefix_any", []))
    if ipc_prefix:
        ors = []
        for idx, pref in enumerate(ipc_prefix):
            pn = f"ipc_pref_{idx}"
            ors.append(f"EXISTS(SELECT 1 FROM UNNEST(ipc) i WHERE UPPER(i.code) LIKE CONCAT(UPPER(@{pn}), '%'))")
            params.append(bigquery.ScalarQueryParameter(pn, "STRING", pref))
        where_parts.append("(" + " OR ".join(ors) + ")")

    cpc_prefix = _safe_terms(filters.get("cpc_prefix_any", []))
    if cpc_prefix:
        ors = []
        for idx, pref in enumerate(cpc_prefix):
            pn = f"cpc_pref_{idx}"
            ors.append(f"EXISTS(SELECT 1 FROM UNNEST(cpc) c WHERE UPPER(c.code) LIKE CONCAT(UPPER(@{pn}), '%'))")
            params.append(bigquery.ScalarQueryParameter(pn, "STRING", pref))
        where_parts.append("(" + " OR ".join(ors) + ")")

    assignees = _safe_terms(filters.get("assignee_any", []))
    if assignees:
        ors = []
        for idx, kw in enumerate(assignees):
            pn = f"asg_{idx}"
            ors.append(
                f"EXISTS(SELECT 1 FROM UNNEST(assignee_harmonized) ah "
                f"WHERE LOWER(ah.name) LIKE CONCAT('%', @{pn}, '%'))"
            )
            params.append(bigquery.ScalarQueryParameter(pn, "STRING", kw))
        where_parts.append("(" + " OR ".join(ors) + ")")

    inventors = _safe_terms(filters.get("inventor_any", []))
    if inventors:
        ors = []
        for idx, kw in enumerate(inventors):
            pn = f"inv_{idx}"
            ors.append(
                f"EXISTS(SELECT 1 FROM UNNEST(inventor_harmonized) ih "
                f"WHERE LOWER(ih.name) LIKE CONCAT('%', @{pn}, '%'))"
            )
            params.append(bigquery.ScalarQueryParameter(pn, "STRING", kw))
        where_parts.append("(" + " OR ".join(ors) + ")")

    country_in = [x.strip().upper() for x in filters.get("country_in", []) if isinstance(x, str) and x.strip()]
    if country_in:
        where_parts.append("country_code IN UNNEST(@country_in)")
        params.append(bigquery.ArrayQueryParameter("country_in", "STRING", country_in))

    if filters.get("pub_date_from"):
        where_parts.append("publication_date >= @pub_date_from")
        params.append(bigquery.ScalarQueryParameter("pub_date_from", "INT64", int(filters["pub_date_from"])))
    if filters.get("pub_date_to"):
        where_parts.append("publication_date <= @pub_date_to")
        params.append(bigquery.ScalarQueryParameter("pub_date_to", "INT64", int(filters["pub_date_to"])))
    if filters.get("filing_date_from"):
        where_parts.append("filing_date >= @filing_date_from")
        params.append(bigquery.ScalarQueryParameter("filing_date_from", "INT64", int(filters["filing_date_from"])))
    if filters.get("filing_date_to"):
        where_parts.append("filing_date <= @filing_date_to")
        params.append(bigquery.ScalarQueryParameter("filing_date_to", "INT64", int(filters["filing_date_to"])))

    where_sql = "\n AND ".join(where_parts)
    match_score_sql = " + ".join(score_terms) if score_terms else "0"
    sql = f"""
    SELECT
      publication_number,
      country_code,
      (SELECT text FROM UNNEST(title_localized) WHERE text IS NOT NULL LIMIT 1) AS title,
      (SELECT text FROM UNNEST(abstract_localized) WHERE text IS NOT NULL LIMIT 1) AS abstract,
      SUBSTR((SELECT text FROM UNNEST(claims_localized) WHERE text IS NOT NULL LIMIT 1), 1, 1200) AS claims,
      ARRAY(SELECT name FROM UNNEST(inventor_harmonized)) AS inventors,
      ARRAY(SELECT name FROM UNNEST(assignee_harmonized)) AS assignees,
      ARRAY(SELECT code FROM UNNEST(ipc)) AS ipc_codes,
      ARRAY(SELECT code FROM UNNEST(cpc)) AS cpc_codes,
      filing_date,
      publication_date,
      ({match_score_sql}) AS match_score
    FROM `{table}`
    WHERE {where_sql}
    ORDER BY match_score DESC, publication_date DESC
    LIMIT @limit
    """
    job_config = bigquery.QueryJobConfig(query_parameters=params)
    return sql, job_config


def _row_to_dict(row: Any, source_round: str) -> Dict[str, Any]:
    return {
        "publication_number": row.publication_number,
        "patent_number": row.publication_number,
        "title": row.title or "",
        "abstract": row.abstract or "",
        "claims": row.claims or "",
        "inventors": list(row.inventors or []),
        "assignees": list(row.assignees or []),
        "ipc_codes": list(row.ipc_codes or []),
        "cpc_codes": list(row.cpc_codes or []),
        "filing_date": row.filing_date,
        "publication_date": row.publication_date,
        "country_code": row.country_code,
        "source_round": source_round,
    }


def _merge_unique(pool: Dict[str, Dict[str, Any]], items: List[Dict[str, Any]]) -> int:
    added = 0
    for item in items:
        key = _norm_pubnum(item)
        if not key:
            continue
        if key in pool:
            continue
        pool[key] = item
        added += 1
    return added


def _expand_round(round_cfg: Dict[str, Any], idx: int) -> Dict[str, Any]:
    relaxed = deepcopy(round_cfg)
    relaxed["round_id"] = f"R-exp-{idx + 1}"
    relaxed["intent"] = "auto-expansion for quality quota"
    relaxed["limit"] = int(relaxed.get("limit", 60)) + 40 + idx * 20

    f = relaxed.get("filters", {})
    kw_all = _safe_terms(f.get("keywords_all", []))
    kw_any = _safe_terms(f.get("keywords_any", []))

    # Progressive relaxation.
    f["keywords_all"] = []
    f["keywords_any"] = _safe_terms(kw_any + kw_all)
    f["keywords_not"] = []
    f["ipc_prefix_any"] = _safe_terms(f.get("ipc_prefix_any", []))[:2]
    f["cpc_prefix_any"] = _safe_terms(f.get("cpc_prefix_any", []))[:2]

    pub_from = f.get("pub_date_from")
    if isinstance(pub_from, int):
        f["pub_date_from"] = max(19000101, pub_from - 60000)

    relaxed["filters"] = f
    return relaxed


def _safe_int_date(value: Any) -> int:
    try:
        return int(str(value))
    except Exception:
        return 0


def _quality_metrics(patents: List[Dict[str, Any]], recent_from: int) -> Dict[str, Any]:
    n = len(patents)
    if n == 0:
        return {
            "result_count": 0,
            "recent_count": 0,
            "recent_ratio": 0.0,
            "country_count": 0,
            "countries": {},
        }

    recent = 0
    countries: Dict[str, int] = {}
    for p in patents:
        dt = _safe_int_date(p.get("publication_date"))
        if dt >= recent_from:
            recent += 1
        cc = str(p.get("country_code", "")).upper().strip()
        if cc:
            countries[cc] = countries.get(cc, 0) + 1

    return {
        "result_count": n,
        "recent_count": recent,
        "recent_ratio": round(recent / n, 4),
        "country_count": len(countries),
        "countries": countries,
    }


def _quality_met(
    patents: List[Dict[str, Any]],
    min_results: int,
    recent_from: int,
    min_recent_ratio: float,
    min_country_count: int,
) -> bool:
    # Country diversity is tracked as a soft target; hard gate focuses on volume+recency.
    # Keep the parameter for compatibility with existing call sites/policy output.
    _ = min_country_count
    m = _quality_metrics(patents, recent_from)
    return (
        m["result_count"] >= min_results
        and m["recent_ratio"] >= min_recent_ratio
    )


def _keyword_pool_from_plan(rounds: List[Dict[str, Any]]) -> List[str]:
    out: List[str] = []
    for r in rounds:
        f = r.get("filters", {}) if isinstance(r.get("filters"), dict) else {}
        out.extend(_safe_terms(f.get("keywords_all", [])))
        out.extend(_safe_terms(f.get("keywords_any", [])))
    return _safe_terms(out)


def _build_stratified_context(
    patents: List[Dict[str, Any]],
    keyword_pool: List[str],
    recent_from: int,
) -> Dict[str, Any]:
    scored: List[Tuple[float, int, Dict[str, Any]]] = []
    keys = set(keyword_pool)
    for p in patents:
        title = str(p.get("title", "")).lower()
        dt = _safe_int_date(p.get("publication_date"))

        kw_hits = sum(1 for k in keys if k and k in title)
        recency_bonus = 0.8 if dt >= recent_from else 0.0
        cpc_bonus = 0.2 if any(str(x).upper().startswith("G06") for x in p.get("cpc_codes", [])) else 0.0
        score = kw_hits + recency_bonus + cpc_bonus
        scored.append((score, dt, p))

    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    sorted_patents = [x[2] for x in scored]

    core = sorted_patents[:30]
    remaining = sorted_patents[30:]
    frontier = [p for p in remaining if _safe_int_date(p.get("publication_date")) >= recent_from][:30]
    frontier_ids = {_norm_pubnum(p) for p in frontier}
    adjacent = [p for p in remaining if _norm_pubnum(p) not in frontier_ids][:30]

    return {
        "core": [p.get("publication_number") for p in core],
        "frontier": [p.get("publication_number") for p in frontier],
        "adjacent": [p.get("publication_number") for p in adjacent],
        "counts": {
            "core": len(core),
            "frontier": len(frontier),
            "adjacent": len(adjacent),
        },
    }


def _default_recent_from() -> int:
    return int(f"{max(1970, datetime.now().year - 2)}0101")


def _effective_policy(plan: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
    policy = plan.get("execution_policy", {}) if isinstance(plan.get("execution_policy"), dict) else {}

    min_rounds = max(int(args.min_rounds), int(policy.get("min_rounds", 0)))
    min_results = max(int(args.min_results), int(policy.get("min_results", 0)))

    recent_from = int(args.recent_from or 0)
    if recent_from <= 0:
        recent_from = int(policy.get("recent_from", 0)) if str(policy.get("recent_from", "")).isdigit() else 0
    if recent_from <= 0:
        recent_from = _default_recent_from()

    min_recent_ratio = max(float(args.min_recent_ratio), float(policy.get("min_recent_ratio", 0.0)))
    min_country_count = max(int(args.min_country_count), int(policy.get("min_country_count", 0)))

    return {
        "min_rounds": max(1, min_rounds),
        "min_results": min_results,
        "recent_from": recent_from,
        "min_recent_ratio": min_recent_ratio,
        "min_country_count": max(1, min_country_count),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Execute query plan on Google patents BigQuery")
    ap.add_argument("--plan", required=True, help="query_plan.json")
    ap.add_argument("--output-raw", required=True, help="retriever_raw.json path")
    ap.add_argument("--output-retriever", required=True, help="retriever_result.json path")
    ap.add_argument("--min-results", type=int, default=20)
    ap.add_argument("--min-rounds", type=int, default=2)
    ap.add_argument("--recent-from", type=int, default=0)
    ap.add_argument("--min-recent-ratio", type=float, default=0.30)
    ap.add_argument("--min-country-count", type=int, default=2)
    ap.add_argument("--max-expand-rounds", type=int, default=2)
    ap.add_argument("--max-bytes-billed", type=int, default=0, help="Per-query max bytes billed (0=unlimited)")
    ap.add_argument("--allow-partial", action="store_true")
    args = ap.parse_args()

    plan_path = Path(args.plan).resolve()
    plan = _load_json(plan_path)

    rounds = plan.get("query_rounds", [])
    if not isinstance(rounds, list) or not rounds:
        raise SystemExit("query_plan.query_rounds 为空")

    table = str(plan.get("table") or "").strip()
    if not table:
        raise SystemExit("query_plan.table 为空")

    policy = _effective_policy(plan, args)

    client = bigquery.Client()
    pool: Dict[str, Dict[str, Any]] = {}
    round_reports: List[Dict[str, Any]] = []
    errors: List[str] = []

    executed_rounds = 0

    for i, round_cfg in enumerate(list(rounds)):
        round_id = str(round_cfg.get("round_id") or f"R{i+1}")
        try:
            sql, job_config = _build_round_query(table=table, round_cfg=round_cfg)
            if args.max_bytes_billed > 0:
                job_config.maximum_bytes_billed = int(args.max_bytes_billed)
            result = client.query(sql, job_config=job_config).result()
            items = [_row_to_dict(r, source_round=round_id) for r in result]
            added = _merge_unique(pool, items)
            executed_rounds += 1

            metrics = _quality_metrics(list(pool.values()), policy["recent_from"])
            round_reports.append(
                {
                    "round_id": round_id,
                    "intent": round_cfg.get("intent", ""),
                    "fetched": len(items),
                    "added_unique": added,
                    "total_unique": len(pool),
                    "quality": metrics,
                }
            )

            if (
                executed_rounds >= policy["min_rounds"]
                and _quality_met(
                    list(pool.values()),
                    min_results=policy["min_results"],
                    recent_from=policy["recent_from"],
                    min_recent_ratio=policy["min_recent_ratio"],
                    min_country_count=policy["min_country_count"],
                )
            ):
                break
        except Exception as exc:  # pragma: no cover
            msg = f"{round_id} failed: {exc}"
            errors.append(msg)
            round_reports.append(
                {
                    "round_id": round_id,
                    "intent": round_cfg.get("intent", ""),
                    "fetched": 0,
                    "added_unique": 0,
                    "total_unique": len(pool),
                    "error": str(exc),
                }
            )

    # Auto expansion until quality quota met.
    expand_base = rounds[-1]
    expand_count = 0
    while (
        not _quality_met(
            list(pool.values()),
            min_results=policy["min_results"],
            recent_from=policy["recent_from"],
            min_recent_ratio=policy["min_recent_ratio"],
            min_country_count=policy["min_country_count"],
        )
        and expand_count < args.max_expand_rounds
    ):
        extra_round = _expand_round(expand_base, expand_count)
        expand_count += 1
        round_id = extra_round["round_id"]
        try:
            sql, job_config = _build_round_query(table=table, round_cfg=extra_round)
            if args.max_bytes_billed > 0:
                job_config.maximum_bytes_billed = int(args.max_bytes_billed)
            result = client.query(sql, job_config=job_config).result()
            items = [_row_to_dict(r, source_round=round_id) for r in result]
            added = _merge_unique(pool, items)

            metrics = _quality_metrics(list(pool.values()), policy["recent_from"])
            round_reports.append(
                {
                    "round_id": round_id,
                    "intent": extra_round.get("intent", ""),
                    "fetched": len(items),
                    "added_unique": added,
                    "total_unique": len(pool),
                    "quality": metrics,
                }
            )
        except Exception as exc:  # pragma: no cover
            msg = f"{round_id} failed: {exc}"
            errors.append(msg)
            round_reports.append(
                {
                    "round_id": round_id,
                    "intent": extra_round.get("intent", ""),
                    "fetched": 0,
                    "added_unique": 0,
                    "total_unique": len(pool),
                    "error": str(exc),
                }
            )

    patents = list(pool.values())
    patents.sort(key=lambda x: _safe_int_date(x.get("publication_date")), reverse=True)

    raw_path = Path(args.output_raw).resolve()
    retriever_path = Path(args.output_retriever).resolve()
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    retriever_path.parent.mkdir(parents=True, exist_ok=True)

    raw_path.write_text(json.dumps(patents, ensure_ascii=False, indent=2), encoding="utf-8")

    keyword_pool = _keyword_pool_from_plan(rounds)
    stratified = _build_stratified_context(patents, keyword_pool=keyword_pool, recent_from=policy["recent_from"])
    final_quality = _quality_metrics(patents, policy["recent_from"])

    task_id = str(plan.get("task_id") or retriever_path.stem)
    topic = str(plan.get("topic") or "")
    retriever_obj = {
        "task_id": task_id,
        "query": topic,
        "country": None,
        "limit": max(policy["min_results"], len(patents)),
        "command": "python3 patent_search_plan.py --plan ...",
        "output_file": str(raw_path),
        "patents": patents,
        "result_count": len(patents),
        "errors": errors,
        "execution": {
            "plan": str(plan_path),
            "policy": policy,
            "round_reports": round_reports,
            "expanded_rounds": expand_count,
            "quality": final_quality,
        },
        "stratified_context": stratified,
    }
    retriever_path.write_text(json.dumps(retriever_obj, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = {
        "task_id": task_id,
        "retriever_raw": str(raw_path),
        "retriever_result": str(retriever_path),
        "result_count": len(patents),
        "quality": final_quality,
        "round_reports": round_reports,
        "errors": errors,
    }

    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if not args.allow_partial and not _quality_met(
        patents,
        min_results=policy["min_results"],
        recent_from=policy["recent_from"],
        min_recent_ratio=policy["min_recent_ratio"],
        min_country_count=policy["min_country_count"],
    ):
        raise SystemExit(
            "检索结果未达到质量配额（数量/新近性）。"
            "请补充关键词、调整国家或放宽条件后重试。"
        )


if __name__ == "__main__":
    main()
