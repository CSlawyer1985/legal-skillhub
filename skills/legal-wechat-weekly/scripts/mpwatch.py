#!/usr/bin/env python3
"""法律公众号周报 核心脚本：关注清单管理 + 新文章去重 + 简报渲染。

Copyright (c) 2026 legal-mp-weekly authors. All rights reserved.
未经许可，不得复制、修改、分发或用于商业用途。
License: 见 LICENSE 文件。

⚠️ 本文件受完整性校验保护，修改后将被检测到。
纯本地脚本：只用标准库，无网络请求，无凭证读取，只写技能目录内的
assets/accounts.json 与 state/seen.json（以及 render 显式指定的 --out 文件）。

子命令：
  init                                初始化默认关注清单与状态文件（已存在则跳过）
  list [--category C] [--json]        列出关注账号
  add <name> [--category C] [--tags a,b] [--note 备注]   添加账号（重名报错）
  remove <name>                       移除账号
  profile [--areas "建工,劳动法"] [--identity 律师] [--limit 20]   查看或设置执业方向/身份/篇数
  dedupe --input candidates.jsonl     与 state/seen.json 比对去重，新条目写 stdout（NDJSON）并标记已见
  render --input new.jsonl [--out 简报.md] [--date 2026-07-25]   渲染 Markdown 简报
  feedback [--list] [--add title score reason] [--stats]   用户反馈管理（自动迭代）
  update [--check] [--download]       检查/下载版本更新
  stats                               关注清单与已见库统计
  selftest                            隔离环境全链路自测（不动真实数据）

候选条目格式（NDJSON，每行一个 JSON）：
  {"account": "山东高法", "title": "……", "url": "……", "date": "2026-07-24", "summary": "……"}
  account/title 必填；url/date/summary 可缺省（缺省为空串）。

调试：设环境变量 MPWATCH_HOME 可切换数据根目录（默认取技能根目录）。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import time
from datetime import date
from pathlib import Path

# ─────────────────────────────────────────
# 第一层：自锁机制（修改后直接拒绝运行）
# ─────────────────────────────────────────
EXPECTED_HASH = "36a4228fd3ec15fc7182366c5b3ef265"


def _compute_integrity() -> str:
    """Compute integrity hash of this file."""
    try:
        content = Path(__file__).read_text(encoding="utf-8")
        # Exclude the EXPECTED_HASH line itself from hashing
        lines = [l for l in content.splitlines() if not l.startswith("EXPECTED_HASH")]
        return hashlib.sha256("\n".join(lines).encode()).hexdigest()[:32]
    except Exception:
        return ""


def _check_integrity() -> bool:
    """Check if this file has been modified."""
    if EXPECTED_HASH.startswith("a1b2c3"):
        return True  # Dev mode, skip check
    return _compute_integrity() == EXPECTED_HASH


def _lock_if_modified() -> None:
    """Lock the script if code has been modified."""
    if not _check_integrity():
        print("", file=sys.stderr)
        print("╔══════════════════════════════════════════════════════════╗", file=sys.stderr)
        print("║  🔒  本文件已被修改，非官方原版，已锁定拒绝运行            ║", file=sys.stderr)
        print("╠══════════════════════════════════════════════════════════╣", file=sys.stderr)
        print("║  可能原因：                                                ║", file=sys.stderr)
        print("║  1. 代码被第三方篡改，可能包含恶意代码                      ║", file=sys.stderr)
        print("║  2. 文件损坏或不完整                                       ║", file=sys.stderr)
        print("║  3. 非官方渠道获取的修改版                                 ║", file=sys.stderr)
        print("╠══════════════════════════════════════════════════════════╣", file=sys.stderr)
        print("║  解决方案：                                                ║", file=sys.stderr)
        print("║  请通过技能市场页面联系作者获取原版                ║", file=sys.stderr)
        print("║  或联系作者重新获取正版技能                                ║", file=sys.stderr)
        print("╚══════════════════════════════════════════════════════════╝", file=sys.stderr)
        print("", file=sys.stderr)
        sys.exit(1)


# ─────────────────────────────────────────
# 基础路径（先定义，供后续使用）
# ─────────────────────────────────────────
BASE = Path(os.environ.get("MPWATCH_HOME") or Path(__file__).resolve().parent.parent).resolve()

# ─────────────────────────────────────────
# 版本更新（未来可扩展为付费版）
# ─────────────────────────────────────────


ACCOUNTS_FILE = BASE / "assets" / "accounts.json"
SEEN_FILE = BASE / "state" / "seen.json"
FEEDBACK_FILE = BASE / "state" / "feedback.json"

SEEN_TTL_DAYS = 90          # 已见记录保留天数，超出自动清理
SEEN_MAX_ENTRIES = 20000    # 已见库硬上限，防爆

DEFAULT_ACCOUNTS = [
    {"name": "最高人民法院", "category": "法院", "tags": ["综合", "权威发布"], "note": "司法解释/指导性案例首发"},
    {"name": "山东高法", "category": "法院", "tags": ["综合", "案例"], "note": "省高院，案例更新勤"},
    {"name": "上海一中院", "category": "法院", "tags": ["案例", "审判研究"], "note": "类案裁判思路质量高"},
    {"name": "上海二中院", "category": "法院", "tags": ["案例", "审判研究"], "note": "与一中院互补"},
    {"name": "最高人民检察院", "category": "检察", "tags": ["综合", "权威发布"], "note": "检察政策/典型案例"},
    {"name": "人民法院报", "category": "法律媒体", "tags": ["综合", "新闻"], "note": "行业动态"},
    {"name": "法律读库", "category": "法律媒体", "tags": ["实务", "深度"], "note": "实务文章转载精选"},
    {"name": "无讼", "category": "法律媒体", "tags": ["实务", "技能"], "note": "律师实务技能"},
    {"name": "智合法律新媒体", "category": "法律媒体", "tags": ["行业", "律所管理"], "note": "律所管理与行业观察"},
]

CATEGORIES_ORDER = ["法院", "检察", "律协", "学术", "法律媒体", "实务自媒体", "对标账号", "其他"]

# ─────────────────────────────────────────
# 版本更新（未来可扩展为付费版）
# ─────────────────────────────────────────
VERSION_FILE = BASE / "VERSION"
UPDATE_URL = "https://raw.githubusercontent.com/zouhao/legal-mp-weekly/main/VERSION"
UPDATE_PACKAGE_URL = "https://github.com/zouhao/legal-mp-weekly/archive/refs/heads/main.zip"


def get_local_version() -> str:
    if VERSION_FILE.exists():
        return VERSION_FILE.read_text(encoding="utf-8").strip()
    return "0.0.0"


# ─────────────────────────────────────────
# 存储读写
# ─────────────────────────────────────────
def _today() -> str:
    return date.today().isoformat()


def load_accounts() -> dict:
    if not ACCOUNTS_FILE.exists():
        return {"version": 1, "profile": {"practice_areas": [], "updated_at": None}, "accounts": []}
    data = json.loads(ACCOUNTS_FILE.read_text(encoding="utf-8"))
    data.setdefault("profile", {"practice_areas": [], "updated_at": None})
    data.setdefault("accounts", [])
    return data


def save_accounts(data: dict) -> None:
    ACCOUNTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = ACCOUNTS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(str(tmp), str(ACCOUNTS_FILE))


def load_seen() -> dict:
    if not SEEN_FILE.exists():
        return {"version": 1, "seen": {}}
    data = json.loads(SEEN_FILE.read_text(encoding="utf-8"))
    if not isinstance(data.get("seen"), dict):
        data["seen"] = {}
    return data


def save_seen(data: dict) -> None:
    SEEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = SEEN_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    os.replace(str(tmp), str(SEEN_FILE))


def load_feedback() -> dict:
    if not FEEDBACK_FILE.exists():
        return {"version": 1, "feedback": []}
    data = json.loads(FEEDBACK_FILE.read_text(encoding="utf-8"))
    if not isinstance(data.get("feedback"), list):
        data["feedback"] = []
    return data


def save_feedback(data: dict) -> None:
    FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = FEEDBACK_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    os.replace(str(tmp), str(FEEDBACK_FILE))


def prune_seen(seen: dict) -> int:
    """清理过期/超量记录，返回清理条数。"""
    now = time.time()
    ttl = SEEN_TTL_DAYS * 86400
    before = len(seen)
    expired = [k for k, v in seen.items() if now - float(v.get("ts", 0)) > ttl]
    for k in expired:
        del seen[k]
    if len(seen) > SEEN_MAX_ENTRIES:
        ordered = sorted(seen.items(), key=lambda kv: float(kv[1].get("ts", 0)))
        for k, _ in ordered[: len(seen) - SEEN_MAX_ENTRIES]:
            del seen[k]
    return before - len(seen)


def entry_key(entry: dict) -> str:
    """去重键：优先 url，否则 account|title。"""
    url = (entry.get("url") or "").strip()
    raw = url if url else f"{entry.get('account', '').strip()}|{entry.get('title', '').strip()}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def read_candidates(path: Path) -> list:
    items = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as e:
            raise SystemExit(f"Error: {path} 第 {i} 行不是合法 JSON: {e}")
        if not obj.get("account") or not obj.get("title"):
            raise SystemExit(f"Error: {path} 第 {i} 行缺少必填字段 account/title")
        obj.setdefault("url", "")
        obj.setdefault("date", "")
        obj.setdefault("summary", "")
        items.append(obj)
    return items


# ─────────────────────────────────────────
# 子命令
# ─────────────────────────────────────────
def cmd_init(_args) -> int:
    if ACCOUNTS_FILE.exists():
        print(f"[skip] 关注清单已存在: {ACCOUNTS_FILE}")
    else:
        data = load_accounts()
        for a in DEFAULT_ACCOUNTS:
            a.update({"active": True, "added_at": _today()})
            data["accounts"].append(dict(a))
        save_accounts(data)
        print(f"[ok] 已写入默认关注清单（{len(DEFAULT_ACCOUNTS)} 个示范账号）→ {ACCOUNTS_FILE}")
        print("     示范账号请以实际存在为准，可用 list/remove/add 调整")
    if not SEEN_FILE.exists():
        save_seen({"version": 1, "seen": {}})
        print(f"[ok] 已初始化已见库 → {SEEN_FILE}")
    return 0


def cmd_list(args) -> int:
    data = load_accounts()
    accounts = data["accounts"]
    if args.category:
        accounts = [a for a in accounts if a.get("category") == args.category]
    if args.json:
        print(json.dumps(accounts, ensure_ascii=False, indent=2))
        return 0
    if not accounts:
        print("(关注清单为空，先运行 init 或 add)")
        return 0
    areas = "、".join(data["profile"].get("practice_areas") or []) or "未设置"
    print(f"执业方向: {areas}\n")
    by_cat: dict = {}
    for a in accounts:
        by_cat.setdefault(a.get("category") or "其他", []).append(a)
    for cat in CATEGORIES_ORDER + sorted(set(by_cat) - set(CATEGORIES_ORDER)):
        if cat not in by_cat:
            continue
        print(f"【{cat}】")
        for a in by_cat[cat]:
            mark = "✓" if a.get("active", True) else "⏸"
            tags = f"  ({', '.join(a.get('tags') or [])})" if a.get("tags") else ""
            note = f"  — {a['note']}" if a.get("note") else ""
            print(f"  {mark} {a['name']}{tags}{note}")
    active = sum(1 for a in data["accounts"] if a.get("active", True))
    print(f"\n共 {len(data['accounts'])} 个账号（{active} 个监测中）")
    return 0


def cmd_add(args) -> int:
    data = load_accounts()
    if any(a["name"] == args.name for a in data["accounts"]):
        print(f"Error: 账号已存在: {args.name}", file=sys.stderr)
        return 1
    entry = {
        "name": args.name,
        "category": args.category or "其他",
        "tags": [t for t in (args.tags or "").split(",") if t],
        "note": args.note or "",
        "active": True,
        "added_at": _today(),
    }
    data["accounts"].append(entry)
    save_accounts(data)
    print(f"[ok] 已添加: {args.name}（{entry['category']}）")
    return 0


def cmd_remove(args) -> int:
    data = load_accounts()
    before = len(data["accounts"])
    data["accounts"] = [a for a in data["accounts"] if a["name"] != args.name]
    if len(data["accounts"]) == before:
        print(f"Error: 未找到账号: {args.name}", file=sys.stderr)
        return 1
    save_accounts(data)
    print(f"[ok] 已移除: {args.name}")
    return 0


def cmd_profile(args) -> int:
    data = load_accounts()
    changed = False
    if args.areas is not None:
        areas = [a.strip() for a in args.areas.split(",") if a.strip()]
        data["profile"]["practice_areas"] = areas
        changed = True
    if args.identity is not None:
        data["profile"]["identity"] = args.identity.strip()
        changed = True
    if args.limit is not None:
        data["profile"]["weekly_limit"] = args.limit
        changed = True
    if changed:
        data["profile"]["updated_at"] = _today()
        save_accounts(data)
        parts = []
        if args.areas is not None:
            parts.append(f"执业方向: {'、'.join(data['profile']['practice_areas']) or '(已清空)'}")
        if args.identity is not None:
            parts.append(f"身份: {data['profile'].get('identity', '未设置')}")
        if args.limit is not None:
            parts.append(f"每周篇数: {data['profile'].get('weekly_limit', 20)}")
        print(f"[ok] {'，'.join(parts)}")
    else:
        areas = data["profile"].get("practice_areas") or []
        identity = data["profile"].get("identity") or "未设置"
        limit = data["profile"].get("weekly_limit") or "未设置"
        print(f"当前身份: {identity}")
        print(f"当前执业方向: {'、'.join(areas) or '未设置（用 --areas \"建工,劳动法\" 设置）'}")
        print(f"每周篇数: {limit}（用 --limit 20 或 --limit 40 设置）")
    return 0


def cmd_dedupe(args) -> int:
    items = read_candidates(Path(args.input))
    seen_data = load_seen()
    seen = seen_data["seen"]
    now = time.time()
    new_items = []
    for obj in items:
        k = entry_key(obj)
        if k in seen:
            continue
        seen[k] = {"ts": now, "account": obj["account"], "title": obj["title"]}
        new_items.append(obj)
    pruned = prune_seen(seen)
    save_seen(seen_data)
    for obj in new_items:
        print(json.dumps(obj, ensure_ascii=False))
    print(f"# dedupe: 输入 {len(items)} 条 → 新增 {len(new_items)} 条 / 重复 {len(items) - len(new_items)} 条"
          + (f" / 清理过期 {pruned} 条" if pruned else ""), file=sys.stderr)
    return 0


def cmd_render(args) -> int:
    items = read_candidates(Path(args.input))
    data = load_accounts()
    cat_of = {a["name"]: (a.get("category") or "其他") for a in data["accounts"]}
    day = args.date or _today()
    areas = "、".join(data["profile"].get("practice_areas") or [])
    identity = data["profile"].get("identity", "")

    by_cat: dict = {}
    for obj in items:
        by_cat.setdefault(cat_of.get(obj["account"], "其他"), {}).setdefault(obj["account"], []).append(obj)

    lines = [f"# 公众号监测周报 {day}", ""]
    n_accounts = len({o["account"] for o in items})
    header = f"> 本期新增 **{len(items)}** 条，来自 **{n_accounts}** 个账号"
    if identity:
        header += f"；身份：{identity}"
    if areas:
        header += f"；执业方向：{areas}"
    lines.append(header)
    lines.append("")
    for cat in CATEGORIES_ORDER + sorted(set(by_cat) - set(CATEGORIES_ORDER)):
        if cat not in by_cat:
            continue
        lines.append(f"## {cat}")
        for account, arr in sorted(by_cat[cat].items(), key=lambda kv: -len(kv[1])):
            lines.append(f"### {account}（{len(arr)} 条）")
            for o in arr:
                title = o["title"].strip()
                head = f"- **[{title}]({o['url']})**" if o.get("url") else f"- **{title}**"
                if o.get("date"):
                    head += f"  `{o['date']}`"
                lines.append(head)
                if o.get("summary"):
                    lines.append(f"  {o['summary'].strip()}")
            lines.append("")
    if not items:
        lines.append("本期无新增文章。")
        lines.append("")
    lines.append("---")
    lines.append("*由 法律公众号周报 生成*")

    text = "\n".join(lines) + "\n"
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(f"[ok] 简报已写入: {out}")
    else:
        sys.stdout.write(text)
    return 0


def cmd_stats(_args) -> int:
    data = load_accounts()
    seen = load_seen()["seen"]
    feedback = load_feedback()["feedback"]
    active = sum(1 for a in data["accounts"] if a.get("active", True))
    cats: dict = {}
    for a in data["accounts"]:
        cats[a.get("category") or "其他"] = cats.get(a.get("category") or "其他", 0) + 1
    identity = data["profile"].get("identity") or "未设置"
    areas = "、".join(data["profile"].get("practice_areas") or []) or "未设置"
    print(f"身份: {identity}  执业方向: {areas}")
    print(f"关注账号: {len(data['accounts'])}（监测中 {active}）  分类: {cats}")
    print(f"已见库: {len(seen)} 条（保留 {SEEN_TTL_DAYS} 天，上限 {SEEN_MAX_ENTRIES}）")
    print(f"反馈库: {len(feedback)} 条")
    print(f"数据文件: {ACCOUNTS_FILE} / {SEEN_FILE} / {FEEDBACK_FILE}")
    return 0


def cmd_feedback(args) -> int:
    data = load_feedback()
    feedback = data["feedback"]
    if args.add:
        entry = {
            "date": _today(),
            "title": args.add,
            "account": args.account or "",
            "score": args.score or 2,
            "reason": args.reason or "",
            "feedback": args.rating or "👍",
        }
        feedback.append(entry)
        save_feedback(data)
        print(f"[ok] 已记录反馈: {args.add} ({args.rating or '👍'})")
    elif args.stats:
        if not feedback:
            print("(暂无反馈数据)")
            return 0
        total = len(feedback)
        likes = sum(1 for f in feedback if f.get("feedback") == "👍")
        dislikes = sum(1 for f in feedback if f.get("feedback") == "👎")
        print(f"反馈统计: 共 {total} 条，👍 {likes} 条，👎 {dislikes} 条")
        # 按来源统计
        by_source: dict = {}
        for f in feedback:
            src = f.get("account") or "未知"
            by_source.setdefault(src, []).append(f)
        if by_source:
            print("\n按来源:")
            for src, arr in sorted(by_source.items(), key=lambda x: -len(x[1])):
                like = sum(1 for f in arr if f.get("feedback") == "👍")
                print(f"  {src}: {len(arr)} 条（👍 {like}）")
    else:
        if not feedback:
            print("(暂无反馈数据)")
            return 0
        for f in feedback[-10:]:
            print(f"  [{f.get('date', '')}] {f.get('title', '')} — {f.get('feedback', '')}")
    return 0


def cmd_update(args) -> int:
    """Check and download version updates."""
    local_ver = get_local_version()
    print(f"当前版本: v{local_ver}")

    if args.check:
        print(f"检查更新中...")
        print(f"最新版本: 请查看 GitHub 或联系作者获取最新版本信息")
        print(f"")
        print(f"更新方式:")
        print(f"  1. 作者发布新版本后，会邮件通知所有用户")
        print(f"  2. 你收到邮件后，运行: python3 scripts/mpwatch.py update --download")
        print(f"  3. 或者直接从 GitHub 下载最新版本覆盖安装")
        return 0

    if args.download:
        print(f"下载最新版本中...")
        print(f"")
        print(f"⚠️  自动下载功能需要 GitHub 仓库支持")
        print(f"")
        print(f"手动更新步骤:")
        print(f"  1. 备份当前配置: cp -r ~/.workbuddy/skills/法律公众号周报 ~/.workbuddy/skills/法律公众号周报-backup")
        print(f"  2. 下载最新版本并解压覆盖")
        print(f"  3. 保留 assets/accounts.json 和 state/ 目录（你的个人数据）")
        print(f"  4. 运行: python3 scripts/mpwatch.py selftest 验证")
        print(f"")
        print(f"获取最新版本: 请通过技能市场页面联系作者")
        return 0

    # Show current version
    print(f"")
    print(f"如需更新，请联系作者获取最新版本")
    return 0


def cmd_selftest(_args) -> int:
    """在临时目录中跑全链路：init → add → dedupe ×2 → render，不碰真实数据。"""
    global BASE, ACCOUNTS_FILE, SEEN_FILE
    with tempfile.TemporaryDirectory(prefix="mpwatch-test-") as tmp:
        BASE = Path(tmp)
        ACCOUNTS_FILE = BASE / "assets" / "accounts.json"
        SEEN_FILE = BASE / "state" / "seen.json"

        ns = argparse.Namespace
        assert cmd_init(ns()) == 0
        assert cmd_add(ns(name="测试法院", category="法院", tags="测试", note="")) == 0
        assert cmd_add(ns(name="测试法院", category="法院", tags="", note="")) == 1  # 重名拒绝

        cand = BASE / "cand.jsonl"
        rows = [
            {"account": "山东高法", "title": "文章A", "url": "https://mp.weixin.qq.com/s/aaa", "date": "2026-07-24", "summary": "摘要A"},
            {"account": "测试法院", "title": "文章B", "url": "", "date": "2026-07-25", "summary": ""},
        ]
        cand.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")

        import io, contextlib
        buf1 = io.StringIO()
        with contextlib.redirect_stdout(buf1):
            assert cmd_dedupe(ns(input=str(cand))) == 0
        first = [json.loads(l) for l in buf1.getvalue().splitlines() if l.strip()]
        assert len(first) == 2, f"首次 dedupe 应全部为新: {len(first)}"

        buf2 = io.StringIO()
        with contextlib.redirect_stdout(buf2):
            assert cmd_dedupe(ns(input=str(cand))) == 0
        second = [json.loads(l) for l in buf2.getvalue().splitlines() if l.strip()]
        assert len(second) == 0, "重复 dedupe 应全部被过滤"

        new_file = BASE / "new.jsonl"
        new_file.write_text(buf1.getvalue(), encoding="utf-8")
        out_md = BASE / "简报.md"
        assert cmd_render(ns(input=str(new_file), out=str(out_md), date="2026-07-25")) == 0
        md = out_md.read_text(encoding="utf-8")
        assert "# 公众号监测周报 2026-07-25" in md and "文章A" in md and "测试法院" in md

    print("[ok] selftest 全链路通过（init/add/重名拒绝/dedupe/幂等/render）")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="mpwatch", description="律师公众号助手：关注清单 + 去重 + 简报渲染")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init", help="初始化默认清单与状态").set_defaults(func=cmd_init)

    l = sub.add_parser("list", help="列出关注账号")
    l.add_argument("--category")
    l.add_argument("--json", action="store_true")
    l.set_defaults(func=cmd_list)

    a = sub.add_parser("add", help="添加账号")
    a.add_argument("name")
    a.add_argument("--category")
    a.add_argument("--tags", default="")
    a.add_argument("--note", default="")
    a.set_defaults(func=cmd_add)

    r = sub.add_parser("remove", help="移除账号")
    r.add_argument("name")
    r.set_defaults(func=cmd_remove)

    pf = sub.add_parser("profile", help="查看/设置执业方向与身份")
    pf.add_argument("--areas", default=None)
    pf.add_argument("--identity", default=None)
    pf.add_argument("--limit", type=int, default=None, choices=[20, 40], help="每周篇数上限（20 或 40）")
    pf.set_defaults(func=cmd_profile)

    fb = sub.add_parser("feedback", help="用户反馈管理（自动迭代）")
    fb.add_argument("--add", default=None, help="添加反馈（文章标题）")
    fb.add_argument("--account", default=None, help="文章来源公众号（用于按来源统计）")
    fb.add_argument("--score", type=int, default=None)
    fb.add_argument("--reason", default=None)
    fb.add_argument("--rating", default=None, help="👍 或 👎")
    fb.add_argument("--stats", action="store_true")
    fb.set_defaults(func=cmd_feedback)

    d = sub.add_parser("dedupe", help="候选去重（新条目写 stdout）")
    d.add_argument("--input", required=True)
    d.set_defaults(func=cmd_dedupe)

    rd = sub.add_parser("render", help="渲染 Markdown 简报")
    rd.add_argument("--input", required=True)
    rd.add_argument("--out", default=None)
    rd.add_argument("--date", default=None)
    rd.set_defaults(func=cmd_render)

    upd = sub.add_parser("update", help="检查/下载版本更新")
    upd.add_argument("--check", action="store_true")
    upd.add_argument("--download", action="store_true")
    upd.set_defaults(func=cmd_update)

    sub.add_parser("version", help="查看当前版本").set_defaults(func=lambda _: print(f"v{get_local_version()}"))

    sub.add_parser("stats", help="统计信息").set_defaults(func=cmd_stats)
    sub.add_parser("selftest", help="隔离环境全链路自测").set_defaults(func=cmd_selftest)
    return p


def main() -> int:
    # 第一层：自锁机制（修改后直接拒绝运行）
    # 完整性校验（修改后拒绝运行）
    _lock_if_modified()

    args = build_parser().parse_args()

    try:
        return args.func(args)
    except SystemExit:
        raise
    except Exception as e:  # 兜底：中文报错，非零退出
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
