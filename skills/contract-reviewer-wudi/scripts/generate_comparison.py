#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对比视图生成器 v1.0.0
生成 Markdown 格式的修订对比表，方便用户快速查看改动

输入：changes.json 或 changes 对象
输出：Markdown 格式的对比表
"""

import json
from pathlib import Path
from typing import List, Dict, Any


def generate_comparison_table(changes: Dict[str, Any], 
                               stance: str = '甲方',
                               round_num: int = 1) -> str:
    """
    生成修订对比表
    
    Args:
        changes: changes.json 内容
        stance: 审核立场（甲方/乙方）
        round_num: 审核轮次
        
    Returns:
        Markdown 格式的对比表
    """
    revisions = changes.get('revisions', [])
    comments = changes.get('comments', [])
    
    # 按风险等级分组
    high_risk = [r for r in revisions if r.get('severity') == '高风险']
    medium_risk = [r for r in revisions if r.get('severity') == '中风险']
    low_risk = [r for r in revisions if r.get('severity') == '低风险' or not r.get('severity')]
    
    md = f"""# 第{round_num}轮修订摘要（{stance}视角）

## 一、修订统计

| 风险等级 | 数量 | 说明 |
|---------|------|------|
| 🔴 高风险 | {len(high_risk)}处 | 必须修改，可能导致重大损失或法律风险 |
| 🟡 中风险 | {len(medium_risk)}处 | 建议修改，可能引发争议或不利解释 |
| 🟢 低风险 | {len(low_risk)}处 | 可选修改，表述不当但不影响实质权利 |

**修订总数**：{len(revisions)}处修订 + {len(comments)}条批注

"""
    
    # 高风险修订
    if high_risk:
        md += "## 二、高风险修订（必须修改）\n\n"
        md += "| 序号 | 条款位置 | 原文（节选） | 修订后 | 修改理由 |\n"
        md += "|------|----------|-------------|--------|----------|\n"
        
        for i, rev in enumerate(high_risk, 1):
            original = rev.get('original_text', '')[:40]
            revised = rev.get('revised_text', '')[:40]
            reason = rev.get('reason', rev.get('comment', ''))[:30]
            para_idx = rev.get('paragraph_index', '?')
            
            md += f"| {i} | 第{para_idx}段 | {original}... | {revised}... | {reason}... |\n"
        
        md += "\n"
    
    # 中风险修订
    if medium_risk:
        md += "## 三、中风险修订（建议修改）\n\n"
        md += "| 序号 | 条款位置 | 原文（节选） | 修订后 | 修改理由 |\n"
        md += "|------|----------|-------------|--------|----------|\n"
        
        for i, rev in enumerate(medium_risk, 1):
            original = rev.get('original_text', '')[:40]
            revised = rev.get('revised_text', '')[:40]
            reason = rev.get('reason', rev.get('comment', ''))[:30]
            para_idx = rev.get('paragraph_index', '?')
            
            md += f"| {i} | 第{para_idx}段 | {original}... | {revised}... | {reason}... |\n"
        
        md += "\n"
    
    # 低风险修订
    if low_risk:
        md += "## 四、低风险修订（可选修改）\n\n"
        md += "| 序号 | 条款位置 | 原文（节选） | 修订后 |\n"
        md += "|------|----------|-------------|--------|\n"
        
        for i, rev in enumerate(low_risk, 1):
            original = rev.get('original_text', '')[:40]
            revised = rev.get('revised_text', '')[:40]
            para_idx = rev.get('paragraph_index', '?')
            
            md += f"| {i} | 第{para_idx}段 | {original}... | {revised}... |\n"
        
        md += "\n"
    
    # 待填项提示
    if comments:
        md += "## 五、待填项提示\n\n"
        md += "| 序号 | 位置 | 提示内容 |\n"
        md += "|------|------|----------|\n"
        
        for i, cmt in enumerate(comments, 1):
            para_idx = cmt.get('paragraph_index', '?')
            comment = cmt.get('comment', cmt.get('text', ''))[:60]
            
            md += f"| {i} | 第{para_idx}段 | {comment}... |\n"
        
        md += "\n"
    
    # 使用说明
    md += """---

## 使用说明

1. 打开 `修订痕迹版.docx`，在 Word 中逐条审阅修订内容
2. 对于高风险修订，建议直接接受
3. 对于中风险修订，根据商业需求决定是否接受
4. 填写空白待填项（合同编号、日期等）
5. 接受所有修订后即为可签署的清洁版

**注意**：修订痕迹版已包含完整法律论证（批注气泡），鼠标悬停可查看详细说明。
"""
    
    return md


def generate_comparison_file(changes_path: Path, 
                               output_path: Path,
                               stance: str = '甲方',
                               round_num: int = 1) -> bool:
    """
    生成对比文件
    
    Args:
        changes_path: changes.json 路径
        output_path: 输出 Markdown 文件路径
        stance: 审核立场
        round_num: 审核轮次
        
    Returns:
        是否成功
    """
    try:
        with open(changes_path, 'r', encoding='utf-8') as f:
            changes = json.load(f)
        
        md = generate_comparison_table(changes, stance, round_num)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md)
        
        return True
    except Exception as e:
        print(f"生成对比文件失败: {e}")
        return False


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 3:
        print("用法: python3 generate_comparison.py <changes.json> <output.md> [--stance 甲方] [--round 1]")
        sys.exit(1)
    
    changes_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    stance = '甲方'
    round_num = 1
    
    for i, arg in enumerate(sys.argv):
        if arg == '--stance' and i + 1 < len(sys.argv):
            stance = sys.argv[i + 1]
        elif arg == '--round' and i + 1 < len(sys.argv):
            round_num = int(sys.argv[i + 1])
    
    success = generate_comparison_file(changes_path, output_path, stance, round_num)
    
    if success:
        print(f"✅ 对比表已生成: {output_path}")
    else:
        sys.exit(1)
