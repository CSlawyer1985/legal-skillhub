# -*- coding: utf-8 -*-
"""
合同审查 PKULaw 北大法宝集成模块 v1.0
===========================================
将北大法宝 MCP 检索结果与本地 ChromaDB 向量库融合，
实现「PKULaw权威检索 → 向量化存储 → RAG语义增强」三级管道。

功能：
  store_law_articles(articles)     — 将PKULaw法条结果存入ChromaDB
  store_cases(cases)                — 将PKULaw案例结果存入ChromaDB
  enrich_risk_analysis(risk_item)   — 对单条风险执行PKULaw+RAG融合检索
  build_enrichment_context(risks)   — 批量构建审查增强上下文
  ingest_pkulaw_batch(batch)        — 批量摄入PKULaw结果到向量库
  get_storage_stats()               — 获取PKULaw向量存储统计

合同审查工作流中的调用顺序：
  1. 风险发现 → pkulaw_result = mcp__pkulaw__search_article(...)
  2. store_law_articles(pkulaw_result)  → 存入ChromaDB
  3. enrich_risk_analysis(risk_item)     → PKULaw+RAG融合
  4. 输出带 pkulaw.com 可追溯链接的审查结论
"""

import sys
import os
import json
import hashlib
import time
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path

# 确保能找到 rag_engine
sys.path.insert(0, r"D:\律师工作\_meta\rag_engine")

try:
    from rag_engine import get_rag
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

try:
    from contract_review_rag import get_cr_rag
    CR_RAG_AVAILABLE = True
except ImportError:
    CR_RAG_AVAILABLE = False


# ============================================================
# 配置
# ============================================================

CHROMADB_PATH = Path(r"D:\律师工作\_meta\rag_engine\indexes")

# PKULaw 专用 ChromaDB collection 名称
PKULAW_LAWS_COLLECTION = "pkulaw_laws"       # 北大法宝法条
PKULAW_CASES_COLLECTION = "pkulaw_cases"     # 北大法宝案例

# PKULaw 来源权重（高于本地库）
PKULAW_SOURCE_WEIGHT = 1.5   # PKULaw来源加权系数
LOCAL_SOURCE_WEIGHT = 1.0    # 本地来源加权系数

# 批量摄入时每批最大条数
MAX_BATCH_SIZE = 20

# 法条权威性排序（PKULaw返回的效力级别映射）
EFFECTIVENESS_RANK = {
    "法律": 10,
    "行政法规": 8,
    "司法解释": 7,
    "部门规章": 6,
    "地方性法规": 4,
    "其他": 2,
}


# ============================================================
# PKULaw 结果标准化
# ============================================================

def normalize_pkulaw_article(raw_article: Dict) -> Dict:
    """将北大法宝 MCP 返回的法条结果标准化为统一格式

    输入格式（来自 mcp__pkulaw__search_article / get_article）：
      {"title": "中华人民共和国民法典",
       "number": "第五百八十五条",
       "article": "当事人可以约定...",
       "url": "https://www.pkulaw.com/...",
       "timeliness": "现行有效", ...}

    输出格式：
      {"id": "pkulaw_law_<hash>",
       "source": "pkulaw",
       "type": "law_article",
       "title": "民法典",
       "article_number": "第585条",
       "content": "当事人可以约定...",
       "url": "https://www.pkulaw.com/...",
       "effectiveness": "现行有效",
       "effectiveness_rank": 10,
       "ingested_at": "2026-06-17T16:00:00"}
    """
    title = raw_article.get("title", "").replace("中华人民共和国", "").strip()
    number = raw_article.get("number", "")
    content = raw_article.get("article", "") or raw_article.get("content", "")
    url = raw_article.get("url", "")
    timeliness = raw_article.get("timeliness", "现行有效")

    # 计算效力级别
    law_type = raw_article.get("law_type", "") or raw_article.get("effectiveness", "")
    eff_rank = EFFECTIVENESS_RANK.get(law_type, 2)

    # 去重ID
    unique_str = f"{title}_{number}_{content[:100]}"
    doc_id = f"pkulaw_law_{hashlib.md5(unique_str.encode()).hexdigest()[:12]}"

    # 为ChromaDB准备的可检索文本
    searchable_text = f"【{title}】第{number}条 {content}"

    return {
        "id": doc_id,
        "source": "pkulaw",
        "type": "law_article",
        "title": title,
        "article_number": number,
        "content": content,
        "searchable_text": searchable_text,
        "url": url,
        "effectiveness": timeliness,
        "effectiveness_rank": eff_rank,
        "ingested_at": datetime.now().isoformat(),
    }


def normalize_pkulaw_case(raw_case: Dict) -> Dict:
    """将北大法宝 MCP 返回的案例结果标准化

    输入格式（来自 mcp__pkulaw__search_case / get_case_list）：
      {"case_number": "(2022)京0105民初12345号",
       "court_name": "北京市朝阳区人民法院",
       "decision_date": "2022-06-15",
       "cause_of_action": "买卖合同纠纷",
       "content": "...",
       "ascertain": "...",
       "controversial_focus": "...",
       "identified": "...",
       "referee_basis": "...",
       "referee_result": "...",
       "case_grade": "普通案例",
       "url": "https://www.pkulaw.com/...", ...}

    输出格式：
      {"id": "pkulaw_case_<hash>",
       "source": "pkulaw",
       "type": "case",
       "case_number": "(2022)京0105民初12345号",
       "court": "北京市朝阳区人民法院",
       "decision_date": "2022-06-15",
       "cause": "买卖合同纠纷",
       "content": "...",
       "ascertain": "...",
       "controversial_focus": "...",
       "identified": "...",
       "referee_basis": "...",
       "referee_result": "...",
       "case_grade": "普通案例",
       "url": "https://www.pkulaw.com/...",
       "ingested_at": "2026-06-17T16:00:00"}
    """
    case_number = raw_case.get("case_number", "")
    court = raw_case.get("court_name", "")
    content = raw_case.get("content", "") or raw_case.get("summary", "")
    url = raw_case.get("url", "")
    case_grade = raw_case.get("case_grade", "普通案例") or raw_case.get("CaseGrade", "普通案例")

    # 深度字段
    ascertain = raw_case.get("ascertain", "") or raw_case.get("Ascertain", "")
    controversy = raw_case.get("controversial_focus", "") or raw_case.get("ControversialFocus", "")
    identified = raw_case.get("identified", "") or raw_case.get("Identified", "")
    referee_basis = raw_case.get("referee_basis", "") or raw_case.get("RefereeBasis", "")
    referee_result = raw_case.get("referee_result", "") or raw_case.get("RefereeResult", "")

    unique_str = f"{case_number}_{content[:80]}"
    doc_id = f"pkulaw_case_{hashlib.md5(unique_str.encode()).hexdigest()[:12]}"

    # 为ChromaDB准备的可检索文本（合并关键信息）
    cause = raw_case.get("cause_of_action", "") or raw_case.get("cause", "")
    searchable_text = f"【{case_number}】{court} {cause} {content[:500]}"

    return {
        "id": doc_id,
        "source": "pkulaw",
        "type": "case",
        "case_number": case_number,
        "court": court,
        "decision_date": raw_case.get("decision_date", ""),
        "cause": cause,
        "content": content,
        "ascertain": ascertain,
        "controversial_focus": controversy,
        "identified": identified,
        "referee_basis": referee_basis,
        "referee_result": referee_result,
        "case_grade": case_grade,
        "case_grade_rank": {"指导案例": 3, "公报案例": 2, "普通案例": 1}.get(case_grade, 1),
        "searchable_text": searchable_text,
        "url": url,
        "ingested_at": datetime.now().isoformat(),
    }


# ============================================================
# ChromaDB 存储引擎
# ============================================================

class PKULawVectorStore:
    """北大法宝结果 → ChromaDB 向量存储引擎"""

    def __init__(self):
        self.chroma_client = None
        self.law_collection = None
        self.case_collection = None
        self._initialized = False

    def initialize(self) -> bool:
        if self._initialized:
            return True
        try:
            import chromadb
            from chromadb.config import Settings

            self.chroma_client = chromadb.PersistentClient(
                path=str(CHROMADB_PATH),
                settings=Settings(anonymized_telemetry=False),
            )

            # 使用RAG引擎的embedding函数（如果可用）
            embedding_fn = None
            if RAG_AVAILABLE:
                try:
                    rag = get_rag()
                    if rag.embedding_fn:
                        embedding_fn = self._wrap_embed_fn(rag.embedding_fn)
                except Exception:
                    pass

            self.law_collection = self.chroma_client.get_or_create_collection(
                name=PKULAW_LAWS_COLLECTION,
                metadata={
                    "description": "北大法宝法条向量库 (PKULaw MCP导入)",
                    "hnsw:space": "cosine",
                    "source": "pkulaw_mcp",
                },
                embedding_function=embedding_fn,
            )
            self.case_collection = self.chroma_client.get_or_create_collection(
                name=PKULAW_CASES_COLLECTION,
                metadata={
                    "description": "北大法宝案例向量库 (PKULaw MCP导入)",
                    "hnsw:space": "cosine",
                    "source": "pkulaw_mcp",
                },
                embedding_function=embedding_fn,
            )
            self._initialized = True
            return True
        except Exception as e:
            print(f"[PKULawStore] 初始化失败: {e}")
            return False

    def _wrap_embed_fn(self, sentence_transformer_model):
        """将 sentence-transformers 模型包装为 ChromaDB embedding function"""
        model = sentence_transformer_model

        class EmbeddingFn:
            def __call__(self, input):
                return model.encode(input).tolist()

        return EmbeddingFn()

    def store_laws(self, articles: List[Dict], batch_id: str = "") -> int:
        """存储法条到 ChromaDB

        Args:
            articles: 标准化后的法条列表
            batch_id: 批次标识（如审查任务ID），用于追踪

        Returns:
            实际存储条数
        """
        if not self._initialized or not articles:
            return 0

        stored = 0
        for i in range(0, len(articles), MAX_BATCH_SIZE):
            batch = articles[i : i + MAX_BATCH_SIZE]
            ids = []
            documents = []
            metadatas = []

            for art in batch:
                art_id = art["id"]
                # 跳过已存在的
                existing = self.law_collection.get(ids=[art_id])
                if existing and existing["ids"]:
                    continue

                ids.append(art_id)
                documents.append(art["searchable_text"])
                metadatas.append({
                    "title": art["title"],
                    "article_number": art["article_number"],
                    "url": art["url"],
                    "effectiveness": art["effectiveness"],
                    "effectiveness_rank": art["effectiveness_rank"],
                    "source": "pkulaw",
                    "batch_id": batch_id,
                    "ingested_at": art["ingested_at"],
                })

            if ids:
                try:
                    self.law_collection.add(
                        ids=ids,
                        documents=documents,
                        metadatas=metadatas,
                    )
                    stored += len(ids)
                except Exception as e:
                    print(f"[PKULawStore] 存储法条失败: {e}")

        return stored

    def store_cases(self, cases: List[Dict], batch_id: str = "") -> int:
        """存储案例到 ChromaDB

        Args:
            cases: 标准化后的案例列表
            batch_id: 批次标识

        Returns:
            实际存储条数
        """
        if not self._initialized or not cases:
            return 0

        stored = 0
        for i in range(0, len(cases), MAX_BATCH_SIZE):
            batch = cases[i : i + MAX_BATCH_SIZE]
            ids = []
            documents = []
            metadatas = []

            for c in batch:
                case_id = c["id"]
                existing = self.case_collection.get(ids=[case_id])
                if existing and existing["ids"]:
                    continue

                ids.append(case_id)
                documents.append(c["searchable_text"])
                metadatas.append({
                    "case_number": c["case_number"],
                    "court": c["court"],
                    "decision_date": c["decision_date"],
                    "cause": c["cause"],
                    "case_grade": c["case_grade"],
                    "case_grade_rank": c["case_grade_rank"],
                    "url": c["url"],
                    "source": "pkulaw",
                    "batch_id": batch_id,
                    "ascertain": c["ascertain"][:200],
                    "controversial_focus": c["controversial_focus"][:200],
                    "identified": c["identified"][:200],
                    "referee_basis": c["referee_basis"][:200],
                    "referee_result": c["referee_result"][:200],
                    "ingested_at": c["ingested_at"],
                })

            if ids:
                try:
                    self.case_collection.add(
                        ids=ids,
                        documents=documents,
                        metadatas=metadatas,
                    )
                    stored += len(ids)
                except Exception as e:
                    print(f"[PKULawStore] 存储案例失败: {e}")

        return stored

    def search_pkulaw_laws(self, query: str, top_k: int = 5) -> List[Dict]:
        """从PKULaw向量库中检索法条"""
        if not self._initialized:
            return []
        try:
            results = self.law_collection.query(
                query_texts=[query],
                n_results=top_k,
            )
            return self._format_search_results(results, "law")
        except Exception as e:
            print(f"[PKULawStore] 法条检索失败: {e}")
            return []

    def search_pkulaw_cases(self, query: str, top_k: int = 5) -> List[Dict]:
        """从PKULaw向量库中检索案例"""
        if not self._initialized:
            return []
        try:
            results = self.case_collection.query(
                query_texts=[query],
                n_results=top_k,
            )
            return self._format_search_results(results, "case")
        except Exception as e:
            print(f"[PKULawStore] 案例检索失败: {e}")
            return []

    def _format_search_results(self, raw_results: Dict, result_type: str) -> List[Dict]:
        """将ChromaDB查询结果格式化为统一结构"""
        formatted = []
        if not raw_results or "ids" not in raw_results or not raw_results["ids"]:
            return formatted

        ids_list = raw_results["ids"][0] if raw_results["ids"] else []
        distances = raw_results.get("distances", [[]])[0]
        metadatas = raw_results.get("metadatas", [[]])[0]
        documents = raw_results.get("documents", [[]])[0]

        for i, doc_id in enumerate(ids_list):
            similarity = 1 - distances[i] if i < len(distances) else 0
            formatted.append({
                "id": doc_id,
                "type": result_type,
                "similarity": round(similarity, 4),
                "content": documents[i] if i < len(documents) else "",
                "metadata": metadatas[i] if i < len(metadatas) else {},
            })
        return sorted(formatted, key=lambda x: x["similarity"], reverse=True)

    def get_stats(self) -> Dict:
        """获取向量存储统计"""
        if not self._initialized:
            return {"initialized": False}
        try:
            return {
                "initialized": True,
                "pkulaw_laws_count": self.law_collection.count(),
                "pkulaw_cases_count": self.case_collection.count(),
            }
        except Exception:
            return {"initialized": True, "error": "无法获取统计"}


# ============================================================
# PKULaw + RAG 融合引擎
# ============================================================

class PKULawEnricher:
    """PKULaw + RAG 融合检索引擎

    策略：
      1. PKULaw MCP 实时检索 → 获取权威法条/案例（带 pkulaw.com 可追溯链接）
      2. 检索结果自动存入 ChromaDB 向量库（积累知识资产）
      3. 从 PKULaw 向量库 + 本地 RAG 向量库并行检索
      4. 按权威性 + 相似度排序合并
      5. 输出标注来源层级（PKULaw > 本地）
    """

    def __init__(self):
        self.pkustore = PKULawVectorStore()
        self.cr_rag = None
        self._initialized = False

    def initialize(self) -> bool:
        if self._initialized:
            return True
        store_ok = self.pkustore.initialize()
        if CR_RAG_AVAILABLE:
            try:
                self.cr_rag = get_cr_rag()
            except Exception:
                pass
        self._initialized = store_ok
        return self._initialized

    def ingest_pkulaw_result(self,
                              laws: List[Dict] = None,
                              cases: List[Dict] = None,
                              batch_id: str = "") -> Dict:
        """摄入PKULaw MCP检索结果：标准化 → 向量化 → 存入ChromaDB

        Args:
            laws: PKULaw MCP返回的原始法条列表
            cases: PKULaw MCP返回的原始案例列表
            batch_id: 批次标识

        Returns:
            {"laws_stored": 3, "cases_stored": 2}
        """
        result = {"laws_stored": 0, "cases_stored": 0}

        if laws:
            normalized = [normalize_pkulaw_article(la) for la in laws]
            result["laws_stored"] = self.pkustore.store_laws(normalized, batch_id)

        if cases:
            normalized = [normalize_pkulaw_case(ca) for ca in cases]
            result["cases_stored"] = self.pkustore.store_cases(normalized, batch_id)

        return result

    def enrich_risk(self, risk_keywords: str, clause_type: str = "",
                    top_k: int = 8) -> Dict:
        """对单条合同风险进行PKULaw+RAG融合检索

        检索管道：
          1. PKULaw向量库检索（已存储的法条+案例）
          2. 本地RAG向量库检索（lawyer_laws + lawyer_cases + lawyer_knowledge）
          3. 按 (权威性权重 × 相似度) 排序合并
          4. 去重（同一条文可能同时出现在PKULaw和本地库）

        Args:
            risk_keywords: 风险关键词（如"违约金 过高 调减"）
            clause_type: 条款类型（用于知识库定向检索）
            top_k: 每库检索数量

        Returns:
            {
                "laws": [...],      # 排序后的法条（PKULaw优先）
                "cases": [...],     # 排序后的案例
                "knowledge": [...], # 相关知识
                "sources": {        # 来源统计
                    "pkulaw_laws": 3,
                    "pkulaw_cases": 2,
                    "local_laws": 5,
                    "local_cases": 3,
                }
            }
        """
        result = {
            "laws": [],
            "cases": [],
            "knowledge": [],
            "sources": {"pkulaw_laws": 0, "pkulaw_cases": 0,
                        "local_laws": 0, "local_cases": 0, "local_knowledge": 0},
        }

        # ── 1. PKULaw向量库检索 ──
        if self._initialized:
            pkulaw_laws = self.pkustore.search_pkulaw_laws(risk_keywords, top_k)
            for law in pkulaw_laws:
                law["_priority"] = "pkulaw"
                law["_weight"] = PKULAW_SOURCE_WEIGHT
            result["laws"].extend(pkulaw_laws)
            result["sources"]["pkulaw_laws"] = len(pkulaw_laws)

            pkulaw_cases = self.pkustore.search_pkulaw_cases(risk_keywords, top_k)
            for case in pkulaw_cases:
                case["_priority"] = "pkulaw"
                case["_weight"] = PKULAW_SOURCE_WEIGHT
            result["cases"].extend(pkulaw_cases)
            result["sources"]["pkulaw_cases"] = len(pkulaw_cases)

        # ── 2. 本地RAG向量库检索 ──
        if self.cr_rag and self.cr_rag._initialized:
            try:
                local_laws = self.cr_rag.search_laws(risk_keywords, top_k)
                for law in local_laws:
                    law["_priority"] = "local"
                    law["_weight"] = LOCAL_SOURCE_WEIGHT
                result["laws"].extend(local_laws)
                result["sources"]["local_laws"] = len(local_laws)

                local_cases = self.cr_rag.search_cases(risk_keywords, top_k)
                for case in local_cases:
                    case["_priority"] = "local"
                    case["_weight"] = LOCAL_SOURCE_WEIGHT
                result["cases"].extend(local_cases)
                result["sources"]["local_cases"] = len(local_cases)

                # 知识库
                if clause_type:
                    from contract_review_rag import CLAUSE_DOMAIN_MAP
                    domain = CLAUSE_DOMAIN_MAP.get(clause_type, {})
                    if domain.get("compliance"):
                        compliance = self.cr_rag.search_compliance(
                            f"{clause_type} {risk_keywords}", top_k=5)
                        for k in compliance:
                            k["_priority"] = "local"
                        result["knowledge"].extend(compliance)
                    if domain.get("governance"):
                        governance = self.cr_rag.search_governance(
                            f"{clause_type} {risk_keywords}", top_k=5)
                        for k in governance:
                            k["_priority"] = "local"
                        result["knowledge"].extend(governance)
                result["sources"]["local_knowledge"] = len(result["knowledge"])
            except Exception as e:
                print(f"[PKULawEnricher] 本地RAG检索失败: {e}")

        # ── 3. 去重 + 加权排序 ──
        result["laws"] = self._dedup_and_rank(result["laws"], "law")
        result["cases"] = self._dedup_and_rank(result["cases"], "case")

        return result

    def _dedup_and_rank(self, items: List[Dict], item_type: str) -> List[Dict]:
        """去重并按 (权重 × 相似度) 排序"""
        seen = set()
        unique = []
        for item in items:
            # 法条：按标题+条号去重；案例：按案号去重
            if item_type == "law":
                key = item.get("metadata", {}).get("title", "") + \
                      item.get("metadata", {}).get("article_number", "")
            else:
                key = item.get("metadata", {}).get("case_number", "")
            if key and key in seen:
                continue
            if key:
                seen.add(key)
            unique.append(item)

        # 按 score = weight × similarity 降序
        return sorted(unique, key=lambda x: x.get("_weight", 1.0) * x.get("similarity", 0), reverse=True)

    def build_citation_context(self, enrichment: Dict, risk_name: str = "",
                                max_items: int = 5) -> Dict:
        """从融合检索结果构建审查引用上下文

        Returns:
            {
                "risk": "违约金过高",
                "primary_law": {"text": "民法典第585条...", "url": "https://...", "similarity": 0.92},
                "supporting_laws": [...],
                "relevant_cases": [...],
                "knowledge_refs": [...],
                "summary": "综合PKULaw+RAG分析..."
            }
        """
        laws = enrichment.get("laws", [])[:max_items]
        cases = enrichment.get("cases", [])[:max_items]
        knowledge = enrichment.get("knowledge", [])[:3]

        primary_law = None
        supporting_laws = []

        if laws:
            pkulaw_laws = [l for l in laws if l.get("_priority") == "pkulaw"]
            if pkulaw_laws:
                primary_law = {
                    "source": "pkulaw",
                    "text": pkulaw_laws[0].get("content", "")[:300],
                    "title": pkulaw_laws[0].get("metadata", {}).get("title", ""),
                    "article": pkulaw_laws[0].get("metadata", {}).get("article_number", ""),
                    "url": pkulaw_laws[0].get("metadata", {}).get("url", ""),
                    "similarity": pkulaw_laws[0].get("similarity", 0),
                }
                supporting_laws = [{
                    "source": l.get("_priority", "local"),
                    "text": l.get("content", "")[:200],
                    "title": l.get("metadata", {}).get("title", ""),
                    "article": l.get("metadata", {}).get("article_number", ""),
                    "url": l.get("metadata", {}).get("url", ""),
                    "similarity": l.get("similarity", 0),
                } for l in laws[1:]]
            else:
                primary_law = {
                    "source": "local",
                    "text": laws[0].get("content", "")[:300],
                    "title": laws[0].get("metadata", {}).get("title", ""),
                    "similarity": laws[0].get("similarity", 0),
                }
                supporting_laws = [{
                    "source": "local",
                    "text": l.get("content", "")[:200],
                    "similarity": l.get("similarity", 0),
                } for l in laws[1:]]

        relevant_cases = [{
            "source": c.get("_priority", "local"),
            "case_number": c.get("metadata", {}).get("case_number", ""),
            "court": c.get("metadata", {}).get("court", ""),
            "case_grade": c.get("metadata", {}).get("case_grade", ""),
            "cause": c.get("metadata", {}).get("cause", ""),
            "url": c.get("metadata", {}).get("url", ""),
            "similarity": c.get("similarity", 0),
            "content": c.get("content", "")[:200],
        } for c in cases]

        knowledge_refs = [{
            "content": k.get("content", "")[:200],
            "similarity": k.get("similarity", 0),
            "category": k.get("metadata", {}).get("category", ""),
        } for k in knowledge]

        return {
            "risk": risk_name,
            "primary_law": primary_law,
            "supporting_laws": supporting_laws,
            "relevant_cases": relevant_cases,
            "knowledge_refs": knowledge_refs,
            "source_stats": enrichment.get("sources", {}),
        }

    def build_irar_citation(self, citation_ctx: Dict) -> str:
        """将引用上下文格式化为 IRAC 审查输出中的 🧠 PKULaw+RAG 来源标注

        输出示例：
        ```
        🧠 PKULaw+RAG 参考:
          ├─ 📜 核心法条 (PKULaw): 民法典第585条 违约金调减 → pkulaw.com/...
          ├─ 📜 辅助法条 (PKULaw): 民法典第584条 损害赔偿
          ├─ 📜 辅助法条 (本地): 民法典合同编司法解释
          ├─ ⚖️ 类案 (PKULaw): (2022)京0105民初12345号 买卖合同纠纷
          ├─ ⚖️ 类案 (本地): (2020)沪01民终8888号 违约金纠纷
          └─ 📚 合规知识: 企业合规·合同管理(违约金条款设计)
        ```
        """
        lines = ["🧠 PKULaw+RAG 参考:"]

        # 核心法条
        primary = citation_ctx.get("primary_law")
        if primary:
            source_tag = "PKULaw" if primary.get("source") == "pkulaw" else "本地RAG"
            article = primary.get("article", "")
            title = primary.get("title", "")
            url = primary.get("url", "")
            law_text = f"{title}第{article}条" if article else title
            line = f"  ├─ 📜 核心法条 ({source_tag}): {law_text}"
            if url:
                line += f" → {url}"
            lines.append(line)

        # 辅助法条
        for sl in citation_ctx.get("supporting_laws", [])[:3]:
            source_tag = "PKULaw" if sl.get("source") == "pkulaw" else "本地RAG"
            article = sl.get("article", "")
            title = sl.get("title", "")
            law_text = f"{title}第{article}条" if article else title
            lines.append(f"  ├─ 📜 辅助法条 ({source_tag}): {law_text}")

        # 案例
        for rc in citation_ctx.get("relevant_cases", [])[:3]:
            source_tag = "PKULaw" if rc.get("source") == "pkulaw" else "本地RAG"
            cn = rc.get("case_number", "")
            cause = rc.get("cause", "")
            grade = rc.get("case_grade", "")
            case_text = f"{cn} {cause} [{grade}]"
            lines.append(f"  ├─ ⚖️ 类案 ({source_tag}): {case_text}")

        # 知识库
        for kr in citation_ctx.get("knowledge_refs", [])[:2]:
            cat = kr.get("category", "通用")
            content = kr.get("content", "")[:80]
            lines.append(f"  └─ 📚 合规知识 ({cat}): {content}")

        return "\n".join(lines)

    def get_stats(self) -> Dict:
        stats = {"initialized": self._initialized}
        if self.pkustore:
            pkustats = self.pkustore.get_stats()
            stats.update(pkustats)
        return stats


# ============================================================
# 便捷接口
# ============================================================

_pkulaw_enricher = None

def get_pkulaw_enricher() -> PKULawEnricher:
    """获取PKULaw融合检索器（单例）"""
    global _pkulaw_enricher
    if _pkulaw_enricher is None:
        _pkulaw_enricher = PKULawEnricher()
        _pkulaw_enricher.initialize()
    return _pkulaw_enricher


# ============================================================
# PKULaw MCP 调用指南（供合同审查技能中的 AI agent 使用）
# ============================================================

"""
PKULaw MCP 5个工具在合同审查中的标准调用模式：

1. search_article — 法条语义检索（最常用）
   适用：发现合同风险后找法律依据
   调用：mcp__pkulaw__search_article({"query": "违约金超过实际损失 法院调减 民法典"})
   返回：相关法条列表（含title, number, article, url）

2. get_article — 法条精确查询
   适用：已知具体法条编号，需要完整原文
   调用：mcp__pkulaw__get_article({"title": "民法典", "number": "第五百八十五条"})
   返回：完整条文 + url

3. get_law_list — 法规列表
   适用：合同涉及特定领域，需列全部相关法规
   调用：mcp__pkulaw__get_law_list({"title": "数据安全"})
   返回：前10部相关法规（含时效性、效力级别）

4. search_case — 案例语义检索
   适用：找类似合同纠纷判例
   调用：mcp__pkulaw__search_case({"text": "买卖合同 违约金过高 法院调减"})
   返回：类案摘要 + 案号 + 法院 + url

5. get_case_list — 案例深度检索（25+字段）
   适用：需要完整判决书要素（查明事实/争议焦点/裁判理由/裁判依据）
   调用：mcp__pkulaw__get_case_list({"title": "买卖合同纠纷", "fulltext": "违约金"})
   返回：前10个判例完整要素

合同审查中的最佳调用时机：
  ┌─────────────────────────────────────────────────────┐
  │ 阶段二 每个M模块风险发现后：                           │
  │   1. search_article(风险关键词) → 找法条依据           │
  │   2. search_case(风险关键词)    → 找类似判例           │
  │   3. ingest_pkulaw_result()    → 存入向量库           │
  │   4. enrich_risk()             → 融合检索增强          │
  │   5. build_irar_citation()     → 生成可追溯引用        │
  └─────────────────────────────────────────────────────┘
"""


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    args = sys.argv[2:]

    if cmd == "help":
        print("合同审查 PKULaw 集成工具 v1.0")
        print("  python contract_review_pkulaw.py stats       — 查看向量库统计")
        print("  python contract_review_pkulaw.py search <查询> — 融合检索测试")
        print("  python contract_review_pkulaw.py enrich <关键词> [条款类型] — 增强检索")
    elif cmd == "stats":
        enricher = get_pkulaw_enricher()
        print(json.dumps(enricher.get_stats(), ensure_ascii=False, indent=2))
    elif cmd == "search":
        query = " ".join(args) if args else "违约金过高"
        enricher = get_pkulaw_enricher()
        result = enricher.enrich_risk(query, top_k=5)
        print(f"法条: PKULaw {result['sources']['pkulaw_laws']} + 本地 {result['sources']['local_laws']}")
        print(f"案例: PKULaw {result['sources']['pkulaw_cases']} + 本地 {result['sources']['local_cases']}")
    elif cmd == "enrich":
        keywords = args[0] if args else "违约金"
        clause = args[1] if len(args) > 1 else ""
        enricher = get_pkulaw_enricher()
        result = enricher.enrich_risk(keywords, clause, top_k=8)
        ctx = enricher.build_citation_context(result, keywords)
        print(enricher.build_irar_citation(ctx))
