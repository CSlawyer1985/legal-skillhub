#!/usr/bin/env python3
# DEPRECATED: 2026-07-29 微信关闭跨号接口，此脚本不再可用
"""从 MP 后台拉取三账号近一周文章，合并写入 mp_articles.json。
依赖：wechat-ocr-research skill 的 wechat_mp_reader（session 已在 cache/session.json）。
"""
import json, sys, os
from datetime import datetime, timezone, timedelta
from pathlib import Path

# 让 import 能找到 wechat_mp_reader
WR_DIR = Path.home() / ".workbuddy/skills/wechat-ocr-research/scripts"
sys.path.insert(0, str(WR_DIR))

import importlib.util
import wechat_mp_reader.session_store as sess_mod

# wechat_mp_reader.py 与 wechat_mp_reader/ 包同名，import 优先加载包。
# 需显式以文件路径加载同名 .py 文件版本，并先注册到 sys.modules 避免 dataclass 反查失败。
_WR_FILE = WR_DIR / "wechat_mp_reader.py"
spec = importlib.util.spec_from_file_location("mp_reader_file", str(_WR_FILE))
mp = importlib.util.module_from_spec(spec)
import sys
sys.modules["mp_reader_file"] = mp
spec.loader.exec_module(mp)

resolve_session = sess_mod.resolve_session

BASE = Path(__file__).resolve().parent
OUT = BASE / "mp_articles.json"

# MP 账号 fakeid（来自 config/sources.yaml）
ACCOUNTS = [
    ("山东高法", "MzA5MDAxMjk5Ng=="),
    ("上海一中院", "MjM5MjkwMDkxMA=="),
    ("上海二中院", "MzA4MzY3NjMxNw=="),
    ("中国应用法学", "MzU5NDcxMjc4Ng=="),
]

PER_ACCOUNT = 30

# 近一周窗口（北京时间 UTC+8，动态计算）
_tz = timezone(timedelta(hours=8))
_now = datetime.now(tz=_tz)
WINDOW_START = _now - timedelta(days=7)
WINDOW_END = _now


def ts_to_dt(ts):
    # MP update_time 为秒级时间戳（东八区）
    return datetime.fromtimestamp(int(ts), tz=timezone(timedelta(hours=8)))


def fetch_account(name, fakeid, session_cfg):
    items = []
    try:
        data = mp.list_articles_via_mp_backend(fakeid, session_cfg, count=PER_ACCOUNT, begin=0)
        raw = mp.extract_article_list(data)
        for a in raw:
            ts = a.get("publish_time_raw") or a.get("update_time") or ""
            if not ts:
                continue
            try:
                dt = ts_to_dt(ts)
            except Exception:
                continue
            if WINDOW_START <= dt <= WINDOW_END:
                items.append({
                    "_source": name,
                    "title": a.get("title", ""),
                    "url": a.get("url", ""),
                    "update_time": int(ts),
                    "digest": a.get("summary", ""),
                    "publish_time": dt.strftime("%Y-%m-%d %H:%M"),
                })
    except Exception as e:
        print(f"  [WARN] {name} 拉取失败: {e}")
    return items


def main():
    session_cfg = resolve_session()
    status = mp.build_session_status(session_cfg) if hasattr(mp, "build_session_status") else {"valid": True}
    print(f"session valid: {status.get('valid')}")
    if not status.get("valid"):
        print("session 无效，退出。请先 refresh_session_from_edge.py")
        sys.exit(1)

    all_items = []
    seen = set()
    for name, fakeid in ACCOUNTS:
        print(f"拉取 {name} ...")
        items = fetch_account(name, fakeid, session_cfg)
        print(f"  -> 近一周命中 {len(items)} 篇")
        for it in items:
            if it["url"] and it["url"] not in seen:
                seen.add(it["url"])
                all_items.append(it)

    all_items.sort(key=lambda x: x["update_time"], reverse=True)
    OUT.write_text(json.dumps(all_items, ensure_ascii=False, indent=2))
    print(f"\n总计 {len(all_items)} 篇（去重后）已写入 {OUT}")


if __name__ == "__main__":
    main()
