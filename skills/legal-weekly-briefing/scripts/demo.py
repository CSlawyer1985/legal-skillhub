#!/usr/bin/env python3
"""Level 0 · 5分钟快速体验:从预置示范候选生成一份演示周报。

用法:
    python3 scripts/demo.py

输出:
    周报_demo_<日期>.md  — 包含 AI+法律(3条) + 纯法律(7条)的演示周报
    周报_demo_<日期>.html — 交互式周报页面（评分/标签/推荐理由/收藏/原文链接）

预置数据:10 条真实法律新闻候选,标注好特征向量。无需手动建 candidates.jsonl,
也无需配置文件。适合首次接触本 skill 的用户快速看到"它最终产出的样子"。
"""

import json
import sys
import os
from datetime import date

# 预置示范候选（带真实 mp.weixin.qq.com 链接 + 完整 HTML 渲染字段）
DEMO_CANDIDATES = [
    {
        "title": "全文发布！涉新质生产力企业典型案例",
        "url": "http://mp.weixin.qq.com/s?__biz=MjM5MjkwMDkxMA==&mid=2649581720&idx=1&sn=9dbab238774e7cc02bc8537cec218cc7&chksm=be86fad989f173cf57b0d3311337411a30609385ce802743df9d56f81c4eb600d6037c75c614#rd",
        "category": "legal",
        "source": "上海一中法院",
        "source_category": "法院 · 权威发布",
        "date": "2026.07",
        "score": 9.0,
        "tags": ["典型案例", "新质生产力", "企业合规", "营商环境"],
        "recommend": "新质生产力是当前政策核心概念。这批案例提供了法院在新经济领域裁判逻辑的重要参照，建议关注其中关于数据权益和绿色转型的裁判要旨。",
        "features": {"author_tier": 2, "platform_tier": 3, "depth": 1, "relevance": 1},
        "preview": "上海一中法院发布涉新质生产力企业典型案例全文，涵盖科技创新、数据权益、绿色转型等前沿领域的司法裁判规则，附完整裁判要旨。",
    },
    {
        "title": "入库案例：抵押预告登记权利人能否就抵押物享有优先受偿权",
        "url": "http://mp.weixin.qq.com/s?__biz=MzA5MDAxMjk5Ng==&mid=2652451717&idx=1&sn=697022fc928809af13d55f3cfa5c627f&chksm=8bffbfaebc8836b821a8c3348383efb2314b8c8315fc43c2c3a57e563d0e6fc9349b43bfb60f#rd",
        "category": "legal",
        "source": "山东高法",
        "source_category": "法院 · 入库案例",
        "date": "2026.07",
        "score": 9.0,
        "tags": ["入库案例", "抵押预告登记", "优先受偿权", "开发商保证"],
        "recommend": "抵押预告登记与阶段性保证的交叉问题在商品房预售纠纷中极为常见。该入库案例对开发商和银行两方均有实务价值。",
        "features": {"author_tier": 2, "platform_tier": 3, "depth": 1, "relevance": 1},
        "preview": "人民法院案例库入库参考案例。围绕抵押预告登记权利人的优先受偿权认定和开发商阶段性保证责任免除问题，附完整裁判要旨。",
    },
    {
        "title": "夫妻借款后离婚，债权人要求一方单独出具借条，是否仍为夫妻共同债务？",
        "url": "http://mp.weixin.qq.com/s?__biz=MzA5MDAxMjk5Ng==&mid=2652451718&idx=1&sn=8d7c1dfb648f9a4169249f37c8638a09&chksm=8bffbfadbc8836bb110fb0e9e6d11f50099a07b4643ed92d839453211b186d7d12fd6097b35e#rd",
        "category": "legal",
        "source": "山东高法",
        "source_category": "法院 · 以案说法",
        "date": "2026.07",
        "score": 8.5,
        "tags": ["婚姻家事", "夫妻债务", "民间借贷", "离婚"],
        "recommend": "离婚后的债务追偿是家事案件与民间借贷交叉领域的高频争议。本文对「离婚协议内部约定能否对抗外部债权人」给出了清晰的分析框架。",
        "features": {"author_tier": 2, "platform_tier": 3, "depth": 1, "relevance": 1},
        "preview": "夫妻双方共同借款后协议离婚，债权人要求一方单独出具借条确认债务。山东高法结合《民法典》第1064条对夫妻共同债务规则进行实务分析。",
    },
    {
        "title": "董监高违反勤勉义务的赔偿责任认定",
        "url": "http://mp.weixin.qq.com/s?__biz=MzA4MzY3NjMxNw==&mid=2656555271&idx=1&sn=b1400188c0f5bacf94f7b60371abfb3b&chksm=8451acf5b32625e34de823f24e72f092553ff26e84fa25bd81e2b0c08a5ec43c8d18214a5d24#rd",
        "category": "legal",
        "source": "上海二中院",
        "source_category": "法院 · 品牌栏目",
        "date": "2026.07",
        "score": 8.5,
        "tags": ["公司法", "董监高", "勤勉义务", "赔偿认定"],
        "recommend": "新《公司法》对董监高勤勉义务的规定更加具体。本文的「四步审查法」为公司诉讼中的董监高责任认定提供了可复用的分析框架。",
        "features": {"author_tier": 2, "platform_tier": 3, "depth": 1, "relevance": 2},
        "preview": "上海二中院至正栏目案例分析。围绕新《公司法》下董监高勤勉义务的赔偿认定标准，从义务来源、违反判断、损害认定、因果关系四个维度展开。",
    },
    {
        "title": "超龄劳动者工作中受伤，能否获得工伤赔偿？",
        "url": "http://mp.weixin.qq.com/s?__biz=MzA5MDAxMjk5Ng==&mid=2652451717&idx=2&sn=557fc6616940430b373da3fb0d0eb722&chksm=8bffbfaebc8836b89db92822208a8db9ccfe2c55a1b09befa535ab0e4837098e8f774d515b40#rd",
        "category": "legal",
        "source": "山东高法",
        "source_category": "法院 · 以案说法",
        "date": "2026.07",
        "score": 8.0,
        "tags": ["劳动法", "工伤认定", "超龄劳动者", "用工关系"],
        "recommend": "超龄用工是物业、建筑、制造等行业普遍存在的现实问题。本文厘清了实践中常见的「劳动关系/劳务关系」认定误区。",
        "features": {"author_tier": 2, "platform_tier": 3, "depth": 2, "relevance": 1},
        "preview": "超龄劳动者与用人单位是劳动关系还是劳务关系？工作中受伤应否适用《工伤保险条例》？山东高法系统梳理了超龄劳动者的工伤认定规则。",
    },
    {
        "title": "Harvey × Microsoft 365 原生集成，法律 AI 工具进入办公套件",
        "url": "https://www.harvey.ai/blog/harvey-accelerates-enterprise-ai-with-agentpowered-platform-and-microsoft-365-copilot",
        "category": "ai-legal",
        "source": "Harvey Blog",
        "source_category": "官方发布",
        "date": "2026.06.16",
        "score": 9.5,
        "tags": ["法律科技", "微软生态", "基础设施", "格局级"],
        "recommend": "迄今为止法律 AI 领域最大规模的平台整合事件。「办公基础设施」定位意味着法律科技不再是律所的边缘工具。对国内律所的信息化决策有直接参照意义。",
        "features": {"signal_strength": 1, "depth": 1, "relevance": 2, "domestic_relevance": 0},
        "preview": "Harvey 与微软达成深度合作，法律 AI 能力嵌入 Word/Outlook/Teams 原生工作流，标志着法律科技从「独立工具」进入「办公基础设施」阶段。信号级别：格局级。",
    },
    {
        "title": "Littler 律所任命首位首席 AI 官，组织架构为 AI 战略让路",
        "url": "https://legaltechnology.com/littler-appoints-stephanie-goutos-as-inaugural-chief-ai-officer",
        "category": "ai-legal",
        "source": "Legal Technology",
        "source_category": "行业动态",
        "date": "2026",
        "score": 8.5,
        "tags": ["律所管理", "AI 战略", "应用落地级"],
        "recommend": "首席 AI 官的设立反映了律所组织架构正在发生结构性变化。国内律所的 AI 推动目前多由管委会或 IT 部门兼管，缺乏专职战略层。",
        "features": {"signal_strength": 2, "depth": 1, "relevance": 1, "domestic_relevance": 1},
        "preview": "美国顶级律所首次设立 C-suite 级别的 AI 职位，负责全所 AI 战略、工具选型与律师培训。国内律所可参考其组织架构调整思路。",
    },
    {
        "title": "合同审查 AI 新突破：基于大模型的条款级风险识别",
        "url": "https://justee.ai/blog/ai-contract-review-guide",
        "category": "ai-legal",
        "source": "Justee / Stanford HAI",
        "source_category": "行业报告",
        "date": "2026",
        "score": 8.0,
        "tags": ["合同审查", "AI 工具", "应用落地级"],
        "recommend": "合同审查是国内律师最关注的法律 AI 落地场景。本文提供了 2026 年主流工具的功能对比和五步审查流水线的完整拆解。",
        "features": {"signal_strength": 2, "depth": 1, "relevance": 2, "domestic_relevance": 0},
        "preview": "新一代合同审查 AI 不再做「整体风险评估」，而是直接定位到具体条款并给出修改建议，准确率突破 90%。信号级别：应用落地级。",
    },
    {
        "title": "老板说「滚」，员工离岗后被指旷工遭解雇",
        "url": "http://mp.weixin.qq.com/s?__biz=MjM5MjkwMDkxMA==&mid=2649581701&idx=1&sn=b92674592614324c4f6a087ba8306759&chksm=be86fac489f173d2c9c3d6da743c86ce1bdbe03c5e42c25adec2905c76f9e54c25f8e711b08d#rd",
        "category": "legal",
        "source": "上海一中法院",
        "source_category": "法院 · 案例精析",
        "date": "2026.07",
        "score": 8.0,
        "tags": ["劳动法", "解除劳动合同", "旷工认定", "意思表示"],
        "recommend": "口头解雇的效力认定是劳动争议中的经典难题。本文对「用人单位口头表达的定性」和「员工离岗的合理性判断」进行了双重分析。",
        "features": {"author_tier": 2, "platform_tier": 3, "depth": 2, "relevance": 1},
        "preview": "老板口头说出「滚」字后员工离岗，用人单位以旷工为由解雇。口头表达是否构成解除劳动合同的意思表示？上海一中法院从意思表示解释角度作出认定。",
    },
    {
        "title": "《建工司法解释（二）》条文解读（上）",
        "url": "http://mp.weixin.qq.com/s?__biz=MzA4MzY3NjMxNw==&mid=2656555265&idx=1&sn=34f487fd7e48c7d75261a4f304bd83fe&chksm=8451acf3b32625e51f86c195dd96dec936b65a58f37cc808e1158292b818cf2acbe1e718a17a#rd",
        "category": "legal",
        "source": "上海二中院",
        "source_category": "法院 · 新法探究",
        "date": "2026.07",
        "score": 7.5,
        "tags": ["建设工程", "司法解释", "施工合同", "条文解读"],
        "recommend": "建工司法解释（二）是今年建工领域最重要的规范性文件。上海二中院的逐条解读既有立法背景又有实务案例对照。",
        "features": {"author_tier": 2, "platform_tier": 3, "depth": 2, "relevance": 1},
        "preview": "上海二中院对最高法《建工司法解释（二）》逐条解读，涵盖合同效力认定、实际施工人权利保护、工程价款优先受偿等核心条文。",
    },
]


def generate_demo_report():
    today = date.today().strftime("%Y-%m-%d")
    base_dir = os.path.dirname(os.path.dirname(__file__))

    legal_items = [c for c in DEMO_CANDIDATES if c["category"] == "legal"]
    ai_legal_items = [c for c in DEMO_CANDIDATES if c["category"] == "ai-legal"]

    def legal_sort_key(c):
        return (c["features"]["depth"], c["features"]["author_tier"])
    def ai_sort_key(c):
        return (c["features"]["signal_strength"], c["features"]["depth"])

    legal_items.sort(key=legal_sort_key)
    ai_legal_items.sort(key=ai_sort_key)

    # === 生成 Markdown 周报 ===
    lines = []
    lines.append(f"# 法律周报 Demo · {today}")
    lines.append("")
    lines.append("> 本份为演示周报，使用预置示范候选数据生成。同时已生成 HTML 交互版本。")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## AI + 法律")
    lines.append("")

    for item in ai_legal_items[:3]:
        signal = item["features"]["signal_strength"]
        lines.append(f"### {item['title']}")
        lines.append(f"{item['url']}")
        lines.append("")
        lines.append(f"{item['preview']}")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 纯法律")
    lines.append("")

    for item in legal_items[:7]:
        lines.append(f"### {item['title']}")
        lines.append(f"{item['url']}")
        lines.append("")
        lines.append(f"*{item['source']}* | {item['preview']}")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 元数据")
    lines.append("")
    lines.append(f"- **引擎版本**: Level 0 Demo (k-NN 评分引擎 v2.1 就绪)")
    lines.append(f"- **数据来源**: 10 条预置示范候选")
    lines.append(f"- **生成日期**: {today}")
    lines.append("")
    lines.append("## 下一步")
    lines.append("")
    lines.append("1. **换成你自己的候选文章** → 创建 `candidates.jsonl`")
    lines.append("2. **跑真实评分引擎** → `PYTHONPATH=scripts python3 scripts/run_pipeline.py candidates.jsonl`")
    lines.append("3. **让 AI 帮你适配** → 在对话中说「帮我配置法律周报」")

    report_path = os.path.join(base_dir, f"周报_demo_{today}.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Markdown 周报已生成: {report_path}")

    # === 导出 JSON（供 HTML 渲染器消费）===
    all_items = ai_legal_items[:3] + legal_items[:7]
    json_data = []
    for item in all_items:
        json_data.append({
            "title": item.get("title"),
            "url": item.get("url"),
            "category": item.get("category"),
            "source": item.get("source"),
            "source_category": item.get("source_category", ""),
            "date": item.get("date", ""),
            "score": item.get("score", 0),
            "tags": item.get("tags", []),
            "abstract": item.get("preview", ""),
            "recommend": item.get("recommend", ""),
        })
    json_path = os.path.join(base_dir, f"demo_data_{today}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    print(f"JSON 数据已导出: {json_path}")

    # === 调用 HTML 渲染器 ===
    sys.path.insert(0, os.path.join(base_dir, "scripts"))
    from render_html import render_html as _render
    html = _render(json_data, today.replace('-', '.'))
    html_path = os.path.join(base_dir, f"周报_demo_{today}.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML 周报已生成: {html_path}")
    print(f"")
    print(f"  包含 {len(ai_legal_items[:3])} 条 AI+法律 + {len(legal_items[:7])} 条公众号精选")
    print(f"  HTML 含评分徽章、出处行、关键词标签、推荐理由、收藏按钮、原文链接")
    print(f"")
    print(f"  下一步: 创建你自己的 candidates.jsonl 后跑真实评分引擎:")
    print(f"  PYTHONPATH=scripts python3 scripts/run_pipeline.py candidates.jsonl")


if __name__ == "__main__":
    generate_demo_report()
