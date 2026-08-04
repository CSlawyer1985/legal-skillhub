#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
蚂蚁工资条 · 劳动争议风险评估引擎
=====================================
覆盖 36+ 争议场景，三维风险评分（法律×经济×声誉），
四维调节因子（城市/行业/公司类型/岗位），
赔偿金额预计算，同类判例匹配。

用法:
  python labor_dispute_risk_engine.py --scenario "未签劳动合同" --monthly "15000" --months 8 --city "北京" --industry "互联网" --company-type "民营企业" --position "技术研发"
  python labor_dispute_risk_engine.py --demo
  python labor_dispute_risk_engine.py --demo --json
"""

from __future__ import annotations
import json
import math
import statistics
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, date
from typing import Optional, List, Dict, Tuple, Any


# ============================================================================
#  数据模型
# ============================================================================

@dataclass
class DisputeScenario:
    """劳动争议场景"""
    code: str                          # 场景代码
    name: str                          # 场景名称
    category: str                      # 大类：合同/薪酬/社保/解雇/工时/工伤/竞业/其他
    law_basis: List[str]               # 法律依据
    risk_legal: float                  # 法律风险基础分 (0-100)
    risk_economic: float               # 经济风险基础分 (0-100)
    risk_reputation: float             # 声誉风险基础分 (0-100)
    compensation_formula: str          # 赔偿计算公式说明
    evidence_checklist: List[str]      # 企业需准备的证据清单
    typical_arbitration_win_rate: float  # 典型仲裁中劳动者胜诉率
    common_defenses: List[str]         # 企业常见抗辩理由
    defense_success_rate: float        # 抗辩成功率 (0-1)
    statute_of_limitation: int         # 仲裁时效(月)
    high_risk_industries: List[str]    # 高发行业
    high_risk_cities: List[str]        # 高发城市
    high_risk_positions: List[str]     # 高发岗位
    high_risk_company_types: List[str] # 高发企业类型
    recommend_settlement_range: Tuple[float, float]  # 和解金额建议区间（占法定赔偿的比例）


@dataclass
class AdjustmentFactors:
    """四维调节因子"""
    city_factor: float
    industry_factor: float
    company_type_factor: float
    position_factor: float


@dataclass
class CompensationResult:
    """赔偿预计算结果"""
    item: str
    amount: float
    formula: str
    legal_basis: str
    notes: str


@dataclass
class CaseReference:
    """同类判例参考"""
    case_id: str
    case_summary: str
    outcome: str               # 劳动者胜诉/企业胜诉/调解结案
    compensation_awarded: float
    key_factor: str
    city: str
    industry: str


@dataclass
class RiskAssessmentResult:
    """风险评估完整结果"""
    scenario_code: str
    scenario_name: str
    category: str
    # 三维风险评分
    risk_legal: float
    risk_economic: float
    risk_reputation: float
    risk_composite: float
    risk_level: str                       # 极高/高/中/低
    # 调节因子
    adjustments: Dict[str, Any]
    # 赔偿预计算
    estimated_compensation: float
    compensation_range: Tuple[float, float]
    compensation_items: List[Dict[str, Any]]
    recommended_settlement: float
    # 法律信息
    law_basis: List[str]
    evidence_checklist: List[str]
    common_defenses: List[str]
    defense_success_rate: float
    # 判例
    similar_cases: List[Dict[str, Any]]
    # 时效
    statute_of_limitation_months: int
    urgent_warning: bool
    # 行动建议
    recommend_immediate: List[str]
    recommend_short_term: List[str]
    recommend_long_term: List[str]
    # 元数据
    assessment_time: str
    confidence: str                     # 高/中/低


# ============================================================================
#  36+ 争议场景库
# ============================================================================

DISPUTE_SCENARIOS: Dict[str, DisputeScenario] = {
    # ========== 劳动合同类 (7) ==========
    "no_contract": DisputeScenario(
        code="no_contract",
        name="未签订书面劳动合同",
        category="劳动合同",
        law_basis=["《劳动合同法》第10条", "《劳动合同法》第82条"],
        risk_legal=85, risk_economic=70, risk_reputation=55,
        compensation_formula="二倍工资差额 = 月工资 × (实际工作月数 - 1)，上限11个月",
        evidence_checklist=["考勤记录", "工资发放记录", "工作证/工牌", "社保缴纳记录", "工作邮件/微信沟通记录", "证人证言"],
        typical_arbitration_win_rate=0.92,
        common_defenses=["已签但劳动者拒签", "劳动者系劳务关系非劳动关系", "劳动者为高管/人事负责人", "已过仲裁时效"],
        defense_success_rate=0.15,
        statute_of_limitation=12,
        high_risk_industries=["建筑", "餐饮", "零售", "物流", "教育培训"],
        high_risk_cities=["深圳", "广州", "杭州", "成都"],
        high_risk_positions=["一线工人", "销售", "服务员", "快递员"],
        high_risk_company_types=["小微企业", "个体工商户", "初创公司"],
        recommend_settlement_range=(0.6, 0.9),
    ),
    "contract_not_renewed": DisputeScenario(
        code="contract_not_renewed",
        name="劳动合同期满不续签",
        category="劳动合同",
        law_basis=["《劳动合同法》第44条", "《劳动合同法》第46条"],
        risk_legal=75, risk_economic=60, risk_reputation=40,
        compensation_formula="经济补偿金 N = 工作年限 × 月平均工资（不满半年计0.5，满半年计1）",
        evidence_checklist=["已到期劳动合同", "不续签通知", "终止前12个月工资单", "考勤记录"],
        typical_arbitration_win_rate=0.80,
        common_defenses=["劳动者主动不续签", "续签条件不低于原合同", "劳动者存在违纪行为"],
        defense_success_rate=0.25,
        statute_of_limitation=12,
        high_risk_industries=["制造业", "互联网", "金融"],
        high_risk_cities=["上海", "北京", "深圳"],
        high_risk_positions=["中层管理", "技术人员", "合同即将到期的老员工"],
        high_risk_company_types=["外企", "大型民营企业"],
        recommend_settlement_range=(0.7, 1.0),
    ),
    "contract_terms_illegal": DisputeScenario(
        code="contract_terms_illegal",
        name="劳动合同条款违法（如违法约定试用期/违约金）",
        category="劳动合同",
        law_basis=["《劳动合同法》第19条", "《劳动合同法》第22-25条", "《劳动合同法》第83条"],
        risk_legal=70, risk_economic=50, risk_reputation=45,
        compensation_formula="违法试用期赔偿 = 试用期满月工资 × 违法试用期月数；违法违约金条款无效，已支付部分应予返还",
        evidence_checklist=["劳动合同文本", "工资发放记录", "培训费用凭证（如涉及服务期）"],
        typical_arbitration_win_rate=0.85,
        common_defenses=["条款系双方自愿约定", "劳动者未提出异议", "违约金有合法依据"],
        defense_success_rate=0.10,
        statute_of_limitation=12,
        high_risk_industries=["教育培训", "互联网", "咨询服务"],
        high_risk_cities=["北京", "上海", "深圳"],
        high_risk_positions=["应届生", "转行者", "高端技术人员（竞业限制问题）"],
        high_risk_company_types=["初创公司", "培训机构"],
        recommend_settlement_range=(0.5, 0.85),
    ),
    "no_fixed_term_contract": DisputeScenario(
        code="no_fixed_term_contract",
        name="应签无固定期限合同未签",
        category="劳动合同",
        law_basis=["《劳动合同法》第14条", "《劳动合同法》第82条第二款"],
        risk_legal=80, risk_economic=65, risk_reputation=50,
        compensation_formula="未签无固定期限合同的二倍工资差额 = 月工资 × 未签月数",
        evidence_checklist=["工龄证明", "连续签订两次固定期限合同证明", "工作满10年证明"],
        typical_arbitration_win_rate=0.82,
        common_defenses=["劳动者主动要求签固定期限", "劳动者不符合条件", "已过时效"],
        defense_success_rate=0.18,
        statute_of_limitation=12,
        high_risk_industries=["制造业", "服务业", "国企"],
        high_risk_cities=["北京", "上海", "广州"],
        high_risk_positions=["老员工（10年以上）", "连续续签2次的员工"],
        high_risk_company_types=["国企", "大型民企"],
        recommend_settlement_range=(0.6, 0.9),
    ),
    "internship_dispute": DisputeScenario(
        code="internship_dispute",
        name="实习生/试用期劳动争议",
        category="劳动合同",
        law_basis=["《劳动合同法》第19条", "《劳动合同法》第20条", "《关于贯彻执行劳动法若干问题的意见》第12条"],
        risk_legal=55, risk_economic=30, risk_reputation=50,
        compensation_formula="试用期工资不得低于合同约定工资80%且不低于当地最低工资；违法约定试用期需按转正工资赔偿",
        evidence_checklist=["实习协议/劳动合同", "工资发放记录", "工作安排记录", "是否独立承担工作任务"],
        typical_arbitration_win_rate=0.68,
        common_defenses=["系在校生实习非劳动关系", "试用期约定合法", "劳动者不符合录用条件"],
        defense_success_rate=0.35,
        statute_of_limitation=12,
        high_risk_industries=["互联网", "媒体", "教育培训"],
        high_risk_cities=["北京", "杭州", "成都"],
        high_risk_positions=["应届毕业生", "实习生"],
        high_risk_company_types=["创业公司", "中小企业"],
        recommend_settlement_range=(0.3, 0.6),
    ),
    "dispatch_labor_dispute": DisputeScenario(
        code="dispatch_labor_dispute",
        name="劳务派遣争议（同工不同酬/岗位超范围）",
        category="劳动合同",
        law_basis=["《劳动合同法》第58-67条", "《劳务派遣暂行规定》"],
        risk_legal=72, risk_economic=55, risk_reputation=48,
        compensation_formula="同工同酬差额 + 可能的二倍工资（派遣公司未签合同）",
        evidence_checklist=["派遣协议", "同岗位正式员工工资标准", "工作岗位说明", "派遣岗位三性证明"],
        typical_arbitration_win_rate=0.78,
        common_defenses=["岗位不符合三性系劳动者签字确认", "薪酬差异属于正常薪酬带宽", "派遣单位非用工单位"],
        defense_success_rate=0.22,
        statute_of_limitation=12,
        high_risk_industries=["制造业", "物流", "银行", "保险"],
        high_risk_cities=["北上广深通用"],
        high_risk_positions=["客服", "操作工", "行政辅助"],
        high_risk_company_types=["大型国企", "外资制造企业"],
        recommend_settlement_range=(0.5, 0.8),
    ),
    "contract_change_unilateral": DisputeScenario(
        code="contract_change_unilateral",
        name="单方面变更劳动合同内容（调岗/降薪/变更工作地点）",
        category="劳动合同",
        law_basis=["《劳动合同法》第35条", "《劳动合同法》第38条"],
        risk_legal=78, risk_economic=55, risk_reputation=52,
        compensation_formula="被迫解除的经济补偿N + 工资差额补发",
        evidence_checklist=["变更通知书", "劳动者书面异议", "原劳动合同", "变更前后的薪资对比"],
        typical_arbitration_win_rate=0.80,
        common_defenses=["企业经营需要合理调岗", "劳动者已实际履行视为同意", "变更不构成重大变更"],
        defense_success_rate=0.20,
        statute_of_limitation=12,
        high_risk_industries=["零售", "房地产", "互联网（业务调整频繁）"],
        high_risk_cities=["北京", "上海", "深圳"],
        high_risk_positions=["中层管理", "销售", "行政"],
        high_risk_company_types=["大型民营企业", "外企"],
        recommend_settlement_range=(0.5, 0.8),
    ),

    # ========== 工资薪酬类 (6) ==========
    "wage_arrears": DisputeScenario(
        code="wage_arrears",
        name="拖欠/克扣工资",
        category="薪酬",
        law_basis=["《劳动合同法》第30条", "《劳动合同法》第85条", "《工资支付暂行规定》"],
        risk_legal=90, risk_economic=75, risk_reputation=65,
        compensation_formula="拖欠工资金额 + 50%-100% 加付赔偿金 + 被迫解除的经济补偿 N",
        evidence_checklist=["工资条/银行流水", "工资制度文件", "考勤记录", "催讨记录", "欠薪金额计算表"],
        typical_arbitration_win_rate=0.93,
        common_defenses=["劳动者绩效不达标", "企业经营困难可暂缓", "已与劳动者协商一致"],
        defense_success_rate=0.08,
        statute_of_limitation=12,
        high_risk_industries=["建筑", "制造业", "餐饮", "零售", "房地产"],
        high_risk_cities=["全国通用（欠薪高发城市：东莞/温州/泉州/重庆）"],
        high_risk_positions=["一线工人", "销售", "建筑工人"],
        high_risk_company_types=["小微企业", "资金链紧张的创业公司", "房地产企业"],
        recommend_settlement_range=(0.75, 1.0),
    ),
    "overtime_pay": DisputeScenario(
        code="overtime_pay",
        name="加班费争议",
        category="薪酬",
        law_basis=["《劳动法》第44条", "《劳动合同法》第31条", "《工资支付暂行规定》第13条"],
        risk_legal=82, risk_economic=68, risk_reputation=50,
        compensation_formula="法定加班费 = 工作日1.5倍 + 休息日2倍 + 法定节假日3倍（全部历史加班）",
        evidence_checklist=["考勤打卡记录", "加班审批记录", "工作成果产出时间记录", "加班工资支付凭证"],
        typical_arbitration_win_rate=0.75,
        common_defenses=["加班需审批,劳动者未经审批", "劳动者自愿加班", "已包含在绩效工资中", "实行综合计算工时制"],
        defense_success_rate=0.25,
        statute_of_limitation=12,
        high_risk_industries=["互联网", "金融", "房地产", "制造业", "咨询"],
        high_risk_cities=["北京", "上海", "深圳", "杭州"],
        high_risk_positions=["程序员", "项目经理", "设计", "运营"],
        high_risk_company_types=["互联网公司（996文化）", "金融投行", "快速成长型企业"],
        recommend_settlement_range=(0.5, 0.8),
    ),
    "bonus_dispute": DisputeScenario(
        code="bonus_dispute",
        name="年终奖/绩效奖金争议",
        category="薪酬",
        law_basis=["《劳动合同法》第4条", "《关于工资总额组成的规定》"],
        risk_legal=60, risk_economic=45, risk_reputation=35,
        compensation_formula="年终奖金额（如有明确约定或制度规定）",
        evidence_checklist=["薪酬制度文件", "绩效评估记录", "历史年终奖发放记录", "劳动合同中薪酬条款"],
        typical_arbitration_win_rate=0.55,
        common_defenses=["年终奖为自主福利非强制", "绩效考核结果为发放条件", "离职员工不享受年终奖"],
        defense_success_rate=0.45,
        statute_of_limitation=12,
        high_risk_industries=["金融", "互联网", "房地产"],
        high_risk_cities=["北京", "上海", "深圳"],
        high_risk_positions=["销售", "管理人员", "技术人员"],
        high_risk_company_types=["大企业", "外企"],
        recommend_settlement_range=(0.3, 0.6),
    ),
    "minimum_wage": DisputeScenario(
        code="minimum_wage",
        name="低于最低工资标准",
        category="薪酬",
        law_basis=["《劳动法》第48条", "《最低工资规定》"],
        risk_legal=88, risk_economic=55, risk_reputation=60,
        compensation_formula="补足差额 + 差额的50%-100%赔偿金",
        evidence_checklist=["工资条/银行流水", "当地最低工资标准文件", "考勤记录"],
        typical_arbitration_win_rate=0.95,
        common_defenses=["含加班费/补贴后已达标", "劳动者未满勤", "实习期/试用期单独标准"],
        defense_success_rate=0.05,
        statute_of_limitation=12,
        high_risk_industries=["餐饮", "零售", "物业服务", "安保"],
        high_risk_cities=["三四线城市", "县城"],
        high_risk_positions=["服务员", "保洁", "保安", "一线操作工"],
        high_risk_company_types=["小微企业", "个体工商户"],
        recommend_settlement_range=(0.8, 1.0),
    ),
    "wage_deduction_illegal": DisputeScenario(
        code="wage_deduction_illegal",
        name="违法罚款/扣工资",
        category="薪酬",
        law_basis=["《工资支付暂行规定》第15-16条"],
        risk_legal=75, risk_economic=40, risk_reputation=45,
        compensation_formula="返还违法扣款 + 可能的赔偿",
        evidence_checklist=["罚款通知/扣款凭证", "企业规章制度", "劳动者违纪证据", "工资条"],
        typical_arbitration_win_rate=0.82,
        common_defenses=["属合法代扣代缴", "规章制度明示且合理", "劳动者造成实际损失"],
        defense_success_rate=0.18,
        statute_of_limitation=12,
        high_risk_industries=["制造", "零售", "物流"],
        high_risk_cities=["全国通用"],
        high_risk_positions=["一线工人", "销售", "客服"],
        high_risk_company_types=["民营企业", "小微制造企业"],
        recommend_settlement_range=(0.6, 0.9),
    ),
    "commission_dispute": DisputeScenario(
        code="commission_dispute",
        name="销售提成/绩效工资争议",
        category="薪酬",
        law_basis=["《劳动合同法》第4条", "《关于工资总额组成的规定》"],
        risk_legal=65, risk_economic=50, risk_reputation=30,
        compensation_formula="应发提成/绩效工资金额",
        evidence_checklist=["提成制度/绩效方案", "业绩达成数据", "历史发放记录", "劳动合同"],
        typical_arbitration_win_rate=0.60,
        common_defenses=["提成制度已明确告知", "业绩核算标准一致", "离职后提成归零条款", "客户回款后才计提成"],
        defense_success_rate=0.40,
        statute_of_limitation=12,
        high_risk_industries=["房地产", "保险", "教育培训", "互联网电商"],
        high_risk_cities=["全国通用"],
        high_risk_positions=["销售", "客户经理", "房产中介"],
        high_risk_company_types=["销售驱动型企业"],
        recommend_settlement_range=(0.4, 0.75),
    ),

    # ========== 解除与终止类 (8) ==========
    "wrongful_dismissal": DisputeScenario(
        code="wrongful_dismissal",
        name="违法解除劳动合同",
        category="解除终止",
        law_basis=["《劳动合同法》第48条", "《劳动合同法》第87条"],
        risk_legal=90, risk_economic=82, risk_reputation=75,
        compensation_formula="2N = 2 × 工作年限 × 月平均工资（3倍社平封顶）",
        evidence_checklist=["解除通知书", "解除事由的证明材料", "规章制度民主程序记录", "劳动者违纪证据"],
        typical_arbitration_win_rate=0.88,
        common_defenses=["劳动者严重违纪", "劳动者不胜任经培训调岗后仍不胜任", "经济性裁员符合程序"],
        defense_success_rate=0.12,
        statute_of_limitation=12,
        high_risk_industries=["互联网", "金融", "房地产", "制造业"],
        high_risk_cities=["北京", "上海", "深圳", "广州"],
        high_risk_positions=["中层管理", "技术人员", "销售"],
        high_risk_company_types=["大型企业（裁员频繁）", "快速扩张后收缩的企业"],
        recommend_settlement_range=(0.6, 0.9),
    ),
    "economic_dismissal": DisputeScenario(
        code="economic_dismissal",
        name="经济性裁员争议（不符合程序/未提前通知/方案不合理）",
        category="解除终止",
        law_basis=["《劳动合同法》第41条"],
        risk_legal=80, risk_economic=75, risk_reputation=65,
        compensation_formula="N（程序合法的经济性裁员）= 工作年限 × 月平均工资；如程序违法则按2N",
        evidence_checklist=["裁员方案", "职工代表大会意见", "劳动行政部门报告回执", "优先留用人员名单", "提前30日通知证明"],
        typical_arbitration_win_rate=0.76,
        common_defenses=["符合经济性裁员条件", "已履行法定程序", "已依法支付补偿"],
        defense_success_rate=0.24,
        statute_of_limitation=12,
        high_risk_industries=["制造业", "房地产", "互联网", "教育培训（双减后）"],
        high_risk_cities=["深圳", "北京", "上海"],
        high_risk_positions=["一线工人", "中层管理", "支持部门"],
        high_risk_company_types=["大型制造业企业", "地产企业", "互联网大厂"],
        recommend_settlement_range=(0.6, 0.9),
    ),
    "forced_resignation": DisputeScenario(
        code="forced_resignation",
        name="被迫解除（变相逼迫离职）",
        category="解除终止",
        law_basis=["《劳动合同法》第38条"],
        risk_legal=78, risk_economic=70, risk_reputation=60,
        compensation_formula="N（被迫解除经济补偿） + 可能的违法解除2N",
        evidence_checklist=["调岗/降薪/不提供劳动条件等证据", "书面催告记录", "辞职通知（注明系被迫）", "工资变化记录"],
        typical_arbitration_win_rate=0.72,
        common_defenses=["劳动者自愿辞职", "工作调整系合理经营安排", "不存在胁迫"],
        defense_success_rate=0.22,
        statute_of_limitation=12,
        high_risk_industries=["互联网", "金融", "房地产"],
        high_risk_cities=["北京", "上海", "深圳"],
        high_risk_positions=["中层管理", "老员工", "高绩效员工"],
        high_risk_company_types=["大型企业", "有裁员压力的企业"],
        recommend_settlement_range=(0.5, 0.8),
    ),
    "probation_dismissal": DisputeScenario(
        code="probation_dismissal",
        name="试用期解除争议（不符合录用条件认定）",
        category="解除终止",
        law_basis=["《劳动合同法》第39条第一项", "《劳动合同法》第21条"],
        risk_legal=68, risk_economic=40, risk_reputation=42,
        compensation_formula="如解除违法 = 2N（最长按试用期计算）",
        evidence_checklist=["录用条件书面文件", "不符合录用条件的客观证据", "试用期评估记录", "告知记录"],
        typical_arbitration_win_rate=0.58,
        common_defenses=["录用条件明确且已告知", "评估客观有据", "已履行告知义务"],
        defense_success_rate=0.42,
        statute_of_limitation=12,
        high_risk_industries=["互联网", "金融", "教育培训"],
        high_risk_cities=["北京", "上海", "杭州"],
        high_risk_positions=["应届生", "转行者", "试用期员工"],
        high_risk_company_types=["创业公司", "中小企业"],
        recommend_settlement_range=(0.3, 0.5),
    ),
    "maternity_dismissal": DisputeScenario(
        code="maternity_dismissal",
        name="三期女职工（孕期/产期/哺乳期）解雇",
        category="解除终止",
        law_basis=["《劳动合同法》第42条", "《女职工劳动保护特别规定》"],
        risk_legal=92, risk_economic=82, risk_reputation=85,
        compensation_formula="2N（违法解除）+ 孕期/产期/哺乳期待遇损失；或恢复劳动关系 + 期间工资补发",
        evidence_checklist=["解除通知书", "怀孕证明", "产假记录", "哺乳时间记录", "企业经营状况证明"],
        typical_arbitration_win_rate=0.94,
        common_defenses=["劳动者存在严重违纪", "劳动者隐瞒怀孕", "不属于三期保护范围"],
        defense_success_rate=0.06,
        statute_of_limitation=12,
        high_risk_industries=["全行业（特别：零售/金融/互联网/教育）"],
        high_risk_cities=["北京", "上海", "深圳"],
        high_risk_positions=["育龄女性员工", "中层管理/销售"],
        high_risk_company_types=["中小企业", "民营企业"],
        recommend_settlement_range=(0.7, 0.95),
    ),
    "medical_dismissal": DisputeScenario(
        code="medical_dismissal",
        name="医疗期职工解雇争议",
        category="解除终止",
        law_basis=["《劳动合同法》第40条第一项", "《劳动合同法》第42条", "《企业职工患病或非因工负伤医疗期规定》"],
        risk_legal=82, risk_economic=65, risk_reputation=70,
        compensation_formula="如解雇违法 = 2N；如医疗期满合法解雇 = N + 医疗补助费（不低于6个月工资）",
        evidence_checklist=["医疗证明", "医疗期计算", "复工通知", "劳动能力鉴定", "另行安排工作的证明"],
        typical_arbitration_win_rate=0.78,
        common_defenses=["医疗期已满且不能从事原工作也不能从事另行安排的工作", "已支付医疗补助费", "劳动者虚构病情"],
        defense_success_rate=0.20,
        statute_of_limitation=12,
        high_risk_industries=["制造业", "物流", "服务业"],
        high_risk_cities=["全国通用"],
        high_risk_positions=["一线工人", "体力劳动者"],
        high_risk_company_types=["制造业企业", "劳动密集型企业"],
        recommend_settlement_range=(0.55, 0.85),
    ),
    "mass_layoff": DisputeScenario(
        code="mass_layoff",
        name="大规模裁员群体性争议",
        category="解除终止",
        law_basis=["《劳动合同法》第41条", "《劳动合同法》第4条"],
        risk_legal=85, risk_economic=90, risk_reputation=88,
        compensation_formula="N（如程序合法）或 2N（如程序违法）；群体性事件附加行政压力",
        evidence_checklist=["裁员方案", "职代会/工会意见", "劳动行政部门备案", "补偿方案", "优先留用人员清单"],
        typical_arbitration_win_rate=0.75,
        common_defenses=["符合经济性裁员条件", "已优于法定标准补偿", "已履行民主程序"],
        defense_success_rate=0.18,
        statute_of_limitation=12,
        high_risk_industries=["互联网", "金融", "房地产", "汽车制造"],
        high_risk_cities=["北京", "上海", "深圳", "杭州", "广州"],
        high_risk_positions=["全岗位"],
        high_risk_company_types=["大型企业（业务收缩期）", "外资撤出企业"],
        recommend_settlement_range=(0.65, 0.95),
    ),
    "severance_calculation": DisputeScenario(
        code="severance_calculation",
        name="经济补偿金/N+1计算争议",
        category="解除终止",
        law_basis=["《劳动合同法》第47条", "《劳动合同法实施条例》第27条"],
        risk_legal=72, risk_economic=68, risk_reputation=38,
        compensation_formula="正确计算N = 工作年限 × 月平均工资（含奖金/津贴/加班费等应发工资）",
        evidence_checklist=["12个月工资条/银行流水", "奖金发放记录", "加班费记录", "津贴/补贴发放记录"],
        typical_arbitration_win_rate=0.82,
        common_defenses=["劳动者对工资基数理解有误", "补偿已按约定支付", "年终奖不应计入月平均工资"],
        defense_success_rate=0.18,
        statute_of_limitation=12,
        high_risk_industries=["全行业"],
        high_risk_cities=["全国通用"],
        high_risk_positions=["全岗位"],
        high_risk_company_types=["全类型"],
        recommend_settlement_range=(0.7, 0.95),
    ),

    # ========== 社会保险类 (5) ==========
    "social_insurance_underpayment": DisputeScenario(
        code="social_insurance_underpayment",
        name="未足额缴纳社保（基数不足/少缴险种）",
        category="社保",
        law_basis=["《社会保险法》第58条", "《社会保险法》第86条"],
        risk_legal=80, risk_economic=72, risk_reputation=68,
        compensation_formula="补缴差额（企业部分+个人部分） + 滞纳金（日万分之五）+ 可能的罚款（差额1-3倍）",
        evidence_checklist=["社保缴费记录", "工资发放记录", "劳动合同", "社保基数核定表"],
        typical_arbitration_win_rate=0.85,
        common_defenses=["基数按当地最低标准核定", "劳动者知情同意", "已补缴"],
        defense_success_rate=0.12,
        statute_of_limitation=0,  # 社保补缴无仲裁时效限制
        high_risk_industries=["全行业"],
        high_risk_cities=["北京", "上海", "深圳", "杭州"],
        high_risk_positions=["全岗位"],
        high_risk_company_types=["中小企业", "民营企业（普遍问题）"],
        recommend_settlement_range=(0.8, 1.0),
    ),
    "social_insurance_not_registered": DisputeScenario(
        code="social_insurance_not_registered",
        name="未为员工办理社会保险登记",
        category="社保",
        law_basis=["《社会保险法》第57-58条", "《社会保险法》第84条"],
        risk_legal=88, risk_economic=75, risk_reputation=72,
        compensation_formula="补缴全部历史社保 + 滞纳金 + 罚款（应缴额1-3倍）；劳动者可据此被迫解除（第38条）→ 经济补偿N",
        evidence_checklist=["社保账户查询记录", "劳动关系证明", "工资发放记录"],
        typical_arbitration_win_rate=0.93,
        common_defenses=["劳动者拒绝参保", "劳动者为劳务派遣/实习生", "已现金折现发放"],
        defense_success_rate=0.05,
        statute_of_limitation=0,
        high_risk_industries=["餐饮", "建筑", "零售", "物流"],
        high_risk_cities=["三四线城市", "县城"],
        high_risk_positions=["一线工人", "临时工", "季节性用工"],
        high_risk_company_types=["小微企业", "个体工商户", "建筑劳务公司"],
        recommend_settlement_range=(0.8, 1.0),
    ),
    "work_injury_dispute": DisputeScenario(
        code="work_injury_dispute",
        name="工伤认定/工伤待遇争议",
        category="社保",
        law_basis=["《工伤保险条例》第14-17条", "《社会保险法》第36-41条"],
        risk_legal=86, risk_economic=85, risk_reputation=78,
        compensation_formula="工伤保险待遇（医疗费+停工留薪期工资+伤残补助金+就业补助金+医疗补助金等）",
        evidence_checklist=["工伤事故报告", "医疗记录", "证人证言", "现场监控/照片"],
        typical_arbitration_win_rate=0.78,
        common_defenses=["非工作时间/工作场所发生", "劳动者故意或重大过失", "不属于工伤认定范围"],
        defense_success_rate=0.22,
        statute_of_limitation=12,  # 工伤认定申请时效1年
        high_risk_industries=["建筑", "制造", "物流", "矿山", "化工"],
        high_risk_cities=["工业城市：东莞/苏州/佛山/无锡"],
        high_risk_positions=["一线工人", "建筑工人", "司机", "机械操作工"],
        high_risk_company_types=["制造业/建筑企业"],
        recommend_settlement_range=(0.6, 0.85),
    ),
    "housing_fund_dispute": DisputeScenario(
        code="housing_fund_dispute",
        name="住房公积金争议（未缴/少缴）",
        category="社保",
        law_basis=["《住房公积金管理条例》第20条", "《住房公积金管理条例》第38条"],
        risk_legal=75, risk_economic=68, risk_reputation=50,
        compensation_formula="补缴差额（企业+个人部分）+ 可能的罚款（1-5万元）",
        evidence_checklist=["公积金缴存记录", "工资发放记录", "劳动合同"],
        typical_arbitration_win_rate=0.88,
        common_defenses=["劳动者同意不缴", "已以现金或补贴形式发放", "非强制缴纳"],
        defense_success_rate=0.08,
        statute_of_limitation=0,
        high_risk_industries=["全行业（特别中小企业）"],
        high_risk_cities=["北京", "上海", "深圳", "广州"],
        high_risk_positions=["全岗位"],
        high_risk_company_types=["中小企业", "创业公司"],
        recommend_settlement_range=(0.75, 1.0),
    ),
    "work_injury_claim_dispute": DisputeScenario(
        code="work_injury_claim_dispute",
        name="工伤赔偿数额争议（伤残等级/工资基数/待遇标准）",
        category="社保",
        law_basis=["《工伤保险条例》第33-45条", "《社会保险法》第38-39条"],
        risk_legal=78, risk_economic=75, risk_reputation=55,
        compensation_formula="按实际伤残等级和工资基数重算差额",
        evidence_checklist=["伤残等级鉴定书", "12个月工资证明", "医疗费票据", "康复费用凭证"],
        typical_arbitration_win_rate=0.80,
        common_defenses=["伤残等级认定有争议", "工资基数以当地社平为准", "已全额支付"],
        defense_success_rate=0.20,
        statute_of_limitation=12,
        high_risk_industries=["建筑", "制造", "物流"],
        high_risk_cities=["东莞", "苏州", "佛山"],
        high_risk_positions=["一线工人"],
        high_risk_company_types=["中小制造业"],
        recommend_settlement_range=(0.55, 0.8),
    ),

    # ========== 工时与休假类 (4) ==========
    "annual_leave_dispute": DisputeScenario(
        code="annual_leave_dispute",
        name="未休年假折算争议",
        category="工时休假",
        law_basis=["《职工带薪年休假条例》第5条", "《企业职工带薪年休假实施办法》第10-12条"],
        risk_legal=72, risk_economic=40, risk_reputation=30,
        compensation_formula="日工资 × 300% × 未休天数（含正常工资100%）",
        evidence_checklist=["年假申请记录", "考勤记录", "年假制度文件", "工资单"],
        typical_arbitration_win_rate=0.80,
        common_defenses=["劳动者已休完年假", "劳动者未主动申请视为放弃（无效抗辩）", "已支付年假补偿"],
        defense_success_rate=0.15,
        statute_of_limitation=12,
        high_risk_industries=["互联网", "金融", "咨询", "制造业"],
        high_risk_cities=["北京", "上海", "深圳"],
        high_risk_positions=["中层管理", "技术人员", "一线工人"],
        high_risk_company_types=["加班文化企业", "制造业企业"],
        recommend_settlement_range=(0.5, 0.8),
    ),
    "rest_day_overtime": DisputeScenario(
        code="rest_day_overtime",
        name="休息日加班工资争议",
        category="工时休假",
        law_basis=["《劳动法》第44条第二项"],
        risk_legal=76, risk_economic=55, risk_reputation=35,
        compensation_formula="休息日加班2倍 × 天数",
        evidence_checklist=["考勤记录", "加班审批/通知记录", "加班费发放明细", "排班表"],
        typical_arbitration_win_rate=0.74,
        common_defenses=["已安排补休", "非单位安排加班", "已含在综合工时/不定时工时制中"],
        defense_success_rate=0.26,
        statute_of_limitation=12,
        high_risk_industries=["互联网", "制造业", "零售"],
        high_risk_cities=["北京", "上海", "深圳", "杭州"],
        high_risk_positions=["程序员", "运营", "客服", "一线工人"],
        high_risk_company_types=["996企业", "制造业加班企业"],
        recommend_settlement_range=(0.5, 0.75),
    ),
    "statutory_holiday_overtime": DisputeScenario(
        code="statutory_holiday_overtime",
        name="法定节假日加班工资争议",
        category="工时休假",
        law_basis=["《劳动法》第44条第三项"],
        risk_legal=82, risk_economic=50, risk_reputation=40,
        compensation_formula="法定节假日加班3倍 × 天数",
        evidence_checklist=["节假日排班记录", "加班通知", "工资条（无3倍工资记录）"],
        typical_arbitration_win_rate=0.85,
        common_defenses=["已安排轮休补休", "用人单位已支付", "劳动者自愿值班"],
        defense_success_rate=0.12,
        statute_of_limitation=12,
        high_risk_industries=["零售", "餐饮", "交通", "医疗", "旅游"],
        high_risk_cities=["旅游城市", "北上广深"],
        high_risk_positions=["服务员", "销售", "客服", "司机"],
        high_risk_company_types=["服务行业企业"],
        recommend_settlement_range=(0.6, 0.85),
    ),
    "flexible_work_hours": DisputeScenario(
        code="flexible_work_hours",
        name="不定时/综合计算工时制争议",
        category="工时休假",
        law_basis=["《关于企业实行不定时工作制和综合计算工时工作制的审批办法》"],
        risk_legal=65, risk_economic=45, risk_reputation=30,
        compensation_formula="超出标准工时的加班费差额",
        evidence_checklist=["劳动部门审批文件", "劳动合同工时条款", "考勤记录", "工资发放明细"],
        typical_arbitration_win_rate=0.56,
        common_defenses=["已获审批且告知", "实行综合计算后未超总工时", "岗位符合不定时工时制适用范围"],
        defense_success_rate=0.40,
        statute_of_limitation=12,
        high_risk_industries=["销售", "物流", "IT运维", "高级管理"],
        high_risk_cities=["全国通用"],
        high_risk_positions=["销售", "外勤", "高管", "运维"],
        high_risk_company_types=["销售型企业", "物流企业"],
        recommend_settlement_range=(0.35, 0.6),
    ),

    # ========== 竞业限制与保密类 (3) ==========
    "non_compete_compensation": DisputeScenario(
        code="non_compete_compensation",
        name="竞业限制补偿金争议（未付/少付/标准争议）",
        category="竞业限制",
        law_basis=["《劳动合同法》第23-24条", "最高法劳动争议司法解释（四）第6-10条"],
        risk_legal=68, risk_economic=55, risk_reputation=35,
        compensation_formula="按约定或法定标准（≥离职前12个月平均工资30%或当地最低工资取高者）× 限制月数",
        evidence_checklist=["竞业限制协议", "竞业限制补偿支付记录", "离职前12个月工资证明", "劳动者违反竞业的证据（如适用）"],
        typical_arbitration_win_rate=0.74,
        common_defenses=["竞业限制协议无效/范围过宽", "劳动者未履行竞业义务", "补偿已包含在离职补偿中"],
        defense_success_rate=0.26,
        statute_of_limitation=12,
        high_risk_industries=["互联网/科技", "金融", "医药", "游戏"],
        high_risk_cities=["北京", "上海", "深圳", "杭州"],
        high_risk_positions=["核心技术人员", "高管", "销售负责人", "产品经理"],
        high_risk_company_types=["科技公司", "金融企业"],
        recommend_settlement_range=(0.5, 0.75),
    ),
    "non_compete_breach": DisputeScenario(
        code="non_compete_breach",
        name="竞业限制违约争议（员工违反竞业限制）",
        category="竞业限制",
        law_basis=["《劳动合同法》第23条第二款", "《劳动合同法》第90条"],
        risk_legal=65, risk_economic=70, risk_reputation=40,
        compensation_formula="返还竞业限制补偿 + 违约金（按约定）",
        evidence_checklist=["竞业限制协议", "违约证据（入职竞对公司/自营竞争业务）", "竞业限制补偿支付记录"],
        typical_arbitration_win_rate=0.60,  # 企业告员工的胜诉率
        common_defenses=["违约金约定过高（违约金调整）+ 约定范围过宽无效"],
        defense_success_rate=0.40,  # 从劳动者角度
        statute_of_limitation=12,
        high_risk_industries=["互联网/科技", "游戏", "芯片/半导体"],
        high_risk_cities=["北京", "上海", "深圳"],
        high_risk_positions=["核心研发", "高管", "算法工程师"],
        high_risk_company_types=["科技公司", "AI企业"],
        recommend_settlement_range=(0.4, 0.7),
    ),
    "trade_secret_leak": DisputeScenario(
        code="trade_secret_leak",
        name="商业秘密泄露/侵犯商业秘密",
        category="竞业限制",
        law_basis=["《反不正当竞争法》第9-10条", "《劳动合同法》第23条"],
        risk_legal=82, risk_economic=90, risk_reputation=65,
        compensation_formula="实际损失或侵权获利 + 合理开支（律师费/调查费）；情节严重可1-5倍惩罚性赔偿",
        evidence_checklist=["保密制度文件", "保密协议", "泄密证据", "损失计算证明", "商业秘密认定证明"],
        typical_arbitration_win_rate=0.62,
        common_defenses=["信息非商业秘密", "劳动者通过合法途径获得", "未造成实际损失"],
        defense_success_rate=0.38,
        statute_of_limitation=12,
        high_risk_industries=["互联网/科技", "医药", "制造业（配方/工艺）"],
        high_risk_cities=["北京", "上海", "深圳"],
        high_risk_positions=["核心研发", "高管", "销售（客户名单）", "技术负责人"],
        high_risk_company_types=["高科技企业", "研发密集型企业"],
        recommend_settlement_range=(0.45, 0.75),
    ),

    # ========== 其他争议类 (3) ==========
    "discrimination": DisputeScenario(
        code="discrimination",
        name="就业歧视争议（性别/年龄/户籍/地域/疾病/婚育等）",
        category="其他",
        law_basis=["《就业促进法》第3条", "《劳动法》第12条", "《妇女权益保障法》", "《个人信息保护法》"],
        risk_legal=78, risk_economic=45, risk_reputation=85,
        compensation_formula="精神损害赔偿（酌定）+ 工资损失 + 可能的行政处罚",
        evidence_checklist=["招聘广告/面试记录", "录用条件", "拒绝录用的理由说明", "相关沟通记录"],
        typical_arbitration_win_rate=0.56,
        common_defenses=["岗位特殊要求（BFOQ）", "候选人综合评估不达标", "不存在歧视"],
        defense_success_rate=0.44,
        statute_of_limitation=12,
        high_risk_industries=["全行业（特别互联网/金融/服务）"],
        high_risk_cities=["北京", "上海", "深圳"],
        high_risk_positions=["全岗位（特别：女性求职者、40+求职者）"],
        high_risk_company_types=["全类型"],
        recommend_settlement_range=(0.3, 0.5),
    ),
    "harassment": DisputeScenario(
        code="harassment",
        name="职场性骚扰/职场霸凌",
        category="其他",
        law_basis=["《民法典》第1010条", "《妇女权益保障法》", "《劳动合同法》第38条"],
        risk_legal=85, risk_economic=60, risk_reputation=92,
        compensation_formula="精神损害赔偿 + 被迫解除补偿N + 可能的行政处罚 + 声誉损失（难以量化但影响重大）",
        evidence_checklist=["骚扰/霸凌证据（聊天记录/录音/邮件）", "投诉记录", "企业处理记录", "医疗记录"],
        typical_arbitration_win_rate=0.58,  # 证据难获取影响胜诉率
        common_defenses=["不存在骚扰/霸凌", "已采取合理措施/建立制度", "劳动者存在误解"],
        defense_success_rate=0.42,
        statute_of_limitation=12,  # 或适用民法典一般时效3年
        high_risk_industries=["全行业（特别：娱乐/媒体/互联网/金融）"],
        high_risk_cities=["北京", "上海"],
        high_risk_positions=["女性员工", "年轻员工", "基层员工"],
        high_risk_company_types=["层级森严的传统企业", "管理不规范的创业公司"],
        recommend_settlement_range=(0.5, 0.8),
    ),
    "hr_self_dispute": DisputeScenario(
        code="hr_self_dispute",
        name="HR/人事负责人自身劳动争议（未签合同/未缴社保等）",
        category="其他",
        law_basis=["《劳动合同法》第82条（HR的特殊适用讨论）"],
        risk_legal=70, risk_economic=50, risk_reputation=62,
        compensation_formula="存在争议：部分法院认为HR作为签订合同的负责人不能主张二倍工资；但未缴社保/未付加班费等主张不受影响",
        evidence_checklist=["劳动合同/无合同证明", "岗位职责说明", "HR相关规章制度", "工资及社保记录"],
        typical_arbitration_win_rate=0.45,  # 未签合同部分胜诉率低
        common_defenses=["劳动者系HR负责人负有签约职责", "劳动者本人怠于履行", "企业已尽合理义务"],
        defense_success_rate=0.55,
        statute_of_limitation=12,
        high_risk_industries=["全行业"],
        high_risk_cities=["全国通用"],
        high_risk_positions=["HR专员/HRM/HRD"],
        high_risk_company_types=["中小企业"],
        recommend_settlement_range=(0.3, 0.55),
    ),
}

# ============================================================================
#  城市/行业/公司类型/岗位调节因子
# ============================================================================

# 城市等级系数（综合仲裁倾向、社平工资、判例密度）
CITY_FACTORS = {
    "北京": 1.15, "上海": 1.15, "深圳": 1.20, "广州": 1.08,
    "杭州": 1.10, "成都": 1.02, "南京": 1.03, "武汉": 1.0,
    "重庆": 0.95, "天津": 1.0, "苏州": 1.05, "西安": 0.98,
    "长沙": 0.95, "郑州": 0.93, "东莞": 1.0, "青岛": 0.97,
    "合肥": 0.95, "厦门": 1.02, "济南": 0.95, "大连": 0.98,
    "福州": 0.95, "宁波": 1.0, "无锡": 1.0, "珠海": 1.02,
    "昆明": 0.92, "南昌": 0.92, "贵阳": 0.90, "太原": 0.90,
    "石家庄": 0.92, "哈尔滨": 0.90, "长春": 0.90, "沈阳": 0.93,
    "三亚": 0.90, "海口": 0.92, "乌鲁木齐": 0.88, "拉萨": 0.85,
    "其他": 0.95,
}
# 默认城市因子
DEFAULT_CITY_FACTOR = 0.95

# 行业调节因子（综合考虑劳动争议密度与判例倾向）
INDUSTRY_FACTORS = {
    "互联网/科技": 1.10, "金融": 1.08, "房地产": 1.05, "制造业": 0.98,
    "建筑": 1.02, "零售": 0.95, "餐饮": 0.92, "物流": 0.95,
    "教育培训": 1.0, "医疗": 0.98, "医药": 1.0, "咨询服务": 0.97,
    "媒体/娱乐": 0.95, "能源": 0.95, "汽车": 1.0, "游戏": 1.05,
    "保险": 1.0, "银行": 0.98, "物业服务": 0.90, "安保": 0.90,
    "旅游": 0.90, "农业": 0.85, "其他": 0.95,
}
DEFAULT_INDUSTRY_FACTOR = 0.95

# 公司类型调节因子
COMPANY_TYPE_FACTORS = {
    "民营企业": 1.12, "外资企业": 1.05, "国有企业": 0.92,
    "合资企业": 1.0, "小微企业": 1.08, "个体工商户": 1.15,
    "创业公司": 1.10, "上市公司": 1.08, "其他": 1.0,
}
DEFAULT_COMPANY_TYPE_FACTOR = 1.0

# 岗位类型调节因子
POSITION_FACTORS = {
    "技术研发": 1.02, "产品": 1.0, "设计": 0.98, "运营": 0.97,
    "销售": 0.95, "市场": 0.96, "客户服务": 0.95, "行政管理": 0.93,
    "人力资源": 1.05, "财务": 0.98, "法务": 1.10, "采购": 0.96,
    "中层管理": 1.08, "高管": 1.15, "一线工人": 0.95, "实习生": 0.90,
    "其他": 1.0,
}
DEFAULT_POSITION_FACTOR = 1.0


# ============================================================================
#  同类判例库（预置参考案例）
# ============================================================================

CASE_REFERENCES: Dict[str, List[CaseReference]] = {
    "no_contract": [
        CaseReference("C-001", "某互联网公司未与运营专员签合同6个月，仲裁裁决二倍工资差额5个月计6万元", "劳动者胜诉", 60000, "未签合同事实清楚", "北京", "互联网"),
        CaseReference("C-002", "某建筑公司未与工地工人签合同，工人工作11个月后离职，仲裁裁决二倍工资11个月", "劳动者胜诉", 99000, "建筑行业高发", "东莞", "建筑"),
    ],
    "overtime_pay": [
        CaseReference("C-010", "某互联网公司程序员主张2年996加班费45万元，法院部分支持（1.5年加班费，约28万）", "劳动者部分胜诉", 280000, "加班事实证据+公司加班文化", "北京", "互联网"),
        CaseReference("C-011", "某金融公司投资经理主张周末加班费，因无法证明加班事实被驳回", "企业胜诉", 0, "证据不足", "上海", "金融"),
    ],
    "wrongful_dismissal": [
        CaseReference("C-020", "某电商公司以不胜任为由辞退运营总监工作8年，法院认定不胜任举证不足，裁决2N=48万", "劳动者胜诉", 480000, "不胜任举证标准高", "杭州", "互联网"),
        CaseReference("C-021", "某制造企业以严重违纪辞退销售经理(10年)，企业举证充分，法院维持", "企业胜诉", 0, "违纪证据充分且经民主程序", "苏州", "制造业"),
    ],
    "maternity_dismissal": [
        CaseReference("C-030", "某金融公司在员工产假期间以组织架构调整为由裁员，法院裁决违法解除2N + 产假待遇损失", "劳动者胜诉", 320000, "三期保护绝对优先", "上海", "金融"),
    ],
    "wage_arrears": [
        CaseReference("C-040", "某建筑包工头拖欠12名工人工资合计28万元，仲裁裁决全额支付+50%加付赔偿金", "劳动者胜诉", 420000, "欠薪证据完整", "重庆", "建筑"),
    ],
}


# ============================================================================
#  核心计算函数
# ============================================================================

def get_scenario(code: str) -> Optional[DisputeScenario]:
    """按代码获取争议场景"""
    return DISPUTE_SCENARIOS.get(code)


def search_scenario(query: str) -> List[DisputeScenario]:
    """按关键词搜索争议场景"""
    ql = query.lower()
    results = []
    for code, sc in DISPUTE_SCENARIOS.items():
        score = 0
        if ql in sc.name:
            score += 3
        if ql in sc.category:
            score += 2
        if ql in " ".join(sc.high_risk_industries):
            score += 1
        if ql in " ".join(sc.high_risk_positions):
            score += 1
        if score > 0:
            results.append((score, sc))
    results.sort(key=lambda x: x[0], reverse=True)
    return [r[1] for r in results]


def get_adjustment_factors(city: str, industry: str, company_type: str, position: str) -> AdjustmentFactors:
    """获取四维调节因子"""
    return AdjustmentFactors(
        city_factor=CITY_FACTORS.get(city, DEFAULT_CITY_FACTOR),
        industry_factor=INDUSTRY_FACTORS.get(industry, DEFAULT_INDUSTRY_FACTOR),
        company_type_factor=COMPANY_TYPE_FACTORS.get(company_type, DEFAULT_COMPANY_TYPE_FACTOR),
        position_factor=POSITION_FACTORS.get(position, DEFAULT_POSITION_FACTOR),
    )


def compute_adjusted_risk(
    scenario: DisputeScenario,
    factors: AdjustmentFactors,
) -> Tuple[float, float, float, float, str]:
    """计算调整后的三维风险分和综合分

    综合分 = (法律分×0.5 + 经济分×0.3 + 声誉分×0.2)
              × 四维调节因子的加权乘积
    """
    adj_legal = min(100, round(scenario.risk_legal * max(factors.city_factor, factors.industry_factor), 1))
    adj_economic = min(100, round(scenario.risk_economic * max(factors.city_factor, factors.position_factor), 1))
    adj_reputation = min(100, round(scenario.risk_reputation * max(factors.industry_factor, factors.company_type_factor), 1))

    # 综合分
    composite_raw = adj_legal * 0.5 + adj_economic * 0.3 + adj_reputation * 0.2
    # 四维调节（几何平均）
    geo_factor = (factors.city_factor * factors.industry_factor * factors.company_type_factor * factors.position_factor) ** 0.25
    composite = min(100, round(composite_raw * geo_factor, 1))

    # 风险等级
    if composite >= 80:
        level = "极高"
    elif composite >= 65:
        level = "高"
    elif composite >= 45:
        level = "中"
    else:
        level = "低"

    return adj_legal, adj_economic, adj_reputation, composite, level


def compute_compensation(
    scenario: DisputeScenario,
    monthly_salary: float,
    months_of_service: int,
    end_date: Optional[str] = None,
) -> List[CompensationResult]:
    """预计算赔偿金额"""
    results = []

    # 根据场景计算不同赔偿项
    if scenario.code in ("no_contract",):
        # 二倍工资差额
        claimable_months = min(months_of_service - 1, 11)
        amount = monthly_salary * claimable_months
        results.append(CompensationResult(
            item="未签劳动合同二倍工资差额",
            amount=amount,
            formula=f"月工资 {monthly_salary:,.0f} × {claimable_months} 个月",
            legal_basis="《劳动合同法》第82条",
            notes=f"应签未签起第2个月至第{min(months_of_service,12)}个月，共{claimable_months}个月"
        ))

    elif scenario.code in ("contract_not_renewed", "severance_calculation"):
        years = months_of_service / 12
        if years - int(years) >= 0.5:
            n = int(years) + 1
        else:
            n = max(1, int(years) + 0.5)
        amount = monthly_salary * n
        results.append(CompensationResult(
            item="经济补偿金 N",
            amount=amount,
            formula=f"{n} 个月 × 月平均工资 {monthly_salary:,.0f}",
            legal_basis="《劳动合同法》第47条",
            notes=f"工作年限：{months_of_service}个月 → 折算 {n} 个月"
        ))

    elif scenario.code == "wrongful_dismissal":
        years = months_of_service / 12
        n = max(1, math.ceil(years * 2) / 2)  # 半年以上算1
        if years - int(years) >= 0.5:
            n_val = int(years) + 1
        else:
            n_val = max(1, int(years) + 0.5)
        amount = monthly_salary * n_val * 2
        results.append(CompensationResult(
            item="违法解除赔偿金 2N",
            amount=amount,
            formula=f"2 × {n_val}个月 × 月工资 {monthly_salary:,.0f}",
            legal_basis="《劳动合同法》第87条",
            notes=f"如月工资超当地3倍社平，基数封顶为3倍社平且年限封顶12年"
        ))

    elif scenario.code == "economic_dismissal":
        years = months_of_service / 12
        if years - int(years) >= 0.5:
            n = int(years) + 1
        else:
            n = max(1, int(years) + 0.5)
        amount_eco = monthly_salary * n
        amount_wrongful = monthly_salary * n * 2
        results.append(CompensationResult(
            item="经济性裁员补偿 N（程序合法时）",
            amount=amount_eco,
            formula=f"{n}个月 × 月工资 {monthly_salary:,.0f}",
            legal_basis="《劳动合同法》第41条、第47条",
            notes="如程序违法，可主张2N"
        ))
        results.append(CompensationResult(
            item="如程序违法→赔偿金 2N",
            amount=amount_wrongful,
            formula=f"2 × {n}个月 × 月工资 {monthly_salary:,.0f}",
            legal_basis="《劳动合同法》第87条",
            notes="取决于程序是否符合第41条要求"
        ))

    elif scenario.code == "maternity_dismissal":
        years = months_of_service / 12
        if years - int(years) >= 0.5:
            n = int(years) + 1
        else:
            n = max(1, int(years) + 0.5)
        amount_2n = monthly_salary * n * 2
        amount_recovery = monthly_salary * 6  # 孕期+产期+哺乳期估算
        results.append(CompensationResult(
            item="违法解除赔偿金 2N",
            amount=amount_2n,
            formula=f"2 × {n}个月 × 月工资 {monthly_salary:,.0f}",
            legal_basis="《劳动合同法》第87条",
            notes="三期女职工受绝对保护"
        ))
        results.append(CompensationResult(
            item="三期期间工资损失（估算）",
            amount=amount_recovery,
            formula=f"月工资 {monthly_salary:,.0f} × 约6个月",
            legal_basis="《女职工劳动保护特别规定》",
            notes="产假+哺乳期内工资应照发"
        ))

    elif scenario.code == "overtime_pay":
        # 假设平均每月加班40小时（20h工作日+20h休息日）
        est_months = min(months_of_service, 24)  # 追溯2年
        hourly = monthly_salary / 21.75 / 8
        workday_ot_per_month = 20 * 1.5 * hourly
        weekend_ot_per_month = 20 * 2 * hourly
        monthly_ot = workday_ot_per_month + weekend_ot_per_month
        amount = monthly_ot * est_months
        results.append(CompensationResult(
            item="加班费差额（月均40h加班估算）",
            amount=round(amount, 0),
            formula=f"时薪 {hourly:,.1f} × (工作日加班1.5倍 × 20h + 休息日加班2倍 × 20h) × {est_months}个月",
            legal_basis="《劳动法》第44条",
            notes="实际金额取决于具体加班时长和举证情况，此为估算"
        ))

    elif scenario.code == "annual_leave_dispute":
        # 按法律规定每年最低5天年假，未休按300%补偿
        years = max(1, months_of_service / 12)
        annual_leave_days = min(15, max(5, int(years) + 5))  # 简化版
        daily = monthly_salary / 21.75
        unpaid_years = min(int(years), 2)  # 追溯2年
        amount = daily * 2 * annual_leave_days * unpaid_years  # 300%-100%已发
        results.append(CompensationResult(
            item="未休年假折算（300%）",
            amount=round(amount, 0),
            formula=f"日工资 {daily:,.0f} × 200% × {annual_leave_days}天 × {unpaid_years}年",
            legal_basis="《职工带薪年休假条例》第5条",
            notes="300%含正常工资100%，另计200%未休补偿；追溯2年"
        ))

    elif scenario.code == "forced_resignation":
        years = months_of_service / 12
        if years - int(years) >= 0.5:
            n = int(years) + 1
        else:
            n = max(1, int(years) + 0.5)
        amount = monthly_salary * n
        results.append(CompensationResult(
            item="被迫解除经济补偿 N",
            amount=amount,
            formula=f"{n}个月 × 月工资 {monthly_salary:,.0f}",
            legal_basis="《劳动合同法》第38条、第46条",
            notes="如能证明被变相逼迫，可进一步主张2N"
        ))

    elif scenario.code == "work_injury_dispute":
        # 工伤赔偿复杂，给出范围
        min_est = monthly_salary * 7  # 最低七级伤残
        max_est = monthly_salary * 27  # 一级伤残
        results.append(CompensationResult(
            item="工伤保险待遇（估算范围）",
            amount=round((min_est + max_est) / 2, 0),
            formula=f"估算范围 ¥{min_est:,.0f} ~ ¥{max_est:,.0f}",
            legal_basis="《工伤保险条例》第33-45条",
            notes="实际金额取决于伤残等级（需劳动能力鉴定），此为参考范围"
        ))

    elif scenario.code == "social_insurance_underpayment":
        # 社保补缴差额 + 可能的罚款
        est_rate = 0.30  # 企业和个人合计约30%
        est_months = min(months_of_service, 60)  # 追溯5年常见
        diff_rate = 0.10  # 假设差额比例
        amount = monthly_salary * est_rate * diff_rate * est_months
        results.append(CompensationResult(
            item="社保补缴差额（企业+个人，估算）",
            amount=round(amount, 0),
            formula=f"月工资 {monthly_salary:,.0f} × 约10%差额率 × {est_months}个月",
            legal_basis="《社会保险法》第86条",
            notes="实际金额需以社保机构核定为准；滞纳金另计（日万分之五）"
        ))

    # 默认追加一个通用项
    if not results:
        results.append(CompensationResult(
            item="法定赔偿/补偿",
            amount=monthly_salary * max(1, months_of_service / 12),
            formula=f"由具体案情确定（参考：月工资 × 工作年限）",
            legal_basis="《劳动合同法》相关条款",
            notes="本项为粗略估算，实际需结合具体争议事实计算"
        ))

    return results


def find_similar_cases(scenario_code: str, city: str, industry: str) -> List[Dict[str, Any]]:
    """查找同类判例"""
    cases = CASE_REFERENCES.get(scenario_code, [])
    result = []
    for c in cases:
        relevance = 0
        if c.city == city: relevance += 2
        if c.industry == industry: relevance += 2
        relevance += 1  # base
        result.append({**asdict(c), "relevance": relevance})
    result.sort(key=lambda x: x["relevance"], reverse=True)
    return result


def assess_risk(
    scenario_code: str,
    monthly_salary: float,
    months_of_service: int,
    city: str = "其他",
    industry: str = "其他",
    company_type: str = "民营企业",
    position: str = "其他",
) -> RiskAssessmentResult:
    """完整风险评估主函数"""
    scenario = DISPUTE_SCENARIOS.get(scenario_code)
    if not scenario:
        raise ValueError(f"未找到争议场景: {scenario_code}")

    factors = get_adjustment_factors(city, industry, company_type, position)
    adj_legal, adj_economic, adj_reputation, composite, level = compute_adjusted_risk(scenario, factors)

    # 赔偿计算
    comp_items = compute_compensation(scenario, monthly_salary, months_of_service)
    estimated_compensation = sum(c.amount for c in comp_items)
    comp_range = (
        estimated_compensation * scenario.recommend_settlement_range[0],
        estimated_compensation * scenario.recommend_settlement_range[1],
    )
    recommended_settlement = estimated_compensation * (scenario.recommend_settlement_range[0] + scenario.recommend_settlement_range[1]) / 2

    # 判例
    cases = find_similar_cases(scenario_code, city, industry)

    # 行动建议
    recommend_immediate = []
    recommend_short_term = []
    recommend_long_term = []

    # 紧急措施（极高/高风险）
    if composite >= 65:
        recommend_immediate.append(f"立即收集并保全 {', '.join(scenario.evidence_checklist[:4])}")
        recommend_immediate.append(f"咨询专业劳动法律师，评估本案抗辩空间（典型抗辩成功率约 {scenario.defense_success_rate*100:.0f}%）")
        if scenario.recommend_settlement_range[0] > 0.5:
            recommend_immediate.append(f"优先考虑和解：建议和解金额区间 ¥{comp_range[0]:,.0f} ~ ¥{comp_range[1]:,.0f}")

    if composite >= 80:
        recommend_immediate.append("⚠️ 极高风险！建议法务/律师立即介入，准备应急预案")
        recommend_immediate.append("评估是否涉及群体性风险或舆情风险，准备PR预案")

    # 短期措施
    recommend_short_term.append(f"对照 {', '.join(scenario.law_basis[:2])} 梳理本企业合规现状")
    if "规章制度" in str(scenario.evidence_checklist):
        recommend_short_term.append("完善民主程序：规章制度需经职代会/全体员工讨论+公示告知")
    recommend_short_term.append("建立劳动争议预警机制：定期排查合同到期日/社保缴纳/加班管理等高风险节点")

    # 长期措施
    recommend_long_term.append("建立完整的劳动用工合规体系（合同管理+薪酬管理+社保管理+解除流程）")
    if scenario.code in ("overtime_pay", "rest_day_overtime"):
        recommend_long_term.append("规范加班审批制度，推行综合计算工时制（如适用）")
    if scenario.code in ("no_contract",):
        recommend_long_term.append("建立新员工入职合同签署SOP：入职当日必须签署，HR系统自动提醒")
    if scenario.code.startswith("social"):
        recommend_long_term.append("年度社保审计：委托第三方核查全体员工社保缴存基数合规性")

    urgent = composite >= 80 or (composite >= 65 and scenario.typical_arbitration_win_rate >= 0.85)

    return RiskAssessmentResult(
        scenario_code=scenario_code,
        scenario_name=scenario.name,
        category=scenario.category,
        risk_legal=adj_legal,
        risk_economic=adj_economic,
        risk_reputation=adj_reputation,
        risk_composite=composite,
        risk_level=level,
        adjustments={
            "city": {"value": city, "factor": factors.city_factor, "reason": "城市仲裁倾向与判例密度"},
            "industry": {"value": industry, "factor": factors.industry_factor, "reason": "行业劳动争议密度与裁审倾向"},
            "company_type": {"value": company_type, "factor": factors.company_type_factor, "reason": "企业类型对争议发生率和判赔率的影响"},
            "position": {"value": position, "factor": factors.position_factor, "reason": "岗位类型对争议复杂度和赔偿的影响"},
        },
        estimated_compensation=round(estimated_compensation, 0),
        compensation_range=(round(comp_range[0], 0), round(comp_range[1], 0)),
        compensation_items=[{
            "item": c.item, "amount": c.amount, "formula": c.formula,
            "legal_basis": c.legal_basis, "notes": c.notes,
        } for c in comp_items],
        recommended_settlement=round(recommended_settlement, 0),
        law_basis=scenario.law_basis,
        evidence_checklist=scenario.evidence_checklist,
        common_defenses=scenario.common_defenses,
        defense_success_rate=scenario.defense_success_rate,
        similar_cases=cases,
        statute_of_limitation_months=scenario.statute_of_limitation,
        urgent_warning=urgent,
        recommend_immediate=recommend_immediate,
        recommend_short_term=recommend_short_term,
        recommend_long_term=recommend_long_term,
        assessment_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        confidence="中" if not cases else "高",
    )


# ============================================================================
#  格式化输出
# ============================================================================

def format_report(result: RiskAssessmentResult) -> str:
    """生成文本报告"""
    bar = "─" * 60
    lines = [
        "",
        "╔" + "═" * 58 + "╗",
        f"║  蚂蚁工资条 · 劳动争议风险评估报告{'':>22}║",
        "╚" + "═" * 58 + "╝",
        "",
        f"  📋 争议场景：{result.scenario_name}",
        f"  🏷️  类别：{result.category}",
        f"  📅 评估时间：{result.assessment_time}",
        f"  🎯 置信度：{result.confidence}",
        "",
        "  " + bar,
        "  📊 三维风险评分",
        "  " + bar,
        f"  法律合规风险：{result.risk_legal:>5.1f} / 100  {'█' * int(result.risk_legal // 2)}",
        f"  经济损失风险：{result.risk_economic:>5.1f} / 100  {'█' * int(result.risk_economic // 2)}",
        f"  声誉影响风险：{result.risk_reputation:>5.1f} / 100  {'█' * int(result.risk_reputation // 2)}",
        f"  {'─' * 40}",
        f"  综合风险评分：{result.risk_composite:>5.1f} / 100  📛 {result.risk_level}风险",
        "",
        "  " + bar,
        "  📐 四维调节因子",
        "  " + bar,
    ]
    for dim, data in result.adjustments.items():
        label = {"city": "城市", "industry": "行业", "company_type": "公司类型", "position": "岗位"}[dim]
        lines.append(f"  {label}: {data['value']} (× {data['factor']:.2f}) — {data['reason']}")

    lines += [
        "",
        "  " + bar,
        "  💰 赔偿预计算",
        "  " + bar,
    ]
    for item in result.compensation_items:
        lines.append(f"  ◈ {item['item']}")
        lines.append(f"    金额: ¥{item['amount']:,.0f}")
        lines.append(f"    算式: {item['formula']}")
        lines.append(f"    依据: {item['legal_basis']}")
        if item['notes']:
            lines.append(f"    说明: {item['notes']}")
        lines.append("")

    lines += [
        f"  {'─' * 40}",
        f"  预估赔偿合计：¥{result.estimated_compensation:,.0f}",
        f"  和解金额区间：¥{result.compensation_range[0]:,.0f} ~ ¥{result.compensation_range[1]:,.0f}",
        f"  建议和解金额：¥{result.recommended_settlement:,.0f}",
        "",
        "  " + bar,
        "  ⚖️  同类判例参考",
        "  " + bar,
    ]
    for i, case in enumerate(result.similar_cases, 1):
        lines += [
            f"  [{i}] {case['case_summary'][:80]}",
            f"      结果: {case['outcome']} | 赔偿: ¥{case['compensation_awarded']:,.0f}",
            f"      城市: {case['city']} | 行业: {case['industry']}",
        ]
        if i >= 3:
            break

    lines += [
        "",
        "  " + bar,
        "  📝 法律依据",
        "  " + bar,
    ]
    for law in result.law_basis:
        lines.append(f"  • {law}")

    lines += [
        "",
        "  " + bar,
        "  🔍 企业证据清单（必须准备）",
        "  " + bar,
    ]
    for ev in result.evidence_checklist:
        lines.append(f"  ☐ {ev}")

    lines += [
        "",
        "  " + bar,
        "  🛡️  企业常见抗辩（成功率 {:.0f}%）".format(result.defense_success_rate * 100),
        "  " + bar,
    ]
    for df in result.common_defenses:
        lines.append(f"  • {df}")

    lines += [
        "",
        "  " + bar,
        "  ⏰ 时效提示",
        "  " + bar,
    ]
    if result.statute_of_limitation_months == 0:
        lines.append("  无仲裁时效限制（社保类争议可追溯全部历史，不受1年时效约束）")
    else:
        lines.append(f"  劳动仲裁申请时效：{result.statute_of_limitation_months} 个月（自知道或应当知道权利被侵害之日起）")
        lines.append(f"  如已超过时效且无中断/中止情形，企业可据此抗辩。")

    lines += [
        "",
        "  " + bar,
        "  🚨 行动建议",
        "  " + bar,
    ]

    if result.urgent_warning:
        lines.append("  ⚠️ 紧急警告：当前情况需要立即采取行动！")

    if result.recommend_immediate:
        lines.append("")
        lines.append("  【立即执行】")
        for i, r in enumerate(result.recommend_immediate, 1):
            lines.append(f"  {i}. {r}")

    if result.recommend_short_term:
        lines.append("")
        lines.append("  【短期（1个月内）】")
        for i, r in enumerate(result.recommend_short_term, 1):
            lines.append(f"  {i}. {r}")

    if result.recommend_long_term:
        lines.append("")
        lines.append("  【长期（制度性建设）】")
        for i, r in enumerate(result.recommend_long_term, 1):
            lines.append(f"  {i}. {r}")

    lines += [
        "",
        "  " + bar,
        "  ⚠️ 免责声明",
        "  " + bar,
        "  本评估基于《劳动合同法》《劳动争议调解仲裁法》等",
        "  现行法律法规及典型判例，综合城市/行业/公司类型/",
        "  岗位四维调节因子生成。评分仅供决策参考，不构成",
        "  法律意见。建议结合具体案情咨询专业劳动法律师。",
        "",
    ]
    return "\n".join(lines)


def format_json(result: RiskAssessmentResult) -> str:
    """生成JSON格式输出"""
    data = {
        "assessment_time": result.assessment_time,
        "scenario_code": result.scenario_code,
        "scenario_name": result.scenario_name,
        "category": result.category,
        "risk_scores": {
            "legal_compliance": result.risk_legal,
            "economic_loss": result.risk_economic,
            "reputation_impact": result.risk_reputation,
            "composite": result.risk_composite,
            "level": result.risk_level,
        },
        "adjustments": result.adjustments,
        "compensation": {
            "estimated_total": result.estimated_compensation,
            "settlement_range": list(result.compensation_range),
            "recommended_settlement": result.recommended_settlement,
            "items": result.compensation_items,
        },
        "legal_info": {
            "law_basis": result.law_basis,
            "evidence_checklist": result.evidence_checklist,
            "common_defenses": result.common_defenses,
            "defense_success_rate": result.defense_success_rate,
            "statute_of_limitation_months": result.statute_of_limitation_months,
        },
        "similar_cases": result.similar_cases,
        "urgent_warning": result.urgent_warning,
        "recommendations": {
            "immediate": result.recommend_immediate,
            "short_term": result.recommend_short_term,
            "long_term": result.recommend_long_term,
        },
        "confidence": result.confidence,
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


# ============================================================================
#  CLI入口 + Demo
# ============================================================================

def list_all_scenarios():
    """列出所有场景"""
    for code, sc in sorted(DISPUTE_SCENARIOS.items()):
        print(f"  [{code}] {sc.name}")


def run_demo():
    """运行演示用例"""
    print("=" * 65)
    print("  蚂蚁工资条 · 劳动争议风险评估引擎 — 演示")
    print("=" * 65)

    demos = [
        ("wrongful_dismissal", "违法解除劳动合同", 25000, 36, "深圳", "互联网", "民营企业", "技术研发"),
        ("no_contract", "未签劳动合同", 8000, 8, "成都", "餐饮", "个体工商户", "服务员"),
        ("overtime_pay", "加班费争议", 18000, 24, "北京", "互联网", "创业公司", "技术研发"),
        ("maternity_dismissal", "三期女职工解雇", 15000, 42, "上海", "金融", "民营企业", "中层管理"),
        ("wage_arrears", "拖欠工资", 6000, 12, "重庆", "建筑", "小微企业", "一线工人"),
    ]

    for i, (code, name, salary, mths, city, ind, ctype, pos) in enumerate(demos, 1):
        print(f"\n{'─' * 65}")
        print(f"  演示 [{i}/{len(demos)}] {name}")
        print(f"  参数：月薪 ¥{salary:,} | 工龄 {mths}月 | {city} | {ind} | {ctype} | {pos}")
        print(f"{'─' * 65}")

        result = assess_risk(code, salary, mths, city, ind, ctype, pos)
        report = format_report(result)
        print(report)

    print(f"\n{'=' * 65}")
    print(f"  所有演示用例运行完毕 ✅")
    print(f"  共覆盖 {len(DISPUTE_SCENARIOS)} 种争议场景")
    print(f"{'=' * 65}")


def run_demo_json():
    """演示JSON输出"""
    result = assess_risk("wrongful_dismissal", 25000, 36, "深圳", "互联网", "民营企业", "技术研发")
    print(format_json(result))


# ============================================================================
#  main
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="蚂蚁工资条 · 劳动争议风险评估引擎")
    parser.add_argument("--scenario", help="争议场景代码（如: no_contract, wrongful_dismissal）")
    parser.add_argument("--monthly", type=float, default=10000, help="月平均工资（元）")
    parser.add_argument("--months", type=int, default=12, help="工作月数/工龄")
    parser.add_argument("--city", default="其他", help="城市")
    parser.add_argument("--industry", default="其他", help="行业")
    parser.add_argument("--company-type", default="民营企业", help="公司类型")
    parser.add_argument("--position", default="其他", help="岗位")
    parser.add_argument("--json", action="store_true", help="JSON格式输出")
    parser.add_argument("--demo", action="store_true", help="运行演示")
    parser.add_argument("--list", action="store_true", help="列出所有争议场景")
    parser.add_argument("--search", help="按关键词搜索场景")

    args = parser.parse_args()

    if args.list:
        list_all_scenarios()
        sys.exit(0)

    if args.search:
        results = search_scenario(args.search)
        if results:
            print(f"搜索「{args.search}」匹配 {len(results)} 个场景：")
            for sc in results:
                print(f"  [{sc.code}] {sc.name} ({sc.category})")
        else:
            print(f"未找到匹配「{args.search}」的场景")
        sys.exit(0)

    if args.demo:
        run_demo()
        run_demo_json()
        sys.exit(0)

    if not args.scenario:
        print("错误: 请指定 --scenario 参数（或使用 --demo / --list / --search）")
        print("\n可用场景:")
        list_all_scenarios()
        sys.exit(1)

    # 单场景评估
    if args.scenario not in DISPUTE_SCENARIOS:
        results = search_scenario(args.scenario)
        if len(results) == 1:
            args.scenario = results[0].code
            print(f"自动匹配场景: {results[0].name}")
        elif results:
            print("模糊匹配到以下场景，请指定精确代码：")
            for sc in results:
                print(f"  [{sc.code}] {sc.name}")
            sys.exit(1)
        else:
            print(f"未找到场景: {args.scenario}")
            list_all_scenarios()
            sys.exit(1)

    result = assess_risk(
        args.scenario, args.monthly, args.months,
        args.city, args.industry, args.company_type, args.position,
    )

    if args.json:
        print(format_json(result))
    else:
        print(format_report(result))
