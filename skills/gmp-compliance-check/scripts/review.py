#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GMP 合规自检核心脚本（零依赖，纯标准库）

用法:
  python review.py --client <基线目录> --docs <待检资料...>
  python review.py --client <基线目录> --copy "粘贴的文本"
  python review.py --client <基线目录> --docs <待检资料> --json
  python review.py --client <基线目录> --docs <待检资料> --config config.json   # 启用大模型语义评估

基线目录需含 gmp_requirements.md（格式见 sample_data/demo_client/gmp_requirements.md）。
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request

# ---------------------------------------------------------------------------
# 基线解析
# ---------------------------------------------------------------------------

RISK_ORDER = {"高": 3, "中": 2, "低": 1}
STATUS_TAG = {"覆盖": "✔", "部分覆盖": "◐", "缺失": "✘", "未知": "?"}


class ChineseArgumentParser(argparse.ArgumentParser):
    """让 argparse 的报错（缺参 / 无法识别参数等）用中文，并指出位置。"""

    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(2, f"参数错误：{_zh_arg_message(message)}\n")


def _zh_arg_message(message):
    m = re.match(r"the following arguments are required:\s*(.+)", message)
    if m:
        return f"缺少必填参数：{m.group(1).strip()}（用 --help 查看必填项）"
    if message.startswith("unrecognized arguments:"):
        return "无法识别的参数：" + message[len("unrecognized arguments:"):].strip()
    if "expected one argument" in message:
        return "有参数缺少取值，请检查是否漏写参数值。"
    if "invalid " in message and "value" in message:
        return "参数取值无效：" + message
    return message


def friendly_mail_error(e):
    """把 SMTP 常见英文异常翻译成人话，便于客户/销售看懂。"""
    s = str(e)
    low = s.lower()
    if "authentication" in low or "535" in s or "username" in low or "password" in low:
        return "邮箱账号或密码/授权码错误"
    if "wrong_version" in low or "ssl" in low or "starttls" in low:
        return "SSL/TLS 加密方式不匹配（465 用 SSL，587 用 STARTTLS，请核对 smtp_port）"
    if "connection" in low or "getaddrinfo" in low or "name or service" in low:
        return "连不上邮件服务器，请检查 smtp_host/port 与网络"
    if "timed out" in low or "timeout" in low:
        return "连接邮件服务器超时"
    return f"邮件发送失败：{s}"


def friendly_net_error(e):
    """把 urllib 推送常见英文异常翻译成人话。"""
    s = str(e)
    low = s.lower()
    if "connection" in low or "getaddrinfo" in low or "name or service" in low:
        return "连不上推送地址，请检查 url 与网络"
    if "timed out" in low or "timeout" in low:
        return "推送超时"
    if "forbidden" in low or "401" in low or "403" in low:
        return "推送被拒绝（鉴权/权限问题，请检查 headers）"
    if "http" in low and ("404" in s or "410" in s):
        return "推送地址不存在（404/410），请检查 url"
    return f"推送失败：{s}"


def parse_baseline(path):
    """解析 gmp_requirements.md，返回 domains 列表。

    格式约定（脚本严格解析，注意冒号可用中文「：」或英文「:」）：
        ## 域名称  weight=20
        - 检查项：检查项名称  risk=高
          keywords: 关键词1、关键词2、关键词3
          advice: 整改建议文本
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"基线文件不存在: {path}")
    domains = []
    cur_domain = None
    cur_item = None
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            m = re.match(r"^##\s+(.+?)\s+weight=(\d+)\s*$", line)
            if m:
                cur_domain = {"name": m.group(1).strip(), "weight": int(m.group(2)), "items": []}
                domains.append(cur_domain)
                cur_item = None
                continue
            m = re.match(r"^-\s*检查项[:：]\s*(.+?)\s*risk=(高|中|低)\s*$", line)
            if m and cur_domain is not None:
                cur_item = {
                    "name": m.group(1).strip(),
                    "risk": m.group(2),
                    "keywords": [],
                    "advice": "",
                }
                cur_domain["items"].append(cur_item)
                continue
            if cur_item is not None:
                mk = re.match(r"^\s*keywords[:：]\s*(.+)$", line)
                if mk:
                    parts = re.split(r"[、，,]+", mk.group(1).strip())
                    cur_item["keywords"] = [p.strip() for p in parts if p.strip()]
                    continue
                ma = re.match(r"^\s*advice[:：]\s*(.+)$", line)
                if ma:
                    cur_item["advice"] = ma.group(1).strip()
                    continue
    if not domains:
        raise ValueError("基线文件未解析到任何合规域，请检查格式（## 域名称 weight=N）。")
    return domains


# ---------------------------------------------------------------------------
# 语料加载
# ---------------------------------------------------------------------------

def load_corpus(paths):
    """读取文件或目录（.txt/.md）拼接为一篇语料。"""
    texts = []
    files = []
    for p in paths:
        if os.path.isdir(p):
            for root, _, names in os.walk(p):
                for n in sorted(names):
                    if n.lower().endswith((".txt", ".md")):
                        files.append(os.path.join(root, n))
        elif os.path.isfile(p):
            files.append(p)
    for fp in files:
        try:
            with open(fp, encoding="utf-8", errors="ignore") as f:
                texts.append(f.read())
        except Exception:
            texts.append("")
    return "\n".join(texts)


# ---------------------------------------------------------------------------
# 评估
# ---------------------------------------------------------------------------

def evaluate(domains, corpus):
    results = []
    for d in domains:
        items_res = []
        for it in d["items"]:
            kws = [k for k in it["keywords"] if len(k) >= 2]
            if not kws:
                items_res.append({
                    "name": it["name"], "risk": it["risk"], "keywords": kws,
                    "hit": 0, "total": 0, "ratio": 0.0, "status": "未知",
                    "advice": it["advice"],
                })
                continue
            hit = sum(1 for k in kws if k in corpus)
            ratio = hit / len(kws)
            if hit == 0:
                status = "缺失"
            elif ratio < 0.5:
                status = "部分覆盖"
            else:
                status = "覆盖"
            items_res.append({
                "name": it["name"], "risk": it["risk"], "keywords": kws,
                "hit": hit, "total": len(kws), "ratio": ratio, "status": status,
                "advice": it["advice"],
            })
        domain_score = (sum(i["ratio"] for i in items_res) / len(items_res)) if items_res else 0.0
        results.append({"name": d["name"], "weight": d["weight"], "items": items_res, "score": domain_score})

    total_w = sum(d["weight"] for d in results) or 1
    overall = sum(d["score"] * d["weight"] for d in results) / total_w * 100
    overall_risk = _compute_risk(results)
    return {"domains": results, "overall_score": round(overall, 1), "overall_risk": overall_risk}


def _compute_risk(results):
    risk = "低"
    for d in results:
        for i in d["items"]:
            if i["status"] == "缺失" and i["risk"] == "高":
                return "高"
            if risk != "高":
                if (i["status"] == "缺失" and i["risk"] == "中") or i["status"] == "部分覆盖":
                    risk = "中"
    return risk


# ---------------------------------------------------------------------------
# 可选：大模型语义级评估（仅对「缺失/部分覆盖」项做确认）
# ---------------------------------------------------------------------------

def llm_assess(item, corpus, config):
    """用大模型对单条检查项做语义确认，返回 (verdict, note)。失败返回 (None, 原因)。"""
    api_key = config.get("api_key")
    if not api_key:
        return None, "未配置 api_key"
    api_base = config.get("api_base", "https://api.openai.com/v1").rstrip("/")
    model = config.get("model", "gpt-4o-mini")
    snippet = corpus[:4000]
    prompt = (
        "你是GMP合规审核专家。下面是一份制药企业信息化/质量体系资料片段，"
        "请判断它是否满足该GMP合规要求。\n"
        f"要求：{item['name']}\n风险等级：{item['risk']}\n"
        f"资料片段：\n'''{snippet}'''\n"
        '只输出JSON：{"verdict":"覆盖|部分覆盖|缺失","note":"一句话理由"}'
    )
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
    }).encode("utf-8")
    req = urllib.request.Request(api_base + "/chat/completions", data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {api_key}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"]
        m = re.search(r"\{.*\}", content, re.S)
        if m:
            obj = json.loads(m.group(0))
            return obj.get("verdict"), obj.get("note", "")
    except urllib.error.HTTPError as e:
        code = e.code
        return {
            401: (None, "大模型鉴权失败(401)，请检查 api_key"),
            403: (None, "大模型鉴权失败(403)，请检查 api_key/权限"),
            404: (None, "模型地址/名称不匹配(404)，请检查 api_base/chat_model"),
            429: (None, "大模型限流(429)，请稍后重试"),
        }.get(code, (None, f"大模型调用失败({code})"))
    except Exception as e:  # noqa: BLE001
        return None, f"大模型调用异常：{e}"
    return None, "大模型返回解析失败"


def apply_semantic(result, domains, corpus, config):
    """对缺失/部分覆盖项调用大模型修正 status，并重算整体风险。"""
    for d in result["domains"]:
        for i in d["items"]:
            if i["status"] in ("缺失", "部分覆盖"):
                v, note = llm_assess(i, corpus, config)
                if v in ("覆盖", "部分覆盖", "缺失"):
                    i["status"] = v
                    if note:
                        i["llm_note"] = note
    result["overall_risk"] = _compute_risk(result["domains"])


# ---------------------------------------------------------------------------
# 报告
# ---------------------------------------------------------------------------

def build_text_report(result, client_name="客户"):
    L = []
    L.append("=" * 58)
    L.append(f"GMP 合规自检报告  |  对象：{client_name}")
    L.append("=" * 58)
    L.append(f"综合合规覆盖度：{result['overall_score']} 分（满分100）")
    L.append(f"整体风险等级：{result['overall_risk']}")
    L.append("")
    for d in result["domains"]:
        pct = int(d["score"] * 100)
        L.append(f"■ {d['name']}  [权重 {d['weight']}]  覆盖度 {pct}%")
        for i in d["items"]:
            tag = STATUS_TAG.get(i["status"], "?")
            L.append(f"   {tag} [{i['risk']}] {i['name']}  ({i['hit']}/{i['total']} 关键词命中)")
            if i["status"] in ("缺失", "部分覆盖") and i["advice"]:
                L.append(f"       整改建议：{i['advice']}")
            if i.get("llm_note"):
                L.append(f"       语义评估：{i['llm_note']}")
        L.append("")
    miss = [(d["name"], i["name"], i["risk"]) for d in result["domains"] for i in d["items"]
            if i["status"] in ("缺失", "部分覆盖")]
    if miss:
        L.append("—— 待整改项汇总 ——")
        for dn, iname, risk in miss:
            L.append(f"  [{risk}] {dn} / {iname}")
    return "\n".join(L)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _ensure_utf8():
    if getattr(sys.stdout, "encoding", "utf-8") != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass


def main():
    _ensure_utf8()
    ap = ChineseArgumentParser(description="GMP 合规自检（零依赖）")
    ap.add_argument("--client", required=True, help="含 gmp_requirements.md 的基线目录")
    ap.add_argument("--docs", nargs="+", help="待检文档/目录（.txt/.md）")
    ap.add_argument("--copy", help="直接粘贴的待检文本")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--config", help="大模型配置 json（启用语义级评估）")
    ap.add_argument("--no-semantic", action="store_true", help="即便有 --config 也不调用大模型")
    ap.add_argument("--name", default="客户", help="报告抬头名称")
    args = ap.parse_args()

    client_dir = args.client
    if not os.path.isdir(client_dir):
        print(
            f"错误：基线目录不存在：{client_dir}\n"
            f"请确认 --client 指向一个【文件夹】，且其中包含 gmp_requirements.md。",
            file=sys.stderr,
        )
        sys.exit(2)
    baseline_path = os.path.join(client_dir, "gmp_requirements.md")
    if not os.path.isfile(baseline_path):
        print(f"错误：基线目录 {client_dir} 中未找到 gmp_requirements.md。", file=sys.stderr)
        sys.exit(2)
    try:
        domains = parse_baseline(baseline_path)
    except Exception as e:
        print(f"错误：{e}", file=sys.stderr)
        sys.exit(2)

    if args.copy:
        corpus = args.copy
    elif args.docs:
        corpus = load_corpus(args.docs)
    else:
        print("错误：请通过 --docs 指定待检资料，或用 --copy 粘贴文本", file=sys.stderr)
        sys.exit(2)

    if args.docs:
        _missing = [p for p in args.docs if not os.path.exists(p)]
        if _missing:
            print(f"提示：以下待检路径不存在，已忽略：{', '.join(_missing)}", file=sys.stderr)

    if not corpus.strip():
        print("错误：待检资料为空（仅支持 .txt/.md；Word/PDF 需先导出纯文本）", file=sys.stderr)
        sys.exit(2)

    result = evaluate(domains, corpus)

    if args.config and not args.no_semantic:
        try:
            with open(args.config, encoding="utf-8") as f:
                config = json.load(f)
            apply_semantic(result, domains, corpus, config)
        except Exception as e:
            print(f"提示：大模型配置加载/调用失败，已回退纯规则评估：{e}", file=sys.stderr)

    if args.json:
        print(json.dumps({"client": args.name, **result}, ensure_ascii=False, indent=2))
    else:
        print(build_text_report(result, args.name))


if __name__ == "__main__":
    main()
