# -*- coding: utf-8 -*-
"""
合同审查 RAG 知识检索模块 v2.4 — 本地向量库 + PKULaw北大法宝双引擎

🆕 v2.4: PKULaw MCP 融合管道
  - enrich_with_pkulaw()  — PKULaw结果摄入+向量化存储+融合检索
  - build_pkulaw_context() — 构建带pkulaw.com可追溯链接的审查引用

功能：
  search_laws(query)           — 检索相关法条（lawyer_laws）
  search_cases(query)          — 检索类案（lawyer_cases）
  search_compliance(query)     — 检索合规知识（lawyer_knowledge 企业合规）
  search_governance(query)     — 检索公司治理知识（lawyer_knowledge 公司治理）
  search_all(query)            — 综合检索（跨三库）
  analyze_clause_risks(clause) — 分析特定合同条款的法律风险
  clause_best_practice(type)   — 检索特定合同类型的条款最佳实践
  🆕 enrich_with_pkulaw(laws, cases, risk_kw, clause) — PKULaw双引擎融合检索
  🆕 build_pkulaw_context(enrich) — 构建可追溯审查引用上下文

用法:
  python contract_review_rag.py search "违约金 过高 调减"
  python contract_review_rag.py clause "违约责任条款 赔偿上限 免责"
  python contract_review_rag.py best-practice "买卖合同"
"""

import sys
import os
import json
from typing import List, Dict, Optional

# 确保能找到 rag_engine
sys.path.insert(0, r"D:\律师工作\_meta\rag_engine")

try:
    from rag_engine import get_rag
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    print("[WARN] RAG引擎不可用，请检查 rag_engine.py 路径")


# ============================================================
# 合同条款 ↔ 法律领域映射表
# ============================================================

CLAUSE_DOMAIN_MAP = {
    "违约责任": {
        "laws": "民法典 合同编 违约责任 违约金 损害赔偿",
        "cases": "合同纠纷 违约金过高 违约认定",
        "compliance": "反腐败与反商业贿赂 合规管理",
        "governance": "关联交易 信息披露",
    },
    "付款条款": {
        "laws": "民法典 合同编 价款支付 履行期限",
        "cases": "合同纠纷 货款支付 逾期付款",
        "compliance": "税务合规 反洗钱",
        "governance": "关联交易",
    },
    "保密条款": {
        "laws": "民法典 合同编 保密义务 反不正当竞争法 商业秘密",
        "cases": "侵害商业秘密 竞业限制 保密协议",
        "compliance": "知识产权合规 数据合规",
        "governance": "董监高义务 竞业禁止",
    },
    "知识产权": {
        "laws": "著作权法 专利法 商标法 反不正当竞争法 商业秘密",
        "cases": "知识产权侵权 权属纠纷 许可合同纠纷",
        "compliance": "知识产权合规 开源合规",
        "governance": "股东出资 知识产权评估",
    },
    "竞业限制": {
        "laws": "劳动合同法 竞业限制 民法典 合同编",
        "cases": "劳动争议 竞业限制 侵害商业秘密",
        "compliance": "劳动用工合规 知识产权合规",
        "governance": "董监高义务 竞业禁止 忠实义务",
    },
    "解除条款": {
        "laws": "民法典 合同编 合同解除 法定解除 约定解除权",
        "cases": "合同解除纠纷 解除权行使 解除后果",
        "compliance": "合规管理体系建设",
        "governance": "公司决议 公司僵局",
    },
    "争议解决": {
        "laws": "民事诉讼法 仲裁法 协议管辖 仲裁条款",
        "cases": "管辖异议 仲裁协议效力 执行",
        "compliance": "跨境经营合规 跨境争议解决",
        "governance": "公司治理纠纷解决",
    },
    "担保条款": {
        "laws": "民法典 担保制度 保证 抵押 质押 公司担保",
        "cases": "担保合同纠纷 越权担保 担保无效",
        "compliance": "证券与金融合规",
        "governance": "公司决议 对外担保 关联交易",
    },
    "不可抗力": {
        "laws": "民法典 合同编 不可抗力 情势变更 合同履行",
        "cases": "合同纠纷 不可抗力认定 免责",
        "compliance": "合规风险应对",
        "governance": "公司僵局 退出机制",
    },
    "送达条款": {
        "laws": "民事诉讼法 送达 电子送达",
        "cases": "送达程序 缺席判决 再审",
        "compliance": "合规管理体系建设",
        "governance": "信息披露与透明度",
    },
    "数据保护": {
        "laws": "个人信息保护法 数据安全法 网络安全法",
        "cases": "个人信息侵权 数据泄露 数据出境",
        "compliance": "数据合规与个人信息保护",
        "governance": "ESG 跨境治理",
    },
    "反腐败": {
        "laws": "刑法 反不正当竞争法",
        "cases": "商业贿赂 职务侵占 单位行贿",
        "compliance": "反腐败与反商业贿赂 刑事合规",
        "governance": "董监高义务 忠实义务 关联交易",
    },
    "环境条款": {
        "laws": "环境保护法 民法典 侵权责任 环境侵权",
        "cases": "环境污染 环境侵权 行政处罚",
        "compliance": "环境合规 ESG合规",
        "governance": "ESG 社会责任",
    },
    "安全条款": {
        "laws": "安全生产法 民法典 侵权责任",
        "cases": "安全事故 人身损害赔偿 行政处罚",
        "compliance": "安全生产合规",
        "governance": "ESG",
    },
}


class ContractReviewRAG:
    """合同审查专用 RAG 检索器"""

    def __init__(self):
        self.rag = None
        self._initialized = False

    def initialize(self) -> bool:
        if self._initialized:
            return True
        if not RAG_AVAILABLE:
            return False
        try:
            self.rag = get_rag()
            self._initialized = self.rag.is_ready
        except Exception as e:
            print(f"[RAG] 初始化失败: {e}")
        return self._initialized

    def _merge_results(self, *result_lists, top_k: int = 5) -> List[Dict]:
        """合并多个搜索结果，按相似度排序"""
        all_results = []
        seen = set()
        for results in result_lists:
            for r in results:
                if r.get("id") not in seen:
                    seen.add(r["id"])
                    all_results.append(r)
        return sorted(all_results, key=lambda x: x.get("similarity", 0), reverse=True)[:top_k]

    # ── 基础检索 ──

    def search_laws(self, query: str, top_k: int = 5) -> List[Dict]:
        """检索相关法律法规"""
        if not self._initialized:
            return []
        return self.rag.search_laws(query, top_k=top_k)

    def search_cases(self, query: str, top_k: int = 5) -> List[Dict]:
        """检索相关类案"""
        if not self._initialized:
            return []
        return self.rag.search_cases(query, top_k=top_k)

    def search_compliance(self, query: str, top_k: int = 5) -> List[Dict]:
        """检索企业合规知识"""
        if not self._initialized:
            return []
        return self.rag.search_knowledge(query, category_filter="企业合规", top_k=top_k)

    def search_governance(self, query: str, top_k: int = 5) -> List[Dict]:
        """检索公司治理知识"""
        if not self._initialized:
            return []
        return self.rag.search_knowledge(query, category_filter="公司治理", top_k=top_k)

    def search_knowledge(self, query: str, top_k: int = 8) -> List[Dict]:
        """综合搜索知识库（公司治理+企业合规）"""
        if not self._initialized:
            return []
        results = self.rag.search_knowledge(query, top_k=top_k)
        return results

    def search_all(self, query: str, top_k: int = 3) -> Dict[str, List[Dict]]:
        """综合检索（类案+法规+知识三库并行）"""
        if not self._initialized:
            return {}
        return self.rag.multi_search(query, top_k=top_k)

    # ── 合同审查专用 ──

    def analyze_clause_risks(self, clause_type: str, clause_text: str = "",
                              top_k: int = 8) -> Dict:
        """分析特定合同条款类型的法律风险

        Args:
            clause_type: 条款类型（如"违约责任""保密条款""竞业限制"等）
            clause_text: 可选的条款原文，用于更精准的语义匹配

        Returns:
            {
                "clause_type": "...",
                "relevant_laws": [...],
                "relevant_cases": [...],
                "relevant_compliance": [...],
                "relevant_governance": [...],
                "risk_summary": "综合分析摘要"
            }
        """
        if not self._initialized:
            return {"error": "RAG引擎不可用"}

        # 获取条款对应的检索方向
        domain = CLAUSE_DOMAIN_MAP.get(clause_type, {
            "laws": f"民法典 合同 {clause_type}",
            "cases": f"合同纠纷 {clause_type}",
            "compliance": "合规管理体系建设",
            "governance": "董监高义务与责任",
        })

        # 构建查询文本
        base_query = f"{clause_type} 合同 {clause_text[:200] if clause_text else ''}"

        # 并行检索
        laws = self.search_laws(f"{base_query} {domain['laws']}", top_k=top_k)
        cases = self.search_cases(f"{base_query} {domain['cases']}", top_k=top_k)
        compliance = self.search_compliance(f"{base_query} {domain['compliance']}", top_k=5)
        governance = self.search_governance(f"{base_query} {domain['governance']}", top_k=5)

        return {
            "clause_type": clause_type,
            "relevant_laws": [{
                "content": r["content"][:300],
                "similarity": r["similarity"],
                "metadata": r["metadata"]
            } for r in laws],
            "relevant_cases": [{
                "content": r["content"][:300],
                "similarity": r["similarity"],
                "metadata": r["metadata"]
            } for r in cases],
            "relevant_compliance": [{
                "content": r["content"][:300],
                "similarity": r["similarity"],
                "metadata": r["metadata"]
            } for r in compliance],
            "relevant_governance": [{
                "content": r["content"][:300],
                "similarity": r["similarity"],
                "metadata": r["metadata"]
            } for r in governance],
        }

    def clause_best_practice(self, contract_type: str, clause_type: str = "",
                              top_k: int = 8) -> Dict:
        """检索特定合同类型的条款最佳实践

        Args:
            contract_type: 合同类型（如"买卖合同""服务合同""租赁合同"等）
            clause_type: 可选的具体条款类型
        """
        if not self._initialized:
            return {"error": "RAG引擎不可用"}

        query = f"{contract_type} {clause_type} 合同条款 审查 风险 要点"
        if not clause_type:
            query = f"{contract_type} 合同审查 风险要点 常见纠纷"

        # 综合搜索
        all_results = self.search_all(query, top_k=top_k)

        return {
            "contract_type": contract_type,
            "clause_type": clause_type or "通用",
            "query": query,
            "laws": [{"content": r["content"][:250], "similarity": r["similarity"]}
                     for r in all_results.get("laws", [])[:5]],
            "cases": [{"content": r["content"][:250], "similarity": r["similarity"]}
                      for r in all_results.get("cases", [])[:3]],
            "knowledge": [{"content": r["content"][:250], "similarity": r["similarity"],
                           "category": r["metadata"].get("category", "")}
                          for r in all_results.get("knowledge", [])[:5]],
        }


    # ── 🆕 v2.4 PKULaw 融合管道 ──

    def enrich_with_pkulaw(self, pkulaw_laws: List[Dict] = None,
                            pkulaw_cases: List[Dict] = None,
                            risk_keywords: str = "",
                            clause_type: str = "",
                            top_k: int = 8) -> Dict:
        """PKULaw MCP 结果摄入 + 向量化存储 + 双引擎融合检索

        这是合同审查中每个风险发现后的标准调用方法。
        执行管道：PKULaw实时结果 → 标准化 → 向量化存储 → 融合检索

        Args:
            pkulaw_laws: PKULaw MCP search_article/get_article 返回的法条列表（原始格式）
            pkulaw_cases: PKULaw MCP search_case/get_case_list 返回的案例列表（原始格式）
            risk_keywords: 风险关键词（用于检索）
            clause_type: 条款类型
            top_k: 每库检索数量

        Returns:
            {
                "laws": [...],          # 融合后的法条（PKULaw+本地）
                "cases": [...],         # 融合后的案例
                "knowledge": [...],     # 相关知识
                "stored": {"laws": 3, "cases": 2},  # 本次摄入数量
                "sources": {...},       # 来源统计
                "citation": "🧠 PKULaw+RAG 参考:\n  ..."  # 格式化引用文本
            }
        """
        # 延迟导入PKULaw模块
        try:
            from contract_review_pkulaw import get_pkulaw_enricher
            enricher = get_pkulaw_enricher()
        except ImportError:
            # PKULaw模块不可用，回退到纯本地RAG
            return self._fallback_enrich(risk_keywords, clause_type, top_k)

        # Step 1: 摄入PKULaw结果到向量库
        stored = enricher.ingest_pkulaw_result(
            laws=pkulaw_laws or [],
            cases=pkulaw_cases or [],
            batch_id=f"cr_{hash(risk_keywords) & 0xFFFF:04x}",
        )

        # Step 2: 双引擎融合检索
        enrichment = enricher.enrich_risk(risk_keywords, clause_type, top_k)

        # Step 3: 构建引用上下文
        citation_ctx = enricher.build_citation_context(enrichment, risk_keywords)
        citation_text = enricher.build_irar_citation(citation_ctx)

        return {
            "laws": enrichment.get("laws", []),
            "cases": enrichment.get("cases", []),
            "knowledge": enrichment.get("knowledge", []),
            "stored": stored,
            "sources": enrichment.get("sources", {}),
            "citation": citation_text,
            "citation_ctx": citation_ctx,
        }

    def _fallback_enrich(self, risk_keywords: str, clause_type: str,
                          top_k: int) -> Dict:
        """PKULaw不可用时的纯本地RAG回退"""
        result = {
            "laws": [],
            "cases": [],
            "knowledge": [],
            "stored": {"laws": 0, "cases": 0},
            "sources": {"pkulaw_laws": 0, "pkulaw_cases": 0,
                        "local_laws": 0, "local_cases": 0, "local_knowledge": 0},
            "citation": "",
            "citation_ctx": {},
        }

        if not self._initialized:
            return result

        # 本地检全
        laws = self.search_laws(risk_keywords, top_k)
        cases = self.search_cases(risk_keywords, top_k)
        knowledge = self.search_knowledge(risk_keywords, top_k=5)

        for law in laws:
            law["_priority"] = "local"
            law["_weight"] = 1.0
        for case in cases:
            case["_priority"] = "local"
            case["_weight"] = 1.0
        for k in knowledge:
            k["_priority"] = "local"

        result["laws"] = laws
        result["cases"] = cases
        result["knowledge"] = knowledge
        result["sources"]["local_laws"] = len(laws)
        result["sources"]["local_cases"] = len(cases)
        result["sources"]["local_knowledge"] = len(knowledge)

        if laws:
            top_law = laws[0]
            result["citation"] = (
                f"🧠 本地RAG参考:\n"
                f"  ├─ 法条: {top_law.get('content', '')[:120]}\n"
                f"  ├─ 类案: {cases[0].get('content', '')[:120] if cases else '无'}\n"
                f"  └─ 知识: {knowledge[0].get('content', '')[:80] if knowledge else '无'}"
            )

        return result

    def build_pkulaw_context(self, enrichment_result: Dict,
                              risk_name: str = "") -> str:
        """从PKULaw融合结果构建审查引用上下文（便捷方法）

        直接返回格式化的引用文本，可直接嵌入IRAC审查输出。
        """
        citation = enrichment_result.get("citation", "")
        if not citation:
            # 回退：手动构建
            laws = enrichment_result.get("laws", [])
            cases = enrichment_result.get("cases", [])
            parts = ["🧠 参考来源:"]
            for i, law in enumerate(laws[:3]):
                src = "PKULaw" if law.get("_priority") == "pkulaw" else "本地"
                parts.append(f"  ├─ 📜 {src}: {law.get('content', '')[:100]}")
            for i, case in enumerate(cases[:2]):
                src = "PKULaw" if case.get("_priority") == "pkulaw" else "本地"
                parts.append(f"  ├─ ⚖️ {src}: {case.get('content', '')[:100]}")
            citation = "\n".join(parts)
        return citation


# ============================================================
# 便捷接口
# ============================================================

_cr_rag_instance = None

def get_cr_rag() -> ContractReviewRAG:
    global _cr_rag_instance
    if _cr_rag_instance is None:
        _cr_rag_instance = ContractReviewRAG()
        _cr_rag_instance.initialize()
    return _cr_rag_instance


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    cr = get_cr_rag()

    if not cr._initialized:
        print("RAG引擎不可用")
        sys.exit(1)

    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""

    if cmd == "help":
        print("合同审查 RAG 查询工具")
        print("  python contract_review_rag.py search <查询文本>")
        print("  python contract_review_rag.py clause <条款类型> [条款原文]")
        print("  python contract_review_rag.py best-practice <合同类型> [条款类型]")
        print("  python contract_review_rag.py all <查询文本>")

    elif cmd == "search":
        if not query:
            print("请提供查询文本")
            sys.exit(1)
        results = cr.search_all(query)
        print(json.dumps({
            "laws": [r["content"][:200] for r in results.get("laws", [])[:3]],
            "cases": [r["content"][:200] for r in results.get("cases", [])[:3]],
            "knowledge": [r["content"][:200] for r in results.get("knowledge", [])[:3]],
        }, ensure_ascii=False, indent=2))

    elif cmd == "clause":
        clause_type = sys.argv[2] if len(sys.argv) > 2 else "违约责任"
        clause_text = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else ""
        result = cr.analyze_clause_risks(clause_type, clause_text)
        # 简化输出
        print(f"=== {clause_type} 风险分析 ===")
        print(f"相关法条: {len(result.get('relevant_laws', []))} 条")
        for r in result.get("relevant_laws", [])[:3]:
            print(f"  [{r['similarity']:.0%}] {r['content'][:120]}")
        print(f"相关类案: {len(result.get('relevant_cases', []))} 条")
        for r in result.get("relevant_cases", [])[:2]:
            print(f"  [{r['similarity']:.0%}] {r['content'][:120]}")
        print(f"相关合规: {len(result.get('relevant_compliance', []))} 条")
        print(f"相关治理: {len(result.get('relevant_governance', []))} 条")

    elif cmd == "best-practice":
        contract_type = sys.argv[2] if len(sys.argv) > 2 else "买卖合同"
        clause_type = sys.argv[3] if len(sys.argv) > 3 else ""
        result = cr.clause_best_practice(contract_type, clause_type)
        print(f"=== {contract_type} {clause_type or '通用'} 实践经验 ===")
        for r in result.get("laws", [])[:3]:
            print(f"  [法条 {r['similarity']:.0%}] {r['content'][:100]}")
        for r in result.get("knowledge", [])[:3]:
            print(f"  [知识:{r['category']} {r['similarity']:.0%}] {r['content'][:100]}")

    elif cmd == "all":
        if not query:
            print("请提供查询文本")
            sys.exit(1)
        result = cr.search_all(query)
        print(json.dumps({
            "laws_count": len(result.get("laws", [])),
            "cases_count": len(result.get("cases", [])),
            "knowledge_count": len(result.get("knowledge", [])),
        }, ensure_ascii=False))

    elif cmd == "list-clauses":
        print("支持的条款类型:")
        for clause, domain in CLAUSE_DOMAIN_MAP.items():
            print(f"  {clause} → 法律:{domain['laws'][:40]}...")
