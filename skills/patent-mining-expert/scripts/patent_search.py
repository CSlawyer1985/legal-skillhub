#!/usr/bin/env python3
"""
专利检索辅助脚本
用于构建检索式和整理检索结果
"""

import json
import re
from datetime import datetime
from typing import List, Dict


def build_search_query(keywords: List[str], classification: str = None) -> str:
    """
    构建专利检索式
    
    Args:
        keywords: 关键词列表
        classification: IPC/CPC分类号
    
    Returns:
        检索式字符串
    """
    # 关键词组合
    keyword_query = " AND ".join([f'"{kw}"' for kw in keywords])
    
    # 添加分类号限定
    if classification:
        query = f"({keyword_query}) AND (IPC={classification} OR CPC={classification})"
    else:
        query = keyword_query
    
    return query


def parse_patent_info(text: str) -> Dict:
    """
    解析专利基本信息
    
    Args:
        text: 专利信息文本
    
    Returns:
        解析后的专利信息字典
    """
    info = {
        "patent_number": "",
        "title": "",
        "applicant": "",
        "inventor": "",
        "application_date": "",
        "publication_date": "",
        "abstract": "",
        "ipc": "",
        "cpc": ""
    }
    
    # 专利号提取
    patent_num_match = re.search(r'(CN|US|EP|WO|JP)\d+[A-Z]?', text)
    if patent_num_match:
        info["patent_number"] = patent_num_match.group()
    
    # IPC分类号提取
    ipc_match = re.findall(r'[A-Z]\d{2}[A-Z]\s*\d+/\d+', text)
    if ipc_match:
        info["ipc"] = ", ".join(ipc_match)
    
    return info


def organize_search_results(results: List[Dict]) -> str:
    """
    整理检索结果为Markdown格式
    
    Args:
        results: 检索结果列表
    
    Returns:
        Markdown格式字符串
    """
    md_content = "# 专利检索结果汇总\n\n"
    md_content += f"检索时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    md_content += f"共检索到 {len(results)} 篇相关专利\n\n"
    
    md_content += "## 专利列表\n\n"
    
    for idx, patent in enumerate(results, 1):
        md_content += f"### {idx}. {patent.get('title', '未知标题')}\n\n"
        md_content += f"- **专利号**: {patent.get('patent_number', '未知')}\n"
        md_content += f"- **申请人**: {patent.get('applicant', '未知')}\n"
        md_content += f"- **发明人**: {patent.get('inventor', '未知')}\n"
        md_content += f"- **申请日**: {patent.get('application_date', '未知')}\n"
        md_content += f"- **公开日**: {patent.get('publication_date', '未知')}\n"
        md_content += f"- **IPC分类号**: {patent.get('ipc', '未知')}\n"
        md_content += f"- **摘要**: {patent.get('abstract', '无')[:200]}...\n\n"
        md_content += "---\n\n"
    
    return md_content


def generate_comparison_table(patents: List[Dict], features: List[str]) -> str:
    """
    生成专利对比表格
    
    Args:
        patents: 专利列表
        features: 对比特征列表
    
    Returns:
        Markdown表格字符串
    """
    table = "| 专利号 |"
    table += "|".join(features)
    table += "|\n"
    
    # 表头分隔符
    table += "|--------|" + "|".join(["----" for _ in features]) + "|\n"
    
    # 表格内容
    for patent in patents:
        row = f"| {patent.get('patent_number', '未知')} |"
        for feature in features:
            value = patent.get('features', {}).get(feature, '-')
            row += f" {value} |"
        table += row + "\n"
    
    return table


def save_results_to_json(results: List[Dict], filename: str):
    """保存结果到JSON文件"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"结果已保存到 {filename}")


if __name__ == "__main__":
    # 示例用法
    print("专利检索辅助工具")
    print("=" * 50)
    
    # 构建检索式示例
    keywords = ["人工智能", "图像识别", "深度学习"]
    query = build_search_query(keywords, classification="G06N")
    print(f"\n生成的检索式:\n{query}")
    
    # 解析专利信息示例
    sample_text = """
    CN12345678A 人工智能图像识别方法及系统
    申请人: 某某科技有限公司
    IPC: G06N 3/08, G06V 10/82
    """
    info = parse_patent_info(sample_text)
    print(f"\n解析的专利信息:\n{json.dumps(info, ensure_ascii=False, indent=2)}")
