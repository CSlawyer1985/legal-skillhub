#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 1 shadow event ledger for Zhilu complaint operations.

Pure local computation only: this module never calls DWS and never updates the
production ledger. It normalizes inbound message envelopes, computes stable
fingerprints, classifies events, ranks supplied case candidates, and appends an
immutable decision record to JSONL.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

EVENT_TYPES = {
    "NEW_CASE", "SUPPLEMENT", "RECONTACT", "PROGRESS",
    "CLOSURE_CANDIDATE", "DUPLICATE", "UNKNOWN",
}
TERMINAL_STATUSES = {"SHADOW_RECORDED", "REVIEW_REQUIRED", "IGNORED", "FAILED"}
SUPPLEMENT_WORDS = ("补充", "追加", "新证据", "凭证", "截图", "订单", "流水", "证明")
RECONTACT_WORDS = ("催办", "再次反馈", "重复投诉", "同一个投诉", "再次来件")
PROGRESS_WORDS = ("正在处理", "处理中", "已联系", "待回复", "已提交退款", "预计到账", "后续反馈", "先核实")
CLOSURE_WORDS = ("已退款", "退款成功", "已到账", "处理完成", "已完成", "不支持退款", "确认收到")
NEGATIVE_OR_PENDING_WORDS = ("未退款", "尚未", "没有到账", "未到账", "预计", "待", "正在", "处理中", "提交退款", "原则上")


def stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def normalize_text(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value or ""))
    text = text.replace("\u3000", " ")
    text = re.sub(r"\s+", " ", text).strip().lower()
    return text


def normalize_phone(value: Any) -> str:
    digits = re.sub(r"\D", "", str(value or ""))
    if digits.startswith("0086"):
        digits = digits[4:]
    elif digits.startswith("86") and len(digits) == 13:
        digits = digits[2:]
    return digits if len(digits) == 11 else ""


def normalize_amount(value: Any) -> str:
    try:
        return f"{float(str(value).replace(',', '').replace('¥', '').strip()):.2f}"
    except (TypeError, ValueError):
        return ""


def first_nonempty(mapping: Dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = mapping.get(key)
        if value not in (None, ""):
            return str(value)
    return ""


def extract_features(event: Dict[str, Any]) -> Dict[str, str]:
    ocr = event.get("ocr_result") or event.get("payload", {}).get("ocr_result") or {}
    text = " ".join(filter(None, [
        first_nonempty(event, "text", "raw_text"),
        first_nonempty(event.get("payload", {}), "raw_text"),
        first_nonempty(ocr, "投诉内容", "content", "备注"),
    ]))
    order_match = re.search(r"(?:订单号|交易号|订单|交易)[：:\s#]*([A-Za-z0-9_-]{5,})", text, re.I)
    case_no = first_nonempty(ocr, "投诉编号", "编号", "case_no")
    return {
        "case_no": normalize_text(case_no),
        "phone": normalize_phone(first_nonempty(ocr, "联系方式", "手机号", "contact", "phone") or text),
        "complainant": normalize_text(first_nonempty(ocr, "投诉人", "complainant")),
        "subject": normalize_text(first_nonempty(ocr, "被投诉主体", "subject")),
        "complaint_type": normalize_text(first_nonempty(ocr, "投诉类型", "type")),
        "amount": normalize_amount(first_nonempty(ocr, "诉求金额", "金额", "amount")),
        "order_no": normalize_text(first_nonempty(ocr, "订单号", "交易号", "order_no") or (order_match.group(1) if order_match else "")),
        "content": normalize_text(text),
    }


def transport_fingerprint(event: Dict[str, Any]) -> str:
    source = event.get("source", {})
    parts = [
        first_nonempty(source, "channel"),
        first_nonempty(source, "conversation_id", "openConversationId"),
        first_nonempty(source, "message_id", "messageId"),
        first_nonempty(source, "resource_id", "resourceId", "media_id", "mediaId"),
        str(source.get("attachment_index", 0)),
    ]
    return sha256_text("|".join(parts))


def content_fingerprint(features: Dict[str, str]) -> str:
    keys = ("phone", "complainant", "subject", "order_no", "amount", "content")
    return sha256_text("|".join(features.get(key, "") for key in keys))


def build_event_id(event: Dict[str, Any], fingerprints: Dict[str, str]) -> str:
    return "evt_" + sha256_text(f"{fingerprints['transport']}|{fingerprints['content']}")[:24]


def classify_event(text: str, has_attachment: bool, has_candidates: bool) -> Tuple[str, float, List[str]]:
    normalized = normalize_text(text)
    reasons: List[str] = []
    if any(word in normalized for word in PROGRESS_WORDS):
        reasons.append("命中过程/未完成表达")
        return "PROGRESS", 0.90, reasons
    if any(word in normalized for word in CLOSURE_WORDS):
        if any(word in normalized for word in NEGATIVE_OR_PENDING_WORDS):
            reasons.append("结案词与否定/未完成表达并存")
            return "PROGRESS", 0.75, reasons
        reasons.append("命中明确结案候选表达")
        return "CLOSURE_CANDIDATE", 0.85, reasons
    if any(word in normalized for word in SUPPLEMENT_WORDS):
        reasons.append("命中补充材料表达")
        return "SUPPLEMENT", 0.85, reasons
    if any(word in normalized for word in RECONTACT_WORDS):
        reasons.append("命中再次来件/催办表达")
        return "RECONTACT", 0.85, reasons
    if has_attachment and has_candidates:
        reasons.append("含附件且存在候选工单")
        return "SUPPLEMENT", 0.60, reasons
    if has_attachment:
        reasons.append("含附件但无候选工单")
        return "NEW_CASE", 0.60, reasons
    reasons.append("缺少明确分类信号")
    return "UNKNOWN", 0.30, reasons


def candidate_features(case: Dict[str, Any]) -> Dict[str, str]:
    return {
        "case_no": normalize_text(first_nonempty(case, "投诉编号", "编号", "标题", "case_no")),
        "phone": normalize_phone(first_nonempty(case, "联系方式", "contact", "phone")),
        "complainant": normalize_text(first_nonempty(case, "投诉人", "complainant")),
        "subject": normalize_text(first_nonempty(case, "被投诉主体", "subject")),
        "complaint_type": normalize_text(first_nonempty(case, "投诉类型", "type")),
        "amount": normalize_amount(first_nonempty(case, "诉求金额", "金额", "amount")),
        "order_no": normalize_text(first_nonempty(case, "订单号", "交易号", "order_no")),
        "content": normalize_text(first_nonempty(case, "投诉内容", "content")),
        "source_media": normalize_text(first_nonempty(case, "原始媒体指纹", "source_media")),
    }


def token_similarity(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    a = set(re.findall(r"[\w\u4e00-\u9fff]+", left))
    b = set(re.findall(r"[\w\u4e00-\u9fff]+", right))
    return len(a & b) / len(a | b) if a and b else 0.0


def score_candidate(features: Dict[str, str], event: Dict[str, Any], case: Dict[str, Any]) -> Dict[str, Any]:
    cf = candidate_features(case)
    score = 0
    details: Dict[str, int] = {}
    conflicts: List[str] = []
    anchors: List[str] = []

    def add(name: str, points: int) -> None:
        nonlocal score
        score += points
        details[name] = points

    if features["case_no"] and cf["case_no"]:
        if features["case_no"] == cf["case_no"]:
            add("case_no", 100); anchors.append("case_no")
        else:
            conflicts.append("case_no_conflict")
            return {"score": -999, "details": details, "conflicts": conflicts, "strong_anchors": anchors, "case": case}

    quoted = normalize_text(first_nonempty(event.get("source", {}), "quoted_case_id", "quoted_record_id"))
    case_id = normalize_text(first_nonempty(case, "_recordId", "recordId", "case_id"))
    if quoted and case_id and quoted == case_id:
        add("quoted_source", 70); anchors.append("quoted_source")

    if features["order_no"] and cf["order_no"]:
        if features["order_no"] == cf["order_no"]:
            add("order_no", 65); anchors.append("order_no")
        else:
            add("order_no_conflict", -70); conflicts.append("order_no_conflict")

    event_media = normalize_text(first_nonempty(event.get("payload", {}), "source_media", "blob_sha256"))
    if event_media and cf["source_media"] and event_media == cf["source_media"]:
        add("source_media", 45); anchors.append("source_media")

    if features["phone"] and cf["phone"]:
        if features["phone"] == cf["phone"]:
            add("phone", 45)
        else:
            add("phone_conflict", -60); conflicts.append("phone_conflict")
    if features["complainant"] and features["complainant"] == cf["complainant"]:
        add("complainant", 15)
    if features["subject"] and cf["subject"]:
        if features["subject"] == cf["subject"]:
            add("subject", 15)
        else:
            add("subject_conflict", -30); conflicts.append("subject_conflict")
    if features["complaint_type"] and features["complaint_type"] == cf["complaint_type"]:
        add("complaint_type", 8)
    if features["amount"] and features["amount"] == cf["amount"]:
        add("amount", 5)
    similarity = token_similarity(features["content"], cf["content"])
    if similarity >= 0.60:
        add("content_similarity", 10)
    elif similarity >= 0.35:
        add("content_similarity", 5)

    text = features["content"]
    if any(word in text for word in SUPPLEMENT_WORDS + RECONTACT_WORDS):
        add("explicit_relation_word", 10)

    return {
        "score": min(100, score),
        "details": details,
        "conflicts": conflicts,
        "strong_anchors": anchors,
        "case": case,
    }


def decide_match(ranked: List[Dict[str, Any]], cfg: Dict[str, Any]) -> Dict[str, Any]:
    if not ranked:
        return {"decision": "UNMATCHED", "reason": "无候选工单", "score": 0, "runner_up_score": 0}
    top = ranked[0]
    runner = ranked[1]["score"] if len(ranked) > 1 else -999
    score = top["score"]
    gap = score - runner
    match_cfg = cfg["match"]
    hard_conflicts = {"case_no_conflict", "order_no_conflict", "phone_conflict"}
    veto = bool(hard_conflicts & set(top["conflicts"]))
    strong = bool(set(top["strong_anchors"]) & set(match_cfg["strong_anchors"]))
    if not veto and score >= match_cfg["auto_link_score"] and gap >= match_cfg["minimum_gap"] and strong:
        decision, reason = "AUTO_LINK", "高置信且具备强锚点"
    elif score >= match_cfg["manual_review_score"]:
        decision, reason = "MANUAL_REVIEW", "分数可疑或缺少强锚点/差距不足"
    else:
        decision, reason = "UNMATCHED", "匹配分不足"
    return {
        "decision": decision, "reason": reason, "score": score,
        "runner_up_score": runner if runner >= 0 else 0,
        "gap": gap, "top": top,
    }


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_known_events(ledger_path: Path) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, List[Dict[str, Any]]], Dict[str, List[Dict[str, Any]]]]:
    by_transport: Dict[str, Dict[str, Any]] = {}
    by_content: Dict[str, List[Dict[str, Any]]] = {}
    by_blob: Dict[str, List[Dict[str, Any]]] = {}
    if not ledger_path.exists():
        return by_transport, by_content, by_blob
    with ledger_path.open(encoding="utf-8") as fh:
        for line in fh:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("processing", {}).get("status") not in TERMINAL_STATUSES:
                continue
            transport = row.get("fingerprints", {}).get("transport")
            content = row.get("fingerprints", {}).get("content")
            blob = row.get("fingerprints", {}).get("blob_sha256")
            if transport:
                by_transport[transport] = row
            if content:
                by_content.setdefault(content, []).append(row)
            if blob:
                by_blob.setdefault(blob, []).append(row)
    return by_transport, by_content, by_blob


def has_meaningful_content(features: Dict[str, str]) -> bool:
    return any(features.get(key) for key in ("case_no", "phone", "complainant", "subject", "order_no", "amount", "content"))


def process_event(event: Dict[str, Any], cases: List[Dict[str, Any]], cfg: Dict[str, Any], known_keys: set[str]) -> Dict[str, Any]:
    features = extract_features(event)
    fingerprints = {
        "transport": transport_fingerprint(event),
        "content": content_fingerprint(features),
        "blob_sha256": first_nonempty(event.get("payload", {}), "blob_sha256"),
    }
    event_id = build_event_id(event, fingerprints)
    if fingerprints["transport"] in known_keys:
        event_type, class_conf, class_reasons = "DUPLICATE", 1.0, ["传输指纹已进入终态"]
        match = {"decision": "DUPLICATE", "score": 100, "runner_up_score": 0, "reason": "幂等重复"}
        status = "IGNORED"
    else:
        ranked = sorted((score_candidate(features, event, case) for case in cases), key=lambda x: x["score"], reverse=True)
        match = decide_match(ranked, cfg)
        event_type, class_conf, class_reasons = classify_event(
            features["content"],
            bool(event.get("payload", {}).get("blob_sha256") or event.get("source", {}).get("resource_id")),
            bool(ranked),
        )
        status = "REVIEW_REQUIRED" if match["decision"] != "AUTO_LINK" else "SHADOW_RECORDED"
        if event_type == "CLOSURE_CANDIDATE":
            status = "REVIEW_REQUIRED"
            class_reasons.append("Phase 1禁止自动结案")
    source = dict(event.get("source", {}))
    return {
        "event_id": event_id,
        "schema_version": 1,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "payload": {
            "kind": event.get("payload", {}).get("kind", "unknown"),
            "blob_sha256": fingerprints["blob_sha256"],
            "raw_text": first_nonempty(event.get("payload", {}), "raw_text") or first_nonempty(event, "text", "raw_text"),
            "ocr_result": event.get("ocr_result") or event.get("payload", {}).get("ocr_result") or {},
        },
        "features": features,
        "fingerprints": fingerprints,
        "classification": {"event_type": event_type, "confidence": class_conf, "reasons": class_reasons},
        "match": {
            "decision": match["decision"], "reason": match["reason"],
            "score": match["score"], "runner_up_score": match.get("runner_up_score", 0),
            "gap": match.get("gap", 0),
            "record_id": first_nonempty(match.get("top", {}).get("case", {}), "_recordId", "recordId"),
            "case_no": first_nonempty(match.get("top", {}).get("case", {}), "投诉编号", "编号", "标题", "case_no"),
            "details": match.get("top", {}).get("details", {}),
            "conflicts": match.get("top", {}).get("conflicts", []),
            "strong_anchors": match.get("top", {}).get("strong_anchors", []),
        },
        "processing": {
            "mode": "shadow", "status": status, "write_main_ledger": False,
            "attempt_count": 1, "last_error": None,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 1 shadow ledger entries without external writes")
    parser.add_argument("--events", required=True, help="JSON array or {events:[...]} input")
    parser.add_argument("--cases", required=True, help="JSON array or DWS result projected to case dictionaries")
    parser.add_argument("--config", required=True, help="shadow_config.json")
    parser.add_argument("--ledger", help="override JSONL ledger path")
    parser.add_argument("--out", help="optional JSON array output of this batch")
    args = parser.parse_args()

    cfg = load_json(Path(args.config))
    events_data = load_json(Path(args.events))
    cases_data = load_json(Path(args.cases))
    events = events_data.get("events", []) if isinstance(events_data, dict) else events_data
    cases = cases_data.get("records", []) if isinstance(cases_data, dict) else cases_data
    if not isinstance(events, list) or not isinstance(cases, list):
        raise SystemExit("events and cases must be JSON arrays")

    ledger_path = Path(args.ledger or cfg.get("paths", {}).get("ledger", "shadow_event_ledger.jsonl"))
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = ledger_path.with_suffix(ledger_path.suffix + ".lock")
    lock_path.touch(exist_ok=True)
    rows: List[Dict[str, Any]] = []
    new_rows: List[Dict[str, Any]] = []
    with lock_path.open("r+") as lock_fh:
        fcntl.flock(lock_fh.fileno(), fcntl.LOCK_EX)
        known_transport, known_content, known_blob = load_known_events(ledger_path)
        for event in events:
            features = extract_features(event)
            key = transport_fingerprint(event)
            content_key = content_fingerprint(features)
            blob_key = first_nonempty(event.get("payload", {}), "blob_sha256")
            prior = known_transport.get(key)
            duplicate_reason = "传输指纹已进入终态" if prior else ""
            if not prior and blob_key and cfg.get("enable_content_dedup", False):
                candidates = known_blob.get(blob_key, [])
                if candidates:
                    prior = candidates[-1]
                    duplicate_reason = "文件SHA-256已进入终态"
            if not prior and has_meaningful_content(features) and cfg.get("enable_content_dedup", False):
                candidates = known_content.get(content_key, [])
                if candidates:
                    prior = candidates[-1]
                    duplicate_reason = "业务内容指纹已进入终态"
            if prior:
                rows.append({
                    "event_id": prior.get("event_id"),
                    "schema_version": prior.get("schema_version", 1),
                    "observed_at": datetime.now(timezone.utc).isoformat(),
                    "source": event.get("source", {}),
                    "fingerprints": {"transport": key, "content": content_key, "blob_sha256": blob_key},
                    "classification": {"event_type": "DUPLICATE", "confidence": 1.0, "reasons": [duplicate_reason]},
                    "match": {"decision": "DUPLICATE", "score": 100, "runner_up_score": 0, "reason": "幂等重复"},
                    "processing": {"mode": "shadow", "status": "IGNORED", "write_main_ledger": False, "attempt_count": 1, "last_error": None},
                })
                continue
            row = process_event(event, cases, cfg, set(known_transport))
            rows.append(row)
            new_rows.append(row)
            known_transport[key] = row
            known_content.setdefault(content_key, []).append(row)
            if blob_key:
                known_blob.setdefault(blob_key, []).append(row)
        if new_rows:
            with ledger_path.open("a", encoding="utf-8") as fh:
                for row in new_rows:
                    fh.write(stable_json(row) + "\n")
                fh.flush()
    if args.out:
        Path(args.out).write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = {
        "mode": "shadow", "events": len(rows), "appended": len(new_rows), "ledger": str(ledger_path),
        "review_required": sum(r["processing"]["status"] == "REVIEW_REQUIRED" for r in rows),
        "shadow_recorded": sum(r["processing"]["status"] == "SHADOW_RECORDED" for r in rows),
        "duplicates": sum(r["classification"]["event_type"] == "DUPLICATE" for r in rows),
        "main_ledger_writes": 0,
    }
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
