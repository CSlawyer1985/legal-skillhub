#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一键自检脚本（self_check.py）——移植部署验收健康检查。

检查四层：
  1. 包结构完整性：SKILL.md、治理文件、九个业务脚本、知识文件、模板与数据齐备；
  2. 数据文件有效性：assets/data/*.json 与法条全文库九部全部可解析；
  3. 脚本冒烟测试：九个业务脚本实际运行一条典型命令，校验退出码与JSON信封；
  4. 触发测试与日历：trigger_tests.json用例四要素齐备；holiday_calendar.json
     覆盖当年与下一年度。

调用方式：
  python scripts/self_check.py [--out 报告输出路径]

统一接口规范：
  - 仅依赖Python标准库；支持--help；
  - 输出JSON信封：{status, error_code, message, data}；
  - 退出码：0成功（HEALTHY或DEGRADED）/ 1参数错误 / 3自检失败（BROKEN）。

边界说明：
  - 本脚本只做本地静态与冒烟检查；触发测试用例的实际模型运行与输出质量评估
    （platform_adapters.md第五节双跑对照测试）仍须在目标平台加载Skill后人工执行；
  - 冒烟测试用固定输入，不读写案件工作区，不产生任何案件数据残留。
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import date

SCRIPT_NAME = "self_check"
SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 结构检查清单（相对路径 → 说明）
STRUCTURE_CHECKS = [
    ("SKILL.md", "主控路由文件"),
    ("README.md", "包概览（八节）"),
    ("使用指引.md", "上手指引（六节）"),
    ("CHANGELOG.md", "变更日志"),
    ("SBOM.json", "供应链组件清单"),
    ("LICENSE_NOTES.md", "授权声明"),
    ("_meta.json", "平台元数据（单一事实源）"),
    ("_icon.png", "图标 512×512"),
    ("references/line0_律师工作模式.md", "律师工作模式"),
    ("references/line1_家属接待线.md", "线 1 工作线文件"),
    ("references/line5_强制措施线.md", "线 5 工作线文件"),
    ("references/line8_文书生成线.md", "线 8 工作线文件"),
    ("references/S1_接待技能库.md", "S1 技能库"),
    ("references/S5_文书技能库.md", "S5 技能库"),
    ("references/S8_举证质证技能库.md", "S8 技能库"),
    ("references/quality_checklist.md", "质检 47 条"),
    ("references/FAQ.md", "常见问题与反模式"),
    ("references/prohibition_index.md", "禁止项索引"),
    ("references/service_config.md", "服务配置与进程表"),
    ("references/evidence_guide/README.md", "证据指引库索引"),
    ("references/crime_distinction/README.md", "罪名辨析库索引"),
    ("assets/schemas/case_status_schema.json", "案件状态 Schema"),
    ("assets/config/freshness_policy.json", "时效校验策略（参数外置）"),
    ("assets/data/registry_summary.json", "精简法条注册表"),
    ("assets/data/law_effectiveness.json", "法条效力库"),
    ("assets/examples/trigger_tests.json", "触发测试用例集"),
    ("assets/examples/feature_matrix.json", "功能×发布形态矩阵"),
    ("assets/examples/demo_case", "示例案件包"),
    ("assets/examples/output_examples", "输出与接口示例"),
    ("localization/local_court_practices.md", "本地化配置模板"),
    ("localization/local_bail_practice.md", "取保实践配置模板"),
]

SCRIPT_NAMES = [
    "case_state_manager.py", "intent_classifier.py", "limit_calculator.py",
    "law_validator.py", "law_text_lookup.py", "crime_lookup.py",
    "sentencing_estimator.py", "evidence_contradiction_checker.py",
    "pii_sanitizer.py", "case_number_validator.py",
    "punctuation_check.py", "quality_checker.py", "md2docx_formal.py",
    "init_case_workspace.py", "build_release.py", "citation_audit.py",
    "freshness_check.py", "backup_manager.py", "holiday_update.py",
    "self_check.py",
]

# 冒烟测试命令（固定输入；case_state_manager以--help验证可执行，不写案件工作区）
SMOKE_TESTS = [
    ("limit_calculator.py",
     ["--type", "detention", "--start_date", "2026-01-05", "--subtype", "general"],
     "ok"),
    ("crime_lookup.py", ["--crime", "盗窃罪"], "ok"),
    ("law_text_lookup.py", ["--law", "刑诉法", "--article", "91"], "ok"),
    ("law_text_lookup.py", ["--law", "量刑指导意见二", "--search", "组织卖淫"], "ok"),
    ("law_text_lookup.py", ["--law", "量刑指导意见", "--article", "四（一）"], "ok"),
    ("law_validator.py", ["--law", "刑法", "--article", "65"], "ok"),
    ("pii_sanitizer.py",
     ["--text", "当事人张三测试，身份证号330226199001011234，办案民警李四承办。"],  # cdiw-pii-fixture
     "ok"),
    ("sentencing_estimator.py",
     ["--crime", "盗窃罪", "--base_sentence", "36",
      "--factors", '[{"id":"surrender","value":0.30}]'],
     "ok"),
    ("case_number_validator.py", ["--number", "（2026）浙0203刑初123号"], "ok"),
    ("intent_classifier.py", ["--text", "帮我计算刑事拘留期限"], "ok"),
    ("evidence_contradiction_checker.py",
     ["--text", "证人甲称2026年3月1日见到当事人；监控显示2026年3月1日当事人在外地。"],
     "ok"),
    ("case_state_manager.py", ["--help"], None),  # --help无JSON信封，退出码0即可
    # ── 2.1.0 新增 8 脚本 ──
    ("punctuation_check.py", ["--path", "README.md"], "ok"),
    ("quality_checker.py", ["--l10n"], None),
    ("citation_audit.py", ["--output", "README.md",
                           "--ledger", "assets/examples/demo_case/citation_ledger.jsonl"], None),
    ("freshness_check.py", [], None),
    ("backup_manager.py", ["--help"], None),
    ("build_release.py", ["--help"], None),
    ("md2docx_formal.py", ["--help"], None),
    ("init_case_workspace.py", ["--help"], None),
]

# 法条全文库清单：单一事实源为 assets/data/law_texts/registry.json（注册表）；
# 注册表缺失/损坏时回退为空清单并在数据文件有效性检查中报错。


def resolve_law_texts_dir():
    """法条全文库目录三级解析，与 law_text_lookup.py 同口径（8.8.4）。

    ① 环境变量 CDIW_LAW_PACK_DIR → ② 同级目录 cdiw-law-pack/
    → ③ 旧版相对路径 <主包>/assets/data/law_texts/
    """
    cands = []
    env = os.environ.get("CDIW_LAW_PACK_DIR")
    if env:
        p = env if env.rstrip("/").endswith("law_texts") \
            else os.path.join(env, "assets", "data", "law_texts")
        cands.append(("env:CDIW_LAW_PACK_DIR", p))
    cands.append(("sibling:cdiw-law-pack", os.path.join(
        os.path.dirname(SKILL_ROOT), "cdiw-law-pack", "assets", "data", "law_texts")))
    cands.append(("legacy:<主包>/assets/data/law_texts",
                  os.path.join(SKILL_ROOT, "assets", "data", "law_texts")))
    for level, path in cands:
        if os.path.isfile(os.path.join(path, "registry.json")):
            return path, level
    return None, None


LAW_TEXT_DIR, LAW_TEXT_LEVEL = resolve_law_texts_dir()


def load_law_registry():
    if LAW_TEXT_DIR is None:
        return None
    reg_path = os.path.join(LAW_TEXT_DIR, "registry.json")
    try:
        with open(reg_path, "r", encoding="utf-8") as f:
            reg = json.load(f)
        return [law["file"] for law in reg.get("laws", []) if law.get("file")]
    except (OSError, ValueError):
        return None


LAW_TEXT_FILES = load_law_registry()


def check_structure(results):
    missing = []
    for rel, desc in STRUCTURE_CHECKS:
        if not os.path.exists(os.path.join(SKILL_ROOT, rel)):
            missing.append("%s（%s）" % (rel, desc))
    for s in SCRIPT_NAMES:
        rel = os.path.join("scripts", s)
        if not os.path.exists(os.path.join(SKILL_ROOT, rel)):
            missing.append(rel)
    results["结构完整性"] = {
        "通过": not missing,
        "问题": ("缺失文件：%s" % "、".join(missing)) if missing else None,
    }


def check_json_files(results):
    bad = []
    notes = []
    total = 0
    data_dir = os.path.join(SKILL_ROOT, "assets", "data")
    targets = [os.path.join(data_dir, f) for f in sorted(os.listdir(data_dir))
               if f.endswith(".json")]
    targets += [os.path.join(SKILL_ROOT, "SBOM.json")]

    # 法条全文库：按三级路径挂载；未挂载按 DEGRADED 注记，不阻断
    if LAW_TEXT_DIR is None:
        notes.append("法条数据包（cdiw-law-pack）未挂载——条文原文核对降级「待核实」，"
                     "效力校验／期限／文书／罪名辨析（非敏感条目）不受影响；"
                     "挂载方式见 PACK.md 三级路径")
        law_files = []
    elif LAW_TEXT_FILES is None:
        bad.append("法条全文库注册表缺失或损坏：%s" % os.path.join(LAW_TEXT_DIR, "registry.json"))
        law_files = []
    else:
        law_files = LAW_TEXT_FILES
        notes.append("法条数据包已挂载（解析层级：%s），法规 %d 部"
                     % (LAW_TEXT_LEVEL, len(law_files)))
        targets.append(os.path.join(LAW_TEXT_DIR, "registry.json"))
        targets += [os.path.join(LAW_TEXT_DIR, f) for f in law_files]

    for path in targets:
        total += 1
        try:
            with open(path, "r", encoding="utf-8") as f:
                json.load(f)
        except (OSError, ValueError) as exc:
            bad.append("%s：%s" % (os.path.relpath(path, SKILL_ROOT), exc))

    if LAW_TEXT_DIR and law_files:
        missing_law = [f for f in law_files
                       if not os.path.exists(os.path.join(LAW_TEXT_DIR, f))]
        if missing_law:
            bad.append("法条全文库缺失（registry已登记但文件不存在）：%s" % "、".join(missing_law[:10]))
        actual_law = {f for f in os.listdir(LAW_TEXT_DIR)
                      if f.endswith(".json") and f != "registry.json"}
        unregistered = sorted(actual_law - set(law_files))
        if unregistered:
            bad.append("法条全文库未注册文件（须在registry.json登记方可进入检索链）：%s"
                       % "、".join(unregistered[:10]))

    results["数据文件有效性"] = {
        "通过": not bad,
        "检查数": total,
        "问题": "；".join(bad) if bad else None,
        "注记": notes,
        "法条包挂载": {"mounted": LAW_TEXT_DIR is not None,
                       "resolved_by": LAW_TEXT_LEVEL,
                       "dir": LAW_TEXT_DIR},
    }


def check_scripts(results):
    details = []
    all_ok = True
    for script, extra_args, expect_status in SMOKE_TESTS:
        cmd = [sys.executable, os.path.join(SKILL_ROOT, "scripts", script)] + extra_args
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30,
                                  cwd=SKILL_ROOT)
        except subprocess.TimeoutExpired:
            details.append({"脚本": script, "结果": "超时（>30秒）"})
            all_ok = False
            continue
        ok = proc.returncode == 0
        note = "退出码%d" % proc.returncode
        if ok and expect_status:
            try:
                env = json.loads(proc.stdout)
                if env.get("status") != expect_status:
                    ok = False
                    note = "JSON信封status=%s（预期%s）" % (env.get("status"), expect_status)
            except ValueError:
                ok = False
                note = "输出非合法JSON"
        details.append({"脚本": script, "结果": "通过" if ok else note})
        if not ok:
            all_ok = False
    results["脚本冒烟测试"] = {"通过": all_ok, "明细": details}


def check_trigger_tests(results):
    path = os.path.join(SKILL_ROOT, "assets", "examples", "trigger_tests.json")
    problems = []
    count = 0
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as exc:
        results["触发测试用例"] = {"通过": False, "问题": "文件读取失败：%s" % exc}
        return
    for tc in data.get("test_cases", []):
        count += 1
        # input对边界/不触发/急停等类型用例可缺省（仅prompt触发），三要素必填
        for field in ("prompt", "expected", "assertions"):
            if not tc.get(field):
                problems.append("用例%s缺%s字段" % (tc.get("id"), field))
    if count == 0:
        problems.append("用例数为0")
    results["触发测试用例"] = {
        "通过": not problems,
        "用例数": count,
        "问题": "；".join(problems) if problems else None,
        "提示": "本项仅校验用例文件四要素齐备；实际触发运行与输出质量评估须在目标平台"
                "加载Skill后按platform_adapters.md第五节双跑对照测试人工执行（建议通过率≥80%）",
    }


def check_holiday_calendar(results):
    path = os.path.join(SKILL_ROOT, "assets", "data", "holiday_calendar.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as exc:
        results["节假日日历覆盖"] = {"通过": False, "问题": "文件读取失败：%s" % exc}
        return
    years = set(data.get("years", {}).keys())
    today = date.today()
    this_year = str(today.year)
    next_year = str(today.year + 1)
    problems = []
    # 当年数据必须齐备；下一年度数据按国务院发布节奏（通常11月）于当年10月起方要求更新
    if this_year not in years:
        problems.append("缺少%d年度数据——当年期限顺延计算将降级，请立即更新" % today.year)
    elif next_year not in years and today.month >= 10:
        problems.append("缺少%d年度数据（国务院通知已发布窗口期），请运行"
                        "scripts/holiday_update.py或按文件内update_rule更新" % (today.year + 1))
    results["节假日日历覆盖"] = {
        "通过": not problems,
        "已覆盖年度": sorted(years),
        "问题": "；".join(problems) if problems else None,
        "提示": "节假日数据覆盖以当年为准；下一年度数据待国务院办公厅通知发布后"
                "（通常每年11月）按update_rule更新",
    }


def main():
    parser = argparse.ArgumentParser(
        prog=SCRIPT_NAME,
        description="一键自检：包结构＋数据文件＋九脚本冒烟＋触发用例与日历覆盖，输出健康报告。"
                    "仅做本地检查，触发测试的实际模型运行须按platform_adapters.md双跑对照执行。",
        epilog="调用示例：\n  python scripts/self_check.py\n  python scripts/self_check.py --out 自检报告.json",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", help="健康报告输出文件路径（可选，默认仅打印）")
    args = parser.parse_args()

    results = {}
    check_structure(results)
    check_json_files(results)
    check_scripts(results)
    check_trigger_tests(results)
    check_holiday_calendar(results)

    failed = [k for k, v in results.items() if not v["通过"]]
    degraded_only = set(failed) <= {"节假日日历覆盖"}  # 日历缺口属降级不属阻断
    law_mounted = LAW_TEXT_DIR is not None
    if not failed:
        verdict = "HEALTHY" if law_mounted else "DEGRADED"
        message = ("自检通过：结构、数据、20 脚本、用例、日历六项全部健康，法条包已挂载"
                   if law_mounted else
                   "自检通过：六项全部健康；法条数据包未挂载——条文原文核对降级「待核实」，"
                   "其余功能不受影响（挂载方式见 PACK.md 三级路径）")
    elif degraded_only:
        verdict = "DEGRADED"
        message = "自检基本通过：仅节假日日历覆盖缺口（降级运行，不影响核心计算）"
        if not law_mounted:
            message += "；法条数据包未挂载，原文核对降级「待核实」"
    else:
        verdict = "BROKEN"
        message = "自检未通过：%s——修复后再行部署" % "、".join(failed)

    data = {"verdict": verdict,
            "checked_at": date.today().isoformat(),
            "skill_root": SKILL_ROOT,
            "script_count": len(SCRIPT_NAMES),
            "law_pack": {"mounted": law_mounted, "resolved_by": LAW_TEXT_LEVEL,
                         "dir": LAW_TEXT_DIR},
            "summary": {k: ("通过" if v["通过"] else "未通过") for k, v in results.items()},
            "details": results,
            "next_step": ("触发测试的实际模型运行与输出质量评估：在目标平台加载Skill后"
                          "按assets/examples/trigger_tests.json逐条执行，"
                          "红线用例组 100%、其余 ≥80% 方可投产"
                          if verdict != "BROKEN" else "先修复上述未通过项，再重新运行self_check.py")}
    out_text = json.dumps({"status": "ok" if verdict != "BROKEN" else "error",
                           "error_code": None if verdict != "BROKEN" else "ERR_SELF_CHECK_FAILED",
                           "message": message, "data": data},
                          ensure_ascii=False, indent=2)
    if args.out:
        try:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(out_text)
        except OSError as exc:
            print(json.dumps({"status": "error", "error_code": "ERR_IO",
                              "message": "报告写入失败：%s" % exc, "data": None},
                             ensure_ascii=False, indent=2))
            sys.exit(2)
    print(out_text)
    sys.exit(0 if verdict != "BROKEN" else 3)


if __name__ == "__main__":
    main()
