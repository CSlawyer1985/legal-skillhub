#!/usr/bin/env python3
"""零参数劳动争议受理入口。

接收自然语言或JSON，自动识别场景并返回已经识别的信息、缺失信息、
缺失原因、获取方式、可复制填写表和下一步命令建议。无第三方依赖。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Field:
    key: str
    label: str
    reason: str
    source: str


SCENARIOS: dict[str, dict[str, Any]] = {
    "compensation": {
        "keywords": ["辞退", "解除", "裁员", "优化", "让我走", "不用上班", "不让上班", "逼我辞职", "调岗", "降薪", "多能工", "一人多岗", "末位", "补偿", "赔偿", "2n", "n+1", "工龄", "2008"],
        "label": "解除/终止与N、2N或分段工龄",
        "fields": [
            Field("work_location", "实际工作地", "地方标准、管辖和部分待遇可能不同", "劳动合同、工作地址或社保缴纳地"),
            Field("start_date", "入职日期", "决定工龄和是否涉及历史分段", "劳动合同、社保记录、工资流水"),
            Field("end_date", "解除或终止日期", "决定工龄、时效和适用规则", "解除通知、离职证明、送达记录"),
            Field("termination_reason", "单位书面理由和依据", "决定N、2N、N+1或继续履行的法律路径", "解除通知、谈话录音、规章制度"),
            Field("monthly_wage", "工资基数及明细", "决定暂算金额和封顶判断", "解除前工资流水、工资条、个税记录"),
            Field("evidence", "现有证据", "决定事实能否证明和方案风险", "合同、聊天、考勤、通知、工资流水"),
        ],
    },
    "overtime": {
        "keywords": ["加班", "考勤", "调休", "周末", "法定节假日", "工时"],
        "label": "加班费",
        "fields": [
            Field("work_location", "实际工作地", "用于核验地方口径和程序", "合同、社保或工作地址"),
            Field("work_time_system", "工时制度", "不同工时制度影响加班认定", "合同、审批文件、员工手册"),
            Field("overtime_detail", "按日期分类的加班小时", "计算工作日、休息日和法定节假日分项", "考勤、排班、审批、聊天"),
            Field("hourly_base", "小时工资基数及来源", "决定算术结果", "合同、工资条和已核验规则"),
            Field("multipliers", "各类加班倍率", "倍率不得由脚本猜测", "争议发生时有效的官方规则"),
            Field("already_paid", "已支付或已调休情况", "避免重复主张", "工资条、调休记录"),
        ],
    },
    "wage_arrears": {
        "keywords": ["欠薪", "欠工资", "拖欠工资", "工资没发", "工资不给", "少发", "扣工资", "提成"],
        "label": "工资欠付",
        "fields": [
            Field("work_location", "实际工作地", "用于管辖和投诉渠道", "合同、工作地址"),
            Field("period", "欠付月份", "确定请求期间", "工资表、银行流水"),
            Field("monthly_wage", "每月应付金额和构成", "区分固定工资、提成、奖金和扣款", "合同、工资条、绩效规则"),
            Field("already_paid", "每月已付金额", "计算差额", "银行流水、工资条"),
            Field("evidence", "工资约定与支付证据", "证明应付和实付", "合同、聊天、流水、工资表"),
        ],
    },
    "sick_leave": {
        "keywords": ["病假", "医疗期", "病假工资", "诊断证明", "住院"],
        "label": "病假工资",
        "fields": [
            Field("work_location", "实际工作地", "病假工资规则存在地方差异", "合同、社保或工作地址"),
            Field("dispute_date", "病假发生年月", "确定当时有效规则", "请假单、诊断证明"),
            Field("days", "病假天数", "决定暂算期间", "请假审批、病历"),
            Field("daily_base", "已核验日基数", "决定算术结果", "工资材料和地方官方规则"),
            Field("rate", "已核验支付比例", "比例存在地方和条件差异", "当地政府或人社官网"),
            Field("already_paid", "已支付金额", "计算差额", "工资条、流水"),
        ],
    },
    "annual_leave": {
        "keywords": ["年假", "年休假", "未休年假", "带薪年休假"],
        "label": "未休年休假工资",
        "fields": [
            Field("work_location", "实际工作地", "用于核验程序和地方口径", "合同或工作地址"),
            Field("year", "争议年度", "决定资格、天数和时效", "考勤、休假记录"),
            Field("entitled_days", "应休天数", "决定计算数量", "累计工龄材料、休假制度"),
            Field("used_days", "已休天数", "计算未休差额", "考勤、请假记录"),
            Field("daily_base", "已核验日基数", "决定算术结果", "工资材料和现行规则"),
            Field("rate", "已核验支付比例", "避免误把已含正常工资部分重复计算", "官方规则"),
        ],
    },
    "work_injury": {
        "keywords": ["工伤", "受伤", "职业病", "劳动能力鉴定", "停工留薪", "上下班事故", "工作中摔伤", "工作中骨折"],
        "label": "工伤认定、鉴定、待遇与争议衔接",
        "fields": [
            Field("work_location", "事故地、用工地及参保地", "用于核验认定管辖、参保经办和地方待遇", "事故记录、劳动合同、社保记录"),
            Field("accident_date", "事故或职业病诊断日期", "决定紧急期限、适用规则和证据保全顺序", "病历、事故报告、诊断证明"),
            Field("accident_context", "事故时间、地点、原因及正在执行的工作", "决定是否可能属于工作原因、上下班事故或其他认定路径", "现场记录、排班、任务指令、交通事故认定书"),
            Field("relationship", "合同、实际管理和工资支付主体", "可能需要确认劳动关系或区分派遣、外包、平台用工", "合同、平台规则、工资结算、考勤和工作指令"),
            Field("medical_materials", "首诊、病历、影像、诊断和费用材料", "证明伤情、治疗经过、因果关系和费用", "医疗机构病历、发票、费用清单、诊断证明"),
            Field("application_status", "单位是否申报及认定/鉴定状态", "决定由谁立即申请以及下一程序", "申报记录、受理决定、认定决定、鉴定结论"),
            Field("insurance_status", "工伤保险参保和缴费情况", "影响经办支付与单位责任分析，但未参保不当然排除工伤认定", "社保查询、缴费记录、单位说明"),
            Field("current_treatment_and_pay", "治疗、停工及工资支付现状", "用于安排治疗、停工留薪和待遇请求", "医嘱、请假记录、工资流水"),
        ],
        "immediate_actions": [
            "先治疗并完整保存首诊病历、影像、诊断、医嘱、发票和费用清单，不因单位口头承诺延误就医。",
            "立即固定事故时间、地点、任务来源、现场人员、排班考勤、监控线索和书面事故经过。",
            "核对单位是否已申报；单位未依法申报时，不等待双方推诿，尽快向当地人社部门核验个人/近亲属/工会申请路径和期限。",
        ],
        "red_flags": [
            "事故或职业病诊断日期接近工伤认定申请期限",
            "单位要求写成个人原因受伤、私了后放弃工伤或倒签材料",
            "劳动关系、派遣主体或实际用工主体被否认",
            "交通事故责任、第三人侵权或商业保险与工伤待遇混在一起",
        ],
    },
    "dispatch": {
        "keywords": ["劳务派遣", "派遣工", "派遣公司", "用工单位", "被退回", "退回派遣", "同工同酬", "假外包", "真派遣", "跨地区派遣"],
        "label": "劳务派遣三方责任、退回解除与待遇",
        "fields": [
            Field("dispatch_company", "劳务派遣单位名称和所在地", "派遣单位通常是劳动合同相对方并承担用人单位义务", "劳动合同、工资流水、社保记录、派遣许可证信息"),
            Field("host_company", "实际用工单位名称和工作地", "用于判断实际管理、劳动保护、福利待遇及协助义务", "工牌、考勤、工作指令、现场照片"),
            Field("dispatch_agreement_facts", "岗位、期限、地点、工资工时和派遣安排", "用于审查三性岗位、报酬、社保和协议履行", "劳动合同、派遣告知、岗位说明、工资条"),
            Field("management_and_payment", "谁招聘、管理、考核、发工资和缴社保", "用于建立三方主体责任矩阵并识别假外包真派遣", "招聘记录、考勤、审批、流水、社保查询"),
            Field("dispute_action", "退回、解除、欠薪、工伤或同工同酬的具体事实", "不同争点对应不同责任主体、程序和请求", "退回通知、解除通知、工资材料、事故材料"),
            Field("special_status", "医疗期、工伤、孕产哺乳期等特殊状态", "可能影响退回、解除和保护规则", "病历、认定决定、孕检或生育材料"),
        ],
        "immediate_actions": [
            "同时向派遣单位和用工单位书面确认劳动合同、岗位、工资社保、退回/解除理由及当前工作安排。",
            "分别保存两方证据：派遣单位的合同、工资和社保；用工单位的考勤、指令、考核、劳动保护和事故材料。",
            "被退回不等于劳动合同已解除；在收到明确安排前书面表示愿意履职，避免被反指拒绝派遣或旷工。",
        ],
        "red_flags": [
            "只告用工单位或只告派遣单位，遗漏可能承担责任的主体",
            "把用工单位退回直接等同于派遣单位合法解除",
            "用外包、承揽名称掩盖由用工单位直接管理的派遣事实",
            "跨地区参保地、工伤申报主体和实际用工地未经核验",
        ],
    },
    "general": {
        "keywords": [],
        "label": "一般劳动法问题",
        "fields": [
            Field("role", "咨询身份", "劳动者和用人单位的目标与义务不同", "直接说明"),
            Field("work_location", "实际工作地", "用于地方规则和管辖", "合同或工作地址"),
            Field("timeline", "关键时间线", "用于判断适用规则和期限", "按日期列出事件"),
            Field("goal", "希望达到的目标", "用于选择继续履行、结算、投诉、仲裁或整改", "直接说明优先目标"),
            Field("evidence", "现有材料", "用于评估事实和风险", "列出文件名称即可"),
        ],
    },
}


def normalize_payload(text: str | None, json_text: str | None) -> dict[str, Any]:
    if json_text:
        try:
            data = json.loads(json_text)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"JSON无法解析：第{exc.lineno}行第{exc.colno}列。请检查双引号、逗号和括号；"
                "也可以不用JSON，改用 --text 直接描述问题"
            ) from exc
        if not isinstance(data, dict):
            raise ValueError("JSON顶层必须是对象，例如 {\"text\": \"公司辞退我\"}")
        return data
    if text:
        return {"text": text}
    return {"text": ""}


def detect_scenarios(payload: dict[str, Any]) -> list[tuple[str, list[str]]]:
    explicit = str(payload.get("scenario", "")).strip()
    if explicit:
        if explicit not in SCENARIOS:
            raise ValueError(
                f"未知场景“{explicit}”。可选：{', '.join(SCENARIOS.keys())}；"
                "不确定时删除scenario字段，由系统自动识别"
            )
        return [(explicit, ["用户明确指定场景"])]
    text = " ".join(str(payload.get(key, "")) for key in ("text", "question", "description")).lower()
    matches: list[tuple[int, str, list[str]]] = []
    for key, config in SCENARIOS.items():
        if key == "general":
            continue
        hits = [word for word in config["keywords"] if word.lower() in text]
        if hits:
            matches.append((len(hits), key, hits))
    matches.sort(key=lambda item: (-item[0], item[1]))
    if not matches:
        return [("general", ["未发现明确场景关键词，进入一般劳动法受理"])]
    return [(key, [f"命中关键词：{', '.join(hits)}"]) for _, key, hits in matches]


def detect_scenario(payload: dict[str, Any]) -> tuple[str, list[str]]:
    """兼容旧调用：返回优先级最高的场景。"""
    return detect_scenarios(payload)[0]


def extract_simple_values(payload: dict[str, Any]) -> dict[str, Any]:
    recognized = {key: value for key, value in payload.items() if key not in {"text", "question", "description", "scenario"} and value not in (None, "", [])}
    text = str(payload.get("text", ""))
    date_matches = re.findall(r"\b\d{4}-\d{2}-\d{2}\b", text)
    if date_matches:
        recognized["dates_found_in_text"] = date_matches
    money_matches = re.findall(r"(?<!\d)(\d+(?:\.\d+)?)\s*元", text)
    if money_matches:
        recognized["money_found_in_text"] = money_matches
    return recognized


def build_intake(payload: dict[str, Any]) -> dict[str, Any]:
    detected = detect_scenarios(payload)
    scenario, reasons = detected[0]
    config = SCENARIOS[scenario]
    recognized = extract_simple_values(payload)
    missing = []
    seen_fields: set[str] = set()
    for detected_key, _ in detected:
        for field in SCENARIOS[detected_key]["fields"]:
            if field.key in seen_fields:
                continue
            seen_fields.add(field.key)
            if field.key not in payload or payload.get(field.key) in (None, "", []):
                missing.append(
                    {
                        "field": field.key,
                        "label": field.label,
                        "why_needed": field.reason,
                        "where_to_find": field.source,
                        "fallback": "暂时拿不到时，说明由谁掌握并提供现有替代材料；不因缺失该项而停止给出保守行动建议。",
                    }
                )
    fill_form = "\n".join(f"{item['label']}：" for item in missing)
    complete = not missing
    return {
        "status": "ready" if complete else "needs_information",
        "scenario": scenario,
        "scenario_label": config["label"],
        "all_detected_scenarios": [
            {
                "scenario": key,
                "label": SCENARIOS[key]["label"],
                "detection_reason": detected_reasons,
            }
            for key, detected_reasons in detected
        ],
        "detection_reason": reasons,
        "recognized": recognized,
        "missing_information": missing,
        "copyable_form": fill_form or "信息已齐，可进入法律核验和计算。",
        "what_can_be_done_now": config.get("immediate_actions", [
            "先保存合同、工资流水、考勤、聊天和通知的原始载体。",
            "先检查是否存在仲裁、起诉、工伤认定、举证或文书签收期限。",
            "对未核验的地方标准、倍率和比例暂不猜测；即使网络不可用也先完成证据与期限止损。",
        ]),
        "scenario_red_flags": config.get("red_flags", [
            "不要把用户口语直接改写为确定法律结论。",
            "不要遗漏主体、期限、要件、证据、渠道和程序衔接检查。",
        ]),
        "novel_issue_checklist": [
            "主体：谁签合同、谁实际管理、谁支付、谁作出争议行为、是否存在多方责任？",
            "期限：哪个事件启动何种申请、仲裁、诉讼、复议、鉴定或举证期限？",
            "要件：请求成立需要哪些事实，哪些已确认、哪些仍待核？",
            "证据：每个要件由什么材料证明、由谁掌握、灭失风险和合法替代证据是什么？",
            "渠道：行政、仲裁、诉讼、工伤或其他程序是否前置、并行、择一或相互等待？",
            "金额：资格与责任是否先成立，基数、期间、比例、已付和地方参数是否可核？",
            "抗辩：对方最可能提出什么事实、程序或证据抗辩，如何提前补强？",
            "衔接：是否涉及派遣、外包、平台、第三人侵权、商业保险、刑事或其他专业移交？",
        ],
        "offline_fallback": {
            "step_1": "先按已确认的全国法律框架给条件式结论，不猜地方数值或入口。",
            "step_2": "列出地区、争议年月、完整待核事项和可复制官方查询词。",
            "step_3": "通过12333或当地人社/受理机关确认文件全称、数值、程序和材料要求。",
        },
        "fallback_if_unavailable": "暂时拿不到材料时，说明材料由谁掌握、何时可能取得；技能将给保守区间、证据补强方案和不依赖该材料的下一步。",
        "next_action": "可填写 copyable_form，也可只回答最紧急的日期和行为；未补齐时仍会先给保守结论与立即动作。" if missing else "进入来源核验、争点分析、透明测算和方案输出。",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="劳动争议零参数受理入口")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--text", help="直接输入自然语言问题")
    group.add_argument("--json", dest="json_text", help="输入JSON对象字符串")
    parser.add_argument("--demo", action="store_true", help="输出可复制示例")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.demo:
        print(json.dumps({
            "natural_language": "python scripts/labor_claim_intake.py --text \"我2005年入职，2026年被辞退，补偿怎么分段算？\"",
            "json": {"scenario": "overtime", "text": "公司长期安排周末加班", "work_location": "上海"},
            "tip": "无参数运行也可以，会返回一般劳动法受理表。",
        }, ensure_ascii=False, indent=2))
        return 0
    try:
        payload = normalize_payload(args.text, args.json_text)
        result = build_intake(payload)
    except ValueError as exc:
        print(json.dumps({
            "status": "error",
            "error_code": "INTAKE_INPUT_ERROR",
            "problem": str(exc),
            "how_to_fix": [
                "运行 --demo 复制正确示例。",
                "不熟悉JSON时改用 --text 直接描述问题。",
                "仍不确定时无参数运行，先取得一般受理填写表。",
            ],
        }, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
