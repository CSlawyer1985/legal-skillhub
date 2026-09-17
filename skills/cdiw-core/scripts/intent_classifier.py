#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""意图识别辅助脚本（intent_classifier.py）。

功能：输入用户文本，输出匹配的工作线标签（含家属身份识别——输入含
"我家人""我弟弟""我先生"等家属口吻且咨询走向的，优先路由至接待线）与置信度。

调用方式：
  python scripts/intent_classifier.py --text "我老公被刑拘了会不会判很重"

统一接口规范：
  - 仅依赖Python标准库；支持--help；
  - 输出JSON信封：{status, error_code, message, data}；
  - 退出码：0成功 / 1参数错误 / 2数据文件缺失或损坏 / 3计算或校验失败；
  - 错误码：ERR_ARGS_MISSING / ERR_TYPE_INVALID；
  - data结构：{"workstreams": [...], "family_voice": bool, "confidence": 0.x}
"""

import argparse
import hashlib
import json
import sys
from datetime import datetime

SCRIPT_NAME = "intent_classifier"

# 工作线关键词表（命中即打标签；多线可同时命中）
KEYWORDS = {
    "meeting": ["会见", "提审", "会见提纲", "看守所会见", "辅导", "法律咨询",
                "七步", "第一次会见", "首次会见", "会见纪要"],
    "document": ["申请书", "意见书", "辩护词", "文书", "起诉状", "上诉状",
                 "质证", "发问提纲", "辩护意见", "法律意见"],
    "limit": ["期限", "倒计时", "多少天", "刑拘第", "黄金37天", "37天", "预警",
              "期限计算", "审限", "上诉期"],
    "reception": ["家属", "接待", "咨询", "赔偿谅解", "谅解书", "服务进程",
                  "工作清单", "确认表", "退赔", "被害人"],
    "communication": ["沟通", "承办", "递交", "递交手续", "办案机关", "民警",
                      "检察官", "法官", "留痕", "12309"],
    "measure": ["取保", "批捕", "逮捕", "羁押必要性", "强制措施", "认罪认罚",
                "不批捕", "监视居住", "累犯", "具结"],
    "evidence": ["取证", "调取证据", "非法证据", "排非", "鉴定意见", "证据矛盾",
                 "证据审查", "证人出庭", "专门知识的人", "检材", "调取录音录像"],
    "retrieval": ["类案检索", "检索", "罪名辨析", "类案", "法条检索", "检索报告",
                  "裁判倾向", "公报案例", "指导性案例", "办案参考"],
    "sentencing": ["量刑", "量刑测算", "基准刑", "宣告刑", "量刑情节", "量刑起点",
                   "缓刑评估", "罚金", "量刑建议", "量刑辩护"],
    "compliance": ["管辖", "管辖异议", "回避", "程序违法", "程序瑕疵", "申诉控告",
                   "发回重审", "程序性救济", "超期羁押", "诉讼权利"],
}

# 家属口吻关键词（含大纲示例："我家人""我弟弟""我先生"等）
FAMILY_PATTERNS = ["我家人", "我弟弟", "我先生", "我老公", "我老婆", "我儿子",
                   "我女儿", "我父亲", "我母亲", "我哥哥", "我姐姐", "我妹妹",
                   "我哥", "我弟", "我们家", "家里人"]

# 家属咨询走向类问题（与家属口吻叠加判定）
FAMILY_TOPIC = ["判", "取保", "会怎么样", "怎么办", "有没有用", "严重", "坐牢",
                "多久", "能不能", "怎么办"]


def make_trace_id():
    stamp = datetime.now().isoformat()
    return SCRIPT_NAME + hashlib.md5((SCRIPT_NAME + stamp).encode("utf-8")).hexdigest()[:8]


def envelope(status, error_code, message, data):
    return {"status": status, "error_code": error_code,
            "message": message, "data": data}


def classify(text):
    hits = {}
    for stream, words in KEYWORDS.items():
        matched = [w for w in words if w in text]
        if matched:
            hits[stream] = matched
    family_voice = any(p in text for p in FAMILY_PATTERNS)
    family_topic = any(t in text for t in FAMILY_TOPIC)

    workstreams = list(hits.keys())
    # 家属身份识别：家属口吻＋咨询走向且无具体任务指令 → 优先路由至接待线
    priority_note = None
    if family_voice and family_topic:
        if "reception" not in workstreams:
            workstreams.insert(0, "reception")
        priority_note = "家属口吻＋走向咨询：优先路由至接待线（reception）"
        hits.setdefault("reception", ["家属口吻"])
    if not workstreams and not family_voice:
        return [], False, 0.0, None

    total_hits = sum(len(v) for v in hits.values())
    confidence = min(0.95, 0.40 + 0.15 * total_hits)
    if family_voice:
        confidence = min(0.95, confidence + 0.10)
    return workstreams, family_voice, round(confidence, 2), priority_note


def main():
    parser = argparse.ArgumentParser(
        prog=SCRIPT_NAME,
        description="意图识别辅助：输入用户文本，输出匹配的工作线标签、家属身份识别与置信度。")
    parser.add_argument("--text", required=True, help="用户输入文本")
    args = parser.parse_args()
    if not args.text.strip():
        print(json.dumps(envelope("error", "ERR_ARGS_MISSING", "--text不能为空", None),
                         ensure_ascii=False, indent=2))
        sys.exit(1)
    workstreams, family_voice, confidence, note = classify(args.text)
    data = {"workstreams": workstreams, "family_voice": family_voice,
            "confidence": confidence}
    if note:
        data["routing_note"] = note
    if not workstreams:
        data["routing_note"] = "未匹配任何工作线：请结合案件阶段人工路由"
    print(json.dumps(envelope("ok", None, "识别完成", data),
                     ensure_ascii=False, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
