#!/usr/bin/env python3
"""专利申请文书助手 - 生成专利申请文档草稿"""


def generate_patent_draft(
    invention_title: str, invention_desc: str,
    inventor: str, patent_type: str = "发明",
) -> dict:
    """生成专利申请文档草稿"""
    # 提取关键词作为权利要求要素
    keywords = [w for w in invention_desc.split() if len(w) >= 2][:5]
    if not keywords:
        keywords = ["核心组件", "控制单元", "信号处理", "数据传输", "输出模块"]

    technical_field = f"本发明属于{patent_type}专利领域，涉及{invention_title}相关的技术方案。"

    background = (
        f"现有技术在{invention_title}方面存在效率低、成本高、精度不足等问题。"
        "亟需一种新的技术方案来解决上述技术问题。"
    )

    summary = (
        f"本发明提供一种{invention_title}，"
        f"通过{keywords[0] if keywords else '创新技术'}实现{invention_desc[:50]}...的效果，"
        "具有效率高、成本低、精度高等优点。"
    )

    technical_solution = f"一种{invention_title}，其特征在于，包括：\n"
    for i, kw in enumerate(keywords, 1):
        technical_solution += f"  {i}. {kw}模块，用于{kw}相关功能；\n"

    claims = [
        f"1. 一种{invention_title}，其特征在于，包括{', '.join(keywords[:3])}。",
        f"2. 根据权利要求1所述的{invention_title}，其特征在于，所述{keywords[0]}为独立设置的{keywords[0]}单元。",
        f"3. 根据权利要求1所述的{invention_title}，其特征在于，还包括{keywords[-1] if len(keywords)>3 else '辅助'}模块。",
    ]

    return {
        "patent_type": patent_type,
        "title": invention_title,
        "inventor": inventor,
        "technical_field": technical_field,
        "background": background,
        "summary": summary,
        "technical_solution": technical_solution.strip(),
        "claims": claims,
    }


if __name__ == "__main__":
    result = generate_patent_draft(
        "智能温控系统", "一种基于物联网的智能温控系统，通过传感器采集温度数据，AI算法自动调节空调运行参数",
        "张三",
    )
    for k, v in result.items():
        print(f"--- {k} ---\n{v}\n")
