#!/usr/bin/env python3
"""
AI Know How 更新脚本
根据输入的 AI 领域周报/资讯，将相关监管动态更新到 AI Know How 知识库中。
"""

import argparse
import os
import sys
from datetime import datetime

# ─────────────────────────────────────────────
# 框架常量：司法管辖区 × 产品条线
# ─────────────────────────────────────────────

JURISDICTIONS = [
    ("美国", "🇺🇸"),
    ("中国大陆", "🇨🇳"),
    ("香港", "🇭🇰"),
    ("欧盟", "🇪🇺"),
    ("日本", "🇯🇵"),
    ("新加坡", "🇸🇬"),
    ("英国", "🇬🇧"),
    ("阿联酋", "🇦🇪"),
]

PRODUCT_LINES = [
    "基础模型与通用 AI (Foundation Models & General AI)",
    "AI 应用与服务 (AI Applications & Services)",
    "AI 生成内容 (AIGC / Generative AI Content)",
    "自动驾驶与机器人 (Autonomous Driving & Robotics)",
    "AI 在金融领域的应用 (AI in Finance)",
    "数据与隐私 (Data & Privacy)",
]

SECTION_TITLES = [
    "监管情况概述",
    "重大执法行动或法院判例",
    "主要法规介绍和立法进展",
]

PLACEHOLDER = "（暂无更新）"

# ─────────────────────────────────────────────
# 生成空白框架
# ─────────────────────────────────────────────

def generate_empty_framework() -> str:
    """生成包含完整框架但内容为空的 Know How 文档。"""
    today = datetime.now().strftime("%Y年%m月%d日")
    lines = []
    lines.append("# AI 全球监管政策 know-how\n")
    lines.append(f"> 本文档持续迭代更新，最后更新日期：{today}\n")
    lines.append("---\n")

    for jurisdiction, flag in JURISDICTIONS:
        lines.append(f"## {flag} {jurisdiction}\n")
        for product in PRODUCT_LINES:
            lines.append(f"### {product}\n")
            for i, section in enumerate(SECTION_TITLES, 1):
                lines.append(f"#### {i}. {section}\n")
                lines.append(f"{PLACEHOLDER}\n")
        lines.append("---\n")

    lines.append("## 附件：参考资料\n")
    lines.append("（脚注来源将随内容更新逐步补充）\n")

    return "\n".join(lines)


# ─────────────────────────────────────────────
# 主流程：读取周报并提示 LLM 更新
# ─────────────────────────────────────────────

def load_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def save_file(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def build_update_prompt(report_text: str, knowhow_text: str) -> str:
    """构建发送给 LLM 的更新提示词。"""
    return f"""你是一名专业的 AI 政策研究员和法律分析师。请根据以下最新 AI 领域资讯，更新 AI 全球监管政策 know-how 知识库。

## 任务要求

1. 仔细阅读【最新资讯】，识别所有涉及 AI 监管的信息（包括：监管机构发布的新规/通知/指引、立法机构推进的法案进展、监管机构对企业的执法行动、法院判决、重要政策声明等）。

2. 将识别到的信息按照"司法管辖区 × 产品条线"进行分类，映射到【当前 Know How】的对应单元中。

3. 在对应单元的三个板块中进行更新：
   - **监管情况概述**：介绍该国在该领域的整体监管方式、主管机构、是否有专门牌照/备案制度
   - **重大执法行动或法院判例**：记录针对头部企业的罚款、民事赔偿、禁令、重要法院判决
   - **主要法规介绍和立法进展**：梳理已生效法规及正在推进的立法草案

4. 写作风格要求：
   - 以散文体（自然语言）为主，避免过度使用项目符号
   - 所有事实性陈述须在文末附脚注，格式为：`[^N]: 参见：[来源名称](URL)`
   - 不得在正文中标注"根据本期资讯"等字样
   - 更新时在现有内容基础上追加或修订，不得删除已有的有效内容
   - 没有新内容的单元保留原有内容（或"暂无更新"），**不得删除板块标题**

5. 输出完整的更新后 Know How 文档（Markdown 格式），保持原有框架结构不变。

---

## 最新资讯

{report_text}

---

## 当前 Know How

{knowhow_text}

---

请直接输出更新后的完整 Know How 文档，不要附加任何说明文字。"""


def call_llm(prompt: str) -> str:
    """调用 OpenAI 兼容接口执行更新。"""
    try:
        from openai import OpenAI
        client = OpenAI()
        response = client.chat.completions.create(
            model="gemini-2.5-flash",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=16000,
        )
        return response.choices[0].message.content
    except ImportError:
        print("错误：未安装 openai 包，请运行 `sudo pip3 install openai`")
        sys.exit(1)
    except Exception as e:
        print(f"错误：LLM 调用失败 - {e}")
        sys.exit(1)


# ─────────────────────────────────────────────
# CLI 入口
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="根据 AI 领域资讯更新 AI 全球监管政策 Know How 知识库"
    )
    parser.add_argument(
        "--report", "-r",
        help="最新 AI 领域资讯/周报的 Markdown 文件路径",
        required=False,
    )
    parser.add_argument(
        "--knowhow", "-k",
        help="当前 Know How 文档路径（如不存在则从零创建）",
        default="/home/ubuntu/ai_knowhow.md",
    )
    parser.add_argument(
        "--output", "-o",
        help="输出文件路径（默认覆盖 knowhow 文件）",
        default=None,
    )
    parser.add_argument(
        "--init",
        action="store_true",
        help="仅生成空白框架文档，不执行更新",
    )
    args = parser.parse_args()

    output_path = args.output or args.knowhow

    # 仅生成空白框架
    if args.init:
        framework = generate_empty_framework()
        save_file(output_path, framework)
        print(f"✅ 已生成空白框架文档：{output_path}")
        return

    # 检查 Know How 文件是否存在，不存在则从零创建
    if not os.path.exists(args.knowhow):
        print(f"⚠️  Know How 文件不存在，将从零创建：{args.knowhow}")
        knowhow_text = generate_empty_framework()
        save_file(args.knowhow, knowhow_text)
    else:
        knowhow_text = load_file(args.knowhow)

    # 检查资讯文件
    if not args.report:
        print("错误：请通过 --report 参数指定资讯文件路径")
        sys.exit(1)
    if not os.path.exists(args.report):
        print(f"错误：资讯文件不存在：{args.report}")
        sys.exit(1)

    report_text = load_file(args.report)

    print("📖 正在读取资讯文件...")
    print("🤖 正在调用 LLM 执行更新（可能需要 30-60 秒）...")

    prompt = build_update_prompt(report_text, knowhow_text)
    updated_content = call_llm(prompt)

    save_file(output_path, updated_content)
    print(f"✅ Know How 已更新并保存至：{output_path}")
    print("\n⚠️  请人工审核输出文件，确认：")
    print("   1. 所有内容已正确映射到对应的「司法管辖区 x 产品条线 x 三板块」结构")
    print("   2. 未有内容的单元保留了完整的三板块框架（填写「暂无更新」）")
    print("   3. 脚注格式正确，来源可追溯")


if __name__ == "__main__":
    main()
