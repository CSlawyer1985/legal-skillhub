"""
损害赔偿计算器 —— 五大类法定赔偿金额计算引擎

覆盖五大赔偿类型，公式来自现行法条：

1. 人身损害赔偿   — 民法典第1179条 + 人身损害赔偿司法解释
2. 交通事故赔偿   — 道路交通安全法第76条 + 交强险条例
3. 违约赔偿       — 民法典第577/584/585条
4. 劳动经济补偿   — 劳动合同法第47/87条
5. 消费者赔偿     — 消法第55条 + 食品安全法第148条

每项计算结果标注法律依据和计算过程，可直接嵌入起诉状金额字段。

使用：
    from damage_calculator import calculate_personal_injury, calculate_labor_comp
    r = calculate_personal_injury(medical=50000, lost_wages=30000, ...)
    print(r.total)          # 总赔偿额
    print(r.breakdown)      # 分项明细
    print(r.legal_basis)    # 法律依据

作者: 智慧半岛
日期: 2026-07-03
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Union
from math import ceil


# ─── 枚举 ────────────────────────────────────────────────────────────────────

class InjuryGrade(Enum):
    """伤残等级"""
    LEVEL_1 = 1    # 一级（最严重，100%）
    LEVEL_2 = 2
    LEVEL_3 = 3
    LEVEL_4 = 4
    LEVEL_5 = 5
    LEVEL_6 = 6
    LEVEL_7 = 7
    LEVEL_8 = 8
    LEVEL_9 = 9
    LEVEL_10 = 10  # 十级（最轻，10%）


class TerminationType(Enum):
    """劳动关系解除类型"""
    NORMAL = "normal"          # 协商一致 / 合同到期不续
    WITHOUT_NOTICE = "n1"      # 未提前30天通知（N+1）
    ILLEGAL = "illegal"        # 违法解除（2N）


# ─── 统一结果 ────────────────────────────────────────────────────────────────

@dataclass
class DamageResult:
    """损害赔偿计算结果"""

    case_type: str = ""                     # 案件类型标识
    total: float = 0.0                      # 赔偿总额
    breakdown: dict = field(default_factory=dict)  # 分项明细 {项名: 金额}
    legal_basis: str = ""                   # 法律依据（法条引用）
    formula: str = ""                       # 计算公式
    disclaimer: str = (
        "以上金额为基于法律依据的理论计算，实际赔偿数额由法院根据证据和案情依法确定。"
        "仅供参考，不构成法律意见。"
    )
    warning: str = ""                       # 特别提示（如有）


# ─── 辅助函数 ────────────────────────────────────────────────────────────────

# 2026年度参考数据（建议用实际统计局数据覆盖）
DEFAULT_PER_CAPITA_INCOME = 49300.0    # 城镇居民人均可支配收入（年）
DEFAULT_PER_CAPITA_CONSUMPTION = 31500.0  # 城镇居民人均消费支出（年）
DEFAULT_AVG_WAGE = 96500.0             # 城镇非私营单位年平均工资
DEFAULT_MIN_WAGE = 2360.0              # 各地最低工资（月，取中位数）
DEFAULT_MEAL_SUBSIDY = 100.0           # 住院伙食补助费（元/天）
DEFAULT_NUTRITION_SUBSIDY = 50.0       # 营养费（元/天，参照医嘱）
DEFAULT_NURSING_FEE = 160.0            # 护理费（元/天）


def _nvl(value: Optional[float], default: float = 0.0) -> float:
    """空值兜底"""
    return float(value) if value is not None else default


def _injury_ratio(grade: Union[int, InjuryGrade]) -> float:
    """伤残等级 → 赔偿系数（1级=100% … 10级=10%）"""
    if isinstance(grade, InjuryGrade):
        grade = grade.value
    if not 1 <= grade <= 10:
        raise ValueError(f"伤残等级必须在1-10之间，收到: {grade}")
    return 0.1 * (11 - grade)  # 1→1.0, 10→0.1, etc.


def _cap_amount(value: float, cap: float, label: str) -> tuple:
    """截断并记录是否超限"""
    if value > cap:
        return cap, f"（{label}限额{cap:,.0f}元，超出部分不计列）"
    return value, ""


# ═══════════════════════════════════════════════════════════════════════════════
# 1. 人身损害赔偿计算
# 民法典第1179条 + 最高人民法院人身损害赔偿司法解释
# ═══════════════════════════════════════════════════════════════════════════════

def calculate_personal_injury(
    medical_expense: float = 0.0,           # 医疗费
    nursing_fee: float = 0.0,               # 护理费
    transport_fee: float = 0.0,             # 交通费
    nutrition_fee: float = 0.0,             # 营养费
    meal_subsidy: float = 0.0,              # 住院伙食补助费
    accommodation_fee: float = 0.0,         # 住宿费（外地就医）
    lost_wages: float = 0.0,                # 误工费
    disability_compensation: float = 0.0,   # 残疾赔偿金（手动输入）
    mental_anguish: float = 0.0,            # 精神损害抚慰金
    funeral_expense: float = 0.0,           # 丧葬费
    death_compensation: float = 0.0,        # 死亡赔偿金（手动输入）
    dependent_living: float = 0.0,          # 被扶养人生活费
    assistive_device: float = 0.0,          # 残疾辅助器具费
    rehab_fee: float = 0.0,                 # 康复费
    followup_fee: float = 0.0,              # 后续治疗费
    property_loss: float = 0.0,             # 财产损失
    other_fee: float = 0.0,                 # 其他合理费用

    # 自动计算参数
    injury_grade: Optional[InjuryGrade] = None,      # 伤残等级（如有）
    victim_age: Optional[int] = None,                 # 受害人定残时年龄
    per_capita_income: Optional[float] = None,        # 城镇居民人均可支配收入
    hospitalization_days: Optional[int] = None,       # 住院天数
    daily_meal_subsidy: Optional[float] = None,       # 日伙食补助标准
    daily_nutrition: Optional[float] = None,          # 日营养费标准
    daily_nursing: Optional[float] = None,            # 日护理费标准
    is_death: bool = False,                           # 是否死亡
) -> DamageResult:
    """人身损害赔偿计算。

    民法典第1179条：侵害他人造成人身损害的，应当赔偿医疗费、护理费、交通费、
    营养费、住院伙食补助费等为治疗和康复支出的合理费用，以及因误工减少的收入。
    造成残疾的，还应当赔偿辅助器具费和残疾赔偿金；造成死亡的，还应当赔偿丧葬费和死亡赔偿金。
    """

    income = _nvl(per_capita_income, DEFAULT_PER_CAPITA_INCOME)
    breakdown = {}
    warning = ""

    # 1) 直接输入的费用
    items = {
        "医疗费": medical_expense,
        "护理费": nursing_fee,
        "交通费": transport_fee,
        "营养费": nutrition_fee,
        "住院伙食补助费": meal_subsidy,
        "住宿费": accommodation_fee,
        "误工费": lost_wages,
        "康复费": rehab_fee,
        "后续治疗费": followup_fee,
        "残疾辅助器具费": assistive_device,
        "财产损失": property_loss,
        "其他合理费用": other_fee,
    }

    # 2) 自动计算的费用
    # 住院伙食补助费（天数×日标准）
    if hospitalization_days and not meal_subsidy:
        daily = _nvl(daily_meal_subsidy, DEFAULT_MEAL_SUBSIDY)
        auto_meal = hospitalization_days * daily
        items["住院伙食补助费"] = auto_meal
        items[f"  └ 计算: {hospitalization_days}天 × {daily:.0f}元/天"] = 0  # 标尺行
    else:
        items["住院伙食补助费"] = meal_subsidy

    # 营养费
    if hospitalization_days and not nutrition_fee:
        daily = _nvl(daily_nutrition, DEFAULT_NUTRITION_SUBSIDY)
        auto_nutrition = hospitalization_days * daily
        items["营养费"] = auto_nutrition
    else:
        items["营养费"] = nutrition_fee

    # 护理费
    if hospitalization_days and not nursing_fee:
        daily = _nvl(daily_nursing, DEFAULT_NURSING_FEE)
        auto_nursing = hospitalization_days * daily
        items["护理费"] = auto_nursing
    else:
        items["护理费"] = nursing_fee

    # 3) 伤残/死亡专项
    if injury_grade and not disability_compensation and not is_death:
        ratio = _injury_ratio(injury_grade)
        # 残疾赔偿金 = 人均可支配收入 × 20年 × 伤残系数（60岁以上递减）
        years = min(20, max(5, 80 - (victim_age or 60))) if victim_age else 20
        if victim_age and victim_age > 60:
            warning = f"受害人定残时{victim_age}岁，赔偿年限按{20 - (victim_age - 60)}年计算（每超过60岁1年减1年，最低5年）"
        auto_disability = income * years * ratio
        items[f"残疾赔偿金({injury_grade.value}级×{ratio*100:.0f}%×{years}年)"] = auto_disability
    elif injury_grade and disability_compensation:
        items[f"残疾赔偿金({injury_grade.value}级)"] = disability_compensation
    elif injury_grade:
        items[f"残疾赔偿金({injury_grade.value}级)"] = 0.0

    if is_death:
        if not death_compensation and not funeral_expense:
            # 死亡赔偿金 = 人均可支配收入 × 20年
            auto_death = income * 20
            items["死亡赔偿金(人均收入×20年)"] = auto_death
            items["丧葬费(6个月平均工资)"] = DEFAULT_AVG_WAGE / 2
            warning = f"丧葬费按受诉法院所在地上一年度职工月平均工资6个月计（此处用{DEFAULT_AVG_WAGE:,.0f}元/年估算）"
        else:
            if death_compensation:
                items["死亡赔偿金"] = death_compensation
            if funeral_expense:
                items["丧葬费"] = funeral_expense

    # 精神损害抚慰金 + 被扶养人生活费
    if mental_anguish:
        items["精神损害抚慰金"] = mental_anguish
    if dependent_living:
        items["被扶养人生活费"] = dependent_living

    # 清理标尺行
    breakdown = {k: v for k, v in items.items() if "└" not in str(k)}

    total = sum(v for v in breakdown.values())

    legal_basis = (
        "《民法典》第1165条（过错责任）、第1179条（人身损害赔偿范围）、"
        "第1183条（精神损害赔偿）"
    )
    if injury_grade:
        legal_basis += "；《人身损害赔偿司法解释》第12条（残疾赔偿金）、第25条（赔偿年限）"
    if is_death:
        legal_basis += "；《人身损害赔偿司法解释》第15条（死亡赔偿金）、第14条（丧葬费）"

    formula = f"总赔偿额 = {' + '.join(f'{k}({v:,.2f})' for k, v in breakdown.items() if v != 0)} = {total:,.2f}"

    return DamageResult(
        case_type="人身损害赔偿",
        total=total,
        breakdown=breakdown,
        legal_basis=legal_basis,
        formula=formula,
        warning=warning,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 2. 交通事故赔偿计算
# 道路交通安全法第76条 + 交强险条例 + 民法典侵权责任编
# ═══════════════════════════════════════════════════════════════════════════════

# 2026年度交强险限额（中国银保监会最新标准）
COMPULSORY_INSURANCE_LIMIT = {
    "death_disability": 180_000,     # 死亡伤残赔偿限额
    "medical": 18_000,               # 医疗费用赔偿限额
    "property": 2_000,               # 财产损失赔偿限额
}


def calculate_traffic_accident(
    medical_expense: float = 0.0,
    nursing_fee: float = 0.0,
    transport_fee: float = 0.0,
    nutrition_fee: float = 0.0,
    meal_subsidy: float = 0.0,
    accommodation_fee: float = 0.0,
    lost_wages: float = 0.0,
    disability_compensation: float = 0.0,
    mental_anguish: float = 0.0,
    funeral_expense: float = 0.0,
    death_compensation: float = 0.0,
    dependent_living: float = 0.0,
    assistive_device: float = 0.0,
    rehab_fee: float = 0.0,
    followup_fee: float = 0.0,
    property_loss: float = 0.0,
    vehicle_damage: float = 0.0,      # 车辆损失
    other_loss: float = 0.0,

    # 自动计算
    injury_grade: Optional[InjuryGrade] = None,
    victim_age: Optional[int] = None,
    per_capita_income: Optional[float] = None,
    hospitalization_days: Optional[int] = None,
    is_death: bool = False,

    # 事故责任
    victim_fault_ratio: float = 0.0,   # 受害人过错比例（0~1）
) -> DamageResult:
    """交通事故损害赔偿计算。

    先由交强险在限额内赔付 → 超出部分按过错比例分担。
    """

    income = _nvl(per_capita_income, DEFAULT_PER_CAPITA_INCOME)
    tipping = ""

    # 先用人身损害赔偿算全部项目
    pi_result = calculate_personal_injury(
        medical_expense=medical_expense,
        nursing_fee=nursing_fee,
        transport_fee=transport_fee,
        nutrition_fee=nutrition_fee,
        meal_subsidy=meal_subsidy,
        accommodation_fee=accommodation_fee,
        lost_wages=lost_wages,
        disability_compensation=disability_compensation,
        mental_anguish=mental_anguish,
        funeral_expense=funeral_expense,
        death_compensation=death_compensation,
        dependent_living=dependent_living,
        assistive_device=assistive_device,
        rehab_fee=rehab_fee,
        followup_fee=followup_fee,
        property_loss=0.0,  # 单独处理
        other_fee=other_loss,
        injury_grade=injury_grade,
        victim_age=victim_age,
        per_capita_income=income,
        hospitalization_days=hospitalization_days,
        is_death=is_death,
    )

    total_human = pi_result.total + property_loss + vehicle_damage

    # 分类到交强险限额
    death_disability_items = 0.0
    medical_items = 0.0
    prop_items = property_loss + vehicle_damage

    # 死亡伤残 → 残疾赔偿金/死亡赔偿金/丧葬费/精神抚慰/护理费/交通费/误工费/被扶养人生活费
    death_disability_keys = {
        "残疾赔偿金", "死亡赔偿金", "丧葬费", "精神损害抚慰金",
        "护理费", "交通费", "误工费", "被扶养人生活费", "康复费", "残疾辅助器具费",
    }
    medical_keys = {"医疗费", "住院伙食补助费", "营养费", "后续治疗费"}

    for k in death_disability_keys:
        for bk, bv in pi_result.breakdown.items():
            if k in str(bk):
                death_disability_items += bv

    for k in medical_keys:
        for bk, bv in pi_result.breakdown.items():
            if k in str(bk):
                medical_items += bv

    # 交强险赔付
    ci_paid_death = min(death_disability_items, COMPULSORY_INSURANCE_LIMIT["death_disability"])
    ci_paid_medical = min(medical_items, COMPULSORY_INSURANCE_LIMIT["medical"])
    ci_paid_prop = min(prop_items, COMPULSORY_INSURANCE_LIMIT["property"])
    ci_total = ci_paid_death + ci_paid_medical + ci_paid_prop

    # 超出交强险部分
    excess_human = total_human - ci_total
    if excess_human < 0:
        excess_human = 0

    # 按过错比例分担（侵权方承担比例 = 1 - victim_fault_ratio）
    tortfeasor_ratio = 1.0 - victim_fault_ratio
    tortfeasor_liability = excess_human * tortfeasor_ratio
    victim_bears = excess_human * victim_fault_ratio

    # 最终受害人可获赔偿 = 交强险赔付 + 侵权方应承担部分
    total_payable = ci_total + tortfeasor_liability

    breakdown = {
        "人身损害合计": total_human,
        "  交强险赔付-死亡伤残": ci_paid_death,
        "  交强险赔付-医疗费用": ci_paid_medical,
        "  交强险赔付-财产损失": ci_paid_prop,
        "  交强险赔付合计": ci_total,
        "超出交强险部分": excess_human,
        f"  侵权方承担({tortfeasor_ratio*100:.0f}%责任)": tortfeasor_liability,
        f"  受害人自担({victim_fault_ratio*100:.0f}%过错)": victim_bears,
        "最终可获赔偿": total_payable,
    }

    if ci_paid_death >= COMPULSORY_INSURANCE_LIMIT["death_disability"]:
        tipping = (
            f"死亡伤残交强险限额{COMPULSORY_INSURANCE_LIMIT['death_disability']:,}元已用尽，"
            "超出部分需由责任方按过错比例承担"
        )

    legal_basis = (
        "《道路交通安全法》第76条（交强险+过错赔偿）；"
        f"交强险限额：死亡伤残{COMPULSORY_INSURANCE_LIMIT['death_disability']:,}元 "
        f"/ 医疗{COMPULSORY_INSURANCE_LIMIT['medical']:,}元 "
        f"/ 财产{COMPULSORY_INSURANCE_LIMIT['property']:,}元"
    )

    return DamageResult(
        case_type="交通事故赔偿",
        total=round(total_payable, 2),
        breakdown=breakdown,
        legal_basis=legal_basis,
        formula=(
            f"交强险赔付{ci_total:,.2f} + "
            f"超出部分{excess_human:,.2f} × 侵权方{tortfeasor_ratio*100:.0f}% = {total_payable:,.2f}"
        ),
        warning=tipping,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 3. 违约赔偿计算
# 民法典第577条（违约责任）/ 第584条（赔偿范围）/ 第585条（违约金）
# ═══════════════════════════════════════════════════════════════════════════════

def calculate_breach_damages(
    actual_loss: float = 0.0,                 # 实际损失
    lost_profit: float = 0.0,                 # 可得利益损失
    contract_penalty: Optional[float] = None,  # 约定违约金
    deposit_paid: float = 0.0,                # 已付定金（违约定金罚则）
    deposit_received: float = 0.0,            # 已收定金（违约定金罚则）
    excessive_penalty: bool = False,           # 违约金是否过高（>损失30%）
) -> DamageResult:
    """违约赔偿计算。

    民法典第584条：赔偿额 = 实际损失 + 可得利益损失（不超过违约方预见的范围）
    第585条：违约金过高可请求适当减少（>损失30%为过高）
    第587条：定金罚则 — 给付方违约无权要求返还，收受方违约双倍返还
    """

    breakdown = {}
    warning = ""

    # 计算法定损失
    statutory_damages = actual_loss + lost_profit

    # 违约金处理
    if contract_penalty is not None:
        if excessive_penalty and contract_penalty > statutory_damages * 1.3:
            adjusted_penalty = statutory_damages * 1.3
            warning = (
                f"约定违约金{contract_penalty:,.2f}元超过损失{statutory_damages:,.2f}元的30%，"
                f"法院可能调整为{adjusted_penalty:,.2f}元（《民法典》第585条第2款）"
            )
            breakdown["约定违约金（原定）"] = contract_penalty
            breakdown["约定违约金（调整后）"] = adjusted_penalty
            total = adjusted_penalty
        else:
            breakdown["约定违约金"] = contract_penalty
            total = contract_penalty
    else:
        breakdown["实际损失"] = actual_loss
        breakdown["可得利益损失"] = lost_profit
        total = statutory_damages

    # 定金罚则（与违约金择一适用，民法典第588条）
    if deposit_paid > 0:
        # 给付方违约 → 无权要求返还
        penalty_deposit = deposit_paid  # 损失已付定金
        breakdown["定金损失（给付方违约）"] = penalty_deposit
        if contract_penalty is not None:
            warning = "定金与违约金只能择一主张（《民法典》第588条），本计算取违约金"
        else:
            total = max(total, penalty_deposit)
    elif deposit_received > 0:
        # 收受方违约 → 双倍返还
        penalty_deposit = deposit_received  # 额外赔偿 = received
        breakdown["定金赔偿（双倍返还中超出部分）"] = penalty_deposit
        if contract_penalty is not None:
            warning = "定金与违约金只能择一主张（《民法典》第588条），本计算取违约金"
        else:
            total = max(total, penalty_deposit)

    legal_basis = (
        "《民法典》第577条（违约责任一般条款）、第584条（赔偿范围=实际损失+可得利益）、"
        "第585条（违约金调整）、第587条（定金罚则）、第588条（定金与违约金竞合）"
    )

    return DamageResult(
        case_type="违约赔偿",
        total=round(total, 2),
        breakdown=breakdown,
        legal_basis=legal_basis,
        formula=f"赔偿额 = {total:,.2f}元",
        warning=warning,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 4. 劳动经济补偿/赔偿计算
# 劳动合同法第47条（经济补偿）/ 第87条（违法解除赔偿）
# ═══════════════════════════════════════════════════════════════════════════════

def calculate_labor_comp(
    monthly_wage: float,                           # 离职前12个月平均工资
    years_of_service: float,                       # 工作年限
    termination_type: TerminationType = TerminationType.NORMAL,
    local_avg_wage_3x: Optional[float] = None,     # 当地上年度职工月平均工资3倍（封顶用）
    local_min_wage: Optional[float] = None,         # 当地最低工资
    is_high_earner: bool = False,                  # 是否高收入者（月工资>3倍社平）
) -> DamageResult:
    """劳动经济补偿/赔偿计算。

    第47条：经济补偿 = 月工资 × 工作年限（每满1年算1月，6月以上算1年，不足6月算半年）
    高收入者封顶：月工资>3倍社平×12年上限
    第87条：违法解除赔偿金 = 经济补偿的2倍
    """

    monthly = monthly_wage
    years = years_of_service
    avg3x = _nvl(local_avg_wage_3x, DEFAULT_AVG_WAGE / 12 * 3)  # 默认约24125
    min_w = _nvl(local_min_wage, DEFAULT_MIN_WAGE)

    warning = ""

    # 工作年限精确到半年
    full_years = int(years)
    remainder = years - full_years
    if remainder > 0 and remainder <= 0.5:
        calculated_years = full_years + 0.5
    elif remainder > 0.5:
        calculated_years = full_years + 1
    else:
        calculated_years = full_years

    # 高收入者封顶
    if is_high_earner or monthly > avg3x:
        monthly_capped = avg3x
        years_capped = min(calculated_years, 12)
        warning = (
            f"月工资{monthly:,.2f}元超过当地上年度职工月平均工资3倍{avg3x:,.2f}元，"
            f"按3倍封顶计算，年限上限12年"
        )
        calculated_years = years_capped
    else:
        monthly_capped = monthly

    # 底线保护：不低于最低工资
    if monthly_capped < min_w:
        warning = f"月工资低于当地最低工资{min_w:,.2f}元，按{min_w:,.2f}元计算"
        monthly_capped = min_w

    base_compensation = monthly_capped * calculated_years

    # 根据解除类型
    if termination_type == TerminationType.NORMAL:
        total = base_compensation
        type_label = "经济补偿（N）"
    elif termination_type == TerminationType.WITHOUT_NOTICE:
        # N + 1（未提前30天通知）
        total = base_compensation + monthly_capped
        type_label = "经济补偿（N+1）"
    elif termination_type == TerminationType.ILLEGAL:
        # 2N（违法解除）
        total = base_compensation * 2
        type_label = "违法解除赔偿金（2N）"
    else:
        total = base_compensation
        type_label = "经济补偿（N）"

    breakdown = {
        "月工资基数": monthly_capped,
        "折算年限": calculated_years,
        f"{type_label}": total,
    }

    legal_basis = (
        "《劳动合同法》第47条（经济补偿计算标准）、第87条（违法解除赔偿金=2N）；"
        f"月工资基数{monthly_capped:,.2f}元 × {calculated_years}年"
    )

    formula = f"{total:,.2f}元"

    return DamageResult(
        case_type=f"劳动{'赔偿' if termination_type == TerminationType.ILLEGAL else '经济补偿'}",
        total=round(total, 2),
        breakdown=breakdown,
        legal_basis=legal_basis,
        formula=formula,
        warning=warning,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 5. 消费者赔偿计算
# 消费者权益保护法第55条 + 食品安全法第148条
# ═══════════════════════════════════════════════════════════════════════════════

class ConsumerCase(Enum):
    FRAUD = "fraud"               # 消法第55条：欺诈 → 退一赔三
    FOOD_SAFETY = "food_safety"   # 食安法第148条：不合格食品 → 退一赔十
    BOTH = "both"                  # 竞合：食安问题优先适用赔十


def calculate_consumer_comp(
    purchase_price: float,                    # 购买价款
    case_type: ConsumerCase = ConsumerCase.FRAUD,
    additional_damage: float = 0.0,           # 其他实际损失
    punitive_base: Optional[float] = None,    # 惩罚性赔偿计算基数（默认=价款）
) -> DamageResult:
    """消费者赔偿计算。

    消法第55条：经营者有欺诈行为 → 退一赔三，不足500按500
    食安法第148条：不符合食品安全标准 → 退一赔十，不足1000按1000
    """

    base = _nvl(punitive_base, purchase_price)
    breakdown = {}
    warning = ""

    # 退款
    breakdown["应退价款"] = purchase_price

    # 惩罚性赔偿
    if case_type == ConsumerCase.FRAUD:
        punitive = base * 3
        floor = 500.0
        label = "惩罚性赔偿（退一赔三）"
        legal = "《消费者权益保护法》第55条"
        if punitive < floor:
            punitive = floor
            warning = f"三倍赔偿额{purchase_price*3:,.2f}元不足{floor}元，按{floor}元计"
    elif case_type == ConsumerCase.FOOD_SAFETY:
        punitive = base * 10
        floor = 1000.0
        label = "惩罚性赔偿（退一赔十）"
        legal = "《食品安全法》第148条"
        if punitive < floor:
            punitive = floor
            warning = f"十倍赔偿额{purchase_price*10:,.2f}元不足{floor}元，按{floor}元计"
    else:  # BOTH → 食安法优先
        punitive = base * 10
        floor = 1000.0
        label = "惩罚性赔偿（退一赔十，食安法优先）"
        legal = "《食品安全法》第148条（食安问题优先于消法第55条）"
        if punitive < floor:
            punitive = floor
            warning = f"十倍赔偿额{purchase_price*10:,.2f}元不足{floor}元，按{floor}元计"

    breakdown[label] = punitive

    # 其他损失
    if additional_damage:
        breakdown["其他实际损失"] = additional_damage

    total = purchase_price + punitive + additional_damage

    legal_basis = legal

    return DamageResult(
        case_type="消费者权益赔偿",
        total=round(total, 2),
        breakdown=breakdown,
        legal_basis=legal_basis,
        formula=(
            f"应退{purchase_price:,.2f} + {label.split('(')[0].strip()}{punitive:,.2f}"
            + (f" + 其他损失{additional_damage:,.2f}" if additional_damage else "")
            + f" = {total:,.2f}"
        ),
        warning=warning,
    )


# ─── 便捷入口 ────────────────────────────────────────────────────────────────

def calculate(case_type: str, **kwargs) -> DamageResult:
    """统一计算入口。

    Args:
        case_type: 类型标识
            "personal_injury" / "人身损害"
            "traffic_accident" / "交通事故"
            "breach" / "违约"
            "labor" / "劳动"
            "consumer" / "消费"
        **kwargs: 对应计算函数的参数

    Returns:
        DamageResult

    Examples:
        r = calculate("人身损害", medical_expense=5000, lost_wages=10000)
        r = calculate("劳动", monthly_wage=8000, years_of_service=3.5,
                      termination_type=TerminationType.ILLEGAL)
    """
    case_map = {
        "personal_injury": calculate_personal_injury,
        "人身损害": calculate_personal_injury,
        "traffic_accident": calculate_traffic_accident,
        "交通事故": calculate_traffic_accident,
        "breach": calculate_breach_damages,
        "违约": calculate_breach_damages,
        "labor": calculate_labor_comp,
        "劳动": calculate_labor_comp,
        "consumer": calculate_consumer_comp,
        "消费": calculate_consumer_comp,
    }

    func = case_map.get(case_type)
    if func is None:
        raise ValueError(
            f"未知案件类型 '{case_type}'，"
            "支持：人身损害 / 交通事故 / 违约 / 劳动 / 消费"
        )

    return func(**kwargs)


# ═══════════════════════════════════════════════════════════════════════════════
# 自测
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 65)
    print("损害赔偿计算器 —— 五类赔偿金计算验证")
    print("=" * 65)

    stats = {"passed": 0, "failed": 0}

    def check(label, result, expect=None, field="total"):
        val = getattr(result, field, None)
        status = "✅" if (expect is None or val == expect) else "❌"
        if status == "✅":
            stats["passed"] += 1
        else:
            stats["failed"] += 1
        print(f"\n  [{status}] {label}")
        print(f"    total: {val:,.2f}")
        print(f"    case:  {result.case_type}")
        print(f"    法律依据: {result.legal_basis[:80]}...")
        if result.warning:
            print(f"    ⚠️ 提示: {result.warning[:80]}")
        for k, v in result.breakdown.items():
            print(f"    {k}: {v:,.2f}")

    # ── 1. 人身损害 ──
    print("\n" + "─" * 40)
    print("模块1: 人身损害赔偿")

    r1 = calculate_personal_injury(
        medical_expense=80000,
        lost_wages=50000,
        hospitalization_days=30,
        injury_grade=InjuryGrade.LEVEL_10,
        mental_anguish=20000,
    )
    check("十级伤残+住院30天", r1)

    r1b = calculate_personal_injury(
        is_death=True,
        medical_expense=120000,
        lost_wages=60000,
        mental_anguish=50000,
    )
    check("死亡赔偿（自动计算）", r1b)

    r1c = calculate_personal_injury(
        injury_grade=InjuryGrade.LEVEL_5,
        victim_age=65,
        mental_anguish=80000,
    )
    check("五级伤残+65岁（年限递减", r1c)

    # ── 2. 交通事故 ──
    print("\n" + "─" * 40)
    print("模块2: 交通事故赔偿")

    r2 = calculate_traffic_accident(
        medical_expense=50000,
        lost_wages=30000,
        hospitalization_days=20,
        injury_grade=InjuryGrade.LEVEL_10,
        property_loss=5000,
        victim_fault_ratio=0.3,
    )
    check("十级伤残+30%过错", r2)

    r2b = calculate_traffic_accident(
        is_death=True,
        medical_expense=80000,
        lost_wages=60000,
        mental_anguish=50000,
        vehicle_damage=15000,
        victim_fault_ratio=0.0,
    )
    check("死亡+全责", r2b)

    # ── 3. 违约 ──
    print("\n" + "─" * 40)
    print("模块3: 违约赔偿")

    r3 = calculate_breach_damages(
        actual_loss=50000,
        lost_profit=20000,
    )
    check("无违约金（法定损失）", r3)

    r3b = calculate_breach_damages(
        actual_loss=50000,
        lost_profit=20000,
        contract_penalty=150000,
        excessive_penalty=True,
    )
    check("违约金过高（应调整）", r3b)

    r3c = calculate_breach_damages(
        actual_loss=50000,
        deposit_paid=30000,
    )
    check("定金罚则（给付方违约）", r3c)

    # ── 4. 劳动 ──
    print("\n" + "─" * 40)
    print("模块4: 劳动经济补偿")

    r4 = calculate_labor_comp(
        monthly_wage=12000,
        years_of_service=5.5,
        termination_type=TerminationType.NORMAL,
    )
    check("正常解除 N=5.5年", r4)

    r4b = calculate_labor_comp(
        monthly_wage=12000,
        years_of_service=5.5,
        termination_type=TerminationType.ILLEGAL,
    )
    check("违法解除 2N=5.5年", r4b)

    r4c = calculate_labor_comp(
        monthly_wage=12000,
        years_of_service=5.5,
        termination_type=TerminationType.WITHOUT_NOTICE,
    )
    check("N+1 补偿", r4c)

    r4d = calculate_labor_comp(
        monthly_wage=40000,
        years_of_service=15,
        termination_type=TerminationType.ILLEGAL,
    )
    check("高收入者封顶", r4d)

    # ── 5. 消费者 ──
    print("\n" + "─" * 40)
    print("模块5: 消费者赔偿")

    r5 = calculate_consumer_comp(
        purchase_price=100,
        case_type=ConsumerCase.FRAUD,
    )
    check("退一赔三（不足500→按500）", r5)

    r5b = calculate_consumer_comp(
        purchase_price=2000,
        case_type=ConsumerCase.FRAUD,
        additional_damage=500,
    )
    check("退一赔三 + 其他损失", r5b)

    r5c = calculate_consumer_comp(
        purchase_price=50,
        case_type=ConsumerCase.FOOD_SAFETY,
    )
    check("退一赔十（不足1000→按1000）", r5c)

    # ── 便捷入口 ──
    print("\n" + "─" * 40)
    print("便捷入口测试")

    r6 = calculate("人身损害", medical_expense=10000, lost_wages=20000)
    check("统一入口-人身损害", r6)

    r6b = calculate("劳动", monthly_wage=10000, years_of_service=3,
                    termination_type=TerminationType.NORMAL)
    check("统一入口-劳动", r6b)

    # ── 汇总 ──
    print("\n" + "=" * 65)
    total_tests = stats["passed"] + stats["failed"]
    print(f"通过: {stats['passed']}/{total_tests}  |  失败: {stats['failed']}/{total_tests}")
    print("=" * 65)
