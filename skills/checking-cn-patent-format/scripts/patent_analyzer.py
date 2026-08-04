#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class PatentAnalyzer:
    def __init__(self, docx_path: str):
        self.docx_path = Path(docx_path)
        self.full_text = ""
        self.paragraphs: List[Tuple[int, str]] = []
        self.patent_type = "unknown"
        self.section_ranges: Dict[str, Tuple[int, int]] = {}
        self._punctuation_variants = self._build_punctuation_variants()

    @staticmethod
    def _build_punctuation_variants() -> Dict[str, List[str]]:
        return {
            "：": [":", "："],
            ":": [":", "："],
            "（": ["(", "（", "("],
            "）": [")", "）", ")"],
            "【": ["[", "【", "["],
            "】": ["]", "】", "]"],
            "；": [";", "；"],
            "，": [",", "，"],
            "。": [".", "。"],
            "\u201c": ['"', "\u201c", '"'],
            "\u201d": ['"', "\u201d", '"'],
        }

    def extract_text(self) -> str:
        try:
            with zipfile.ZipFile(self.docx_path) as zf:
                xml_content = zf.read("word/document.xml")
        except Exception as e:
            print(f"⚠️  文档文本提取失败: {e}")
            return ""

        try:
            root = ET.fromstring(xml_content)
        except Exception as e:
            print(f"⚠️  XML 解析失败: {e}")
            return ""

        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        texts = []
        for node in root.findall(".//w:t", ns):
            if node.text:
                texts.append(node.text)
        self.full_text = "".join(texts)
        return self.full_text

    def extract_paragraphs(self) -> List[Tuple[int, str]]:
        if not self.full_text:
            self.extract_text()

        lines = self.full_text.split('\n')
        self.paragraphs = []
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped:
                self.paragraphs.append((i, stripped))
        return self.paragraphs

    def identify_patent_type(self) -> str:
        if not self.full_text:
            self.extract_text()

        text = self.full_text
        if "发明专利申请" in text or "发明名称" in text:
            self.patent_type = "发明"
        elif "实用新型专利" in text or "实用新型名称" in text:
            self.patent_type = "实用新型"
        elif re.search(r'说\s*明\s*书', text):
            if re.search(r'实\s*用\s*新\s*型\s*内\s*容', text):
                self.patent_type = "实用新型"
            else:
                self.patent_type = "发明"
        else:
            self.patent_type = "unknown"

        return self.patent_type

    def detect_sections(self) -> Dict[str, Tuple[int, int]]:
        if not self.paragraphs:
            self.extract_paragraphs()

        section_starts = {}
        for i, (line_num, text) in enumerate(self.paragraphs):
            stripped = text.strip()

            if re.search(r'说\s*明\s*书\s*摘\s*要', stripped):
                section_starts.setdefault("摘要", i)
            elif re.search(r'摘\s*要\s*附\s*图', stripped):
                section_starts.setdefault("摘要附图", i)
            elif re.search(r'权\s*利\s*要\s*求\s*书', stripped):
                section_starts.setdefault("权利要求书", i)
            elif stripped in ('技术领域', '背景技术', '发明内容', '实用新型内容',
                             '附图说明', '具体实施方式'):
                section_starts.setdefault("说明书", i)
            elif re.search(r'说\s*明\s*书\s*附\s*图', stripped):
                section_starts.setdefault("说明书附图", i)

        ordered = sorted(section_starts.items(), key=lambda x: x[1])
        self.section_ranges = {}
        for idx, (name, start) in enumerate(ordered):
            end = ordered[idx + 1][1] if idx + 1 < len(ordered) else len(self.paragraphs)
            self.section_ranges[name] = (start, end)

        return self.section_ranges

    def generate_search_keywords(self, target_text: str) -> List[str]:
        if not target_text:
            return [target_text]

        keywords = [target_text]

        for cn_punct, variants in self._punctuation_variants.items():
            if cn_punct in target_text:
                for variant in variants:
                    if variant != cn_punct:
                        alt = target_text.replace(cn_punct, variant)
                        if alt not in keywords:
                            keywords.append(alt)

        if re.search(r'[\u4e00-\u9fff]\s+[\u4e00-\u9fff]', target_text):
            compact = re.sub(r'\s+', '', target_text)
            if compact not in keywords:
                keywords.append(compact)

        common_substitutions = {
            "所述": ["所述", "其", "该"],
            "包括": ["包括", "包含", "具有"],
            "所述的": ["所述的", "其", "该"],
            "根据": ["根据", "依据", "按照"],
            "配置为": ["配置为", "设置为", "构造成"],
            "设置为": ["设置为", "配置为", "构造成"],
        }

        for key, subs in common_substitutions.items():
            if key in target_text:
                for sub in subs:
                    if sub != key:
                        alt = target_text.replace(key, sub)
                        if alt not in keywords:
                            keywords.append(alt)

        return keywords

    def find_text_with_keywords(self, target_text: str) -> Optional[Tuple[int, str]]:
        if not self.full_text:
            self.extract_text()

        keywords = self.generate_search_keywords(target_text)

        for keyword in keywords:
            idx = self.full_text.find(keyword)
            if idx != -1:
                return (idx, keyword)

        normalized_full = re.sub(r'\s+', '', self.full_text)
        for keyword in keywords:
            normalized_keyword = re.sub(r'\s+', '', keyword)
            idx = normalized_full.find(normalized_keyword)
            if idx != -1:
                return (idx, keyword)

        return None

    def analyze_common_fields(self) -> Dict[str, List[str]]:
        if not self.full_text:
            self.extract_text()

        common_fields = {
            "发明名称": [
                "发明名称:", "发明名称：", "实用新型名称:", "实用新型名称：",
                "名称:", "名称：",
            ],
            "申请人": [
                "申请人:", "申请人：", "申请号:", "申请号：",
            ],
            "技术领域": [
                "技术领域", "技术领域：",
            ],
            "背景技术": [
                "背景技术", "背景技术：",
            ],
            "发明内容": [
                "发明内容", "发明内容：", "实用新型内容", "实用新型内容：",
            ],
            "权利要求书": [
                "权利要求书", "权利要求", "权利要求：",
            ],
            "说明书附图": [
                "说明书附图", "附图说明", "附图说明：",
            ],
        }

        found_fields = {}
        for field_name, keywords in common_fields.items():
            found_keywords = [kw for kw in keywords if kw in self.full_text]
            if found_keywords:
                found_fields[field_name] = found_keywords

        return found_fields

    def get_patent_summary(self) -> Dict:
        if not self.full_text:
            self.extract_text()

        if not self.paragraphs:
            self.extract_paragraphs()

        if self.patent_type == "unknown":
            self.identify_patent_type()

        if not self.section_ranges:
            self.detect_sections()

        common_fields = self.analyze_common_fields()

        return {
            "patent_type": self.patent_type,
            "total_paragraphs": len(self.paragraphs),
            "text_length": len(self.full_text),
            "sections": list(self.section_ranges.keys()),
            "found_fields": len(common_fields),
            "common_fields": common_fields,
        }


if __name__ == "__main__":
    print("专利文档智能分析器")
    print("=" * 60)
    print()
    print("使用示例:")
    print()
    print("from scripts.patent_analyzer import PatentAnalyzer")
    print()
    print("analyzer = PatentAnalyzer('专利申请文件.docx')")
    print("summary = analyzer.get_patent_summary()")
    print("print(summary)")
    print()
    print("keywords = analyzer.generate_search_keywords('所述的碳毡电极')")
    print("print(keywords)")
