#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""财税技能矩阵 · 智能路由器（仅标准库，无第三方依赖）。

设计目标（对应需求「智能化调用矩阵相关技能」）：
- 给定用户自然语言查询，按 matrix.json 中每个技能的主题(topics)/关键词(keywords)
  做子串打分匹配，返回最相关的技能排序列表（含命中词与分值），用于「自动归口」
  到最合适的专精技能，避免单体技能包过大却覆盖不深。
- 提供 associations(slug) 返回该技能的关联技能，支撑跨专题「智能化关联支撑」交叉入口。
- 纯离线、确定性、可单测；供技能在对话中决策「应加载哪一个矩阵技能」。

典型用法：
    r = MatrixRouter()
    hits = r.route("企业分立怎么交税")
    # -> [{"slug": "tax-restructuring", "score": 4, "matched": ["企业分立"]}, ...]
    r.associations("tax-restructuring")
    # -> ["tax-equity-governance", "tax-incentives", "tax-compliance-dispute", "tax-policy-knowledge"]
"""
import os
import json

HERE = os.path.dirname(os.path.abspath(__file__))


class MatrixRouter:
    def __init__(self, manifest_path=None):
        p = manifest_path or os.path.join(HERE, "matrix.json")
        if not os.path.isfile(p):
            raise FileNotFoundError(f"找不到矩阵清单: {p}")
        with open(p, "r", encoding="utf-8") as f:
            self.m = json.load(f)
        self.by_slug = {s["slug"]: s for s in self.m["skills"]}
        # 预建 (slug, [keywords+topics]) 索引；长词在前优先匹配
        self._index = []
        for s in self.m["skills"]:
            kws = list(s.get("keywords", [])) + list(s.get("topics", []))
            kws = sorted(set(kws), key=len, reverse=True)
            self._index.append((s["slug"], kws))

    def route(self, query, top_n=3):
        """返回与查询最相关的技能列表（按分值降序）。"""
        q = (query or "").lower()
        scored = []
        for slug, kws in self._index:
            matched = []
            score = 0
            for kw in kws:
                k = kw.lower()
                if k and k in q:
                    score += len(k)  # 长词权重大，更具体的主题胜出
                    matched.append(kw)
            if score > 0:
                scored.append({"slug": slug, "score": score, "matched": matched})
        scored.sort(key=lambda x: -x["score"])
        return scored[:top_n]

    def best(self, query):
        """返回最相关技能的 slug；无匹配返回 None。"""
        r = self.route(query, top_n=1)
        return r[0]["slug"] if r else None

    def associations(self, slug):
        """返回该技能的关联技能 slug 列表。"""
        return list(self.m.get("associations", {}).get(slug, []))

    def describe(self, slug):
        """返回技能名称；未知返回 None。"""
        s = self.by_slug.get(slug)
        return s["name"] if s else None

    def all_slugs(self):
        return [s["slug"] for s in self.m["skills"]]


if __name__ == "__main__":
    import sys
    r = MatrixRouter()
    q = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "企业分立怎么交税"
    print(f"查询: {q}")
    for hit in r.route(q):
        print(f"  -> {hit['slug']} (score={hit['score']}, matched={hit['matched']})")
