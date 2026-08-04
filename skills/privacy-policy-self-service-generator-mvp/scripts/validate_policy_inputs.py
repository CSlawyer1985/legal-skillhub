#!/usr/bin/env python3
"""Validate structured product facts before drafting a privacy agreement."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = {
    "handler.name": "个人信息处理者名称",
    "handler.contact": "个人信息保护负责人或责任部门联系方式",
    "product.name": "产品或服务名称",
    "product.scope": "适用产品或服务范围",
    "product.tool_types": "工具类型或能力类型",
    "product.users": "适用个人信息主体类型",
    "functions": "业务功能清单",
    "rights.channels": "用户权利行使渠道",
    "security.measures": "个人信息安全保护措施",
    "storage.region": "个人信息存储地域",
    "storage.retention": "保存期限或期限确定方法",
    "third_parties.status": "第三方 SDK、插件或对外提供状态",
}

HIGH_RISK_FIELDS = {
    "sensitive_personal_information": "敏感个人信息处理说明",
    "minors": "未成年人个人信息处理说明",
    "cross_border": "跨境传输说明",
    "automated_decision": "自动化决策说明",
    "ai.training": "AI 训练或模型优化说明",
}


def get_path(data: dict[str, Any], path: str) -> Any:
    current: Any = data
    for part in path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current


def has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def validate(data: dict[str, Any]) -> dict[str, Any]:
    blocking_gaps = []
    warnings = []

    for path, label in REQUIRED_FIELDS.items():
        if not has_value(get_path(data, path)):
            blocking_gaps.append({"path": path, "label": label})

    for path, label in HIGH_RISK_FIELDS.items():
        value = get_path(data, path)
        if value in (True, "yes", "是", "存在") and not has_value(get_path(data, path + "_details")):
            warnings.append({"path": path, "label": label, "message": "高风险事项存在，但缺少详细规则"})

    functions = get_path(data, "functions")
    if isinstance(functions, list):
        for index, function in enumerate(functions, start=1):
            if not isinstance(function, dict):
                warnings.append({"path": f"functions[{index}]", "message": "业务功能应使用对象结构描述"})
                continue
            for key in ("name", "personal_information", "purpose", "necessity"):
                if not has_value(function.get(key)):
                    warnings.append({"path": f"functions[{index}].{key}", "message": "业务功能描述不完整"})

    tool_types = get_path(data, "product.tool_types")
    if isinstance(tool_types, list):
        creative_ai_markers = {"文生视频", "图生视频", "文生图", "图生图", "视频编辑", "图片编辑", "数字人", "语音生成"}
        if creative_ai_markers.intersection(set(tool_types)) and not has_value(get_path(data, "ai.creation_inputs")):
            warnings.append({"path": "ai.creation_inputs", "message": "AI 创作工具应说明输入材料类型"})
        if creative_ai_markers.intersection(set(tool_types)) and not has_value(get_path(data, "ai.creation_outputs")):
            warnings.append({"path": "ai.creation_outputs", "message": "AI 创作工具应说明输出内容类型"})

    return {
        "passed": not blocking_gaps,
        "blocking_gaps": blocking_gaps,
        "warnings": warnings,
    }


def self_test() -> int:
    sample = {
        "handler": {"name": "示例公司", "contact": "privacy@example.com"},
        "product": {"name": "示例产品", "scope": "移动应用", "tool_types": ["文生图"], "users": ["注册用户"]},
        "functions": [
            {
                "name": "账号注册",
                "personal_information": ["手机号码"],
                "purpose": "创建账号",
                "necessity": "必要",
            }
        ],
        "rights": {"channels": ["App 设置", "邮箱"]},
        "security": {"measures": ["加密传输", "访问控制"]},
        "storage": {"region": "中国境内", "retention": "账号存续期间"},
        "third_parties": {"status": "存在"},
        "ai": {"creation_inputs": ["文本提示词"], "creation_outputs": ["图片"]},
    }
    result = validate(sample)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate privacy agreement product facts.")
    parser.add_argument("input", nargs="?", help="Path to a JSON file with product facts.")
    parser.add_argument("--self-test", action="store_true", help="Run a built-in smoke test.")
    args = parser.parse_args()

    if args.self_test:
        return self_test()
    if not args.input:
        print("Provide a JSON input file or use --self-test.", file=sys.stderr)
        return 2

    path = Path(args.input)
    data = json.loads(path.read_text(encoding="utf-8"))
    result = validate(data)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
