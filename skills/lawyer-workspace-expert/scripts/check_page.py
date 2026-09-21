#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""单文件页面静态检查（6 项）
author: 小台 (DeskCraft) · local-file-workspace skill
作者：陆凌燕（北京德恒（无锡）律师事务所）

用法：python3 check_page.py <页面路径> [动态生成的id,逗号分隔]
示例：python3 check_page.py index.html "noteBody,mdwrap"

检查项：
  1 缺失 id —— JS 里 $("x") 但 HTML 里没有
  2 隐式全局赋值 —— 漏 var，严格模式下抛 ReferenceError 并中断 refreshAll
  3 函数调用环 —— DFS 找环，防渲染函数互调导致栈溢出
  4 CSS 重复定义 —— "改了没反应"的头号原因
  5 外部依赖 —— 铁律：零外链
  6 emoji 当图标 —— 铁律：只用手写 SVG
"""
import re
import sys
from collections import Counter

path = sys.argv[1]
dynamic_ids = set((sys.argv[2] if len(sys.argv) > 2 else "").split(",")) - {""}

p = open(path, encoding="utf-8").read()
m = re.search(r"<script>\n(.*?)\n</script>", p, re.S)
if not m:
    print("找不到 <script> 块")
    sys.exit(1)
js = m.group(1)
open("/tmp/_page_check.js", "w", encoding="utf-8").write(js)

fails = []

# ---- 1. 缺失 id ----
ids = set(re.findall(r'id="([^"]+)"', p)) | dynamic_ids
used = set(re.findall(r'\$\("([^"]+)"\)', js))
missing = sorted(used - ids)
print("[1] 缺失 id：", missing or "无")
if missing:
    fails.append("缺失 id " + str(missing))

# ---- 2. 隐式全局赋值（先收集所有已声明名字，含函数参数，避免误报重赋值） ----
declared = set()
for chunk in re.findall(r"\b(?:var|let|const)\s+([^;\n]+)", js):   # 含逗号多声明
    for part in chunk.split(","):
        nm = part.strip().split("=")[0].strip()
        if re.match(r"^[A-Za-z_$][\w$]*$", nm):
            declared.add(nm)
for params in re.findall(r"function\s*\w*\s*\(([^)]*)\)", js):
    for a in params.split(","):
        a = a.strip().split("=")[0].strip()
        if re.match(r"^[A-Za-z_$][\w$]*$", a):
            declared.add(a)
for params in re.findall(r"\(([^)]*)\)\s*=>", js):        # 箭头函数参数
    for a in params.split(","):
        a = a.strip().split("=")[0].strip()
        if re.match(r"^[A-Za-z_$][\w$]*$", a):
            declared.add(a)

implicit = []
for n, line in enumerate(js.split("\n"), 1):
    s2 = line.strip()
    mm = re.match(r"^([A-Za-z_$][\w$]*)\s*=(?!=)", s2)
    if mm and mm.group(1) not in declared and \
       not re.match(r"^(var|let|const|return|if|while|for|function|else|case)\b", s2):
        implicit.append((n, s2[:60]))
print("[2] 隐式全局赋值：", implicit or "无（%d 个已声明名字）" % len(declared))
if implicit:
    fails.append("隐式全局 " + str(implicit))

# ---- 3. 函数调用环（花括号计数提取函数体，DFS 找环） ----
names = re.findall(r"^function (\w+)\(", js, re.M)


def body_of(fn):
    i = js.find("function " + fn + "(")
    if i < 0:
        return ""
    j = js.find("{", i)
    if j < 0:
        return ""
    depth, k = 0, j
    while k < len(js):
        if js[k] == "{":
            depth += 1
        elif js[k] == "}":
            depth -= 1
            if depth == 0:
                return js[j:k]
        k += 1
    return ""


bodies = {n: body_of(n) for n in names}
calls = {n: {c for c in names if c != n and re.search(r"\b" + re.escape(c) + r"\s*\(", bodies[n])}
         for n in names}
WHITE, GRAY, BLACK = 0, 1, 2
color = {n: WHITE for n in names}
cycles = []


def dfs(n, stack):
    color[n] = GRAY
    stack.append(n)
    for nxt in calls.get(n, ()):
        if color.get(nxt, WHITE) == GRAY:
            cycles.append(stack[stack.index(nxt):] + [nxt])
        elif color.get(nxt, WHITE) == WHITE:
            dfs(nxt, stack)
    stack.pop()
    color[n] = BLACK


for n in names:
    if color[n] == WHITE:
        dfs(n, [])
uniq = sorted({tuple(c) for c in cycles})
print("[3] 函数调用环：", [" -> ".join(c) for c in uniq] or "无（DAG 成立）")
if uniq:
    fails.append("调用环 " + str(uniq))

# ---- 4. CSS 重复定义 ----
css = re.search(r"<style>\n(.*?)\n</style>", p, re.S)
if css:
    cnt = Counter(re.findall(r"^(\.[\w.\-]+)\{", css.group(1), re.M))
    dup = {k: v for k, v in cnt.items() if v > 1}
    print("[4] CSS 重复定义：", dup or "无")
    if dup:
        fails.append("CSS 重复 " + str(dup))

# ---- 5. 零外链 ----
ext = re.findall(r'(?:src|href)="(https?://[^"]+)"', p)
print("[5] 外部依赖：", ext or "无")
if ext:
    fails.append("外部依赖 " + str(ext))

# ---- 6. emoji 当图标 ----
emoji = re.findall(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]", p)
print("[6] emoji 出现次数：", len(emoji), sorted(set(emoji))[:8] or "")
if emoji:
    fails.append("emoji " + str(sorted(set(emoji))[:8]))

print()
print("结果：" + ("全部通过" if not fails else "  |  ".join(fails)))
sys.exit(1 if fails else 0)
