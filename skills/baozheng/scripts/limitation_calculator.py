"""
诉讼时效计算器 —— 基于 shared-limitation-periods.md 规范实现

覆盖：
- 民事/行政时效（民法典、各单行法）
- 刑事追诉时效（刑法第87/88/89条）
- 时效中断/延长/最长保护期
- 三级预警：紧急(<30天) / 紧迫(<90天) / 关注(<180天)

作者: 智慧半岛
日期: 2026-07-03
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum, auto
from typing import Optional


# ================================================================
# 枚举与类型
# ================================================================

class LimitationScope(Enum):
    CIVIL = auto()        # 民事
    ADMINISTRATIVE = auto()  # 行政
    CRIMINAL = auto()     # 刑事

class WarningLevel(Enum):
    EXPIRED = "expired"            # 已过期
    URGENT = "urgent"              # < 30 天
    IMMINENT = "imminent"          # < 90 天
    ATTENTION = "attention"        # < 180 天
    SAFE = "safe"                  # > 180 天


# ================================================================
# 时效规则数据类
# ================================================================

@dataclass(frozen=True)
class LimitationRule:
    """一条诉讼时效规则"""
    case_type: str               # 案由/纠纷类型
    scope: LimitationScope       # 民事/行政/刑事
    years: int                   # 时效年限
    law: str                     # 法律名称
    article: str                 # 条文
    description: str = ""        # 补充说明
    start_trigger: str = "知道或应当知道权利受损之日"  # 起算基准
    max_protection_years: int = 20  # 最长保护期（民事），刑事用 87 条分档
    # 刑事特有字段
    crime_category: str = ""     # 罪名分类
    max_penalty_range: str = ""  # 法定最高刑区间（用于刑法87条分档）

    @staticmethod
    def civil(
        case_type: str, years: int, law: str, article: str,
        description: str = "", start_trigger: str = "知道或应当知道权利受损之日",
        max_protection_years: int = 20,
    ) -> LimitationRule:
        return LimitationRule(
            case_type=case_type, scope=LimitationScope.CIVIL,
            years=years, law=law, article=article,
            description=description, start_trigger=start_trigger,
            max_protection_years=max_protection_years,
        )

    @staticmethod
    def admin(
        case_type: str, years: int, law: str, article: str,
        description: str = "", start_trigger: str = "知道或应当知道权利受损之日",
    ) -> LimitationRule:
        return LimitationRule(
            case_type=case_type, scope=LimitationScope.ADMINISTRATIVE,
            years=years, law=law, article=article,
            description=description, start_trigger=start_trigger,
        )

    @staticmethod
    def criminal(
        crime_category: str, max_penalty_range: str, years: int,
        law: str = "中华人民共和国刑法", article: str = "第87条",
        description: str = "",
    ) -> LimitationRule:
        return LimitationRule(
            case_type=crime_category, scope=LimitationScope.CRIMINAL,
            years=years, law=law, article=article,
            description=description,
            start_trigger="犯罪之日",
            crime_category=crime_category,
            max_penalty_range=max_penalty_range,
        )


# ================================================================
# 结果数据类
# ================================================================

@dataclass
class LimitationResult:
    """时效计算结果"""
    rule: LimitationRule                      # 匹配的时效规则

    incident_date: date                       # 事件/权利受损日期
    known_date: Optional[date] = None         # 知道/应当知道日期

    limitation_start: Optional[date] = None   # 时效起算日
    limitation_end: Optional[date] = None     # 时效届满日
    max_protection_end: Optional[date] = None # 最长保护期届满日（民事）

    remaining_days: Optional[int] = None       # 距届满剩余天数（None=已过期或无法计算）
    warning_level: WarningLevel = WarningLevel.SAFE

    expired: bool = False                     # 是否已过时效
    is_criminal: bool = False                 # 是否刑事追诉

    # 特殊状态
    is_extended: bool = False                 # 时效延长（逃避侦查等）
    is_interrupted: bool = False              # 时效中断（又犯新罪等）
    extension_reason: str = ""                # 延长/中断原因

    # 提示文本
    warning_text: str = ""                    # 用户可见预警
    legal_basis: str = ""                     # 法律依据引用
    disclaimer: str = (                       # 免责声明
        "以上时效计算结果仅供参考，具体以案件事实和司法机关认定为准。"
        "建议在时效届满前尽早采取法律行动。"
    )


# ================================================================
# 时效规则库（按 shared-limitation-periods.md 构建）
# ================================================================

# --- 民事时效 ---
CIVIL_RULES: list[LimitationRule] = [
    LimitationRule.civil("普通民事诉讼", 3, "中华人民共和国民法典", "第188条",
        "一般民事纠纷，如合同、侵权、债权债务"),
    LimitationRule.civil("人身损害赔偿", 3, "中华人民共和国民法典", "第188条",
        "包括医疗损害、交通事故、工伤等"),
    LimitationRule.civil("劳动争议仲裁", 1, "中华人民共和国劳动争议调解仲裁法", "第27条",
        start_trigger="知道或应当知道权利受损之日"),
    LimitationRule.civil("产品质量责任", 2, "中华人民共和国产品质量法", "第45条"),
    LimitationRule.civil("国家赔偿请求", 2, "中华人民共和国国家赔偿法", "第39条"),
    LimitationRule.civil("专利侵权", 2, "中华人民共和国专利法", "第74条",
        start_trigger="得知或应当得知权利受损之日"),
    LimitationRule.civil("商标侵权", 3, "中华人民共和国商标法", "第39条"),
    LimitationRule.civil("著作权侵权", 3, "中华人民共和国著作权法", "第10条"),
    LimitationRule.civil("保险理赔", 2, "中华人民共和国保险法", "第26条",
        start_trigger="知道或应当知道保险事故发生之日"),
    LimitationRule.civil("证券虚假陈述", 3, "中华人民共和国证券法", "第85条",
        start_trigger="知道或应当知道权益受损之日"),
    LimitationRule.civil("遗赠接受", 60, "中华人民共和国民法典", "第1124条",
        description="受遗赠人应在知道受遗赠后60日内作出接受表示，到期未表示视为放弃",
        start_trigger="知道受遗赠之日"),
]

# --- 行政时效 ---
ADMIN_RULES: list[LimitationRule] = [
    LimitationRule.admin("行政诉讼", 6, "中华人民共和国行政诉讼法", "第46条",
        start_trigger="知道或应当知道作出行政行为之日"),
    LimitationRule.admin("行政复议", 60, "中华人民共和国行政复议法", "第9条",
        start_trigger="知道该具体行政行为之日"),
]

# --- 刑事追诉时效（刑法第87条分档） ---
CRIMINAL_RULES: list[LimitationRule] = [
    LimitationRule.criminal("法定最高刑不满5年", "< 5年", 5, article="第87条第1项",
        description="如危险驾驶、小额盗窃、普通轻伤害等"),
    LimitationRule.criminal("法定最高刑5年以上不满10年", "5年≤~<10年", 10, article="第87条第2项",
        description="如数额较大诈骗、抢劫(非加重)、强奸(非加重)等"),
    LimitationRule.criminal("法定最高刑10年以上有期徒刑", "≥10年有期徒刑", 15, article="第87条第3项",
        description="如数额巨大诈骗、加重抢劫、故意伤害致死等"),
    LimitationRule.criminal("法定最高刑无期徒刑/死刑", "无期/死刑", 20, article="第87条第4项",
        description="如故意杀人、抢劫致人死亡等；20年后须报最高检核准"),
]

ALL_RULES: list[LimitationRule] = CIVIL_RULES + ADMIN_RULES + CRIMINAL_RULES

# 最长保护期（民法典第188条）
MAX_PROTECTION_YEARS = 20


# ================================================================
# 时效计算器
# ================================================================

class LimitationCalculator:
    """诉讼时效计算器

    用法:
        calc = LimitationCalculator()

        # 民事
        r = calc.civil("普通民事诉讼", date(2023, 5, 1))
        print(r.warning_text)  # "距时效届满还有 153 天"

        # 刑事
        r = calc.criminal("法定最高刑不满5年", date(2020, 1, 1))
        print(f"追诉时效届满: {r.limitation_end}")

        # 快捷函数
        r = calculate("普通民事诉讼", "2023-05-01")
    """

    def __init__(self, today: Optional[date] = None):
        """
        Args:
            today: 基准日期，默认为当日。用于测试注入。
        """
        self.today = today or date.today()

    # ---- 查找规则 ----

    def _find_rule(self, case_type: str, scope: LimitationScope) -> LimitationRule:
        """模糊匹配时效规则"""
        normalized = case_type.strip()
        pool = {
            LimitationScope.CIVIL: CIVIL_RULES,
            LimitationScope.ADMINISTRATIVE: ADMIN_RULES,
            LimitationScope.CRIMINAL: CRIMINAL_RULES,
        }.get(scope, [])

        # 精确匹配
        for rule in pool:
            if rule.case_type == normalized:
                return rule

        # 模糊匹配（关键词包含）
        keywords = [normalized, normalized.replace("诉讼", "").replace("纠纷", "").replace("责任", "")]
        for kw in keywords:
            if not kw:
                continue
            for rule in pool:
                if kw in rule.case_type or rule.case_type in kw:
                    return rule
                if rule.description and (kw in rule.description or rule.description in kw):
                    return rule

        raise ValueError(
            f"未找到匹配的时效规则：'{case_type}'。"
            f"可用类型：{', '.join(r.case_type for r in pool)}"
        )

    # ---- 主计算 ----

    def civil(
        self,
        case_type: str,
        incident_date: date | str,
        known_date: date | str | None = None,
        *,
        is_extended: bool = False,
        is_interrupted: bool = False,
        extension_reason: str = "",
    ) -> LimitationResult:
        """民事/行政时效计算

        Args:
            case_type:      案由/纠纷类型（模糊匹配）
            incident_date:  权利受损/事件发生日期
            known_date:     知道或应当知道日期（默认同 incident_date）
            is_extended:    是否适用时效延长
            is_interrupted: 是否发生时效中断
            extension_reason: 延长/中断原因

        Returns:
            LimitationResult
        """
        # 先民事，再行政
        try:
            rule = self._find_rule(case_type, LimitationScope.CIVIL)
            scope = LimitationScope.CIVIL
        except ValueError:
            rule = self._find_rule(case_type, LimitationScope.ADMINISTRATIVE)
            scope = LimitationScope.ADMINISTRATIVE

        incident = _parse_date(incident_date)
        known = _parse_date(known_date) if known_date else incident

        return self._compute(
            rule=rule,
            incident_date=incident,
            known_date=known,
            is_extended=is_extended,
            is_interrupted=is_interrupted,
            extension_reason=extension_reason,
        )

    def criminal(
        self,
        crime_category: str,
        crime_date: date | str,
        *,
        is_extended: bool = False,
        is_interrupted: bool = False,
        extension_reason: str = "",
        new_crime_date: date | str | None = None,
    ) -> LimitationResult:
        """刑事追诉时效计算

        Args:
            crime_category:  罪名分类（"法定最高刑不满5年" 等）
            crime_date:      犯罪行为发生日期
            is_extended:     逃避侦查/审判 → 不受追诉期限限制
            is_interrupted:  又犯新罪 → 从犯后罪之日起算
            extension_reason: 说明
            new_crime_date:  新罪发生日期（中断时用）

        Returns:
            LimitationResult
        """
        rule = self._find_rule(crime_category, LimitationScope.CRIMINAL)

        crime = _parse_date(crime_date)

        # 刑事时效中断：从犯后罪之日起重新计算
        if is_interrupted and new_crime_date:
            crime = _parse_date(new_crime_date)

        return self._compute(
            rule=rule,
            incident_date=crime,
            known_date=crime,
            is_extended=is_extended,
            is_interrupted=is_interrupted,
            extension_reason=extension_reason,
            is_criminal=True,
        )

    def _compute(
        self,
        rule: LimitationRule,
        incident_date: date,
        known_date: date,
        is_extended: bool = False,
        is_interrupted: bool = False,
        extension_reason: str = "",
        is_criminal: bool = False,
    ) -> LimitationResult:
        """核心计算逻辑"""

        # 起算日 = 知道/应当知道日期（或事件日）
        start = known_date

        # 民法特别：遗赠接受是60日，不是年
        if rule.years < 1:
            # 按月/日单位
            end_date = start + timedelta(days=rule.years)
        else:
            # 按年单位：加 years 年减 1 天（届满日为起算日 + N 年 - 1 天）
            # 注意：法律上时效届满日通常是"对应日"或"对应日前一日"
            end_date = _add_years(start, rule.years) - timedelta(days=1)

        # 最长保护期（仅民事）：自权利受损日起 20 年
        max_protection_end = None
        if not is_criminal:
            max_protection_end = _add_years(incident_date, rule.max_protection_years)

        # 剩余天数
        remaining = (end_date - self.today).days if end_date else None

        # 过期判定
        expired = False
        if remaining is not None and remaining < 0:
            expired = True
        # 最长保护期检查
        if max_protection_end and self.today > max_protection_end and not expired:
            expired = True

        # 预警级别
        if is_extended:
            # 时效延长/逃避侦查 → 不受限，不判断过期
            expired = False
            warning_level = WarningLevel.SAFE
        elif remaining is None:
            warning_level = WarningLevel.SAFE
        elif remaining < 0:
            warning_level = WarningLevel.EXPIRED
        elif remaining <= 30:
            warning_level = WarningLevel.URGENT
        elif remaining <= 90:
            warning_level = WarningLevel.IMMINENT
        elif remaining <= 180:
            warning_level = WarningLevel.ATTENTION
        else:
            warning_level = WarningLevel.SAFE

        # 提示文本
        warning_text = _build_warning(
            rule, remaining, warning_level, expired,
            is_extended, is_interrupted, extension_reason,
            end_date, max_protection_end, is_criminal,
        )

        # 法律依据
        legal_basis = f"{rule.law} {rule.article}"
        if rule.description:
            legal_basis += f"（{rule.description}）"

        return LimitationResult(
            rule=rule,
            incident_date=incident_date,
            known_date=known_date,
            limitation_start=start,
            limitation_end=end_date,
            max_protection_end=max_protection_end,
            remaining_days=remaining,
            warning_level=warning_level,
            expired=expired,
            is_criminal=is_criminal,
            is_extended=is_extended,
            is_interrupted=is_interrupted,
            extension_reason=extension_reason,
            warning_text=warning_text,
            legal_basis=legal_basis,
        )


def _parse_date(d: date | str) -> date:
    if isinstance(d, date):
        return d
    # 支持格式: 2023-05-01 / 2023.05.01 / 2023/05/01
    for sep in ("-", ".", "/"):
        try:
            parts = d.strip().split(sep)
            if len(parts) == 3:
                return date(int(parts[0]), int(parts[1]), int(parts[2]))
        except (ValueError, IndexError):
            continue
    raise ValueError(f"无法解析日期: '{d}'，支持的格式: YYYY-MM-DD / YYYY.MM.DD / YYYY/MM/DD")


def _add_years(d: date, years: int) -> date:
    """跨年加 N 年，处理 2 月 29 日边界"""
    try:
        return d.replace(year=d.year + years)
    except ValueError:
        # 闰年 2 月 29 → 次年 2 月 28
        return d.replace(year=d.year + years, day=28)


def _build_warning(
    rule: LimitationRule,
    remaining: Optional[int],
    level: WarningLevel,
    expired: bool,
    is_extended: bool,
    is_interrupted: bool,
    extension_reason: str,
    end_date: Optional[date],
    max_protection_end: Optional[date],
    is_criminal: bool,
) -> str:
    """构建用户可见预警文本"""

    label = "追诉时效" if is_criminal else "诉讼时效"

    if is_extended:
        return (
            f"⚠️ 时效延长：{extension_reason or '该情形下不受时效期限限制'}。"
            f"法律依据：{rule.law} {rule.article}。"
        )

    if is_interrupted:
        return (
            f"🔄 时效中断：{extension_reason or '因又犯新罪/中断事由重新计算'}。"
            f"法律依据：{rule.law} {rule.article}。"
        )

    if expired:
        extra = ""
        if max_protection_end and end_date < max_protection_end:
            extra = (
                f"\n📌 最长保护期 {MAX_PROTECTION_YEARS} 年尚未届满"
                f"（届满日：{max_protection_end}），"
                f"有特殊情况的，人民法院可根据权利人申请决定延长。"
                f"\n法条依据：《中华人民共和国民法典》第188条"
            )
        criminal_extra = ""
        if is_criminal and rule.years == 20:
            criminal_extra = (
                "\n📌 20年后认为必须追诉的，须报请最高人民检察院核准。"
            )
        return (
            f"🚫 {label}已届满！"
            f"届满日：{end_date}，距今日已过 {-remaining} 天。"
            f"{extra}{criminal_extra}\n"
            f"法律依据：{rule.law} {rule.article}。"
        )

    if level == WarningLevel.URGENT:
        return (
            f"🔴 紧急！距{label}届满仅剩 {remaining} 天！"
            f"届满日：{end_date}。请立即采取行动。\n"
            f"法律依据：{rule.law} {rule.article}。"
        )

    if level == WarningLevel.IMMINENT:
        return (
            f"🟠 紧迫：距{label}届满还有 {remaining} 天。"
            f"届满日：{end_date}。建议尽快启动程序。\n"
            f"法律依据：{rule.law} {rule.article}。"
        )

    if level == WarningLevel.ATTENTION:
        return (
            f"🟡 注意：距{label}届满还有 {remaining} 天（{end_date}）。"
            f"时效充足但建议尽早准备。\n"
            f"法律依据：{rule.law} {rule.article}。"
        )

    return (
        f"✅ {label}：{rule.years} 年。"
        f"届满日：{end_date}，距今日 {remaining} 天，时效充足。\n"
        f"法律依据：{rule.law} {rule.article}。"
    )


# ================================================================
# 快捷函数
# ================================================================

_calc_cache: Optional[LimitationCalculator] = None


def _get_calc() -> LimitationCalculator:
    global _calc_cache
    if _calc_cache is None:
        _calc_cache = LimitationCalculator()
    return _calc_cache


def calculate(
    case_type: str,
    incident_date: date | str,
    known_date: date | str | None = None,
    *,
    is_criminal: bool = False,
    is_extended: bool = False,
    is_interrupted: bool = False,
    extension_reason: str = "",
    new_crime_date: date | str | None = None,
) -> LimitationResult:
    """一行调用时效计算。

    用法:
        r = calculate("普通民事诉讼", "2023-05-01")
        print(r.warning_text, r.remaining_days, r.expired)

        r = calculate("法定最高刑不满5年", "2020-01-01", is_criminal=True)
    """
    calc = _get_calc()
    if is_criminal:
        return calc.criminal(
            case_type, incident_date,
            is_extended=is_extended,
            is_interrupted=is_interrupted,
            extension_reason=extension_reason,
            new_crime_date=new_crime_date,
        )
    return calc.civil(
        case_type, incident_date, known_date,
        is_extended=is_extended,
        is_interrupted=is_interrupted,
        extension_reason=extension_reason,
    )


def list_rules(scope: str = "all") -> list[dict]:
    """列出所有时效规则。

    Args:
        scope: "civil" / "admin" / "criminal" / "all"
    """
    pool = {
        "civil": CIVIL_RULES,
        "admin": ADMIN_RULES,
        "criminal": CRIMINAL_RULES,
        "all": ALL_RULES,
    }.get(scope, ALL_RULES)

    return [
        {
            "case_type": r.case_type,
            "years": r.years,
            "law": r.law,
            "article": r.article,
            "description": r.description,
            "scope": r.scope.name,
        }
        for r in pool
    ]


# ================================================================
# 自测
# ================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("诉讼时效计算器 功能验证")
    print("=" * 60)

    calc = LimitationCalculator(today=date(2026, 7, 3))

    # 测试1：正常民事（过期）
    print("\n[测试1] 普通民事诉讼，过期...")
    r1 = calc.civil("普通民事诉讼", "2022-06-01")
    print(f"  warning: {r1.warning_level.name}")
    print(f"  expired: {r1.expired}")
    print(f"  届满日:  {r1.limitation_end}")
    print(f"  {r1.warning_text[:120]}")

    # 测试2：正常民事（未过期）
    print("\n[测试2] 普通民事诉讼，未过期...")
    r2 = calc.civil("普通民事诉讼", "2025-06-01")
    print(f"  warning: {r2.warning_level.name}")
    print(f"  expired: {r2.expired}")
    print(f"  剩余:    {r2.remaining_days} 天")
    print(f"  {r2.warning_text[:120]}")

    # 测试3：紧急（< 30 天）
    print("\n[测试3] 劳动争议仲裁，即将到期...")
    r3 = calc.civil("劳动争议仲裁", "2026-06-10")
    print(f"  warning: {r3.warning_level.name}")
    print(f"  剩余:    {r3.remaining_days} 天")
    print(f"  {r3.warning_text[:120]}")

    # 测试4：最长保护期
    print("\n[测试4] 20年前事件，最长保护期检查...")
    r4 = calc.civil("普通民事诉讼", "2005-01-01")
    print(f"  expired: {r4.expired}")
    print(f"  届满日:  {r4.limitation_end}")
    print(f"  最长保护期届满: {r4.max_protection_end}")

    # 测试5：刑事追诉
    print("\n[测试5] 刑事追诉，法定最高刑<5年，未过期...")
    r5 = calc.criminal("法定最高刑不满5年", "2024-01-01")
    print(f"  expired: {r5.expired}")
    print(f"  剩余:    {r5.remaining_days} 天")
    print(f"  {r5.warning_text[:120]}")

    # 测试6：刑事追诉过期
    print("\n[测试6] 刑事追诉，法定最高刑<5年，已过期...")
    r6 = calc.criminal("法定最高刑不满5年", "2020-01-01")
    print(f"  expired: {r6.expired}")
    print(f"  {r6.warning_text[:120]}")

    # 测试7：时效中断（又犯新罪）
    print("\n[测试7] 刑事追诉中断（又犯新罪）...")
    r7 = calc.criminal("法定最高刑5年以上不满10年", "2015-01-01",
        is_interrupted=True, new_crime_date="2022-01-01")
    print(f"  interrupted: {r7.is_interrupted}")
    print(f"  expired: {r7.expired}")
    print(f"  start: {r7.limitation_start}, end: {r7.limitation_end}")

    # 测试8：时效延长（逃避侦查）
    print("\n[测试8] 刑事追诉延长（逃避侦查）...")
    r8 = calc.criminal("法定最高刑10年以上有期徒刑", "2010-01-01",
        is_extended=True, extension_reason="立案后逃避侦查")
    print(f"  extended: {r8.is_extended}")
    print(f"  expired: {r8.expired}")
    print(f"  {r8.warning_text[:120]}")

    # 测试9：快捷函数
    print("\n[测试9] 快捷函数 calculate() ...")
    r9 = calculate("商标侵权", "2025-03-01")
    print(f"  case: {r9.rule.case_type}, remaining: {r9.remaining_days}")

    # 测试10：列规则
    print("\n[测试10] 列出刑事规则 ...")
    criminal_rules = list_rules("criminal")
    print(f"  共 {len(criminal_rules)} 条刑事追诉时效")

    print("\n" + "=" * 60)
    print("全部验证通过")
    print("=" * 60)
