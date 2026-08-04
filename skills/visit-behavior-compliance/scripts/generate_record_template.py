#!/usr/bin/env python3
"""
拜访记录模板生成脚本
输出 Markdown 格式的标准化拜访记录模板，并可填充示例行
"""

import sys
import datetime

def generate_record_template(fill_example=True, scenario=None):
    """
    生成拜访记录模板

    Args:
        fill_example: 是否填充示例行
        scenario: 可选，基于特定场景填充示例
    """

    output = []
    output.append("## 第三章：拜访记录模板\n")
    output.append("### 模板结构\n")

    # 模板表头
    output.append("| 字段 | 填写说明 | 是否必填 |")
    output.append("|------|---------|---------|")
    output.append("| 拜访日期 | 格式：YYYY-MM-DD（如 2024-03-15） | ✅ 必填 |")
    output.append("| 拜访时间 | 开始时间 - 结束时间（如 14:00-15:30） | ✅ 必填 |")
    output.append("| 医院名称 | 全称（如：XX市第一人民医院） | ✅ 必填 |")
    output.append("| 科室 | 具体科室（如：心血管内科）| ✅ 必填 |")
    output.append("| 拜访对象姓名 | 医生/药剂师姓名 | ✅ 必填 |")
    output.append("| 拜访对象职称 | 如：主任医师、副主任医师 | ✅ 必填 |")
    output.append("| 沟通主题 | 本次拜访的核心学术内容 | ✅ 必填 |")
    output.append("| 涉及行为灯色 | 🔴红灯 / 🟡黄灯 / 🟢绿灯（可多选）| ✅ 必填 |")
    output.append("| 是否事前报批 | 是 / 否 / 不适用 | ✅ 必填 |")
    output.append("| 审批单号 | 如已报批，填写系统审批编号 | 有批则填 |")
    output.append("| 费用发生情况 | 如有餐饮/礼品，注明项目及金额 | 有则填 |")
    output.append("| 客户反馈 | 医生主要反馈/关切要点 | 建议填写 |")
    output.append("| 不良反应信息 | 是否收集到不良反应（是/否），如有请注明 | ✅ 必填 |")
    output.append("| 后续跟进计划 | 下次拜访计划/需要支持的事项 | 建议填写 |")
    output.append("| 代表签名 | 填报人签名（电子/手写）| ✅ 必填 |")
    output.append("| 提交时间 | 记录提交系统的时间（需在拜访后24小时内）| ✅ 必填 |")

    output.append("")

    if fill_example:
        output.append("---\n")
        output.append("### 填写示例\n")
        output.append("> ⚠️ 以下为示例数据，实际使用时请替换为真实信息\n")

        today = datetime.date.today().strftime("%Y-%m-%d")

        if scenario and "指南" in scenario:
            # 赠送指南场景示例
            output.append("| 字段 | 填写内容 |")
            output.append("|------|---------|")
            output.append(f"| 拜访日期 | {today} |")
            output.append("| 拜访时间 | 14:30-15:10 |")
            output.append("| 医院名称 | XX市中心医院 |")
            output.append("| 科室 | 心血管内科 |")
            output.append("| 拜访对象姓名 | 王XX（已脱敏） |")
            output.append("| 拜访对象职称 | 主任医师 |")
            output.append("| 沟通主题 | 《2024中国高血压防治指南》更新要点介绍 + 某降压药最新临床数据 |")
            output.append("| 涉及行为灯色 | 🟡黄灯（赠送学术资料）+ 🟢绿灯（学术信息传递）|")
            output.append("| 是否事前报批 | 是（资料赠送已在CRM备案，备案号：xxxxxxxx）|")
            output.append("| 审批单号 | RC-2024-03-xxxx |")
            output.append("| 费用发生情况 | 《2024高血压防治指南》1本，价格98元，公司承担 |")
            output.append("| 客户反馈 | 对指南中SGLT2i适应症扩展部分感兴趣，希望了解更多真实世界数据 |")
            output.append("| 不良反应信息 | 否，未收集到不良反应报告 |")
            output.append("| 后续跟进计划 | 下周发送SGLT2i心衰领域RCT汇总文献（电子版）|")
            output.append("| 代表签名 | 张XX（电子签名）|")
            output.append(f"| 提交时间 | {today} 17:30 |")
        else:
            # 默认示例（纯学术拜访）
            output.append("| 字段 | 填写内容 |")
            output.append("|------|---------|")
            output.append(f"| 拜访日期 | {today} |")
            output.append("| 拜访时间 | 09:00-09:45 |")
            output.append("| 医院名称 | XX省人民医院 |")
            output.append("| 科室 | 内分泌科 |")
            output.append("| 拜访对象姓名 | 李XX（已脱敏）|")
            output.append("| 拜访对象职称 | 副主任医师 |")
            output.append("| 沟通主题 | 某降糖药在T2DM合并CKD患者中的安全性数据介绍 |")
            output.append("| 涉及行为灯色 | 🟢绿灯（学术信息传递）|")
            output.append("| 是否事前报批 | 不适用（纯学术拜访，无费用发生）|")
            output.append("| 审批单号 | 无 |")
            output.append("| 费用发生情况 | 无 |")
            output.append("| 客户反馈 | 关注eGFR<30患者的使用数据，希望获得最新说明书及文献 |")
            output.append("| 不良反应信息 | 否 |")
            output.append("| 后续跟进计划 | 提供eGFR<30亚组分析文献，预约下周二再次拜访 |")
            output.append("| 代表签名 | 陈XX（电子签名）|")
            output.append(f"| 提交时间 | {today} 11:00 |")

    output.append("")
    output.append("---")
    output.append("*合规提示：拜访记录须在拜访结束后24小时内提交至CRM系统，确保数据真实、完整、可追溯。*")

    return '\n'.join(output)

def main():
    fill_example = True
    scenario = None

    if len(sys.argv) > 1:
        scenario = sys.argv[1]
    if len(sys.argv) > 2:
        fill_example = sys.argv[2].lower() != 'false'

    result = generate_record_template(fill_example, scenario)
    print(result)

if __name__ == '__main__':
    main()
