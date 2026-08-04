#!/usr/bin/env python3
"""
Clean and validate risk annotation JSON from LLM output.

Takes:
- LLM-generated JSON text (mapping contract snippets to risk comments)
- Original document text (extracted from .docx)

Outputs:
- comments_json: validated JSON string of annotations
- debug: debug information
- can_generate: "true" or "false"
- doc_preview: first 500 chars of document text

Replaces Dify's "清洗批注JSON" code node.

Usage:
    python clean_annotations.py --llm-file <llm_output.txt> --doc-file <doc_text.txt> [--output <result.json>]
    python clean_annotations.py --llm-text "<inline llm text>" --doc-text "<inline doc text>"
    cat llm_output.txt | python clean_annotations.py --doc-file doc.txt --llm-stdin
"""

import json
import re
import sys
import os
import argparse

MIN_VALID_DOC_LEN = 30
MAX_TOTAL_COMMENTS = 20
MAX_SENSITIVE_COMMENTS = 15
MIN_SENSITIVE_KEY_LEN = 2

SENSITIVE_RULES = [
    {
        "enabled": True,
        "name": "价格/金额",
        "mask": "**********",
        "patterns": [
            r"(?:人民币|RMB|CNY|USD|美元|美金|￥|¥|\$)\s*\d+(?:,\d{3})*(?:\.\d+)?\s*(?:元|万元|亿元|美元|美金)?",
            r"\d+(?:,\d{3})*(?:\.\d+)?\s*(?:元|万元|亿元|美元|美金)",
            r"(?:合同价款|合同总价|总价|价款|价格|报价|金额|费用|服务费|货款|付款金额|支付金额|结算金额|含税金额|不含税金额|预算|采购金额)[：:\s为是]*\d+(?:,\d{3})*(?:\.\d+)?",
            r"(?:人民币)?[零壹贰叁肆伍陆柒捌玖拾佰仟]+(?:万|亿)?[零壹贰叁肆伍陆柒捌玖拾佰仟]*(?:圆|元)(?:[零壹贰叁肆伍陆柒捌玖角分]+)?(?:整|正)?",
            r"[￥¥]\s*\d+(?:,\d{3})*(?:\.\d+)?"
        ]
    },
    {
        "enabled": True,
        "name": "单价",
        "mask": "**********",
        "patterns": [
            r"(?:单价|含税单价|不含税单价|报价|价格)[：:\s为是]*\d+(?:,\d{3})*(?:\.\d+)?\s*(?:元|万元|美元|美金)?",
            r"\d+(?:,\d{3})*(?:\.\d+)?\s*(?:元|万元|美元|美金)\s*/\s*(?:个|件|台|套|吨|公斤|kg|KG|平方米|㎡|月|年|日|小时|人天|人月)",
            r"[￥¥]\s*\d+(?:,\d{3})*(?:\.\d+)?\s*/\s*(?:个|件|台|套|吨|公斤|kg|KG|平方米|㎡|月|年|日|小时|人天|人月)"
        ]
    },
    {
        "enabled": True,
        "name": "银行账号",
        "mask": "**********",
        "patterns": [
            r"(?:银行账号|账号|账户|收款账号|付款账号|收款账户|付款账户)[：:\s]*[0-9][0-9\s\-]{7,30}"
        ]
    },
    {
        "enabled": True,
        "name": "开户行信息",
        "mask": "**********",
        "patterns": [
            r"(?:开户行|开户银行)[：:\s]*[^。；;\n]{4,80}"
        ]
    },
    {
        "enabled": True,
        "name": "税号/统一社会信用代码",
        "mask": "**********",
        "patterns": [
            r"(?:统一社会信用代码|社会信用代码|纳税人识别号|税号)[：:\s]*[0-9A-Z]{15,20}",
            r"\b[0-9A-Z]{18}\b"
        ]
    },
    {
        "enabled": True,
        "name": "身份证号",
        "mask": "**********",
        "patterns": [
            r"\b[1-9]\d{5}(?:18|19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx]\b"
        ]
    },
    {
        "enabled": True,
        "name": "手机号",
        "mask": "**********",
        "patterns": [
            r"(?<!\d)1[3-9]\d{9}(?!\d)"
        ]
    },
    {
        "enabled": True,
        "name": "固定电话",
        "mask": "**********",
        "patterns": [
            r"(?:电话|联系电话|联系方式)[：:\s]*(?:\d{3,4}-\d{7,8}|\d{7,8})"
        ]
    },
    {
        "enabled": True,
        "name": "电子邮箱",
        "mask": "**********",
        "patterns": [
            r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"
        ]
    },
    {
        "enabled": True,
        "name": "联系地址/注册地址",
        "mask": "**********",
        "patterns": [
            r"(?:联系地址|注册地址|住所地|通讯地址|地址)[：:\s]*[^。；;\n]{6,100}"
        ]
    },
    {
        "enabled": True,
        "name": "合同编号/项目编号",
        "mask": "**********",
        "patterns": [
            r"(?:合同编号|项目编号|项目编码|订单编号|采购编号)[：:\s]*[A-Za-z0-9\-_（）()]{4,60}"
        ]
    }
]


def clean_text(s):
    if s is None:
        return ""
    s = str(s)
    s = s.replace("\r", "\n")
    s = s.replace("\u3000", " ")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n+", "\n", s)
    return s.strip()


def one_line(s):
    s = clean_text(s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def extract_json_object(text):
    if not text:
        return None, "LLM 输出为空"

    raw = str(text).strip()
    raw = re.sub(r"^```json\s*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"^```\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    match = re.search(r"\{[\s\S]*\}", raw)
    if match:
        raw = match.group(0)

    try:
        data = json.loads(raw)
        return data, ""
    except Exception as e:
        return None, "JSON 解析失败：" + str(e)


def split_sentences(doc_text):
    text = clean_text(doc_text)
    if not text:
        return []

    raw_parts = re.split(r"(?<=[。；;！？!?])|\n", text)
    parts = []

    for p in raw_parts:
        p = one_line(p)
        if not p:
            continue
        parts.append(p)

    return parts


def make_sensitive_key(sentence, match):
    s = one_line(sentence)
    matched_text = one_line(match.group(0))

    if 6 <= len(s) <= 120:
        return s

    if len(matched_text) >= MIN_SENSITIVE_KEY_LEN:
        return matched_text

    start, end = match.span()
    left = max(0, start - 35)
    right = min(len(s), end + 35)

    key = s[left:right]
    key = key.strip(" ，,；;。")

    if len(key) > 120:
        key = key[:120].strip(" ，,；;。")

    return key


def sensitive_comment(rule_name, mask):
    return (
        "【高风险】敏感信息：该处包含"
        + rule_name
        + "等敏感信息，建议纳入脱敏或访问控制范围；"
        + "风险后果：未经授权披露可能导致商业秘密泄露、价格体系暴露、财务信息泄露、个人信息合规风险或交易谈判不利；"
        + "修改建议：建议在对外版本、流转版本或非必要披露场景中将敏感内容替换为"
        + mask
        + "，并限制知悉范围。"
    )


def build_sensitive_comments(doc_text, max_items=15):
    text = clean_text(doc_text)

    sentence_parts = split_sentences(text)
    line_parts = [one_line(x) for x in text.split("\n") if one_line(x)]

    parts = []
    seen_part = set()

    for p in sentence_parts + line_parts:
        p = one_line(p)
        if not p:
            continue
        if p in seen_part:
            continue
        seen_part.add(p)
        parts.append(p)

    result = {}
    seen_key = set()

    for p in parts:
        if len(result) >= max_items:
            break

        sentence = one_line(p)
        if not sentence:
            continue

        for rule in SENSITIVE_RULES:
            if len(result) >= max_items:
                break

            if not rule.get("enabled", True):
                continue

            rule_name = rule.get("name", "敏感信息")
            mask = rule.get("mask", "**********")
            patterns = rule.get("patterns", [])

            for pattern in patterns:
                if len(result) >= max_items:
                    break

                try:
                    matches = list(re.finditer(pattern, sentence, flags=re.IGNORECASE))
                except Exception:
                    continue

                for m in matches:
                    if len(result) >= max_items:
                        break

                    key = make_sensitive_key(sentence, m)
                    key = one_line(key)

                    if not key:
                        continue

                    if len(key) < MIN_SENSITIVE_KEY_LEN:
                        continue

                    if key in seen_key:
                        continue

                    if key not in text:
                        continue

                    seen_key.add(key)
                    result[key] = sensitive_comment(rule_name, mask)

    return result


def comment_for_sentence(sentence):
    s = one_line(sentence)

    if any(k in s for k in ["付款", "支付", "价款", "费用", "款项"]):
        return "【中风险】风险点：付款条款需进一步核查付款金额、付款节点、付款条件、发票要求及逾期付款责任是否明确；风险后果：约定不清可能导致付款时间、付款条件及违约责任发生争议；修改建议：建议明确付款金额、付款期限、付款前置条件、开票要求及逾期付款违约责任。"

    if any(k in s for k in ["验收", "确认", "合格"]):
        return "【中风险】风险点：验收条款需进一步明确验收标准、验收流程、异议期限及逾期未验收的处理规则；风险后果：可能导致交付成果是否合格及付款条件是否成就发生争议；修改建议：建议补充书面验收标准、验收期限、异议反馈机制及逾期视为验收通过的规则。"

    if any(k in s for k in ["违约", "赔偿", "违约金", "损失", "责任"]):
        return "【中风险】风险点：违约责任条款需进一步核查违约情形、违约金计算方式、损失赔偿范围及责任限制是否明确；风险后果：约定不清可能导致违约救济不足或赔偿范围争议；修改建议：建议明确各类违约情形、违约金比例或计算方式、赔偿范围及守约方救济措施。"

    if any(k in s for k in ["解除", "终止"]):
        return "【中风险】风险点：解除或终止条款需进一步明确解除条件、通知期限、费用结算及已履行部分处理规则；风险后果：可能导致单方解除、费用结算或损失承担发生争议；修改建议：建议明确解除触发条件、提前通知期限、结算规则、资料返还义务及违约后果。"

    if any(k in s for k in ["争议", "管辖", "仲裁", "法院", "诉讼"]):
        return "【中风险】风险点：争议解决条款需核查管辖法院或仲裁机构是否明确、唯一且具有可执行性；风险后果：约定不明可能导致争议解决程序延误或管辖争议；修改建议：建议明确选择诉讼或仲裁，并写明具体有管辖权的法院或仲裁机构。"

    if any(k in s for k in ["保密", "商业秘密", "秘密"]):
        return "【中风险】风险点：保密条款需明确保密信息范围、保密期限、例外情形、返还或销毁要求及违约责任；风险后果：约定不完整可能导致商业秘密或敏感信息保护不足；修改建议：建议补充保密信息定义、保密期限、允许披露情形、资料返还或销毁规则及违约责任。"

    if any(k in s for k in ["知识产权", "著作权", "专利", "商标", "成果"]):
        return "【中风险】风险点：知识产权条款需明确成果归属、使用范围、许可方式、第三方侵权担保及责任承担；风险后果：可能导致成果使用受限、权属争议或侵权责任承担不清；修改建议：建议明确合同成果及背景知识产权的归属、许可范围、使用期限、侵权担保及责任承担。"

    if any(k in s for k in ["交付", "交货", "完成", "提交", "履行"]):
        return "【中风险】风险点：交付条款需明确交付内容、交付时间、交付地点、交付方式及迟延交付责任；风险后果：可能导致履约范围、交付节点和迟延责任发生争议；修改建议：建议明确交付清单、交付期限、交付方式、签收确认规则及迟延交付违约责任。"

    if any(k in s for k in ["通知", "送达", "地址", "联系人"]):
        return "【中风险】风险点：通知送达条款需进一步明确通知方式、送达地址、联系人变更及视为送达规则；风险后果：可能影响合同通知、解除、催告等法律文件的有效送达；修改建议：建议明确电子邮件、快递、短信等通知方式及地址变更后的通知义务。"

    if any(k in s for k in ["期限", "有效期", "生效"]):
        return "【中风险】风险点：合同期限或生效条款需进一步明确起止时间、生效条件及期满后的处理规则；风险后果：可能导致合同效力期间、续展或终止时间存在理解差异；修改建议：建议明确合同生效条件、有效期限、续展规则及期满后的权利义务处理。"

    return "【中风险】风险点：该条款表述可进一步细化权利义务、履行标准或操作流程；风险后果：可能在履行过程中产生理解差异或履约争议；修改建议：建议结合交易安排补充具体履行标准、期限、流程及责任承担方式。"


def build_fallback_from_real_doc(doc_text, max_items=6):
    text = clean_text(doc_text)
    parts = split_sentences(text)

    candidates = []
    seen = set()

    keyword_groups = [
        ["付款", "支付", "价款", "费用", "款项"],
        ["验收", "确认", "合格"],
        ["违约", "赔偿", "违约金", "损失", "责任"],
        ["解除", "终止"],
        ["争议", "管辖", "仲裁", "法院", "诉讼"],
        ["保密", "商业秘密"],
        ["知识产权", "著作权", "专利", "商标", "成果"],
        ["交付", "交货", "完成", "提交", "履行"],
        ["通知", "送达", "地址", "联系人"],
        ["期限", "有效期", "生效"]
    ]

    for group in keyword_groups:
        for p in parts:
            p = one_line(p)

            if len(p) < 8 or len(p) > 120:
                continue

            if p in seen:
                continue

            if any(k in p for k in group):
                seen.add(p)
                candidates.append(p)
                break

        if len(candidates) >= max_items:
            break

    if len(candidates) < 3:
        for p in parts:
            p = one_line(p)

            if len(p) < 8 or len(p) > 120:
                continue

            if p in seen:
                continue

            if re.match(r"^第[一二三四五六七八九十\d]+[章节条、.．]?$", p):
                continue

            seen.add(p)
            candidates.append(p)

            if len(candidates) >= max_items:
                break

    result = {}

    for c in candidates[:max_items]:
        result[c] = comment_for_sentence(c)

    return result


def add_or_merge_comment(target, key, value):
    if key in target:
        if value not in target[key]:
            target[key] = target[key] + "；同时，" + value
    else:
        target[key] = value


def limit_comments(data, max_items=MAX_TOTAL_COMMENTS):
    result = {}

    for k, v in data.items():
        if len(result) >= max_items:
            break
        result[k] = v

    return result


def main(llm_text: str, doc_text: str) -> dict:
    """Process LLM output and document text to produce cleaned annotations.

    Args:
        llm_text: The raw JSON text output from the LLM.
        doc_text: The extracted document text from the .docx file.

    Returns:
        dict with keys: comments_json, debug, doc_preview, can_generate
    """
    doc_text_clean = clean_text(doc_text)
    doc_len = len(doc_text_clean)

    if doc_len < MIN_VALID_DOC_LEN:
        return {
            "comments_json": "{}",
            "debug": "文档提取内容过短，已阻止生成批注；文档提取内容：\"" + doc_text_clean + "\"；文档提取长度：" + str(doc_len),
            "doc_preview": doc_text_clean[:500],
            "can_generate": "false"
        }

    data, parse_error = extract_json_object(llm_text)

    llm_cleaned = {}

    if isinstance(data, dict):
        for k, v in data.items():
            if k is None or v is None:
                continue

            key = one_line(k)
            value = one_line(v)

            if not key or not value:
                continue

            if len(key) < 6:
                continue

            if len(key) > 140:
                key = key[:140]

            if key not in doc_text_clean:
                continue

            llm_cleaned[key] = value

    sensitive_data = build_sensitive_comments(
        doc_text_clean,
        max_items=MAX_SENSITIVE_COMMENTS
    )

    final_comments = {}

    for k, v in sensitive_data.items():
        add_or_merge_comment(final_comments, k, v)

    for k, v in llm_cleaned.items():
        add_or_merge_comment(final_comments, k, v)

    final_comments = limit_comments(final_comments, MAX_TOTAL_COMMENTS)

    if len(final_comments) > 0:
        sensitive_preview = " | ".join(list(sensitive_data.keys())[:5]) if len(sensitive_data) > 0 else "无"

        return {
            "comments_json": json.dumps(final_comments, ensure_ascii=False),
            "debug": (
                "已生成批注；"
                + "敏感信息批注数量："
                + str(len(sensitive_data))
                + "；敏感信息命中示例："
                + sensitive_preview
                + "；LLM 有效批注数量："
                + str(len(llm_cleaned))
                + "；最终批注数量："
                + str(len(final_comments))
                + "；文档提取长度："
                + str(doc_len)
            ),
            "doc_preview": doc_text_clean[:500],
            "can_generate": "true"
        }

    fallback_data = build_fallback_from_real_doc(doc_text_clean, max_items=6)

    if len(fallback_data) > 0:
        return {
            "comments_json": json.dumps(fallback_data, ensure_ascii=False),
            "debug": (
                "LLM 未生成有效批注，且未识别到敏感信息，已使用合同正文兜底生成；"
                + "兜底批注数量："
                + str(len(fallback_data))
                + "；解析信息："
                + parse_error
                + "；文档提取长度："
                + str(doc_len)
            ),
            "doc_preview": doc_text_clean[:500],
            "can_generate": "true"
        }

    return {
        "comments_json": "{}",
        "debug": "未生成有效批注对；解析信息：" + parse_error + "；文档提取长度：" + str(doc_len),
        "doc_preview": doc_text_clean[:500],
        "can_generate": "false"
    }


def cli_main():
    parser = argparse.ArgumentParser(
        description="Clean and validate risk annotation JSON from LLM output"
    )
    parser.add_argument("--llm-file", help="Path to file containing LLM output text")
    parser.add_argument("--doc-file", help="Path to file containing extracted document text")
    parser.add_argument("--llm-text", help="Inline LLM output text")
    parser.add_argument("--doc-text", help="Inline document text")
    parser.add_argument("--llm-stdin", action="store_true", help="Read LLM output from stdin")
    parser.add_argument("--output", "-o", help="Path to output JSON file (default: stdout)")
    args = parser.parse_args()

    # Get LLM text
    llm_text = ""
    if args.llm_file:
        with open(args.llm_file, "r", encoding="utf-8") as f:
            llm_text = f.read()
    elif args.llm_text:
        llm_text = args.llm_text
    elif args.llm_stdin:
        llm_text = sys.stdin.read()
    else:
        print("ERROR: Must provide --llm-file, --llm-text, or --llm-stdin", file=sys.stderr)
        sys.exit(1)

    # Get document text
    doc_text = ""
    if args.doc_file:
        with open(args.doc_file, "r", encoding="utf-8") as f:
            doc_text = f.read()
    elif args.doc_text:
        doc_text = args.doc_text
    else:
        print("ERROR: Must provide --doc-file or --doc-text", file=sys.stderr)
        sys.exit(1)

    result = main(llm_text, doc_text)

    output_text = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_text)
        print(f"Result written to: {args.output}", file=sys.stderr)
    else:
        print(output_text)


if __name__ == "__main__":
    cli_main()
