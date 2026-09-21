#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
step1 OCR识别录入：识别投诉截图，提取结构化字段，输出JSON
用法: python3 step1_ocr_intake.py --image <截图路径> [--image <更多截图>...]
密钥: 环境变量 OCR_API_KEY（视觉模型，兼容DashScope qwen-vl接口）
"""
import argparse
import base64
import json
import os
import sys
import urllib.request

API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"

SCHEMA = ("请识别这张工商投诉工单截图，提取所有可见字段，以JSON格式返回（只返回JSON）。"
          "不得猜测；看不清的值留空，并为每个字段给出0到1的置信度及对应原文片段："
          '{"投诉编号":"","投诉人":"","联系方式":"","被投诉主体":"","投诉类型":"",'
          '"投诉内容":"","诉求金额":"","截止日期":"","订单号":"","交易号":"","备注":"",'
          '"_confidence":{},"_source_spans":{}}')


def encode_image(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def ocr_one(api_key: str, image_b64: str) -> dict:
    payload = {
        "model": "qwen-vl-max",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}},
                {"type": "text", "text": SCHEMA},
            ],
        }],
        "temperature": 0.1,
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {api_key}",
                 "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    text = data["choices"][0]["message"]["content"].strip()
    # 容错：剥掉可能的markdown代码块包裹
    if text.startswith("```"):
        text = text.strip("`").lstrip("json").strip()
    return json.loads(text)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", action="append", required=True, help="截图路径，可多次传入")
    parser.add_argument("--out", default="ocr_result.json", help="输出JSON路径")
    args = parser.parse_args()

    api_key = os.environ.get("OCR_API_KEY", "")
    if not api_key:
        print("未设置 OCR_API_KEY，识别未执行", file=sys.stderr)
        sys.exit(2)

    results = []
    for path in args.image:
        record = ocr_one(api_key, encode_image(path))
        record["_source_image"] = os.path.basename(path)
        record["_ocr_model"] = "qwen-vl-max"
        record["_ocr_schema_version"] = 2
        results.append(record)
        print(f"[OK] {path}: 投诉人={record.get('投诉人', '?')} 类型={record.get('投诉类型', '?')}")

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"共识别 {len(results)} 条，已写入 {args.out}")


if __name__ == "__main__":
    main()
