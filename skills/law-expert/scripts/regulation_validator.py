#!/usr/bin/env python3
"""
法眼 - 法规时效验证工具
用法: python3 regulation_validator.py <法规名称>
功能: 验证法规是否现行有效
"""

import sys
import json
from datetime import datetime


def validate_timeliness(law_name: str) -> dict:
    """
    验证法规时效，返回:
    {
        "name": "法规名称",
        "status": "✅现行有效" | "⚠️已修订" | "❌已废止",
        "effective_date": "生效日期",
        "latest_revision": "最新修订日期",
        "note": "说明",
        "validation_timestamp": "验证时间"
    }
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"\n🔍 正在验证「{law_name}」的时效性...")
    print(f"⏰ 验证时间: {timestamp}\n")

    # 验证步骤说明
    print("📋 时效性验证步骤:\n")
    print("  Step 1: 在国家法律法规数据库中检索法规名称")
    print("  Step 2: 查看法规状态标注（现行有效/已修订/已废止）")
    print("  Step 3: 检查是否有修订案")
    print("  Step 4: 检查是否有废止决定")
    print("  Step 5: 确认最新版本号及修订日期\n")

    # 验证建议
    verification_sources = [
        {
            "name": "国家法律法规数据库",
            "url": "https://flk.npc.gov.cn",
            "action": f"搜索「{law_name}」并查看状态标注"
        },
        {
            "name": "中国人大网",
            "url": "http://www.npc.gov.cn",
            "action": f"搜索「{law_name} 修订」或「{law_name} 废止」"
        },
        {
            "name": "北大法宝",
            "url": "https://www.pkulaw.com",
            "action": f"搜索「{law_name}」查看时效性标注和修订历史"
        }
    ]

    for i, source in enumerate(verification_sources, 1):
        print(f"  渠道{i}: {source['name']}")
        print(f"  URL: {source['url']}")
        print(f"  操作: {source['action']}\n")

    print("=" * 60)
    print("⚠️  时效性验证提示:")
    print("=" * 60)
    print("""
  ✅ 现行有效  — 可以直接引用，注意区分原版和修订版
  ⚠️ 已被修订  — 引用时需注明修订后版本
                  例如：「《民法典》第X条（2020年修订版）」
  ❌ 已废止    — 不可引用，需寻找替代法规
                  例如：《合同法》已被《民法典》取代

  📌 特别注意:
  - 民法典于2021年1月1日施行后，《婚姻法》《继承法》
    《民法通则》《收养法》《担保法》《合同法》《物权法》
    《侵权责任法》《民法总则》同时废止
  - 引用前务必确认是否被新法规取代
  - 司法解释的时效性独立于原法律，需单独验证
    """)

    print("=" * 60)

    result = {
        "name": law_name,
        "status": "needs_websearch_verification",
        "verification_timestamp": timestamp,
        "verification_sources": verification_sources,
        "note": "需通过上述渠道联网验证法规最新时效状态。不可仅凭记忆判断法规是否有效。"
    }

    return result


def check_common_laws(law_name: str) -> dict:
    """
    检查常见法律的已知更替关系
    """
    # 已知被民法典吸收/废止的法律
    absorbed_by_civil_code = {
        "婚姻法": "已由《民法典》第五编（婚姻家庭）取代",
        "继承法": "已由《民法典》第六编（继承）取代",
        "民法通则": "已由《民法典》取代",
        "收养法": "已由《民法典》第五编第五章（收养）取代",
        "担保法": "已由《民法典》第二编第四分编（担保物权）和合同编取代",
        "合同法": "已由《民法典》第三编（合同）取代",
        "物权法": "已由《民法典》第二编（物权）取代",
        "侵权责任法": "已由《民法典》第七编（侵权责任）取代",
        "民法总则": "已由《民法典》第一编（总则）取代",
    }

    if law_name in absorbed_by_civil_code:
        print(f"\n⚠️  已知信息: 《{law_name}》{absorbed_by_civil_code[law_name]}")
        print("   建议检索最新版《民法典》相关条款替代。\n")

    return {
        "name": law_name,
        "absorbed": law_name in absorbed_by_civil_code,
        "replacement": absorbed_by_civil_code.get(law_name, None)
    }


def batch_validate(laws: list) -> list:
    """批量验证多个法规"""
    results = []
    for law in laws:
        print(f"\n{'=' * 60}")
        result = validate_timeliness(law)
        # Also check common law replacements
        replacement_info = check_common_laws(law)
        result["replacement"] = replacement_info
        results.append(result)
    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法:")
        print("  python3 regulation_validator.py <法规名称>")
        print("  python3 regulation_validator.py --batch <法规1> <法规2> ...")
        print("\n示例:")
        print("  python3 regulation_validator.py 民法典")
        print("  python3 regulation_validator.py 劳动法")
        print("  python3 regulation_validator.py --batch 合同法 物权法 婚姻法")
        sys.exit(0)

    if sys.argv[1] == "--batch":
        if len(sys.argv) < 3:
            print("用法: python3 regulation_validator.py --batch <法规1> <法规2> ...")
            sys.exit(1)
        laws = sys.argv[2:]
        results = batch_validate(laws)
        print(f"\n📤 批量验证结果:\n{json.dumps(results, ensure_ascii=False, indent=2)}")
    else:
        law_name = sys.argv[1]
        result = validate_timeliness(law_name)
        replacement_info = check_common_laws(law_name)
        result["replacement"] = replacement_info
        print(f"\n📤 验证结果:\n{json.dumps(result, ensure_ascii=False, indent=2)}")
