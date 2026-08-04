# -*- coding: utf-8 -*-
"""aladin-drama-portrait · portrait_report.py
把授权链自查结果渲染成：自包含 HTML 授权链看板 + Markdown 整改清单 + 授权台账。

用法：
  python portrait_report.py --report _portrait.json \
      --out-html portrait_board.html --out-md _portrait_fix.md

仅 Python 标准库，输出自包含（无外链），可离线打开。
"""
import argparse
import html
import json
import sys

GATE_COLOR = {"READY": "#1a9c4e", "REVIEW": "#d98a00", "BLOCK": "#d32029"}
SEV_COLOR = {"P0": "#d32029", "P1": "#d98a00", "P2": "#6b7280"}
RULE_CN = {
    "A1": "缺授权凭证", "A2": "授权要素缺失", "A3": "授权已过期", "A4": "即将到期",
    "A5": "平台越界", "A6": "用途越界", "A7": "撞脸公众人物", "A8": "声音克隆缺授权",
    "A9": "转授瑕疵", "A10": "平台报备缺失",
}


def esc(s):
    return html.escape(str(s), quote=True)


def render_html(rep):
    s = rep["summary"]
    gate = s["gate"]
    color = GATE_COLOR.get(gate, "#6b7280")
    rel = rep.get("release", {})
    rows = []
    for f in rep.get("findings", []):
        sc = SEV_COLOR.get(f["severity"], "#6b7280")
        rows.append(
            "<tr>"
            "<td><span class='sev' style='background:%s'>%s</span></td>"
            "<td><b>%s</b><br><span class='rule'>%s</span></td>"
            "<td>%s</td>"
            "<td>%s</td>"
            "<td class='fix'>%s</td>"
            "</tr>" % (
                sc, esc(f["severity"]), esc(RULE_CN.get(f["rule"], f["rule"])),
                esc(f["rule"]), esc(f["asset"]), esc(f["message"]), esc(f["fix"]))
        )
    if not rows:
        rows.append("<tr><td colspan='5' class='ok'>✅ 零命中：当前人物资产授权链完整，未发现风险项。</td></tr>")

    fb = rep.get("feedback", {})
    fb_items = []
    if fb.get("to_drama_cast_missing_license"):
        fb_items.append("补授权（回灌 drama-cast）：" + "、".join(esc(x) for x in fb["to_drama_cast_missing_license"]))
    if fb.get("to_drama_publish_platform_conflict"):
        fb_items.append("平台冲突（回灌 drama-publish）：" + "、".join(esc(x) for x in fb["to_drama_publish_platform_conflict"]))
    if fb.get("renew_watchlist"):
        fb_items.append("续签观察名单：" + "、".join(esc(x) for x in fb["renew_watchlist"]))
    if fb.get("need_platform_filing"):
        fb_items.append("需完成平台 AI 合成人物报备/标识")
    fb_html = "".join("<li>%s</li>" % x for x in fb_items) or "<li>无待回灌项</li>"

    return """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>阿拉丁·短剧肖像权授权链看板</title>
<style>
:root{color-scheme:light}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,'Segoe UI','Microsoft YaHei',sans-serif;background:#f4f6f9;color:#1f2937}
.wrap{max-width:1040px;margin:0 auto;padding:28px 20px 60px}
.brand{font-size:13px;letter-spacing:2px;color:#9a6a00;font-weight:700}
h1{font-size:22px;margin:6px 0 2px}
.sub{color:#6b7280;font-size:13px;margin-bottom:20px}
.gate{display:flex;align-items:center;gap:22px;background:#fff;border-radius:14px;padding:22px 26px;box-shadow:0 1px 3px rgba(0,0,0,.08);margin-bottom:18px}
.badge{font-size:30px;font-weight:800;color:#fff;border-radius:12px;padding:14px 26px;min-width:150px;text-align:center}
.score{font-size:40px;font-weight:800}
.score small{font-size:15px;color:#6b7280;font-weight:500}
.meters{display:flex;gap:10px;flex-wrap:wrap;margin-left:auto}
.meter{background:#f4f6f9;border-radius:10px;padding:10px 16px;text-align:center;min-width:70px}
.meter b{display:block;font-size:22px}
.meter span{font-size:12px;color:#6b7280}
.ctx{background:#fff;border-radius:12px;padding:14px 20px;margin-bottom:18px;font-size:13px;color:#374151;box-shadow:0 1px 3px rgba(0,0,0,.06)}
.ctx b{color:#111}
table{width:100%%;border-collapse:collapse;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.08)}
th,td{padding:12px 14px;text-align:left;font-size:13px;border-bottom:1px solid #eef1f5;vertical-align:top}
th{background:#fafbfc;color:#6b7280;font-weight:600}
.sev{color:#fff;font-weight:700;border-radius:6px;padding:2px 9px;font-size:12px}
.rule{color:#9ca3af;font-size:11px}
.fix{color:#1a6c9c}
.ok{text-align:center;color:#1a9c4e;padding:26px;font-size:15px}
.fbbox{background:#fff;border-radius:12px;padding:16px 22px;margin-top:18px;box-shadow:0 1px 3px rgba(0,0,0,.06)}
.fbbox h3{margin:0 0 8px;font-size:15px}
.fbbox li{font-size:13px;color:#374151;margin:4px 0}
.foot{margin-top:26px;color:#9ca3af;font-size:12px;text-align:center}
</style></head><body><div class="wrap">
<div class="brand">ALADIN · 阿拉丁出品</div>
<h1>AI 短剧数字人肖像权授权链看板</h1>
<div class="sub">项目：%s ｜ 发行基准日：%s ｜ 发行平台：%s</div>
<div class="gate">
  <div class="badge" style="background:%s">%s</div>
  <div><div class="score">%d<small> / 100 · %s 档</small></div></div>
  <div class="meters">
    <div class="meter"><b style="color:%s">%d</b><span>P0 硬伤</span></div>
    <div class="meter"><b style="color:%s">%d</b><span>P1 风险</span></div>
    <div class="meter"><b style="color:%s">%d</b><span>P2 提示</span></div>
    <div class="meter"><b>%d</b><span>人物资产</span></div>
    <div class="meter"><b>%d</b><span>授权登记</span></div>
  </div>
</div>
<div class="ctx"><b>门禁说明：</b>READY 可提审 ｜ REVIEW 建议整改后上架 ｜ BLOCK 存在授权硬伤禁止上架。评分为上架前授权链参考，最终以平台审核与法律意见为准。</div>
<table><thead><tr><th>级别</th><th>检查项</th><th>人物资产</th><th>问题说明</th><th>整改建议</th></tr></thead>
<tbody>%s</tbody></table>
<div class="fbbox"><h3>闭环回灌（feedback）</h3><ul>%s</ul></div>
<div class="foot">阿拉丁 · AI 短剧创作闭环 · 数字人肖像权合规工坊 · 纯本地生成，授权信息不出本机</div>
</div></body></html>""" % (
        esc(rep.get("project") or "未命名"),
        esc(rel.get("release_date", "")),
        esc("、".join(rel.get("platforms", [])) or "(未指定)"),
        color, esc(gate), s["score"], esc(s["grade"]),
        SEV_COLOR["P0"], s["P0"], SEV_COLOR["P1"], s["P1"], SEV_COLOR["P2"], s["P2"],
        rep.get("person_count", 0), rep.get("license_count", 0),
        "".join(rows), fb_html,
    )


def render_md(rep):
    s = rep["summary"]
    rel = rep.get("release", {})
    L = []
    L.append("# 阿拉丁·AI短剧数字人肖像权授权链整改清单")
    L.append("")
    L.append("- 项目：%s" % (rep.get("project") or "未命名"))
    L.append("- 发行基准日：%s ｜ 发行平台：%s" % (rel.get("release_date", ""), "、".join(rel.get("platforms", [])) or "(未指定)"))
    L.append("- 门禁结论：**%s**（%d 分 / %s 档）" % (s["gate"], s["score"], s["grade"]))
    L.append("- 命中：P0=%d ｜ P1=%d ｜ P2=%d ｜ 合计 %d 条" % (s["P0"], s["P1"], s["P2"], s["finding_count"]))
    L.append("")
    if s["gate"] == "BLOCK":
        L.append("> ⚠️ 存在 P0 授权硬伤，**禁止上架**，请先处理下列 P0 项。")
        L.append("")
    findings = rep.get("findings", [])
    if not findings:
        L.append("✅ 零命中：当前人物资产授权链完整，未发现风险项。")
    else:
        for sev in ("P0", "P1", "P2"):
            items = [f for f in findings if f["severity"] == sev]
            if not items:
                continue
            L.append("## %s（%d 条）" % (sev, len(items)))
            L.append("")
            for f in items:
                L.append("- **[%s %s] %s**" % (f["rule"], RULE_CN.get(f["rule"], ""), f["asset"]))
                L.append("  - 问题：%s" % f["message"])
                L.append("  - 整改：%s" % f["fix"])
            L.append("")
    fb = rep.get("feedback", {})
    L.append("## 闭环回灌契约")
    L.append("")
    L.append("- 补授权（→ drama-cast）：%s" % ("、".join(fb.get("to_drama_cast_missing_license", [])) or "无"))
    L.append("- 平台冲突（→ drama-publish）：%s" % ("、".join(fb.get("to_drama_publish_platform_conflict", [])) or "无"))
    L.append("- 续签观察名单：%s" % ("、".join(fb.get("renew_watchlist", [])) or "无"))
    L.append("- 需平台 AI 合成人物报备：%s" % ("是" if fb.get("need_platform_filing") else "否"))
    L.append("")
    L.append("---")
    L.append("_阿拉丁出品 · 授权链自查为上架前参考，最终以平台审核与法律意见为准。_")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description="肖像权授权链看板与整改清单渲染")
    ap.add_argument("--report", required=True, help="portrait_audit 产出的 _portrait.json")
    ap.add_argument("--out-html", default="portrait_board.html")
    ap.add_argument("--out-md", default="_portrait_fix.md")
    args = ap.parse_args()

    with open(args.report, encoding="utf-8") as f:
        rep = json.load(f)

    with open(args.out_html, "w", encoding="utf-8") as f:
        f.write(render_html(rep))
    with open(args.out_md, "w", encoding="utf-8") as f:
        f.write(render_md(rep))

    print("[ok] 已生成看板 %s 与整改清单 %s" % (args.out_html, args.out_md))
    return 0


if __name__ == "__main__":
    sys.exit(main())
