#!/usr/bin/env python3
"""法律意见书 Word 生成（流式函件式模板 + post-check 一致性校验）。
参数通过 stdin JSON 传入，输出至 outputs/。模板结构：
标题/保密标注/首部表格/敬启者/引言四段/第一部分事实/第二部分分析意见/结论/声明/附件/落款。
"""
import json, sys, os, re
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '非争议解决公共标准', 'references'))
from format_docx import create_document
from format_base import *
from docx.shared import Pt


def _num_cn(n):
    """数字→中文序号（1-20）。"""
    m = {1: '一', 2: '二', 3: '三', 4: '四', 5: '五', 6: '六', 7: '七', 8: '八', 9: '九', 10: '十',
         11: '十一', 12: '十二', 13: '十三', 14: '十四', 15: '十五', 16: '十六', 17: '十七', 18: '十八', 19: '十九', 20: '二十'}
    return m.get(n, str(n))


def _risk_label(level):
    m = {'无保留': '无保留意见', '保留': '保留意见', '否定': '否定意见', '无法表示': '无法表示意见'}
    return m.get(level, '')


def _quotes(s):
    """弯引号统一（「」→“”，『』→‘’），对齐 §3 规范。"""
    return (s.replace('\u300c', '\u201c').replace('\u300d', '\u201d')
             .replace('\u300e', '\u2018').replace('\u300f', '\u2019'))


def _cn2num(s):
    """中文数字→阿拉伯数字（用于编号校验）。"""
    m = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
         '十一': 11, '十二': 12, '十三': 13, '十四': 14, '十五': 15, '十六': 16, '十七': 17, '十八': 18, '十九': 19, '二十': 20}
    return m.get(s)


def _post_check(doc, meta, sections):
    """生成后一致性校验（§3 强制）：①章节编号连续 ②方案指代一致 ③全文日期一致。返回问题列表（非空则拒生成）。"""
    issues = []
    full = '\n'.join(p.text for p in doc.paragraphs)
    for t in doc.tables:
        for row in t.rows:
            full += '\n' + ' | '.join(c.text for c in row.cells)

    # ① 章节编号连续：匹配"一、二、三…"及"第一部分/第二部分"
    cn_heads = [(_cn2num(x), x) for x in re.findall(r'^([一二三四五六七八九十]+)、', full, re.M) if _cn2num(x)]
    cn_heads.sort()
    nums = [n for n, _ in cn_heads]
    for i in range(1, len(nums)):
        if nums[i] != nums[i - 1] + 1:
            issues.append(f'章节编号不连续：{_num_cn(nums[i-1])}、后接{_num_cn(nums[i])}、')
    if cn_heads and len(set(nums)) != len(nums):
        issues.append('章节编号重复：存在相同编号')
    # 第一部分/第二部分顺序
    p1 = full.find('第一部分'); p2 = full.find('第二部分')
    if p1 >= 0 and p2 >= 0 and p1 > p2:
        issues.append('结构错误：第二部分出现在第一部分之前')

    # ② 方案指代一致：plan_defs 定义 vs 正文使用
    plan_defs = meta.get('plan_defs') or {}
    if plan_defs:
        for key in plan_defs:
            if full.count(key) == 0:
                issues.append(f'方案指代：{key}（{plan_defs[key]}）在正文中未出现')
        for m in re.finditer(r'方案([一二三四五六七八九十ABCDEFGH])', full):
            label = m.group(1)
            if not any(key.endswith(label) for key in plan_defs):
                issues.append(f'方案指代：出现未定义的方案编号「方案{label}」')
        # 表格与正文指代一致性：统计各方案在正文/表格出现次数均>0
        for key in plan_defs:
            if full.count(key) < 2:
                issues.append(f'方案指代：{key} 仅出现一次，建议核对标题/正文/结论是否覆盖')

    # ③ 全文日期一致：首部表格日期、声明"截至"日期、落款
    date = meta.get('date', '')
    m_date = re.match(r'(\d{4})-(\d{2})-(\d{2})', date) if date else None
    if m_date:
        disp = f'{int(m_date.group(1))}年{int(m_date.group(2))}月{int(m_date.group(3))}日'
        if disp not in full:
            issues.append(f'日期不一致：首部表格日期 {disp} 未出现在文档')
        for m in re.finditer(r'截至(\d{4})年(\d{1,2})月(\d{1,2})日', full):
            if (m.group(1), int(m.group(2)), int(m.group(3))) != (m_date.group(1), int(m_date.group(2)), int(m_date.group(3))):
                issues.append(f'日期不一致：声明中「截至{m.group(0)}」与落款日期 {disp} 不符')
        for m in re.finditer(r'出具日', full):
            issues.append('日期表述不一致：出现「出具日」字样，应统一为具体日期或「截至…日」')
    return issues


def generate_opinion(meta, sections, output_dir="/sandbox/workspace/outputs"):
    """生成流式函件式法律意见书。meta 见 SKILL.md Phase 5。"""
    d = meta.get
    B = []

    # ── 标题与保密标注 ──
    B.append({'type': 'title', 'text': d('title', '法律意见书')})
    if d('confidentiality'):
        B.append({'type': 'right', 'text': d('confidentiality')})
    B.append({'type': 'blank'})

    # ── 首部表格 ──
    m_date = re.match(r'(\d{4})-(\d{2})-(\d{2})', d('date', '')) if d('date') else None
    date_disp = f'{int(m_date.group(1))}年{int(m_date.group(2))}月{int(m_date.group(3))}日' if m_date else d('date', '')
    B.append({'type': 'table', 'attrs': {'cols': ['', ''], 'rows': [
        ['日期', date_disp],
        ['收件人', d('recipient', '')],
        ['发件人', d('law_firm', '')],
        ['事由', d('matter', '')],
    ]}})
    B.append({'type': 'blank'})

    # ── 称谓 ──
    B.append({'type': 'body', 'text': '敬启者：'})

    # ── 引言四段式 ──
    B.append({'type': 'body', 'text': _quotes(d('intro', f'首先，感谢{d("entrusting_party", "")}（下称「贵司」）对{d("law_firm", "")}（下称「我们」）的信任，就{d("matter", "")}，委托我们出具本法律意见书。'))})
    B.append({'type': 'body', 'text': _quotes(d('analysis_method', '根据贵司向我们提供的相关材料，我们依据现行有效的法律、法规和司法解释，结合相关法学理论研究成果、司法实践中的裁判案例以及我们的实践经验，出具本法律意见书，供贵司参考。'))})
    B.append({'type': 'body', 'text': _quotes(d('disclaimer_note', '需要说明的是，根据贵司目前提供的材料及公开信息，我们对本案情况的理解可能并不完整或不准确，下述法律分析意见仅供贵司参考。如贵司进一步提供材料或者向我们介绍新的案件事实，我们可能对下述法律分析意见作出调整或修改。'))})
    B.append({'type': 'body', 'text': _quotes(d('service_note', '如有任何疑问，请随时与我们联系。我们期望以最专业的态度，为贵司提供高水准的法律服务！'))})

    # ── 第一部分 事实背景 ──
    fact_bg = d('fact_background', [])
    if fact_bg:
        B.append({'type': 'h2', 'text': d('part1_title', '第一部分  本案主要事实')})
        for para in fact_bg:
            B.append({'type': 'body', 'text': _quotes(para)})

    # ── 客户关注问题与过渡 ──
    questions = d('client_questions', [])
    if questions:
        B.append({'type': 'body', 'text': _quotes(d('questions_lead', '综合贵司的委托需求，贵司关注的核心问题包括：'))})
        for q in questions:
            B.append({'type': 'body', 'text': _quotes(q)})

    # ── 第二部分 法律分析意见 ──
    B.append({'type': 'h2', 'text': _quotes(d('part2_title', '第二部分  关于本案的法律分析意见'))})
    if questions:
        B.append({'type': 'body', 'text': _quotes(d('transition', '综合目前我们掌握的案件情况，立足于贵司诉求，我们将结合相关法律规定和司法实践经验提出以下法律分析意见，供贵司参考。'))})
    for idx, sec in enumerate(sections, 1):
        title = sec.get('title') or sec.get('question') or f'{_num_cn(idx)}、'
        B.append({'type': 'h2', 'text': _quotes(title)})
        for label, key in [('1. 法律依据', 'legal_basis'), ('2. 事实适用', 'fact_application')]:
            if sec.get(key):
                B.append({'type': 'bold', 'text': label})
                B.append({'type': 'body', 'text': _quotes(sec.get(key, ''))})
        if sec.get('risk_level') or sec.get('risk_judgment'):
            B.append({'type': 'bold', 'text': '3. 风险判断'})
            rl = _risk_label(sec.get('risk_level', ''))
            if rl:
                B.append({'type': 'bold', 'text': f'【意见类型{rl}】'})
            B.append({'type': 'body', 'text': _quotes(sec.get('risk_judgment', ''))})
        if sec.get('conclusion'):
            B.append({'type': 'bold', 'text': '4. 结论'})
            B.append({'type': 'body', 'text': _quotes(sec.get('conclusion', ''))})
        # working_notes 默认不渲染（论证与工作建议分离 §2.7）

    # ── 结论 ──
    conclusions = d('conclusions', [])
    if conclusions:
        B.append({'type': 'h2', 'text': _quotes(d('conclusion_title', '结论'))})
        for para in conclusions:
            B.append({'type': 'body', 'text': _quotes(para)})

    # ── 声明 ──
    declaration = d('declaration', '')
    if declaration:
        B.append({'type': 'h2', 'text': '声明'})
        B.append({'type': 'body', 'text': _quotes(declaration)})

    # ── 附件（可选） ──
    attachments = d('attachments', [])
    if attachments:
        B.append({'type': 'h2', 'text': '附件'})
        for a in attachments:
            B.append({'type': 'body', 'text': _quotes(a)})

    # ── 落款 ──
    B.append({'type': 'blank'})
    B.append({'type': 'blank'})
    B.append({'type': 'right', 'text': f'{d("law_firm", "")}（盖章）'})
    B.append({'type': 'blank'})
    if d('lawyer'):
        B.append({'type': 'right', 'text': f'律师：{d("lawyer")}'})
        B.append({'type': 'blank'})
    B.append({'type': 'right', 'text': _to_chinese_date(d('date', ''))})
    if d('version'):
        B.append({'type': 'right', 'text': f'（版本V{d("version")}）', 'attrs': {'size': Pt(9), 'color': (128, 128, 128)}})

    # ── 生成 ──
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, f'legal_opinion_{datetime.now():%Y%m%d_%H%M%S}.docx')
    doc = create_document(B, output_path=filepath)

    # ── post-check 一致性校验（§3 强制） ──
    issues = _post_check(doc, meta, sections)
    if issues:
        os.remove(filepath)
        raise RuntimeError('生成后一致性校验未通过：\n' + '\n'.join('- ' + i for i in issues))
    return filepath


if __name__ == '__main__':
    try:
        data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)
    try:
        fp = generate_opinion(data.get('meta', {}), data.get('sections', []),
                              data.get('output_dir', '/sandbox/workspace/outputs'))
        print(json.dumps({'status': 'ok', 'filepath': fp}))
    except RuntimeError as e:
        print(json.dumps({'status': 'check_failed', 'error': str(e)}))
        sys.exit(2)
