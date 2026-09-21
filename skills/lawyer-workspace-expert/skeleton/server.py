#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""律师工作台 · 最小可运行骨架
=================================

它做三件事：
  1. **只读**你的日程表（Excel），解析成"哪天有什么"
  2. 提供一个三栏页面（左栏选案件 / 中栏月历 / 右栏看当天）
  3. 把你新记的事，**只写进 data/动态.csv 一个文件**

三条不可改的原则：
  · 只读正本 —— 任何情况下都不写你的 Excel、不动你的案件文件夹
  · 单一写入 —— 所有动态只落 data/动态.csv，方便你随时用 Excel 打开改
  · 只绑本机 —— 服务只监听 127.0.0.1，同一个 WiFi 下的别人也访问不到

改造给你的数据：只需要改下面【配置区】两处，再按注释调整解析函数。

author: 请在这里写上你的名字
"""

import argparse
import csv
import datetime as dt
import io
import json
import re
import threading
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# ==========================================================================
# 【配置区】通常只需要改这里
# ==========================================================================

# 你的日程表路径（**字符串**）。留空 = 用内置示例数据（先跑起来看效果）
# macOS 上找路径的小技巧：右键文件 → 按住 Option → 拷贝「…」为路径名称
# ⚠️ 这里必须是字符串，不要写成 Path("") —— Path("") 等于当前目录，不是"空"
XLSX = ""

# 月历栅格在哪个工作表？留空 = 自动找「1 月」「2 月」这种名字的表
MONTH_SHEET_RE = r"^(\d{1,2})\s*月\s*$"

# 备忘/待办表的名字（没有就留空）
MEMO_SHEET = ""

# ==========================================================================

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DYN_CSV = DATA_DIR / "动态.csv"
ENC = "utf-8-sig"          # 带 BOM：你双击就能用 Excel / WPS 直接改，不会乱码

DYN_HEADER = ["id", "日期", "归属", "类型", "内容", "状态"]
DYN_TYPE = ("进展", "提醒")   # 进展 = 记已做的（留痕）；提醒 = 记要做的（会标红）

_lock = threading.Lock()


# ==========================================================================
# 一、只读源：把你的日程表解析成「日期 + 事项」的列表
# ==========================================================================

def parse_calendar():
    """返回 [{"date": "2026-09-14", "text": "上午九点开庭", "sheet": "9 月"}, ...]

    如果你的日程表不是"月历栅格"结构，改这个函数即可，其余代码都不用动。
    栅格结构长这样（律师的 Excel 日程表最常见的写法）：
        第 3 行：B~H 七列 = 周一~周日（日期）
        第 4 行：B~H 七列 = 那 7 天填的内容
        第 5、6 行：下一周……
    """
    if not XLSX or not Path(XLSX).exists():
        return demo_calendar(), "内置示例数据（未配置日程表）"

    try:
        import openpyxl
    except ImportError:
        return demo_calendar(), "没装 openpyxl，暂用示例数据（pip install openpyxl）"

    try:
        wb = openpyxl.load_workbook(str(XLSX), data_only=True)
    except Exception as ex:                     # 文件被占用 / 正在同步
        return [], "读不到日程表：%s" % ex

    out = []
    for name in wb.sheetnames:
        m = re.match(MONTH_SHEET_RE, name.strip())
        if not m:
            continue
        month = int(m.group(1))
        ws = wb[name]
        year = dt.date.today().year
        for r in range(1, ws.max_row + 1):
            # 判据：一行里出现 >= 4 个日期 → 认作"日期行"，它的下一行是内容行。
            # 这样你在表里插行删行，都不会解析错位（比按固定行号稳）。
            days = []
            for c in range(2, 9):               # B~H 七列
                v = ws.cell(r, c).value
                if isinstance(v, (dt.datetime, dt.date)):
                    days.append((c, v.day))
                elif isinstance(v, str) and re.fullmatch(r"\d{1,2}\s*[日号]?", v.strip()):
                    days.append((c, int(re.sub(r"\D", "", v))))
            if len(days) < 4:
                continue
            for c, day in days:
                txt = ws.cell(r + 1, c).value
                txt = re.sub(r"\s+", " ", str(txt)).strip() if txt is not None else ""
                if not txt:
                    continue
                try:
                    d = dt.date(year, month, day)
                except ValueError:
                    continue
                out.append({"date": d.isoformat(), "text": txt, "sheet": name})
    out.sort(key=lambda x: x["date"])
    return out, ""


def demo_calendar():
    """没配置日程表时用的示例排期 —— **全部虚构**，只为让你先看到效果。"""
    t = dt.date.today()
    mk = lambda n: (t + dt.timedelta(days=n)).isoformat()
    return [
        {"date": mk(0),  "text": "09:00 示例案件A 开庭（示例数据）", "sheet": "示例"},
        {"date": mk(0),  "text": "14:00 与当事人沟通（示例数据）",   "sheet": "示例"},
        {"date": mk(1),  "text": "上午十点 示例案件B 调解（示例数据）", "sheet": "示例"},
        {"date": mk(3),  "text": "全天 出差（示例数据）",            "sheet": "示例"},
        {"date": mk(7),  "text": "15:00 所内例会（示例数据）",       "sheet": "示例"},
    ]


# ==========================================================================
# 二、写入层：唯一的可写文件
# ==========================================================================

def norm_type(t):
    t = (t or "").strip()
    return t if t in DYN_TYPE else "进展"


def _seed():
    """首次运行时的示例动态 —— **虚构数据**，页面上有「清空示例」按钮。"""
    t = dt.date.today()
    return [
        {"id": "d1", "date": t.isoformat(), "project": "示例案件A", "type": "进展",
         "text": "已提交调查申请（示例数据，可删除）", "status": "已办"},
        {"id": "d2", "date": (t - dt.timedelta(days=2)).isoformat(), "project": "示例案件B",
         "type": "提醒", "text": "跟进排期通知（示例数据，可删除）", "status": "待办"},
    ]


def _next_id(rows):
    """取现有最大编号 +1。

    ⚠️ 不要按行号重新编号！否则删掉一条之后，剩下的条目 id 会整体前移，
    前端还攥着旧 id，就会删错/改错条目。
    """
    n = 0
    for r in rows:
        m = re.fullmatch(r"d(\d+)", r.get("id") or "")
        if m:
            n = max(n, int(m.group(1)))
    return "d%d" % (n + 1)


def _write_rows(rows):
    """整本写回。rows 是 dict 列表，每项必须带**稳定的 id**。"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(DYN_HEADER)
    for r in rows:
        w.writerow([r.get("id", ""), r.get("date", ""), r.get("project", ""),
                    norm_type(r.get("type")), r.get("text", ""),
                    (r.get("status") or "待办")])
    tmp = DYN_CSV.with_suffix(".csv.tmp")
    tmp.write_text(buf.getvalue(), encoding=ENC)
    tmp.replace(DYN_CSV)               # 先写临时文件再替换，避免写一半崩掉


def read_dyn():
    if not DYN_CSV.exists():
        _write_rows(_seed())
    with open(DYN_CSV, encoding=ENC, newline="") as f:
        out = []
        for r in csv.DictReader(f):
            if not (r.get("内容") or "").strip():
                continue
            out.append({
                "id": (r.get("id") or "").strip(),
                "date": (r.get("日期") or "").strip(),
                "project": (r.get("归属") or "").strip(),
                "type": norm_type(r.get("类型")),
                "text": (r.get("内容") or "").strip(),
                "status": (r.get("状态") or "待办").strip() or "待办",
            })
    return out


def mutate(op, item):
    with _lock:
        rows = read_dyn()
        if op == "add":
            t = norm_type(item.get("type"))
            rows.insert(0, {
                "id": _next_id(rows),
                "date": (item.get("date") or "").strip(),
                "project": (item.get("project") or "").strip(),
                "type": t,
                "text": (item.get("text") or "").strip(),
                "status": "待办" if t == "提醒" else "已办",
            })
        elif op == "update":
            for r in rows:
                if r["id"] == item.get("id"):
                    for k in ("date", "project", "type", "text", "status"):
                        if item.get(k) is not None:
                            r[k] = item[k]
                    r["type"] = norm_type(r["type"])
        elif op == "delete":
            rows = [r for r in rows if r["id"] != item.get("id")]
        elif op == "finish":
            for r in rows:
                if r["id"] == item.get("id"):
                    r["status"] = "已办"
        elif op == "clear_demo":
            rows = [r for r in rows if "示例数据" not in r["text"]]
        _write_rows(rows)
        return read_dyn()


# ==========================================================================
# 三、汇总：页面要的全部数据，一次给全
# ==========================================================================

def build_month(cal, ym, today_iso):
    """把排期铺成"周一开头"的月历栅格。"""
    y, m = int(ym[:4]), int(ym[5:7])
    first = dt.date(y, m, 1)
    days_in = (dt.date(y + (m == 12), (m % 12) + 1, 1) - first).days
    start = first - dt.timedelta(days=first.weekday())     # 回退到周一
    weeks, cur = [], []
    for i in range(42):                                     # 6 周 × 7 天
        d = start + dt.timedelta(days=i)
        iso = d.isoformat()
        items = [c for c in cal if c["date"] == iso]
        cur.append({
            "date": iso, "day": d.day, "inMonth": d.month == m,
            "isToday": iso == today_iso, "items": items,
        })
        if len(cur) == 7:
            weeks.append(cur); cur = []
    if all(not d["inMonth"] for d in weeks[-1]):            # 末行全是下个月，去掉
        weeks.pop()
    return weeks


def build_state(month=None, project=None):
    today = dt.date.today()
    today_iso = today.isoformat()
    ym = month or today_iso[:7]

    cal, cal_err = parse_calendar()
    all_dyn = read_dyn()

    def hit(t):
        return (not project) or (project.lower() in (t or "").lower())

    cal_view = [{"date": c["date"], "text": c["text"], "sheet": c["sheet"],
                 "hit": hit(c["text"])} for c in cal]

    dyn_all = [dict(r, hit=hit(r["text"] + " " + r["project"])) for r in all_dyn]
    dyn = [r for r in dyn_all if r["hit"]]        # 右栏只看聚焦范围内的事

    # 左栏候选**始终基于全量** —— 否则点了某个案子，就没法再切到别的案子了
    names = {}
    for r in dyn_all:
        if r["project"]:
            names.setdefault(r["project"], {"name": r["project"], "n": 0, "open": 0})
            names[r["project"]]["n"] += 1
            if r["type"] == "提醒" and r["status"] != "已办":
                names[r["project"]]["open"] += 1
    projects = sorted(names.values(), key=lambda x: (-x["open"], -x["n"], x["name"]))

    # 「今天要处理」：逾期 / 今天 / 三天内
    alerts, due_today, later = [], [], []
    for r in dyn:
        if r["type"] != "提醒" or r["status"] == "已办":
            continue
        try:
            d = dt.date.fromisoformat(r["date"])
        except ValueError:
            d = today
        if d < today:
            alerts.append(dict(r, overdue=(today - d).days))
        elif d == today:
            due_today.append(r)
        else:
            later.append(r)
    later.sort(key=lambda x: x["date"])

    sel = today_iso
    day_items = [c for c in cal_view if c["date"] == sel]

    return {
        "ok": True,
        "today": today_iso,
        "month": ym,
        "source": {"xlsx": XLSX or "（未配置，正在用内置示例数据）",
                   "mtime": dt.datetime.fromtimestamp(Path(XLSX).stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                            if XLSX and Path(XLSX).exists() else ""},
        "calendarError": cal_err,
        "weeks": build_month(cal_view, ym, today_iso),
        "projects": projects,
        "dynamic": dyn,
        "alerts": alerts,
        "dueToday": due_today,
        "later": later,
        "dayItems": day_items,
        "totals": {"dyn": len(dyn), "open": len(alerts) + len(due_today),
                   "demo": sum(1 for r in dyn if "示例数据" in r["text"])},
    }


# ==========================================================================
# 四、本地服务（只绑 127.0.0.1）
# ==========================================================================

class Handler(BaseHTTPRequestHandler):
    server_version = "LawyerDesk-Skeleton/1.0"

    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        raw = body if isinstance(body, bytes) else str(body).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj, ensure_ascii=False))

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(u.query)
        if u.path in ("/", "/index.html"):
            html = (ROOT / "index.html").read_text(encoding="utf-8")
            return self._send(200, html, "text/html; charset=utf-8")
        if u.path == "/api/state":
            return self._json(build_state(qs.get("month", [None])[0],
                                          qs.get("project", [None])[0]))
        return self._send(404, "not found", "text/plain; charset=utf-8")

    def do_POST(self):
        u = urllib.parse.urlparse(self.path)
        try:
            n = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            body = {}
        if u.path == "/api/dynamic":
            rows = mutate(body.get("op", "add"), body.get("item") or {})
            return self._json({"ok": True, "dynamic": rows})
        return self._send(404, "not found", "text/plain; charset=utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-browser", action="store_true")
    args = ap.parse_args()

    url = "http://127.0.0.1:%d/" % args.port
    srv = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)   # 只绑本机，别改成 0.0.0.0

    print("=" * 52)
    print("  律师工作台 · 本地服务已启动")
    print("  地址：%s" % url)
    print("  正本：%s" % (XLSX if XLSX else "（未配置，正在用示例数据）"))
    print("  写入层：%s" % DYN_CSV)
    print("  关闭：在本窗口按 Control + C")
    print("=" * 52)

    if not args.no_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")


if __name__ == "__main__":
    main()
