#!/usr/bin/env python3
"""Validate example JSON files for minimal complaint drafting quality."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path


CASE_EXAMPLES = {
    "00": "general-civil-data.json",
    "01": "private-lending-data.json",
    "02": "divorce-data.json",
    "03": "sales-contract-data.json",
    "04": "financial-loan-data.json",
    "05": "property-service-data.json",
    "06": "credit-card-data.json",
    "07": "traffic-accident-data.json",
    "08": "labor-dispute-data.json",
    "09": "finance-lease-data.json",
    "10": "guarantee-insurance-data.json",
    "11": "securities-fraud-data.json",
    "12": "inheritance-data.json",
    "13": "administrative-data.json",
    "14": "medical-dispute-data.json",
    "15": "real-estate-data.json",
    "16": "company-equity-data.json",
    "17": "construction-contract-data.json",
    "18": "intellectual-property-data.json",
    "19": "personality-internet-data.json",
    "20": "land-demolition-data.json",
    "21": "environmental-protection-data.json",
    "22": "foreign-related-data.json",
    "23": "insurance-claim-data.json",
    "24": "fund-investment-data.json",
    "25": "private-fund-data.json",
    "26": "trust-dispute-data.json",
    "27": "house-lease-data.json",
    "28": "personal-injury-data.json",
    "29": "patent-dispute-data.json",
    "30": "trade-secret-data.json",
    "31": "company-dissolution-data.json",
    "32": "government-info-data.json",
    "33": "foreign-service-data.json",
    "34": "consumer-rights-data.json",
    "criminal-accusation": "criminal-accusation-data.json",
    "bail-application": "bail-application-data.json",
    "criminal-defense-opinion": "criminal-defense-opinion-data.json",
    "criminal-incidental-civil": "criminal-incidental-civil-data.json",
    "detention-family-communication": "detention-family-communication-data.json",
}

QUALITY_RULES = {
    "party": ["原告", "被告", "控告人", "被控告人", "申请人", "被申请人", "犯罪嫌疑人", "被告人", "当事人", "家属"],
    "claim": ["诉讼请求", "请求", "判令", "控告请求", "申请事项", "申请", "辩护", "沟通"],
    "fact": ["事实", "理由", "签订", "发生", "拖欠", "违法", "事故", "处罚", "违约"],
    "evidence": ["证据", "合同", "记录", "凭证", "认定书", "处罚决定", "账单", "工资", "转账", "病历"],
}

CASE_QUALITY_RULES = {
    "general-civil-data.json": {
        "general.dispute": ["争议", "纠纷", "合同"],
        "general.court": ["人民法院", "法院"],
    },
    "private-lending-data.json": {
        "private_lending.principal": ["本金", "借款金额"],
        "private_lending.interest": ["利息", "逾期"],
        "private_lending.delivery": ["转账", "交付", "银行"],
    },
    "divorce-data.json": {
        "divorce.marriage": ["结婚", "婚后", "夫妻"],
        "divorce.breakdown": ["感情", "分居", "破裂"],
        "divorce.child_or_property": ["子女", "抚养", "财产"],
    },
    "sales-contract-data.json": {
        "sales.contract": ["买卖合同", "合同"],
        "sales.goods": ["货物", "交付"],
        "sales.payment": ["货款", "付款"],
    },
    "financial-loan-data.json": {
        "financial_loan.loan": ["贷款", "借款合同"],
        "financial_loan.principal": ["本金", "贷款本金"],
        "financial_loan.interest": ["利息", "罚息"],
    },
    "property-service-data.json": {
        "property.service": ["物业服务", "物业"],
        "property.fee": ["物业服务费", "收费"],
        "property.notice": ["催告", "催缴"],
    },
    "credit-card-data.json": {
        "credit_card.card": ["信用卡"],
        "credit_card.bill": ["账单", "交易明细"],
        "credit_card.repayment": ["还款", "欠款"],
    },
    "traffic-accident-data.json": {
        "traffic.accident": ["交通事故", "事故"],
        "traffic.liability": ["认定书", "责任"],
        "traffic.damage": ["医疗费", "误工费", "护理费"],
        "traffic.insurance": ["保险"],
    },
    "labor-dispute-data.json": {
        "labor.relationship": ["劳动关系", "劳动合同"],
        "labor.wage_or_termination": ["工资", "解除"],
        "labor.arbitration": ["仲裁", "裁决书"],
    },
    "finance-lease-data.json": {
        "finance_lease.contract": ["融资租赁合同", "租赁合同"],
        "finance_lease.object": ["租赁物", "设备"],
        "finance_lease.rent": ["租金"],
    },
    "guarantee-insurance-data.json": {
        "guarantee_insurance.policy": ["保证保险", "保险合同"],
        "guarantee_insurance.compensation": ["代偿"],
        "guarantee_insurance.recourse": ["追偿", "催收"],
    },
    "securities-fraud-data.json": {
        "securities.misstatement": ["虚假陈述", "信息披露"],
        "securities.penalty": ["处罚", "处罚决定"],
        "securities.trade": ["交易记录", "买入"],
        "securities.loss": ["损失"],
    },
    "inheritance-data.json": {
        "inheritance.decedent": ["被继承人"],
        "inheritance.heir": ["继承人", "继承权"],
        "inheritance.estate": ["遗产", "房产", "存款"],
        "inheritance.death": ["死亡证明", "死亡"],
    },
    "administrative-data.json": {
        "administrative.defendant": ["行政机关", "市场监督管理局", "被告"],
        "administrative.action": ["行政处罚", "处罚决定"],
        "administrative.deadline": ["起诉期限", "六个月"],
        "administrative.review": ["行政复议", "复议"],
    },
    "medical-dispute-data.json": {
        "medical.institution": ["医院", "医疗机构"],
        "medical.record": ["病历", "住院病案"],
        "medical.damage": ["损害", "残疾", "死亡"],
        "medical.appraisal": ["鉴定", "司法鉴定"],
    },
    "real-estate-data.json": {
        "real_estate.house": ["房屋", "不动产"],
        "real_estate.contract": ["房屋买卖合同", "买卖合同"],
        "real_estate.payment": ["定金", "首付款", "房款"],
        "real_estate.registration": ["过户", "转移登记"],
    },
    "company-equity-data.json": {
        "company.target": ["目标公司", "公司"],
        "company.equity": ["股权", "股东"],
        "company.registration": ["工商变更", "登记"],
        "company.records": ["章程", "股东会决议", "股东名册"],
    },
    "construction-contract-data.json": {
        "construction.project": ["工程", "建设工程"],
        "construction.payment": ["工程款", "结算款", "质保金"],
        "construction.acceptance": ["竣工", "验收"],
        "construction.variation": ["签证", "变更", "施工日志"],
    },
    "intellectual-property-data.json": {
        "ip.right": ["著作权", "商标", "知识产权"],
        "ip.infringement": ["侵权", "未经许可"],
        "ip.evidence": ["公证", "时间戳", "链接"],
        "ip.damage": ["赔偿", "维权费用"],
    },
    "personality-internet-data.json": {
        "personality.right": ["名誉权", "肖像权", "个人信息"],
        "personality.platform": ["平台", "账号", "链接"],
        "personality.spread": ["浏览量", "评论", "传播"],
        "personality.notice": ["删除通知", "投诉", "披露"],
    },
    "land-demolition-data.json": {
        "land.expropriation": ["征收", "征地", "拆迁"],
        "land.compensation": ["补偿", "安置"],
        "land.demolition": ["强制拆除", "强拆"],
        "land.review": ["行政复议", "起诉期限", "送达"],
    },
    "environmental-protection-data.json": {
        "environment.pollution": ["污染", "排污", "污染物"],
        "environment.monitoring": ["监测报告", "检测报告"],
        "environment.penalty": ["行政处罚", "责令整改"],
        "environment.damage": ["损失", "修复", "鉴定"],
    },
    "foreign-related-data.json": {
        "foreign.party": ["境外", "注册地", "新加坡"],
        "foreign.jurisdiction": ["管辖", "履行地"],
        "foreign.evidence": ["翻译件", "附加证明书", "公证认证"],
        "foreign.payment": ["美元", "银行水单", "SWIFT"],
    },
    "insurance-claim-data.json": {
        "insurance.policy": ["保险单", "保险期间", "保险金额"],
        "insurance.claim": ["理赔", "报案", "拒赔"],
        "insurance.exemption": ["免责条款", "提示说明"],
        "insurance.loss": ["保险金", "评估费", "施救费"],
    },
    "fund-investment-data.json": {
        "fund.product": ["基金", "基金代码", "风险等级"],
        "fund.suitability": ["风险测评", "适当性", "风险承受能力"],
        "fund.disclosure": ["风险揭示", "招募说明书", "净值公告"],
        "fund.loss": ["赎回", "损失计算表", "投资损失"],
    },
    "private-fund-data.json": {
        "private_fund.product": ["私募基金", "基金编号", "备案"],
        "private_fund.qualified": ["合格投资者", "资产证明"],
        "private_fund.underlying": ["底层资产", "投后管理"],
        "private_fund.default": ["兑付", "延期", "损失计算表"],
    },
    "trust-dispute-data.json": {
        "trust.plan": ["信托计划", "信托编号", "受益人"],
        "trust.disclosure": ["信息披露", "清算报告"],
        "trust.underlying": ["底层资产", "信托财产"],
        "trust.credit": ["差额补足", "保证合同", "增信"],
    },
    "house-lease-data.json": {
        "lease.contract": ["房屋租赁合同", "商铺", "租期"],
        "lease.payment": ["租金", "押金", "物业费"],
        "lease.termination": ["解除通知", "腾退", "返还房屋"],
        "lease.damage": ["违约金", "占有使用费", "维修"],
    },
    "personal-injury-data.json": {
        "injury.accident": ["事故", "受伤", "现场"],
        "injury.medical": ["病历", "诊断证明", "医疗费"],
        "injury.appraisal": ["伤残鉴定", "三期鉴定"],
        "injury.damage": ["误工费", "护理费", "赔偿计算表"],
    },
    "patent-dispute-data.json": {
        "patent.right": ["专利号", "实用新型", "专利权评价报告"],
        "patent.claim": ["权利要求", "技术特征", "技术比对"],
        "patent.infringement": ["被诉产品", "许诺销售", "专利侵权"],
        "patent.evidence": ["网页公证", "购买公证", "技术比对表"],
    },
    "trade-secret-data.json": {
        "trade_secret.secret": ["商业秘密", "实验参数", "客户报价"],
        "trade_secret.confidentiality": ["保密制度", "保密协议", "权限分级"],
        "trade_secret.misappropriation": ["离职", "异常下载", "竞争公司"],
        "trade_secret.evidence": ["访问日志", "非公知性鉴定", "证据保全"],
    },
    "company-dissolution-data.json": {
        "dissolution.company": ["目标公司", "股权", "公司章程"],
        "dissolution.deadlock": ["股东会", "无法形成有效决议", "经营管理"],
        "dissolution.liquidation": ["解散", "清算组", "清算"],
        "dissolution.evidence": ["营业执照", "股东名册", "公章账册"],
    },
    "government-info-data.json": {
        "government_info.request": ["政府信息公开", "申请编号", "邮寄"],
        "government_info.response": ["答复", "不予公开", "逾期"],
        "government_info.content": ["征地批复", "补偿安置方案", "征地公告"],
        "government_info.evidence": ["申请表", "签收记录", "答复书"],
    },
    "foreign-service-data.json": {
        "foreign_service.party": ["境外", "新加坡", "Global Supply"],
        "foreign_service.service": ["涉外送达", "海牙送达公约", "司法协助"],
        "foreign_service.material": ["翻译件", "附加证明书", "境外主体登记"],
        "foreign_service.contact": ["送达邮箱", "注册地址", "联络办公室"],
        "foreign_service.jurisdiction": ["管辖", "法院", "争议"],
        "foreign_service.claims": ["预付款", "赔偿", "诉讼费用"],
    },
    "criminal-accusation-data.json": {
        "criminal_accusation.accuser": ["控告人"],
        "criminal_accusation.accused": ["被控告人"],
        "criminal_accusation.crime": ["涉嫌", "罪"],
        "criminal_accusation.authority": ["公安", "检察院", "接收机关"],
    },
    "bail-application-data.json": {
        "bail.applicant": ["申请人"],
        "bail.suspect": ["被申请人", "犯罪嫌疑人", "被告人"],
        "bail.measure": ["取保候审", "强制措施"],
        "bail.guarantee": ["保证人", "保证金", "保证方式"],
    },
    "criminal-defense-opinion-data.json": {
        "defense.stage": ["侦查阶段", "刑事拘留", "羁押"],
        "defense.charge": ["涉嫌", "罪", "指控"],
        "defense.focus": ["争议焦点", "有利事实", "不构罪"],
        "defense.evidence": ["证据审查", "讯问", "阅卷"],
    },
    "criminal-incidental-civil-data.json": {
        "incidental.party": ["附带民事诉讼原告人", "附带民事诉讼被告人"],
        "incidental.criminal_case": ["刑事案件", "故意伤害罪", "提起公诉"],
        "incidental.claim": ["赔偿", "医疗费", "误工"],
        "incidental.evidence": ["刑事起诉书", "鉴定", "票据"],
    },
    "detention-family-communication-data.json": {
        "detention.family": ["家属", "亲属关系"],
        "detention.measure": ["刑事拘留", "羁押", "看守所"],
        "detention.procedure": ["拘留通知书", "逮捕", "取保候审"],
        "detention.risk": ["不得", "串供", "毁灭"],
    },
}


@dataclass(frozen=True)
class ValidationResult:
    file: str
    field_count: int
    missing_rules: list[str]

    @property
    def passed(self) -> bool:
        return not self.missing_rules


def resolve_skill_root(skill_root: str | None) -> Path:
    if skill_root:
        return Path(skill_root).resolve()
    return Path(__file__).resolve().parents[1]


def load_fields(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path.name}: JSON root must be an object")

    fields = data.get("fields")
    if not isinstance(fields, dict):
        raise ValueError(f"{path.name}: missing object field 'fields'")
    return fields


def text_blob(fields: dict[str, object]) -> str:
    parts: list[str] = []
    for key, value in fields.items():
        parts.append(str(key))
        parts.append(stringify(value))
    return "\n".join(parts)


def stringify(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple)):
        return "；".join(stringify(item) for item in value)
    if isinstance(value, dict):
        return "；".join(f"{key}：{stringify(item)}" for key, item in value.items())
    return str(value)


def validate_file(path: Path) -> ValidationResult:
    fields = load_fields(path)
    content = text_blob(fields)
    missing_rules: list[str] = []

    if len(fields) < 5:
        missing_rules.append("min_fields")

    for rule_name, keywords in QUALITY_RULES.items():
        if not any(keyword in content for keyword in keywords):
            missing_rules.append(rule_name)

    for rule_name, keywords in CASE_QUALITY_RULES.get(path.name, {}).items():
        if not any(keyword in content for keyword in keywords):
            missing_rules.append(rule_name)

    return ValidationResult(file=path.name, field_count=len(fields), missing_rules=missing_rules)


def validate_examples(skill_root: Path) -> list[ValidationResult]:
    examples_dir = skill_root / "examples"
    results: list[ValidationResult] = []
    checked_names: set[str] = set()

    for example_name in CASE_EXAMPLES.values():
        checked_names.add(example_name)
        path = examples_dir / example_name
        if not path.exists():
            results.append(ValidationResult(file=example_name, field_count=0, missing_rules=["missing_file"]))
            continue
        results.append(validate_file(path))

    for path in sorted(examples_dir.glob("*-data.json")):
        if path.name in checked_names:
            continue
        results.append(validate_file(path))

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate baozheng example JSON quality.")
    parser.add_argument("--skill-root", help="Path to baozheng-skills root. Defaults to script parent.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON report.")
    args = parser.parse_args()

    results = validate_examples(resolve_skill_root(args.skill_root))
    report = [
        {
            "file": item.file,
            "field_count": item.field_count,
            "passed": item.passed,
            "missing_rules": item.missing_rules,
        }
        for item in results
    ]

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for item in report:
            status = "OK" if item["passed"] else "FAIL"
            print(f"{status} {item['file']} fields={item['field_count']} missing={','.join(item['missing_rules'])}")

    return 0 if all(item.passed for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
