#!/usr/bin/env python3
"""
官方制裁名单浏览器校验模块
使用 Playwright 浏览器直接访问各国政府官方制裁搜索网站进行校验

核心原则：
  - 不下载任何文件到本地（避免更新维护成本）
  - 直接在官方网站在线搜索
  - 对于 AI agent：生成浏览器操作指令，由 agent 的 browser_subagent 执行
  - 对于交互模式：使用 Playwright 自动操作浏览器

支持的官方源：
  1. OFAC SDN — sanctionssearch.ofac.treas.gov
  2. UK Sanctions List — search-uk-sanctions-list.service.gov.uk
  3. UN Security Council — scsanctions.un.org
  4. EU Sanctions Map — sanctionsmap.eu
  5. Australia DFAT — dfat.gov.au
  6. Canada — international.gc.ca
"""

import json
import sys
from datetime import datetime


# ═══════════════════════════════════════════════════════
# 官方源定义
# ═══════════════════════════════════════════════════════

OFFICIAL_SOURCES = {
    "ofac": {
        "name": "🇺🇸 OFAC SDN",
        "full_name": "U.S. Treasury OFAC Sanctions List Search",
        "search_url": "https://sanctionssearch.ofac.treas.gov/",
        "search_url_template": "https://sanctionssearch.ofac.treas.gov/?name={entity}",
        "type": "form_search",
        "fuzzy_support": True,
        "browser_steps": [
            "1. 打开 https://sanctionssearch.ofac.treas.gov/",
            '2. 在 Name 字段输入实体名称: "{entity}"',
            "3. Type 选择: {entity_type}",
            "4. ⭐ 重要：将 Minimum Name Score 滑块调低到 70 (启用模糊匹配，默认100只精确匹配)",
            "5. 点击 Search 按钮",
            "6. 等待结果加载",
            "7. 检查结果表格：",
            "   - 如果显示 '0 results found' → 清除",
            "   - 如果有匹配记录 → 命中，记录 Name, Type, Program, List, Score",
            "   - Score=100 表示精确匹配，70-99 为模糊匹配",
        ],
    },
    "uk": {
        "name": "🇬🇧 UK Sanctions List",
        "full_name": "UK Sanctions List Search (FCDO)",
        "search_url": "https://search-uk-sanctions-list.service.gov.uk/",
        "search_url_template": "https://search-uk-sanctions-list.service.gov.uk/search?q={entity}",
        "type": "url_search",
        "fuzzy_support": True,
        "browser_steps": [
            "1. 打开 https://search-uk-sanctions-list.service.gov.uk/",
            '2. 在搜索框输入实体名称: "{entity}"',
            "3. ⭐ 重要：勾选 'Fuzzy Search' 复选框（启用模糊匹配，匹配近似拼写）",
            "4. 点击 Search 按钮",
            "5. 检查搜索结果：",
            "   - 如果页面显示 'No results' 或空列表 → 清除",
            "   - 如果有匹配记录 → 命中，记录制裁类型和限制措施",
            "6. 如果精确搜索无结果，先取消 Fuzzy 再试一次确认",
        ],
    },
    "un": {
        "name": "🇺🇳 UN Security Council",
        "full_name": "United Nations Security Council Consolidated List",
        "search_url": "https://scsanctions.un.org/consolidated/",
        "search_url_template": "https://scsanctions.un.org/consolidated/?query={entity}",
        "type": "url_search",
        "browser_steps": [
            "1. 打开 https://scsanctions.un.org/consolidated/",
            '2. 在搜索框输入实体名称: "{entity}"',
            "3. 点击搜索按钮或按回车",
            "4. 检查搜索结果：",
            "   - 如果无匹配记录 → 清除",
            "   - 如果有匹配 → 命中，注意区分制裁委员会 (1267/1718/2231 等)",
        ],
    },
    "eu": {
        "name": "🇪🇺 EU Sanctions Map",
        "full_name": "European Union Sanctions Map (EEAS)",
        "search_url": "https://www.sanctionsmap.eu/",
        "search_url_template": "https://www.sanctionsmap.eu/#/main?search=%7B%22value%22%3A%22{entity}%22%7D",
        "type": "spa_search",
        "browser_steps": [
            "1. 打开 https://www.sanctionsmap.eu/",
            "2. 等待页面完全加载（SPA 应用，需要等待几秒）",
            '3. 点击页面上的搜索图标或搜索框，输入: "{entity}"',
            "4. 等待搜索结果出现",
            "5. 检查搜索结果：",
            "   - 如果无匹配 → 清除",
            "   - 如果有匹配 → 命中，记录制裁类型、限制措施和相关法规",
        ],
    },
    "au": {
        "name": "🇦🇺 Australia DFAT",
        "full_name": "Australian DFAT Consolidated Sanctions List",
        "search_url": "https://www.dfat.gov.au/international-relations/security/sanctions/consolidated-list",
        "search_url_template": "https://www.dfat.gov.au/international-relations/security/sanctions/consolidated-list",
        "type": "page_search",
        "browser_steps": [
            "1. 打开 https://www.dfat.gov.au/international-relations/security/sanctions/consolidated-list",
            "2. 等待页面加载完成",
            "3. 使用浏览器的 Ctrl+F (查找功能) 搜索实体名称",
            '4. 搜索: "{entity}"',
            "5. 检查是否有匹配：",
            "   - 如果未找到 → 清除",
            "   - 如果找到 → 命中，记录上下文信息",
            "6. 可选：页面上有 XLSX 下载链接，如需详细数据可下载",
        ],
    },
    "ca": {
        "name": "🇨🇦 Canada SEMA",
        "full_name": "Canadian Consolidated Autonomous Sanctions List",
        "search_url": "https://www.international.gc.ca/world-monde/international_relations-relations_internationales/sanctions/consolidated-consolide.aspx",
        "search_url_template": "https://www.international.gc.ca/world-monde/international_relations-relations_internationales/sanctions/consolidated-consolide.aspx",
        "type": "page_search",
        "browser_steps": [
            "1. 打开加拿大制裁名单页面",
            "2. 等待页面加载",
            "3. 使用 Ctrl+F 搜索实体名称",
            '4. 搜索: "{entity}"',
            "5. 检查匹配结果",
        ],
    },
}

# OpenSanctions 数据集 → 官方校验源映射
DATASET_TO_OFFICIAL = {
    "us_ofac_sdn": ["ofac"],
    "us_ofac_cons": ["ofac"],
    "un_sc_sanctions": ["un"],
    "eu_fsf": ["eu"],
    "eu_sanctions_map": ["eu"],
    "eu_journal_sanctions": ["eu"],
    "gb_hmt_sanctions": ["uk"],
    "gb_fcdo_sanctions": ["uk"],
    "au_dfat_sanctions": ["au"],
    "ca_dfatd_sema_sanctions": ["ca"],
    "jp_mof_sanctions": [],
    "us_bis_denied": ["ofac"],
    "us_trade_csl": ["ofac"],       # BIS 综合筛查清单 → 用 OFAC 校验
    "us_sam_exclusions": ["ofac"],
    "us_dod_chinese_milcorps": ["ofac"],  # 国防部中国涉军企业单
    "ch_seco_sanctions": [],
    "ua_nsdc_sanctions": [],
    "nz_russia_sanctions": [],
    "tw_shtc": [],
}


def get_verification_plan(entity_name: str, hit_datasets: list = None,
                          entity_type: str = "Entity") -> dict:
    """
    生成官方校验计划

    参数:
        entity_name: 实体名称
        hit_datasets: OpenSanctions 命中的数据集列表（用于确定需要校验哪些官方源）
        entity_type: OFAC 的实体类型 "Entity" 或 "Individual"
    返回:
        校验计划字典，包含每个官方源的浏览器操作指令
    """
    # 根据命中数据集确定需要校验哪些官方源
    sources_to_check = set()
    if hit_datasets:
        for ds in hit_datasets:
            officials = DATASET_TO_OFFICIAL.get(ds, [])
            sources_to_check.update(officials)
    else:
        # 默认检查所有主要源
        sources_to_check = {"ofac", "uk", "un", "eu"}

    plan = {
        "entity": entity_name,
        "entity_type": entity_type,
        "timestamp": datetime.now().isoformat(),
        "sources_to_verify": [],
        "summary": f"需要在 {len(sources_to_check)} 个官方网站进行浏览器校验",
    }

    for source_key in sorted(sources_to_check):
        source = OFFICIAL_SOURCES.get(source_key)
        if not source:
            continue

        # 替换模板中的实体名称
        search_url = source["search_url_template"].replace("{entity}", entity_name)
        steps = [s.replace("{entity}", entity_name).replace("{entity_type}", entity_type)
                 for s in source["browser_steps"]]

        plan["sources_to_verify"].append({
            "key": source_key,
            "name": source["name"],
            "full_name": source["full_name"],
            "search_url": search_url,
            "home_url": source["search_url"],
            "type": source["type"],
            "steps": steps,
        })

    return plan


def get_sources_for_datasets(datasets: list) -> set:
    """根据 OpenSanctions 数据集列表，确定需要校验的官方源"""
    sources = set()
    for ds in datasets:
        officials = DATASET_TO_OFFICIAL.get(ds, [])
        sources.update(officials)
    return sources


def format_verification_plan(plan: dict) -> str:
    """格式化校验计划为 Markdown 指令"""
    lines = []
    lines.append("# 官方制裁名单浏览器校验计划\n")
    lines.append(f"**实体：** {plan['entity']}")
    lines.append(f"**时间：** {plan['timestamp']}")
    lines.append(f"**{plan['summary']}**\n")
    lines.append("> 请使用浏览器（或 browser_subagent）逐一访问以下官方网站进行校验。\n")

    for source in plan.get("sources_to_verify", []):
        lines.append(f"## {source['name']} — {source['full_name']}")
        lines.append(f"\n**搜索链接：** [{source['search_url']}]({source['search_url']})")
        lines.append(f"**操作步骤：**\n")
        for step in source["steps"]:
            lines.append(f"  {step}")
        lines.append("")

    return "\n".join(lines)


def main():
    """CLI 入口"""
    import argparse
    parser = argparse.ArgumentParser(description="官方制裁名单浏览器校验（Playwright）")
    parser.add_argument("entity", help="待校验实体名称")
    parser.add_argument("--sources", nargs="+",
                        choices=list(OFFICIAL_SOURCES.keys()),
                        default=None, help="指定校验源 (默认: ofac uk un eu)")
    parser.add_argument("--type", default="Entity",
                        choices=["Entity", "Individual"],
                        help="OFAC 实体类型")
    parser.add_argument("--json", action="store_true")

    args = parser.parse_args()

    plan = get_verification_plan(
        entity_name=args.entity,
        hit_datasets=None,
        entity_type=args.type,
    )

    # 如果指定了 sources，过滤
    if args.sources:
        plan["sources_to_verify"] = [
            s for s in plan["sources_to_verify"] if s["key"] in args.sources
        ]
        plan["summary"] = f"需要在 {len(plan['sources_to_verify'])} 个官方网站进行浏览器校验"

    if args.json:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
    else:
        print(format_verification_plan(plan))


if __name__ == "__main__":
    main()
