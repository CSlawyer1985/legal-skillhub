#!/usr/bin/env python3
"""
实体筛查核心引擎
整合 OpenSanctions（初筛）+ 官方源直连校验 + Tavily（情报搜索）
流程：OpenSanctions 快速初筛 → 直连官方政府网站校验 → Tavily 情报补充

关键原则：
  - OpenSanctions 是第三方聚合，可用作初筛但不能作为最终依据
  - 官方校验必须直接查询官方政府网站（OFAC/UK/UN/EU/CA），不依赖 Tavily
  - 报告中明确标注每条命中的验证状态：已验证/待验证/需浏览器验证
"""

import json
import os
import sys
from datetime import datetime

# 导入同目录下的模块
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

# 自动加载 .env 文件中的 API Key
from env_loader import load_dotenv
load_dotenv()

from tavily_search import tavily_search, search_trusted_sources, verify_results, TRUSTED_DOMAINS
from opensanctions_search import match_entity, search_entity, scrape_opensanctions
from official_verify import get_verification_plan, get_sources_for_datasets, DATASET_TO_OFFICIAL
from risk_scorer import calculate_risk_score, format_risk_badge
from fuzzy_match import normalize_name, generate_name_variants


# OpenSanctions 数据集 → 官方校验源的映射
# 根据初筛命中的数据集，决定去哪些官方网站校验
DATASET_TO_OFFICIAL_SOURCE = {
    "us_ofac_sdn": ["ofac"],
    "us_ofac_cons": ["ofac"],
    "un_sc_sanctions": ["un"],
    "eu_fsf": ["eu"],
    "gb_hmt_sanctions": ["uk"],
    "au_dfat_sanctions": ["au"],
    "ca_sema_sanctions": ["ca"],
    "jp_mof_sanctions": [],  # 通过 OpenSanctions 已间接覆盖
    "us_bis_denied": ["ofac"],
    "us_state_debarred": ["ofac"],
}

# 数据集显示名称（中英双语）
DATASET_NAMES = {
    "us_ofac_sdn": "🇺🇸 OFAC SDN (美国特别指定国民名单)",
    "us_ofac_cons": "🇺🇸 OFAC 综合制裁名单",
    "un_sc_sanctions": "🇺🇳 联合国安理会制裁名单",
    "eu_fsf": "🇪🇺 欧盟金融制裁名单",
    "gb_hmt_sanctions": "🇬🇧 英国制裁名单 (UK Sanctions List)",
    "au_dfat_sanctions": "🇦🇺 澳大利亚 DFAT 制裁名单",
    "ca_sema_sanctions": "🇨🇦 加拿大特别经济措施制裁名单",
    "jp_mof_sanctions": "🇯🇵 日本财务省经济制裁名单",
    "us_bis_denied": "🇺🇸 BIS 被拒绝人清单 (DPL)",
    "us_state_debarred": "🇺🇸 国务院禁止名单",
}


def screen_entity(
    entity_name: str,
    entity_type: str = "LegalEntity",
    birth_date: str = None,
    countries: list = None,
    id_number: str = None,
    verify_official: bool = True,
    search_intel: bool = True,
    score_threshold: float = 0.4,
    exact_name_only: bool = False,
    extra_variants: list = None,
) -> dict:
    """
    完整实体筛查流程

    参数:
        entity_name: 实体名称（公司或个人）
        entity_type: "Person" 或 "LegalEntity"
        birth_date: 出生日期（仅个人）
        countries: 国家代码列表
        id_number: 身份证/护照号
        verify_official: 是否对命中结果进行官方源校验
        search_intel: 是否搜索实时情报
        score_threshold: 最低匹配分数
        exact_name_only: 是否只使用用户提供的单个名称，不自动扩展变体
        extra_variants: 用户显式指定的额外名称；提供后只使用显式给定列表
    返回:
        完整筛查结果字典
    """
    report = {
        "entity": entity_name,
        "entity_type": entity_type,
        "timestamp": datetime.now().isoformat(),
        "screening_id": f"SCR-{datetime.now().strftime('%Y%m%d%H%M%S')}",

        # 第一层：OpenSanctions 初筛
        "opensanctions_screening": None,

        # 第二层：官方源校验
        "official_verification": [],

        # 第三层：Tavily 情报搜索
        "intelligence": None,

        # 综合评估
        "risk_assessment": None,

        # 行动建议
        "recommendation": None,
    }

    # ── 第一层：OpenSanctions 初筛 ──
    print(f"[1/3] OpenSanctions 初筛: {entity_name} ...", file=sys.stderr)

    # 名称策略：
    # - exact_name_only: 只搜 entity_name 本身
    # - extra_variants: 只搜 entity_name + 用户显式给定的其他名称
    # - 默认：自动扩展变体
    if exact_name_only:
        name_variants = [entity_name]
        print("  [VARIANTS] 精确名称模式：只使用用户提供的单个名称", file=sys.stderr)
    elif extra_variants:
        name_variants = [entity_name]
        for variant in extra_variants:
            variant = variant.strip()
            if variant and variant not in name_variants:
                name_variants.append(variant)
        print(f"  [VARIANTS] 用户指定名称集合模式：只使用显式给定列表 {name_variants}", file=sys.stderr)
    else:
        name_variants = generate_name_variants(entity_name)
        print(f"  [VARIANTS] 自动扩展模式：{name_variants[:3]}", file=sys.stderr)
    all_matches = []
    seen_ids = set()

    for variant in name_variants[:3]:  # 最多3个变体
        match_result = match_entity(
            name=variant,
            schema=entity_type,
            birth_date=birth_date,
            countries=countries,
            id_number=id_number,
            score_threshold=score_threshold,
        )
        for m in match_result.get("matches", []):
            if m["id"] not in seen_ids:
                seen_ids.add(m["id"])
                m["matched_variant"] = variant
                all_matches.append(m)

    # /match 端点对短名（如 "DJI"）效果差，fallback 到 /search 端点（文本搜索）
    if not all_matches:
        print(f"  [OpenSanctions] /match 无结果，尝试 /search 文本搜索...", file=sys.stderr)
        for variant in name_variants[:3]:
            search_result = search_entity(variant, limit=10)
            for r in search_result.get("results", []):
                rid = r.get("id", "")
                if rid and rid not in seen_ids:
                    seen_ids.add(rid)
                    # 转换 search 结果格式为 match 结果格式
                    r["matched_variant"] = variant
                    r["properties"] = {
                        k: r.pop(k) for k in list(r.keys())
                        if k in ("name", "alias", "country", "topics", "program")
                    }
                    all_matches.append(r)

    # API 都失败时（429 限流等），用网页抓取作为最终 fallback
    if not all_matches:
        print(f"  [OpenSanctions] API 无结果，尝试网页抓取...", file=sys.stderr)
        for variant in name_variants[:2]:
            scrape_result = scrape_opensanctions(variant, limit=5)
            for r in scrape_result.get("results", []):
                rid = r.get("id", "")
                if rid and rid not in seen_ids:
                    seen_ids.add(rid)
                    r["matched_variant"] = variant
                    all_matches.append(r)

    # 按分数排序
    all_matches.sort(key=lambda x: x.get("score", 0), reverse=True)

    report["opensanctions_screening"] = {
        "total_matches": len(all_matches),
        "name_variants_searched": name_variants[:3],
        "matches": all_matches[:20],  # 最多保留20个匹配
        "status": "hit" if all_matches else "clear",
    }

    # ── 第二层：生成官方网站浏览器校验计划 ──
    # 注意：即使初筛未命中也应生成校验计划（OpenSanctions 可能漏报或 API 故障）
    if verify_official:
        if all_matches:
            print(f"[2/3] 生成官方网站校验计划 ({len(all_matches)} 个命中) ...", file=sys.stderr)
        else:
            print(f"[2/3] 初筛未命中，但仍生成官方校验计划（防止漏报）...", file=sys.stderr)

        # 收集所有命中数据集
        hit_datasets = []
        for m in all_matches:
            hit_datasets.extend(m.get("datasets", []))

        # 生成浏览器校验计划
        entity_type_ofac = "Individual" if entity_type == "Person" else "Entity"
        verification_plan = get_verification_plan(
            entity_name=entity_name,
            hit_datasets=hit_datasets if hit_datasets else None,
            entity_type=entity_type_ofac,
        )

        # 将校验计划存入报告
        for source in verification_plan.get("sources_to_verify", []):
            report["official_verification"].append({
                "status": "browser_required",
                "source": source["name"],
                "full_name": source["full_name"],
                "source_url": source["home_url"],
                "search_url": source["search_url"],
                "method": "playwright_browser",
                "reason": "需通过浏览器访问官方网站在线搜索校验",
                "browser_instruction": {
                    "url": source["search_url"],
                    "steps": source["steps"],
                },
            })
    else:
        print("[2/3] 已跳过官方校验 (--no-verify)", file=sys.stderr)

    # ── 第三层：Tavily 多轮深度情报搜索 ──
    if search_intel:
        # 生成英文搜索名（用于英文源搜索）
        en_name = entity_name
        for v in name_variants:
            import re as _re
            if not _re.search(r'[\u4e00-\u9fff]', v):
                en_name = v
                break

        print(f"[3/3] Tavily 多轮深度情报搜索 (entity: {en_name}) ...", file=sys.stderr)

        # 定义 3 轮搜索（先制裁 → 再出口管制 → 再执法行动）
        search_rounds = [
            {
                "round": 1,
                "name": "制裁与黑名单",
                "query": f'"{en_name}" sanctions OR sanctioned OR designated OR blacklisted',
                "topic": "news",
                "days": 365,
            },
            {
                "round": 2,
                "name": "出口管制与实体清单",
                "query": f'"{en_name}" "export control" OR "entity list" OR "trade restriction" OR "BIS" OR "commerce department"',
                "topic": "news",
                "days": 365,
            },
            {
                "round": 3,
                "name": "执法行动与合规案例",
                "query": f'"{en_name}" enforcement OR penalty OR fine OR violation OR prosecution OR indictment OR "plea deal"',
                "topic": "news",
                "days": 730,  # 执法案例搜索更长时间范围
            },
        ]

        all_news = []
        seen_urls = set()
        round_results = []

        for rd in search_rounds:
            print(f"  [Round {rd['round']}/3] {rd['name']}: {rd['query'][:60]}...", file=sys.stderr)
            try:
                rd_result = tavily_search(
                    query=rd["query"],
                    max_results=8,
                    topic=rd["topic"],
                    days=rd["days"],
                )
                rd_articles = rd_result.get("results", [])
                # 去重
                new_articles = []
                for a in rd_articles:
                    url = a.get("url", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        a["search_round"] = rd["name"]
                        new_articles.append(a)
                        all_news.append(a)

                round_results.append({
                    "round": rd["round"],
                    "name": rd["name"],
                    "query": rd["query"],
                    "total_found": len(rd_articles),
                    "new_unique": len(new_articles),
                })
                print(f"    → {len(rd_articles)} found, {len(new_articles)} new unique", file=sys.stderr)
            except Exception as e:
                print(f"    → Failed: {e}", file=sys.stderr)

        # 受信任源搜索（独立一轮）
        print(f"  [Trusted Sources] Searching...", file=sys.stderr)
        trusted_result = search_trusted_sources(
            f'"{en_name}" sanctions compliance enforcement',
            max_results=8,
        )
        trusted_articles = []
        for a in trusted_result.get("results", []):
            url = a.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                a["search_round"] = "受信任源"
                trusted_articles.append(a)

        # 验证所有 URL 有效性（过滤 404）
        print(f"  [Verifying] Checking {len(all_news) + len(trusted_articles)} URLs...", file=sys.stderr)
        all_news = verify_results(all_news, max_verify=15)
        trusted_articles = verify_results(trusted_articles, max_verify=8)
        print(f"  [Verified] {len(all_news)} news + {len(trusted_articles)} trusted URLs confirmed accessible", file=sys.stderr)

        report["intelligence"] = {
            "search_rounds": round_results,
            "news_results": all_news[:15],
            "trusted_source_results": trusted_articles[:8],
            "total_articles": len(all_news) + len(trusted_articles),
            "search_name_used": en_name,
        }
        print(f"  [TOTAL] {len(all_news)} news + {len(trusted_articles)} trusted = {len(all_news) + len(trusted_articles)} verified articles", file=sys.stderr)
    else:
        print("[3/3] 跳过情报搜索", file=sys.stderr)

    # ── 综合风险评估 ──
    report["risk_assessment"] = calculate_risk_score(report)

    # ── 行动建议 ──
    risk_level = report["risk_assessment"]["risk_level"]
    if risk_level == "CRITICAL":
        report["recommendation"] = {
            "action": "HALT",
            "action_cn": "🛑 立即停止",
            "detail": "该实体在多个制裁名单中被精确命中，已通过官方源验证。建议立即停止所有交易，联系外部法律顾问。",
        }
    elif risk_level == "HIGH":
        report["recommendation"] = {
            "action": "ESCALATE",
            "action_cn": "🔴 升级审批",
            "detail": "该实体存在高风险匹配，建议升级至高级合规官/法律顾问进行深度尽职调查，暂缓交易审批。",
        }
    elif risk_level == "MEDIUM":
        report["recommendation"] = {
            "action": "INVESTIGATE",
            "action_cn": "🟠 深入调查",
            "detail": "发现中度风险信号，建议进行增强尽职调查(EDD)，收集更多信息后再做决定。",
        }
    elif risk_level == "LOW":
        report["recommendation"] = {
            "action": "MONITOR",
            "action_cn": "🟡 持续监控",
            "detail": "存在低度风险信号，建议正常推进但加入持续监控名单，定期复查。",
        }
    else:
        report["recommendation"] = {
            "action": "PROCEED",
            "action_cn": "🟢 正常推进",
            "detail": "未发现制裁风险信号。建议正常推进交易，按标准合规流程操作。",
        }

    return report


def format_screening_report(report: dict) -> str:
    """将筛查结果格式化为专业 Markdown 报告"""
    lines = []

    # ── 报告头部 ──
    lines.append("=" * 60)
    lines.append("# 🏛️ 全球制裁筛查报告")
    lines.append("=" * 60)
    lines.append(f"\n**筛查编号：** `{report['screening_id']}`")
    lines.append(f"**筛查时间：** {report['timestamp']}")
    lines.append(f"**筛查实体：** {report['entity']}")
    lines.append(f"**实体类型：** {report['entity_type']}")

    # ── 风险评级 ──
    risk = report.get("risk_assessment", {})
    badge = format_risk_badge(risk.get("total_score", 0), risk.get("risk_level", "CLEAR"))
    lines.append(f"\n## 📊 综合风险评级")
    lines.append(f"\n{badge}")
    lines.append(f"**总分：** {risk.get('total_score', 0)}/80")

    # 各维度得分
    dims = risk.get("dimensions", {})
    if dims:
        lines.append(f"\n| 维度 | 得分 | 说明 |")
        lines.append(f"|------|------|------|")
        dim_names = {
            "sanctions_list_hit": "制裁名单命中",
            "official_verification": "官方源校验",
            "country_risk": "国家/地区风险",
            "news_intelligence": "新闻/情报风险",
            "match_quality": "匹配质量",
            "multi_list_exposure": "多名单曝光",
            "recency": "时效性",
            "adverse_media": "负面媒体",
        }
        for key, value in dims.items():
            name = dim_names.get(key, key)
            lines.append(f"| {name} | {value['score']}/10 | {value.get('detail', '')} |")

    # ── 行动建议 ──
    rec = report.get("recommendation", {})
    lines.append(f"\n## 🎯 行动建议")
    lines.append(f"\n**{rec.get('action_cn', '')}** — `{rec.get('action', '')}`")
    lines.append(f"\n{rec.get('detail', '')}")

    # ── OpenSanctions 初筛结果 ──
    screening = report.get("opensanctions_screening", {})
    lines.append(f"\n## 🔍 第一层：OpenSanctions 初筛")
    lines.append(f"\n**搜索变体：** {', '.join(screening.get('name_variants_searched', []))}")
    lines.append(f"**状态：** {'⚠️ 命中' if screening.get('status') == 'hit' else '✅ 清除'}")
    lines.append(f"**匹配数：** {screening.get('total_matches', 0)}")

    if screening.get("status") == "hit":
        lines.append(f"\n> ⚠️ 注意：OpenSanctions 为第三方聚合数据源，以下结果需通过官方源交叉验证。\n")
        for i, m in enumerate(screening.get("matches", [])[:10], 1):
            score_pct = m.get("score", 0) * 100
            if score_pct >= 90:
                badge = "🔴 高度"
            elif score_pct >= 70:
                badge = "🟠 中度"
            else:
                badge = "🟡 低度"
            lines.append(f"### {i}. {m.get('name', 'N/A')} — {badge}匹配 ({score_pct:.0f}%)")
            datasets = m.get("datasets", [])
            ds_display = [DATASET_NAMES.get(d, d) for d in datasets[:5]]
            lines.append(f"**命中名单：** {' | '.join(ds_display)}")
            props = m.get("properties", {})
            if props.get("alias"):
                lines.append(f"**别名：** {', '.join(props['alias'][:5])}")
            if props.get("country"):
                lines.append(f"**国家：** {', '.join(props['country'])}")
            if props.get("program"):
                lines.append(f"**制裁项目：** {', '.join(props['program'][:3])}")
            lines.append("")

    # ── 官方源校验 ──
    verifications = report.get("official_verification", [])
    lines.append(f"\n## ✅ 第二层：官方政府网站直连校验")
    lines.append("\n> 以下校验结果来自直接查询各国政府官方制裁名单网站，非第三方数据。\n")
    if not verifications:
        lines.append("\n初筛未命中，无需官方校验。")
    else:
        for v in verifications:
            status_badge = {
                "verified": "✅ 官网已确认命中",
                "clear": "✅ 官网确认清除",
                "partial": "🟡 部分验证",
                "unverified": "❌ 未能在官网确认",
                "browser_required": "🌐 需浏览器手动验证",
            }.get(v["status"], v["status"])
            source = v.get('source', 'N/A')
            lines.append(f"\n### {source} — {status_badge}")
            lines.append(f"**官方网址：** [{v.get('source_url', '')}]({v.get('source_url', '')})")
            lines.append(f"**校验方式：** {v.get('method', 'N/A')}")
            lines.append(f"**说明：** {v['reason']}")
            if v.get("verify_url"):
                lines.append(f"**验证链接：** [{v['verify_url']}]({v['verify_url']})")
            # 如需浏览器验证，输出操作步骤
            bi = v.get("browser_instruction")
            if bi and v.get("status") in ("browser_required", "verified", "partial"):
                lines.append("\n**📋 浏览器验证步骤（供人工或 AI agent 执行）：**")
                for step in bi.get("steps", []):
                    lines.append(f"  {step}")

    # ── 情报搜索 ──
    intel = report.get("intelligence")
    if intel:
        lines.append(f"\n## 📰 第三层：实时情报搜索")
        lines.append(f"**相关文章总数：** {intel.get('total_articles', 0)}")

        news = intel.get("news_results", [])
        if news:
            lines.append(f"\n### 新闻/情报 ({len(news)} 条)")
            for i, n in enumerate(news[:5], 1):
                lines.append(f"{i}. [{n.get('title', 'N/A')}]({n.get('url', '')})")
                if n.get("content"):
                    lines.append(f"   > {n['content'][:150]}...")

        trusted = intel.get("trusted_source_results", [])
        if trusted:
            lines.append(f"\n### 受信任源 ({len(trusted)} 条)")
            for i, t in enumerate(trusted[:3], 1):
                lines.append(f"{i}. [{t.get('title', 'N/A')}]({t.get('url', '')})")

    # ── 免责声明 ──
    lines.append(f"\n---")
    lines.append(f"\n## ⚖️ 免责声明")
    lines.append(f"""
- 本报告由自动化工具生成，仅供参考，不构成法律意见。
- OpenSanctions 数据为第三方聚合，命中结果已尽可能通过官方源交叉验证。
- 标注为「✅ 已验证」表示在官方源中找到确认信息；「❌ 未验证」表示未能通过官方源确认。
- 制裁名单持续更新，本报告有效期建议不超过 **7 天**，建议定期复查。
- 最终合规决策应咨询具有执业资格的律师或合规专家。
""")

    return "\n".join(lines)


def main():
    """CLI 入口"""
    import argparse
    parser = argparse.ArgumentParser(
        description="全球制裁筛查引擎 — OpenSanctions 初筛 + 官方源校验 + Tavily 情报",
    )
    parser.add_argument("entity", help="待筛查实体名称")
    parser.add_argument("--type", choices=["Person", "LegalEntity"],
                        default="LegalEntity", help="实体类型")
    parser.add_argument("--birth-date", default=None, help="出生日期 (YYYY-MM-DD)")
    parser.add_argument("--countries", nargs="+", default=None, help="国家代码")
    parser.add_argument("--id-number", default=None, help="身份证/护照号")
    parser.add_argument("--no-verify", action="store_true", help="跳过官方源校验")
    parser.add_argument("--no-intel", action="store_true", help="跳过情报搜索")
    parser.add_argument("--threshold", type=float, default=0.4, help="最低匹配分 (0-1)")
    parser.add_argument("--exact-name-only", action="store_true",
                        help="只使用输入的单个名称，不自动扩展搜索变体")
    parser.add_argument("--extra-variants", nargs="+", default=None, metavar="VARIANT",
                        help="额外显式名称列表（可传 1-N 个）；提供后只使用 entity + 这些名称，不自动扩展变体")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    parser.add_argument("--output", "-o", default=None, help="输出文件路径")

    args = parser.parse_args()

    report = screen_entity(
        entity_name=args.entity,
        entity_type=args.type,
        birth_date=args.birth_date,
        countries=args.countries,
        id_number=args.id_number,
        verify_official=not args.no_verify,
        search_intel=not args.no_intel,
        score_threshold=args.threshold,
        exact_name_only=args.exact_name_only,
        extra_variants=args.extra_variants,
    )

    if args.json:
        output = json.dumps(report, ensure_ascii=False, indent=2)
    else:
        output = format_screening_report(report)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"报告已保存至: {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
