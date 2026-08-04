#!/usr/bin/env python3
"""
Build Google BigQuery-only concept scan and query plan.

Upgraded scanner-style planner:
- Optional seed evidence from preliminary retrieval (--seed-raw / --seed-retriever)
- JB-like pattern abstraction + 4-dimension scoring
- Claim angles and evidence map
- Query rounds prioritized by high-score patterns
"""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

TABLE = "patents-public-data.patents.publications"
DEFAULT_THRESHOLD = 8.0

# Domain hints anchored to Google patent taxonomy reality.
CPC_HINTS: Dict[str, List[str]] = {
    "ai": ["G06N", "G06F"],
    "agent": ["G06N", "G06Q"],
    "workflow": ["G06Q", "G06F"],
    "video": ["H04N", "G06T"],
    "image": ["G06T", "H04N"],
    "nlp": ["G06F", "G06N"],
    "speech": ["G10L", "H04R"],
    "recommend": ["G06Q", "G06N"],
    "forecast": ["G06Q", "G06F"],
    "sentiment": ["G06F", "G06N"],
    "risk": ["G06Q", "G06F"],
    "security": ["H04L", "G06F"],
    "control": ["G05B", "G06F"],
}

TOKEN_EXPANSION: Dict[str, List[str]] = {
    "ai": ["artificial intelligence", "machine learning", "智能", "机器学习"],
    "agent": ["autonomous", "workflow", "代理", "智能体"],
    "video": ["short video", "multimodal", "短视频", "多模态"],
    "generation": ["generative", "synthesis", "生成", "合成"],
    "forecast": ["prediction", "predictive", "预测", "预估"],
    "recommend": ["recommendation", "ranking", "推荐", "排序"],
    "automation": ["orchestration", "pipeline", "自动化", "编排"],
    "sentiment": ["opinion mining", "emotion analysis", "情感分析", "舆情"],
}

STOPWORDS = {
    "a", "an", "the", "for", "with", "from", "and", "or", "to", "in", "on", "of", "by", "using",
    "data", "public", "information", "method", "methods", "system", "systems", "device", "devices",
    "apparatus", "module", "network", "processing", "management", "operation", "operations",
    "user", "users", "based", "thereof",
    "一种", "用于", "方法", "系统", "装置", "及其", "相关", "实现", "包括", "基于", "应用", "进行", "其中",
}

FRAME_SHIFT_TERMS = {
    "causal", "counterfactual", "autonomous", "self-supervised", "federated", "real-time",
    "因果", "反事实", "联邦", "自治", "实时", "自监督", "闭环",
}

NOISE_QUERY_TERMS = {
    "first", "second", "third", "set", "sets", "model", "models", "analysis",
    "application", "applications", "example", "examples",
}


def _dedup_keep_order(values: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for item in values:
        key = item.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(item.strip())
    return out


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def _extract_tokens(topic: str, keywords: str) -> List[str]:
    raw = f"{topic} {keywords}".lower()
    zh = re.findall(r"[\u4e00-\u9fff]{2,8}", raw)
    en = re.findall(r"[a-z][a-z0-9_-]{2,}", raw)
    candidates = _dedup_keep_order(zh + en)
    return [x for x in candidates if x not in STOPWORDS]


def _tokenize_text(text: str) -> List[str]:
    raw = re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}|[\u4e00-\u9fff]{2,8}", text or "")
    out: List[str] = []
    for t in raw:
        n = t.strip().lower()
        if not n or n in STOPWORDS or n.isdigit():
            continue
        out.append(n)
    return out


def _filter_seed_query_terms(tokens: List[str]) -> List[str]:
    out: List[str] = []
    for token in tokens or []:
        n = str(token).strip().lower()
        if not n or n in STOPWORDS or n in NOISE_QUERY_TERMS:
            continue
        if re.fullmatch(r"[a-z0-9_-]+", n):
            if n.isdigit() or len(n) < 4:
                continue
        out.append(n)
    return _dedup_keep_order(out)


def _infer_cpc_prefix(tokens: List[str]) -> List[str]:
    out: List[str] = []
    for token in tokens:
        for k, v in CPC_HINTS.items():
            if k in token:
                out.extend(v)
    return _dedup_keep_order(out)


def _expand_keywords(tokens: List[str]) -> List[str]:
    out = list(tokens)
    for token in tokens:
        for k, vals in TOKEN_EXPANSION.items():
            if k in token:
                out.extend(vals)
    return _dedup_keep_order(out)


def _load_seed_patents(seed_raw: Optional[str], seed_retriever: Optional[str]) -> List[Dict[str, Any]]:
    def _load(path: str) -> Any:
        p = Path(path).resolve()
        return json.loads(p.read_text(encoding="utf-8"))

    if seed_retriever:
        data = _load(seed_retriever)
        pats = data.get("patents", []) if isinstance(data, dict) else []
        return pats if isinstance(pats, list) else []
    if seed_raw:
        data = _load(seed_raw)
        return data if isinstance(data, list) else []
    return []


def _safe_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _pubnum(p: Dict[str, Any]) -> str:
    for k in ["publication_number", "patent_number", "id"]:
        v = p.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip().upper()
    return "UNKNOWN"


def _extract_seed_features(seed_patents: List[Dict[str, Any]]) -> Dict[str, Any]:
    token_counter: Counter = Counter()
    cpc_counter: Counter = Counter()
    ipc_counter: Counter = Counter()
    assignees: Counter = Counter()
    countries: Counter = Counter()
    frame_terms_hits = 0
    claims_len = []

    for p in seed_patents:
        title = str(p.get("title", ""))
        abstract = str(p.get("abstract", ""))
        claims = str(p.get("claims", ""))
        text = f"{title} {abstract}"
        token_counter.update(_tokenize_text(text))

        claims_tokens = _tokenize_text(claims)
        if claims_tokens:
            claims_len.append(len(claims_tokens))

        cpcs = [str(x).upper() for x in _safe_list(p.get("cpc_codes")) if str(x).strip()]
        ipcs = [str(x).upper() for x in _safe_list(p.get("ipc_codes")) if str(x).strip()]
        cpc_counter.update([x[:4] for x in cpcs])
        ipc_counter.update([x[:4] for x in ipcs])

        assignee_list = [str(x).strip() for x in _safe_list(p.get("assignees")) if str(x).strip()]
        if not assignee_list and isinstance(p.get("applicant"), str):
            assignee_list = [x.strip() for x in str(p["applicant"]).split(",") if x.strip()]
        assignees.update(assignee_list)

        cc = str(p.get("country_code", "")).upper().strip()
        if cc:
            countries.update([cc])

        frame_terms_hits += sum(1 for t in _tokenize_text(text + " " + claims) if t in FRAME_SHIFT_TERMS)

    return {
        "top_tokens": [k for k, _ in token_counter.most_common(30)],
        "top_cpc": [k for k, _ in cpc_counter.most_common(8)],
        "top_ipc": [k for k, _ in ipc_counter.most_common(8)],
        "top_assignees": [k for k, _ in assignees.most_common(8)],
        "top_countries": [k for k, _ in countries.most_common(8)],
        "avg_claims_len": (sum(claims_len) / len(claims_len)) if claims_len else 0.0,
        "frame_terms_hits": frame_terms_hits,
        "sample_size": len(seed_patents),
    }


def _pick_component_windows(tokens: List[str], top_tokens: List[str]) -> List[List[str]]:
    base = _dedup_keep_order(tokens + top_tokens[:20])
    if not base:
        return [["innovation", "system", "optimization"]]
    windows: List[List[str]] = []
    window_size = 3
    for i in range(0, min(len(base), 15), 3):
        w = base[i:i + window_size]
        if len(w) >= 2:
            windows.append(w)
    while len(windows) < 5:
        windows.append(base[:3] if len(base) >= 3 else base)
    return windows[:5]


def _score_pattern(
    components: List[str],
    seed_features: Dict[str, Any],
    sample_size: int,
) -> Dict[str, float]:
    # Distinctiveness: rarer term combos -> higher score.
    top_tokens = set(seed_features.get("top_tokens", []))
    uncommon = sum(1 for c in components if c not in top_tokens)
    distinctiveness = 1.6 + min(2.4, uncommon * 0.8)

    # Sophistication: derive from claim length + taxonomy diversity.
    avg_claims_len = float(seed_features.get("avg_claims_len", 0.0))
    taxonomy_depth = min(1.0, (len(seed_features.get("top_cpc", [])) + len(seed_features.get("top_ipc", []))) / 12.0)
    sophistication = 1.1 + min(1.9, 1.0 * taxonomy_depth + min(0.9, avg_claims_len / 140.0))

    # System impact: assignee/country spread as architecture impact proxy.
    assignee_div = len(seed_features.get("top_assignees", []))
    country_div = len(seed_features.get("top_countries", []))
    system_impact = 1.2 + min(1.8, (assignee_div / 7.0) + (country_div / 9.0))

    # Frame shift: presence of advanced framing terms.
    frame_hits = int(seed_features.get("frame_terms_hits", 0))
    frame_shift = 1.1 + min(1.9, frame_hits / max(3.0, sample_size / 7.0))

    total = round(distinctiveness + sophistication + system_impact + frame_shift, 2)
    return {
        "distinctiveness": round(min(4.0, distinctiveness), 2),
        "sophistication": round(min(3.0, sophistication), 2),
        "system_impact": round(min(3.0, system_impact), 2),
        "frame_shift": round(min(3.0, frame_shift), 2),
        "total": total,
    }


def _patent_signals(total: float, sample_size: int) -> Dict[str, str]:
    if total >= 9.5:
        novelty = "high"
    elif total >= 8.0:
        novelty = "medium"
    else:
        novelty = "low"

    if sample_size >= 60:
        market = "high"
    elif sample_size >= 30:
        market = "medium"
    else:
        market = "low"

    competitive = "high" if total >= 8.0 and sample_size >= 30 else "medium"
    return {
        "market_demand": market,
        "competitive_value": competitive,
        "novelty_confidence": novelty,
    }


def _build_patterns(
    topic: str,
    tokens: List[str],
    threshold: float,
    seed_patents: List[Dict[str, Any]],
    seed_features: Dict[str, Any],
) -> List[Dict[str, Any]]:
    component_windows = _pick_component_windows(tokens=tokens, top_tokens=seed_features.get("top_tokens", []))
    top_pub = [_pubnum(p) for p in seed_patents[:12]]
    patterns: List[Dict[str, Any]] = []

    for idx, comps in enumerate(component_windows, start=1):
        mechanism = " + ".join(comps)
        score = _score_pattern(comps, seed_features=seed_features, sample_size=max(1, len(seed_patents)))
        total = score["total"]
        title = f"{topic}：{comps[0]}驱动的{('系统编排' if idx % 2 == 0 else '机制创新')}"

        claim_angles = [
            f"Method: 一种面向{topic}的步骤方法，包含{mechanism}的协同处理。",
            f"System: 一种面向{topic}的系统，包含{mechanism}相关模块并执行闭环控制。",
            f"Apparatus: 一种用于{topic}的装置/平台，配置有{mechanism}功能单元。",
        ]

        patterns.append(
            {
                "pattern_id": f"P{idx}",
                "title": title,
                "category": "high_value" if total >= threshold else "candidate",
                "components": [{"name": c, "domain": "seed_evidence", "role": "core_signal"} for c in comps],
                "score": score,
                "synergy": {
                    "combined_benefit": f"{mechanism} 联合后形成更强的可解释与可部署能力。",
                    "individual_sum": "单一模块仅提供局部优化。",
                    "synergy_factor": "多模块闭环使方案具备工程放大效应。",
                },
                "evidence": {
                    "user_claims": [f"主题围绕 {topic}"],
                    "technical_details": [f"来自 seed 专利样本 {len(seed_patents)} 条的高频技术信号"],
                    "supporting_patents": top_pub[idx - 1: idx + 2],
                },
                "problem_solution_benefit": {
                    "problem": f"当前{topic}方案多为单点优化，跨模块协同不足。",
                    "solution": f"以{mechanism}形成可执行的端到端编排机制。",
                    "benefit": "提高稳定性、可解释性和部署可行性。",
                },
                "patent_signals": _patent_signals(total=total, sample_size=len(seed_patents)),
                "_claim_angles_note": "patterns>=threshold 将优先进入查询规划",
                "claim_angles": claim_angles,
                "abstract_mechanism": f"将{mechanism}抽象为可迁移的发明机制",
                "concrete_reference": f"基于 seed 样本中的技术表达（{', '.join(top_pub[:2]) if top_pub else 'N/A'}）",
            }
        )

    patterns.sort(key=lambda x: x.get("score", {}).get("total", 0), reverse=True)
    return patterns


def _date_yyyymmdd(years_back: int) -> Tuple[int, int]:
    now = datetime.now()
    to_date = int(now.strftime("%Y%m%d"))
    from_year = max(1970, now.year - years_back)
    from_date = int(f"{from_year}{now.strftime('%m%d')}")
    return from_date, to_date


def _build_round(
    round_id: str,
    intent: str,
    limit: int,
    keywords_all: List[str],
    keywords_any: List[str],
    keywords_anchor_any: List[str],
    ipc_prefix_any: List[str],
    cpc_prefix_any: List[str],
    country_in: List[str],
    pub_date_from: int,
    pub_date_to: int,
) -> Dict[str, Any]:
    return {
        "round_id": round_id,
        "intent": intent,
        "limit": limit,
        "filters": {
            "keywords_all": keywords_all,
            "keywords_any": keywords_any,
            "keywords_anchor_any": keywords_anchor_any,
            "keywords_not": [],
            "ipc_prefix_any": ipc_prefix_any,
            "cpc_prefix_any": cpc_prefix_any,
            "assignee_any": [],
            "inventor_any": [],
            "country_in": country_in,
            "pub_date_from": pub_date_from,
            "pub_date_to": pub_date_to,
        },
    }


def _build_query_plan(
    task_id: str,
    topic: str,
    tokens: List[str],
    patterns: List[Dict[str, Any]],
    threshold: float,
    country_in: List[str],
    years_back: int,
    per_round_limit: int,
    seed_features: Dict[str, Any],
) -> Dict[str, Any]:
    seed_query_terms = _filter_seed_query_terms(seed_features.get("top_tokens", []))[:6]
    expanded = _expand_keywords(tokens + seed_query_terms)
    anchor_seed = _expand_keywords(tokens)
    anchor_terms = _dedup_keep_order(
        [
            t for t in anchor_seed
            if t not in STOPWORDS and t not in NOISE_QUERY_TERMS and t not in {"monitoring", "analysis", "model"}
        ]
    )[:8]
    cpc_prefix = _dedup_keep_order(seed_features.get("top_cpc", []) + _infer_cpc_prefix(tokens))
    ipc_prefix = _dedup_keep_order(seed_features.get("top_ipc", []))
    pub_from, pub_to = _date_yyyymmdd(years_back)
    recent_from = int(f"{max(1970, datetime.now().year - 2)}0101")

    high_value = [p for p in patterns if p.get("score", {}).get("total", 0) >= threshold]
    selected = high_value[:2] if high_value else patterns[:2]

    rounds: List[Dict[str, Any]] = []
    # Round 1: recall-first, prioritize recency and multilingual synonyms.
    rounds.append(
        _build_round(
            round_id="R1-recent-recall",
            intent="high recall for recent patents (scanner-guided)",
            limit=max(80, per_round_limit + 20),
            keywords_all=[],
            keywords_any=_dedup_keep_order(expanded[:20]),
            keywords_anchor_any=anchor_terms,
            ipc_prefix_any=ipc_prefix[:6],
            cpc_prefix_any=cpc_prefix[:6],
            country_in=country_in,
            pub_date_from=recent_from,
            pub_date_to=pub_to,
        )
    )

    # Round 2/3: pattern-guided retrieval. Keep soft filters (keywords_any) to avoid early over-filtering.
    for idx, p in enumerate(selected, start=2):
        comps = [str(c.get("name", "")).lower() for c in p.get("components", []) if str(c.get("name", "")).strip()]
        kw_any = _dedup_keep_order(comps + expanded[:16])
        rounds.append(
            _build_round(
                round_id=f"R{idx}-pattern-{p.get('pattern_id','X')}",
                intent=f"scanner high-value pattern retrieval (soft filter): {p.get('title','')}",
                limit=max(70, per_round_limit + 10),
                keywords_all=[],
                keywords_any=kw_any,
                keywords_anchor_any=anchor_terms,
                ipc_prefix_any=ipc_prefix[:6],
                cpc_prefix_any=cpc_prefix[:6],
                country_in=country_in,
                pub_date_from=pub_from,
                pub_date_to=pub_to,
            )
        )

    rounds.append(
        _build_round(
            round_id=f"R{len(rounds) + 1}-broad-recall",
            intent="validator-style broad recall with scanner evidence",
            limit=max(100, per_round_limit + 40),
            keywords_all=[],
            keywords_any=_dedup_keep_order(expanded[:16]),
            keywords_anchor_any=anchor_terms,
            ipc_prefix_any=ipc_prefix,
            cpc_prefix_any=cpc_prefix,
            country_in=country_in,
            pub_date_from=pub_from,
            pub_date_to=pub_to,
        )
    )

    if not rounds:
        raise ValueError("无法生成查询轮次，请补充 topic/keywords")

    return {
        "task_id": task_id,
        "topic": topic,
        "source": "google_patents_bigquery",
        "table": TABLE,
        "threshold": threshold,
        "query_rounds": rounds,
        "execution_policy": {
            "min_rounds": 2,
            "min_results": 20,
            "recent_from": recent_from,
            "min_recent_ratio": 0.30,
            "min_country_count": 1,
            "stop_after_quality_met": True,
        },
        "mapping_notes": [
            "JB-2 abstraction: pattern components are abstracted from seed evidence and topic tokens.",
            "JB-5 claim angles generated for all patterns; retrieval uses recall-first, then pattern-guided rounds.",
            "Execution layer must avoid early hard filtering and ensure quality quotas before stopping.",
            "Execution layer must auto-expand when quality quota is not met.",
        ],
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Build concept scan and query plan (scanner-style)")
    ap.add_argument("--topic", required=True)
    ap.add_argument("--keywords", default="")
    ap.add_argument("--task-id", required=True)
    ap.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    ap.add_argument("--years-back", type=int, default=8)
    ap.add_argument("--country-in", default="US,CN,WO,EP,JP,KR")
    ap.add_argument("--per-round-limit", type=int, default=60)
    ap.add_argument("--seed-raw", default="")
    ap.add_argument("--seed-retriever", default="")
    ap.add_argument("--concept-output", required=True)
    ap.add_argument("--plan-output", required=True)
    args = ap.parse_args()

    topic = _normalize_text(args.topic)
    keywords = _normalize_text(args.keywords)
    tokens = _extract_tokens(topic, keywords)
    countries = [x.strip().upper() for x in args.country_in.split(",") if x.strip()]

    seed_patents = _load_seed_patents(
        seed_raw=args.seed_raw.strip() or None,
        seed_retriever=args.seed_retriever.strip() or None,
    )
    seed_features = _extract_seed_features(seed_patents)

    # if no seed evidence, fallback to token-only pseudo seed.
    if not seed_patents:
        seed_features["top_tokens"] = _dedup_keep_order(tokens + _expand_keywords(tokens))[:20]

    patterns = _build_patterns(
        topic=topic,
        tokens=tokens,
        threshold=args.threshold,
        seed_patents=seed_patents,
        seed_features=seed_features,
    )
    high_value = [p for p in patterns if p.get("score", {}).get("total", 0) >= args.threshold]

    concept_scan = {
        "scan_metadata": {
            "scan_date": datetime.now().isoformat(),
            "input_type": "topic_keywords_with_seed_evidence" if seed_patents else "topic_keywords",
            "industry": "generic",
            "source": "zeelin-patent-retriever:build_query_plan(scanner-style)",
            "seed_sample_size": len(seed_patents),
        },
        "patterns": patterns,
        "summary": {
            "total_patterns": len(patterns),
            "high_value_patterns": len(high_value),
            "recommended_focus": high_value[0]["title"] if high_value else patterns[0]["title"],
        },
    }

    query_plan = _build_query_plan(
        task_id=args.task_id,
        topic=topic,
        tokens=tokens,
        patterns=patterns,
        threshold=args.threshold,
        country_in=countries,
        years_back=args.years_back,
        per_round_limit=args.per_round_limit,
        seed_features=seed_features,
    )

    concept_path = Path(args.concept_output).resolve()
    plan_path = Path(args.plan_output).resolve()
    concept_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.parent.mkdir(parents=True, exist_ok=True)

    concept_path.write_text(json.dumps(concept_scan, ensure_ascii=False, indent=2), encoding="utf-8")
    plan_path.write_text(json.dumps(query_plan, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "task_id": args.task_id,
                "concept_scan": str(concept_path),
                "query_plan": str(plan_path),
                "tokens": tokens,
                "seed_sample_size": len(seed_patents),
                "high_value_patterns": len(high_value),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
