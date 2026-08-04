#!/usr/bin/env python3
"""IMA 知识库导入模块（开源化：幂等 + 失败队列 + 配置驱动 + 队列解耦）

职责：
- 从 config/taxonomy.yaml 解析领域 → folder_id
- 导入前查重（imported_cache.jsonl，url 为键）
- 分类决策后写入 ima_import_queue.jsonl（待导入队列）
- 失败写入 failed_import.jsonl + 指数退避重试
- 多领域命中 → 主领域优先，副类记录

设计：本模块不直接调用 IMA API。它产出"待导入队列"，由外层客户端消费：
- WorkBuddy 环境：自动化运行时读取队列 → 调用 ima-skill 的 import_urls MCP 工具
- 开源用户：可用 IMA OpenAPI / 客户端手动导入队列中的 url+folder_id
这样 Python 模块保持可测试、不耦合 MCP 运行时，且不硬编码凭证。
"""
import json, time, sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

BASE = Path(__file__).resolve().parent
# taxonomy 读取优先级：本地真实配置（~/.config/legal-weekly/taxonomy.local.yaml，含用户自建 KB_ID/folder_id）
# > 仓库配置（assets/config/taxonomy.yaml，开源打包版恒为占位符——推送安全，真实值不入 git）
_LOCAL_TAXONOMY = Path.home() / ".config" / "legal-weekly" / "taxonomy.local.yaml"
TAXONOMY = _LOCAL_TAXONOMY if _LOCAL_TAXONOMY.exists() else BASE.parent / "assets" / "config" / "taxonomy.yaml"
CACHE = BASE / "imported_cache.jsonl"
FAILED = BASE / "failed_import.jsonl"
NEEDS_LLM = BASE / "needs_llm_classify.jsonl"


def load_taxonomy():
    if yaml is None or not TAXONOMY.exists():
        return None
    with open(TAXONOMY) as f:
        return yaml.safe_load(f) or {}


def classify(title, tags=None):
    """返回 (primary_category, folder_id, secondary_categories)。无命中返回 (None, uncategorized_folder_id, [])。"""
    tax = load_taxonomy()
    if not tax:
        return None, "", []
    cats = tax.get('categories', [])
    text = (title or '') + ' ' + ' '.join(tags or [])
    matched = []
    for c in cats:
        kw = c.get('keywords', [])
        if any(k in text for k in kw):
            matched.append(c)
    if not matched:
        return None, tax.get('uncategorized_folder_id', ''), []
    # 主领域：priority 最高；并列取首个
    matched.sort(key=lambda c: c.get('priority', 0), reverse=True)
    primary = matched[0]
    secondary = [c['name'] for c in matched[1:]]
    return primary['name'], primary.get('folder_id', ''), secondary


def load_cache():
    if not CACHE.exists():
        return set()
    with open(CACHE) as f:
        return set(line.strip() for line in f if line.strip())


def save_cache(url):
    with open(CACHE, 'a') as f:
        f.write(url + '\n')


def load_failed():
    if not FAILED.exists():
        return []
    with open(FAILED) as f:
        return [json.loads(line) for line in f if line.strip()]


def save_failed(entry):
    with open(FAILED, 'a') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')


def save_needs_llm(entry):
    """无法分类的条目写入 needs_llm_classify.jsonl，由 Agent 按 SKILL.md Step 5 做 LLM 批量兜底分类。"""
    with open(NEEDS_LLM, 'a') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')


def import_one(url, title, max_retries=3, backoff=2):
    """决定单条是否导入 IMA，并写入待导入队列。

    返回 dict: {url, status, folder_id, category, error}
    status: 'queued'（已写入待导入队列）| 'skipped_duplicate' | 'failed' | 'needs_llm'（分类未命中，待 LLM 兜底）

    设计：本模块不直接调用 IMA API。它负责"分类决策 + 幂等查重 + 队列写出"，
    真正的 import_urls 调用由外层（WorkBuddy MCP / 用户客户端）读取队列后执行。
    这样 Python 模块保持可测试、不耦合 MCP 运行时，开源用户可用任意 IMA 客户端消费队列。
    """
    cache = load_cache()
    if url in cache:
        return {"url": url, "status": "skipped_duplicate", "folder_id": "", "category": "", "error": ""}

    category, folder_id, secondary = classify(title)
    # 占位符检测：taxonomy.yaml 未配置（开源打包版）时 folder_id 是占位符，
    # 视为未分类 → needs_llm，避免把条目 queued 到无效 folder
    if folder_id and "YOUR_" in folder_id:
        folder_id = ""
    if not folder_id:
        # 无 folder_id（分类未命中且未配置兜底）-> 写入 needs_llm_classify.jsonl，由 Agent LLM 兜底分类（SKILL.md Step 5）
        entry = {"url": url, "title": title, "ts": time.time()}
        save_needs_llm(entry)
        return {"url": url, "status": "needs_llm", "folder_id": "", "category": category or "", "error": "unclassified"}

    # 重试：队列写出可能因 IO 失败，退避重试
    last_err = ""
    for attempt in range(max_retries):
        try:
            _enqueue(url, title, folder_id, category, secondary)
            save_cache(url)
            return {"url": url, "status": "queued", "folder_id": folder_id, "category": category or "", "error": ""}
        except Exception as e:
            last_err = str(e)
            time.sleep(backoff ** attempt)

    entry = {"url": url, "title": title, "folder_id": folder_id, "error": last_err, "ts": time.time()}
    save_failed(entry)
    return {"url": url, "status": "failed", "folder_id": folder_id, "category": category or "", "error": last_err}


def _enqueue(url, title, folder_id, category, secondary):
    """将待导入条目追加到队列文件，供外层 IMA 客户端消费。

    队列格式（JSONL）：{url, title, folder_id, category, secondary, ts}
    外层消费后调用 import_urls(knowledge_base_id, folder_id, [url])。
    """
    queue = BASE / "ima_import_queue.jsonl"
    record = {
        "url": url,
        "title": title,
        "folder_id": folder_id,
        "category": category,
        "secondary": secondary,
        "ts": time.time(),
    }
    with open(queue, 'a') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    # CLI: python3 ima_importer.py < url_list.jsonl
    # 每行: {"url":..., "title":...}
    results = []
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        r = import_one(obj['url'], obj.get('title', ''))
        results.append(r)
        print(json.dumps(r, ensure_ascii=False))
    queued = sum(1 for r in results if r['status'] == 'queued')
    failed = sum(1 for r in results if r['status'] == 'failed')
    print(f"# summary: queued={queued} failed={failed} total={len(results)}", file=sys.stderr)
    print("# 待导入队列已写入 ima_import_queue.jsonl，由外层 IMA 客户端（MCP/API/手动）消费", file=sys.stderr)
