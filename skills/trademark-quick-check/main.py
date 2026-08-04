#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
商标快速预查 - 核心功能模块

功能：
1. 音/形/义三维度近似度量化评分
2. 图形商标维也纳编码生成
3. 盲查期风险提示
"""

import re
import math
import json
import sys
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple, Any


# ============================================================
# 维也纳分类编码映射表（快速查询用）
# ============================================================

VIENNA_CLASSIFICATION = {
    '星': '01.01', '星星': '01.01', '星辰': '01.01',
    '太阳': '01.03', '日光': '01.03',
    '月亮': '01.05', '月球': '01.05',
    '男性': '02.01', '男人': '02.01', '男孩': '02.01',
    '女性': '02.03', '女人': '02.03', '女孩': '02.03',
    '人': '02.07', '人物': '02.07', '人脸': '02.07',
    '哺乳动物': '03.01', '狗': '03.01', '猫': '03.01',
    '马': '03.01', '牛': '03.01', '狮子': '03.01',
    '老虎': '03.01', '大象': '03.01',
    '鸟': '03.03', '鸟类': '03.03', '凤凰': '03.03',
    '鹰': '03.03', '鸽子': '03.03',
    '鱼': '03.07', '鱼类': '03.07',
    '花': '05.01', '花朵': '05.01', '花卉': '05.01',
    '玫瑰': '05.01', '莲花': '05.01', '牡丹': '05.01',
    '叶': '05.03', '叶子': '05.03', '树叶': '05.03',
    '树木': '05.05', '树': '05.05', '松树': '05.05',
    '建筑': '07.01', '房子': '07.01', '房屋': '07.01',
    '塔': '07.03', '纪念碑': '07.03',
    '桥': '07.05', '桥梁': '07.05',
    '盾': '24.01', '盾形': '24.01', '盾牌': '24.01',
    '皇冠': '24.03', '王冠': '24.03',
    '箭头': '24.15', '箭': '24.15',
    '圆': '26.01', '圆形': '26.01', '圆圈': '26.01',
    '椭圆': '26.02', '椭圆形': '26.02',
    '多边形': '26.04', '方形': '26.04', '正方形': '26.04',
    '矩形': '26.04', '三角形': '26.04', '菱形': '26.04',
    '线条': '26.11', '线': '26.11', '曲线': '26.11',
    '颜色组合': '29.01', '彩色': '29.01',
    '抽象': '29.02', '抽象图案': '29.02',
}


# ============================================================
# 音/形/义三维度近似度评分
# ============================================================

def _levenshtein_similarity(s1: str, s2: str) -> float:
    """
    莱文斯坦相似度算法
    计算两个字符串的编辑距离，返回归一化相似度（0-1）
    """
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0

    # 确保s1是较短的字符串
    if len(s1) > len(s2):
        s1, s2 = s2, s1

    len1, len2 = len(s1), len(s2)

    # 使用滚动数组优化空间
    prev_row = list(range(len2 + 1))
    for i in range(1, len1 + 1):
        curr_row = [i]
        for j in range(1, len2 + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            curr_row.append(min(
                curr_row[j - 1] + 1,      # 插入
                prev_row[j] + 1,           # 删除
                prev_row[j - 1] + cost     # 替换
            ))
        prev_row = curr_row

    distance = prev_row[len2]
    max_len = max(len1, len2)
    return 1.0 - (distance / max_len)


def _shape_similarity(name1: str, name2: str) -> float:
    """
    字形相似度计算
    基于：
    1. 字面重叠度（相同字符比例）
    2. 笔画特征相似度（通过字符数、结构等）
    """
    if not name1 or not name2:
        return 0.0

    # 1. 字符重叠度
    set1 = set(name1)
    set2 = set(name2)
    if not set1 or not set2:
        return 0.0
    intersection = set1 & set2
    union = set1 | set2
    jaccard = len(intersection) / len(union) if union else 0.0

    # 2. 长度相似度
    len_sim = 1.0 - abs(len(name1) - len(name2)) / max(len(name1), len(name2)) if max(len(name1), len(name2)) > 0 else 0.0

    # 3. 顺序一致性（相同字符的顺序匹配度）
    order_score = 0.0
    if intersection:
        # 从name1中找与name2中相同字符的顺序匹配
        matched = 0
        pos1 = 0
        for ch in name2:
            if ch in intersection:
                idx = name1.find(ch, pos1)
                if idx >= pos1:
                    matched += 1
                    pos1 = idx + 1
        order_score = matched / len(intersection) if intersection else 0.0

    # 综合权重：重叠度0.5，长度相似度0.25，顺序一致性0.25
    score = jaccard * 0.5 + len_sim * 0.25 + order_score * 0.25
    return min(score, 1.0)


def _pinyin_similarity(s1: str, s2: str) -> float:
    """
    拼音相似度（简化版）
    通过首字母匹配和字符数近似度判断
    """
    if not s1 or not s2:
        return 0.0

    # 简易拼音映射（仅常用字）
    pinyin_map = {
        'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6, 'g': 7,
        'h': 8, 'j': 9, 'k': 10, 'l': 11, 'm': 12, 'n': 13,
        'p': 14, 'q': 15, 'r': 16, 's': 17, 't': 18,
        'w': 19, 'x': 20, 'y': 21, 'z': 22,
    }

    # 提取首字母（简化处理，取每个字符的Unicode拼音首字母近似）
    def get_initials(text):
        initials = []
        for ch in text:
            if '\u4e00' <= ch <= '\u9fff':
                # 中文字符，用Unicode编码近似
                code = (ord(ch) - 0x4e00) // 2000
                initials.append(code)
            else:
                initials.append(ord(ch))
        return initials

    init1 = get_initials(s1)
    init2 = get_initials(s2)

    if not init1 or not init2:
        return 0.0

    # 计算首字母序列相似度
    max_len = max(len(init1), len(init2))
    min_len = min(len(init1), len(init2))

    if max_len == 0:
        return 0.0

    # 匹配相同位置的首字母值
    matches = 0
    for i in range(min_len):
        diff = abs(init1[i] - init2[i])
        if diff <= 2:
            matches += 1

    return matches / max_len


def _meaning_similarity(name1: str, name2: str) -> float:
    """
    语义相似度计算
    基于：
    1. 同义词/近义词匹配
    2. 行业关联度
    3. 反义词判断
    """
    if not name1 or not name2:
        return 0.0

    # 同义词/近义词映射（简化版）
    synonym_groups = {
        '鑫': ['金', '财', '富', '盛'],
        '盛': ['昌', '兴', '旺', '荣', '隆'],
        '创': ['新', '造', '开', '立'],
        '新': ['创', '鑫', '星', '晨'],
        '星': ['鑫', '新', '晨', '辰', '光'],
        '晨': ['辰', '星', '曦', '光'],
        '辰': ['晨', '星', '龙'],
        '龙': ['辰', '凤', '祥', '瑞'],
        '凤': ['凰', '龙', '祥', '瑞'],
        '祥': ['瑞', '吉', '安', '康'],
        '瑞': ['祥', '吉', '安'],
        '福': ['禄', '寿', '喜', '吉'],
        '喜': ['福', '乐', '欢'],
        '乐': ['喜', '欢', '快'],
        '美': ['丽', '好', '佳'],
        '佳': ['美', '好', '优'],
        '优': ['佳', '好', '美'],
        '天': ['天', '空', '云'],
        '云': ['天', '云'],
        '海': ['洋', '海', '江'],
        '江': ['河', '海', '川'],
        '山': ['峰', '岳', '岭'],
        '峰': ['山', '岭', '岳'],
        '科': ['技', '研', '创'],
        '技': ['科', '术', '能'],
        '智': ['慧', '能', '聪', '明'],
        '慧': ['智', '聪', '明'],
        '源': ['泉', '源', '本'],
        '本': ['源', '基', '根'],
        '信': ['诚', '诺', '誉'],
        '诚': ['信', '实', '真'],
        '达': ['通', '畅', '顺'],
        '通': ['达', '畅', '顺'],
        '飞': ['翔', '腾', '跃'],
        '腾': ['飞', '翔', '跃'],
        '宏': ['大', '伟', '鸿'],
        '鸿': ['宏', '大', '鸿'],
        '泰': ['安', '稳', '康'],
        '恒': ['久', '永', '长'],
        '永': ['恒', '久', '长'],
        '长': ['永', '恒', '久'],
        '朋': ['友', '宾', '客'],
        '友': ['朋', '谊', '善'],
        '品': ['质', '牌', '誉'],
        '质': ['品', '量', '优'],
        '坊': ['斋', '堂', '轩', '阁'],
        '斋': ['坊', '堂', '轩'],
        '堂': ['斋', '坊', '轩'],
        '轩': ['斋', '堂', '阁'],
        '阁': ['轩', '斋', '堂'],
        '庄': ['园', '苑', '馆'],
        '园': ['庄', '苑', '馆'],
        '馆': ['庄', '园', '苑'],
        '楼': ['阁', '轩', '斋'],
    }

    # 计算语义重叠
    total_score = 0.0
    count = 0

    for ch1 in name1:
        best_match = 0.0
        for ch2 in name2:
            if ch1 == ch2:
                best_match = 1.0
                break
            # 检查同义词
            if ch1 in synonym_groups and ch2 in synonym_groups[ch1]:
                best_match = max(best_match, 0.7)
            elif ch2 in synonym_groups and ch1 in synonym_groups[ch2]:
                best_match = max(best_match, 0.7)
        total_score += best_match
        count += 1

    # 反向计算
    for ch2 in name2:
        best_match = 0.0
        for ch1 in name1:
            if ch2 == ch1:
                best_match = 1.0
                break
            if ch2 in synonym_groups and ch1 in synonym_groups[ch2]:
                best_match = max(best_match, 0.7)
            elif ch1 in synonym_groups and ch2 in synonym_groups[ch1]:
                best_match = max(best_match, 0.7)
        total_score += best_match
        count += 1

    if count == 0:
        return 0.0

    score = total_score / count
    return min(score, 1.0)


def calculate_similarity_score(name1: str, name2: str) -> Dict[str, float]:
    """
    音/形/义三维度近似度量化评分

    Args:
        name1: 第一个商标名称
        name2: 第二个商标名称

    Returns:
        包含各维度评分和综合评分的字典
    """
    # 音（Sound）- 35%权重
    sound_score = (
        _levenshtein_similarity(name1, name2) * 0.5 +
        _pinyin_similarity(name1, name2) * 0.5
    )

    # 形（Shape）- 35%权重
    shape_score = _shape_similarity(name1, name2)

    # 义（Meaning）- 30%权重
    meaning_score = _meaning_similarity(name1, name2)

    # 综合评分
    composite = sound_score * 0.35 + shape_score * 0.35 + meaning_score * 0.30

    # 风险等级判断
    if composite >= 0.75:
        risk_level = '高风险'
        risk_icon = '🔴'
    elif composite >= 0.45:
        risk_level = '中风险'
        risk_icon = '🟡'
    else:
        risk_level = '低风险'
        risk_icon = '🟢'

    return {
        'sound_score': round(sound_score, 4),
        'shape_score': round(shape_score, 4),
        'meaning_score': round(meaning_score, 4),
        'composite_score': round(composite, 4),
        'risk_level': risk_level,
        'risk_icon': risk_icon,
    }


# ============================================================
# 图形商标维也纳编码生成
# ============================================================

def generate_vienna_codes(description: str) -> Dict[str, Any]:
    """
    根据图形商标描述，生成维也纳分类编码

    Args:
        description: 图形商标的文字描述

    Returns:
        包含匹配的维也纳编码和分析结果的字典
    """
    if not description:
        return {
            'codes': [],
            'description': '未提供描述',
            'summary': '无法分析',
        }

    matched_codes = []
    matched_elements = []

    # 从描述中提取元素并匹配维也纳编码
    for keyword, code in sorted(VIENNA_CLASSIFICATION.items(), key=lambda x: -len(x[0])):
        if keyword in description:
            if code not in matched_codes:
                matched_codes.append(code)
                matched_elements.append({
                    'keyword': keyword,
                    'code': code,
                    'category': _get_vienna_category(code),
                })

    # 如果没有匹配到，尝试拆解描述中的字词
    if not matched_codes:
        # 拆解为单个字尝试匹配
        for ch in description:
            if ch in VIENNA_CLASSIFICATION:
                code = VIENNA_CLASSIFICATION[ch]
                if code not in matched_codes:
                    matched_codes.append(code)
                    matched_elements.append({
                        'keyword': ch,
                        'code': code,
                        'category': _get_vienna_category(code),
                    })

    # 生成分类摘要
    if matched_codes:
        categories = list(set(e['category'] for e in matched_elements))
        summary = f"图形包含{len(matched_codes)}个可识别元素：{', '.join(categories)}"
    else:
        summary = "未识别到标准维也纳分类元素，建议人工核验"

    return {
        'codes': matched_codes,
        'elements': matched_elements,
        'summary': summary,
        'description': description,
    }


def _get_vienna_category(code: str) -> str:
    """根据维也纳编码获取大类描述"""
    category_map = {
        '01': '天体',
        '02': '人物',
        '03': '动物',
        '05': '植物',
        '07': '建筑',
        '24': '标识',
        '26': '几何',
        '29': '抽象',
    }
    major = code.split('.')[0]
    return category_map.get(major, '其他')


# ============================================================
# 盲查期风险提示
# ============================================================

def generate_blind_period_warning() -> str:
    """
    生成盲查期风险提示文本

    Returns:
        格式化的盲查期提示文本
    """
    today = datetime.now()
    # 盲查期约1-3个月，建议在1-2周前再次查询
    suggestion_date = today + timedelta(days=14)

    warning = (
        f"⏳ **盲查期风险提示**\n"
        f"• 中国商标注册存在约**1-3个月**的盲查期（数据录入延迟）\n"
        f"• 盲查期内已提交但未公开的商标申请无法被查询到\n"
        f"• 查询日期：{today.strftime('%Y-%m-%d')}\n"
        f"• 建议在提交申请前（{suggestion_date.strftime('%Y-%m-%d')}左右）再次查询确认"
    )
    return warning


# ============================================================
# 输出格式化
# ============================================================

def format_similarity_report(name1: str, name2: str, category: str = '') -> str:
    """
    生成近似度评分报告

    Args:
        name1: 申请商标名称
        name2: 近似商标名称
        category: 商标类别

    Returns:
        格式化的评分报告
    """
    score = calculate_similarity_score(name1, name2)

    lines = []
    lines.append(f"━━━ 近似度评分报告 ━━━")
    lines.append(f"")
    lines.append(f"📋 申请商标：{name1}")
    lines.append(f"📋 近似商标：{name2}")
    if category:
        lines.append(f"📂 查询类别：{category}")
    lines.append(f"")
    lines.append(f"📊 三维度量化评分：")
    lines.append(f"  • 音(Sound) 相似度：{score['sound_score']:.2%}（权重35%）")
    lines.append(f"  • 形(Shape) 相似度：{score['shape_score']:.2%}（权重35%）")
    lines.append(f"  • 义(Meaning) 相似度：{score['meaning_score']:.2%}（权重30%）")
    lines.append(f"  ─────────────────────────────")
    lines.append(f"  • **综合评分：{score['composite_score']:.2%}**")
    lines.append(f"  • **风险等级：{score['risk_icon']} {score['risk_level']}**")
    lines.append(f"")
    lines.append(generate_blind_period_warning())
    lines.append(f"")

    return '\n'.join(lines)


def format_vienna_report(description: str) -> str:
    """
    生成维也纳分类分析报告

    Args:
        description: 图形商标描述

    Returns:
        格式化的维也纳分类报告
    """
    result = generate_vienna_codes(description)

    lines = []
    lines.append(f"━━━ 图形商标维也纳分类分析 ━━━")
    lines.append(f"")
    lines.append(f"🎨 图形描述：{result['description']}")
    lines.append(f"")
    lines.append(f"📋 分析结果：{result['summary']}")
    lines.append(f"")

    if result['elements']:
        lines.append(f"| 元素 | 维也纳编码 | 大类 |")
        lines.append(f"|------|-----------|------|")
        for elem in result['elements']:
            lines.append(f"| {elem['keyword']} | {elem['code']} | {elem['category']} |")

        lines.append(f"")
        lines.append(f"🔍 查询策略：")
        codes_str = '+'.join(result['codes'])
        lines.append(f"  • 搜索词：`{codes_str}`")
        lines.append(f"  • 推荐查询：TMview (https://www.tmdn.org/tmview/)")
    else:
        lines.append(f"⚠️ 未识别到标准维也纳分类元素")
        lines.append(f"建议手动查询或提供更详细的图形描述")

    lines.append(f"")

    return '\n'.join(lines)


# ============================================================
# 主入口
# ============================================================

def main():
    """
    命令行入口，接受JSON参数
    使用方式：
        python main.py '{"action":"similarity","name1":"满仓红","name2":"满仓红运"}'
        python main.py '{"action":"vienna","description":"一个圆形里面有一只凤凰"}'
        python main.py '{"action":"blind_period_warning"}'
    """
    if len(sys.argv) < 2:
        print(json.dumps({"error": "请传入JSON参数"}))
        sys.exit(1)

    try:
        params = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        print(json.dumps({"error": "参数格式错误，请传入有效的JSON"}))
        sys.exit(1)

    action = params.get('action', '')

    if action == 'similarity':
        name1 = params.get('name1', '')
        name2 = params.get('name2', '')
        category = params.get('category', '')
        if not name1 or not name2:
            print(json.dumps({"error": "请提供name1和name2参数"}))
            sys.exit(1)
        score = calculate_similarity_score(name1, name2)
        report = format_similarity_report(name1, name2, category)
        print(json.dumps({
            "success": True,
            "score": score,
            "report": report,
        }))

    elif action == 'vienna':
        description = params.get('description', '')
        if not description:
            print(json.dumps({"error": "请提供description参数"}))
            sys.exit(1)
        result = generate_vienna_codes(description)
        report = format_vienna_report(description)
        print(json.dumps({
            "success": True,
            "result": result,
            "report": report,
        }))

    elif action == 'blind_period_warning':
        warning = generate_blind_period_warning()
        print(json.dumps({
            "success": True,
            "warning": warning,
        }))

    else:
        print(json.dumps({"error": f"未知的操作类型: {action}"}))
        sys.exit(1)


if __name__ == '__main__':
    main()