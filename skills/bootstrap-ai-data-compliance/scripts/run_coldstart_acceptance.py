#!/usr/bin/env python3
"""四步冷启动工作流端到端验收。

用零售电商客服场景走完四步：intake → kb-build → model-generate+render → field-pack。
独立验证每步真实产物，不接受生产器自报通过。
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from common import safe_write_json

SCRIPT_DIR = Path(__file__).resolve().parent
FLOW = SCRIPT_DIR / "flow.py"


def run(command: list[str], cwd: Path | None = None) -> dict:
    env = dict(os.environ)  # 继承用户环境（含 AI_COMPLIANCE_KB_ROOT 等自定义变量）
    env.update({
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPYCACHEPREFIX": "/private/tmp/bootstrap_ai_compliance_pyc",
        "TMPDIR": "/private/tmp",
    })
    result = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True, check=False)
    return {"command": " ".join(str(c) for c in command), "returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr}


def flow(*args: str) -> list[str]:
    return [sys.executable, str(FLOW), *args]


def main() -> None:
    parser = argparse.ArgumentParser(description="四步冷启动工作流端到端验收")
    parser.add_argument("--target-root", type=Path, required=True, help="临时运行根目录")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    target = args.target_root.resolve()
    target.mkdir(parents=True, exist_ok=True)
    logs = []

    # 第一步：intake（创建→记录必填→收口）
    logs.append(run(flow("intake", "--target", str(target), "--question-set", "retail-ecommerce-customer-service", "--project-id", "CS-ACCEPT-001")))
    required_ids = ["BB-01", "BB-02", "BB-03", "BB-04", "DS-01", "DS-02", "DS-03", "MS-01", "MS-02", "MS-03", "MS-04", "CH-01", "CH-02", "CD-01", "CD-02", "CD-03", "TH-01", "TH-02", "TH-03"]
    answers = {
        "BB-01": "面向C端消费者的智能客服，覆盖售前/售后/物流/投诉",
        "BB-02": "AI处理80%常规咨询，高风险强制转人工",
        "BB-03": "平台C端注册用户，日均500万轮对话",
        "BB-04": "中国大陆为主，部分跨境涉及港澳",
        "DS-01": "历史对话记录+订单数据，平台自有",
        "DS-02": "用户协议+平台授权",
        "DS-03": "对话（个人信息）+订单手机号（敏感）",
        "MS-01": "通义千问Turbo主+文心一言备用",
        "MS-02": "官方API调用",
        "MS-03": "合同含数据安全条款，不用于训练",
        "MS-04": "退出后删除返还",
        "CH-01": "APP/小程序/H5",
        "CH-02": "售前/订单/售后/物流/投诉",
        "CD-01": "文本+图片+语音",
        "CD-02": "向量化检索增强",
        "CD-03": "按协议保留可删除",
        "TH-01": "超500元/食品安全/人身伤害转人工",
        "TH-02": "30秒转接闭环",
        "TH-03": "记录转接原因结果",
    }
    for qid in required_ids:
        logs.append(run(flow("intake-record", "--target", str(target), "--question-id", qid, "--answer", answers[qid])))
    logs.append(run(flow("intake-close", "--target", str(target))))
    intake_path = target / "ai_compliance/00_project/intake.json"
    intake_closed = intake_path.exists() and json.loads(intake_path.read_text(encoding="utf-8")).get("closed") is True

    # 第二步：kb-build
    logs.append(run(flow("kb-build", "--target", str(target))))
    kb_path = target / "ai_compliance/03_knowledge_base/kb_index.json"
    kb_created = kb_path.exists()

    # 第三步：model-generate + render
    logs.append(run(flow("model-generate", "--target", str(target))))
    model_path = target / "ai_compliance/05_model/industry-model.json"
    model_ok = model_path.exists() and "processMap" in json.loads(model_path.read_text(encoding="utf-8"))
    logs.append(run(flow("render", "--target", str(target))))
    process_svg = target / "ai_compliance/05_model/rendered/process-map.svg"
    dataflow_svg = target / "ai_compliance/05_model/rendered/data-flow-map.svg"
    report_html = target / "ai_compliance/05_model/rendered/评估报告.html"
    render_ok = process_svg.exists() and dataflow_svg.exists() and report_html.exists()

    # 第四步：field-pack
    logs.append(run(flow("field-pack", "--target", str(target), "--project-name", "智服通智能客服系统")))
    field_docs = sorted((target / "ai_compliance/06_field_pack").glob("*.docx")) if (target / "ai_compliance/06_field_pack").exists() else []
    field_ok = len(field_docs) == 7  # 信息调研表/风险识别表/访谈提纲/文件清单/数据资产盘点/现场核查/保密与授权

    checks = {
        "intake_created_and_closed": intake_closed,
        "kb_index_created": kb_created,
        "model_generated_with_process_map": model_ok,
        "render_svgs_and_report": render_ok,
        "field_pack_seven_documents": field_ok,
    }
    passed = all(checks.values())
    report = {
        "schema_version": "1.0",
        "command": "coldstart-acceptance",
        "passed": passed,
        "checks": checks,
        "target": str(target),
        "field_documents": [p.name for p in field_docs],
        "boundary": "四步端到端验收检查真实产物；评估结论仍须律师复核。",
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        safe_write_json(args.output, report, allow_update=True)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if passed else 5)


if __name__ == "__main__":
    main()
