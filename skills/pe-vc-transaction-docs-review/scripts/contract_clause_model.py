#!/usr/bin/env python3
"""Build and align conservative clause records from extracted contract paragraphs."""

from __future__ import annotations

import difflib
import hashlib
import re
from collections.abc import Iterable


CHINESE_DIGITS = {
    "零": 0,
    "〇": 0,
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
}
CHINESE_UNITS = {"十": 10, "百": 100, "千": 1000, "万": 10000}

ZH_ARTICLE_RE = re.compile(
    r"^\s*(?:#{1,6}\s*)?第\s*([零〇一二两三四五六七八九十百千万\d]+)\s*条"
    r"(?:\s*之\s*([零〇一二两三四五六七八九十百千万\d]+))?"
    r"\s*[：:、.．-]?\s*(.*)$",
    re.IGNORECASE,
)
EN_ARTICLE_RE = re.compile(
    r"^\s*(?:#{1,6}\s*)?(article|section|clause)\s+([A-Z0-9IVXLC]+(?:[.\-][A-Z0-9IVXLC]+)*)"
    r"\s*[：:、.．-]?\s*(.*)$",
    re.IGNORECASE,
)
DECIMAL_RE = re.compile(
    r"^\s*(?:#{1,6}\s*)?(\d+(?:\.\d+){0,5})\s*(?:[条款]\s*)?(?:[：:、.．-]\s*|\s+)(.+)$"
)
MARKDOWN_HEADING_RE = re.compile(r"^\s*(#{1,6})\s+(.+?)\s*$")


def normalize_text(value: object) -> str:
    text = str(value or "").replace("\u3000", " ").lower()
    text = re.sub(r"[“”‘’\"']", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def compact_text(value: object) -> str:
    return re.sub(r"[^0-9a-z\u3400-\u9fff%]+", "", normalize_text(value))


def chinese_number(value: str) -> int | None:
    value = value.strip()
    if not value:
        return None
    if value.isdigit():
        return int(value)
    if all(char in CHINESE_DIGITS for char in value):
        return int("".join(str(CHINESE_DIGITS[char]) for char in value))
    total = 0
    section = 0
    number = 0
    for char in value:
        if char in CHINESE_DIGITS:
            number = CHINESE_DIGITS[char]
        elif char in CHINESE_UNITS:
            unit = CHINESE_UNITS[char]
            if unit == 10000:
                section = (section + (number or 0)) * unit
                total += section
                section = 0
                number = 0
            else:
                section += (number or 1) * unit
                number = 0
        else:
            return None
    return total + section + number


def normalize_label(kind: str, raw: str, suffix: str | None = None) -> str:
    if kind == "zh_article":
        base = chinese_number(raw)
        if base is None:
            return f"article:{compact_text(raw)}"
        if suffix:
            suffix_number = chinese_number(suffix)
            suffix_value = str(suffix_number) if suffix_number is not None else compact_text(suffix)
            return f"article:{base}.{suffix_value}"
        return f"article:{base}"
    if kind == "decimal":
        return f"clause:{raw.strip('.')}"
    if kind == "en_article":
        return f"article:{raw.lower().strip('.')}"
    return f"heading:{compact_text(raw)[:80]}"


def detect_heading(text: str) -> dict[str, object] | None:
    match = ZH_ARTICLE_RE.match(text)
    if match:
        raw, suffix, title = match.groups()
        display = f"第{raw}条" + (f"之{suffix}" if suffix else "")
        return {
            "kind": "zh_article",
            "label": display,
            "normalized_label": normalize_label("zh_article", raw, suffix),
            "title": title.strip(),
            "level": 1,
        }
    match = EN_ARTICLE_RE.match(text)
    if match:
        word, raw, title = match.groups()
        return {
            "kind": "en_article",
            "label": f"{word.title()} {raw}",
            "normalized_label": normalize_label("en_article", raw),
            "title": title.strip(),
            "level": 1,
        }
    match = DECIMAL_RE.match(text)
    if match:
        raw, title = match.groups()
        return {
            "kind": "decimal",
            "label": raw,
            "normalized_label": normalize_label("decimal", raw),
            "title": title.strip(),
            "level": raw.count(".") + 1,
        }
    match = MARKDOWN_HEADING_RE.match(text)
    if match:
        markers, title = match.groups()
        return {
            "kind": "heading",
            "label": title.strip(),
            "normalized_label": normalize_label("heading", title),
            "title": title.strip(),
            "level": len(markers),
        }
    return None


def paragraph_location(paragraph: dict) -> str:
    if paragraph.get("page"):
        block = paragraph.get("page_block", paragraph.get("paragraph"))
        return f"page {paragraph['page']}, block {block}"
    if paragraph.get("source_part"):
        part_paragraph = paragraph.get("part_paragraph", paragraph.get("paragraph"))
        return f"{paragraph['source_part']}, paragraph {part_paragraph}"
    return f"paragraph {paragraph.get('paragraph', '?')}"


def _clause_record(
    index: int,
    heading: dict[str, object] | None,
    paragraphs: list[dict],
) -> dict[str, object]:
    texts = [str(paragraph.get("text", "")).strip() for paragraph in paragraphs]
    text = "\n\n".join(value for value in texts if value)
    if heading:
        label = str(heading["label"])
        normalized_label = str(heading["normalized_label"])
        title = str(heading.get("title", ""))
        kind = str(heading["kind"])
        level = int(heading["level"])
    else:
        label = f"P{index}"
        normalized_label = f"paragraph:{index}"
        title = texts[0][:80] if texts else ""
        kind = "paragraph_fallback"
        level = 0
    normalized = normalize_text(text)
    semantic_parts = texts
    if heading:
        semantic_parts = [str(heading.get("title", "")).strip(), *texts[1:]]
    semantic_text = "\n\n".join(value for value in semantic_parts if value)
    normalized_semantic = normalize_text(semantic_text)
    return {
        "clause_id": f"C{index:04d}",
        "sequence": index,
        "kind": kind,
        "level": level,
        "label": label,
        "normalized_label": normalized_label,
        "title": title,
        "start_location": paragraph_location(paragraphs[0]),
        "end_location": paragraph_location(paragraphs[-1]),
        "paragraph_start": paragraphs[0].get("paragraph"),
        "paragraph_end": paragraphs[-1].get("paragraph"),
        "paragraphs": paragraphs,
        "text": text,
        "normalized_text": normalized,
        "semantic_text": semantic_text,
        "normalized_semantic_text": normalized_semantic,
        "content_fingerprint": hashlib.sha256(normalized_semantic.encode("utf-8")).hexdigest(),
    }


def build_clauses(paragraphs: Iterable[dict]) -> list[dict[str, object]]:
    source = [paragraph for paragraph in paragraphs if str(paragraph.get("text", "")).strip()]
    if not source:
        return []
    clauses: list[dict[str, object]] = []
    pending: list[dict] = []
    pending_heading: dict[str, object] | None = None
    for paragraph in source:
        heading = detect_heading(str(paragraph.get("text", "")))
        if heading and pending:
            clauses.append(_clause_record(len(clauses) + 1, pending_heading, pending))
            pending = []
        if heading:
            pending_heading = heading
        elif not pending:
            pending_heading = None
        pending.append(paragraph)
        if pending_heading is None:
            clauses.append(_clause_record(len(clauses) + 1, None, pending))
            pending = []
    if pending:
        clauses.append(_clause_record(len(clauses) + 1, pending_heading, pending))
    return clauses


def text_similarity(left: object, right: object) -> float:
    a = compact_text(left)
    b = compact_text(right)
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()


def _pair_record(
    change_type: str,
    prior: list[dict[str, object]],
    current: list[dict[str, object]],
    method: str,
    similarity: float,
) -> dict[str, object]:
    prior_labels = [str(item["label"]) for item in prior]
    current_labels = [str(item["label"]) for item in current]
    flags: list[str] = []
    if prior and current:
        if [item["normalized_label"] for item in prior] != [item["normalized_label"] for item in current]:
            flags.append("renumbered")
        if min(item["sequence"] for item in prior) != min(item["sequence"] for item in current):
            flags.append("moved")
    confidence = "high" if method in {"exact_label", "exact_content"} else "medium"
    if method in {"unmatched", "positional_fallback"}:
        confidence = "low"
    return {
        "type": change_type,
        "alignment_method": method,
        "confidence": confidence,
        "similarity": round(similarity, 6),
        "flags": flags,
        "prior_clause_ids": [item["clause_id"] for item in prior],
        "current_clause_ids": [item["clause_id"] for item in current],
        "prior_labels": prior_labels,
        "current_labels": current_labels,
        "prior_locations": [item["start_location"] for item in prior],
        "current_locations": [item["start_location"] for item in current],
        "prior_text": "\n\n".join(str(item["text"]) for item in prior),
        "current_text": "\n\n".join(str(item["text"]) for item in current),
    }


def _unique_index(
    records: list[dict[str, object]],
    field: str,
    *,
    exclude_kinds: set[str] | None = None,
) -> dict[str, int]:
    positions: dict[str, list[int]] = {}
    for index, record in enumerate(records):
        if exclude_kinds and str(record.get("kind")) in exclude_kinds:
            continue
        value = str(record.get(field, ""))
        if value:
            positions.setdefault(value, []).append(index)
    return {value: indexes[0] for value, indexes in positions.items() if len(indexes) == 1}


def _consecutive_groups(indexes: set[int], max_size: int = 3) -> Iterable[list[int]]:
    ordered = sorted(indexes)
    for start_position, start in enumerate(ordered):
        group = [start]
        for candidate in ordered[start_position + 1 :]:
            if candidate != group[-1] + 1 or len(group) >= max_size:
                break
            group.append(candidate)
            if len(group) >= 2:
                yield list(group)


def align_clauses(
    prior: list[dict[str, object]],
    current: list[dict[str, object]],
    fuzzy_threshold: float = 0.62,
    group_threshold: float = 0.72,
) -> list[dict[str, object]]:
    paired_prior: set[int] = set()
    paired_current: set[int] = set()
    pairs: list[tuple[list[int], list[int], str, float]] = []

    prior_labels = _unique_index(prior, "normalized_label", exclude_kinds={"paragraph_fallback"})
    current_labels = _unique_index(current, "normalized_label", exclude_kinds={"paragraph_fallback"})
    for label in sorted(set(prior_labels) & set(current_labels), key=lambda value: prior_labels[value]):
        i = prior_labels[label]
        j = current_labels[label]
        similarity = text_similarity(prior[i]["semantic_text"], current[j]["semantic_text"])
        pairs.append(([i], [j], "exact_label", similarity))
        paired_prior.add(i)
        paired_current.add(j)

    prior_fingerprints = _unique_index(prior, "content_fingerprint")
    current_fingerprints = _unique_index(current, "content_fingerprint")
    for fingerprint in set(prior_fingerprints) & set(current_fingerprints):
        i = prior_fingerprints[fingerprint]
        j = current_fingerprints[fingerprint]
        if i in paired_prior or j in paired_current:
            continue
        pairs.append(([i], [j], "exact_content", 1.0))
        paired_prior.add(i)
        paired_current.add(j)

    unmatched_prior = set(range(len(prior))) - paired_prior
    unmatched_current = set(range(len(current))) - paired_current

    group_candidates: list[tuple[float, str, list[int], list[int]]] = []
    for i in unmatched_prior:
        for group in _consecutive_groups(unmatched_current):
            combined = "\n\n".join(str(current[j]["semantic_text"]) for j in group)
            score = text_similarity(prior[i]["semantic_text"], combined)
            if score >= group_threshold:
                group_candidates.append((score, "split", [i], group))
    for j in unmatched_current:
        for group in _consecutive_groups(unmatched_prior):
            combined = "\n\n".join(str(prior[i]["semantic_text"]) for i in group)
            score = text_similarity(combined, current[j]["semantic_text"])
            if score >= group_threshold:
                group_candidates.append((score, "merged", group, [j]))
    for score, method, prior_group, current_group in sorted(group_candidates, reverse=True):
        if any(index in paired_prior for index in prior_group) or any(index in paired_current for index in current_group):
            continue
        pairs.append((prior_group, current_group, method, score))
        paired_prior.update(prior_group)
        paired_current.update(current_group)

    fuzzy_candidates: list[tuple[float, int, int]] = []
    for i in set(range(len(prior))) - paired_prior:
        for j in set(range(len(current))) - paired_current:
            content_score = text_similarity(prior[i]["semantic_text"], current[j]["semantic_text"])
            prior_title = str(prior[i].get("title", ""))
            current_title = str(current[j].get("title", ""))
            title_score = text_similarity(prior_title, current_title) if prior_title and current_title else 0.0
            distance = abs(int(prior[i]["sequence"]) - int(current[j]["sequence"]))
            sequence_score = max(0.0, 1.0 - distance / max(len(prior), len(current), 1))
            score = 0.75 * content_score + 0.15 * title_score + 0.10 * sequence_score
            if score >= fuzzy_threshold:
                fuzzy_candidates.append((score, i, j))
    for score, i, j in sorted(fuzzy_candidates, reverse=True):
        if i in paired_prior or j in paired_current:
            continue
        pairs.append(([i], [j], "fuzzy_content", score))
        paired_prior.add(i)
        paired_current.add(j)

    remaining_prior = set(range(len(prior))) - paired_prior
    remaining_current = set(range(len(current))) - paired_current
    for index in sorted(remaining_prior & remaining_current):
        if prior[index]["kind"] != "paragraph_fallback" or current[index]["kind"] != "paragraph_fallback":
            continue
        score = text_similarity(prior[index]["semantic_text"], current[index]["semantic_text"])
        pairs.append(([index], [index], "positional_fallback", score))
        paired_prior.add(index)
        paired_current.add(index)

    results: list[dict[str, object]] = []
    for prior_indexes, current_indexes, method, similarity in pairs:
        prior_group = [prior[index] for index in prior_indexes]
        current_group = [current[index] for index in current_indexes]
        if method == "split":
            change_type = "split"
        elif method == "merged":
            change_type = "merged"
        else:
            if len(prior_group) != len(current_group):
                raise ValueError("non-split clause alignment groups must have equal lengths")
            same_text = all(
                left["normalized_semantic_text"] == right["normalized_semantic_text"]
                for left, right in zip(prior_group, current_group)
            )
            same_label = [item["normalized_label"] for item in prior_group] == [
                item["normalized_label"] for item in current_group
            ]
            same_position = [item["sequence"] for item in prior_group] == [item["sequence"] for item in current_group]
            if same_text and same_label and same_position:
                change_type = "unchanged"
            elif same_text and not same_label:
                change_type = "renumbered"
            elif same_text and not same_position:
                change_type = "moved"
            else:
                change_type = "modified"
        results.append(_pair_record(change_type, prior_group, current_group, method, similarity))

    for i in set(range(len(prior))) - paired_prior:
        results.append(_pair_record("deleted", [prior[i]], [], "unmatched", 0.0))
    for j in set(range(len(current))) - paired_current:
        results.append(_pair_record("added", [], [current[j]], "unmatched", 0.0))

    def sort_key(record: dict[str, object]) -> tuple[int, int]:
        prior_ids = record["prior_clause_ids"]
        current_ids = record["current_clause_ids"]
        prior_number = int(str(prior_ids[0])[1:]) if prior_ids else 10**9
        current_number = int(str(current_ids[0])[1:]) if current_ids else 10**9
        return min(prior_number, current_number), current_number

    return sorted(results, key=sort_key)
