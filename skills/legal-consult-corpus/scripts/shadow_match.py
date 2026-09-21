#!/usr/bin/env python3
"""口径匹配引擎 — BM25 关键词匹配，零外部依赖。

输入：问题文本 + 口径库 JSON
输出：Top-K 匹配结果 + 相似度分数
"""

import argparse
import json
import math
import os
import re
import sys
from collections import Counter


def tokenize(text):
    """中文分词：按2-gram + 英文单词混合切分。"""
    if not text:
        return []
    tokens = []
    # 英文单词
    tokens.extend(re.findall(r'[a-zA-Z]+', text.lower()))
    # 中文 2-gram
    cn = re.findall(r'[\u4e00-\u9fff]', text)
    for i in range(len(cn) - 1):
        tokens.append(cn[i] + cn[i + 1])
    # 单字兜底
    tokens.extend(cn)
    return tokens


class BM25:
    """BM25 文本检索，纯 stdlib 实现。"""

    def __init__(self, k1=1.5, b=0.75):
        self.k1 = k1
        self.b = b
        self.docs = []
        self.doc_lens = []
        self.avgdl = 0
        self.df = Counter()
        self.idf = {}
        self.n = 0

    def fit(self, texts):
        """构建索引。texts: list[str]"""
        self.docs = [tokenize(t) for t in texts]
        self.doc_lens = [len(d) for d in self.docs]
        self.n = len(self.docs)
        self.avgdl = sum(self.doc_lens) / self.n if self.n else 1
        self.df = Counter()
        for tokens in self.docs:
            self.df.update(set(tokens))
        self.idf = {}
        for term, freq in self.df.items():
            self.idf[term] = math.log((self.n - freq + 0.5) / (freq + 0.5) + 1)

    def score(self, query_text, top_k=3):
        """返回 [(doc_index, score)] Top-K。"""
        query_tokens = tokenize(query_text)
        if not query_tokens or self.n == 0:
            return []
        scores = []
        for i, doc_tokens in enumerate(self.docs):
            s = 0
            dl = self.doc_lens[i]
            tf = Counter(doc_tokens)
            for qt in query_tokens:
                if qt not in tf:
                    continue
                f = tf[qt]
                idf = self.idf.get(qt, 0)
                numerator = f * (self.k1 + 1)
                denominator = f + self.k1 * (1 - self.b + self.b * dl / self.avgdl)
                s += idf * numerator / denominator
            scores.append((i, s))
        scores.sort(key=lambda x: -x[1])
        return scores[:top_k]


def match(question, corpus, config=None, top_k=3):
    """
    口径匹配主函数。

    Parameters
    ----------
    question : str
        用户问题文本
    corpus : list[dict]
        口径库（consult_corpus.json）
    config : dict, optional
        配置（含 thresholds.reuse_similarity）
    top_k : int

    Returns
    -------
    list[dict]
        [{corpus_entry, similarity, rank}]
    """
    if not corpus or not question.strip():
        return []

    # 构建 BM25 索引
    texts = [c.get("典型问题", "") + " " + c.get("标准答复", "") for c in corpus]
    bm25 = BM25()
    bm25.fit(texts)

    # BM25 原始分仅用于同分时的次序 tiebreak
    raw_scores = dict(bm25.score(question, top_k=len(corpus)))

    # 绝对相似度 = IDF 加权的查询覆盖率：
    # 命中的查询词 idf 之和 / 全部查询词 idf 之和。
    # 未覆盖的高信息量词进分母 -> 离题问题分数自然降低；常见虚词 idf 小几乎不贡献。
    query_tokens = set(tokenize(question))
    idf = bm25.idf
    # 语料外词（OOV）信息量最高：赋最大 idf，确保离题主语词计入分母、压低覆盖率，
    # 否则 OOV 取 0 会让"只命中怎么处理"的离题查询虚高误判 REUSE。
    oov_idf = max(idf.values()) if idf else 1.0
    q_weight = sum(idf.get(t, oov_idf) for t in query_tokens)

    threshold = (config or {}).get("thresholds", {}).get("reuse_similarity", 0.7)

    scored = []
    for idx, entry in enumerate(corpus):
        doc_tokens = set(tokenize(texts[idx]))
        hit_weight = sum(idf.get(t, 0.0) for t in query_tokens if t in doc_tokens)
        sim = (hit_weight / q_weight) if q_weight > 0 else 0.0
        scored.append((idx, sim, raw_scores.get(idx, 0.0)))

    # 相似度降序，同分按 BM25 原始分降序
    scored.sort(key=lambda x: (-x[1], -x[2]))

    matched = []
    for rank, (idx, sim, _raw) in enumerate(scored[:top_k]):
        matched.append({
            "rank": rank + 1,
            "corpus_entry": corpus[idx],
            "similarity": round(sim, 3),
            "is_reuse": sim >= threshold,
        })

    return matched


def main():
    ap = argparse.ArgumentParser(description="法律咨询口径匹配引擎")
    ap.add_argument("--question", required=True, help="待匹配的问题文本")
    ap.add_argument("--corpus", required=True, help="口径库 JSON 路径")
    ap.add_argument("--config", default=None, help="配置文件路径")
    ap.add_argument("--top-k", type=int, default=3)
    ap.add_argument("--output", default=None)
    args = ap.parse_args()

    corpus = json.load(open(args.corpus, encoding="utf-8"))
    config = json.load(open(args.config, encoding="utf-8")) if args.config else None

    results = match(args.question, corpus, config=config, top_k=args.top_k)

    out = json.dumps(results, ensure_ascii=False, indent=2, default=str)
    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"[shadow_match] Top{args.top_k} → {args.output}", file=sys.stderr)
    else:
        print(out)

    # 摘要输出到 stderr
    for r in results:
        tag = "REUSE" if r["is_reuse"] else "NEW"
        print(f"  [{tag}] {r['similarity']:.3f} | {r['corpus_entry'].get('id','')} | "
              f"{r['corpus_entry'].get('典型问题','')[:40]}", file=sys.stderr)


if __name__ == "__main__":
    main()
