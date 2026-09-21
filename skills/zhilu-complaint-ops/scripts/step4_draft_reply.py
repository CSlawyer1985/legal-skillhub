#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
step4 AI起草答复：基于黄金口径库检索相似历史案件，调用LLM生成三段式答复初稿
（【合规研判】【处理建议】【答复口径】），供承办人修改定稿。
用法: python3 step4_draft_reply.py --case data/sample_complaints.json --index 0
密钥: 环境变量 LLM_API_KEY（未设置时输出模板演示稿）
"""
import argparse
import json
import os
import re
import urllib.request

API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"

SYSTEM_PROMPT = (
    "你是钉钉法务专员，负责起草市场监管局转办投诉的答复。请严格按三段式输出：\n"
    "【合规研判】先判断投诉主体是消费者还是企业客户——企业采购的产品/服务不适用《消费者权益保护法》，"
    "应按《民法典》合同编与服务协议处理；再研判合规风险性质与等级。\n"
    "【处理建议】给出内部处理路径，标注承办部门与时限。\n"
    "【答复口径】面向消费者和市监局的外部答复文本，语气诚恳、简洁专业。\n\n"
    "【核心立场：条件式退款，不得默认倾向退款】依据真实处置口径，退款与否取决于核实结果，分七种情形：\n"
    "1. 核实属实+订单有效+未实际使用/功能质量不达标 → 全额退款，简洁告知退款方式与到账时间，不展开合规论述；\n"
    "2. 订单已过期/无进线记录/多次联系不上用户 → 不支持退款，如实说明订单时效与核实情况；\n"
    "3. 服务质量/技术故障类 → 不承诺退款，详细说明技术原因，援引服务协议已有提示，引导联系客服个案处理；\n"
    "4. 产品设计/功能入口类 → 属产品设计权范畴，说明版本更新与功能定位，不陷入反垄断/不当引流论述；\n"
    "5. 企业客户合同纠纷 → 按合同条款与服务协议处理，不套用消保法退款逻辑；\n"
    "6. 企业大额专业版退费 → 按未使用部分折算退款（非全额、非拒绝），先核实订单为新购买及续费机制；\n"
    "7. 付费服务未按承诺履行（客服失联/服务缩水）→ 属服务合同未履行，核实后退款。\n"
    "【硬性要求】不得在未核实前擅自承诺退款金额与时限；涉及具体金额/日期/时限处用占位符并提示承办人核对；"
    "优先参考下方历史真实口径的处置方式与语气。"
)


def load_corpus(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def retrieve_similar(corpus, content, top_k=3):
    """简单关键词检索（部署时可替换为向量检索）"""
    def score(case):
        a = set(re.findall(r"[\u4e00-\u9fa5]{2,}", case.get("case_content", "")))
        b = set(re.findall(r"[\u4e00-\u9fa5]{2,}", content or ""))
        return len(a & b)
    return sorted(corpus, key=score, reverse=True)[:top_k]


def draft_with_llm(api_key, case, refs):
    ref_text = "\n".join(
        f"历史案件{i}: {r.get('case_content','')[:100]}... 参考口径: {r.get('golden_reply','')[:100]}..."
        for i, r in enumerate(refs, 1)
    )
    payload = {
        "model": "qwen-plus",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"投诉内容：{case.get('投诉内容','')}\n"
                                        f"投诉类型：{case.get('投诉类型','')} 诉求金额：{case.get('诉求金额','')}\n\n"
                                        f"参考历史口径：\n{ref_text}"},
        ],
        "temperature": 0.3,
    }
    req = urllib.request.Request(
        API_URL, data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    text = data["choices"][0]["message"]["content"]
    # post-processing：修复年份幻觉（2024→2026，2025仅替换"将于/将于X日前"等未来承诺语境）
    import re as _re
    text = _re.sub(r"2024年", "2026年", text)
    text = _re.sub(r"(将于|前|日前|内)2025年", r"\g<1>2026年", text)
    return text


def draft_template(case):
    """无API密钥时的演示模板"""
    return (
        "【合规研判】\n本件属{}类投诉，涉及金额{}元。需结合订单记录与服务协议核实告知义务履行情况，"
        "初步研判为一般消费争议，暂无行政处罚风险信号。\n\n"
        "【处理建议】\n1. 业务部门核实订单与沟通记录（1个工作日）；\n"
        "2. 符合退款条件的按原路退回，时限7-15个工作日；\n3. 承办人跟进至用户确认关闭。\n\n"
        "【答复口径】\n尊敬的用户/市监局同志：关于您反映的问题，我司已收悉并正在核实，"
        "将于承诺时限内向您反馈处理结果。"
    ).format(case.get("投诉类型", "服务质量"), case.get("诉求金额", "0"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", required=True, help="案件JSON文件")
    parser.add_argument("--index", type=int, default=0, help="案件在文件中的序号")
    parser.add_argument("--corpus", default="data/golden_corpus_sample.json", help="黄金口径库")
    args = parser.parse_args()

    with open(args.case, encoding="utf-8") as f:
        case = json.load(f)[args.index]
    refs = retrieve_similar(load_corpus(args.corpus), case.get("投诉内容", ""))
    print(f"检索到 {len(refs)} 条相似历史口径\n" + "-" * 60)

    api_key = os.environ.get("LLM_API_KEY", "")
    if api_key:
        reply = draft_with_llm(api_key, case, refs)
    else:
        print("（未设置LLM_API_KEY，输出演示模板）\n")
        reply = draft_template(case)
    print(reply)


if __name__ == "__main__":
    main()
