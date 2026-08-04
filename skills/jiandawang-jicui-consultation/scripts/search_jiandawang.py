#!/usr/bin/env python3
"""检索技能内置的检答网集萃全文。

本脚本面向 Claude Code skill 调用，输入用户问题后，先根据术语映射扩展
检索词，再对内置 Markdown 问题块做本地全文检索，输出结构化候选结果。
脚本只使用 Python 标准库，避免技能依赖额外安装。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from build_index import (  # pylint: disable=import-error
    DEFAULT_BATCHES_DIR,
    REFERENCES_DIR,
    IssueRecord,
    collect_topic_terms,
    normalize_space,
    parse_all_documents,
    read_legal_term_map,
    split_terms,
)


FIELD_WEIGHTS = {
    "question_title": 9.0,
    "category": 5.0,
    "consult_content": 4.5,
    "answer_content": 3.0,
    "original_title": 2.5,
    "expert": 0.5,
}

GENERIC_TERMS = {
    "检察",
    "检察院",
    "检察机关",
    "案件",
    "问题",
    "规定",
    "处理",
    "办理",
    "如何",
    "是否",
    "能否",
    "可以",
    "应当",
    "法律",
    "相关",
    "咨询",
    "答疑",
    "集萃",
    "检答网",
    "检察日报",
}

BROAD_MATCH_TERMS = {
    "公益诉讼",
    "行政公益诉讼",
    "民事公益诉讼",
    "社会公共利益",
    "公共利益",
    "不特定多数人利益",
    "审查起诉",
}

QUERY_SPLIT_RE = re.compile(r"[\s,，。；;、？?！!：:（）()《》<>\[\]【】\"'“”‘’/|｜]+")


@dataclass(frozen=True)
class SearchTerm:
    """单个检索词及其来源。"""

    text: str
    source: str


@dataclass(frozen=True)
class SearchResult:
    """单个检索结果。"""

    record: IssueRecord
    score: float
    matched_terms: list[str]
    excerpt: str


def normalize_query(value: str) -> str:
    """规范化用户查询文本。

    Args:
        value: 用户输入的自然语言问题。

    Returns:
        清理空白后的查询文本。
    """
    return normalize_space(value.replace("\n", " "))


def add_unique_term(terms: list[SearchTerm], text: str, source: str) -> None:
    """向检索词列表追加去重后的术语。

    Args:
        terms: 已收集的检索词列表。
        text: 待追加术语。
        source: 术语来源说明。

    Returns:
        None。
    """
    term_text = normalize_space(text.strip("`'\" "))
    if len(term_text) < 2 or term_text in GENERIC_TERMS:
        return
    if any(term.text == term_text for term in terms):
        return
    terms.append(SearchTerm(term_text, source))


def extract_query_chunks(query: str) -> list[str]:
    """从用户问题中提取基础查询片段。

    Args:
        query: 规范化后的用户查询。

    Returns:
        适合参与检索的片段列表。
    """
    chunks: list[str] = []
    for chunk in QUERY_SPLIT_RE.split(query):
        text = normalize_space(chunk)
        if len(text) < 2 or text in GENERIC_TERMS:
            continue
        if len(text) > 18:
            chunks.extend(split_long_chunk(text))
        else:
            chunks.append(text)
    return chunks


def split_long_chunk(chunk: str) -> list[str]:
    """切分较长中文查询片段。

    Args:
        chunk: 连续无标点的长片段。

    Returns:
        切分后的片段列表。
    """
    useful_parts: list[str] = []
    connectors = ["后", "时", "但", "并", "和", "与", "或者", "以及", "因为", "导致"]
    pending_parts = [chunk]
    for connector in connectors:
        next_parts: list[str] = []
        for part in pending_parts:
            next_parts.extend(piece for piece in part.split(connector) if piece)
        pending_parts = next_parts
    for part in pending_parts:
        text = normalize_space(part)
        if 2 <= len(text) <= 18 and text not in GENERIC_TERMS:
            useful_parts.append(text)
    return useful_parts or [chunk[:18]]


def expand_search_terms(
    query: str,
    term_map: dict[str, list[str]],
    topic_terms: Iterable[str],
) -> list[SearchTerm]:
    """生成原始查询和法律术语扩展后的检索词。

    Args:
        query: 用户查询文本。
        term_map: 通俗表达到法律术语的映射。
        topic_terms: 内置主题词列表。

    Returns:
        有序去重后的检索词列表。
    """
    normalized_query = normalize_query(query)
    terms: list[SearchTerm] = []
    for source_term, target_terms in term_map.items():
        if source_term and source_term in normalized_query:
            add_unique_term(terms, source_term, "通俗表达")
            for target_term in target_terms:
                add_unique_term(terms, target_term, f"由“{source_term}”扩展")
    for topic_term in topic_terms:
        if topic_term in normalized_query:
            add_unique_term(terms, topic_term, "直接法律概念")
    for chunk in extract_query_chunks(normalized_query):
        add_unique_term(terms, chunk, "原始问题片段")
    return terms


def get_record_fields(record: IssueRecord) -> dict[str, str]:
    """返回可检索字段。

    Args:
        record: 问题记录。

    Returns:
        字段名到字段文本的映射。
    """
    return {
        "question_title": record.question_title,
        "category": record.category,
        "consult_content": record.consult_content,
        "answer_content": record.answer_content,
        "original_title": record.original_title,
        "expert": record.expert,
    }


def term_weight(term: SearchTerm) -> float:
    """计算单个检索词的权重。

    Args:
        term: 检索词。

    Returns:
        权重系数。
    """
    length_bonus = min(len(term.text) / 6.0, 2.0)
    source_bonus = 0.6 if term.source.startswith("由") else 0.0
    direct_bonus = 0.8 if term.source == "直接法律概念" else 0.0
    return 1.0 + length_bonus + source_bonus + direct_bonus


def count_term_occurrences(text: str, term: str) -> int:
    """统计术语在文本中的出现次数。

    Args:
        text: 被检索文本。
        term: 检索术语。

    Returns:
        出现次数。
    """
    if not text or not term:
        return 0
    return text.count(term)


def score_record(record: IssueRecord, terms: list[SearchTerm], query: str) -> tuple[float, list[str]]:
    """计算记录与查询的相关分。

    Args:
        record: 问题记录。
        terms: 扩展后的检索词。
        query: 原始用户查询。

    Returns:
        相关分和命中术语列表。
    """
    score = 0.0
    matched_terms: list[str] = []
    broad_term_score = 0.0
    narrow_term_count = 0
    fields = get_record_fields(record)
    normalized_query = normalize_query(query)

    for term in terms:
        term_score = 0.0
        for field_name, field_text in fields.items():
            occurrence_count = count_term_occurrences(field_text, term.text)
            if occurrence_count <= 0:
                continue
            capped_count = min(occurrence_count, 5)
            term_score += FIELD_WEIGHTS[field_name] * term_weight(term) * (1 + 0.12 * (capped_count - 1))
        if term_score <= 0:
            continue
        score += term_score
        matched_terms.append(term.text)
        if term.text in BROAD_MATCH_TERMS:
            broad_term_score += term_score
        else:
            narrow_term_count += 1

    if normalized_query and normalized_query in record.search_text:
        score += 18.0
    if len(set(matched_terms)) >= 2:
        score += 2.0 * len(set(matched_terms))
    if len(set(matched_terms)) == 1 and matched_terms[0] in {"公益诉讼", "不起诉", "抗诉", "逮捕"}:
        score *= 0.72
    if narrow_term_count == 0 and broad_term_score:
        score = min(score * 0.45, broad_term_score * 0.5)
    return round(score, 4), sorted(set(matched_terms), key=lambda item: (-len(item), item))


def make_excerpt(record: IssueRecord, matched_terms: list[str], max_length: int = 220) -> str:
    """根据命中词生成摘要片段。

    Args:
        record: 问题记录。
        matched_terms: 命中术语。
        max_length: 摘要最大长度。

    Returns:
        摘要片段。
    """
    source_text = normalize_space(record.search_text.replace("\n", " "))
    if not source_text:
        return ""
    first_index = -1
    for term in matched_terms:
        index = source_text.find(term)
        if index != -1 and (first_index == -1 or index < first_index):
            first_index = index
    if first_index == -1:
        return source_text[:max_length] + ("…" if len(source_text) > max_length else "")
    start = max(first_index - max_length // 3, 0)
    end = min(start + max_length, len(source_text))
    excerpt = source_text[start:end]
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(source_text) else ""
    return prefix + excerpt + suffix


def search_records(
    records: list[IssueRecord],
    terms: list[SearchTerm],
    query: str,
    min_score: float,
) -> list[SearchResult]:
    """检索并排序问题记录。

    Args:
        records: 问题记录列表。
        terms: 扩展后的检索词。
        query: 原始用户查询。
        min_score: 最小返回分数。

    Returns:
        按相关分降序排列的检索结果列表。
    """
    results: list[SearchResult] = []
    for record in records:
        score, matched_terms = score_record(record, terms, query)
        if score < min_score or not matched_terms:
            continue
        results.append(SearchResult(record, score, matched_terms, make_excerpt(record, matched_terms)))
    return sorted(
        results,
        key=lambda result: (
            -result.score,
            result.record.batch_number,
            result.record.question_number,
        ),
    )


def result_support_level(result: SearchResult) -> str:
    """判断检索结果的支撑强度。

    Args:
        result: 检索结果。

    Returns:
        `direct_candidate` 表示可进入全文核验；`weak` 表示仅宽泛主题命中。
    """
    matched_term_set = set(result.matched_terms)
    if matched_term_set and matched_term_set.issubset(BROAD_MATCH_TERMS):
        return "weak"
    return "direct_candidate"


def result_to_dict(result: SearchResult, include_block: bool = False) -> dict[str, object]:
    """把检索结果转换为 JSON 友好的字典。

    Args:
        result: 检索结果。
        include_block: 是否包含完整问题块。

    Returns:
        JSON 友好的结果字典。
    """
    record = result.record
    support_level = result_support_level(result)
    payload: dict[str, object] = {
        "batch_number": record.batch_number,
        "batch_label": record.batch_label,
        "question_number": record.question_number,
        "question_title": record.question_title,
        "publish_date": record.publish_date,
        "source_raw": record.source_raw,
        "citation": record.citation,
        "category": record.category,
        "expert": record.expert,
        "score": result.score,
        "support_level": support_level,
        "support_note": "仅宽泛主题命中，回答前需核验是否能直接支撑用户问题" if support_level == "weak" else "候选结果仍需读取完整问题块核验",
        "matched_terms": result.matched_terms,
        "excerpt": result.excerpt,
        "file": record.relative_file,
        "original_url": record.original_url,
    }
    if include_block:
        payload["question_block"] = record.question_block
    return payload


def build_json_payload(
    query: str,
    terms: list[SearchTerm],
    results: list[SearchResult],
    top_k: int,
    include_block: bool,
) -> dict[str, object]:
    """生成完整 JSON 输出对象。

    Args:
        query: 用户查询。
        terms: 扩展后的检索词。
        results: 已排序检索结果。
        top_k: 返回结果数量。
        include_block: 是否包含完整问题块。

    Returns:
        JSON 输出对象。
    """
    selected_results = results[:top_k]
    return {
        "query": query,
        "expanded_terms": [{"term": term.text, "source": term.source} for term in terms],
        "result_count": len(selected_results),
        "results": [result_to_dict(result, include_block=include_block) for result in selected_results],
        "notice": "未在检答网集萃中检索到相关内容" if not selected_results else "",
    }


def render_text_payload(payload: dict[str, object]) -> str:
    """渲染便于人工阅读的文本输出。

    Args:
        payload: JSON 输出对象。

    Returns:
        Markdown 风格文本。
    """
    lines = [f"查询：{payload['query']}", ""]
    expanded_terms = payload.get("expanded_terms", [])
    if expanded_terms:
        term_text = "；".join(f"{item['term']}（{item['source']}）" for item in expanded_terms)
        lines.extend([f"扩展检索词：{term_text}", ""])
    if not payload.get("results"):
        lines.append(str(payload["notice"]))
        return "\n".join(lines)
    for index, result in enumerate(payload["results"], start=1):
        lines.extend(
            [
                f"## 结果{index}：{result['question_title']}",
                "",
                f"- 引用：{result['citation']}",
                f"- 咨询类别：{result['category']}",
                f"- 解答专家：{result['expert']}",
                f"- 分数：{result['score']}",
                f"- 命中词：{'；'.join(result['matched_terms'])}",
                f"- 文件：`{result['file']}`",
                f"- 摘要：{result['excerpt']}",
                "",
            ]
        )
    return "\n".join(lines)


def run_search(
    query: str,
    batches_dir: Path,
    reference_dir: Path,
    min_score: float,
) -> tuple[list[SearchTerm], list[SearchResult]]:
    """执行完整检索流程。

    Args:
        query: 用户查询。
        batches_dir: 批次 Markdown 目录。
        reference_dir: references 目录。
        min_score: 最小返回分数。

    Returns:
        扩展检索词和检索结果。
    """
    term_map = read_legal_term_map(reference_dir)
    topic_terms = collect_topic_terms(term_map)
    terms = expand_search_terms(query, term_map, topic_terms)
    if not terms:
        for chunk in extract_query_chunks(normalize_query(query)):
            add_unique_term(terms, chunk, "原始问题片段")
    records = parse_all_documents(batches_dir=batches_dir, reference_dir=reference_dir)
    return terms, search_records(records, terms, query, min_score=min_score)


def parse_args() -> argparse.Namespace:
    """解析命令行参数。

    Args:
        无。

    Returns:
        argparse 解析结果。
    """
    parser = argparse.ArgumentParser(description="检索内置检答网集萃全文")
    parser.add_argument("--query", required=True, help="用户问题或检索词")
    parser.add_argument("--top-k", type=int, default=8, help="最多返回结果数")
    parser.add_argument("--min-score", type=float, default=4.0, help="最小相关分")
    parser.add_argument("--batches-dir", type=Path, default=DEFAULT_BATCHES_DIR, help="批次 Markdown 目录")
    parser.add_argument("--reference-dir", type=Path, default=REFERENCES_DIR, help="references 目录")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    parser.add_argument("--include-block", action="store_true", help="输出完整问题块")
    return parser.parse_args()


def main() -> int:
    """命令行入口函数。

    Args:
        无。

    Returns:
        进程退出码，0 表示成功。
    """
    args = parse_args()
    if args.top_k <= 0:
        print("--top-k 必须为正整数", file=sys.stderr)
        return 2
    try:
        terms, results = run_search(args.query, args.batches_dir, args.reference_dir, args.min_score)
        payload = build_json_payload(args.query, terms, results, args.top_k, args.include_block)
    except Exception as exc:  # noqa: BLE001 - 命令行入口需要明确报告所有失败原因。
        print(f"检索失败：{exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_text_payload(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
