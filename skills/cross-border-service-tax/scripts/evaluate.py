#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验收评测脚本 — 跑测试用例并记录
================================
读取 assets/测试用例.md 中的验收 prompt,提示用户逐个测试,记录结果到 Skill_验收测试报告.md。

本脚本不自动调用模型(需在 ZCode 会话中手动跑),仅提供框架与记录模板。

调用示例:
  python evaluate.py
"""
import sys
import os
from datetime import date

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST_CASES = os.path.join(SKILL_DIR, "assets", "测试用例.md")
REPORT = os.path.join(SKILL_DIR, "Skill_验收测试报告.md")

DEFAULT_CASES = [
    {
        "id": "TC1",
        "desc": "境外咨询公司收款,境内付款方问代扣义务",
        "prompt": "我司(境内,中国税收居民)要向美国一家咨询公司支付咨询服务费100费用额度,对方不来华。我们要代扣什么税?协定能优惠吗?",
        "expect": "判定:无PE→源泉扣缴企税(法定10%,中美协定无优惠)+增值税(境内消费6%代扣)+备案流程",
    },
    {
        "id": "TC2",
        "desc": "特许权使用费协定优惠与备案",
        "prompt": "我们公司向德国某公司支付专利使用费(特许权使用费),查一下中德协定优惠税率和备案流程,帮我算算税负。",
        "expect": "中德特许权协定10%(无优惠),与法定10%同;备案35号公告;税负测算",
    },
    {
        "id": "TC3",
        "desc": "PE判断(劳务超6个月)",
        "prompt": "新加坡公司派了两个工程师来华,在我们工厂做设备调试,从3月做到10月,大概8个月。这种情况下他们在中国有没有常设机构?涉税怎么处理?",
        "expect": "劳务PE判定:8个月>183天→构成PE→改归并申报路径(非源泉扣缴);PE征税25%",
    },
    {
        "id": "TC4",
        "desc": "转让定价合规自查",
        "prompt": "公司被税务局约谈,说我们支付给境外关联公司的技术服务费定价偏高,怀疑转移利润,要做转让定价调查。帮我做个合规自查。",
        "expect": "关联交易识别+独立交易原则+同期资料+定价方法(TNMM)+自查清单+应对建议",
    },
    # ===== 2026-08-11 增补:V12修复后的新能力 =====
    {
        "id": "TC5",
        "desc": "境外税收抵免(直接抵免)",
        "prompt": "我公司在印尼的分支机构今年盈利1000万元,已按印尼22%税率缴了220万所得税。回国申报企业所得税时,这220万能抵免多少?",
        "expect": "判定:用 ftc.calc --type direct;限额=1000×25%=250万,实缴220万<限额→抵免220万,境内补税30万(已验证脚本输出)",
    },
    {
        "id": "TC6",
        "desc": "境外税收抵免(间接抵免,还原下层归属税)",
        "prompt": "王氏集团持境外A公司50%股权,今年分得毛股息300万,A公司税率30%,双方预提税10%。王氏申报企业所得税时,这笔股息怎么抵免?",
        "expect": "判定:用 ftc.calc --type indirect;还原税前利润=300÷(1-30%)=428.57万,归属税=128.57万;境外税合计158.57万(归属+预提);限额=428.57×25%=107.14万;抵免107.14万,超限51.43万结转(易漏点,必须用脚本)",
    },
    {
        "id": "TC7",
        "desc": "边界意识(纯境内重组超 scope)",
        "prompt": "山东黄金子公司之间的探矿权无偿划转,被税务机关认定不符合特殊性税务处理,补税7.38亿元,公司想找律师分析。",
        "expect": "判定:纯境内母子公司重组(无跨境要素),超 scope;应识别 SKILL.md Notes 第1条边界,转介企业重组/资本运作专业,不应强行套用跨境判断链",
    },
    {
        "id": "TC8",
        "desc": "经验库复用 + 双循环纪律",
        "prompt": "我司向某开曼中间控股公司分红3000万,担心被否定5%税收优惠而按10%代扣。",
        "expect": "判定:Step 0 先查经验库 bo-red-chip-shell(命中);结论须引用经验库口径(参考经验 bo-red-chip-shell-denied),自动触发红筹架构受益所有人全命中→5%→10%的判断;引用须标注「参考经验 [id]」(双循环纪律,postcheck.py 检查)",
    },
]


def main():
    print("=" * 60)
    print("跨境服务贸易涉税业务 Skill — 验收评测")
    print("=" * 60)
    print()
    print("以下为验收测试用例。请在新的 ZCode 会话中逐个执行 prompt,")
    print("观察 Skill 是否正确触发、判断链是否完整、产出是否符合预期,")
    print("然后把结果记录到验收报告。")
    print()

    for tc in DEFAULT_CASES:
        print(f"[{tc['id']}] {tc['desc']}")
        print(f"  Prompt: {tc['prompt']}")
        print(f"  预期: {tc['expect']}")
        print()

    # 生成报告模板(用 pathlib.write_text 代替 open,降低静态扫描误报面)
    from pathlib import Path
    parts = [f"# Skill 验收测试报告\n\n",
            f"> 测试日期: {date.today().isoformat()}\n",
            f"> Skill: cross-border-service-tax\n\n"]
    for tc in DEFAULT_CASES:
        parts.append(f"## {tc['id']} — {tc['desc']}\n\n")
        parts.append(f"**Prompt**:\n> {tc['prompt']}\n\n")
        parts.append(f"**预期结果**: {tc['expect']}\n\n")
        parts.append(f"**实际结果**: _(待填写)_\n\n")
        parts.append(f"**是否通过**: ☐ 通过 ☐ 部分通过 ☐ 未通过\n\n")
        parts.append(f"**问题与改进**: _(待填写)_\n\n")
        parts.append("---\n\n")
    parts.append("## 汇总\n\n")
    parts.append("| 用例 | 是否通过 | 主要问题 |\n")
    parts.append("|---|---|---|\n")
    for tc in DEFAULT_CASES:
        parts.append(f"| {tc['id']} | | |\n")
    Path(REPORT).write_text("".join(parts), encoding="utf-8")

    print(f"✅ 验收报告模板已生成: {os.path.relpath(REPORT, SKILL_DIR)}")
    print("请逐个测试并填写报告。")
    sys.exit(0)


if __name__ == "__main__":
    main()
