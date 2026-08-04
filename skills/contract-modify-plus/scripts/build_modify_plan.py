#!/usr/bin/env python3
"""生成 modify-plan.json 骨架。

给定合同文本，按 Playbook 类型输出一个待填的 modify-plan.json 模板，
便于在对话中快速填充 findings。也可在与用户确认分析后由 AI 直接产出完整 plan。

本骨架对应三方法论融合的修改逻辑：
- 《三观四步法（第五版）》：view 字段（macro/meso/micro）承载三观视角
- 《完美的合同（第四版）》：quality_dim（inner/outer/layout）+ module（五大模块）
- 《合同审查与修改实务》（杨司和2022）：action（delete/insert/replace/comment = 增删改调）

用法：
    python3 build_modify_plan.py --name "XXX合同" --role 甲方 --type 买卖 \
        --out modify-plan.json
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description="生成 modify-plan.json 骨架")
    parser.add_argument("--name", required=True, help="合同名称")
    parser.add_argument("--role", default="甲方", help="我方角色")
    parser.add_argument("--type", default="其他", help="合同类型（买卖/服务/租赁/合作/借款/其他）")
    parser.add_argument("--out", default="modify-plan.json", help="输出路径")
    args = parser.parse_args()

    plan = {
        "meta": {
            "contract_name": args.name,
            "party_role": args.role,
            "contract_type": args.type,
            "playbook": "PLAYBOOK_zh-CN.md",
            # modify_perspective 为必填字段，须按 Step 1 用户选定的修改视角补填，
            # 取值：甲方利益 | 乙方利益 | 中立公平 | 自定义:<内容>
            "modify_perspective": "",
            "methodology": "三观四步法(第五版)+完美的合同(第四版)+合同审查与修改实务(杨司和2022)",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
        "findings": [
            {
                "id": "F1",
                "view": "micro",  # macro|meso|micro，对应《三观四步法》三观视角
                "quality_dim": "inner",  # inner|outer|layout，对应《完美的合同》质量三维度
                "module": "liability",  # quality|price|term|object|liability，五大基本模块
                "clause_func": "dispute",  # statement|promise|exemption|dispute|ancillary，条款功能分类
                "clause": "（条款名，如：第X条 违约责任）",
                "action": "replace",  # delete|insert|replace|comment（杨司和增删改调）
                "anchor_text": "（用于定位的原句片段，可选）",
                "current_text": "（原文）",
                "proposed_text": "（建议改法）",
                "risk_level": "高",
                "reason": "（风险/修改理由，含三观视角+质量维度+模块依据）",
                "legal_basis": "（法条/案号，须经华宇元典核验）",
                "verify_status": "pending",
                "dimension": "",  # ①|②|③|④|⑤|⑥|⑦|⑧|⑨，对应实战审查九维，可选
            }
        ],
    }
    out = Path(args.out)
    out.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"骨架已生成：{out}")


if __name__ == "__main__":
    main()
