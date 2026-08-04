#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用模板填充引擎 v3：基于段落区域定位的docx模板填充

核心改进：
1. 区分"当事人信息区""诉讼请求区""事实与理由区"等段落区域
2. 字段填充时限定在特定区域内，避免跨区域误填
3. 勾选框处理时精确匹配段落上下文
"""

import os
import re
import shutil
import zipfile
import xml.etree.ElementTree as ET
from copy import deepcopy
from typing import Dict, List, Optional, Tuple, Any

# 注册命名空间
NAMESPACES = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'mc': 'http://schemas.openxmlformats.org/markup-compatibility/2006',
    'w14': 'http://schemas.microsoft.com/office/word/2010/wordml',
}
for prefix, uri in NAMESPACES.items():
    ET.register_namespace(prefix, uri)

EXTRA_NS = {
    'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'pic': 'http://schemas.openxmlformats.org/drawingml/2006/picture',
    'xml': 'http://www.w3.org/XML/1998/namespace',
    'wne': 'http://schemas.microsoft.com/office/word/2006/wordml',
}
for prefix, uri in EXTRA_NS.items():
    ET.register_namespace(prefix, uri)


class TemplateFiller:
    """通用模板填充引擎 v3"""

    def __init__(self, template_path: str, output_dir: str = '.'):
        self.template_path = template_path
        self.output_dir = output_dir
        self.unpacked_dir = None
        self.root = None
        self._xml_decl = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'

    def fill(self, fill_data: Dict[str, Any], output_filename: str = None) -> str:
        """一键填充模板"""
        self._unpack()
        self._parse_xml()
        
        # 获取段落区域索引
        section_map = self._build_section_map()
        
        # 1. 区域内字段填充
        section_fills = fill_data.get('section_fills', [])
        for sf in section_fills:
            self._fill_section(sf, section_map)
        
        # 2. 精确勾选框处理
        checkbox_ops = fill_data.get('checkbox_ops', [])
        for cb in checkbox_ops:
            self._do_checkbox(cb, section_map)
        
        # 3. 全局文本替换（慎用）
        text_replacements = fill_data.get('text_replacements', {})
        for old, new in text_replacements.items():
            self._replace_text_global(old, new)
        
        output_path = self._save_and_pack(output_filename)
        self._cleanup()
        return output_path

    # ================================================================
    # 区域索引
    # ================================================================
    def _build_section_map(self) -> Dict[str, Tuple[int, int]]:
        """
        构建段落区域索引
        
        Returns:
            {"原告_自然人": (start_idx, end_idx), "被告_自然人": ..., ...}
        """
        ns = NAMESPACES
        paragraphs = list(self.root.findall('.//w:p', ns))
        
        # 可跟子类型（自然人/法人）的当事人标记
        PERSON_MARKERS = {'原告', '被告', '第三人', '答辩人', '赔偿请求人', '申请人'}
        # 独立自然人标记（无子类型行）
        STANDALONE_NATURAL = {
            '自诉人': '自诉人_自然人',
            '被告人': '被告人_自然人',
        }
        # 代理人标记
        AGENT_MARKERS = {
            '委托诉讼代理人': '委托诉讼代理人',
            '诉讼代理人': '诉讼代理人',
            '辩护人': '辩护人',
            '委托代理人': '委托代理人',
        }
        # 请求区域标记
        REQUEST_MARKERS = ['诉讼请求', '答辩事项', '答辩意见', '赔偿请求']
        # 组织/机关标记
        ORG_MARKERS = {
            '赔偿义务机关': '赔偿义务机关',
            '复议机关': '复议机关',
        }
        
        section_map = {}
        current_section = None
        section_start = None
        
        for i, p in enumerate(paragraphs):
            text = self._get_para_text(p).strip()
            
            # 检测区域边界
            new_section = None
            
            # 子类型行：自然人/法人
            if text == '（自然人）':
                if current_section in PERSON_MARKERS:
                    new_section = f'{current_section}_自然人'
                elif current_section and current_section in STANDALONE_NATURAL:
                    new_section = f'{current_section}_自然人'
            elif text == '（法人、非法人组织）':
                if current_section in PERSON_MARKERS:
                    new_section = f'{current_section}_法人'
            elif text.startswith('（行政机关') or (text.startswith('（') and '行政机关' in text):
                if current_section in PERSON_MARKERS:
                    new_section = f'{current_section}_行政机关'
            # 当事人标记
            elif text in PERSON_MARKERS:
                new_section = text
            # 独立自然人标记
            elif text in STANDALONE_NATURAL:
                new_section = STANDALONE_NATURAL[text]
            # 组织/机关标记
            elif text in ORG_MARKERS:
                new_section = ORG_MARKERS[text]
            # 代理人标记
            elif text in AGENT_MARKERS:
                new_section = AGENT_MARKERS[text]
            # 请求区域
            else:
                for marker in REQUEST_MARKERS:
                    if text == marker or text.startswith(marker):
                        new_section = marker
                        break
            
            # 其他已知标记
            if new_section is None:
                if text.startswith('事实与理由') or text == '事实与理由':
                    new_section = '事实与理由'
                elif text.startswith('约定管辖') or text.startswith('约定管辖和诉前保全'):
                    new_section = '约定管辖和诉前保全'
                elif text.startswith('对纠纷解决方式的意愿'):
                    new_section = '对纠纷解决方式的意愿'
                elif text == '当事人信息':
                    new_section = '_START_PARTIES'
                elif text.startswith('法定代理人') or '代为告诉人' in text:
                    new_section = '法定代理人或代为告诉人'
            
            if new_section == '_END_PARTIES':
                # 结束当前区域
                if current_section and section_start is not None:
                    section_map[current_section] = (section_start, i)
                current_section = None
                section_start = None
            elif new_section and not new_section.startswith('_'):
                # 保存前一个区域
                if current_section and section_start is not None:
                    section_map[current_section] = (section_start, i)
                current_section = new_section
                section_start = i
            elif new_section == '_START_PARTIES':
                current_section = None
                section_start = None
        
        # 最后一个区域
        if current_section and section_start is not None:
            section_map[current_section] = (section_start, len(paragraphs))
        
        # 后处理：无子类型的当事人标记自动加_自然人
        sections_to_rename = {}
        for section_name in list(section_map.keys()):
            if section_name in PERSON_MARKERS:
                has_subtype = any(s.startswith(section_name + '_') for s in section_map)
                if not has_subtype:
                    sections_to_rename[section_name] = f'{section_name}_自然人'
        for old_name, new_name in sections_to_rename.items():
            section_map[new_name] = section_map.pop(old_name)
        
        return section_map

    # ================================================================
    # 区域内字段填充
    # ================================================================
    def _fill_section(self, sf: Dict, section_map: Dict):
        """
        在指定区域内填充字段
        
        sf: {
            "section": "原告_自然人",   # 区域名
            "fields": {"姓名：": "张三", "联系电话：": "138xxx"},  # 标签→值
            "checkboxes": {"性别：男": True, "性别：女": False},   # 上下文→是否勾选
        }
        """
        section_name = sf.get('section', '')
        fields = sf.get('fields', {})
        checkboxes = sf.get('checkboxes', {})
        
        # 找到区域对应的段落
        ns = NAMESPACES
        paragraphs = list(self.root.findall('.//w:p', ns))
        
        region = section_map.get(section_name)
        if not region:
            # 尝试模糊匹配
            for key in section_map:
                if section_name in key or key in section_name:
                    region = section_map[key]
                    break
        
        if not region:
            return
        
        start_idx, end_idx = region
        region_paragraphs = paragraphs[start_idx:end_idx + 1]
        
        # 填充字段
        for label, value in fields.items():
            if not value:
                continue
            self._fill_field_in_region(region_paragraphs, label, str(value))
        
        # 处理勾选框
        for context, should_check in checkboxes.items():
            self._fill_checkbox_in_region(region_paragraphs, context, should_check)

    def _fill_field_in_region(self, paragraphs: list, label: str, value: str):
        """在区域内段落中填充字段"""
        ns = NAMESPACES
        
        for p in paragraphs:
            full_text = self._get_para_text(p)
            if label not in full_text:
                continue
            
            # 找到包含标签的<w:t>元素
            t_elems = p.findall('.//w:t', ns)
            
            for t in t_elems:
                if not t.text or label not in t.text:
                    continue
                
                idx = t.text.index(label) + len(label)
                after = t.text[idx:]
                
                # 如果标签后是空白占位符或空，直接替换
                if not after.strip() or re.match(r'^\s+$', after):
                    t.text = t.text[:idx] + value
                    t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
                    return
            
            # 如果标签和值不在同一个<w:t>中
            # 查找标签run后面的空run
            runs = list(p.findall('w:r', ns))
            label_run_idx = None
            
            for ri, r in enumerate(runs):
                for t in r.findall('w:t', ns):
                    if t.text and label in t.text:
                        label_run_idx = ri
                        break
                if label_run_idx is not None:
                    break
            
            if label_run_idx is not None:
                # 在标签run后找空run
                for next_r in runs[label_run_idx + 1:]:
                    for t in next_r.findall('w:t', ns):
                        if not t.text or not t.text.strip():
                            t.text = value
                            t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
                            return
                
                # 没有空run，在标签文本后追加
                for t in runs[label_run_idx].findall('w:t', ns):
                    if t.text and label in t.text:
                        idx = t.text.index(label) + len(label)
                        t.text = t.text[:idx] + value
                        t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
                        return

    def _fill_checkbox_in_region(self, paragraphs: list, context: str, should_check: bool):
        """
        在区域内处理勾选框
        
        关键：只勾选紧接在context文字之后的□，不勾选同一行其他的□
        例如："性别：男□    女□" 中 context="性别：男"，只勾选"男"后面的□
        """
        ns = NAMESPACES
        
        for p in paragraphs:
            full_text = self._get_para_text(p)
            if context not in full_text:
                continue
            
            t_elems = p.findall('.//w:t', ns)
            
            # 策略：在段落文本中找到 context 的位置，然后找紧随其后的□
            # 这需要在<w:t>级别精确定位
            
            # 方法1：如果context和□在同一个<w:t>中
            for t in t_elems:
                if not t.text:
                    continue
                if context in t.text:
                    # context和□可能在同一个<w:t>中
                    after_context = t.text[t.text.index(context) + len(context):]
                    if '□' in after_context:
                        # 只替换context后的第一个□
                        if should_check:
                            # 精确替换：将context后的第一个□改为☑
                            ctx_end = t.text.index(context) + len(context)
                            before = t.text[:ctx_end]
                            after = t.text[ctx_end:]
                            after = after.replace('□', '☑', 1)
                            t.text = before + after
                        return
            
            # 方法2：context在一个<w:t>，□在后续<w:t>中
            context_found = False
            for t in t_elems:
                if not context_found:
                    if t.text and context in t.text:
                        # 检查这个<w:t>中context后是否有□
                        after = t.text[t.text.index(context) + len(context):]
                        if '□' in after:
                            if should_check:
                                ctx_end = t.text.index(context) + len(context)
                                before = t.text[:ctx_end]
                                after_part = t.text[ctx_end:].replace('□', '☑', 1)
                                t.text = before + after_part
                            return
                        context_found = True
                    continue
                
                # context已找到，检查后续<w:t>中的□
                if t.text and '□' in t.text:
                    if should_check:
                        t.text = t.text.replace('□', '☑', 1)
                    return
                elif t.text and '☐' in t.text:
                    if should_check:
                        t.text = t.text.replace('☐', '☑', 1)
                    return

    # ================================================================
    # 精确勾选框操作
    # ================================================================
    def _do_checkbox(self, cb: Dict, section_map: Dict):
        """
        精确勾选框操作
        
        cb: {
            "section": "原告_自然人",  # 限定区域
            "paragraph_contains": "性别",  # 段落必须包含的文字
            "before_checkbox": "男",  # □紧前面的文字
            "check": True,
        }
        """
        section_name = cb.get('section', '')
        para_contains = cb.get('paragraph_contains', '')
        before_checkbox = cb.get('before_checkbox', '')
        should_check = cb.get('check', True)
        
        ns = NAMESPACES
        paragraphs = list(self.root.findall('.//w:p', ns))
        
        # 确定搜索范围
        search_paragraphs = paragraphs
        if section_name:
            region = section_map.get(section_name)
            if region:
                start_idx, end_idx = region
                search_paragraphs = paragraphs[start_idx:end_idx + 1]
        
        for p in search_paragraphs:
            full_text = self._get_para_text(p)
            
            if para_contains and para_contains not in full_text:
                continue
            
            t_elems = p.findall('.//w:t', ns)
            
            # 在段落文本中定位 before_checkbox + □ 的精确位置
            # 然后在XML中找到对应的<w:t>进行替换
            target = before_checkbox + '□'  # 如 "男□"
            target2 = before_checkbox + '☐'  # 如 "男☐"
            
            for t in t_elems:
                if not t.text:
                    continue
                
                # 检查同一<w:t>中是否有 before_checkbox + □/☐
                if target in t.text:
                    if should_check:
                        t.text = t.text.replace(target, before_checkbox + '☑', 1)
                    return
                
                if target2 in t.text:
                    if should_check:
                        t.text = t.text.replace(target2, before_checkbox + '☑', 1)
                    return
            
            # 如果before_checkbox和□不在同一个<w:t>中
            # 情况：before_checkbox在<w:t>A末尾，□在<w:t>B开头
            prev_text = ''
            for t in t_elems:
                if t.text and '□' in t.text:
                    # 检查前序文本是否以before_checkbox结尾
                    combined = prev_text + t.text[:t.text.index('□')]
                    if combined.rstrip().endswith(before_checkbox):
                        if should_check:
                            t.text = t.text.replace('□', '☑', 1)
                        return
                if t.text and '☐' in t.text:
                    combined = prev_text + t.text[:t.text.index('☐')]
                    if combined.rstrip().endswith(before_checkbox):
                        if should_check:
                            t.text = t.text.replace('☐', '☑', 1)
                        return
                if t.text:
                    prev_text += t.text

    # ================================================================
    # 全局文本替换
    # ================================================================
    def _replace_text_global(self, old_text: str, new_text: str):
        ns = NAMESPACES
        for t in self.root.findall('.//w:t', ns):
            if t.text and old_text in t.text:
                t.text = t.text.replace(old_text, new_text)

    # ================================================================
    # 辅助方法
    # ================================================================
    def _get_para_text(self, p) -> str:
        ns = NAMESPACES
        return ''.join(t.text or '' for t in p.findall('.//w:t', ns))

    def _unpack(self):
        self.unpacked_dir = self.template_path.replace('.docx', '_work')
        if os.path.exists(self.unpacked_dir):
            shutil.rmtree(self.unpacked_dir)
        with zipfile.ZipFile(self.template_path, 'r') as zf:
            zf.extractall(self.unpacked_dir)

    def _parse_xml(self):
        doc_path = os.path.join(self.unpacked_dir, 'word', 'document.xml')
        with open(doc_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.root = ET.fromstring(content)

    def _save_and_pack(self, output_filename: str = None) -> str:
        # 保存XML
        doc_path = os.path.join(self.unpacked_dir, 'word', 'document.xml')
        content = ET.tostring(self.root, encoding='unicode')
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(self._xml_decl + content)
        
        # 打包
        if output_filename is None:
            output_filename = os.path.basename(self.template_path)
        output_path = os.path.join(self.output_dir, output_filename)
        
        if os.path.exists(output_path):
            os.remove(output_path)
        
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root_dir, dirs, files in os.walk(self.unpacked_dir):
                for file in files:
                    file_path = os.path.join(root_dir, file)
                    arc_name = os.path.relpath(file_path, self.unpacked_dir)
                    zf.write(file_path, arc_name)
        
        return output_path

    def _cleanup(self):
        if self.unpacked_dir and os.path.exists(self.unpacked_dir):
            shutil.rmtree(self.unpacked_dir)
