#!/usr/bin/env python3
"""读取 run_pipeline.py 产出的 ima_import_queue.jsonl 并直调 IMA OpenAPI 全量导入。

与 run_pipeline.py 的分工：
- run_pipeline.py Stage 5: 评分 → 分类 → 写入 ima_import_queue.jsonl（数据准备层）
- import_ima.py: 读取队列 → 调 IMA OpenAPI 导入 → 状态核查（执行层）

不再独立重建队列或重新评分——单一入口避免双轨不一致。
"""
import json, time, os, sys
from pathlib import Path
from datetime import date
from collections import defaultdict

BASE = Path(__file__).resolve().parent
IMA_CFG = Path.home() / ".config/ima"
QUEUE_FILE = BASE / "ima_import_queue.jsonl"


def load_queue():
    """从 ima_import_queue.jsonl 读取待导入条目。"""
    if not QUEUE_FILE.exists():
        print("⚠️  ima_import_queue.jsonl 不存在，请先运行 run_pipeline.py")
        sys.exit(1)
    items = []
    for line in open(QUEUE_FILE):
        line = line.strip()
        if line:
            items.append(json.loads(line))
    if not items:
        print("⚠️  ima_import_queue.jsonl 为空，无待导入条目")
        sys.exit(0)
    return items


def load_kb_id():
    """加载 KB_ID 并做安全门禁（占位符阻断）。"""
    import yaml as _yaml
    taxonomy = BASE / "config" / "taxonomy.yaml"
    kb_id = (_yaml.safe_load(open(taxonomy)) or {}).get('knowledge_base_id', '')

    _FORBIDDEN = {"YOUR_KNOWLEDGE_BASE_ID", "YOUR_KB_ID", "your_knowledge_base_id", ""}
    if kb_id in _FORBIDDEN or kb_id.startswith("YOUR_") or kb_id.startswith("REPLACE"):
        print("\n⚠️  ================================================================")
        print("⚠️  阻断: config/taxonomy.yaml 中 knowledge_base_id 仍为占位符")
        print("⚠️  请先配置你的 IMA 知识库 ID")
        print("⚠️  ================================================================\n")
        sys.exit(1)
    return kb_id


def import_batches(qitems, kb_id):
    """按 folder_id 分组，每批 ≤10 条，调 IMA OpenAPI。返回 (ok, fail)。"""
    import requests
    API = "https://ima.qq.com/openapi/wiki/v1/import_urls"
    client_id = (IMA_CFG / "client_id").read_text().strip()
    api_key = (IMA_CFG / "api_key").read_text().strip()
    headers = {
        "ima-openapi-clientid": client_id,
        "ima-openapi-apikey": api_key,
        "Content-Type": "application/json",
    }

    groups = defaultdict(list)
    for q in qitems:
        groups[q.get("folder_id", "")].append(q)

    ok_total = 0
    fail_total = 0
    for folder_id, items in groups.items():
        urls = [i["url"] for i in items]
        for i in range(0, len(urls), 10):
            batch = urls[i:i+10]
            payload = {"knowledge_base_id": kb_id, "folder_id": folder_id, "urls": batch}
            try:
                r = requests.post(API, headers=headers, json=payload, timeout=30)
                j = r.json()
                if j.get("ret") == 0 or j.get("code") == 0 or j.get("ret_code") == 0:
                    ok_total += len(batch)
                    fid_short = folder_id[:20] if folder_id else "(根目录)"
                    print(f"  ✅ 导入成功 folder={fid_short} {len(batch)} 条")
                else:
                    fail_total += len(batch)
                    print(f"  ❌ 失败 folder={folder_id[:20]} {len(batch)} 条: {j}")
            except Exception as e:
                fail_total += len(batch)
                print(f"  ❌ 异常 folder={folder_id[:20]}: {e}")

    return ok_total, fail_total


def check_imports(qitems, kb_id):
    """导入后状态核查：检查各条目是否已在 KB 中可检索。

    由于 IMA 解析 MP 文章需要较长时间（数小时），30 秒后立即检查通常全量报"未找到"。
    这是正常的延迟现象，非导入失败。本检查提供参考信息，不影响导入成功判定。
    """
    import requests
    client_id = (IMA_CFG / "client_id").read_text().strip()
    api_key = (IMA_CFG / "api_key").read_text().strip()
    headers = {
        "ima-openapi-clientid": client_id,
        "ima-openapi-apikey": api_key,
        "Content-Type": "application/json",
    }
    SEARCH_API = "https://ima.qq.com/openapi/wiki/v1/search_knowledge"

    print("\n⏳ 等待 IMA 解析（30秒）...")
    time.sleep(30)

    found = 0
    not_found = 0
    for q in qitems:
        url = q["url"]
        try:
            resp = requests.post(SEARCH_API,
                json={"query": url.split("/")[-1][:20], "knowledge_base_id": kb_id, "cursor": ""},
                headers=headers, timeout=10)
            items = resp.json().get("data", {}).get("info_list", [])
            if items and any(item.get("media_id") for item in items):
                found += 1
            else:
                not_found += 1
        except Exception:
            not_found += 1

    print(f"\n📊 导入后状态: 可检索 {found}/{len(qitems)}，解析中 {not_found}/{len(qitems)}")
    if not_found > 0:
        print(f"   💡 IMA 解析 MP 文章通常需数小时，30 秒后暂不可检索为正常现象。")
        print(f"      建议 2-4 小时后在 IMA 网页端确认。")
    else:
        print("   ✅ 全部可检索")
    return found, not_found


def main():
    qitems = load_queue()
    kb_id = load_kb_id()

    print(f"📋 加载队列：{len(qitems)} 条（来源: {QUEUE_FILE.name}，由 run_pipeline.py 产出）")
    missing_score = 0
    for q in qitems:
        fid = q.get("folder_id", "")[:20] or "(根目录)"
        cat = q.get("category") or "-"
        score = q.get('score', '?')
        source = q.get('source', '?')
        if score == '?' or score is None:
            missing_score += 1
        print(f"  【{score}】{source} | {cat} | {fid} | {q['title'][:40]}")
    if missing_score:
        print(f"  ⚠️ {missing_score} 条缺少 score 字段（不影响 IMA 导入）")

    print(f"\n🚀 开始导入 IMA 知识库...")
    ok, fail = import_batches(qitems, kb_id)
    print(f"\n📊 IMA 导入统计：成功 {ok} 条，失败 {fail} 条")

    # 写导入报告
    report = {
        "date": date.today().isoformat(),
        "ok": ok, "fail": fail,
        "queue": qitems,
        "source": str(QUEUE_FILE.name),
    }
    with open(BASE / "ima_import_report.json", "w") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # 状态核查
    check_imports(qitems, kb_id)


if __name__ == "__main__":
    main()
