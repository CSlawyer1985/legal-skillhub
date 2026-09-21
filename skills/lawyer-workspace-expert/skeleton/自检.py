#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""工作台自检骨架 —— 改完代码跑一遍，确认没把已有功能改坏。

用法：
    # 1) 另起一个端口启动服务（不要动你正在用的那个）
    python3 server.py --port 9101 --no-browser &
    # 2) 指向它跑自检
    DESK=http://127.0.0.1:9101 python3 自检.py
    # 3) 停掉那个测试服务

注意：自检会写入 data/动态.csv。跑之前先备份：
    cp -a data /tmp/data_bk
    DESK=http://127.0.0.1:9101 python3 自检.py
    rm -rf data && mv /tmp/data_bk data

⚠️ 不要在脏数据上连跑两遍 —— 第二遍的结果是无效的。

author: 请在这里写上你的名字
"""

import csv
import json
import os
import re
import sys
import urllib.parse
import urllib.request

DESK = os.environ.get("DESK", "http://127.0.0.1:8765")
FAIL = []


def chk(name, cond, extra=""):
    print(("  PASS  " if cond else "  FAIL  ") + name + ("" if cond else "   [%s]" % (extra,)))
    if not cond:
        FAIL.append(name)


def get(path):
    return json.loads(urllib.request.urlopen(DESK + path, timeout=15).read())


def post(path, body):
    req = urllib.request.Request(DESK + path, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=15).read())


print("=" * 52)
print("  工作台自检 · %s" % DESK)
print("=" * 52)

print()
print("== 1. 服务与数据结构 ==")
st = get("/api/state")
chk("服务返回 ok", st.get("ok") is True)
chk("today 是 YYYY-MM-DD", bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", st.get("today", ""))), st.get("today"))
chk("month 是 YYYY-MM", bool(re.fullmatch(r"\d{4}-\d{2}", st.get("month", ""))), st.get("month"))
chk("weeks 是若干行、每行 7 列",
    len(st.get("weeks", [])) in (4, 5, 6) and all(len(w) == 7 for w in st.get("weeks", [])),
    [len(w) for w in st.get("weeks", [])])
flat = [d for w in st["weeks"] for d in w]
chk("每个格子都有 date / day / items",
    all(("date" in d and "day" in d and "items" in d) for d in flat))
chk("本月至少有一格标了今天", any(d["isToday"] for d in flat))

# 首次打开不能是空白页 —— 没配 Excel 时必须有内置示例排期
cal_n = sum(len(d["items"]) for w in st["weeks"] for d in w)
if "未配置" in st["source"]["xlsx"]:
    chk("未配置 Excel 时，日历要有内置示例排期（首屏不能是空的）", cal_n > 0,
        "0 条 —— 检查 demo_calendar 有没有生效")

print()
print("== 2. 左栏候选来自写入层 ==")
add = post("/api/dynamic", {"op": "add", "item": {
    "date": st["today"], "project": "自检示例项目", "type": "提醒", "text": "自检用条目"}})
chk("新增返回 ok", add.get("ok") is True)
st2 = get("/api/state")
names = [p["name"] for p in st2["projects"]]
chk("新条目出现在候选里", "自检示例项目" in names, names[:5])
mine = [p for p in st2["projects"] if p["name"] == "自检示例项目"][0]
chk("该候选的未办数 = 1", mine.get("open") == 1, mine)

print()
print("== 3. 状态流转 ==")
rid = [r for r in st2["dynamic"] if r["text"] == "自检用条目"][0]["id"]
chk("新条目默认是待办",
    [r for r in st2["dynamic"] if r["id"] == rid][0]["status"] == "待办")
chk("它进了「今天到期」列表", any(r["id"] == rid for r in st2["dueToday"]))
post("/api/dynamic", {"op": "finish", "item": {"id": rid}})
st3 = get("/api/state")
chk("办结后状态变已办",
    [r for r in st3["dynamic"] if r["id"] == rid][0]["status"] == "已办")
chk("办结后不在到期列表", not any(r["id"] == rid for r in st3["dueToday"]))

print()
print("== 4. 筛选 ==")
st4 = get("/api/state?project=" + urllib.parse.quote("自检示例项目"))
chk("筛选后动态只剩该归属的",
    all(r["project"] == "自检示例项目" for r in st4["dynamic"]), len(st4["dynamic"]))
chk("筛选后日历条目带 hit 标记",
    all("hit" in it for w in st4["weeks"] for d in w for it in d["items"]))
chk("无筛选时 hit 全为真",
    all(it["hit"] for w in get("/api/state")["weeks"] for d in w for it in d["items"]))

print()
print("== 5. 删除与清空 ==")
post("/api/dynamic", {"op": "delete", "item": {"id": rid}})
chk("删除后条目消失", not any(r["id"] == rid for r in get("/api/state")["dynamic"]))
post("/api/dynamic", {"op": "clear_demo", "item": {}})
chk("清空示例后没有示例条目", get("/api/state")["totals"]["demo"] == 0)

print()
print("== 6. 写入层文件本身 ==")
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "动态.csv")
if os.path.exists(p):
    rows = list(csv.reader(open(p, encoding="utf-8-sig")))
    chk("表头是预期的 6 列", rows[0] == ["id", "日期", "归属", "类型", "内容", "状态"], rows[0])
    chk("每行列数一致", len(set(len(r) for r in rows if r)) == 1,
        sorted(set(len(r) for r in rows if r)))
    chk("没有残留的 .tmp", not os.path.exists(p + ".tmp"))
else:
    chk("写入层文件存在", False, p)

print()
print("=" * 52)
print("  结果：" + ("全部通过" if not FAIL else "%d 项失败 -> %s" % (len(FAIL), FAIL)))
print("=" * 52)
sys.exit(1 if FAIL else 0)
