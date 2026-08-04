#!/usr/bin/env python3
"""
风险评分引擎
8 维度定量评分矩阵：制裁名单命中、官方校验、国家风险、情报风险、
匹配质量、多名单曝光、时效性、负面媒体
"""


# 国家/地区风险分级
COUNTRY_RISK_TIERS = {
    # Tier 1 — 全面制裁 (10分)
    "cu": 10, "ir": 10, "kp": 10, "sy": 10,  # 古巴/伊朗/朝鲜/叙利亚
    # Tier 2 — 严厉制裁 (8分)
    "ru": 8, "by": 8, "ve": 8, "ni": 8, "mm": 8,  # 俄/白俄/委/尼/缅
    # Tier 3 — 定向制裁 (5分)
    "cn": 5, "hk": 5, "et": 5, "ml": 5, "cd": 5,  # 中/港/埃塞/马里/刚果
    # Tier 4 — 关注 (3分)
    "ae": 3, "tr": 3, "ge": 3, "am": 3, "kz": 3,  # 阿联酋/土/格/亚/哈
    "kg": 3, "uz": 3, "rs": 3,  # 吉/乌兹/塞尔维亚
}


def get_country_risk(countries: list) -> tuple:
    """获取国家风险评分和最高风险国家"""
    if not countries:
        return 0, ""
    max_score = 0
    max_country = ""
    for c in countries:
        code = c.lower().strip()
        score = COUNTRY_RISK_TIERS.get(code, 0)
        if score > max_score:
            max_score = score
            max_country = code
    return max_score, max_country


def calculate_risk_score(report: dict) -> dict:
    """
    计算综合风险评分

    8 维度评分，每维度 0-10 分，总分 0-80

    参数:
        report: 筛查报告字典（含 opensanctions_screening、official_verification、intelligence）
    返回:
        风险评估结果字典
    """
    dimensions = {}

    # ── 1. 制裁名单命中 (0-10) ──
    screening = report.get("opensanctions_screening", {})
    matches = screening.get("matches", [])
    if not matches:
        dim1_score = 0
        dim1_detail = "未命中任何制裁名单"
    else:
        top_score = max(m.get("score", 0) for m in matches)
        if top_score >= 0.95:
            dim1_score = 10
            dim1_detail = f"精确命中 (匹配度 {top_score*100:.0f}%)"
        elif top_score >= 0.8:
            dim1_score = 8
            dim1_detail = f"高度匹配 (匹配度 {top_score*100:.0f}%)"
        elif top_score >= 0.6:
            dim1_score = 5
            dim1_detail = f"中度匹配 (匹配度 {top_score*100:.0f}%)"
        else:
            dim1_score = 3
            dim1_detail = f"低度匹配 (匹配度 {top_score*100:.0f}%)"
    dimensions["sanctions_list_hit"] = {"score": dim1_score, "detail": dim1_detail}

    # ── 2. 官方源校验 (0-10) ──
    verifications = report.get("official_verification", [])
    verified_hits = sum(1 for v in verifications if v.get("status") == "verified")
    partial_hits = sum(1 for v in verifications if v.get("status") == "partial")
    if verified_hits >= 3:
        dim2_score = 10
        dim2_detail = f"在 {verified_hits} 个官方源中已验证命中"
    elif verified_hits >= 1:
        dim2_score = 8
        dim2_detail = f"在 {verified_hits} 个官方源中已验证命中"
    elif partial_hits >= 1:
        dim2_score = 4
        dim2_detail = f"{partial_hits} 个官方源部分验证"
    elif matches:
        dim2_score = 2
        dim2_detail = "初筛命中但未通过官方校验（可能是同名）"
    else:
        dim2_score = 0
        dim2_detail = "无需官方校验（初筛清除）"
    dimensions["official_verification"] = {"score": dim2_score, "detail": dim2_detail}

    # ── 3. 国家/地区风险 (0-10) ──
    countries = []
    for m in matches:
        props = m.get("properties", {})
        countries.extend(props.get("country", []))
    dim3_score, dim3_country = get_country_risk(countries)
    dim3_detail = f"最高风险国家: {dim3_country}" if dim3_country else "无国家信息或低风险国家"
    dimensions["country_risk"] = {"score": dim3_score, "detail": dim3_detail}

    # ── 4. 新闻/情报风险 (0-10) ──
    intel = report.get("intelligence") or {}
    news_count = len(intel.get("news_results", []))
    trusted_count = len(intel.get("trusted_source_results", []))
    if news_count >= 10:
        dim4_score = 8
        dim4_detail = f"发现大量相关制裁情报 ({news_count} 条)"
    elif news_count >= 5:
        dim4_score = 5
        dim4_detail = f"发现较多相关情报 ({news_count} 条)"
    elif news_count >= 1:
        dim4_score = 3
        dim4_detail = f"发现少量相关情报 ({news_count} 条)"
    else:
        dim4_score = 0
        dim4_detail = "未发现相关制裁情报"
    if trusted_count >= 3:
        dim4_score = min(dim4_score + 2, 10)
        dim4_detail += f"，{trusted_count} 条来自受信任源"
    dimensions["news_intelligence"] = {"score": dim4_score, "detail": dim4_detail}

    # ── 5. 匹配质量 (0-10) ──
    if matches:
        avg_score = sum(m.get("score", 0) for m in matches) / len(matches)
        dim5_score = int(avg_score * 10)
        dim5_detail = f"平均匹配质量 {avg_score*100:.0f}%"
    else:
        dim5_score = 0
        dim5_detail = "无匹配"
    dimensions["match_quality"] = {"score": dim5_score, "detail": dim5_detail}

    # ── 6. 多名单曝光 (0-10) ──
    all_datasets = set()
    for m in matches:
        all_datasets.update(m.get("datasets", []))
    dataset_count = len(all_datasets)
    if dataset_count >= 5:
        dim6_score = 10
        dim6_detail = f"在 {dataset_count} 个不同名单中出现"
    elif dataset_count >= 3:
        dim6_score = 7
        dim6_detail = f"在 {dataset_count} 个不同名单中出现"
    elif dataset_count >= 1:
        dim6_score = 4
        dim6_detail = f"在 {dataset_count} 个名单中出现"
    else:
        dim6_score = 0
        dim6_detail = "未在任何名单中出现"
    dimensions["multi_list_exposure"] = {"score": dim6_score, "detail": dim6_detail}

    # ── 7. 时效性 (0-10) ──
    # 最近被制裁的风险更高
    recent = False
    for m in matches:
        last_change = m.get("last_change", "")
        if last_change and "2025" in last_change or "2026" in last_change:
            recent = True
            break
    if recent:
        dim7_score = 8
        dim7_detail = "近期有制裁记录更新"
    elif matches:
        dim7_score = 4
        dim7_detail = "有制裁记录但非近期更新"
    else:
        dim7_score = 0
        dim7_detail = "无制裁记录"
    dimensions["recency"] = {"score": dim7_score, "detail": dim7_detail}

    # ── 8. 负面媒体 (0-10) ──
    # 基于情报搜索中新闻的负面程度估算
    negative_keywords = [
        "sanction", "penalty", "fine", "violation", "banned",
        "blocked", "frozen", "seized", "indicted", "arrested",
        "制裁", "处罚", "违规", "禁止", "冻结", "查封", "起诉",
    ]
    negative_count = 0
    for n in intel.get("news_results", []):
        content = (n.get("title", "") + " " + n.get("content", "")).lower()
        if any(kw in content for kw in negative_keywords):
            negative_count += 1
    if negative_count >= 5:
        dim8_score = 8
        dim8_detail = f"{negative_count} 条负面媒体报道"
    elif negative_count >= 2:
        dim8_score = 5
        dim8_detail = f"{negative_count} 条负面媒体报道"
    elif negative_count >= 1:
        dim8_score = 3
        dim8_detail = f"{negative_count} 条负面媒体报道"
    else:
        dim8_score = 0
        dim8_detail = "未发现负面媒体报道"
    dimensions["adverse_media"] = {"score": dim8_score, "detail": dim8_detail}

    # ── 综合评分 ──
    total_score = sum(d["score"] for d in dimensions.values())

    if total_score >= 56:
        risk_level = "CRITICAL"
    elif total_score >= 36:
        risk_level = "HIGH"
    elif total_score >= 20:
        risk_level = "MEDIUM"
    elif total_score >= 8:
        risk_level = "LOW"
    else:
        risk_level = "CLEAR"

    return {
        "total_score": total_score,
        "max_score": 80,
        "risk_level": risk_level,
        "dimensions": dimensions,
    }


def format_risk_badge(score: int, level: str) -> str:
    """生成可视化风险等级标签"""
    filled = score * 10 // 80  # 0-10 的填充格数
    empty = 10 - filled

    level_display = {
        "CRITICAL": "🛑 极高风险 (CRITICAL)",
        "HIGH": "🔴 高风险 (HIGH)",
        "MEDIUM": "🟠 中风险 (MEDIUM)",
        "LOW": "🟡 低风险 (LOW)",
        "CLEAR": "🟢 清除 (CLEAR)",
    }

    bar = "■" * filled + "□" * empty
    return f"**{level_display.get(level, level)}**  [{bar}] {score}/80"
