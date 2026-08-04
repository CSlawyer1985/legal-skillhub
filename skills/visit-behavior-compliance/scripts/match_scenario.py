#!/usr/bin/env python3
"""
场景匹配脚本
将用户描述的拜访场景与行为库中的典型场景进行关键词匹配
返回最相关的行为条目（最多3条）
"""

import json
import sys
import os
import re

def load_behavior_library():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ref_path = os.path.join(script_dir, '..', 'references', 'behavior_library.json')
    with open(ref_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def tokenize(text):
    """简单的中文分词（基于字符n-gram和关键词拆分）"""
    # 移除标点符号
    text = re.sub(r'[^\w\u4e00-\u9fff]', ' ', text)
    # 提取2-4字的中文短语
    tokens = set()
    for i in range(len(text)):
        for n in [2, 3, 4]:
            if i + n <= len(text):
                tokens.add(text[i:i+n])
    return tokens

def match_scenario(user_description, top_k=3):
    """
    将用户描述与行为库进行关键词匹配

    Args:
        user_description: 用户描述的拜访场景
        top_k: 返回最相关的条目数

    Returns:
        最相关的行为列表（按相关度排序）
    """
    library = load_behavior_library()
    user_tokens = tokenize(user_description)

    scores = []
    for behavior in library:
        # 构建行为的搜索文本
        search_text = ' '.join([
            behavior.get('name', ''),
            behavior.get('typical_scenario', ''),
            behavior.get('reason', ''),
            behavior.get('category', ''),
            behavior.get('violative_speech', ''),
            behavior.get('compliant_speech', '')
        ])

        behavior_tokens = tokenize(search_text)

        # 计算交集
        overlap = len(user_tokens & behavior_tokens)

        if overlap > 0:
            scores.append((overlap, behavior))

    # 按得分降序排序
    scores.sort(key=lambda x: x[0], reverse=True)

    return [behavior for _, behavior in scores[:top_k]]

def format_match_results(matches, user_description):
    """格式化匹配结果"""
    if not matches:
        print(f"⚠️ 未找到与"{user_description}"直接匹配的行为，请提供更具体的场景描述。")
        return

    print(f"## 场景匹配结果\n")
    print(f"**用户描述**：{user_description}\n")
    print(f"**匹配到 {len(matches)} 条最相关行为：**\n")

    light_emoji = {'red': '🔴', 'yellow': '🟡', 'green': '🟢'}
    light_label = {'red': '违规', 'yellow': '疑似违规（需报批）', 'green': '合规'}

    for i, behavior in enumerate(matches, 1):
        emoji = light_emoji.get(behavior['light'], '⚪')
        label = light_label.get(behavior['light'], '未知')

        print(f"### 匹配 {i}：{behavior['name']}")
        print(f"**合规结论**：{emoji} {label}")
        print(f"**判定理由**：{behavior['reason']}")
        print(f"**法规依据**：{behavior.get('law_reference', '参见《医药代表备案管理办法》')}")
        print(f"**典型场景**：{behavior['typical_scenario']}")

        if behavior.get('approval_condition'):
            print(f"**报批条件**：{behavior['approval_condition']}")

        if behavior.get('compliant_speech'):
            print(f"\n✅ **合规说法**：{behavior['compliant_speech']}")

        if behavior.get('violative_speech'):
            print(f"\n❌ **违规说法**：{behavior['violative_speech']}")

        print()

def main():
    if len(sys.argv) < 2:
        print("用法：python match_scenario.py <场景描述> [top_k]")
        print("示例：python match_scenario.py '带一本诊疗指南给心内科主任' 3")
        sys.exit(1)

    user_description = sys.argv[1]
    top_k = int(sys.argv[2]) if len(sys.argv) > 2 else 3

    matches = match_scenario(user_description, top_k)
    format_match_results(matches, user_description)

if __name__ == '__main__':
    main()
