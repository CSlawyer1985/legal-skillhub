#!/usr/bin/env python3
"""
律典·法律检索 入场预检脚本（Step 0 后必须运行）
==================================================
作用：检索开始前检查环境可用性，FAIL 则不得开始检索（流程门禁 G1）。
幂等只读：不修改任何文件、不产生副作用。

检查项：
  1. 外网连通性（flk.npc.gov.cn 可达）
  2. flk 后端 API 可用（/law-search/search/list 返回正常）
  3. 国家行政法规库可达性（gov.cn/zhengce/xxgk/fzfgk，warning 级提示，不阻断主路径）
  4. 环境依赖提示（无外网时的降级路径）

用法：
  python3 scripts/preflight_check.py

退出码：
  0 = PASS（可开始检索）
  1 = FAIL（不得开始检索，按铁律三（最后防线）处置）
"""

import json
import sys
import urllib.request

FLK_LIST_URL = "https://flk.npc.gov.cn/law-search/search/list"
# 国家行政法规库（warning 级探测）：2026-08-20 实测旧路径 zhengce/xxgk/fzfgk 已 404，
# 现行入口为 zhengce/xzfgk（与中国政府网公开页面一致；官方根库另见 xzfg.moj.gov.cn）
GOV_ADMIN_URL = "https://www.gov.cn/zhengce/xzfgk/"
TIMEOUT = 15


def check_flk_api() -> dict:
    """测试 flk 后端检索 API 是否可用（发一个最小请求）。"""
    body = {
        "searchContent": "中华人民共和国行政处罚法",
        "searchRange": 1, "sxrq": [], "gbrq": [], "sxx": [],
        "searchType": 1, "page": 1, "pageSize": 10, "sortType": 1,
    }
    req = urllib.request.Request(
        FLK_LIST_URL,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        data = json.load(urllib.request.urlopen(req, timeout=TIMEOUT))
        rows = data.get("rows", [])
        return {
            "ok": data.get("code") in (200, 0) or len(rows) > 0,
            "detail": f"API 可达，返回 {len(rows)} 条",
            "rows_sample": [r.get("title", "")[:30] for r in rows[:2]],
        }
    except Exception as e:
        return {"ok": False, "detail": f"API 不可达: {e}"}


def check_gov_reachable() -> dict:
    """测试国家行政法规库可达性（P2-1：预检覆盖补强）。
    仅作 warning 级提示，不阻断检索主路径（flk 硬性门禁保持）。"""
    req = urllib.request.Request(GOV_ADMIN_URL, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            resp.read(2048)  # 只读前 2KB 验证可达即关闭
        return {"ok": True, "detail": "国家行政法规库可达（gov.cn/zhengce/xzfgk）"}
    except Exception as e:
        return {"ok": False, "detail": f"国家行政法规库不可达（仅提示，不阻断）: {e}"}


def main():
    results = []  # (name, ok, detail, blocking)

    # 检查 1：flk API 可达性（硬性）
    api = check_flk_api()
    results.append(("flk API 可达", api["ok"], api["detail"], True))

    # 检查 2：国家行政法规库可达性（可选 warning，不阻断）
    gov = check_gov_reachable()
    results.append(("国家行政法规库可达（warning）", gov["ok"], gov["detail"], False))

    # 汇总
    print("=" * 60)
    print("律典·法律检索 入场预检报告")
    print("=" * 60)
    all_pass = True
    warns = []
    for name, ok, detail, blocking in results:
        mark = "✅ PASS" if ok else ("⚠️ WARN" if not blocking else "❌ FAIL")
        if not ok and blocking:
            all_pass = False
        if not ok and not blocking:
            warns.append(name)
        print(f"  [{mark}] {name}: {detail}")

    if warns:
        print("  ⚠️ 提示：以下信源不可达不影响本技能主路径（flk），检索时请留意对应层级降级（见 SKILL.md Step 2.6）。")

    print("-" * 60)
    if all_pass:
        print("✅ 预检通过：可开始检索（官方权威库优先）。")
        sys.exit(0)
    else:
        print("❌ 预检未通过：flk 不可达时按 SKILL.md 铁律三（最后防线）处置——")
        print("   标 [未证实/待核实]、提示人工于国家法律法规数据库/人大官网复核，绝不降级第三方。")
        sys.exit(1)


if __name__ == "__main__":
    main()
