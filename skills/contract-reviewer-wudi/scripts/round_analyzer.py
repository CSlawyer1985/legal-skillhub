#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合同审核多轮迭代分析器（round_analyzer.py）

自动读取对方修改/批注后的 docx，识别立场，生成回应策略，
输出符合 SKILL 规范的 changes.json，供下一轮批注使用。

⚠️ 触发条件：用户发来对方批注版 + 明确告知自己站在哪一方。
零外部依赖，仅使用 Python 标准库。

输入：含历史批注的 docx（可能来自对方律师修改版）
输出：本轮 changes.json（含完整回应策略）

使用方式：
    python3 scripts/round_analyzer.py \
        对方修改版.docx \
        --our-previous changes-上一轮.json \
        --output round-2/changes.json \
        --round 2
"""

import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from typing import Optional


# ─── Word XML 命名空间 ──────────────────────────────────────────
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'


def qn(tag):
    return f'{{{W}}}{tag}'


# ─── 我方作者识别模式（用于区分轮次和阵营）──────────────────────
# 格式："Claude AI 法律审核" 或 "Claude AI 法律审核（第二轮）"
OUR_AUTHOR_PATTERNS = [
    re.compile(r'^Claude'),
    re.compile(r'^OpenClaw'),
    re.compile(r'^AI.*审核'),
    re.compile(r'.*法律审核.*'),
]


def is_our_comment(author: str) -> bool:
    """判断批注是否来自我方"""
    for pat in OUR_AUTHOR_PATTERNS:
        if pat.match(author.strip()):
            return True
    return False


def extract_round_from_author(author: str) -> Optional[int]:
    """从作者名称中提取轮次编号"""
    m = re.search(r'第[一二三四五六七八九十\d]+轮', author)
    if m:
        round_map = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
                     '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}
        for cn, num in round_map.items():
            if cn in m.group(0):
                return num
        dm = re.search(r'\d+', m.group(0))
        if dm:
            return int(dm.group())
    m2 = re.search(r'\(第(\d+)轮\)', author)
    if m2:
        return int(m2.group(1))
    return None


# ─── 立场分类关键词 ─────────────────────────────────────────────
ACCEPTANCE_PATTERNS = [
    r'已接受', r'已同意', r'已确认', r'已采纳',    # "已"字开头
    r'同意', r'确认', r'接受',                   # 接受（单独出现）
    r'✅', r'☑', r'可以接受', r'确认接受',
    r'无争议', r'无异议',                        # 明确表示无反对意见
    r'(?<![无没])接受[，。].*(?:确认|同意|执行)', # 接受+后续确认词
]

PARTIAL_ACCEPT_PATTERNS = [
    r'部分接受', r'有条件接受', r'原则上同意',
    r'接受[，。].*但', r'同意[，。].*但', r'可以[，。].*但',
]

REBUTTAL_PATTERNS = [
    r'不接受', r'不同意', r'反对', r'无法接受', r'不能接受', r'拒绝',
    r'有异议', r'持异议', r'提出异议',
    r'❌', r'☒', r'反驳', r'反对方',
]

COUNTER_PROPOSAL_PATTERNS = [
    r'建议.*折中', r'各退一步', r'折中', r'调整.*为',
    r'修改为.*或', r'改为.*建议', r'退让', r'妥协',
    r'可接受.*底线', r'让步方案',
]

NEW_ISSUE_PATTERNS = [
    r'新问题', r'新增', r'还发现', r'此外', r'另外',
    r'补充', r'另需', r'还应', r'还应考虑',
]


def classify_stance(text: str) -> str:
    """根据批注文本判断立场（含捆绑式谈判识别）"""
    if not text or not text.strip():
        return 'needs_analysis'

    # 捆绑式谈判检测："接受A条；但B条拒绝；C条需再议"
    sentences = re.split(r'[;；]', text)
    stances = [classify_single_stance(s) for s in sentences if s.strip()]
    unique = list(dict.fromkeys(
        s for s in stances if s not in ('needs_analysis',)))

    if len(set(unique)) > 1:
        return 'bundled'

    return unique[0] if unique else 'needs_analysis'


def classify_single_stance(text: str) -> str:
    """对单条文本（不含分号分隔）做立场分类"""
    for pat in REBUTTAL_PATTERNS:
        if re.search(pat, text): return 'rebuttal'
    for pat in PARTIAL_ACCEPT_PATTERNS:
        if re.search(pat, text): return 'partial_acceptance'
    for pat in ACCEPTANCE_PATTERNS:
        if re.search(pat, text): return 'acceptance'
    for pat in COUNTER_PROPOSAL_PATTERNS:
        if re.search(pat, text): return 'counter_proposal'
    for pat in NEW_ISSUE_PATTERNS:
        if re.search(pat, text): return 'new_issue'
    return 'needs_analysis'


BUNDLED_PATTERNS = {
    'rebuttal':          r'不接受|不同意|反对|拒绝|无法接受',
    'partial_acceptance': r'部分接受|有条件|原则上同意',
    'acceptance':        r'已接受|已同意|无争议|无异议',
    'counter_proposal': r'各退|折中|各让一步',
    'new_issue':        r'新问题|还发现|此外',
}


def parse_bundled_stances(text: str) -> list:
    """解析捆绑式批注中各条独立立场，含条款编号"""
    results = []
    for sent in re.split(r'[;；]', text):
        sent = sent.strip()
        if not sent: continue
        clause = ''
        m = re.search(r'第[一二三四五六七八九十\d]+[条款节章]', sent)
        if m: clause = m.group()
        results.append({
            'stance': classify_single_stance(sent),
            'clause': clause,
            'text': sent,
        })
    return results


def detect_counterparty_position(text: str) -> dict:
    """
    分析对方批注中的核心立场
    返回: {accepts: [], rejects: [], proposes: [], questions: []}
    """
    result = {'accepts': [], 'rejects': [], 'proposes': [], 'questions': [], 'other': []}

    # 检测接受：对方说"接受"、"同意"、"确认"某条建议
    for pat in ACCEPTANCE_PATTERNS:
        for m in re.finditer(pat, text):
            context = text[max(0, m.start()-30):m.end()+30]
            result['accepts'].append(context.strip())

    # 检测拒绝：对方说"不接受"、"反对"、"有异议"
    for pat in REBUTTAL_PATTERNS:
        for m in re.finditer(pat, text):
            context = text[max(0, m.start()-50):m.end()+80]
            result['rejects'].append(context.strip())

    # 检测对方提出新条件/方案
    for pat in COUNTER_PROPOSAL_PATTERNS:
        for m in re.finditer(pat, text):
            context = text[max(0, m.start()-20):m.end()+50]
            result['proposes'].append(context.strip())

    # 检测对方提出的疑问
    if re.search(r'[?？]', text):
        for m in re.finditer(r'[^。]{10,}[?？]', text):
            result['questions'].append(m.group().strip())

    if not any(result.values()):
        result['other'].append(text[:100])

    return result


# ─── 回应生成策略库 ────────────────────────────────────────────
# 针对不同立场类型的回应模板和策略

RESPONSE_STRATEGIES = {
    'acceptance': {
        'template': '✅ 已接受，无需进一步论证。此条按对方确认方案执行即可。',
        'status': 'CLOSED',
    },
    'partial_acceptance': {
        'template': '【谈判立场】对方有条件接受，我方应在对方接受的范围内推进，对分歧部分继续论证。',
        'status': 'NEGOTIATING',
    },
    'rebuttal': {
        'template': '【核心立场】对方提出异议，我方需坚守底线并给出法律论据，必要时适当让步。',
        'status': 'NEGOTIATING',
    },
    'counter_proposal': {
        'template': '【谈判立场】对方提出折中方案，我方应评估其合理性，寻求双方都能接受的平衡点。',
        'status': 'NEGOTIATING',
    },
    'new_issue': {
        'template': '【新增事项】对方提出了原审核范围之外的问题，需单独评估风险并给出意见。',
        'status': 'NEW',
    },
    'needs_analysis': {
        'template': '【需分析】该批注立场不明确，建议进一步确认对方意图后针对性回应。',
        'status': 'PENDING',
    },
}


# ─── 法律论据库（用于生成回应）─────────────────────────────────
# 格式: {关键词: (回应模板, 法律依据列表)}
LEGAL_COUNTER_ARGUMENTS = {
    '违约金过高': {
        'counter': '违约金超过损失30%即可能被法院认定为"过分高于"，我方建议不超过20%，且甲乙双方违约责任应对等。',
        'legal_basis': [
            '《民法典》第585条第2款（违约金调减权）',
            '《最高人民法院关于适用〈民法典〉合同编通则若干问题的解释》第65条',
            '参照(2019)最高法民终xxx号判决要旨',
        ],
        'concession': '可接受20-25%，但须要求甲方违约责任对等封顶。',
    },
    '审计期限': {
        'counter': '无限期审计严重影响承包方资金回收，依据行业惯例应设置合理期限。',
        'legal_basis': [
            '《建设工程价款结算暂行办法》第14条（结算审核期限30日）',
            '《建设工程价款结算暂行办法》第16条',
        ],
        'concession': '可接受90日报送审计+督促条款，放弃硬性时限约束第三方。',
    },
    '质保金': {
        'counter': '3%质保金在两年质保期内是否充足，应结合工程性质和金额判断。',
        'legal_basis': [
            '《建设工程质量保证金管理办法》第7条',
        ],
        'concession': '若对方坚持3%，可接受，但须明确质保期满后15个工作日无息返还。',
    },
    '专票': {
        'counter': '增值税专用发票与普通发票税额差异涉及实际经济利益，合同应明确约定。',
        'legal_basis': [
            '《增值税暂行条例》第1条、第21条',
        ],
        'concession': '此条应坚持，若对方不同意，可在合同价格中额外考虑税费因素。',
    },
    '3天': {
        'counter': '三天内完成大额资金筹措在实践中几乎不可能，属明显不公平条款。',
        'legal_basis': [
            '《民法典》第497条（格式条款的规制）',
            '《民法典》第591条（减损义务的合理期限）',
        ],
        'concession': '底线7个工作日，这是我方可接受的最优让步。',
    },
    '管辖': {
        'counter': '建设工程施工合同属专属管辖，工程所在地法院具有管辖权，送达地址确认条款保护双方。',
        'legal_basis': [
            '《民事诉讼法》第34条（专属管辖）',
            '《最高人民法院关于适用〈民事诉讼法〉的解释》第3条（送达地址确认）',
        ],
        'concession': '若工程在金牛区，管辖条款可接受，但必须增加送达地址确认条款。',
    },
    '合同法': {
        'counter': '《合同法》已于2021年废止，此为法律常识，对方应无异议。',
        'legal_basis': [
            '《民法典》第1269条（合同编附则）',
        ],
        'concession': '直接修改为《民法典》，无需谈判。',
    },
}


def get_counter_argument(issue_key: str) -> Optional[dict]:
    """获取针对特定问题的反驳论据"""
    for key in LEGAL_COUNTER_ARGUMENTS:
        if key in issue_key:
            return LEGAL_COUNTER_ARGUMENTS[key]
    return None


# ─── 核心解析函数 ──────────────────────────────────────────────

def extract_all_comments(docx_path: str) -> list:
    """
    从 docx 中提取所有批注，返回列表：
    [{
        'id': int,
        'author': str,
        'round': Optional[int],
        'is_ours': bool,
        'text': str,
        'stance': str,
        'paragraph_index': Optional[int],  # 如果能关联上的话
        'position_hint': str,  # 批注内容的前50字，用于定位
    }]
    """
    results = []

    with zipfile.ZipFile(docx_path, 'r') as zf:
        # 读取批注文件
        if 'word/comments.xml' not in zf.namelist():
            return results

        xml_content = zf.read('word/comments.xml')
        tree = ET.fromstring(xml_content)

        for comment in tree.findall(qn('comment')):
            cid = int(comment.get(qn('id'), 0))
            author = comment.get(qn('author'), 'Unknown')
            full_text = ''.join(t.text or '' for t in comment.iter(qn('t')))
            stance = classify_stance(full_text)
            round_num = extract_round_from_author(author)
            is_ours = is_our_comment(author)

            results.append({
                'id': cid,
                'author': author,
                'round': round_num,
                'is_ours': is_ours,
                'text': full_text,
                'stance': stance,
                'position_hint': full_text[:60].replace('\n', ' | '),
            })

    return results


def group_by_round(comments: list) -> dict:
    """
    将批注按轮次分组
    返回: {1: [our_comments], 2: [their_comments], ...}
    策略：交替分配（奇数轮我方，偶数轮对方）
    或者按作者名称判断
    """
    rounds = {}
    current_round = 0
    prev_is_ours = True  # 假设从第一轮我方开始

    for c in sorted(comments, key=lambda x: x['id']):
        if c['round'] is not None:
            r = c['round']
        elif c['is_ours'] != prev_is_ours:
            current_round += 1
            prev_is_ours = c['is_ours']
        elif not c['is_ours'] and prev_is_ours:
            current_round += 1
            prev_is_ours = False
        else:
            # 同一方，可能是同一轮的新批注
            pass

        if current_round == 0:
            current_round = 1

        rounds.setdefault(current_round, []).append(c)

    return rounds


def parse_our_previous(json_path: str) -> list:
    """读取我方上一轮的 changes.json"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('comments', [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def analyze_negotiation(comments: list, our_previous: list) -> dict:
    """
    分析谈判态势，识别：
    1. 对方接受了哪些
    2. 对方在争议哪些
    3. 对方提出了什么新问题

    返回结构化的分析结果
    """
    our_comments = [c for c in comments if c['is_ours']]
    their_comments = [c for c in comments if not c['is_ours']]

    analysis = {
        'summary': {
            'total_comments': len(comments),
            'our_comments': len(our_comments),
            'their_comments': len(their_comments),
            'accepted': [],
            'disputed': [],
            'new_issues': [],
            'unclear': [],
        },
        'by_issue': {},  # paragraph_index -> analysis
    }

    # 构建我方原始批注索引（按段落）
    our_by_para = {}
    for c in our_comments:
        # 从文本中推断段落索引（通过高亮文本匹配）
        hint = c['text'][:80]
        our_by_para[c['id']] = {
            'text': c['text'],
            'hint': hint,
            'stance': c['stance'],
        }

    # 分析对方每条批注
    for tc in their_comments:
        position = detect_counterparty_position(tc['text'])
        stance = tc['stance']

        item = {
            'their_text': tc['text'][:200],
            'their_stance': stance,
            'accepts': position['accepts'],
            'rejects': position['rejects'],
            'proposes': position['proposes'],
            'questions': position['questions'],
            'our_response_needed': stance in ('rebuttal', 'counter_proposal', 'needs_analysis'),
        }

        # 根据立场分类
        if stance == 'acceptance':
            analysis['summary']['accepted'].append({
                'their_comment': tc['position_hint'],
                'likely_responding_to': '见我方原批注',
            })
        elif stance in ('rebuttal', 'counter_proposal'):
            analysis['summary']['disputed'].append({
                'their_comment': tc['position_hint'],
                'their_stance': stance,
                'proposals': position['proposes'],
            })
        elif stance == 'new_issue':
            analysis['summary']['new_issues'].append({
                'their_comment': tc['position_hint'],
            })
        else:
            analysis['summary']['unclear'].append({
                'their_comment': tc['position_hint'],
            })

    return analysis


def generate_responses(comments: list, analysis: dict) -> list:
    """
    为每条需要回应的批注生成回应策略
    返回符合 changes.json 格式的 comment 条目列表
    """
    responses = []

    # 获取对方的批注
    their_comments = [c for c in comments if not c['is_ours']]
    our_comments = [c for c in comments if c['is_ours']]

    # 构建我方批注索引（按ID）
    our_by_id = {c['id']: c for c in our_comments}

    for tc in their_comments:
        stance = tc['stance']
        text = tc['text']
        position_hint = tc['position_hint']

        # 推断对应的段落索引（从批注文本中搜索）
        # 尝试从文本中提取 highlight_text 或段落引用
        para_hint = infer_paragraph_hint(text)

        if stance == 'acceptance':
            # 对方接受了，我方确认即可
            responses.append({
                'paragraph_index': para_hint.get('index', 0),
                'highlight_text': para_hint.get('highlight', ''),
                'comment': f'【我方确认】对方已接受此条修改建议。{text[:60]}',
                'severity': 'info',
                'reason': '对方书面确认，无争议，可直接按确认方案执行。',
                'legal_basis': '',
                'suggestion': '✅ 接受，纳入最终合同版本。',
            })

        elif stance in ('rebuttal', 'counter_proposal'):
            # 对方有异议，需要认真回应
            # 识别具体问题类型
            issue_key = identify_issue_key(text, our_comments)
            counter = get_counter_argument(issue_key)

            if counter:
                counter_text = counter['counter']
                legal = '；'.join(counter['legal_basis'])
                concession = counter['concession']
            else:
                counter_text = '对方提出异议，我方需就具体问题给出法律回应。'
                legal = '待定，需进一步检索'
                concession = '根据个案情况确定'

            # 生成回应文本
            stance_label = '【反驳】' if stance == 'rebuttal' else '【协商】'
            response_text = (
                f'{stance_label}对方认为：{text[:80]}'
                f'\n\n【我方立场】{counter_text}'
            )

            responses.append({
                'paragraph_index': para_hint.get('index', 0),
                'highlight_text': para_hint.get('highlight', ''),
                'comment': response_text,
                'severity': detect_severity_from_stance(stance),
                'reason': f'对方{stance}，我方坚持立场并提供法律论据。让步空间：{concession}',
                'legal_basis': legal,
                'suggestion': generate_suggestion_from_stance(stance, text, counter),
            })

        elif stance == 'new_issue':
            # 对方提出了新问题，需要单独评估
            responses.append({
                'paragraph_index': para_hint.get('index', 0),
                'highlight_text': para_hint.get('highlight', ''),
                'comment': f'【新增事项】{text[:100]}',
                'severity': assess_new_issue_severity(text),
                'reason': '对方提出了本轮审核范围之外的新问题，需单独评估。',
                'legal_basis': '',
                'suggestion': '请对方提供具体修改建议文本，我方评估后给出法律意见。',
            })

        elif stance == 'partial_acceptance':
            responses.append({
                'paragraph_index': para_hint.get('index', 0),
                'highlight_text': para_hint.get('highlight', ''),
                'comment': f'【谈判进展】对方有条件接受：{text[:80]}',
                'severity': '中风险',
                'reason': '对方部分接受，我方应对接受部分表示认可，对分歧部分继续论证。',
                'legal_basis': '',
                'suggestion': '建议整理双方已达成的共识点和分歧点，分别处理。',
            })

        elif stance == 'bundled':
            # 捆绑式谈判：解析各条立场，分别生成回应
            sub_stances = parse_bundled_stances(text)
            accepted_parts = [s for s in sub_stances if s['stance'] == 'acceptance']
            rebutted_parts = [s for s in sub_stances if s['stance'] == 'rebuttal']
            partial_parts  = [s for s in sub_stances if s['stance'] == 'partial_acceptance']
            new_parts      = [s for s in sub_stances if s['stance'] == 'new_issue']
            counter_parts  = [s for s in sub_stances if s['stance'] == 'counter_proposal']

            summary_lines = []
            if accepted_parts: summary_lines.append(f'接受{len(accepted_parts)}条')
            if rebutted_parts: summary_lines.append(f'拒绝{len(rebutted_parts)}条')
            if partial_parts:  summary_lines.append(f'部分接受{len(partial_parts)}条')
            if new_parts:      summary_lines.append(f'新问题{len(new_parts)}条')

            bundle_comment = '【捆绑式谈判】' + '、'.join(summary_lines)
            if rebutted_parts:
                bundle_comment += '\n【重点关注】对方拒绝条款：' + '；'.join(
                    f'{s["clause"] or s["text"][:30]}' for s in rebutted_parts[:3])

            responses.append({
                'paragraph_index': para_hint.get('index', 0),
                'highlight_text': para_hint.get('highlight', ''),
                'comment': bundle_comment,
                'severity': '高风险' if rebutted_parts else '中风险',
                'reason': f'捆绑式谈判，涉及：{"；".join(summary_lines)}。需对每条分别评估并生成回应。',
                'legal_basis': '',
                'suggestion': f'接受{len(accepted_parts)}条；继续论证{len(rebutted_parts)}条拒绝项；评估{len(new_parts)}条新问题',
            })

        else:
            # 立场不明确，提示需要人工判断
            responses.append({
                'paragraph_index': para_hint.get('index', 0),
                'highlight_text': para_hint.get('highlight', ''),
                'comment': f'【待确认】对方立场不明确，建议人工跟进确认：{text[:80]}',
                'severity': '低风险',
                'reason': '批注内容无法明确判断对方意图，需人工与对方确认。',
                'legal_basis': '',
                'suggestion': '建议直接与对方律师电话或书面沟通明确意图。',
            })

    return responses


def infer_paragraph_hint(text: str) -> dict:
    """
    从批注文本中推断段落信息
    返回: {index: int, highlight: str}
    """
    # 尝试提取引用条款
    clause_match = re.search(r'第[一二三四五六七八九十\d]+条', text)
    clause = clause_match.group(0) if clause_match else ''

    # 尝试提取段落引用 [数字]
    bracket_match = re.search(r'\[(\d+)\]', text)
    para_index = int(bracket_match.group(1)) if bracket_match else 0

    # 尝试提取高亮文本（通常是批注开头引用的原文）
    # 高亮文本通常在【】或「」中
    highlight_match = re.search(r'【[^】]+】([^【】]+)', text)
    if not highlight_match:
        highlight_match = re.search(r'引用[^：：]*[：:]\s*[""\'"\'"]?([^"\'""\'"\'"\n]{5,30})', text)
    highlight = highlight_match.group(1).strip() if highlight_match else ''

    return {'index': para_index, 'clause': clause, 'highlight': highlight}


def identify_issue_key(text: str, our_comments: list) -> str:
    """识别对方争议对应的核心问题类型"""
    text_lower = text.lower()

    keywords_map = [
        ('违约金', '违约金过高'),
        ('30%', '违约金过高'),
        ('审计', '审计期限'),
        ('质保金', '质保金'),
        ('保证金', '质保金'),
        ('发票', '专票'),
        ('增值税', '专票'),
        ('三天', '3天'),
        ('3天', '3天'),
        ('管辖', '管辖'),
        ('送达', '管辖'),
        ('合同法', '合同法'),
        ('民法典', '合同法'),
    ]

    for keyword, issue_key in keywords_map:
        if keyword in text:
            return issue_key

    return '一般条款争议'


def detect_severity_from_stance(stance: str) -> str:
    """根据立场类型推断严重程度"""
    if stance == 'rebuttal':
        return '高风险'
    elif stance == 'counter_proposal':
        return '中风险'
    elif stance == 'partial_acceptance':
        return '中风险'
    else:
        return '低风险'


def assess_new_issue_severity(text: str) -> str:
    """评估新问题的风险等级"""
    high_keywords = ['无效', '违法', '重大', '损失', '违约', '责任', '赔偿']
    medium_keywords = ['争议', '风险', '建议', '明确']

    for kw in high_keywords:
        if kw in text:
            return '高风险'
    for kw in medium_keywords:
        if kw in text:
            return '中风险'
    return '低风险'


def generate_suggestion_from_stance(stance: str, their_text: str, counter: Optional[dict]) -> str:
    """根据立场类型生成建议文本"""
    if stance == 'rebuttal' and counter:
        concession = counter.get('concession', '')
        return f'【底线】{concession}\n【备选】若对方坚持原条款，建议诉诸法院依职权调整。'

    if stance == 'counter_proposal' and counter:
        return f'【评估】对方提出折中方案，我方认为合理部分可接受。\n{counter.get("concession", "")}'

    if stance == 'rebuttal':
        return '【底线】建议坚持原修改方案，若对方坚持异议，建议通过诉讼由法院裁判。'

    return '建议与对方进一步协商。'


# ─── 主函数 ────────────────────────────────────────────────────

def analyze_and_generate(docx_path: str,
                         our_previous_json: Optional[str] = None,
                         output_path: Optional[str] = None,
                         current_round: int = 2,
                         author_name: str = "Claude AI 法律审核") -> dict:
    """
    主入口：分析对方批注并生成回应 changes.json

    参数:
        docx_path: 含历史批注的 docx 文件路径
        our_previous_json: 我方上一轮的 changes.json 路径（可选）
        output_path: 输出 changes.json 路径（可选）
        current_round: 当前轮次编号
        author_name: 本轮批注作者名称
    """
    docx_path = Path(docx_path).resolve()

    if not docx_path.exists():
        return {'error': f'文件不存在: {docx_path}'}

    # Step 1: 提取所有批注
    all_comments = extract_all_comments(str(docx_path))

    if not all_comments:
        return {'error': '文档中未找到任何批注，请确认文件包含批注内容。'}

    # Step 2: 读取我方上一轮 changes.json（如有）
    our_previous = []
    if our_previous_json:
        our_previous = parse_our_previous(our_previous_json)

    # Step 3: 分析谈判态势
    analysis = analyze_negotiation(all_comments, our_previous)

    # Step 4: 生成回应
    responses = generate_responses(all_comments, analysis)

    # Step 5: 构建输出
    result = {
        'author': f'{author_name}（第{current_round}轮）',
        'date': datetime.now().isoformat(),
        'round': current_round,
        'parent_docx': docx_path.name,
        'analysis': {
            'total_comments_in_doc': len(all_comments),
            'their_accepted_count': len(analysis['summary']['accepted']),
            'their_disputed_count': len(analysis['summary']['disputed']),
            'their_new_issues_count': len(analysis['summary']['new_issues']),
            'their_unclear_count': len(analysis['summary']['unclear']),
        },
        'revisions': [],
        'comments': responses,
    }

    # Step 6: 输出
    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f'[OK] 已生成: {output_path}')
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))

    # Step 7: 打印摘要
    print_summary(analysis, responses)

    return result


def print_summary(analysis: dict, responses: list):
    """打印分析摘要"""
    summary = analysis['summary']
    print('\n' + '=' * 50)
    print('  多轮迭代分析报告')
    print('=' * 50)
    print(f'  对方接受: {len(summary["accepted"])} 条')
    print(f'  存在争议: {len(summary["disputed"])} 条')
    print(f'  新增问题: {len(summary["new_issues"])} 条')
    print(f'  立场不明: {len(summary["unclear"])} 条')
    print(f'  本轮将生成回应: {len(responses)} 条')
    print('=' * 50)


def main():
    if len(sys.argv) < 2:
        print('用法:')
        print('  python3 scripts/round_analyzer.py <docx文件> [选项]')
        print('')
        print('选项:')
        print('  --our-previous <json>   我方上一轮的 changes.json')
        print('  --output <json>         输出路径（默认: 标准输出）')
        print('  --round <N>             当前轮次（默认: 2）')
        print('  --author <name>         批注作者名（默认: Claude AI 法律审核）')
        print('')
        print('示例:')
        print('  python3 scripts/round_analyzer.py 对方修改版.docx \\')
        print('    --our-previous round-1/changes.json \\')
        print('    --output round-2/changes.json \\')
        print('    --round 2')
        sys.exit(1)

    docx_path = sys.argv[1]
    kwargs = {}

    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--our-previous':
            kwargs['our_previous_json'] = sys.argv[i + 1]
            i += 2
        elif arg == '--output':
            kwargs['output_path'] = sys.argv[i + 1]
            i += 2
        elif arg == '--round':
            kwargs['current_round'] = int(sys.argv[i + 1])
            i += 2
        elif arg == '--author':
            kwargs['author_name'] = sys.argv[i + 1]
            i += 2
        else:
            i += 1

    result = analyze_and_generate(docx_path, **kwargs)

    if 'error' in result:
        print(f'[ERROR] {result["error"]}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
