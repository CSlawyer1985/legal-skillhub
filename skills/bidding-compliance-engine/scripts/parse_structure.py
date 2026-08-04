#!/usr/bin/env python3
"""
招标文件结构化解析脚本
将原始文本按章节结构切分为独立section，输出结构化JSON
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime


# 章节标题匹配模式（优先级从高到低）
HEADING_PATTERNS = [
    # 第X章 XXX
    (re.compile(r'^(第[一二三四五六七八九十百]+章)\s*(.*)'), 1),
    # 第X节 XXX
    (re.compile(r'^(第[一二三四五六七八九十百]+节)\s*(.*)'), 2),
    # 一、XXX / 二、XXX
    (re.compile(r'^([一二三四五六七八九十]+、)\s*(.*)'), 3),
    # （一）XXX / （二）XXX
    (re.compile(r'^（([一二三四五六七八九十]+)）\s*(.*)'), 4),
    # 1. XXX / 1.1 XXX / 1.1.1 XXX
    (re.compile(r'^(\d+(?:\.\d+)*)[.、．]\s*(.*)'), 5),
]


def detect_heading(line):
    """检测一行是否为标题，返回(level, full_title)或None"""
    line = line.strip()
    if not line or len(line) > 100:  # 过长行不太可能是标题
        return None

    for pattern, level in HEADING_PATTERNS:
        m = pattern.match(line)
        if m:
            full_title = line.strip()
            return (level, full_title)
    return None


def detect_table(lines, start_idx):
    """检测从start_idx开始是否为表格区域"""
    table_markers = 0
    i = start_idx
    while i < len(lines) and table_markers < 50:
        line = lines[i].strip()
        if '|' in line or '\t' in line or line.startswith('+') or line.startswith('|'):
            table_markers += 1
        elif table_markers > 0 and line == '':
            break
        i += 1
    return table_markers >= 2


def parse_text_to_sections(text, project_id):
    """将文本解析为章节结构"""
    lines = text.split('\n')
    sections = []
    section_id_counter = 0

    current_section = None
    content_lines = []

    for i, line in enumerate(lines):
        heading = detect_heading(line)

        if heading:
            # 保存上一个section
            if current_section is not None:
                current_section["content"] = '\n'.join(content_lines).strip()
                current_section["end_pos"] = i
                current_section["has_table"] = detect_table(lines, current_section["start_pos"])
                sections.append(current_section)

            level, title = heading
            section_id_counter += 1
            sid = f"S{section_id_counter:02d}"

            current_section = {
                "section_id": sid,
                "level": level,
                "title": title,
                "content": "",
                "start_pos": i,
                "end_pos": i,
                "has_table": False,
                "children_section_ids": []
            }
            content_lines = []
        else:
            content_lines.append(line)

    # 保存最后一个section
    if current_section is not None:
        current_section["content"] = '\n'.join(content_lines).strip()
        current_section["end_pos"] = len(lines)
        current_section["has_table"] = detect_table(lines, current_section["start_pos"])
        sections.append(current_section)

    # 如果没有识别到章节，整篇作为一节
    if not sections:
        sections.append({
            "section_id": "S01",
            "level": 1,
            "title": "全文",
            "content": text,
            "start_pos": 0,
            "end_pos": len(lines),
            "has_table": False,
            "children_section_ids": []
        })

    # 构建层级关系
    for i, sec in enumerate(sections):
        for j in range(i + 1, len(sections)):
            if sections[j]["level"] > sec["level"]:
                sec["children_section_ids"].append(sections[j]["section_id"])
            elif sections[j]["level"] <= sec["level"]:
                break

    return {
        "project_id": project_id,
        "total_sections": len(sections),
        "sections": sections,
        "metadata": {
            "parse_time": datetime.now().isoformat(),
            "method": "heuristic_regex"
        }
    }


def main():
    parser = argparse.ArgumentParser(description='招标文件结构化解析')
    parser.add_argument('--raw_text_path', required=True, help='原始文本路径')
    parser.add_argument('--project_id', required=True, help='项目ID')
    parser.add_argument('--output_dir', required=True, help='输出目录')
    args = parser.parse_args()

    with open(args.raw_text_path, 'r', encoding='utf-8') as f:
        text = f.read()

    result = parse_text_to_sections(text, args.project_id)

    os.makedirs(args.output_dir, exist_ok=True)
    output_path = os.path.join(args.output_dir, "tender.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"解析完成: {result['total_sections']} 个章节")
    print(f"输出文件: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
