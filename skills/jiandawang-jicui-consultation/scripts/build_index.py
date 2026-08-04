#!/usr/bin/env python3
"""生成检答网集萃技能索引。

本脚本只使用 Python 标准库，负责解析技能内置的 Markdown 全文，
生成 `references/index.md`，并输出结构校验信息。索引是给技能快速缩小
检索范围使用的辅助文件，不替代全文检索。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
REFERENCES_DIR = SKILL_DIR / "references"
DEFAULT_BATCHES_DIR = REFERENCES_DIR / "batches"
DEFAULT_INDEX_PATH = REFERENCES_DIR / "index.md"

CHINESE_DIGIT_VALUES = {
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

FIELD_NAMES = ("问题标题", "咨询类别", "咨询内容", "解答专家", "解答内容")

DEFAULT_TOPIC_TERMS = [
    "认罪认罚",
    "不起诉",
    "存疑不起诉",
    "相对不起诉",
    "附条件不起诉",
    "抗诉",
    "逮捕",
    "审查逮捕",
    "刑事拘留",
    "羁押",
    "羁押期限",
    "国家赔偿",
    "刑事赔偿",
    "公益诉讼",
    "社会公共利益",
    "行政公益诉讼",
    "民事公益诉讼",
    "刑事执行检察",
    "控告申诉检察",
    "未成年人检察",
    "侦查监督",
    "补充侦查",
    "继续侦查",
    "事实不清",
    "证据不足",
    "排除合理怀疑",
    "以危险方法危害公共安全罪",
    "妨害安全驾驶",
    "抢夺方向盘",
    "公共交通工具",
    "交通肇事罪",
    "宣告死亡",
    "非法证据排除",
    "自首",
    "立功",
    "共同犯罪",
    "犯罪数额",
    "追诉时效",
    "量刑建议",
    "速裁程序",
    "简易程序",
    "检察建议",
    "民事行政检察",
    "行政检察",
    "民事检察",
    "环境污染",
    "食品药品安全",
    "个人信息",
    "网络犯罪",
]


@dataclass
class IssueRecord:
    """单个检答网问题块的结构化记录。"""

    batch_number: int
    batch_label: str
    question_number: int
    question_title: str
    publish_date: str
    source_raw: str
    original_title: str
    original_url: str
    category: str
    consult_content: str
    expert: str
    answer_content: str
    relative_file: str
    question_block: str
    keywords: list[str] = field(default_factory=list)

    @property
    def citation(self) -> str:
        """返回用户要求的固定引用格式。"""
        return f"检答网集萃第{self.batch_number}批·问题{self.question_number}（检察日报，{self.publish_date}）"

    @property
    def search_text(self) -> str:
        """返回用于全文检索的合并文本。"""
        parts = [
            self.original_title,
            self.question_title,
            self.category,
            self.consult_content,
            self.expert,
            self.answer_content,
        ]
        return "\n".join(part for part in parts if part)


def normalize_space(value: str) -> str:
    """规范化空白字符。

    Args:
        value: 原始字符串。

    Returns:
        替换全角空格和连续空白后的字符串。
    """
    value = value.replace("\xa0", " ").replace(" ", " ").replace("　", " ")
    return re.sub(r"[ \t]+", " ", value).strip()


def normalize_multiline(value: str) -> str:
    """规范化多行文本，保留段落边界。

    Args:
        value: 原始多行字符串。

    Returns:
        清理空白行和行内连续空白后的多行字符串。
    """
    lines = [normalize_space(line) for line in value.splitlines()]
    cleaned_lines = [line for line in lines if line]
    return "\n".join(cleaned_lines).strip()


def markdown_cell(value: str, max_length: int = 120) -> str:
    """生成安全的 Markdown 表格单元格文本。

    Args:
        value: 原始单元格内容。
        max_length: 单元格最大显示长度。

    Returns:
        转义竖线并截断后的单行文本。
    """
    compact_value = normalize_space(value.replace("\n", " "))
    compact_value = compact_value.replace("|", "\\|")
    if len(compact_value) > max_length:
        return compact_value[: max_length - 1] + "…"
    return compact_value


def chinese_to_int(value: str) -> int:
    """将中文数字转换为整数。

    Args:
        value: 中文数字或阿拉伯数字，例如“一百四十”或“140”。

    Returns:
        转换后的整数。

    Raises:
        ValueError: 无法解析数字时抛出。
    """
    text = value.strip()
    if text.isdigit():
        return int(text)
    if not text:
        raise ValueError("空中文数字无法解析")

    total = 0
    current_digit = 0
    unit_values = {"十": 10, "百": 100, "千": 1000}
    for char in text:
        if char in CHINESE_DIGIT_VALUES:
            current_digit = CHINESE_DIGIT_VALUES[char]
            continue
        if char in unit_values:
            unit_value = unit_values[char]
            total += (current_digit or 1) * unit_value
            current_digit = 0
            continue
        raise ValueError(f"无法解析中文数字字符：{char}")
    return total + current_digit


def extract_batch_number(value: str) -> int:
    """从批次标签中提取阿拉伯数字批次号。

    Args:
        value: 包含“第X批”的文件名、标题或标签。

    Returns:
        批次号。

    Raises:
        ValueError: 未找到批次标签时抛出。
    """
    match = re.search(r"第([一二三四五六七八九十百千万零〇两\d]+)批", value)
    if not match:
        raise ValueError(f"未找到批次标签：{value}")
    return chinese_to_int(match.group(1))


def make_batch_label(batch_number: int) -> str:
    """将阿拉伯数字批次号转换为显示标签。

    Args:
        batch_number: 批次号。

    Returns:
        形如“第140批”的显示标签。
    """
    return f"第{batch_number}批"


def extract_first_field(text: str, field_name: str) -> str:
    """提取文章级单行字段。

    Args:
        text: Markdown 全文。
        field_name: 字段名，例如“发布日期”。

    Returns:
        字段值；未找到时返回空字符串。
    """
    pattern = rf"^{re.escape(field_name)}\s*[：:]\s*(.*)$"
    match = re.search(pattern, text, flags=re.MULTILINE)
    return normalize_space(match.group(1)) if match else ""


def extract_field_block(block: str, field_name: str) -> str:
    """从问题块中提取指定字段。

    Args:
        block: 单个 `## 问题N` Markdown 块。
        field_name: 需要提取的字段名。

    Returns:
        字段内容；未找到时返回空字符串。
    """
    lines = block.splitlines()
    field_pattern = re.compile(rf"^{re.escape(field_name)}\s*[：:]\s*(.*)$")
    stop_pattern = re.compile(rf"^({'|'.join(FIELD_NAMES)})\s*[：:]")
    collected: list[str] = []
    collecting = False

    for line in lines:
        stripped_line = line.strip()
        if not collecting:
            match = field_pattern.match(stripped_line)
            if match:
                collected.append(match.group(1))
                collecting = True
            continue
        if stripped_line.startswith("## "):
            break
        if stop_pattern.match(stripped_line):
            break
        collected.append(stripped_line)
    return normalize_multiline("\n".join(collected))


def split_issue_blocks(markdown_text: str) -> list[tuple[int, str, str]]:
    """按 Markdown 二级问题标题切分问题块。

    Args:
        markdown_text: 单个批次 Markdown 全文。

    Returns:
        元组列表，每项为“问题号、标题、完整问题块”。
    """
    pattern = re.compile(
        r"^##\s*问题\s*([一二三四五六七八九十百千万零〇两\d]+)\s*[：:]\s*(.*)$",
        flags=re.MULTILINE,
    )
    matches = list(pattern.finditer(markdown_text))
    blocks: list[tuple[int, str, str]] = []

    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown_text)
        question_number = chinese_to_int(match.group(1))
        heading_title = normalize_space(match.group(2))
        question_block = markdown_text[start:end].strip()
        blocks.append((question_number, heading_title, question_block))
    return blocks


def read_legal_term_map(reference_dir: Path = REFERENCES_DIR) -> dict[str, list[str]]:
    """读取通俗表达与法律术语映射。

    Args:
        reference_dir: skill 的 references 目录。

    Returns:
        映射字典；文件不存在时返回空字典。
    """
    map_path = reference_dir / "legal-term-map.md"
    if not map_path.exists():
        return {}

    term_map: dict[str, list[str]] = {}
    for raw_line in map_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "->" not in line:
            continue
        left_text, right_text = line.split("->", 1)
        source_terms = split_terms(left_text)
        target_terms = split_terms(right_text)
        for source_term in source_terms:
            if source_term:
                term_map[source_term] = target_terms
    return term_map


def split_terms(value: str) -> list[str]:
    """按常见中文分隔符拆分术语。

    Args:
        value: 包含多个术语的字符串。

    Returns:
        去重后的术语列表。
    """
    candidates = re.split(r"[、,，;；/|｜\s]+", value)
    terms: list[str] = []
    seen_terms: set[str] = set()
    for candidate in candidates:
        term = normalize_space(candidate.strip("`'\" "))
        if term and term not in seen_terms:
            terms.append(term)
            seen_terms.add(term)
    return terms


def collect_topic_terms(term_map: dict[str, list[str]]) -> list[str]:
    """合并默认主题词和术语映射中的词。

    Args:
        term_map: 通俗表达与法律术语映射。

    Returns:
        按长度降序排列的主题词列表。
    """
    terms: set[str] = set(DEFAULT_TOPIC_TERMS)
    for source_term, target_terms in term_map.items():
        terms.add(source_term)
        terms.update(target_terms)
    return sorted((term for term in terms if len(term) >= 2), key=lambda item: (-len(item), item))


def extract_keywords(record: IssueRecord, topic_terms: Iterable[str]) -> list[str]:
    """从问题记录中提取主题关键词。

    Args:
        record: 单个问题记录。
        topic_terms: 候选主题词列表。

    Returns:
        在标题、咨询内容或解答内容中命中的关键词。
    """
    search_text = record.search_text
    keywords: list[str] = []
    for term in topic_terms:
        if term in search_text and term not in keywords:
            keywords.append(term)
        if len(keywords) >= 12:
            break
    return keywords


def parse_document(markdown_path: Path, topic_terms: Iterable[str]) -> list[IssueRecord]:
    """解析单个批次 Markdown 文件。

    Args:
        markdown_path: Markdown 文件路径。
        topic_terms: 候选主题词列表。

    Returns:
        该文件中的问题记录列表。

    Raises:
        ValueError: 批次号无法解析时抛出。
    """
    markdown_text = markdown_path.read_text(encoding="utf-8")
    heading_match = re.search(r"^#\s*检答网集萃（([^）]+)）", markdown_text, flags=re.MULTILINE)
    batch_label_source = heading_match.group(1) if heading_match else markdown_path.stem
    batch_number = extract_batch_number(batch_label_source)
    relative_file = markdown_path.relative_to(SKILL_DIR).as_posix()

    original_title = extract_first_field(markdown_text, "原始标题")
    publish_date = extract_first_field(markdown_text, "发布日期")
    source_raw = extract_first_field(markdown_text, "来源")
    original_url = extract_first_field(markdown_text, "原始链接")
    records: list[IssueRecord] = []

    for question_number, heading_title, question_block in split_issue_blocks(markdown_text):
        question_title = extract_field_block(question_block, "问题标题") or heading_title
        record = IssueRecord(
            batch_number=batch_number,
            batch_label=make_batch_label(batch_number),
            question_number=question_number,
            question_title=question_title,
            publish_date=publish_date,
            source_raw=source_raw,
            original_title=original_title,
            original_url=original_url,
            category=extract_field_block(question_block, "咨询类别"),
            consult_content=extract_field_block(question_block, "咨询内容"),
            expert=extract_field_block(question_block, "解答专家"),
            answer_content=extract_field_block(question_block, "解答内容"),
            relative_file=relative_file,
            question_block=question_block,
        )
        record.keywords = extract_keywords(record, topic_terms)
        records.append(record)
    return records


def parse_all_documents(
    batches_dir: Path = DEFAULT_BATCHES_DIR,
    reference_dir: Path = REFERENCES_DIR,
) -> list[IssueRecord]:
    """解析所有批次 Markdown 文件。

    Args:
        batches_dir: 批次 Markdown 所在目录。
        reference_dir: references 目录，用于读取术语映射。

    Returns:
        按批次号和问题号排序的问题记录列表。
    """
    term_map = read_legal_term_map(reference_dir)
    topic_terms = collect_topic_terms(term_map)
    records: list[IssueRecord] = []
    for markdown_path in sorted(batches_dir.glob("*.md")):
        records.extend(parse_document(markdown_path, topic_terms))
    return sorted(records, key=lambda record: (record.batch_number, record.question_number))


def validate_records(records: list[IssueRecord], markdown_count: int) -> dict[str, object]:
    """校验解析结果完整性。

    Args:
        records: 已解析的问题记录列表。
        markdown_count: Markdown 文件数量。

    Returns:
        包含统计和问题清单的字典。
    """
    batch_numbers = sorted({record.batch_number for record in records})
    expected_batches = set(range(1, max(batch_numbers, default=0) + 1))
    actual_batches = set(batch_numbers)
    citations = [record.citation for record in records]
    duplicate_citations = sorted({citation for citation in citations if citations.count(citation) > 1})

    return {
        "markdown_count": markdown_count,
        "batch_count": len(batch_numbers),
        "issue_count": len(records),
        "first_batch": min(batch_numbers) if batch_numbers else None,
        "last_batch": max(batch_numbers) if batch_numbers else None,
        "missing_batches": sorted(expected_batches - actual_batches),
        "missing_dates": [record.citation for record in records if not record.publish_date],
        "missing_sources": [record.citation for record in records if not record.source_raw],
        "missing_titles": [record.citation for record in records if not record.question_title],
        "missing_answers": [record.citation for record in records if not record.answer_content],
        "duplicate_citations": duplicate_citations,
    }


def group_records_by_batch(records: list[IssueRecord]) -> dict[int, list[IssueRecord]]:
    """按批次号分组问题记录。

    Args:
        records: 问题记录列表。

    Returns:
        批次号到问题记录列表的映射。
    """
    grouped_records: dict[int, list[IssueRecord]] = defaultdict(list)
    for record in records:
        grouped_records[record.batch_number].append(record)
    return dict(sorted(grouped_records.items()))


def build_overview_section(records: list[IssueRecord], validation: dict[str, object]) -> list[str]:
    """生成索引概览段落。

    Args:
        records: 问题记录列表。
        validation: 校验统计结果。

    Returns:
        Markdown 行列表。
    """
    dates = sorted(record.publish_date for record in records if record.publish_date)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# 检答网集萃第1–140批索引",
        "",
        "> 本索引由 `scripts/build_index.py` 根据技能内置 Markdown 全文自动生成，用于快速了解批次分布和缩小检索范围；正式回答仍应以全文检索结果为准。",
        "",
        "## 语料概览",
        "",
        f"- 语料名称：检答网集萃",
        f"- Markdown 文件数：{validation['markdown_count']}",
        f"- 批次数：{validation['batch_count']}",
        f"- 问题块数：{validation['issue_count']}",
        f"- 起始发布日期：{dates[0] if dates else '未识别'}",
        f"- 最新发布日期：{dates[-1] if dates else '未识别'}",
        f"- 生成时间：{generated_at}",
        f"- 生成脚本：`scripts/build_index.py`",
        "",
    ]
    problem_items = [
        ("缺失批次", validation["missing_batches"]),
        ("缺失发布日期", validation["missing_dates"]),
        ("缺失来源", validation["missing_sources"]),
        ("缺失问题标题", validation["missing_titles"]),
        ("缺失解答内容", validation["missing_answers"]),
        ("重复引用", validation["duplicate_citations"]),
    ]
    warnings = [(name, items) for name, items in problem_items if items]
    if warnings:
        lines.extend(["## 结构校验提示", ""])
        for name, items in warnings:
            preview = "；".join(str(item) for item in list(items)[:10])
            suffix = "……" if len(items) > 10 else ""
            lines.append(f"- {name}：{preview}{suffix}")
        lines.append("")
    return lines


def build_batch_section(records: list[IssueRecord]) -> list[str]:
    """生成按批次索引表。

    Args:
        records: 问题记录列表。

    Returns:
        Markdown 行列表。
    """
    lines = [
        "## 按批次索引",
        "",
        "| 批次 | 发布日期 | 来源 | 原始标题 | 问题数 | 咨询类别 | 问题标题摘要 | 文件 |",
        "|---|---|---|---|---:|---|---|---|",
    ]
    for batch_number, batch_records in group_records_by_batch(records).items():
        first_record = batch_records[0]
        categories = "；".join(sorted({record.category for record in batch_records if record.category}))
        titles = "；".join(record.question_title for record in batch_records)
        lines.append(
            "| "
            f"{make_batch_label(batch_number)} | "
            f"{first_record.publish_date} | "
            f"{markdown_cell(first_record.source_raw, 40)} | "
            f"{markdown_cell(first_record.original_title, 80)} | "
            f"{len(batch_records)} | "
            f"{markdown_cell(categories, 80)} | "
            f"{markdown_cell(titles, 120)} | "
            f"`{first_record.relative_file}` |"
        )
    lines.append("")
    return lines


def build_issue_section(records: list[IssueRecord]) -> list[str]:
    """生成按问题索引表。

    Args:
        records: 问题记录列表。

    Returns:
        Markdown 行列表。
    """
    lines = [
        "## 按问题索引",
        "",
        "| 批次 | 问题号 | 发布日期 | 咨询类别 | 问题标题 | 解答专家 | 关键词 | 文件 |",
        "|---|---:|---|---|---|---|---|---|",
    ]
    for record in records:
        keyword_text = "；".join(record.keywords[:8])
        lines.append(
            "| "
            f"{record.batch_label} | "
            f"{record.question_number} | "
            f"{record.publish_date} | "
            f"{markdown_cell(record.category, 40)} | "
            f"{markdown_cell(record.question_title, 100)} | "
            f"{markdown_cell(record.expert, 40)} | "
            f"{markdown_cell(keyword_text, 100)} | "
            f"`{record.relative_file}` |"
        )
    lines.append("")
    return lines


def build_category_section(records: list[IssueRecord]) -> list[str]:
    """生成按咨询类别分布索引。

    Args:
        records: 问题记录列表。

    Returns:
        Markdown 行列表。
    """
    category_map: dict[str, list[IssueRecord]] = defaultdict(list)
    for record in records:
        category_map[record.category or "未标注咨询类别"].append(record)

    lines = ["## 按咨询类别分布", ""]
    for category, category_records in sorted(category_map.items(), key=lambda item: (-len(item[1]), item[0])):
        lines.append(f"### {category}（{len(category_records)}）")
        lines.append("")
        for record in category_records:
            lines.append(f"- {record.batch_label}·问题{record.question_number}：{record.question_title}")
        lines.append("")
    return lines


def build_keyword_section(records: list[IssueRecord]) -> list[str]:
    """生成主题关键词索引。

    Args:
        records: 问题记录列表。

    Returns:
        Markdown 行列表。
    """
    keyword_map: dict[str, list[IssueRecord]] = defaultdict(list)
    for record in records:
        for keyword in record.keywords:
            keyword_map[keyword].append(record)

    lines = ["## 主题关键词索引", ""]
    for keyword, keyword_records in sorted(keyword_map.items(), key=lambda item: (-len(item[1]), item[0])):
        lines.append(f"### {keyword}（{len(keyword_records)}）")
        lines.append("")
        for record in keyword_records[:30]:
            lines.append(f"- {record.batch_label}·问题{record.question_number}：{record.question_title}")
        if len(keyword_records) > 30:
            lines.append(f"- ……另有 {len(keyword_records) - 30} 条")
        lines.append("")
    return lines


def write_index(records: list[IssueRecord], output_path: Path, validation: dict[str, object]) -> None:
    """写入 Markdown 索引文件。

    Args:
        records: 问题记录列表。
        output_path: 索引输出路径。
        validation: 校验统计结果。

    Returns:
        None。
    """
    sections: list[str] = []
    sections.extend(build_overview_section(records, validation))
    sections.extend(build_batch_section(records))
    sections.extend(build_issue_section(records))
    sections.extend(build_category_section(records))
    sections.extend(build_keyword_section(records))
    sections.extend(
        [
            "## 使用说明",
            "",
            "- 本索引用于快速定位可能相关批次；最终答复应继续读取全文问题块或运行全文检索脚本。",
            "- 引用任何答疑内容时，应使用脚本生成的固定格式：`检答网集萃第X批·问题Y（检察日报，YYYY-MM-DD）`。",
            "- 未检索到可支撑内容时，不得凭模型记忆补写检答网观点、专家姓名或问题编号。",
            "",
        ]
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(sections), encoding="utf-8")


def build_index(batches_dir: Path, output_path: Path, reference_dir: Path) -> dict[str, object]:
    """生成索引并返回校验统计。

    Args:
        batches_dir: 批次 Markdown 所在目录。
        output_path: 索引输出路径。
        reference_dir: references 目录。

    Returns:
        校验统计字典。
    """
    markdown_count = len(list(batches_dir.glob("*.md")))
    records = parse_all_documents(batches_dir=batches_dir, reference_dir=reference_dir)
    validation = validate_records(records, markdown_count)
    write_index(records, output_path, validation)
    return validation


def parse_args() -> argparse.Namespace:
    """解析命令行参数。

    Args:
        无。

    Returns:
        argparse 解析结果。
    """
    parser = argparse.ArgumentParser(description="生成检答网集萃本地索引")
    parser.add_argument("--batches-dir", type=Path, default=DEFAULT_BATCHES_DIR, help="批次 Markdown 目录")
    parser.add_argument("--output", type=Path, default=DEFAULT_INDEX_PATH, help="索引 Markdown 输出路径")
    parser.add_argument("--reference-dir", type=Path, default=REFERENCES_DIR, help="references 目录")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出校验结果")
    parser.add_argument("--strict", action="store_true", help="发现结构问题时以非零状态退出")
    return parser.parse_args()


def main() -> int:
    """命令行入口函数。

    Args:
        无。

    Returns:
        进程退出码，0 表示成功。
    """
    args = parse_args()
    try:
        validation = build_index(args.batches_dir, args.output, args.reference_dir)
    except Exception as exc:  # noqa: BLE001 - 命令行入口需要明确报告所有失败原因。
        print(f"索引生成失败：{exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(validation, ensure_ascii=False, indent=2))
    else:
        print(f"索引已生成：{args.output}")
        print(f"Markdown 文件数：{validation['markdown_count']}")
        print(f"批次数：{validation['batch_count']}")
        print(f"问题块数：{validation['issue_count']}")

    has_warnings = any(
        validation[key]
        for key in (
            "missing_batches",
            "missing_dates",
            "missing_sources",
            "missing_titles",
            "missing_answers",
            "duplicate_citations",
        )
    )
    return 1 if args.strict and has_warnings else 0


if __name__ == "__main__":
    raise SystemExit(main())
