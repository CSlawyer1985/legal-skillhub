#!/usr/bin/env python3
"""起草引擎 — 基于匹配到的口径生成群聊回复草稿。

纯模板引擎（零 LLM 依赖），从 config.yaml 读取风格参数。
实际使用时由 Agent 调用 LLM 做二次润色，本脚本提供结构化 prompt。
"""

import argparse
import json
import os
import sys


def build_draft_prompt(question, match_results, config=None):
    """
    构建起草 prompt，供 Agent/LLM 使用。

    Parameters
    ----------
    question : str
        用户原始问题
    match_results : list[dict]
        shadow_match.py 输出的匹配结果
    config : dict
        config.yaml 中的 draft_style 部分

    Returns
    -------
    dict
        {prompt, context, style_rules}
    """
    style = (config or {}).get("draft_style", {})
    max_chars = style.get("max_chars", 100)
    tone = style.get("tone", "professional")
    include_basis = style.get("include_legal_basis", True)
    basis_depth = style.get("legal_basis_depth", "brief")
    mark_case = style.get("mark_case_specific", True)
    forbidden = style.get("forbidden_phrases", [])

    # 构建上下文
    context_parts = []
    for r in match_results:
        e = r["corpus_entry"]
        context_parts.append(
            f"[口径 {e.get('id', '?')} 相似度={r['similarity']:.2f}]\n"
            f"  典型问题：{e.get('典型问题', '')}\n"
            f"  标准答复：{e.get('标准答复', '')}\n"
            f"  法条依据：{e.get('法条依据', '')}\n"
            f"  适用场景：{e.get('适用场景', '')}\n"
            f"  不适用场景：{e.get('不适用场景', '')}"
        )
    context = "\n\n".join(context_parts)

    # 构建风格规则
    rules = [
        f"字数上限：{max_chars}字",
        f"语气：{tone}",
        f"结论先行：是" if style.get("conclusion_first") else "",
        f"附法条依据：是（{basis_depth}）" if include_basis else "不附法条",
        f"标注个案确认：是" if mark_case else "",
    ]
    if forbidden:
        rules.append(f"禁用表述：{', '.join(forbidden)}")
    rules = [r for r in rules if r]

    prompt = (
        f"你是一个法务团队的AI助手。业务方在群里问了一个法律问题，"
        f"请基于以下历史口径生成可直接粘贴到群里的回复。\n\n"
        f"## 用户问题\n{question}\n\n"
        f"## 历史口径参考\n{context}\n\n"
        f"## 风格要求\n" + "\n".join(f"- {r}" for r in rules) + "\n\n"
        f"## 输出格式\n"
        f"【快速回复版】≤{max_chars}字，可直接粘贴到群里\n"
        f"【内部参考版】补充法条原文+注意事项（不限长度）\n"
        f"⚠️AI初稿须律师审核后发出"
    )

    return {
        "prompt": prompt,
        "context": context,
        "style_rules": rules,
        "question": question,
        "top_match": match_results[0] if match_results else None,
    }


def quick_template_draft(question, match_results, config=None):
    """
    纯模板快速草稿（不依赖 LLM）。
    用于无 LLM 环境下的降级方案。
    """
    if not match_results:
        return {
            "quick": f"收到，这个问题需要进一步了解具体情况后回复。",
            "internal": "无匹配历史口径，需律师从头分析。",
            "matched": False,
        }

    top = match_results[0]["corpus_entry"]
    sim = match_results[0]["similarity"]
    style = (config or {}).get("draft_style", {})
    max_chars = style.get("max_chars", 100)

    # 基于标准答复裁剪
    reply = top.get("标准答复", "")
    basis = top.get("法条依据", "")

    # 截断到字数上限
    if len(reply) > max_chars:
        # 保留第一句
        sentences = reply.split("。")
        truncated = "。".join(sentences[:2]) + "。"
        if len(truncated) > max_chars + 20:
            truncated = reply[:max_chars] + "..."
        reply = truncated

    # 添加个案确认标记
    if style.get("mark_case_specific", True):
        reply += "（个案请确认具体情况）"

    internal = f"匹配口径：{top.get('id', '')}（相似度{sim:.2f}）\n"
    internal += f"法条依据：{basis}\n"
    internal += f"适用场景：{top.get('适用场景', '')}\n"
    internal += f"不适用场景：{top.get('不适用场景', '')}\n"
    internal += f"标准答复全文：{top.get('标准答复', '')}"

    return {
        "quick": reply,
        "internal": internal,
        "matched": True,
        "matched_id": top.get("id", ""),
        "similarity": sim,
    }


def main():
    ap = argparse.ArgumentParser(description="法律咨询起草引擎")
    ap.add_argument("--question", required=True, help="用户问题")
    ap.add_argument("--match-results", required=True, help="shadow_match 输出 JSON")
    ap.add_argument("--config", default=None, help="config.yaml 路径")
    ap.add_argument("--mode", choices=["prompt", "template"], default="template",
                    help="prompt=生成LLM prompt, template=纯模板快速草稿")
    ap.add_argument("--output", default=None)
    args = ap.parse_args()

    match_results = json.load(open(args.match_results, encoding="utf-8"))
    config = None
    if args.config:
        import yaml
        config = yaml.safe_load(open(args.config, encoding="utf-8"))

    if args.mode == "prompt":
        result = build_draft_prompt(args.question, match_results, config)
    else:
        result = quick_template_draft(args.question, match_results, config)

    out = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"[draft_reply] → {args.output}", file=sys.stderr)
    else:
        print(out)


if __name__ == "__main__":
    main()
