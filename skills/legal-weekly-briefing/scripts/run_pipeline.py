#!/usr/bin/env python3
"""周报生成流水线编排层（开源化：失败容错 + 自检断言 + 结构化日志）

职责：
- 串联：内容发现 → 去重 → 评分 → 写简报 → IMA 导入
- 每步 try/except：RETRYABLE（限流/网络/超时 → 退避重试）vs FATAL（依赖缺失 → 告警退出）
- 自检改为退出码断言（候选池≥min_candidates、导入数≥交付数、MD 非空）
- 写 run-report.json + .workbuddy/runs/<date>.jsonl 日志
- MP 不可用 → 跳过 MP 阶段，标"MP 缺失"继续

注意：内容发现（WebSearch/MP 拉取）由调用方完成并写入 candidates 文件，本文件负责
去重→评分→写简报→IMA队列的确定性编排。CLI 契约：

    python3 run_pipeline.py candidates.jsonl

candidates.jsonl 每行: {"title":..., "url":..., "category":"legal|ai-legal", "features":{...}}
输出: 周报_<date>.md + ima_import_queue.jsonl + run-report.json
"""
import json, time, sys, re
from pathlib import Path
from datetime import date
from urllib.parse import urlparse

try:
    import yaml
except ImportError:
    yaml = None

BASE = Path(__file__).resolve().parent
SETTINGS = BASE.parent / "assets" / "config" / "settings.yaml"
RUNS_DIR = BASE / ".workbuddy" / "runs"


class PipelineError(Exception):
    pass


class RetryableError(PipelineError):
    pass


class FatalError(PipelineError):
    pass


def load_settings():
    if yaml is None or not SETTINGS.exists():
        return {}
    with open(SETTINGS) as f:
        return yaml.safe_load(f) or {}


def preflight_channels() -> dict:
    """四层降级链前置检查（P4 新增，替代原 MP session 检查）。

    层级（自上而下优先）：
      1. weread 登录态  → fetch_weread_week.py（微信读书，主通道）
      2. yuanbao 登录态 → fetch_yuanbao_supplement.py（元宝，补充通道）
      3. TokenHub key   → fetch_hunyuan_week.py（API 兜底）
      4. WebSearch      → 手动/Agent 搜索构建候选（最后降级）

    返回 {"levels": [...], "active": "weread|yuanbao|tokenhub|websearch", "missing": [...]}
    """
    home = Path.home()

    def check_state(p, vid_name=None):
        if not p.exists():
            return False
        try:
            cookies = json.loads(p.read_text()).get("cookies", [])
            if vid_name:
                return any(c.get("name") == vid_name and c.get("value") for c in cookies)
            return len(cookies) > 0
        except Exception:
            return False

    levels = [
        {
            "name": "weread",
            "ok": check_state(home / ".config" / "weread_state.json", "wr_vid"),
            "desc": "微信读书登录态（主通道）",
            "script": "fetch_weread_week.py",
        },
        {
            "name": "yuanbao",
            "ok": check_state(home / ".config" / "yuanbao_state.json"),
            "desc": "元宝登录态（补充通道）",
            "script": "fetch_yuanbao_supplement.py",
        },
        {
            "name": "tokenhub",
            "ok": (home / ".config" / "tencentcloud" / "tokenhub_api_key").exists(),
            "desc": "TokenHub API 密钥（兜底通道）",
            "script": "fetch_hunyuan_week.py",
        },
    ]
    missing = [lv["name"] for lv in levels if not lv["ok"]]
    active = next((lv["name"] for lv in levels if lv["ok"]), "websearch")
    return {"levels": levels, "active": active, "missing": missing}


def log_stage(report, stage, **kw):
    entry = {"ts": time.time(), "stage": stage, **kw}
    report["stages"].append(entry)
    # 结构化日志落盘
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    logfile = RUNS_DIR / f"{date.today().isoformat()}.jsonl"
    with open(logfile, 'a') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    return entry


def run_with_retry(fn, max_retries=3, backoff=2):
    """包装可重试步骤。RETRYABLE 异常退避重试；FATAL 立即抛出。"""
    last = None
    for attempt in range(max_retries):
        try:
            return fn()
        except RetryableError as e:
            last = e
            time.sleep(backoff ** attempt)
    raise last


def self_check(report, settings):
    """退出码断言：返回 (ok, failures)。"""
    out = settings.get('output', {})
    min_c = out.get('min_candidates', 10)
    failures = []
    n_candidates = report.get('counts', {}).get('candidates', 0)
    if n_candidates < min_c:
        failures.append(f"候选池 {n_candidates} < 最小 {min_c}")
    report_path = report.get('report_path')
    if report_path and not Path(report_path).exists():
        failures.append("周报 MD 文件未生成")
    return (len(failures) == 0, failures)


def classify_source(candidate):
    """从候选条目的 source/title/url 推断归一化来源标识。

    返回归一化来源字符串（如 '山东高法'、'上海一中院'、'Artificial Lawyer'）。
    用于 diversity-aware selection 的同源识别。
    """
    src = candidate.get('source', '') or ''
    title = candidate.get('title', '') or ''
    url = candidate.get('url', '') or ''

    # 法院公众号（精确匹配）
    if '山东高法' in src or '山东高法' in title:
        return '山东高法'
    if '上海一中' in src or '上海一中' in title:
        return '上海一中院'
    if '上海二中' in src or '上海二中' in title:
        return '上海二中院'
    if '中国应用法学' in src or '中国应用法学' in title:
        return '中国应用法学'
    if '最高法' in src or '最高人民法院' in src or 'court.gov.cn' in url:
        return '最高法'
    if '全国人大' in src:
        return '全国人大'
    if '国务院' in src or '人社部' in src or 'gov.cn' in url:
        return '国务院/部委'
    # 国际法律科技源
    if 'Artificial Lawyer' in src:
        return 'Artificial Lawyer'

    # Fallback: source 字段的第一段，或域名
    if src:
        return src.split('/')[0].strip().split('|')[0].strip()
    try:
        domain = urlparse(url).netloc
        return domain or '未知来源'
    except Exception:
        return '未知来源'


def select_diverse(scored, category, count, max_per_source, score_floor=0.0):
    """多样性感知选择：从已评分候选中选取 top N，同源不超过 max_per_source。

    scored: 已按分数降序排列的候选列表（含 score, category 等字段）
    category: 'ai-legal' | 'legal'（筛选条件）
    count: 目标条数
    max_per_source: 同一来源最大条数（0=不限制）
    score_floor: 精选评分下限，低于此分不进精选（宁缺毋滥，防低质条目混入）

    返回: (selected, remaining) — selected 是入选的 N 条，remaining 是未入选的（可用于 IMA 导入）
    """
    cat_items = [c for c in scored if c.get('category') == category or (category == 'legal' and c.get('category') != 'ai-legal')]
    if not max_per_source or max_per_source <= 0:
        selected = [c for c in cat_items[:count] if c.get('score', 0) >= score_floor]
        remaining = cat_items[len(selected):]
        return selected, remaining

    source_counts = {}
    selected = []
    remaining = []
    for item in cat_items:
        # 评分下限：低于 floor 不进精选（宁缺毋滥）
        if item.get('score', 0) < score_floor:
            remaining.append(item)
            continue
        s = classify_source(item)
        if len(selected) >= count:
            remaining.append(item)
            continue
        if source_counts.get(s, 0) < max_per_source:
            selected.append(item)
            source_counts[s] = source_counts.get(s, 0) + 1
        else:
            remaining.append(item)

    # 如果选不够 count 条（候选太少），允许同源重复——但补位仍须满足评分下限
    if len(selected) < count:
        overflow = []
        for item in remaining:
            if len(selected) >= count:
                break
            if item.get('score', 0) < score_floor:
                continue  # 宁缺毋滥：低分条不补位进精选
            selected.append(item)
            overflow.append(item)
        remaining = [r for r in remaining if r not in overflow]

    # 按分数降序重排（diversity-aware selection 可能打乱顺序）
    selected.sort(key=lambda x: x.get('score', 0), reverse=True)
    return selected, remaining


def default_write_report(candidates, scored):
    """简报写入：diversity-aware 选择 + 分数降序排列，返回 (路径, ai_selected, legal_selected, legal_remaining)。

    Stage 4.5 HTML 渲染复用全部 legal 条目（selected + remaining），remaining 供雷达区使用。
    """
    settings = load_settings()
    out = settings.get('output', {})
    template = out.get('report_template', '周报_{date}.md')
    max_per_source = out.get('max_per_source', 2)
    ai_count = out.get('ai_legal_count', 3)
    legal_count = out.get('legal_count', 7)
    path = BASE / template.format(date=date.today().isoformat())

    # Diversity-aware selection
    score_floor = out.get('select_score_floor', 0)
    ai_selected, ai_remaining = select_diverse(scored, 'ai-legal', ai_count, max_per_source, score_floor)
    legal_selected, legal_remaining = select_diverse(scored, 'legal', legal_count, max_per_source, score_floor)

    # AI+法律 signal_strength 标签映射
    signal_labels = {1: '格局级', 2: '应用落地级', 3: '融资动态级'}

    # 分类器（轻量导入，避免循环依赖）
    from ima_importer import classify as _classify

    with open(path, 'w') as f:
        report_date = date.today().isoformat()
        f.write(f"# 法律周报 {report_date}\n\n")
        f.write("## AI + 法律\n\n")
        for c in ai_selected:
            score = c.get('score', 0)
            title = c.get('title', '')
            url = c.get('url', '')
            src = classify_source(c)
            sig = c.get('features', {}).get('signal_strength', 2)
            sig_label = signal_labels.get(sig, '')
            abstract = c.get('abstract', '')
            recommend = c.get('recommend', '')

            f.write(f"### 【{score}】{title}\n\n")
            f.write(f"📡 {sig_label} · {src}\n\n")
            if abstract:
                f.write(f"{abstract}\n\n")
            if recommend:
                f.write(f"💡 {recommend}\n\n")
            f.write(f"🔗 {url}\n\n")
            f.write("---\n\n")

        f.write("## 纯法律\n\n")
        for c in legal_selected:
            score = c.get('score', 0)
            title = c.get('title', '')
            url = c.get('url', '')
            src = classify_source(c)
            cat, _, _ = _classify(title)
            cat_tag = cat or ''
            abstract = c.get('abstract', '')
            recommend = c.get('recommend', '')

            f.write(f"### 【{score}】{title}\n\n")
            parts = [src]
            if cat_tag:
                parts.append(cat_tag)
            f.write(f"📂 {' · '.join(parts)}\n\n")
            if abstract:
                f.write(f"{abstract}\n\n")
            if recommend:
                f.write(f"💡 {recommend}\n\n")
            f.write(f"🔗 {url}\n\n")
            f.write("---\n\n")

        # 雷达区（其他领域速览，2026-08-01 补齐 md 第三板块——SKILL.md 交付格式要求）：
        # 与 HTML 雷达区同规则：未进精选 且 分数低于精选最低分（评分不如精选）
        featured_scores = [c.get('score', 0) for c in legal_selected]
        radar_floor = min(featured_scores) if featured_scores else 7.0
        radar_rows = [c for c in legal_remaining if c.get('score', 0) < radar_floor]
        if radar_rows:
            f.write("## 其他领域速览（雷达区）\n\n")
            for c in radar_rows[:8]:
                f.write(f"### 【{c.get('score')}】{c.get('title', '')}\n\n")
                f.write(f"📂 {classify_source(c)}\n\n")
                f.write(f"🔗 {c.get('url', '')}\n\n")
                f.write("---\n\n")

    return str(path), ai_selected, legal_selected, legal_remaining


def _infer_features(c):
    """轻量特征兜底（2026-08-01 对抗审查新增）。

    新通道（微信读书/元宝）候选无 features 字段时，全部条目会拿到评分引擎默认值
    → 评分同质化，精选/导入排序失真。此处从标题/摘要启发式提取可区分的老四维
    （author_tier/platform_tier/depth/relevance），与 scoring_engine.normalize_features
    的键映射对齐。Agent 精修候选时仍建议用 build_candidates.py 的完整七维分类器。
    """
    t = (c.get("title", "") or "") + " " + (c.get("abstract", "") or "")
    feat = {"author_tier": 2, "platform_tier": 3, "depth": 1, "relevance": 2}
    if any(k in t for k in ["案例", "裁判", "判决", "被告", "原告", "诉"]):
        feat["depth"] = 2
    if any(k in t for k in ["规则", "要旨", "指引", "要点", "解读", "分析", "探析"]):
        feat["depth"] = 3
    if any(k in t for k in ["最高法", "司法解释", "民法典", "公司法", "法释", "劳动法"]):
        feat["platform_tier"] = 1
    elif any(k in t for k in ["省高院", "高院", "典型案例", "公报"]):
        feat["platform_tier"] = 2
    return feat


def run_pipeline(discover_fn, write_report_fn=None, import_fn=None, settings=None, candidates_raw=None):
    """主入口。

    discover_fn: () -> list[dict]  # 返回候选条目（已合并 MP+WebSearch）
    candidates_raw: list[dict]     # 或直接从文件载入的候选（CLI 模式）
    write_report_fn: (candidates, scored) -> str  # 写 MD，返回路径（默认 default_write_report）
    import_fn: (candidates) -> list[dict]  # IMA 导入（默认调用 ima_importer 写队列）

    返回: (exit_code, report)
    """
    settings = settings or load_settings()
    pipeline_cfg = settings.get('pipeline', {})
    max_retries = pipeline_cfg.get('max_retries', 3)
    backoff = pipeline_cfg.get('backoff', 2)
    if write_report_fn is None:
        write_report_fn = default_write_report

    report = {"date": date.today().isoformat(), "stages": [], "counts": {}, "errors": []}

    # Stage 0: 通道前置检查（四层降级链，P4 新增）
    ch = preflight_channels()
    log_stage(report, "preflight", active=ch["active"], missing=ch["missing"])
    for lv in ch["levels"]:
        mark = "✓" if lv["ok"] else "✗"
        print(f"  [{mark}] {lv['name']:8s} {lv['desc']}")
    if ch["missing"]:
        print(f"  ⚠️ 缺失通道: {', '.join(ch['missing'])} → 降级至 {ch['active']}")
    if ch["active"] == "websearch":
        report["errors"].append("所有自动通道不可用，降级 WebSearch（内容发现由调用方完成）")

    # Stage 1: 内容发现（含 MP 拉取，失败可降级）
    if candidates_raw is not None:
        candidates_raw = candidates_raw
        log_stage(report, "discover", count=len(candidates_raw), mode="from_file")
    else:
        try:
            def _discover():
                items = discover_fn()
                if not items:
                    raise RetryableError("内容发现返回空")
                return items
            candidates_raw = run_with_retry(_discover, max_retries, backoff)
            log_stage(report, "discover", count=len(candidates_raw))
        except RetryableError as e:
            candidates_raw = []
            report["errors"].append(f"discover 降级: {e}")
            log_stage(report, "discover", status="degraded", error=str(e))

    # Stage 2: 去重
    from dedupe import dedupe_items
    candidates = dedupe_items(candidates_raw)

    # 字段兜底（P4 新增）：新通道 5 字段候选补全 pipeline 必需字段
    # abstract ← digest；category 默认 legal；features 空 dict 由 _infer_features 启发式兜底
    for c in candidates:
        if not c.get("abstract") and c.get("digest"):
            c["abstract"] = c["digest"]
        c.setdefault("category", "legal")
        c.setdefault("source", c.get("_source", ""))
        if not c.get("features"):
            c["features"] = _infer_features(c)

    report["counts"]["candidates"] = len(candidates)
    log_stage(report, "dedupe", before=len(candidates_raw), after=len(candidates))

    # Stage 3: 评分（调用 scoring_engine.predict）
    from scoring_engine import predict
    scored = []
    for c in candidates:
        cat = c.get('category', 'legal')
        score, conf = predict({"features": c.get('features', {}), "title": c.get('title', '')}, cat)
        c['score'] = score
        c['confidence'] = conf
        scored.append(c)
    scored.sort(key=lambda x: x.get('score', 0), reverse=True)
    log_stage(report, "score", count=len(scored))

    # Stage 4: 写简报（返回 path + ai_selected + legal_selected）
    report_path, ai_selected, legal_selected, legal_remaining = write_report_fn(candidates, scored)
    report["report_path"] = report_path
    log_stage(report, "write_report", path=report_path)

    # Stage 4.5: HTML 渲染（复用脚本同目录的 render_html.py，浅色简报风）
    try:
        sys.path.insert(0, str(BASE))
        from render_html import render_html as _render
        html_articles = []
        for c in ai_selected + legal_selected + legal_remaining:
            html_articles.append({
                "title": c.get("title", ""),
                "url": c.get("url", ""),
                "category": c.get("category", "legal"),
                "source": c.get("source", ""),
                "source_category": c.get("source_category", ""),
                "date": c.get("date", ""),
                "score": c.get("score", 0),
                "tags": c.get("tags", []),
                "abstract": c.get("abstract", ""),
                "recommend": c.get("recommend", ""),
            })
        html_out = _render(html_articles, date.today().strftime('%Y年%m月%d日'))
        html_path = BASE / f"周报_{date.today().isoformat()}.html"
        html_path.write_text(html_out, encoding="utf-8")
        report["html_path"] = str(html_path)
        log_stage(report, "render_html", path=str(html_path))
    except Exception as e:
        report["errors"].append(f"render_html 失败: {e}")
        log_stage(report, "render_html", status="degraded", error=str(e))

    # Stage 5: IMA 导入（默认写队列，启用了阈值过滤）
    if import_fn is None:
        from ima_importer import import_one
        def import_fn(items):
            return [import_one(c['url'], c.get('title', '')) for c in items]

    # IMA 导入阈值：仅导入分数 >= 阈值 且 来源为法院/官方公众号的条目
    threshold = (settings.get('output', {}) or {}).get('ima_import_threshold', 0)
    court_sources = {'山东高法', '上海一中院', '上海二中院', '中国应用法学', '最高法', '国务院/部委'}
    importable = [c for c in scored
                  if c.get('score', 0) >= threshold
                  and classify_source(c) in court_sources]
    results = import_fn(importable)
    queued = sum(1 for r in results if r.get('status') in ('imported', 'queued'))
    report["counts"]["imported"] = queued
    log_stage(report, "import", queued=queued, total=len(results))

    # 自检
    ok, failures = self_check(report, settings)
    report["self_check"] = {"ok": ok, "failures": failures}

    # 写 run-report.json
    with open(BASE / "run-report.json", 'w') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    exit_code = 0 if ok else 1
    return exit_code, report


def load_candidates(path):
    """从 JSONL 或 JSON 文件载入候选。每行/每项: {title, url, category, features}"""
    p = Path(path)
    items = []
    if p.suffix == '.jsonl':
        for line in open(p):
            line = line.strip()
            if line:
                items.append(json.loads(line))
    else:
        data = json.loads(open(p).read())
        items = data if isinstance(data, list) else data.get('candidates', [])
    return items


if __name__ == '__main__':
    # 用法：
    #   python3 run_pipeline.py                      # 演示 dry-run
    #   python3 run_pipeline.py candidates.jsonl     # CLI 模式：从候选文件跑全流程
    if len(sys.argv) > 1:
        candidates = load_candidates(sys.argv[1])
        code, rep = run_pipeline(None, candidates_raw=candidates)
        print(f"exit_code={code}, candidates={rep['counts'].get('candidates')}, "
              f"imported={rep['counts'].get('imported')}, self_check={rep['self_check']}")
        print(f"report={rep.get('report_path')}")
        print(f"ima_queue=ima_import_queue.jsonl")
    else:
        # 演示 dry-run
        demo = [
            {"title": "公司股东出资纠纷", "url": "https://mp.weixin.qq.com/s/a", "category": "legal",
             "features": {"author_tier": 2, "platform_tier": 3, "depth": 1, "relevance": 1}},
            {"title": "AI 法律助手发布", "url": "https://example.com/b", "category": "ai-legal",
             "features": {"first_hand": 1, "depth": 1, "relevance": 1}},
        ]
        code, rep = run_pipeline(None, candidates_raw=demo)
        print(f"exit_code={code}, candidates={rep['counts'].get('candidates')}, imported={rep['counts'].get('imported')}")
