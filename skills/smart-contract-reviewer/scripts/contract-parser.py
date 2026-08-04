#!/usr/bin/env python3
"""
contract-parser.py - 合同结构化解析脚本

功能：
1. 从合同文本中提取关键条款
2. 识别条款类型和风险关键词
3. 输出结构化JSON供SKILL.md工作流使用

用法：
  python3 contract-parser.py --input contract.txt --output result.json
  python3 contract-parser.py --input contract.pdf --ocr
"""

import argparse
import json
import re
import sys
from pathlib import Path


# 关键条款识别模式
CLAUSE_PATTERNS = {
    "当事人信息": [
        r"(甲方|乙方|卖方|买方|出租方|承租方|服务提供方|服务接受方)[：:].*?[\n\r]",
        r"统一社会信用代码[：:].*?[\n\r]",
        r"法定代表人[：:].*?[\n\r]",
    ],
    "标的条款": [
        r"标的[名称]*[：:].*?[\n\r]",
        r"服务内容[：:].*?[\n\r]",
        r"采购内容[：:].*?[\n\r]",
    ],
    "价款与支付": [
        r"价款[：:].*?元",
        r"总金额[：:].*?[\n\r]",
        r"支付方式[：:].*?[\n\r]",
        r"付款节点[：:].*?[\n\r]",
    ],
    "履行条款": [
        r"履行期限[：:].*?[\n\r]",
        r"交付时间[：:].*?[\n\r]",
        r"验收标准[：:].*?[\n\r]",
    ],
    "违约责任": [
        r"违约责任[：:].*?[\n\r]",
        r"违约金[：:].*?[\n\r]",
        r"赔偿.*损失",
    ],
    "争议解决": [
        r"争议解决[：:].*?[\n\r]",
        r"管辖法院[：:].*?[\n\r]",
        r"仲裁机构?[：:].*?[\n\r]",
        r"适用.*法律",
    ],
    "保密条款": [
        r"保密[条款]*[：:].*?[\n\r]",
        r"保密信息[：:].*?[\n\r]",
        r"保密期限[：:].*?[\n\r]",
    ],
    "知识产权": [
        r"知识产权[：:].*?[\n\r]",
        r"著作权[：:].*?[\n\r]",
        r"专利权[：:].*?[\n\r]",
    ],
    "合同解除": [
        r"解除.*合同",
        r"终止.*条款",
        r"解除条件[：:].*?[\n\r]",
    ],
    "不可抗力": [
        r"不可抗力[：:].*?[\n\r]",
        r"不可抗力.*免责",
    ],
}

# 风险关键词
RISK_KEYWORDS = {
    "高风险": [
        "放弃法定解除权", "放弃诉讼时效", "无限责任",
        "全部损失（包括间接损失）", "赔偿一切损失",
        "无条件赔偿", "放弃一切抗辩",
    ],
    "中风险": [
        "可随时解除", "无需说明理由", "最终解释权",
        "承担全部费用", "自行承担一切风险",
    ],
    "低风险": [
        "以实际为准", "双方另行协商", "可予调整",
    ],
}


def extract_clauses(text: str) -> dict:
    """从合同文本中提取关键条款"""
    results = {}
    for clause_type, patterns in CLAUSE_PATTERNS.items():
        matches = []
        for pattern in patterns:
            found = re.findall(pattern, text, re.DOTALL | re.MULTILINE)
            if found:
                matches.extend(found if isinstance(found[0], str) else [m[0] for m in found])
        if matches:
            results[clause_type] = list(set(matches))[:3]  # 去重，最多3条
    return results


def assess_risk(text: str) -> dict:
    """评估合同文本中的风险关键词"""
    risk_found = {"高风险": [], "中风险": [], "低风险": []}
    for level, keywords in RISK_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                risk_found[level].append(kw)
    return risk_found


def parse_contract(input_path: str) -> dict:
    """解析合同主函数"""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {input_path}")

    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    return {
        "filename": path.name,
        "text_length": len(text),
        "clauses": extract_clauses(text),
        "risk_keywords": assess_risk(text),
        "risk_summary": {
            "高风险数": len([k for k in assess_risk(text)["高风险"]]),
            "中风险数": len([k for k in assess_risk(text)["中风险"]]),
            "低风险数": len([k for k in assess_risk(text)["低风险"]]),
        },
    }


def main():
    parser = argparse.ArgumentParser(description="合同结构化解析脚本")
    parser.add_argument("--input", "-i", required=True, help="输入合同文件路径（TXT/MD）")
    parser.add_argument("--output", "-o", help="输出JSON文件路径")
    args = parser.parse_args()

    try:
        result = parse_contract(args.input)
        json_output = json.dumps(result, ensure_ascii=False, indent=2)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(json_output)
            print(f"✅ 解析完成，结果保存至: {args.output}")
        else:
            print(json_output)

        # 打印风险摘要
        summary = result["risk_summary"]
        print(f"\n📊 风险摘要:")
        print(f"   高风险关键词: {summary['高风险数']} 处")
        print(f"   中风险关键词: {summary['中风险数']} 处")
        print(f"   低风险关键词: {summary['低风险数']} 处")

    except Exception as e:
        print(f"❌ 错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
