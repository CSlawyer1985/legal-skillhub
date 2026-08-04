#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
劳动仲裁申请书自动生成脚本

功能：
  根据用户提供的案件信息，自动生成仲裁申请书、证据清单和金额计算表。

用法：
  方式一：通过命令行参数传入
    python generate_arbitration_docs.py --applicant-name "张三" --applicant-id "110..." \
        --respondent "XX公司" --respondent-code "91XXX..." \
        --city "北京" --start-date "2023-01-01" --end-date "2024-06-30" \
        --monthly-salary 8000 --output-dir ./output

  方式二：通过 JSON 配置文件传入（推荐，适合复杂案件）
    python generate_arbitration_docs.py --config case_info.json --output-dir ./output

  JSON 配置文件格式示例：
    {
        "applicant_name": "张三",
        "applicant_gender": "男",
        "applicant_id": "110101199001011234",
        "applicant_address": "北京市XX区XX路XX号",
        "applicant_phone": "13800138000",
        "respondent_name": "XX科技有限公司",
        "respondent_code": "91110100XXXXXXXXXX",
        "respondent_address": "北京市XX区XX路XX号",
        "respondent_legal_rep": "李四",
        "respondent_phone": "010-XXXXXXXX",
        "city": "北京",
        "start_date": "2023-01-01",
        "end_date": "2024-06-30",
        "end_reason": "公司单方辞退",
        "monthly_salary": 8000,
        "has_contract": true,
        "claims": [
            {
                "type": "back_pay",
                "description": "支付2024年5月至6月拖欠工资",
                "amount": 16000,
                "period": "2024-05-01至2024-06-30"
            },
            {
                "type": "severance_2n",
                "description": "支付违法解除劳动合同赔偿金",
                "amount": 24000,
                "period": "工作1.5年，按2个月×2倍计算"
            },
            {
                "type": "annual_leave",
                "description": "支付未休年休假工资",
                "amount": 3678,
                "period": "5天未休"
            }
        ],
        "facts": "申请人于2023年1月1日入职被申请人处，担任开发工程师，月工资8000元。2024年5月起被申请人拖欠工资。2024年6月30日，被申请人以'公司业务调整'为由单方辞退申请人，未提前30日通知，也未支付经济补偿。申请人工作期间有5天年休假未休。",
        "evidence_list": [
            {"name": "劳动合同", "purpose": "证明双方存在劳动合同关系，约定月工资8000元"},
            {"name": "银行工资流水", "purpose": "证明工资发放情况及拖欠事实"},
            {"name": "解除通知书", "purpose": "证明被申请人单方解除劳动合同"},
            {"name": "考勤记录", "purpose": "证明出勤情况及未休年休假"},
            {"name": "社保缴纳记录", "purpose": "证明劳动关系及工作年限"}
        ]
    }

输出文件：
  - 仲裁申请书.md
  - 证据清单.md
  - 金额计算表.md
"""

import argparse
import json
import os
import sys
from datetime import datetime


def calculate_work_years(start_date: str, end_date: str) -> dict:
    """计算工作年限，返回年限和补偿月数信息"""
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        return {"years": 0, "severance_months": 0, "severance_2n_months": 0, "description": "日期格式错误"}

    days = (end - start).days
    months = days / 30.44  # 平均每月天数
    years = months / 12

    # 计算经济补偿月数
    if months >= 12:
        full_years = int(months // 12)
        remaining_months = months - full_years * 12
        if remaining_months >= 6:
            severance_months = full_years + 1
        else:
            severance_months = full_years + 0.5
    elif months >= 6:
        severance_months = 1
    else:
        severance_months = 0.5

    return {
        "years": round(years, 2),
        "total_months": round(months, 1),
        "severance_months": severance_months,
        "severance_2n_months": severance_months * 2,
        "description": f"工作约{round(months, 1)}个月（约{round(years, 2)}年），经济补偿{severance_months}个月，违法解除赔偿{severance_months * 2}个月"
    }


def calculate_amounts(claims: list, monthly_salary: float, start_date: str, end_date: str) -> list:
    """计算各项请求金额明细"""
    work_info = calculate_work_years(start_date, end_date)
    daily_rate = monthly_salary / 21.75
    hourly_rate = daily_rate / 8

    results = []
    total = 0

    for claim in claims:
        item = {
            "description": claim.get("description", ""),
            "type": claim.get("type", ""),
            "amount": claim.get("amount", 0),
            "calculation": claim.get("period", ""),
        }

        # 自动计算常见类型
        ctype = claim.get("type", "")
        if ctype == "severance_n" and monthly_salary:
            item["calculation"] = f"月工资{monthly_salary}元 × {work_info['severance_months']}个月 = {monthly_salary * work_info['severance_months']:.0f}元"
            item["amount"] = monthly_salary * work_info["severance_months"]
        elif ctype == "severance_2n" and monthly_salary:
            item["calculation"] = f"月工资{monthly_salary}元 × {work_info['severance_months']}个月 × 2倍 = {monthly_salary * work_info['severance_2n_months']:.0f}元"
            item["amount"] = monthly_salary * work_info["severance_2n_months"]
        elif ctype == "double_salary" and monthly_salary:
            months_unpaid = claim.get("months", 0)
            item["calculation"] = f"月工资{monthly_salary}元 × {months_unpaid}个月 = {monthly_salary * months_unpaid:.0f}元"
            item["amount"] = monthly_salary * months_unpaid
        elif ctype == "annual_leave":
            days = claim.get("days", 0)
            extra = daily_rate * 2 * days  # 额外支付200%
            item["calculation"] = f"日工资{daily_rate:.2f}元 × 200% × {days}天 = {extra:.0f}元"
            item["amount"] = extra

        total += item["amount"]
        item["amount"] = round(item["amount"])
        results.append(item)

    return results, round(total)


def generate_arbitration_application(case: dict, amounts: list, total: int) -> str:
    """生成仲裁申请书"""
    work_info = calculate_work_years(case.get("start_date", ""), case.get("end_date", ""))

    # 构建仲裁请求
    claims_text = ""
    for i, item in enumerate(amounts, 1):
        claims_text += f"{'一' if i == 1 else '二' if i == 2 else '三' if i == 3 else '四' if i == 4 else '五' if i == 5 else str(i)}、{item['description']}{'人民币' if item['amount'] > 0 else ''}{item['amount']:,.0f}{'元' if item['amount'] > 0 else ''}；\n"

    claims_text += f"（以上金额合计：人民币{total:,.0f}元）"

    # 构建证据清单
    evidence_text = ""
    evidence_list = case.get("evidence_list", [])
    cn_nums = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十",
               "十一", "十二", "十三", "十四", "十五"]
    for i, ev in enumerate(evidence_list):
        num = cn_nums[i] if i < len(cn_nums) else str(i + 1)
        evidence_text += f"证据{num}：{ev['name']}（复印件）\n证明目的：{ev['purpose']}\n\n"

    # 事实与理由
    facts = case.get("facts", "")
    if not facts:
        facts = f"申请人于{case.get('start_date', 'XX年XX月XX日')}入职被申请人处，月工资{case.get('monthly_salary', 'XXXX')}元。{case.get('end_reason', '')}。"

    applicant_name = case.get("applicant_name", "XXX")
    applicant_gender = case.get("applicant_gender", "X")
    applicant_id = case.get("applicant_id", "XXXXXXXXXXXXXXXXXX")
    applicant_address = case.get("applicant_address", "XXXXXXXXXXXXXXXXXXXXX")
    applicant_phone = case.get("applicant_phone", "XXXXXXXXXXX")
    respondent_name = case.get("respondent_name", "XXXXXXXXXXX公司")
    respondent_code = case.get("respondent_code", "XXXXXXXXXXXXXXXXXX")
    respondent_address = case.get("respondent_address", "XXXXXXXXXXXXXXXXXXXXX")
    respondent_legal_rep = case.get("respondent_legal_rep", "XXX")
    respondent_phone = case.get("respondent_phone", "XXXXXXXXXXX")
    city = case.get("city", "XX")
    today = datetime.now().strftime("%Y年%m月%d日")

    template = f"""# 劳动人事争议仲裁申请书

**申请人**：{applicant_name}，性别：{applicant_gender}

身份证号：{applicant_id}

住址：{applicant_address}

电话：{applicant_phone}

**被申请人**：{respondent_name}

统一社会信用代码：{respondent_code}

住所地：{respondent_address}

法定代表人：{respondent_legal_rep}  职务：法定代表人

电话：{respondent_phone}

---

## 仲裁请求

{claims_text}

## 事实与理由

{facts}

{work_info['description'] if work_info['total_months'] > 0 else ''}

综上所述，被申请人的行为严重违反了《中华人民共和国劳动合同法》及相关劳动法律法规的规定，损害了申请人的合法权益。为维护申请人的合法权益，特向贵委申请仲裁，请依法裁决。

此致

{city}劳动人事争议仲裁委员会

**申请人**：{applicant_name}（签名）

{today}

---

## 证据清单

{evidence_text}
"""

    return template


def generate_evidence_list(case: dict) -> str:
    """生成证据清单"""
    evidence_list = case.get("evidence_list", [])
    cn_nums = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十",
               "十一", "十二", "十三", "十四", "十五"]

    lines = ["# 证据清单\n"]
    lines.append(f"申请人：{case.get('applicant_name', 'XXX')}\n")
    lines.append(f"被申请人：{case.get('respondent_name', 'XXX公司')}\n")
    lines.append("---\n")

    for i, ev in enumerate(evidence_list):
        num = cn_nums[i] if i < len(cn_nums) else str(i + 1)
        lines.append(f"**证据{num}**：{ev['name']}（复印件）")
        lines.append(f"- 证明目的：{ev['purpose']}")
        lines.append("")

    lines.append("---\n")
    lines.append("注：以上证据均为复印件，原件备查。")

    return "\n".join(lines)


def generate_amount_calculation(case: dict, amounts: list, total: int) -> str:
    """生成金额计算表"""
    work_info = calculate_work_years(case.get("start_date", ""), case.get("end_date", ""))
    monthly_salary = case.get("monthly_salary", 0)

    lines = ["# 金额计算表\n"]
    lines.append(f"申请人：{case.get('applicant_name', 'XXX')}\n")
    lines.append(f"被申请人：{case.get('respondent_name', 'XXX公司')}\n")
    lines.append("---\n")

    lines.append("## 基础信息\n")
    lines.append(f"| 项目 | 内容 |")
    lines.append(f"|------|------|")
    lines.append(f"| 入职日期 | {case.get('start_date', 'XX')} |")
    lines.append(f"| 离职日期 | {case.get('end_date', 'XX')} |")
    lines.append(f"| 工作时长 | 约{work_info.get('total_months', 0)}个月（约{work_info.get('years', 0)}年） |")
    lines.append(f"| 月工资标准 | ¥{monthly_salary:,.0f} |")
    lines.append(f"| 日工资标准 | ¥{monthly_salary / 21.75:,.2f} |")
    lines.append(f"| 时工资标准 | ¥{monthly_salary / 21.75 / 8:,.2f} |")
    lines.append("")

    lines.append("## 各项请求金额明细\n")
    lines.append("| 序号 | 请求事项 | 计算方式 | 金额(元) |")
    lines.append("|------|---------|---------|---------|")
    for i, item in enumerate(amounts, 1):
        lines.append(f"| {i} | {item['description']} | {item['calculation']} | {item['amount']:,.0f} |")
    lines.append(f"| **合计** | | | **{total:,.0f}** |")
    lines.append("")

    lines.append("## 经济补偿/赔偿金计算依据\n")
    lines.append(f"- 经济补偿月数：{work_info.get('severance_months', 0)}个月")
    lines.append(f"- 违法解除赔偿月数：{work_info.get('severance_2n_months', 0)}个月")
    lines.append(f"- 计算说明：{work_info.get('description', '')}")
    lines.append("")
    lines.append("> 注意：如月工资超过当地上年度职工月平均工资三倍，按三倍封顶计算，年限最高12年。")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="劳动仲裁申请书自动生成工具")
    parser.add_argument("--config", type=str, help="案件信息JSON配置文件路径")
    parser.add_argument("--output-dir", type=str, default="./output", help="输出目录")
    parser.add_argument("--applicant-name", type=str, default="", help="申请人姓名")
    parser.add_argument("--applicant-gender", type=str, default="", help="申请人性别")
    parser.add_argument("--applicant-id", type=str, default="", help="申请人身份证号")
    parser.add_argument("--applicant-address", type=str, default="", help="申请人住址")
    parser.add_argument("--applicant-phone", type=str, default="", help="申请人电话")
    parser.add_argument("--respondent-name", type=str, default="", help="被申请人单位名称")
    parser.add_argument("--respondent-code", type=str, default="", help="被申请人统一社会信用代码")
    parser.add_argument("--respondent-address", type=str, default="", help="被申请人地址")
    parser.add_argument("--respondent-legal-rep", type=str, default="", help="法定代表人姓名")
    parser.add_argument("--respondent-phone", type=str, default="", help="被申请人电话")
    parser.add_argument("--city", type=str, default="", help="所在城市")
    parser.add_argument("--start-date", type=str, default="", help="入职日期 YYYY-MM-DD")
    parser.add_argument("--end-date", type=str, default="", help="离职日期 YYYY-MM-DD")
    parser.add_argument("--end-reason", type=str, default="", help="离职/解除原因")
    parser.add_argument("--monthly-salary", type=float, default=0, help="月工资标准")
    parser.add_argument("--has-contract", action="store_true", help="是否签订劳动合同")
    parser.add_argument("--facts", type=str, default="", help="事实与理由")

    args = parser.parse_args()

    # 加载配置
    if args.config:
        with open(args.config, "r", encoding="utf-8") as f:
            case = json.load(f)
    else:
        case = {
            "applicant_name": args.applicant_name or "XXX",
            "applicant_gender": args.applicant_gender or "X",
            "applicant_id": args.applicant_id or "",
            "applicant_address": args.applicant_address or "",
            "applicant_phone": args.applicant_phone or "",
            "respondent_name": args.respondent_name or "",
            "respondent_code": args.respondent_code or "",
            "respondent_address": args.respondent_address or "",
            "respondent_legal_rep": args.respondent_legal_rep or "XXX",
            "respondent_phone": args.respondent_phone or "",
            "city": args.city or "XX",
            "start_date": args.start_date or "",
            "end_date": args.end_date or "",
            "end_reason": args.end_reason or "",
            "monthly_salary": args.monthly_salary or 0,
            "has_contract": args.has_contract,
            "claims": [],
            "facts": args.facts or "",
            "evidence_list": [],
        }

    # 确保关键字段存在
    case.setdefault("claims", [])
    case.setdefault("evidence_list", [])
    case.setdefault("facts", "")
    case.setdefault("monthly_salary", 0)

    # 计算金额
    amounts, total = calculate_amounts(case.get("claims", []), case.get("monthly_salary", 0),
                                         case.get("start_date", ""), case.get("end_date", ""))

    # 创建输出目录
    os.makedirs(args.output_dir, exist_ok=True)

    # 生成文档
    application = generate_arbitration_application(case, amounts, total)
    evidence_list_doc = generate_evidence_list(case)
    amount_table = generate_amount_calculation(case, amounts, total)

    # 写入文件
    app_path = os.path.join(args.output_dir, "仲裁申请书.md")
    evidence_path = os.path.join(args.output_dir, "证据清单.md")
    amount_path = os.path.join(args.output_dir, "金额计算表.md")

    with open(app_path, "w", encoding="utf-8") as f:
        f.write(application)
    with open(evidence_path, "w", encoding="utf-8") as f:
        f.write(evidence_list_doc)
    with open(amount_path, "w", encoding="utf-8") as f:
        f.write(amount_table)

    print(f"✅ 仲裁申请书已生成：{app_path}")
    print(f"✅ 证据清单已生成：{evidence_path}")
    print(f"✅ 金额计算表已生成：{amount_path}")
    print(f"📊 仲裁请求总金额：¥{total:,.0f}")
    print(f"📁 输出目录：{os.path.abspath(args.output_dir)}")


if __name__ == "__main__":
    main()
