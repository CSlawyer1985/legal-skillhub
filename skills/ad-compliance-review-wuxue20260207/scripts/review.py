#!/usr/bin/env python3
"""
广告公司 AI 合规审查 —— 零依赖审查脚本（纯 Python 标准库）

用法：
  python review.py --client <客户目录> --copy "<待审文案>" [--json] [--config config.json]

功能：
  - 读取客户 banned_words.md（违禁词表）与 brand.md（品牌禁用词）
  - 合并内置"绝对化 / 医疗功效"通用基线词表
  - 对文案做命中扫描，输出违规项（词 / 类型 / 严重度 / 建议）
  - 给出整体风险等级（高 / 中 / 低）
  - 若提供 --config（含 LLM api_key），调用大模型生成合规改写文案
"""
import os
import re
import sys
import json
import time
import argparse
import urllib.request
from pathlib import Path

# ---------------- 国内大模型预设（OpenAI 兼容端点） ----------------
# 用 --preset <名称> 一键切换，省去手填 api_base / chat_model。
# 适配国内主流服务商；api_key 仍从 config.json 或环境变量 AD_REVIEW_API_KEY 读取。
PRESETS = {
    "deepseek":   {"api_base": "https://api.deepseek.com/v1",                  "chat_model": "deepseek-chat"},
    "qwen":       {"api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1", "chat_model": "qwen-plus"},
    "zhipu":      {"api_base": "https://open.bigmodel.cn/api/paas/v4",         "chat_model": "glm-4-flash"},
    "hunyuan":    {"api_base": "https://api.hunyuan.cloud.tencent.com/v1",     "chat_model": "hunyuan-turbo"},
    "doubao":     {"api_base": "https://ark.cn-beijing.volces.com/api/v3",     "chat_model": "doubao-seed-1.6-250615"},
    "kimi":       {"api_base": "https://api.moonshot.cn/v1",                   "chat_model": "moonshot-v1-8k"},
    "siliconflow": {"api_base": "https://api.siliconflow.cn/v1",               "chat_model": "deepseek-ai/DeepSeek-V3"},
}

# ---------------- 内置通用基线（与客户词表合并去重） ----------------
BUILTIN_ABSOLUTE = [
    "第一", "唯一", "顶级", "最佳", "最好", "最高级", "国家级", "极致",
    "史无前例", "最便宜", "全网最低", "销量第一", "第一品牌", "独家",
    "绝对", "万能", "永久", "100%", "立竿见影", "立即见效",
]
BUILTIN_MEDICAL = [
    "治疗", "治愈", "药到病除", "抗炎", "抗菌", "医用", "药用",
    "修复肌肤屏障", "消炎", "杀菌", "防敏",
]

SEV = {"绝对化用语": "高", "医疗功效暗示": "高", "平台特别限制": "中",
       "品牌禁用词": "中", "违禁词(客户)": "中", "疑似绝对化(最X)": "高"}


def _split_list(s):
    """把「A、B，C；D」这类字符串拆成词条，去掉引号与括号。"""
    s = re.sub(r"[「」“”'()（）]", "", s)
    return [t.strip() for t in re.split(r"[、，,；;\\s]+", s) if t.strip()]


def _quoted_terms(text):
    return re.findall(r"[「“'\"](.+?)[」”'\"].", text)


def load_client_terms(client_dir):
    """返回 {term: category}"""
    terms = {}
    bw = Path(client_dir) / "banned_words.md"
    if bw.exists():
        text = bw.read_text(encoding="utf-8", errors="ignore")
        # 按 ## 标题分段
        sections = re.split(r"^##\s+", text, flags=re.M)
        for sec in sections:
            head = sec.splitlines()[0] if sec.splitlines() else ""
            if "绝对化" in head:
                cat = "绝对化用语"
            elif "医疗" in head or "功效" in head:
                cat = "医疗功效暗示"
            elif "平台" in head:
                cat = "平台特别限制"
            else:
                cat = "违禁词(客户)"
            # 引号内词条
            for q in re.findall(r"[「“'\"](.+?)[」”'\"]", sec):
                terms[q.strip()] = cat
            # 行内列表（、，分隔）
            for line in sec.splitlines():
                line = line.lstrip("-* ").strip()
                if ("严禁" in line or "、" in line or "，" in line) and len(line) < 120:
                    for t in _split_list(line):
                        if len(t) >= 1:
                            terms.setdefault(t, cat)
    # 品牌禁用词
    brand = Path(client_dir) / "brand.md"
    if brand.exists():
        btext = brand.read_text(encoding="utf-8", errors="ignore")
        for line in btext.splitlines():
            if "禁用词" in line:
                for t in _split_list(line):
                    if t and t not in ("禁用词",):
                        terms.setdefault(t, "品牌禁用词")
    # 内置基线
    for t in BUILTIN_ABSOLUTE:
        terms.setdefault(t, "绝对化用语")
    for t in BUILTIN_MEDICAL:
        terms.setdefault(t, "医疗功效暗示")
    return terms


def validate_client_dir(client_dir):
    """校验 --client 路径，避免静默回退内置基线。
    返回 (ok, message)：
      ok=False 且 message 非空 -> 致命错误，应中止（路径不存在 / 不是目录）
      ok=True  且 message 非空 -> 警告（目录存在但缺客户词表，将回退内置基线）
      ok=True  且 message 空   -> 正常
    """
    p = Path(client_dir)
    if not p.exists():
        return False, (f"客户资料目录不存在：{client_dir}\n"
                       f"请检查 --client 路径是否正确（应为含 banned_words.md / brand.md 的目录）。")
    if not p.is_dir():
        return False, (f"--client 指向的不是目录而是文件：{client_dir}\n"
                       f"请改为传入包含 banned_words.md / brand.md 的目录路径。")
    bw = p / "banned_words.md"
    brand = p / "brand.md"
    if not bw.exists() and not brand.exists():
        return True, (f"【警告】目录 {client_dir} 下未找到 banned_words.md 或 brand.md，"
                      f"将仅使用内置通用基线词库审查（等于未加载客户专属词表）。")
    return True, ""


def scan(copy, terms):
    violations = []
    seen = set()
    low = copy.lower()
    for term, cat in terms.items():
        if not term:
            continue
        hit = (term.lower() in low) if re.search(r"[a-z0-9]", term) else (term in copy)
        if hit and term not in seen:
            seen.add(term)
            violations.append({
                "term": term,
                "category": cat,
                "severity": SEV.get(cat, "中"),
                "suggestion": _suggest(term, cat),
            })
    # 启发式：最 + 汉字
    for m in re.findall(r"最[一-鿿]", copy):
        if m not in seen:
            seen.add(m)
            violations.append({
                "term": m,
                "category": "疑似绝对化(最X)",
                "severity": "高",
                "suggestion": "慎用绝对化表述，改为客观描述（如'更''较'）",
            })
    # 风险等级
    sevs = [v["severity"] for v in violations]
    if "高" in sevs:
        level = "高"
    elif "中" in sevs:
        level = "中"
    elif violations:
        level = "低"
    else:
        level = "通过"
    return violations, level


def _suggest(term, cat):
    if cat == "绝对化用语":
        return f"删除或替换'{term}'，避免绝对化（改用'更''较''之一'等）"
    if cat == "医疗功效暗示":
        return f"删除'{term}'，美妆/普通商品不得暗示医疗功效"
    if cat == "平台特别限制":
        return f"删除'{term}'，违反平台比价/导流限制"
    if cat == "品牌禁用词":
        return f"替换为符合品牌调性的表述，规避'{term}'"
    return f"复核并移除'{term}'"


def llm_rewrite(copy, violations, config):
    cfg = config.get("llm", {})
    # api_key 来源优先级：config.json > 环境变量 AD_REVIEW_API_KEY（便于密钥不落盘）
    api_key = cfg.get("api_key") or os.environ.get("AD_REVIEW_API_KEY")
    if not api_key:
        return None
    items = "\n".join(f"- {v['term']}（{v['category']}）：{v['suggestion']}" for v in violations)
    prompt = (
        "你是广告合规专家。下面是待审广告文案及其违规项，请在不改变原意与核心卖点的前提下，"
        "改写为合规版本，并在末尾用『修改说明：』简要说明改了哪里。\n\n"
        f"【原文】\n{copy}\n\n【违规项】\n{items}"
    )
    url = cfg["api_base"].rstrip("/") + "/chat/completions"
    payload = json.dumps({
        "model": cfg.get("chat_model", "gpt-4o-mini"),
        "temperature": cfg.get("temperature", 0.2),
        "messages": [
            {"role": "system", "content": "只输出合规改写文案与简要修改说明，不要多余解释。"},
            {"role": "user", "content": prompt},
        ],
    }).encode()
    # 重试配置：网络抖动 / 限流 / 5xx 等瞬时故障自动退避重试，避免一次失败就放弃
    max_retries = int(cfg.get("max_retries", 3))
    base_delay = float(cfg.get("retry_delay", 1.5))

    last_msg = None
    for attempt in range(max_retries + 1):
        try:
            req = urllib.request.Request(url, data=payload, headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + api_key,
            })
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode())["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            code = getattr(e, "code", 0)
            if code in (401, 403):
                return ("（AI 改写暂不可用：API Key 无效或未授权（请检查 config.json 的 api_key 是否正确）。"
                        "你可先按下方建议手动修改。）")
            if code == 404:
                return ("（AI 改写暂不可用：模型接口地址不存在（请检查 config.json 的 api_base / chat_model "
                        "是否匹配该服务商）。你可先按下方建议手动修改。）")
            if code == 429:
                last_msg = "请求被限流（HTTP 429）"  # 可重试
            elif 500 <= code < 600:
                last_msg = f"模型服务暂时不可用（HTTP {code}）"  # 可重试
            else:
                return (f"（AI 改写暂不可用：模型服务返回错误码 {code}。"
                        f"你可先按下方建议手动修改。）")
        except urllib.error.URLError:
            last_msg = "网络异常，无法连接模型服务"  # 可重试
        except Exception as e:
            last_msg = str(e)[:160]  # 其他未知异常，也尝试重试
        # 未到最后一轮则按指数退避（1x, 2x, 4x ...）后重试
        if attempt < max_retries:
            time.sleep(base_delay * (2 ** attempt))
    return (f"（AI 改写暂不可用：已自动重试 {max_retries} 次仍失败（{last_msg}）。"
            f"你可先按下方建议手动修改，或检查网络 / 配置后重试。）")


def main():
    ap = argparse.ArgumentParser(description="广告公司 AI 合规审查")
    ap.add_argument("--client", default=None, help="客户资料目录（含 banned_words.md / brand.md）")
    ap.add_argument("--copy", default=None, help="待审广告文案")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--config", default=None, help="可选 config.json（含 LLM api_key 以生成改写）")
    ap.add_argument("--preset", default=None,
                    help="国内大模型预设：deepseek/qwen/zhipu/hunyuan/doubao/kimi/siliconflow"
                         "（一键适配，配合 --config 或环境变量 AD_REVIEW_API_KEY 提供 key）")
    ap.add_argument("--list-presets", action="store_true", help="列出所有内置国内模型预设并退出")
    args = ap.parse_args()

    if args.list_presets:
        print("内置国内大模型预设（--preset <名称>）：")
        for name, p in PRESETS.items():
            print(f"  {name:12s} {p['api_base']}")
            print(f"  {'':12s} -> 默认模型：{p['chat_model']}")
        return

    if not args.client or not args.copy:
        print("【错误】除 --list-presets 外，必须同时提供 --client 与 --copy。", file=sys.stderr)
        sys.exit(2)

    ok, msg = validate_client_dir(args.client)
    if not ok:
        print("【错误】" + msg, file=sys.stderr)
        sys.exit(2)
    if msg:
        print(msg, file=sys.stderr)
    terms = load_client_terms(args.client)
    violations, level = scan(args.copy, terms)

    # 统一加载 LLM 配置：config.json（显式优先） + 预设（一键适配） + 环境变量（密钥）
    cfg = {}
    if args.config and Path(args.config).exists():
        try:
            cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
        except Exception as e:
            print(f"【警告】config.json 解析失败，将跳过 AI 改写：{e}", file=sys.stderr)
    llm = cfg.setdefault("llm", {})
    if args.preset:
        if args.preset not in PRESETS:
            print(f"【错误】未知预设 '{args.preset}'。可用：{', '.join(PRESETS)}", file=sys.stderr)
            sys.exit(2)
        llm["api_base"] = PRESETS[args.preset]["api_base"]
        llm["chat_model"] = PRESETS[args.preset]["chat_model"]
    use_llm = bool(args.config) or bool(args.preset)

    if args.json:
        out = {"risk_level": level, "violations": violations}
        if msg:
            out["client_warning"] = msg
        if use_llm:
            out["rewrite"] = llm_rewrite(args.copy, violations, cfg)
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return

    print("=" * 48)
    print("广告文案合规审查报告")
    print("=" * 48)
    print(f"整体风险等级：{level}\n")
    if not violations:
        print("未检出违规词，文案合规。")
    else:
        for i, v in enumerate(violations, 1):
            print(f"{i}. 「{v['term']}」  [{v['category']} / 严重度:{v['severity']}]")
            print(f"   建议：{v['suggestion']}")
    if use_llm:
        rw = llm_rewrite(args.copy, violations, cfg)
        if rw:
            print("\n--- 建议改写文案 ---\n" + rw)
    print("\n" + "=" * 48)


if __name__ == "__main__":
    main()
