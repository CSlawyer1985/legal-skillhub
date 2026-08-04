#!/usr/bin/env python3
"""候选池去重工具

用法：
    python3 dedupe.py < candidates.jsonl > deduped.jsonl
    # 或直接调用 dedupe_items(items, threshold=0.85) -> list

输入：每行 JSON {"title":..., "url":..., "source":...}
输出：去重后候选列表（保留首次出现）
"""
import json, sys, re
from pathlib import Path

STOPWORDS = set("的 了 是 在 与 和 及 对 关于 最高人民法院 人民法院 法院 公布 发布 关于 印发 通知".split())


def normalize_title(title):
    """去停用词 + 去标点 + 小写化，用于相似度比较。"""
    if not title:
        return ""
    t = re.sub(r'[^\w\u4e00-\u9fff]', '', title)
    for w in STOPWORDS:
        t = t.replace(w, '')
    return t.lower()


def canonical_url(url):
    """URL 规范化：去参数、去 trailing slash、统一 scheme。

    注意：mp.weixin.qq.com 链接保留 query（__biz/mid/sn 是文章身份标识，
    砍掉会把不同文章误判为同一 URL）。"""
    if not url:
        return ""
    u = url.split('#')[0].rstrip('/').lower()
    if "mp.weixin.qq.com" in u:
        return u
    return u.split('?')[0]


def similarity(a, b):
    """基于字符 bigram 的 Jaccard 相似度。"""
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    def bigrams(s):
        return set(s[i:i+2] for i in range(len(s) - 1))
    sa, sb = bigrams(a), bigrams(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def dedupe_items(items, threshold=0.85):
    """对候选列表去重。同一 URL 或标题相似度 >= threshold 视为重复。"""
    seen = []
    result = []
    for item in items:
        title = normalize_title(item.get('title', ''))
        url = canonical_url(item.get('url', ''))
        dup = False
        for s in seen:
            if url and s['url'] == url:
                dup = True
                break
            if title and s['title'] and similarity(title, s['title']) >= threshold:
                dup = True
                break
        if not dup:
            seen.append({'title': title, 'url': url})
            result.append(item)
    return result


if __name__ == '__main__':
    items = []
    for line in sys.stdin:
        line = line.strip()
        if line:
            items.append(json.loads(line))
    for it in dedupe_items(items):
        print(json.dumps(it, ensure_ascii=False))
