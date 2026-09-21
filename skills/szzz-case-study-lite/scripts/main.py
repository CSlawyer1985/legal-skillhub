#!/usr/bin/env python3
"""SZZZ Case Study Lite 本地案例研究总控脚本。"""

import argparse
import hashlib
import json
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
MAIN_SCRIPT_PATH = SKILL_ROOT / "scripts" / "main.py"
REQUIREMENTS_PATH = SKILL_ROOT / "scripts" / "requirements.txt"
ANALYZER_PROMPT_PATH = SKILL_ROOT / "prompts" / "analyzer-logic.md"
MASTER_PROMPT_PATH = SKILL_ROOT / "prompts" / "master-report-logic.md"

try:
    import pdfplumber
    from docx import Document
except ImportError:
    print("缺少依赖库，请先运行：")
    print(
        shlex.join(
            [sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS_PATH)]
        )
    )
    raise SystemExit(1)


RESULTS_DIR = "law_analysis_results"
SOURCE_DIR = "source_texts"
CASES_DIR = "individual_cases"
STATUS_FILE = "status.json"
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc"}
MIN_TEXT_LENGTH = 50
SUMMARY_BATCH_SIZE = 3


class ExtractionError(RuntimeError):
    pass


def format_command(command, *args):
    return shlex.join(
        [sys.executable, str(MAIN_SCRIPT_PATH), command]
        + [str(argument) for argument in args]
    )


def results_path(base_path):
    return Path(base_path) / RESULTS_DIR


def source_dir_path(base_path):
    return results_path(base_path) / SOURCE_DIR


def cases_dir_path(base_path):
    return results_path(base_path) / CASES_DIR


def status_path(base_path):
    return results_path(base_path) / STATUS_FILE


def ensure_dirs(base_path):
    source_dir_path(base_path).mkdir(parents=True, exist_ok=True)
    cases_dir_path(base_path).mkdir(parents=True, exist_ok=True)


def new_status():
    return {
        "schema_version": 1,
        "current_step": 1,
        "files_scanned": [],
        "pending_incremental": [],
        "last_incremental_batch": [],
        "excluded_files": [],
        "duplicate_files": [],
        "dedup_map": {},
        "processed_files": 0,
    }


def load_status(base_path):
    path = status_path(base_path)
    if not path.exists():
        return new_status()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"无法读取项目状态文件：{path}：{exc}") from exc
    baseline = new_status()
    baseline.update(data)
    return baseline


def save_status(base_path, status):
    ensure_dirs(base_path)
    path = status_path(base_path)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(status, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporary.replace(path)


def standardize_case_num(raw_num):
    return re.sub(r"[^0-9a-zA-Z\u4e00-\u9fa5]", "", str(raw_num or "")).strip()


def extract_case_number(content):
    match = re.search(
        r"[(（]\s*\d{4}\s*[)）]\s*"
        r"[\u4e00-\u9fa5A-Za-z0-9\s\-./]{1,50}?号",
        str(content or "")[:3000],
    )
    return match.group(0).strip() if match else ""


def extract_document_type(content, filename=""):
    probe = f"{filename}\n{str(content or '')[:3000]}"
    known_types = [
        "民事判决书",
        "民事裁定书",
        "民事调解书",
        "民事决定书",
        "执行裁定书",
        "执行通知书",
        "执行决定书",
        "行政判决书",
        "行政裁定书",
        "刑事判决书",
        "刑事裁定书",
        "仲裁裁决书",
    ]
    for document_type in known_types:
        if document_type in probe:
            return document_type
    match = re.search(
        r"([\u4e00-\u9fa5]{0,6}(?:判决书|裁定书|调解书|决定书|通知书|裁决书))",
        probe,
    )
    return match.group(1) if match else "未识别文书类型"


def is_reference_case_summary(content, filename=""):
    probe = f"{filename}\n{str(content or '')[:3000]}"
    markers = [
        "典型案例",
        "参考案例",
        "指导性案例",
        "案例通报",
        "案例总结",
        "裁判要旨",
        "案例要旨",
        "公报案例",
        "案例评析",
    ]
    return any(marker in probe for marker in markers)


def is_execution_objection_ruling(content, filename=""):
    probe = f"{filename}\n{str(content or '')[:5000]}"
    markers = [
        "执行异议",
        "案外人异议",
        "案外人执行异议",
        "申请执行人执行异议",
        "执行复议",
        "复议申请",
    ]
    return any(marker in probe for marker in markers)


def should_include_source(content, filename, document_type):
    if document_type in {"民事判决书", "民事裁定书"}:
        return True, document_type, document_type
    if document_type == "执行裁定书" and is_execution_objection_ruling(
        content, filename
    ):
        return True, document_type, "执行异议相关执行裁定书"
    if document_type == "未识别文书类型" and is_reference_case_summary(
        content, filename
    ):
        return True, "典型案例总结", "非标准格式典型案例总结"
    return False, document_type, "非纳入范围裁判文书或非典型案例总结"


def build_dedup_key(case_number, document_type):
    normalized_case = standardize_case_num(case_number)
    normalized_type = standardize_case_num(document_type)
    return f"{normalized_case}::{normalized_type}" if normalized_case else ""


def content_similarity(text_a, text_b, sample_len=3000, shingle_len=5):
    def shingles(value):
        normalized = re.sub(r"\s+", "", str(value or ""))[:sample_len]
        if len(normalized) < shingle_len:
            return {normalized} if normalized else set()
        return {
            normalized[index : index + shingle_len]
            for index in range(len(normalized) - shingle_len + 1)
        }

    left = shingles(text_a)
    right = shingles(text_b)
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def extract_pdf(file_path):
    pages = []
    try:
        with pdfplumber.open(file_path) as document:
            for page_number, page in enumerate(document.pages, 1):
                page_text = (page.extract_text() or "").strip()
                if page_text:
                    pages.append(f"[第 {page_number} 页]\n{page_text}")
    except Exception as exc:
        raise ExtractionError(f"无法读取 PDF：{exc}") from exc
    return "\n\n".join(pages)


def extract_docx(file_path):
    try:
        document = Document(file_path)
    except Exception as exc:
        raise ExtractionError(f"无法读取 DOCX：{exc}") from exc
    paragraphs = [paragraph.text.strip() for paragraph in document.paragraphs]
    return "\n".join(text for text in paragraphs if text)


def extract_doc(file_path):
    textutil = shutil.which("textutil")
    if textutil:
        result = subprocess.run(
            [textutil, "-convert", "txt", "-stdout", str(file_path)],
            capture_output=True,
            check=False,
        )
        if result.returncode == 0:
            return result.stdout.decode("utf-8", errors="replace").strip()
        textutil_error = result.stderr.decode("utf-8", errors="replace").strip()
    else:
        textutil_error = "未检测到 textutil"

    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if soffice:
        with tempfile.TemporaryDirectory(prefix="szzz-lite-doc-") as temp_dir:
            result = subprocess.run(
                [
                    soffice,
                    "--headless",
                    "--convert-to",
                    "docx",
                    "--outdir",
                    temp_dir,
                    str(file_path),
                ],
                capture_output=True,
                check=False,
            )
            converted = list(Path(temp_dir).glob("*.docx"))
            if result.returncode == 0 and converted:
                return extract_docx(converted[0])
            soffice_error = result.stderr.decode("utf-8", errors="replace").strip()
    else:
        soffice_error = "未检测到 LibreOffice"

    raise ExtractionError(
        "无法转换旧式 DOC。"
        f"textutil：{textutil_error or '转换失败'}；"
        f"LibreOffice：{soffice_error or '转换失败'}。"
    )


def extract_text(file_path):
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return extract_pdf(file_path)
    if suffix == ".docx":
        return extract_docx(file_path)
    if suffix == ".doc":
        return extract_doc(file_path)
    raise ExtractionError(f"不支持的文件格式：{suffix}")


def find_parent_project(base_path):
    base = Path(base_path).resolve()
    for parent in base.parents:
        if (parent / RESULTS_DIR / STATUS_FILE).exists():
            return parent
    return None


def scan_source_files(base_path):
    base = Path(base_path)
    files = []
    for path in base.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        try:
            relative_parts = path.relative_to(base).parts
        except ValueError:
            continue
        if RESULTS_DIR in relative_parts:
            continue
        files.append(path)
    return sorted(files, key=lambda path: str(path).casefold())


def build_output_stems(files, base_path):
    counts = {}
    base = Path(base_path)
    for path in files:
        relative = path.relative_to(base)
        key = (str(relative.parent).casefold(), path.stem.casefold())
        counts[key] = counts.get(key, 0) + 1
    result = {}
    for path in files:
        relative = path.relative_to(base)
        key = (str(relative.parent).casefold(), path.stem.casefold())
        result[path] = (
            f"{path.stem}_{path.suffix.lower().lstrip('.')}"
            if counts[key] > 1
            else path.stem
        )
    return result


def raw_path_for_source(base_path, source_path, output_stem):
    relative = source_path.relative_to(Path(base_path))
    return (
        source_dir_path(base_path)
        / relative.parent
        / f"{output_stem}-raw.md"
    )


def read_raw_record(record):
    path = Path(record.get("path", ""))
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def write_dedup_report(base_path, duplicates, excluded, failures):
    if not duplicates and not excluded and not failures:
        return
    path = results_path(base_path) / "dedup_report.txt"
    lines = [
        "=== 去重、纳入范围与提取报告 ===",
        f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"重复排除：{len(duplicates)} 份",
        f"范围排除：{len(excluded)} 份",
        f"提取失败：{len(failures)} 份",
        "",
    ]
    if duplicates:
        lines.append("## 重复文件")
        for index, item in enumerate(duplicates, 1):
            lines.extend(
                [
                    f"[{index}] {item['source_file']}",
                    f"    保留：{item['kept']}",
                    f"    原因：{item['reason']}",
                ]
            )
        lines.append("")
    if excluded:
        lines.append("## 非处理范围文件")
        for index, item in enumerate(excluded, 1):
            lines.extend(
                [
                    f"[{index}] {item['source_file']}",
                    f"    文书类型：{item['doc_type']}",
                    f"    原因：{item['reason']}",
                ]
            )
        lines.append("")
    if failures:
        lines.append("## 提取失败文件")
        for index, item in enumerate(failures, 1):
            lines.extend(
                [
                    f"[{index}] {item['source_file']}",
                    f"    原因：{item['reason']}",
                ]
            )
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def command_init(base_path, force=False):
    base = Path(base_path).expanduser().resolve()
    if not base.is_dir():
        print(f"❌ 项目目录不存在：{base}")
        return 1

    if not force:
        parent_project = find_parent_project(base)
        if parent_project:
            print("【父项目探测器】当前目录属于已有案例项目。")
            print(f"父项目：{parent_project}")
            print(
                "请改为运行："
                f"{format_command('init', parent_project)}"
            )
            print("确需独立建库时可增加 --force。")
            return 2

    was_existing_project = status_path(base).exists()
    ensure_dirs(base)
    status = load_status(base)
    found_files = scan_source_files(base)
    output_stems = build_output_stems(found_files, base)

    all_known_records = (
        status.get("files_scanned", [])
        + status.get("pending_incremental", [])
        + status.get("excluded_files", [])
        + status.get("duplicate_files", [])
    )
    known_sources = {
        str(Path(record.get("source_file", "")).resolve())
        for record in all_known_records
        if record.get("source_file")
    }
    dedup_map = dict(status.get("dedup_map", {}))
    comparison_records = [
        record
        for record in (
            status.get("files_scanned", [])
            + status.get("pending_incremental", [])
        )
        if not record.get("has_standard_case_num")
    ]

    new_records = []
    duplicates = []
    excluded = []
    failures = []

    for source_file in found_files:
        if str(source_file.resolve()) in known_sources:
            continue

        output_path = raw_path_for_source(
            base, source_file, output_stems[source_file]
        )
        try:
            content = extract_text(source_file).strip()
        except ExtractionError as exc:
            failures.append(
                {"source_file": str(source_file), "reason": str(exc)}
            )
            continue
        if not content:
            failures.append(
                {
                    "source_file": str(source_file),
                    "reason": "未提取到正文，可能是扫描件或文件损坏",
                }
            )
            continue

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        if len(content) < MIN_TEXT_LENGTH:
            print(
                f"⚠️ {source_file.name} 仅提取到 {len(content)} 个字符，"
                "建议人工核对。"
            )

        document_type = extract_document_type(content, source_file.name)
        include, document_type, include_reason = should_include_source(
            content, source_file.name, document_type
        )
        case_number = extract_case_number(content)
        has_standard_case_num = bool(case_number)
        case_label = case_number or output_stems[source_file]
        relative = source_file.relative_to(base)
        record = {
            "path": str(output_path),
            "source_file": str(source_file),
            "case_raw": case_label,
            "doc_type": document_type,
            "sub_folder": str(relative.parent) if str(relative.parent) != "." else "",
            "has_standard_case_num": has_standard_case_num,
        }

        if not include:
            record["reason"] = include_reason
            excluded.append(record)
            continue

        if has_standard_case_num:
            dedup_key = build_dedup_key(case_number, document_type)
        else:
            digest = hashlib.sha256(
                re.sub(r"\s+", "", content).encode("utf-8")
            ).hexdigest()[:24]
            dedup_key = f"content::{digest}"
        record["dedup_key"] = dedup_key

        if dedup_key in dedup_map:
            duplicates.append(
                {
                    "source_file": str(source_file),
                    "kept": dedup_map[dedup_key],
                    "reason": "案号与文书类型相同" if has_standard_case_num else "正文完全相同",
                }
            )
            continue

        similar_record = None
        similarity = 0.0
        if not has_standard_case_num:
            for existing_record in comparison_records + new_records:
                if existing_record.get("has_standard_case_num"):
                    continue
                candidate_text = read_raw_record(existing_record)
                score = content_similarity(content, candidate_text)
                if score > 0.7:
                    similar_record = existing_record
                    similarity = score
                    break
        if similar_record:
            duplicates.append(
                {
                    "source_file": str(source_file),
                    "kept": similar_record.get("source_file")
                    or similar_record.get("path"),
                    "reason": f"无标准案号且正文相似度为 {similarity:.0%}",
                }
            )
            continue

        dedup_map[dedup_key] = str(source_file)
        new_records.append(record)

    status["dedup_map"] = dedup_map
    if excluded:
        status.setdefault("excluded_files", []).extend(excluded)
    if duplicates:
        status.setdefault("duplicate_files", []).extend(duplicates)
    status["dedup_stats"] = {
        "raw_files_found": len(found_files),
        "new_unique_count": len(new_records),
        "duplicate_count": len(duplicates),
        "scope_excluded_count": len(excluded),
        "extraction_failure_count": len(failures),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    status["last_extraction_failures"] = failures
    write_dedup_report(base, duplicates, excluded, failures)

    print("【扫描与去重完成】")
    print(f"发现源文件：{len(found_files)} 份")
    print(f"本轮新增唯一材料：{len(new_records)} 份")
    print(f"本轮重复排除：{len(duplicates)} 份")
    print(f"本轮范围排除：{len(excluded)} 份")
    print(f"本轮提取失败：{len(failures)} 份")

    if not was_existing_project:
        status["files_scanned"].extend(new_records)
        status["current_step"] = 3
        save_status(base, status)
        if new_records:
            print("下一步：运行 focus，开始逐案摘要。")
        else:
            print("当前没有可进入摘要队列的材料。")
        return 0 if not failures else 2

    if new_records:
        status.setdefault("pending_incremental", []).extend(new_records)
        status["last_incremental_detected_at"] = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        save_status(base, status)
        print(
            f"检测到 {len(new_records)} 份增量材料。"
            "下一步：运行 focus_incremental。"
        )
        return 0 if not failures else 2

    save_status(base, status)
    if status.get("pending_incremental"):
        print(
            f"当前仍有 {len(status['pending_incremental'])} 份待启动的增量材料，"
            "请运行 focus_incremental。"
        )
        return 0

    print("当前项目没有新的待处理材料。可选择：")
    print("A. 基于既有摘要和原文进行具体问题检索或类案问答；")
    print("B. 选择专题方向，重新生成或改写 Master Report；")
    print("C. 结束本轮处理；")
    print("D. 明确确认后执行 reset，重新处理整个项目。")
    return 0


def summary_match_key(raw_text):
    stem = Path(str(raw_text or "")).stem
    for suffix in ("-raw", "_raw", " raw", "-摘要", "_摘要", " 摘要"):
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
    key = standardize_case_num(stem)
    for suffix in ("摘要", "raw", "md"):
        if key.lower().endswith(suffix):
            key = key[: -len(suffix)]
    return key[:-1] if key.endswith("案") else key


def keys_match(left_key, right_key):
    return bool(left_key and right_key and (left_key in right_key or right_key in left_key))


def identity_keys_for_record(record):
    source_name = Path(record.get("path", "")).name
    keys = {summary_match_key(source_name)}
    if record.get("has_standard_case_num"):
        keys.add(
            summary_match_key(
                f"{record.get('case_raw', '')}-{record.get('doc_type', '')}"
            )
        )
    else:
        keys.add(summary_match_key(record.get("case_raw", "")))
    return {key for key in keys if key}


def extract_summary_case_key(summary_path):
    try:
        content = Path(summary_path).read_text(encoding="utf-8")[:4000]
    except OSError:
        return ""
    match = re.search(r"\*\*案号\*\*[:：]\s*(.*?)\n", content)
    if not match:
        return ""
    case_number = match.group(1).strip()
    if not case_number or case_number in {"[完整案号]", "N/A"}:
        return ""
    type_match = re.search(r"\*\*文书类型\*\*[:：]\s*(.*?)\n", content)
    document_type = type_match.group(1).strip() if type_match else ""
    identity = f"{case_number}-{document_type}" if document_type else case_number
    return summary_match_key(identity)


def auto_organize_summaries(base_path, records):
    cases_root = cases_dir_path(base_path)
    mapping = {}
    for record in records:
        for key in identity_keys_for_record(record):
            mapping[key] = record.get("sub_folder", "")

    for summary in cases_root.glob("*摘要.md"):
        summary_key = summary_match_key(summary.name)
        target_subfolder = ""
        for source_key, subfolder in mapping.items():
            if subfolder and keys_match(source_key, summary_key):
                target_subfolder = subfolder
                break
        if not target_subfolder:
            continue
        target_dir = cases_root / target_subfolder
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / summary.name
        if not target_path.exists():
            summary.replace(target_path)


def get_unprocessed_files(records, base_path):
    ensure_dirs(base_path)
    auto_organize_summaries(base_path, records)
    processed_keys = set()
    for summary in cases_dir_path(base_path).rglob("*摘要.md"):
        filename_key = summary_match_key(summary.name)
        if filename_key:
            processed_keys.add(filename_key)
        content_key = extract_summary_case_key(summary)
        if content_key:
            processed_keys.add(content_key)

    unprocessed = []
    for record in records:
        record_keys = identity_keys_for_record(record)
        if not any(
            keys_match(record_key, processed_key)
            for record_key in record_keys
            for processed_key in processed_keys
        ):
            unprocessed.append(record)
    return unprocessed


def sync_processed_files(status, base_path):
    count = len(list(cases_dir_path(base_path).rglob("*摘要.md")))
    status["processed_files"] = count
    save_status(base_path, status)
    return count


def print_focus_batch(batch, command_name):
    print(f"本批派发 {len(batch)} 份材料：")
    for record in batch:
        print(f"- {record['path']}")
    print(
        "逐份读取以上 raw 文件，并严格使用 "
        f"`{ANALYZER_PROMPT_PATH}`。"
    )
    print(
        "摘要保存到 `law_analysis_results/individual_cases/`，文件名使用："
        "案号-文书类型-当事人简称-案由-摘要.md。"
    )
    print(
        "本批写入后立即再次运行 "
        f"`{format_command(command_name, '[项目路径]')}`，直到队列清空。"
    )


def print_three_directions(incremental=False):
    print("【摘要队列已清空】请先从摘要中提炼三个高频、重要争议焦点 A、B、C。")
    if incremental:
        print("本轮还可以选择只围绕增量案件提问。")
    print("随后向用户提供三个方向：")
    print("1. 提供具体案情或问题，从案例库检索并在必要时回溯原文；")
    print("2. 从 A/B/C 中选择一个，作为 Master Report 的重点专题；")
    print("3. 提供自定义报告关键词。")


def command_focus(base_path):
    base = Path(base_path).expanduser().resolve()
    status = load_status(base)
    records = status.get("files_scanned", [])
    unprocessed = get_unprocessed_files(records, base)
    completed = len(records) - len(unprocessed)
    sync_processed_files(status, base)
    print(
        f"【全库数量对账】目标 {len(records)} 份，"
        f"已完成 {completed} 份，剩余 {len(unprocessed)} 份。"
    )
    if not unprocessed:
        print_three_directions()
        return 0
    print_focus_batch(unprocessed[:SUMMARY_BATCH_SIZE], "focus")
    return 0


def command_focus_incremental(base_path):
    base = Path(base_path).expanduser().resolve()
    status = load_status(base)
    pending = status.get("pending_incremental", [])
    if pending:
        known_sources = {
            record.get("source_file") for record in status.get("files_scanned", [])
        }
        new_batch = [
            record for record in pending if record.get("source_file") not in known_sources
        ]
        status["files_scanned"].extend(new_batch)
        status["last_incremental_batch"] = new_batch
        status["pending_incremental"] = []
        status["last_incremental_started_at"] = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        save_status(base, status)

    batch_records = status.get("last_incremental_batch", [])
    unprocessed = get_unprocessed_files(batch_records, base)
    all_records = status.get("files_scanned", [])
    all_unprocessed = get_unprocessed_files(all_records, base)
    incremental_completed = len(batch_records) - len(unprocessed)
    all_completed = len(all_records) - len(all_unprocessed)
    sync_processed_files(status, base)

    print(
        f"【本轮增量对账】新增 {len(batch_records)} 份，"
        f"已完成 {incremental_completed} 份，剩余 {len(unprocessed)} 份。"
    )
    print(
        f"【全库数量对账】累计 {len(all_records)} 份，"
        f"已完成 {all_completed} 份，剩余 {len(all_unprocessed)} 份。"
    )
    if not unprocessed:
        print_three_directions(incremental=True)
        return 0
    print_focus_batch(unprocessed[:SUMMARY_BATCH_SIZE], "focus_incremental")
    return 0


def extract_summary_field(content, label):
    match = re.search(
        rf"\*\*{re.escape(label)}\*\*[:：]\s*(.*?)\n",
        content,
    )
    return match.group(1).strip() if match else "N/A"


def command_report(topic, base_path):
    base = Path(base_path).expanduser().resolve()
    status = load_status(base)
    records = status.get("files_scanned", [])
    unprocessed = get_unprocessed_files(records, base)
    if unprocessed:
        print(
            f"❌ 摘要尚未完成：目标 {len(records)} 份，"
            f"仍有 {len(unprocessed)} 份。禁止提前生成 Master Report。"
        )
        return 2

    summary_paths = sorted(
        cases_dir_path(base).rglob("*摘要.md"),
        key=lambda path: str(path).casefold(),
    )
    if not summary_paths:
        print("❌ 尚未找到任何单案摘要。")
        return 2

    summary_list = []
    for path in summary_paths:
        content = path.read_text(encoding="utf-8")
        summary_list.append(
            {
                "case_no": extract_summary_field(content, "案号"),
                "court": extract_summary_field(content, "法院/程序"),
                "cause": extract_summary_field(content, "核心案由"),
                "result": extract_summary_field(content, "最终结论"),
                "tags": extract_summary_field(content, "关键词"),
                "summary_path": str(path),
            }
        )

    master_data = results_path(base) / "master_data.json"
    master_data.write_text(
        json.dumps(summary_list, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("【报告数据准备完成】")
    print(f"案例摘要：{len(summary_list)} 份")
    print(f"用户确认的重点专题：{topic}")
    print(
        "请读取全部单案摘要及 "
        f"`{MASTER_PROMPT_PATH}`，"
        "生成结构完整、案号可溯源的 Master Report。"
    )
    print(
        f"报告必须保存到：{results_path(base) / 'Master_Report.md'}"
    )
    return 0


def command_next(base_path):
    base = Path(base_path).expanduser().resolve()
    status = load_status(base)
    records = status.get("files_scanned", [])
    unprocessed = get_unprocessed_files(records, base)
    print(f"全库材料：{len(records)} 份")
    print(f"已完成摘要：{len(records) - len(unprocessed)} 份")
    print(f"待完成摘要：{len(unprocessed)} 份")
    print(f"待启动增量：{len(status.get('pending_incremental', []))} 份")
    return 0


def command_reset(base_path):
    base = Path(base_path).expanduser().resolve()
    target = results_path(base)
    if target.exists():
        shutil.rmtree(target)
        print(f"已删除案例分析结果：{target}")
    else:
        print("未发现既有案例分析结果，无需重置。")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="扫描、提取、去重并识别增量")
    init_parser.add_argument("base_path")
    init_parser.add_argument("--force", action="store_true")

    for name, help_text in (
        ("focus", "派发全库单案摘要队列"),
        ("focus_incremental", "派发本轮增量摘要队列"),
        ("next", "查看项目进度"),
        ("reset", "删除既有分析结果后重建"),
    ):
        command_parser = subparsers.add_parser(name, help=help_text)
        command_parser.add_argument("base_path")

    report_parser = subparsers.add_parser("report", help="准备 Master Report 数据")
    report_parser.add_argument("topic")
    report_parser.add_argument("base_path")
    return parser


def main():
    args = build_parser().parse_args()
    if args.command == "init":
        return command_init(args.base_path, force=args.force)
    if args.command == "focus":
        return command_focus(args.base_path)
    if args.command == "focus_incremental":
        return command_focus_incremental(args.base_path)
    if args.command == "report":
        return command_report(args.topic, args.base_path)
    if args.command == "next":
        return command_next(args.base_path)
    if args.command == "reset":
        return command_reset(args.base_path)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
