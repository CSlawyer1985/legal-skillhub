#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合同审查审批卡片生成模块
生成飞书交互卡片 JSON，用户点击按钮直接跳转到审批表单

由于飞书开放平台暂不支持 AI Agent 通过 API 自动创建审批实例，
本模块生成带跳转按钮的卡片，用户点击后跳转到审批表单页面手动填写提交。
"""

import json
import argparse
from typing import Dict, Any

# ============== 审批配置 ==============
APPROVAL_CONFIG = {
    "definition_code": "92398274-D3EB-4F0D-AC2A-994C1340C361",
    "form_url": "https://appr.mingdao.com/approvalCenter/approval/detail?processCode=92398274-D3EB-4F0D-AC2A-994C1340C361",
}


def generate_card_json(
    contract_name: str = "",
    contract_type: str = "其他",
    risk_level: str = "🟢低",
    risk_count: int = 0,
    suggestion: str = "通过",
) -> Dict[str, Any]:
    """
    生成飞书审批卡片 JSON
    返回可直接使用的卡片数据结构
    """
    card = {
        "msg_type": "interactive",
        "card": {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": "📋 合同审查完成"
                },
                "template": "blue"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": (
                            f"**合同名称：** {contract_name}\n"
                            f"**风险等级：** {risk_level}\n"
                            f"**风险数量：** {risk_count} 处\n"
                            f"**处理建议：** {suggestion}"
                        )
                    }
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "点击下方按钮，跳转到审批表单，填写并提交即可。"
                    }
                },
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {
                                "tag": "plain_text",
                                "content": "🚀 立即发起审批"
                            },
                            "type": "primary",
                            "url": APPROVAL_CONFIG["form_url"]
                        }
                    ]
                }
            ]
        }
    }
    return card


def print_card_json(**kwargs):
    """打印卡片 JSON 到 stdout（供 skill 脚本调用）"""
    card = generate_card_json(**kwargs)
    print(json.dumps(card, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="合同审查审批卡片生成工具")
    parser.add_argument("--contract_name", required=True, help="合同名称")
    parser.add_argument("--contract_type", default="其他", help="合同类型")
    parser.add_argument("--risk_level", default="🟢低", help="风险等级")
    parser.add_argument("--risk_count", type=int, default=0, help="风险数量")
    parser.add_argument("--suggestion", default="通过", help="处理建议")
    args = parser.parse_args()

    print_card_json(
        contract_name=args.contract_name,
        contract_type=args.contract_type,
        risk_level=args.risk_level,
        risk_count=args.risk_count,
        suggestion=args.suggestion,
    )


if __name__ == "__main__":
    main()
