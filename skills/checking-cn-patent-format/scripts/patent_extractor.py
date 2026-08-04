#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专利文档综合提取工具 - 多Agent版

基于OOXML标准的docx解析，支持：
1. 按页眉章节结构准确提取文字内容
2. 提取文档中的所有图片（按章节分组）并生成分析报告
3. 兼容原有接口：--extract-only, --output-json, --split-sections
4. 支持 .doc 格式自动转换

输出文件：
- header_sections_<timestamp>.json：按页眉章节的文本提取结果
- image_analysis_<timestamp>.json：图片分析报告（包含章节归属、重复引用等）
"""

# os 提供操作系统接口，如文件路径操作
import os
# sys 提供系统相关功能
import sys
# io 提供流处理功能，这里用于设置 UTF-8 输出
import io
# zipfile 用于解压 docx 文件（docx 本质上是 ZIP 压缩包）
import zipfile
# shutil 用于文件复制等操作
import shutil
# json 用于读写 JSON 格式文件
import json
# re 提供正则表达式支持
import re
# argparse 用于解析命令行参数
import argparse
# datetime 用于处理日期和时间
from datetime import datetime
# Path 用于面向对象的文件路径处理
from pathlib import Path
# ElementTree 用于解析 XML
from xml.etree import ElementTree as ET

# 设置标准输出为 UTF-8 编码，确保中文正常显示
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
except (AttributeError, io.UnsupportedOperation):
    pass

# 将父目录添加到 Python 路径，以便导入其他模块
sys.path.insert(0, str(Path(__file__).parent.parent))

# 导入 doc_converter 模块中的 ensure_docx 函数，用于 .doc 转 .docx
from scripts.doc_converter import ensure_docx


# ===================== 命名空间定义 =====================
# OOXML 使用 XML 命名空间来区分不同来源的元素
# 这些命名空间对应 Word 文档中各种元素的 URI
NAMESPACES = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'pic': 'http://schemas.openxmlformats.org/drawingml/2006/picture',
    'ct': 'http://schemas.openxmlformats.org/package/2006/content-types',
    'rels': 'http://schemas.openxmlformats.org/package/2006/relationships'
}

# 为常用命名空间创建快捷变量
W_NS = NAMESPACES['w']      # Word 主命名空间
R_NS = NAMESPACES['r']      # 关系命名空间
RELS_NS = NAMESPACES['rels'] # 包关系命名空间
WP_NS = NAMESPACES['wp']    # WordprocessingDrawing 命名空间
A_NS = NAMESPACES['a']      # DrawingML 命名空间
V_NS = 'urn:schemas-microsoft-com:vml'  # VML 矢量图形命名空间

# 格式化后的命名空间字符串，用于 ElementTree 的 find/findall 方法
W_NS_F = f'{{{W_NS}}}'
R_NS_F = f'{{{R_NS}}}'

# 专利文档预期的标准章节名称
EXPECTED_SECTIONS = ['说明书摘要', '摘要附图', '权利要求书', '说明书', '说明书附图']

# 页眉名称校正映射：将简写映射为标准名称
HEADER_CORRECTIONS = {
    '摘要': '说明书摘要',
}


def register_namespaces():
    """注册 XML 命名空间，确保序列化时保留前缀。"""
    for prefix, uri in NAMESPACES.items():
        try:
            ET.register_namespace(prefix, uri)
        except (ValueError, AttributeError):
            pass


def unpack_docx(docx_path, output_dir):
    """
    解压 docx 文件到指定目录。

    docx 文件本质上是一个 ZIP 压缩包，包含多个 XML 文件和资源文件。
    """
    if not os.path.exists(docx_path):
        raise FileNotFoundError(f"输入文件不存在: {docx_path}")

    if not docx_path.lower().endswith('.docx'):
        raise ValueError("输入文件必须是.docx格式")

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    try:
        # 使用 zipfile 解压 docx
        with zipfile.ZipFile(docx_path, 'r') as zip_ref:
            zip_ref.extractall(output_dir)
        return output_dir
    except zipfile.BadZipFile:
        raise ValueError("无效的docx文件（不是有效的ZIP格式）")


def extract_images(unpacked_dir, output_dir):
    """
    从解压后的目录中提取所有图片，并收集图片元数据。

    Word 文档中的图片存放在 word/media/ 目录下。
    元数据包括尺寸、格式等，供图片审查Agent在无法直接查看图片时降级使用。
    """
    media_dir = os.path.join(unpacked_dir, 'word', 'media')

    if not os.path.exists(media_dir):
        return []

    os.makedirs(output_dir, exist_ok=True)

    # 支持的图片扩展名
    image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.emf', '.wmf', '.svg', '.tiff'}
    extracted_images = []

    # 遍历媒体目录中的所有文件
    for filename in sorted(os.listdir(media_dir)):
        if Path(filename).suffix.lower() in image_extensions:
            src_path = os.path.join(media_dir, filename)
            dst_path = os.path.join(output_dir, filename)

            # 复制图片到输出目录
            shutil.copy2(src_path, dst_path)

            file_size = os.path.getsize(dst_path)
            image_info = {
                'name': filename,
                'path': dst_path,
                'size': file_size,
                'metadata': _extract_image_metadata(dst_path)
            }
            extracted_images.append(image_info)

    return extracted_images


def _extract_image_metadata(image_path):
    """
    提取图片文件的元数据（尺寸、格式、DPI等）。

    使用Pillow库读取图片元数据。当Pillow不可用或图片格式
    不受支持时，返回基础文件信息。

    Args:
        image_path: 图片文件路径

    Returns:
        包含元数据的字典
    """
    metadata = {
        'width': None,
        'height': None,
        'format': None,
        'mode': None,
        'dpi': None,
        'readable': True,
        'read_error': None
    }

    try:
        from PIL import Image
        with Image.open(image_path) as img:
            metadata['width'] = img.width
            metadata['height'] = img.height
            metadata['format'] = img.format
            metadata['mode'] = img.mode
            metadata['dpi'] = img.info.get('dpi', None)
    except ImportError:
        metadata['readable'] = False
        metadata['read_error'] = 'Pillow not available'
        # 【BUG-008修复】首次检测到Pillow缺失时输出明确警告
        if not hasattr(_extract_image_metadata, '_pillow_warned'):
            _extract_image_metadata._pillow_warned = True
            print("  ⚠️ [环境警告] Pillow库未安装！图片元数据（尺寸/DPI/格式）将无法提取。")
            print("     影响范围：图片分辨率合规性检查、图片尺寸验证等功能将降级或跳过。")
            print("     修复方法：pip install Pillow>=10.0.0")
    except Exception as e:
        metadata['readable'] = False
        metadata['read_error'] = str(e)

    return metadata


# 【BUG-008修复】初始化静态标记变量
_extract_image_metadata._pillow_warned = False


def check_environment_health():
    """
    环境健康检查：验证skill运行所依赖的关键库是否可用。

    在文档提取流程早期调用，提前发现依赖缺失问题，
    避免在深层处理阶段才发现功能降级。

    Returns:
        dict: 包含各依赖项状态的字典
    """
    health = {
        'pillow': {'available': False, 'version': None, 'required': True},
        'lxml': {'available': False, 'version': None, 'required': True},
        'defusedxml': {'available': False, 'version': None, 'required': True},
    }

    # 检查 Pillow
    try:
        from PIL import __version__ as pv
        health['pillow']['available'] = True
        health['pillow']['version'] = pv
    except ImportError:
        pass

    # 检查 lxml
    try:
        import lxml
        health['lxml']['available'] = True
        health['lxml']['version'] = lxml.__version__
    except ImportError:
        pass

    # 检查 defusedxml
    try:
        import defusedxml
        health['defusedxml']['available'] = True
        health['defusedxml']['version'] = defusedxml.__version__
    except ImportError:
        pass

    # 输出检查结果
    all_ok = all(v['available'] or not v['required'] for v in health.values())
    missing_required = [k for k, v in health.items() if not v['available'] and v['required']]

    print("\n📋 环境健康检查:")
    for name, info in health.items():
        status = "✅" if info['available'] else "❌"
        ver = f" (v{info['version']})" if info['version'] else ""
        req = " [必需]" if info['required'] else " [可选]"
        print(f"  {status} {name}{ver}{req}")

    if missing_required:
        print(f"\n  ⚠️ 缺少 {len(missing_required)} 个必需依赖: {', '.join(missing_required)}")
        for m in missing_required:
            if m == 'pillow':
                print(f"     修复: pip install 'Pillow>=10.0.0'")
            elif m == 'lxml':
                print(f"     修复: pip install 'lxml>=5.0.0'")
            elif m == 'defusedxml':
                print(f"     修复: pip install 'defusedxml>=0.7.1'")
    else:
        print("\n  ✅ 所有依赖已就绪")

    return {'all_ok': all_ok, 'details': health, 'missing_required': missing_required}


def extract_header_text_by_methods(header_path):
    """
    使用多种策略提取页眉文本，返回所有候选结果。

    页眉中的文本可能存储在不同类型的元素中，需要多种方法提取。
    """
    results = {}

    try:
        tree = ET.parse(header_path)
        root = tree.getroot()
    except Exception as e:
        return results

    # 方法1：提取 w:t 元素中的文本（标准文本元素）
    w_t_texts = []
    for t in root.iter(f'{{{W_NS}}}t'):
        if t.text:
            w_t_texts.append(t.text.strip())
    results['w_t'] = ''.join(w_t_texts).strip()

    # 方法2：提取 docPr 元素的 descr 属性（图形描述）
    descr_texts = []
    for elem in root.iter():
        if elem.tag.endswith('}docPr') or elem.tag == 'docPr':
            descr = elem.get('descr', '')
            if descr:
                descr_texts.append(descr.strip())
    results['docPr_descr'] = ''.join(descr_texts).strip()

    # 方法3：提取 VML textpath 元素的文本（旧版矢量图形文本）
    v_textpath_texts = []
    for vt in root.iter(f'{{{V_NS}}}textpath'):
        if vt.text:
            v_textpath_texts.append(vt.text.strip())
    results['v_textpath'] = ''.join(v_textpath_texts).strip()

    # 方法4：从原始 XML 中提取所有连续中文字符
    raw = ET.tostring(root, encoding='unicode')
    cn_chunks = re.findall(r'[\u4e00-\u9fff]{2,}', raw)
    cn_unique = list(dict.fromkeys(cn_chunks))  # 去重同时保持顺序
    results['all_cn'] = ''.join(cn_unique)

    return results


def resolve_header_name(methods_results, header_id, section_index):
    """
    从多种提取策略中确定最终的章节名。

    优先级：
    1. 预期章节名的精确匹配
    2. 预期章节名的包含匹配
    3. 第一个候选结果
    """
    candidates = []

    # 收集各种提取方法的候选结果
    descr = methods_results.get('docPr_descr', '')
    if descr:
        candidates.append(('docPr_descr', descr))

    w_t = methods_results.get('w_t', '')
    if w_t:
        candidates.append(('w_t', w_t))
        corrected = HEADER_CORRECTIONS.get(w_t, None)
        if corrected:
            candidates.append(('w_t_corrected', corrected))

    all_cn = methods_results.get('all_cn', '')
    if all_cn and all_cn != w_t:
        candidates.append(('all_cn', all_cn))

    # 特殊处理：第一个页眉且第一个章节，将"摘要"纠正为"说明书摘要"
    if header_id == 'header1' and section_index == 0:
        for name in ['说明书摘要']:
            if any(c[1] == name for c in candidates):
                continue
            if 'w_t' in methods_results and methods_results['w_t'] == '摘要':
                return name

    # 尝试精确匹配预期章节名
    for source, text in candidates:
        if text in EXPECTED_SECTIONS:
            return text

    # 尝试包含匹配
    for source, text in candidates:
        for expected in EXPECTED_SECTIONS:
            if text in expected or expected in text:
                return expected

    # 返回第一个候选结果，如果没有则返回"未分类"
    if candidates:
        best = candidates[0]
        return best[1]

    return "未分类"


def parse_headers(unpacked_dir):
    """解析所有页眉文件，返回页眉ID到文本的映射（多策略）。"""
    word_dir = os.path.join(unpacked_dir, 'word')
    headers = {}

    # 查找所有 header*.xml 文件
    for filename in sorted(os.listdir(word_dir)):
        if filename.startswith('header') and filename.endswith('.xml'):
            header_path = os.path.join(word_dir, filename)
            header_id = filename.replace('.xml', '')

            methods_results = extract_header_text_by_methods(header_path)
            headers[header_id] = methods_results

    return headers


def parse_relationships(unpacked_dir):
    """
    解析关系文件，返回 rId 到目标文件的映射。

    OOXML 使用关系文件来管理文档各部分之间的引用关系。
    """
    rels_path = os.path.join(unpacked_dir, 'word', '_rels', 'document.xml.rels')

    if not os.path.exists(rels_path):
        return {}

    relationships = {}

    try:
        tree = ET.parse(rels_path)
        root = tree.getroot()

        ns = {'rels': RELS_NS}
        for rel in root.findall('rels:Relationship', ns):
            rid = rel.get('Id')
            target = rel.get('Target')
            rel_type = rel.get('Type')

            if rid and target:
                relationships[rid] = {
                    'target': target,
                    'type': rel_type
                }

    except Exception as e:
        pass

    return relationships


def get_element_position(element, all_elements):
    """获取元素在遍历列表中的位置索引。"""
    try:
        return all_elements.index(element)
    except ValueError:
        return -1


def build_section_map(unpacked_dir, headers_raw, rels_map):
    """
    构建章节映射：确定每个 sectPr 对应的章节名。

    在 OOXML 中，sectPr（section properties）标记一个章节的结束。
    每个 sectPr 可以引用一个页眉，通过页眉文本确定章节名称。

    返回: list of dict with {position, header_name}
    """
    document_path = os.path.join(unpacked_dir, 'word', 'document.xml')
    if not os.path.exists(document_path):
        raise FileNotFoundError("未找到document.xml")

    try:
        tree = ET.parse(document_path)
        root = tree.getroot()
    except Exception as e:
        raise RuntimeError(f"解析document.xml失败: {e}")

    all_elements = list(root.iter())
    body = root.find(f'.//{{{W_NS}}}body')

    sect_pr_infos = []

    # 遍历 body 中的所有元素，查找 sectPr
    if body is not None:
        for child in body:
            for sect_pr in child.iter(f'{{{W_NS}}}sectPr'):
                pos = get_element_position(sect_pr, all_elements)
                is_direct_child = (child.tag == f'{{{W_NS}}}sectPr')
                header_ref = sect_pr.find(f'.//{{{W_NS}}}headerReference')
                r_id = header_ref.get(f'{{{R_NS}}}id') if header_ref is not None else None
                sect_pr_infos.append({
                    'element': sect_pr,
                    'position': pos,
                    'r_id': r_id,
                    'is_direct_child': is_direct_child
                })

    # 按位置排序
    sect_pr_infos.sort(key=lambda x: x['position'])

    section_boundaries = []
    for idx, info in enumerate(sect_pr_infos):
        r_id = info.get('r_id')
        target = None
        if r_id and r_id in rels_map:
            target = rels_map[r_id]['target']
            header_id = os.path.basename(target).replace('.xml', '')
        else:
            header_id = None

        # 根据页眉 ID 解析章节名称
        if header_id and header_id in headers_raw:
            header_name = resolve_header_name(headers_raw[header_id], header_id, idx)
        else:
            header_name = f"Section_{idx + 1}"

        section_boundaries.append({
            'index': idx,
            'position': info['position'],
            'header_name': header_name,
            'r_id': r_id,
            'target': target,
            'is_body_end': info['is_direct_child']
        })

    return section_boundaries


def extract_text_from_element(elem):
    """从 XML 元素中递归提取所有文本。"""
    texts = []
    for t in elem.iter(f'{{{W_NS}}}t'):
        if t.text:
            texts.append(t.text)
    text = ''.join(texts).strip()

    # 如果元素包含 sdt（结构化文档标签），优先使用其中的文本
    sdt_texts = []
    for sdt in elem.iter(f'{{{W_NS}}}sdt'):
        for t in sdt.iter(f'{{{W_NS}}}t'):
            if t.text:
                sdt_texts.append(t.text)
    if sdt_texts:
        text = ''.join(sdt_texts).strip()

    return text


def extract_paragraphs_by_section(unpacked_dir, section_boundaries):
    """
    按章节提取文本内容。

    每个 sectPr 标记一个章节的结束，根据元素位置确定所属章节。
    """
    document_path = os.path.join(unpacked_dir, 'word', 'document.xml')
    tree = ET.parse(document_path)
    root = tree.getroot()

    # 过滤掉 body 末尾的 sectPr（它不代表一个章节的开始）
    non_body_end_boundaries = [b for b in section_boundaries if not b['is_body_end']]

    all_elements = list(root.iter())
    body = root.find(f'.//{{{W_NS}}}body')
    if body is None:
        return []

    body_children = list(body)

    # 根据元素位置确定所属章节索引
    def get_section_for_element(elem_pos):
        for i, b in enumerate(non_body_end_boundaries):
            if elem_pos <= b['position']:
                return i
        return len(non_body_end_boundaries)

    # 初始化章节文本列表
    sections_text = []
    for b in section_boundaries:
        sections_text.append({
            'section_name': b['header_name'],
            'paragraphs': []
        })
    if not section_boundaries:
        sections_text.append({
            'section_name': '默认',
            'paragraphs': []
        })

    # 遍历 body 的子元素，按章节分类
    for child in body_children:
        if child.tag == f'{{{W_NS}}}sectPr':
            continue

        child_pos = get_element_position(child, all_elements)

        section_idx = get_section_for_element(child_pos)
        if section_idx >= len(sections_text):
            section_idx = len(sections_text) - 1

        # 处理段落
        if child.tag == f'{{{W_NS}}}p':
            text = extract_text_from_element(child)
            if text:
                sections_text[section_idx]['paragraphs'].append(text)

        # 处理表格
        elif child.tag == f'{{{W_NS}}}tbl':
            table_rows = []
            for row in child.iter(f'{{{W_NS}}}tr'):
                cells = []
                for cell in row.iter(f'{{{W_NS}}}tc'):
                    cell_text = extract_text_from_element(cell)
                    cells.append(cell_text)
                if any(cells):
                    table_rows.append(cells)
            if table_rows:
                sections_text[section_idx]['paragraphs'].append(f"[表格: {len(table_rows)}行 x {len(table_rows[0])}列]")
                for row in table_rows:
                    sections_text[section_idx]['paragraphs'].append(' | '.join(row))

        # 处理结构化文档标签
        elif child.tag == f'{{{W_NS}}}sdt':
            text = extract_text_from_element(child)
            if text:
                sections_text[section_idx]['paragraphs'].append(text)

    return sections_text


def extract_fig_text_name_after_drawing(drawing_element, all_elements):
    """
    提取图片后紧邻的文字作为该图片的图号名称（fig_text_name）。

    在专利文档中，说明书附图章节的图片后面通常紧跟图号文字（如"图1"、"图2"等）。
    本函数查找drawing元素后的文本内容，提取符合"图N"格式的文字作为fig_text_name。
    """
    try:
        drawing_pos = get_element_position(drawing_element, all_elements)

        # 查找drawing之后的元素（在合理范围内搜索，避免跨段落）
        search_range = min(50, len(all_elements) - drawing_pos)
        for i in range(1, search_range):
            next_elem = all_elements[drawing_pos + i]

            # 跳过非文本元素
            if next_elem.tag != f'{{{W_NS}}}p':
                continue

            # 提取段落文本
            text = extract_text_from_element(next_elem)
            if not text:
                continue

            # 使用正则表达式匹配"图N"格式（N为阿拉伯数字）
            match = re.search(r'图(\d+)', text)
            if match:
                return match.group(0)  # 返回完整的"图N"格式文本

        return None
    except Exception as e:
        return None


def analyze_document_structure(unpacked_dir, section_boundaries, rels_map):
    """
    分析文档结构，提取章节信息和图片位置。

    使用已构建的 section_boundaries 来确定图片的章节归属。
    """
    document_path = os.path.join(unpacked_dir, 'word', 'document.xml')

    if not os.path.exists(document_path):
        return {
            'sections': {},
            'image_references': {},
            'headers_found': len(section_boundaries),
            'total_drawings': 0
        }

    register_namespaces()

    try:
        tree = ET.parse(document_path)
        root = tree.getroot()
    except Exception as e:
        return {
            'sections': {},
            'image_references': {},
            'headers_found': len(section_boundaries),
            'total_drawings': 0
        }

    all_elements = list(root.iter())

    def get_current_header_for_pos(element_pos):
        """
        根据元素位置确定当前生效的页眉。

        sectPr 在 OOXML 中标记该节内容的结束位置。sectPr_i 之前、
        sectPr_{i-1}之后的元素属于第 i 节。

        重要：必须包含 is_body_end=True 的 sectPr（文档末尾标记），
        否则最后一章（如说明书附图）的内容会被错误地归到前一章节。
        """
        all_boundaries = section_boundaries  # 包含所有sectPr，不排除is_body_end
        for i, b in enumerate(all_boundaries):
            if element_pos < b['position']:
                return b['header_name']

        if all_boundaries:
            return all_boundaries[-1]['header_name']
        return "未分类"

    sections = {}
    section_image_counter = {}
    seen_rids = set()

    drawing_count = 0

    def _add_image_info(r_id, elem_pos, element_for_fig_text=None):
        nonlocal drawing_count
        if not r_id or r_id not in rels_map:
            return
        if r_id in seen_rids:
            return
        seen_rids.add(r_id)

        drawing_count += 1
        media_target = rels_map[r_id]['target']
        media_filename = os.path.basename(media_target)

        header_name = get_current_header_for_pos(elem_pos)

        if header_name not in sections:
            sections[header_name] = []
            section_image_counter[header_name] = 0

        section_image_counter[header_name] += 1
        logical_name = f"{header_name}第{section_image_counter[header_name]}张图"

        fig_text_name = None
        if header_name == '说明书附图' and element_for_fig_text is not None:
            fig_text_name = extract_fig_text_name_after_drawing(element_for_fig_text, all_elements)

        image_info = {
            'logical_name': logical_name,
            'source_file': media_filename,
            'rid': r_id,
            'position': drawing_count,
            'element_position': elem_pos,
            'header_name': header_name,
            'fig_text_name': fig_text_name
        }

        sections[header_name].append(image_info)

    # 方式1：遍历所有 w:drawing 元素（DrawingML格式，现代docx使用）
    for drawing in root.iter(f'{W_NS_F}drawing'):
        drawing_pos = get_element_position(drawing, all_elements)

        blip = drawing.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}blip')
        if blip is None:
            continue

        r_id = blip.get(f'{R_NS_F}embed')
        _add_image_info(r_id, drawing_pos, drawing)

    # 方式2：遍历所有 v:imagedata 元素（VML格式，.doc转.docx后常见）
    V_NS_F = f'{{{V_NS}}}'
    for imagedata in root.iter(f'{V_NS_F}imagedata'):
        elem_pos = get_element_position(imagedata, all_elements)

        r_id = imagedata.get(f'{R_NS_F}id')
        if r_id:
            parent = imagedata
            _add_image_info(r_id, elem_pos, parent)
            continue

        r_id = imagedata.get('id')
        if r_id and r_id.startswith('rId'):
            parent = imagedata
            _add_image_info(r_id, elem_pos, parent)

    # 方式3：遍历 w:object 中的 v:imagedata（旧版OLE嵌入图片）
    for obj_elem in root.iter(f'{W_NS_F}object'):
        for imagedata in obj_elem.iter(f'{V_NS_F}imagedata'):
            elem_pos = get_element_position(imagedata, all_elements)
            r_id = imagedata.get(f'{R_NS_F}id') or imagedata.get('id')
            if r_id:
                _add_image_info(r_id, elem_pos, imagedata)

    # 方式4：兜底 - 从 rels_map 中查找所有图片关系，与已发现的rid对比
    image_rels = {}
    for rid, info in rels_map.items():
        target = info.get('target', '')
        if target.startswith('media/') or '/media/' in target:
            image_rels[rid] = target

    if image_rels and not seen_rids:
        for rid, target in image_rels.items():
            media_filename = os.path.basename(target)
            header_name = "未分类"
            if header_name not in sections:
                sections[header_name] = []
                section_image_counter[header_name] = 0
            section_image_counter[header_name] += 1
            drawing_count += 1
            logical_name = f"{header_name}第{section_image_counter[header_name]}张图"
            sections[header_name].append({
                'logical_name': logical_name,
                'source_file': media_filename,
                'rid': rid,
                'position': drawing_count,
                'element_position': -1,
                'header_name': header_name,
                'fig_text_name': None
            })

    # 构建图片引用映射（检测重复引用）
    image_references = {}

    for section_name, images in sections.items():
        for img in images:
            source_file = img['source_file']
            logical_name = img['logical_name']

            if source_file not in image_references:
                image_references[source_file] = []

            image_references[source_file].append(logical_name)

    result = {
        'sections': sections,
        'image_references': image_references,
        'headers_found': len(section_boundaries),
        'total_drawings': drawing_count
    }

    return result


def _extract_figure_references_from_text(sections_text):
    """
    从说明书章节文本中提取附图说明部分引用的所有图号。

    扫描说明书的"附图说明"子章节，提取所有"图N"格式的引用，
    用于与实际图片的fig_text_name交叉比对，检测缺失图号。

    Args:
        sections_text: 按页眉章节提取的文本列表（extract_paragraphs_by_section的返回值）

    Returns:
        图号引用列表，每个元素为 {'figure_name': '图1', 'figure_number': 1, 'description': '...是...'}
        如果未找到附图说明章节，返回空列表
    """
    if not sections_text:
        return []

    description_section = None
    for section in sections_text:
        if section.get('section_name') == '说明书':
            description_section = section
            break

    if not description_section:
        return []

    paragraphs = description_section.get('paragraphs', [])

    in_fig_description = False
    fig_refs = []

    for para in paragraphs:
        stripped = para.strip()

        if re.search(r'附\s*图\s*说\s*明', stripped):
            in_fig_description = True
            continue

        if in_fig_description:
            if re.search(r'具\s*体\s*实\s*施\s*方\s*式', stripped):
                break

            matches = re.finditer(r'图(\d+)', stripped)
            for match in matches:
                fig_num = int(match.group(1))
                fig_name = f'图{fig_num}'
                description = stripped[:100] if len(stripped) > 100 else stripped

                already_found = any(r['figure_number'] == fig_num for r in fig_refs)
                if not already_found:
                    fig_refs.append({
                        'figure_name': fig_name,
                        'figure_number': fig_num,
                        'description': description
                    })

    return fig_refs


def generate_image_json_report(analysis_result, docx_filename, output_path,
                               extracted_images=None, sections_text=None):
    """
    生成图片分析的 JSON 报告。

    增强功能：
    1. 包含图片元数据（尺寸、格式、DPI等）
    2. 检测缺失图号（附图说明中提及但无对应图片的图号）
    3. 检测摘要附图来源合规性

    Args:
        analysis_result: analyze_document_structure 的返回结果
        docx_filename: 文档文件名
        output_path: 输出路径
        extracted_images: extract_images 的返回结果（含元数据）
        sections_text: 按章节提取的文本列表（用于提取附图说明中的图号引用）
    """
    report = {
        'document_info': {
            'filename': docx_filename,
            'total_sections': len(analysis_result['sections']),
            'headers_found': analysis_result['headers_found'],
            'extraction_time': datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        },
        'sections': [],
        'image_reference_map': {},
        'statistics': {
            'total_unique_images': 0,
            'total_references': 0,
            'duplicate_references': 0
        }
    }

    # 构建图片元数据映射（source_file -> metadata）
    image_metadata_map = {}
    if extracted_images:
        for img_info in extracted_images:
            image_metadata_map[img_info['name']] = img_info.get('metadata', {})

    total_refs = 0
    duplicate_refs = 0

    # 收集所有实际存在的fig_text_name
    actual_fig_names = set()

    # 按章节组织图片信息
    for section_name, images in analysis_result['sections'].items():
        section_data = {
            'section_name': section_name,
            'image_count': len(images),
            'images': []
        }

        for img in images:
            source_file = img['source_file']
            logical_name = img['logical_name']

            ref_list = analysis_result['image_references'].get(source_file, [])
            is_duplicate = len(ref_list) > 1
            duplicates_in = [ref for ref in ref_list if ref != logical_name]

            if is_duplicate:
                duplicate_refs += 1

            total_refs += 1

            fig_text_name = img.get('fig_text_name', None)
            if fig_text_name:
                actual_fig_names.add(fig_text_name)

            image_detail = {
                'logical_name': logical_name,
                'source_file': source_file,
                'is_duplicate': is_duplicate,
                'duplicates_in': duplicates_in,
                'fig_text_name': fig_text_name
            }

            # 附加图片元数据
            if source_file in image_metadata_map:
                image_detail['metadata'] = image_metadata_map[source_file]

            section_data['images'].append(image_detail)

        report['sections'].append(section_data)

    # 填充图片引用映射
    for source_file, refs in analysis_result['image_references'].items():
        report['image_reference_map'][source_file] = {
            'referenced_by': refs,
            'reference_count': len(refs)
        }

    unique_images = len(analysis_result['image_references'])

    report['statistics'] = {
        'total_unique_images': unique_images,
        'total_references': total_refs,
        'duplicate_references': duplicate_refs
    }

    # ========== 缺失图号检测 ==========
    # 从附图说明文本中提取所有"图N"引用，与实际图片的fig_text_name交叉比对
    text_referenced_figures = _extract_figure_references_from_text(sections_text)
    if text_referenced_figures:
        missing_figures = []
        for fig_ref in sorted(text_referenced_figures, key=lambda x: x['figure_number']):
            if fig_ref['figure_name'] not in actual_fig_names:
                missing_figures.append(fig_ref)

        report['text_referenced_figures'] = text_referenced_figures
        report['missing_figures'] = missing_figures

        if missing_figures:
            missing_names = [f['figure_name'] for f in missing_figures]
            print(f"  ⚠️ 检测到缺失图号: {', '.join(missing_names)}")
            print(f"     附图说明中提及的图号: {sorted([f['figure_name'] for f in text_referenced_figures])}")
            print(f"     实际图片对应的图号: {sorted(actual_fig_names) if actual_fig_names else '无'}")

    # ========== 摘要附图来源合规性检测 ==========
    abstract_fig_source = None
    description_fig_sources = set()
    for section_data in report['sections']:
        if section_data['section_name'] == '摘要附图':
            for img in section_data['images']:
                abstract_fig_source = img['source_file']
        elif section_data['section_name'] == '说明书附图':
            for img in section_data['images']:
                description_fig_sources.add(img['source_file'])

    if abstract_fig_source and description_fig_sources:
        abstract_fig_from_description = abstract_fig_source in description_fig_sources
        report['abstract_fig_compliance'] = {
            'abstract_fig_source': abstract_fig_source,
            'is_from_description_figs': abstract_fig_from_description,
            'description_fig_sources': sorted(description_fig_sources),
            'note': '摘要附图应当是说明书附图中的一幅' if not abstract_fig_from_description else '摘要附图来源合规'
        }
        if not abstract_fig_from_description:
            print(f"  ⚠️ 摘要附图来源不合规: {abstract_fig_source} 不在说明书附图中")

    # 写入 JSON 文件
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"✓ 图片分析报告已生成: {output_path}")
    print(f"  - 唯一图片数: {unique_images}")
    print(f"  - 总引用次数: {total_refs}")
    print(f"  - 重复引用次数: {duplicate_refs}")
    print(f"  - 章节数量: {len(analysis_result['sections'])}")

    return report


def convert_to_legacy_format(sections_text):
    """
    将按页眉章节提取的结果转换为传统的5章节格式。

    以保持向后兼容性，输出格式与旧版本一致。
    """
    result = {
        "abstract_text": "",
        "abstract_fig": "",
        "claims": "",
        "description": "",
        "description_figs": ""
    }

    section_mapping = {
        "说明书摘要": "abstract_text",
        "摘要附图": "abstract_fig",
        "权利要求书": "claims",
        "说明书": "description",
        "说明书附图": "description_figs"
    }

    for section in sections_text:
        section_name = section['section_name']
        content = '\n'.join(section['paragraphs'])

        if section_name in section_mapping:
            result[section_mapping[section_name]] = content
        else:
            # 对于未识别的章节，尝试模糊匹配
            for expected, key in section_mapping.items():
                if expected in section_name or section_name in expected:
                    if not result[key]:  # 只在为空时填充
                        result[key] = content
                    break

    return result


def extract_full_text(sections_text):
    """从所有章节提取完整文本。"""
    all_paragraphs = []
    for section in sections_text:
        all_paragraphs.extend(section['paragraphs'])
    return '\n'.join(all_paragraphs)


def process_docx(file_path, work_dir=None):
    """
    处理 docx 文件的主函数。

    返回: (sections_text, section_boundaries, extracted_images, unpacked_dir, rels_map)
    """
    input_path = Path(file_path)
    converted_docx = None
    actual_input = str(input_path)

    # 如果是 .doc 格式，先转换为 .docx
    if input_path.suffix.lower() == ".doc":
        print(f"检测到 .doc 格式文件，正在转换为 .docx ...")
        try:
            docx_path, was_converted = ensure_docx(str(input_path))
            if was_converted:
                converted_docx = docx_path
                actual_input = docx_path
        except Exception as e:
            raise RuntimeError(f"无法转换 .doc 文件: {e}")

    try:
        # 创建临时工作目录用于解压
        if work_dir:
            unpacked_dir = os.path.join(work_dir, 'unpacked')
        else:
            import tempfile
            unpacked_dir = tempfile.mkdtemp(prefix='docx_unpacked_')

        os.makedirs(unpacked_dir, exist_ok=True)

        # 解压 docx
        unpack_docx(actual_input, unpacked_dir)

        # 解析页眉和关系文件
        register_namespaces()
        headers_raw = parse_headers(unpacked_dir)
        rels_map = parse_relationships(unpacked_dir)

        # 构建章节映射
        section_boundaries = build_section_map(unpacked_dir, headers_raw, rels_map)

        # 按章节提取文本
        sections_text = extract_paragraphs_by_section(unpacked_dir, section_boundaries)

        # 提取图片
        images_output_dir = os.path.join(work_dir, 'images') if work_dir else None
        if images_output_dir:
            os.makedirs(images_output_dir, exist_ok=True)
            extracted_images = extract_images(unpacked_dir, images_output_dir)
        else:
            extracted_images = []

        return sections_text, section_boundaries, extracted_images, unpacked_dir, rels_map

    finally:
        # 清理临时转换文件
        if converted_docx:
            try:
                Path(converted_docx).unlink()
            except OSError:
                pass


def main():
    parser = argparse.ArgumentParser(description='Extract and split Chinese patent .docx with OOXML parsing')
    parser.add_argument('input', type=str, help='Input .docx/.doc file path')
    parser.add_argument('--extract-only', action='store_true', help='Extract full text only, print to stdout')
    parser.add_argument('--extract-output', type=str, metavar='FILE', help='Extract full text and write to file (UTF-8)')
    parser.add_argument('--output-json', type=str, metavar='FILE', help='Output split sections as JSON to file')
    parser.add_argument('--split-sections', type=str, metavar='DIR', help='Split sections into individual JSON files in the specified directory')
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    if not input_path.suffix.lower() in ('.docx', '.doc'):
        print(f"Error: Only .docx and .doc files are supported, got: {input_path.suffix}", file=sys.stderr)
        sys.exit(1)

    # 【BUG-008修复】环境健康检查（在文档处理前执行）
    env_health = check_environment_health()

    # 处理文档
    work_dir = None
    if args.split_sections:
        work_dir = str(Path(args.split_sections))
    elif args.extract_output or args.output_json:
        work_dir = str(Path(args.extract_output or args.output_json).parent)

    sections_text, section_boundaries, extracted_images, unpacked_dir, rels_map = process_docx(str(input_path), work_dir)

    # 提取完整文本
    full_text = extract_full_text(sections_text)

    if args.extract_only:
        print(full_text)
        return

    if args.extract_output:
        output_path = Path(args.extract_output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_text)
        print(f"Extracted text written to: {output_path}")
        return

    # 转换为传统格式以保持向后兼容
    legacy_result = convert_to_legacy_format(sections_text)

    if args.split_sections:
        split_dir = Path(args.split_sections)
        split_dir.mkdir(parents=True, exist_ok=True)
        timestamp_match = re.search(r'(\d{8}_\d{6})', str(split_dir.name))
        ts = timestamp_match.group(1) if timestamp_match else "unknown"

        # 输出完整文本文件
        extracted_text_file = split_dir / f"extracted_text_{ts}.txt"
        with open(extracted_text_file, 'w', encoding='utf-8') as f:
            f.write(full_text)

        # 输出各章节拆分文件
        section_files = {
            "abstract_text": f"section_abstract_text_{ts}.json",
            "claims": f"section_claims_{ts}.json",
            "description": f"section_description_{ts}.json",
            "description_figs": f"section_description_fig_{ts}.json",
            "abstract_fig": f"section_abstract_fig_{ts}.json",
        }
        for key, filename in section_files.items():
            filepath = split_dir / filename
            section_content = legacy_result.get(key, "")
            section_paragraphs = [p for p in section_content.split('\n') if p.strip()] if section_content else []
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({"section_name": key, "paragraphs": section_paragraphs}, f, ensure_ascii=False, indent=2)

        # 输出按页眉章节的详细信息（核心输出文件1）
        header_sections_path = split_dir / f"header_sections_{ts}.json"
        header_sections_data = {
            'extraction_time': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
            'sections': []
        }
        for section in sections_text:
            char_count_no_spaces = len('\n'.join(section['paragraphs']).replace(' ', '').replace('\u3000', '').replace('\t', '').replace('\n', '').replace('\r', ''))
            header_sections_data['sections'].append({
                'section_name': section['section_name'],
                'paragraph_count': len(section['paragraphs']),
                'char_count_no_spaces': char_count_no_spaces,
                'paragraphs': section['paragraphs']
            })
        with open(header_sections_path, 'w', encoding='utf-8') as f:
            json.dump(header_sections_data, f, ensure_ascii=False, indent=2)

        print(f"✅ 文本提取完成:")
        print(f"  - 完整文本: {extracted_text_file}")
        print(f"  - 页眉章节JSON: {header_sections_path}")
        for key, filename in section_files.items():
            print(f"  - 章节[{key}]: {split_dir / filename}")

        # ========== 图片分析与报告生成（核心输出文件2）==========
        print(f"\n📊 开始图片分析...")

        # 分析文档结构中的图片位置
        image_analysis_result = analyze_document_structure(unpacked_dir, section_boundaries, rels_map)

        # 生成图片分析报告
        image_report_path = split_dir / f"image_analysis_{ts}.json"
        docx_filename = os.path.basename(str(input_path))

        if image_analysis_result['total_drawings'] > 0:
            image_report = generate_image_json_report(
                image_analysis_result,
                docx_filename,
                str(image_report_path),
                extracted_images=extracted_images,
                sections_text=sections_text
            )
            print(f"\n✅ 图片分析完成:")
            print(f"  - 图片分析报告: {image_report_path}")

            # 输出各章节图片详情
            if image_report['sections']:
                print(f"\n📷 各章节图片分布:")
                for section in image_report['sections']:
                    print(f"  【{section['section_name']}】 ({section['image_count']} 张)")
                    for img in section['images']:
                        dup_marker = " 🔁重复" if img['is_duplicate'] else ""
                        fig_name = f" → {img['fig_text_name']}" if img.get('fig_text_name') else ""
                        print(f"    - {img['logical_name']} → {img['source_file']}{fig_name}{dup_marker}")
        else:
            # 即使没有图片也生成空报告
            empty_report = {
                'document_info': {
                    'filename': docx_filename,
                    'total_sections': 0,
                    'headers_found': len(section_boundaries),
                    'extraction_time': datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
                },
                'sections': [],
                'image_reference_map': {},
                'statistics': {
                    'total_unique_images': 0,
                    'total_references': 0,
                    'duplicate_references': 0
                }
            }
            with open(image_report_path, 'w', encoding='utf-8') as f:
                json.dump(empty_report, f, ensure_ascii=False, indent=2)
            print(f"  ⚠️ 未在文档中发现图片，已生成空报告: {image_report_path}")

        # 输出图片文件信息
        if extracted_images:
            print(f"\n📁 提取的图片文件:")
            for img in extracted_images:
                print(f"  - {img['name']} ({img['size']} bytes)")
            print(f"  图片保存位置: {os.path.join(work_dir, 'images')}")

        print(f"\n{'='*60}")
        print(f"✅ 全部完成！已生成以下核心文件供后续分析使用:")
        print(f"  1️⃣  {header_sections_path.name} (按页眉章节的文本)")
        print(f"  2️⃣  {image_report_path.name} (图片分析报告)")
        print(f"{'='*60}")

        return

    if args.output_json:
        output_path = Path(args.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(legacy_result, f, ensure_ascii=False, indent=2)
        print(f"Output written to: {output_path}")
    else:
        print(json.dumps(legacy_result, ensure_ascii=False, indent=2))


# 当直接运行此脚本时执行 main 函数
if __name__ == '__main__':
    main()
