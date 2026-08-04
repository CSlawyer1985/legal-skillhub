#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合同文档结构解析器
零外部依赖，仅使用 Python 标准库
从 .docx 文件中提取段落结构、条款编号、定义词、交叉引用等信息
输出结构化 JSON，供 AI 审核时精确定位
"""

import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime

# Word XML 命名空间
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'


def qn(tag):
    """生成带命名空间的标签"""
    return f'{{{W}}}{tag}'


def get_paragraph_text(p_elem):
    """从 w:p 元素中提取纯文本"""
    texts = []
    for t in p_elem.iter(qn('t')):
        if t.text:
            texts.append(t.text)
    return ''.join(texts)


def get_paragraph_style(p_elem):
    """提取段落样式信息"""
    result = {'style': '', 'num_id': '', 'num_level': ''}
    ppr = p_elem.find(qn('pPr'))
    if ppr is None:
        return result
    pstyle = ppr.find(qn('pStyle'))
    if pstyle is not None:
        result['style'] = pstyle.get(f'{{{W}}}val', '')
    numpr = ppr.find(qn('numPr'))
    if numpr is not None:
        numid = numpr.find(qn('numId'))
        if numid is not None:
            result['num_id'] = numid.get(f'{{{W}}}val', '')
        ilvl = numpr.find(qn('ilvl'))
        if ilvl is not None:
            result['num_level'] = ilvl.get(f'{{{W}}}val', '')
    return result


# ============================================================
# 条款编号检测
# ============================================================
CLAUSE_PATTERNS = [
    re.compile(r'^第[一二三四五六七八九十百千万零\d]+条'),
    re.compile(r'^\d+[\.、]\s'),
    re.compile(r'^[（(]\s*[一二三四五六七八九十\d]+\s*[）)]'),
    re.compile(r'^[一二三四五六七八九十]+[、．\.]'),
    re.compile(r'^\d+\.\d+\s'),
    re.compile(r'^第[一二三四五六七八九十百千万零\d]+章'),
    re.compile(r'^第[一二三四五六七八九十百千万零\d]+部分'),
]

# ============================================================
# 定义词检测
# ============================================================
DEF_PATTERNS = [
    re.compile(
        r'[""「」\']?([^""」\'\s]{2,20})[""」\'\']?\s*(?:是指|指的?是|指|定义为|defined\s+as|means)\b'
    ),
    re.compile(
        r'(?:本合同|本协议|本补充协议|本确认书)(?:中|内)?(?:所?称|所述|所指)(?:的|之)?'
        r'[""「」]?([^""」\'\s]{2,20})[""」\'\']'
    ),
    re.compile(r'[""「]?([^""」\s]{2,20})[""」]?\s*[（(]以下简?称[""「]?([^""」\)]+)[""」]?[）)]'),
]

# ============================================================
# 交叉引用检测
# ============================================================
XREF_PATTERNS = [
    re.compile(r'第[一二三四五六七八九十百千万零\d]+条(?:第[一二三四五六七八九十\d]+款)?'),
    re.compile(r'(?:详见?|参见|见|依照|按照|依据|援引|引用|遵照|参照)\b'),
    re.compile(r'(?:附件|附表|附录)\s*[一二三四五六七八九十\d]?(?:之?\d)?'),
]

# ============================================================
# 条款类型粗分类
# ============================================================
CLAUSE_CATEGORIES = {
    '定义': ['定义', '释义', '含义', '术语'],
    '标的': ['标的', '范围', '内容', '工作成果', '交付物', '服务内容'],
    '价款': ['价款', '金额', '费用', '报酬', '价格', '付款', '结算', '开票', '发票'],
    '交付': ['交付', '提供', '移交', '验收', '完成', '上线', '部署'],
    '期限': ['期限', '日期', '时间', '起算', '截止', '有效', '工期'],
    '权利义务': ['权利', '义务', '责任', '职责', '保证', '承诺'],
    '违约': ['违约', '违反', '逾期', '赔偿', '违约金', '罚金', '滞纳金', '损害赔偿'],
    '解除': ['解除', '终止', '退出', '取消'],
    '保密': ['保密', '商业秘密', '保密义务', '保密期限'],
    '知识产权': ['知识产权', '著作权', '版权', '专利', '商标', '许可', '许可使用'],
    '争议解决': ['争议', '仲裁', '诉讼', '管辖', '法院', '调解'],
    '不可抗力': ['不可抗力', 'Force\s+Majeure'],
    '通知': ['通知', '送达', '通讯', '联系'],
    '附则': ['附则', '生效', '修改', '补充', '完整协议', '文本份数', '签署'],
    '声明保证': ['声明', '保证', '陈述', '确认', '承诺'],
}


def detect_clause_number(text):
    """检测条款编号，返回匹配的编号字符串或 None"""
    for pat in CLAUSE_PATTERNS:
        m = pat.match(text.strip())
        if m:
            return m.group(0).strip()
    return None


def detect_definitions(text):
    """检测定义词，返回定义词列表"""
    defs_found = []
    for pat in DEF_PATTERNS:
        for m in pat.finditer(text):
            if m.lastindex and m.lastindex >= 1:
                term = m.group(1).strip()
                if term not in defs_found:
                    defs_found.append(term)
    return defs_found


def detect_xrefs(text):
    """检测交叉引用，返回引用列表"""
    refs = []
    for pat in XREF_PATTERNS:
        for m in pat.finditer(text):
            ref = m.group(0).strip()
            if ref not in refs:
                refs.append(ref)
    return refs


def classify_clause(text):
    """粗略分类条款类型"""
    detected = []
    for cat, keywords in CLAUSE_CATEGORIES.items():
        for kw in keywords:
            if kw in text:
                detected.append(cat)
                break
    return detected


def count_words(text):
    """统计字数（中文按字计，英文按词计）"""
    chinese = len(re.findall(r'[\u4e00-\u9fff]', text))
    english_words = len(re.findall(r'[a-zA-Z]+', text))
    return chinese + english_words


def parse_docx(docx_path, output_json=None):
    """
    解析 .docx 文件，输出结构化 JSON

    参数:
        docx_path: .docx 文件路径
        output_json: 输出 JSON 文件路径（可选，不传则打印到 stdout）
    """
    path = Path(docx_path).resolve()

    if not path.exists():
        result = {'error': f'文件不存在: {path}'}
        _output(result, output_json)
        return result

    if not path.suffix.lower() == '.docx':
        result = {'error': f'非 .docx 文件: {path.suffix}'}
        _output(result, output_json)
        return result

    paragraphs = []
    all_definitions = []
    all_xrefs = []
    clause_index = {}  # 条款编号 -> 段落索引列表
    total_words = 0

    try:
        with zipfile.ZipFile(path, 'r') as zf:
            # 检查是否存在 word/document.xml
            if 'word/document.xml' not in zf.namelist():
                result = {'error': '无效的 .docx 文件：缺少 word/document.xml'}
                _output(result, output_json)
                return result

            xml_content = zf.read('word/document.xml')
            tree = ET.fromstring(xml_content)

            body = tree.find(qn('body'))
            if body is None:
                result = {'error': '无法解析文档主体'}
                _output(result, output_json)
                return result

            idx = 0
            for p_elem in body.iter(qn('p')):
                text = get_paragraph_text(p_elem).strip()
                style_info = get_paragraph_style(p_elem)

                if not text:
                    paragraphs.append({
                        'index': idx,
                        'text': '',
                        'style': style_info['style'],
                        'empty': True,
                    })
                    idx += 1
                    continue

                clause_num = detect_clause_number(text)
                definitions = detect_definitions(text)
                xrefs = detect_xrefs(text)
                categories = classify_clause(text)
                word_count = count_words(text)
                total_words += word_count

                if clause_num:
                    clause_index.setdefault(clause_num, []).append(idx)

                for d in definitions:
                    if d not in all_definitions:
                        all_definitions.append(d)

                for x in xrefs:
                    if x not in all_xrefs:
                        all_xrefs.append(x)

                paragraphs.append({
                    'index': idx,
                    'text': text,
                    'style': style_info['style'],
                    'num_id': style_info['num_id'],
                    'num_level': style_info['num_level'],
                    'empty': False,
                    'clause_number': clause_num,
                    'definitions': definitions,
                    'cross_references': xrefs,
                    'categories': categories,
                    'word_count': word_count,
                })
                idx += 1

    except zipfile.BadZipFile:
        result = {'error': f'无法打开文件（非有效 ZIP 格式）: {path}'}
        _output(result, output_json)
        return result
    except ET.ParseError as e:
        result = {'error': f'XML 解析失败: {e}'}
        _output(result, output_json)
        return result

    # 构建输出
    result = {
        'file': str(path),
        'file_name': path.name,
        'file_stem': path.stem,
        'parsed_at': datetime.now().isoformat(),
        'statistics': {
            'total_paragraphs': len(paragraphs),
            'non_empty_paragraphs': sum(1 for p in paragraphs if not p.get('empty', True)),
            'total_words': total_words,
            'total_definitions': len(all_definitions),
            'total_cross_references': len(all_xrefs),
            'total_clauses': len(clause_index),
        },
        'structure': {
            'paragraphs': paragraphs,
            'clause_index': clause_index,
        },
        'definitions': all_definitions,
        'cross_references': all_xrefs,
        'category_summary': _build_category_summary(paragraphs),
    }

    _output(result, output_json)
    return result


def _build_category_summary(paragraphs):
    """构建条款类型分布统计"""
    cats = {}
    for p in paragraphs:
        if p.get('empty', True):
            continue
        for c in p.get('categories', []):
            cats[c] = cats.get(c, 0) + 1
    # 按出现次数降序排列
    return dict(sorted(cats.items(), key=lambda x: x[1], reverse=True))


def _output(result, output_json):
    """输出结果"""
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if output_json:
        Path(output_json).parent.mkdir(parents=True, exist_ok=True)
        Path(output_json).write_text(text, encoding='utf-8')
        print(f'已输出: {output_json}')
    else:
        print(text)


# ============================================================
# 合同类型自动检测
# ============================================================
import os

# 缓存已加载的配置
_CONFIG_CACHE = {}


def _get_skill_base():
    """推断 skill 根目录（向上两级从 scripts/）"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(script_dir)   # scripts/ → skill 根目录


def load_contract_type_configs(base_dir=None):
    """加载所有合同类型配置文件，返回 {文件名: 数据}"""
    if base_dir is None:
        base_dir = _get_skill_base()
    cfg_dir = os.path.join(base_dir, 'references', 'contract-types')

    configs = {}
    if not os.path.isdir(cfg_dir):
        return configs

    for fname in os.listdir(cfg_dir):
        if not fname.endswith('.json') or fname == 'template.json':
            continue
        fpath = os.path.join(cfg_dir, fname)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            key = data.get('contract_type_en', fname[:-5])
            configs[key] = data
        except (json.JSONDecodeError, IOError):
            pass
    return configs


def _score_keywords(text, keywords):
    """计算文本中关键词命中得分（忽略大小写）"""
    text_lower = text.lower()
    score = 0
    matched = []
    for kw in keywords:
        # 支持普通字符串和正则表达式两种格式
        import re
        try:
            if re.search(kw, text_lower, re.IGNORECASE):
                score += 1
                matched.append(kw)
        except re.error:
            # 不是合法正则，按普通字符串匹配
            if kw.lower() in text_lower:
                score += 1
                matched.append(kw)
    return score, matched


def detect_contract_type(paragraphs_or_text, configs=None, top_k=3, base_dir=None):
    """
    根据合同文本或段落列表，自动识别合同类型。

    参数:
        paragraphs_or_text: 段落列表（dict）或字符串文本
        configs: 可选，预加载的配置 dict；None 时自动加载
        top_k: 返回前几名候选
        base_dir: 可选，skill 根目录

    返回:
        [
            {
                'type': 'house-sale',
                'name': '房屋买卖合同',
                'confidence': 0.85,
                'matched_keywords': ['房屋', '定金', '过户'],
                'all_keywords': [...],
            },
            ...
        ]
    """
    if configs is None:
        global _CONFIG_CACHE
        if not _CONFIG_CACHE:
            _CONFIG_CACHE.update(load_contract_type_configs(base_dir))
        configs = _CONFIG_CACHE

    # 提取纯文本
    if isinstance(paragraphs_or_text, str):
        text_chunks = [paragraphs_or_text]
    else:
        # 段落列表：取所有非空段落文本，合并前200个以节省时间
        chunks = []
        for p in paragraphs_or_text[:200]:
            t = p if isinstance(p, str) else p.get('text', '')
            if t.strip():
                chunks.append(t)
        text_chunks = chunks

    all_text = '\n'.join(text_chunks)

    scores = []
    for key, cfg in configs.items():
        keywords = cfg.get('keywords_for_detection', [])
        if not keywords:
            continue

        total_score = 0
        all_matched = []

        for chunk in text_chunks[:50]:   # 每次最多扫描50段
            sc, matched = _score_keywords(chunk, keywords)
            total_score += sc
            all_matched.extend(matched)

        if total_score > 0:
            # 归一化：得分 / sqrt(关键词总数)，防止关键词多的类型天然占优
            norm = total_score / (len(keywords) ** 0.5)
            # 同时考虑命中密度（命中词数/总词数）
            density = len(set(all_matched)) / max(len(keywords), 1)
            final_score = norm * (0.6 + 0.4 * density)

            scores.append({
                'type': key,
                'name': cfg.get('contract_type', key),
                'confidence': round(final_score, 3),
                'matched_keywords': list(set(all_matched))[:10],
                'all_keywords': keywords,
            })

    # 按置信度降序，取前 top_k
    scores.sort(key=lambda x: x['confidence'], reverse=True)
    return scores[:top_k]


def main():
    import argparse
    parser = argparse.ArgumentParser(description='合同文档结构解析器')
    parser.add_argument('docx_path', help='待解析的 .docx 文件路径')
    parser.add_argument('output_json', nargs='?', help='输出 JSON 文件路径（可选）')
    parser.add_argument('--detect-type', action='store_true',
                        help='同时执行合同类型自动检测')
    parser.add_argument('--top-k', type=int, default=3,
                        help='返回前几名候选合同类型（默认 3）')
    args = parser.parse_args()

    result = parse_docx(args.docx_path, args.output_json)

    if '--detect-type' in sys.argv or (len(sys.argv) > 1 and sys.argv[1] == '--detect-type'):
        if 'error' not in result:
            paragraphs = result.get('structure', {}).get('paragraphs', [])
            candidates = detect_contract_type(paragraphs, top_k=args.top_k)
            print('\n=== 合同类型检测结果 ===')
            for i, c in enumerate(candidates, 1):
                print(f'  {i}. {c["name"]} ({c["type"]})')
                print(f'     置信度: {c["confidence"]:.2f}')
                print(f'     命中关键词: {", ".join(c["matched_keywords"][:8])}')
            result['_contract_type_detection'] = candidates

            if args.output_json:
                with open(args.output_json, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                print(f'\n已输出: {args.output_json}')
            else:
                print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print('[ERROR] 解析失败，无法执行类型检测')
            sys.exit(1)
    elif 'error' in result:
        print(f'[ERROR] {result["error"]}')
        sys.exit(1)


if __name__ == '__main__':
    main()
