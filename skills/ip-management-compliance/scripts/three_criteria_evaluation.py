"""
三性自动评估引擎模块 (Module D)
功能：新颖性评估、创造性评估、实用性评估
依据：《专利法》第22条、《专利审查指南》（2023/2026）
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field


@dataclass
class NoveltyResult:
    """新颖性评估结果"""
    conclusion: str = "具备新颖性"
    reason: str = ""
    legal_basis: str = ""
    risk_patents: List[str] = field(default_factory=list)
    uncovered_features: List[str] = field(default_factory=list)


@dataclass
class CreativityResult:
    """创造性评估结果"""
    conclusion: str = "具备创造性"
    reason: str = ""
    legal_basis: str = ""
    three_step_analysis: Dict = field(default_factory=dict)
    iso_tech_scores: Dict = field(default_factory=dict)
    overall_score: float = 0.0


@dataclass
class UtilityResult:
    """实用性评估结果"""
    conclusion: str = "具备实用性"
    reason: str = ""
    legal_basis: str = ""
    risks: List[str] = field(default_factory=list)
    industrial_applicable: bool = True
    positive_effect_verified: bool = True


@dataclass
class ThreeCriteriaEvaluation:
    """三性评估综合结果"""
    novelty: NoveltyResult
    creativity: CreativityResult
    utility: UtilityResult
    overall_conclusion: str = ""
    suggestions: List[str] = field(default_factory=list)


def extract_keywords(text: str) -> set:
    """从文本提取关键词"""
    words = re.findall(r'[\u4e00-\u9fa5a-zA-Z0-9]{2,}', text)
    return {w for w in words if len(w) >= 2}


def calculate_feature_coverage(disclosure_features: List[str], prior_art_text: str) -> Tuple[int, List[str], List[str]]:
    """计算技术特征覆盖度"""
    covered = []
    uncovered = []
    prior_keywords = extract_keywords(prior_art_text)

    for feature in disclosure_features:
        feature_keywords = extract_keywords(feature)
        if any(kw in prior_keywords for kw in feature_keywords):
            covered.append(feature)
        else:
            uncovered.append(feature)

    return len(covered), covered, uncovered


def evaluate_novelty(disclosure_elements: Dict, prior_art: List[Dict]) -> NoveltyResult:
    """新颖性评估：严格遵循单独对比原则"""
    result = NoveltyResult()
    result.legal_basis = "《专利法》第22条第2款、《专利审查指南》第二部分第三章"
    disclosure_features = disclosure_elements.get("tech_features", [])

    if not disclosure_features:
        result.conclusion = "新颖性无法判断"
        result.reason = "技术特征提取失败"
        return result

    for patent in prior_art:
        patent_text = f"{patent.get('title', '')} {patent.get('abstract', '')}"
        _, _, uncovered = calculate_feature_coverage(disclosure_features, patent_text)

        if len(uncovered) == 0:
            result.conclusion = "不具备新颖性"
            result.risk_patents.append(patent.get("patent_no", ""))
            result.reason = f"对比文件{patent.get('patent_no', '')}公开了全部技术特征"
            break

    if not result.risk_patents:
        result.conclusion = "具备新颖性"
        result.reason = "未发现覆盖全部技术特征的对比文件"

    return result


def _score_tech_advancement(distinctive_features: List[str]) -> float:
    if not distinctive_features:
        return 3.0
    return min(10.0, 5.0 + len(distinctive_features) * 0.5)


def _score_tech_barrier(tech_field: str) -> float:
    high = ["医药", "芯片", "算法", "人工智能", "新材料"]
    medium = ["食品", "机械", "化工", "环保"]
    for kw in high:
        if kw in tech_field:
            return 8.0
    for kw in medium:
        if kw in tech_field:
            return 6.0
    return 5.0


def _score_lifecycle(tech_field: str) -> float:
    emerging = ["人工智能", "区块链", "量子计算", "基因编辑"]
    mature = ["传统机械", "传统化工", "食品加工"]
    for kw in emerging:
        if kw in tech_field:
            return 8.0
    for kw in mature:
        if kw in tech_field:
            return 5.0
    return 6.0


def evaluate_creativity(disclosure_elements: Dict, prior_art: List[Dict]) -> CreativityResult:
    """创造性评估：三步法 + ISO 56005技术维度评分"""
    result = CreativityResult()
    result.legal_basis = "《专利法》第22条第3款、《专利审查指南》第二部分第四章"

    if not prior_art:
        result.conclusion = "创造性无法判断"
        return result

    d1 = prior_art[0]
    d1_text = f"{d1.get('title', '')} {d1.get('abstract', '')}"
    disclosure_features = disclosure_elements.get("tech_features", [])
    _, covered, distinctive = calculate_feature_coverage(disclosure_features, d1_text)

    obvious = False
    for patent in prior_art[1:5]:
        p_text = f"{patent.get('title', '')} {patent.get('abstract', '')}"
        for f in distinctive:
            if any(kw in extract_keywords(p_text) for kw in extract_keywords(f)):
                obvious = True
                break

    result.three_step_analysis = {
        "step1_d1": {"patent_no": d1.get("patent_no", ""), "title": d1.get("title", "")},
        "step2_distinctive": distinctive[:5],
        "step3_obvious": obvious
    }

    result.iso_tech_scores = {
        "tech_advancement": _score_tech_advancement(distinctive),
        "tech_barrier": _score_tech_barrier(disclosure_elements.get("tech_field", "")),
        "lifecycle": _score_lifecycle(disclosure_elements.get("tech_field", ""))
    }

    result.overall_score = (
        result.iso_tech_scores["tech_advancement"] * 0.4 +
        result.iso_tech_scores["tech_barrier"] * 0.3 +
        result.iso_tech_scores["lifecycle"] * 0.3
    )

    if result.overall_score >= 7 and not obvious:
        result.conclusion = "具备创造性"
        result.reason = "区别特征非显而易见"
    elif result.overall_score >= 4:
        result.conclusion = "创造性存疑"
        result.reason = "建议补充技术效果证据"
    else:
        result.conclusion = "不具备创造性"
        result.reason = "区别特征为公知常识"

    return result


def evaluate_utility(disclosure_elements: Dict) -> UtilityResult:
    """实用性评估"""
    result = UtilityResult()
    result.legal_basis = "《专利法》第22条第4款、《专利审查指南》第二部分第五章"
    risks = []

    examples = disclosure_elements.get("examples", [])
    features = disclosure_elements.get("tech_features", [])
    result.industrial_applicable = len(examples) >= 1 and len(features) >= 2
    if not result.industrial_applicable:
        risks.append("实施例不完整")

    effects = disclosure_elements.get("beneficial_effects", [])
    result.positive_effect_verified = len(effects) > 0
    if not result.positive_effect_verified:
        risks.append("未记载有益效果")

    scheme = disclosure_elements.get("tech_scheme", "")
    if any(kw in scheme for kw in ["永动机", "违反物理定律"]):
        risks.append("违背自然规律")

    result.risks = risks
    result.conclusion = "具备实用性（存在风险点）" if risks else "具备实用性"
    result.reason = "; ".join(risks) if risks else "可产业实施，具有积极效果"

    return result


def evaluate_three_criteria(disclosure_elements: Dict, prior_art: List[Dict]) -> ThreeCriteriaEvaluation:
    """三性综合评估"""
    novelty = evaluate_novelty(disclosure_elements, prior_art)
    creativity = evaluate_creativity(disclosure_elements, prior_art)
    utility = evaluate_utility(disclosure_elements)

    if novelty.conclusion == "不具备新颖性":
        overall = "不建议申请（缺乏新颖性）"
    elif creativity.conclusion == "不具备创造性":
        overall = "不建议申请（缺乏创造性）"
    elif creativity.conclusion == "创造性存疑":
        overall = "建议完善后申请"
    else:
        overall = "建议申请（具备三性）"

    suggestions = []
    if novelty.conclusion == "不具备新颖性":
        suggestions.append("建议寻找区别特征")
    if creativity.conclusion in ["不具备创造性", "创造性存疑"]:
        suggestions.append("建议补充技术效果数据")
    if utility.risks:
        suggestions.append(f"实用性风险：{'；'.join(utility.risks)}")
    if not suggestions:
        suggestions.append("具备可专利性，建议提交申请")

    return ThreeCriteriaEvaluation(
        novelty=novelty,
        creativity=creativity,
        utility=utility,
        overall_conclusion=overall,
        suggestions=suggestions
    )


if __name__ == "__main__":
    print("三性自动评估引擎 (Module D)")
    print("使用方法: from three_criteria_evaluation import evaluate_three_criteria")