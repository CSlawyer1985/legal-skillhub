#!/usr/bin/env python3
"""legal-weekly-briefing 回归测试 + 交付门禁

用法：
    python3 scripts/verify.py

三层检查：
  1. 评分引擎回归（6 个 test-prompts 样例）
  2. HTML 交付门禁（P0: 模板风格 / 字段完整性 / 流水线集成）
  3. 新通道门禁（W1-W3: 微信读书登录态 / 通道脚本 / 旧 MP 文档废弃标记）

全部通过 → 退出码 0；任一失败 → 退出码 1。
"""
import json, sys, os
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "scripts"))

PASSED = 0
FAILED = 0

def check(ok, label, detail=""):
    global PASSED, FAILED
    mark = "✓" if ok else "✗"
    msg = f"  {mark} [{label}]"
    if detail:
        msg += f"  {detail}"
    print(msg)
    if ok:
        PASSED += 1
    else:
        FAILED += 1
    return ok


# ============================================================
# Layer 1: 评分引擎回归（保持原有逻辑）
# ============================================================
def run_scoring_tests():
    global PASSED, FAILED
    perf = PASSED
    perf = FAILED
    P, F = 0, 0

    from scoring_engine import predict
    TEST_PATH = BASE / "assets" / "data" / "test-prompts.json"
    if not TEST_PATH.exists():
        print(f"✗ 测试样例缺失: {TEST_PATH}")
        return False

    cases = json.loads(TEST_PATH.read_text())["cases"]
    print(f"\n--- 评分引擎回归 ({len(cases)} 样例) ---")
    for c in cases:
        cat = c["category"]
        feat = c["features"]
        score, conf = predict({"title": c.get("title", ""), "features": feat}, cat)
        lo, hi = c["expect_min"], c["expect_max"]
        ok = lo <= score <= hi
        detail = f"score={score:.1f} (期望 {lo}-{hi}) | {c.get('title','')[:36]}"
        if check(ok, f"评分/{c['id']}", detail):
            P += 1
        else:
            F += 1
    return F == 0


# ============================================================
# Layer 2: HTML 交付门禁（P0 — 任一失败即阻塞交付）
# ============================================================
def run_html_gate():
    print(f"\n--- HTML 交付门禁 ---")
    all_ok = True

    # G1: render_html.py 存在且可导入
    render_path = BASE / "scripts" / "render_html.py"
    exists = render_path.exists()
    all_ok &= check(exists, "G1-render_html存在", f"路径: {render_path}")

    try:
        import render_html
        has_fn = hasattr(render_html, "render_html")
        all_ok &= check(has_fn, "G1-render_html可导入", "render_html.render_html() 函数可用")
    except Exception as e:
        all_ok &= check(False, "G1-render_html可导入", f"导入失败: {e}")

    # G2: 模板风格 = 浅色简报风（禁止深色翻页幻灯片）
    if render_path.exists():
        template_src = render_path.read_text()
        is_light_bg = "#f8f7f5" in template_src
        is_dark_header = "#1a1a2e" in template_src
        has_no_dark_slide = "var cur" not in template_src  # 翻页幻灯片的典型 JS 变量

        all_ok &= check(is_light_bg, "G2-浅色背景", "模板含 #f8f7f5（浅色简报风）")
        all_ok &= check(is_dark_header, "G2-深色页眉", "模板含 #1a1a2e（深色页眉）")
        all_ok &= check(has_no_dark_slide, "G2-禁止翻页幻灯片",
                        "模板不含翻页 JS（禁止自造深色翻页版）")

        # G3: HTML 模板必须含 abstract / recommend 渲染段
        has_abstract = "abstract" in template_src and "{abstract}" in template_src
        has_recommend = "推荐理由" in template_src and "{recommend}" in template_src
        has_fav = "fav-btn" in template_src
        all_ok &= check(has_abstract, "G3-abstract字段", "模板渲染 abstract 占位符")
        all_ok &= check(has_recommend, "G3-recommend字段", "模板渲染 推荐理由 占位符")
        all_ok &= check(has_fav, "G3-收藏按钮", "模板含 fav-btn 交互")

    # G4: demo.py 产出 JSON 必须含 abstract/recommend 字段
    demo_path = BASE / "scripts" / "demo.py"
    if demo_path.exists():
        demo_src = demo_path.read_text()
        has_abstract_in_demo = '"abstract"' in demo_src and '"recommend"' in demo_src
        all_ok &= check(has_abstract_in_demo, "G4-demo含abstract/recommend",
                        "demo.py 候选数据含完整渲染字段")

    # G5: run_pipeline.py 必须含 HTML 渲染步骤（Stage 4.5 或 render_html 调用）
    pipeline_path = BASE / "scripts" / "run_pipeline.py"
    if pipeline_path.exists():
        pl_src = pipeline_path.read_text()
        has_html_stage = "render_html" in pl_src or "Stage 4.5" in pl_src or "HTML" in pl_src
        all_ok &= check(has_html_stage, "G5-流水线含HTML渲染",
                        "run_pipeline.py 必须含 render_html 调用步骤")

    # G6: taxonomy.yaml 的 knowledge_base_id 不能是作者/他人 KB（占位符=尚未配置，警告不阻断）
    tax_path = BASE / "assets" / "config" / "taxonomy.yaml"
    if tax_path.exists():
        tax_src = tax_path.read_text()
        kb_line = [l for l in tax_src.split('\n') if 'knowledge_base_id' in l]
        kb_val = ""
        if kb_line:
            import re
            # 兼容裸值（knowledge_base_id: 作者ID）与引号值（knowledge_base_id: "xxx"）两种格式
            m = re.search(r'knowledge_base_id:\s*"?([^"\s#]+)"?', kb_line[0])
            kb_val = m.group(1) if m else ""

        # 占位符检测（警告 — 打包版合法，但提醒用户配置）
        if kb_val in {"YOUR_KNOWLEDGE_BASE_ID", "YOUR_KB_ID", ""} or kb_val.startswith("YOUR_"):
            all_ok &= check(True, "G6-KB_ID待配置(警告)",
                            f"knowledge_base_id=占位符 — 打包版正常，用户部署时需替换为自建 KB_ID")
        elif kb_val:
            all_ok &= check(True, "G6-KB_ID已配置",
                            f"knowledge_base_id={kb_val[:12]}...（请确认该 ID 属于你自己的知识库）")

    # G7: render_html.py 的 radar_score_ceiling 必须从 settings.yaml 读取，不再硬编码
    if render_path.exists():
        render_src = render_path.read_text()
        has_hardcoded_radar = "RADAR_SCORE_CEILING = " in render_src
        has_settings_reader = "_get_radar_score_ceiling" in render_src
        settings_path = BASE / "assets" / "config" / "settings.yaml"
        has_settings_key = False
        if settings_path.exists():
            settings_src = settings_path.read_text()
            has_settings_key = "radar_score_ceiling:" in settings_src
        all_ok &= check(
            not has_hardcoded_radar and has_settings_reader and has_settings_key,
            "G7-雷达阈值收口",
            "render_html.py 从 settings.yaml 读取 radar_score_ceiling，不再硬编码"
        )

    return all_ok


# ============================================================
# Layer 3: 新通道门禁（P4 新增 — 微信读书/元宝通道就绪检查）
# ============================================================
def run_channel_gate():
    print(f"\n--- 新通道门禁 ---")
    all_ok = True

    # W1: weread 登录态存在且有效（含非空 wr_vid）
    weread_state = Path.home() / ".config" / "weread_state.json"
    w_ok = False
    w_detail = f"路径: {weread_state}"
    if weread_state.exists():
        try:
            cookies = json.loads(weread_state.read_text()).get("cookies", [])
            w_ok = any(c.get("name") == "wr_vid" and c.get("value") for c in cookies)
            w_detail += f" | cookies={len(cookies)}"
            if not w_ok:
                w_detail += " | 缺 wr_vid（登录态无效，请重跑 weread_login.py）"
        except Exception as e:
            w_detail += f" | 解析失败: {e}"
    else:
        w_detail += " | 缺失（请运行 scripts/weread_login.py 扫码）"
    all_ok &= check(w_ok, "W1-weread登录态", w_detail)

    # W2: fetch_weread_week.py 存在且可编译
    fww = BASE / "scripts" / "fetch_weread_week.py"
    exists = fww.exists()
    compiles = False
    if exists:
        try:
            import py_compile
            py_compile.compile(str(fww), doraise=True)
            compiles = True
        except Exception:
            compiles = False
    all_ok &= check(exists, "W2-fetch_weread_week存在", f"路径: {fww}")
    all_ok &= check(compiles, "W2-fetch_weread_week可执行", "py_compile 通过（语法有效）")

    # W3: mp-setup-guide.md 已标记 DEPRECATED
    mp_guide = BASE / "references" / "mp-setup-guide.md"
    dep = False
    if mp_guide.exists():
        head = mp_guide.read_text()[:400]
        dep = "DEPRECATED" in head
    all_ok &= check(dep, "W3-mp-guide已废弃", "references/mp-setup-guide.md 顶部含 DEPRECATED 标记")

    # W4: 候选内容质量门禁（P6 新增 — 防 Agent 精修被跳过）
    # 检查 candidates_merged.jsonl：digest 无文末/法条段、recommend 非空、features 非空
    cand_path = BASE / "scripts" / "candidates_merged.jsonl"
    if not cand_path.exists():
        all_ok &= check(True, "W4-候选内容质量(跳过)", "无 candidates_merged.jsonl（未跑 L3 流程），跳过内容质量检查")
    else:
        import re as _re
        bad_digest, bad_recommend, bad_features = [], [], []
        try:
            for line in cand_path.read_text().splitlines():
                line = line.strip()
                if not line:
                    continue
                c = json.loads(line)
                d = (c.get("digest") or c.get("abstract") or "").strip()
                r = (c.get("recommend") or "").strip()
                f = c.get("features") or {}
                # digest 质量：非空、≥20 字、不以文末特征词/《开头（法条段）
                if len(d) < 20 or _re.match(r'^(来稿|投稿|关注|点击|长按|扫描|更多信息)|^《[^》]{1,30}》第', d):
                    bad_digest.append(c.get("title", "?")[:25])
                # recommend：非空、≥20 字
                if len(r) < 20:
                    bad_recommend.append(c.get("title", "?")[:25])
                # features：非空 dict（法律条目必须有特征标注，空 features → k-NN 评分失真）
                if not f:
                    bad_features.append(c.get("title", "?")[:25])
        except Exception as e:
            all_ok &= check(False, "W4-候选内容质量", f"解析 candidates_merged.jsonl 失败: {e}")
            return all_ok
        w4_ok = not (bad_digest or bad_recommend or bad_features)
        detail = []
        if bad_digest:
            detail.append(f"低质摘要 {len(bad_digest)} 条({','.join(bad_digest[:3])})")
        if bad_recommend:
            detail.append(f"缺推荐理由 {len(bad_recommend)} 条({','.join(bad_recommend[:3])})")
        if bad_features:
            detail.append(f"缺特征标注 {len(bad_features)} 条({','.join(bad_features[:3])})")
        all_ok &= check(w4_ok, "W4-候选内容质量", "; ".join(detail) if detail else "digest/recommend/features 全部合格（Agent 精修已执行）")

    return all_ok


def main():
    print("legal-weekly-briefing 回归测试 + 交付门禁\n")

    scoring_ok = run_scoring_tests()
    html_gate_ok = run_html_gate()
    channel_ok = run_channel_gate()

    total = PASSED + FAILED
    print(f"\n{'='*50}")
    print(f"评分引擎: {'✓ 通过' if scoring_ok else '✗ 失败'}")
    print(f"HTML门禁: {'✓ 通过' if html_gate_ok else '✗ 失败 (P0 — 阻塞交付)'}")
    print(f"新通道门禁: {'✓ 通过' if channel_ok else '✗ 失败'}")
    print(f"总计: {PASSED} 通过 / {FAILED} 失败 / {total} 项")
    sys.exit(0 if (scoring_ok and html_gate_ok and channel_ok) else 1)


if __name__ == "__main__":
    main()
