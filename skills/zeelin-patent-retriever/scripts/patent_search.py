#!/usr/bin/env python3
"""
专利搜索模块

从 Google BigQuery patents-public-data 抓取专利数据。

Usage:
    from scripts.patent_search import PatentSearcher

    searcher = PatentSearcher()
    patents = searcher.search_patents("舆情+AI+预警", limit=20)
"""

from __future__ import annotations

import os
import re
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# 让脚本无论从哪里执行都能找到本项目的 modules（scripts.config 等）
_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# 确保环境变量加载
import scripts.config as config  # noqa: F401

try:
    from google.cloud import bigquery
except ImportError:  # pragma: no cover - 运行时提示依赖
    print("缺少 google-cloud-bigquery 依赖")
    print("请运行: pip install -r requirements.txt")
    bigquery = None


@dataclass
class PatentResult:
    """专利搜索结果"""

    publication_number: str
    title: str = ""
    abstract: str = ""
    claims: str = ""
    inventors: Optional[List[str]] = None
    assignees: Optional[List[str]] = None
    ipc_codes: Optional[List[str]] = None
    cpc_codes: Optional[List[str]] = None
    filing_date: Optional[int] = None
    publication_date: Optional[int] = None
    country_code: str = ""
    citation_count: int = 0
    family_size: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于脑暴模块输入）"""
        return {
            "patent_number": self.publication_number,
            "publication_number": self.publication_number,
            "title": self.title or "",
            "abstract": self.abstract or "",
            "claims": self.claims or "",
            "ipc_codes": self.ipc_codes or [],
            "cpc_codes": self.cpc_codes or [],
            "inventors": self.inventors or [],
            "assignees": self.assignees or [],
            "country_code": self.country_code or "",
            "citation_count": self.citation_count,
            "applicant": ", ".join(self.assignees or []) if self.assignees else "",
            "publication_date": str(self.publication_date) if self.publication_date else "",
        }


class PatentSearcher:
    """专利搜索器"""

    TABLE = "patents-public-data.patents.publications"

    def __init__(self):
        if bigquery is None:
            raise ImportError("google-cloud-bigquery 未安装")
        self.client = bigquery.Client()

    def search_patents(
        self,
        keywords: str,
        limit: int = 20,
        country: Optional[str] = None,
    ) -> List[PatentResult]:
        """
        搜索专利（按发布日期排序，不筛选引用次数）

        Args:
            keywords: 搜索关键词，多个可用 + 或空格分隔
            limit: 返回数量
            country: 国家代码筛选
        """
        keyword_list = [kw.strip() for kw in re.split(r"[+\s]+", keywords) if kw.strip()]
        if not keyword_list:
            raise ValueError("请提供至少一个关键词")

        match_conditions: List[str] = []
        match_score_terms: List[str] = []
        params: List[bigquery.ScalarQueryParameter] = []

        for i, kw in enumerate(keyword_list):
            param_name = f"kw_{i}"
            cond = (
                "(EXISTS(SELECT 1 FROM UNNEST(title_localized) t WHERE LOWER(t.text) LIKE CONCAT('%', @{param}, '%')) "
                "OR EXISTS(SELECT 1 FROM UNNEST(abstract_localized) a WHERE LOWER(a.text) LIKE CONCAT('%', @{param}, '%')))"
            ).format(param=param_name)
            match_conditions.append(cond)
            match_score_terms.append(f"CASE WHEN {cond} THEN 1 ELSE 0 END")
            params.append(bigquery.ScalarQueryParameter(param_name, "STRING", kw.lower()))

        keyword_count = len(keyword_list)
        min_match = 1 if keyword_count <= 2 else (2 if keyword_count <= 5 else 3)
        params.append(bigquery.ScalarQueryParameter("min_match", "INT64", min_match))

        where_parts = ["publication_number IS NOT NULL"]
        if country:
            where_parts.append("country_code = @country")
            params.append(bigquery.ScalarQueryParameter("country", "STRING", country.upper()))
        where_clause = " AND ".join(where_parts)
        match_score_sql = " + ".join(match_score_terms)

        query = f"""
            WITH scored_patents AS (
                SELECT
                    publication_number,
                    country_code,
                    title_localized,
                    abstract_localized,
                    claims_localized,
                    inventor_harmonized,
                    assignee_harmonized,
                    ipc,
                    cpc,
                    filing_date,
                    publication_date,
                    ({match_score_sql}) AS match_score
                FROM `{self.TABLE}`
                WHERE {where_clause}
            ),
            matched_patents AS (
                SELECT *
                FROM scored_patents
                WHERE match_score >= @min_match
            )
            SELECT
                publication_number,
                country_code,
                (SELECT text FROM UNNEST(title_localized) WHERE text IS NOT NULL LIMIT 1) as title,
                (SELECT text FROM UNNEST(abstract_localized) WHERE text IS NOT NULL LIMIT 1) as abstract,
                (SELECT text FROM UNNEST(claims_localized) WHERE text IS NOT NULL LIMIT 1) as claims,
                ARRAY(SELECT name FROM UNNEST(inventor_harmonized)) as inventors,
                ARRAY(SELECT name FROM UNNEST(assignee_harmonized)) as assignees,
                ARRAY(SELECT code FROM UNNEST(ipc)) as ipc_codes,
                ARRAY(SELECT code FROM UNNEST(cpc)) as cpc_codes,
                filing_date,
                publication_date,
                match_score
            FROM matched_patents
            ORDER BY match_score DESC, publication_date DESC
            LIMIT @limit
        """

        params.append(bigquery.ScalarQueryParameter("limit", "INT64", limit))
        job_config = bigquery.QueryJobConfig(query_parameters=params)

        results = self.client.query(query, job_config=job_config).result()

        patents: List[PatentResult] = []
        for row in results:
            patents.append(
                PatentResult(
                    publication_number=row.publication_number,
                    country_code=row.country_code,
                    title=row.title,
                    abstract=row.abstract,
                    claims=row.claims,
                    inventors=list(row.inventors) if row.inventors else [],
                    assignees=list(row.assignees) if row.assignees else [],
                    ipc_codes=list(row.ipc_codes) if row.ipc_codes else [],
                    cpc_codes=list(row.cpc_codes) if row.cpc_codes else [],
                    filing_date=row.filing_date,
                    publication_date=row.publication_date,
                )
            )

        return patents


def _cli():  # pragma: no cover
    import argparse

    parser = argparse.ArgumentParser(description="专利搜索工具")
    parser.add_argument("--keywords", "-k", required=True, help="搜索关键词，多个用+连接")
    parser.add_argument("--output", "-o", default=None, help="输出文件 (默认: patents_TIMESTAMP.json)")
    parser.add_argument("--limit", "-l", type=int, default=20, help="返回数量")
    parser.add_argument("--country", "-c", default=None, help="国家筛选 (CN/US)")
    args = parser.parse_args()

    searcher = PatentSearcher()
    patents = searcher.search_patents(
        keywords=args.keywords,
        limit=args.limit,
        country=args.country,
    )

    import time
    if args.output:
        output_file = args.output
    else:
        # 默认生成带时间戳的文件名，避免并发覆盖
        timestamp = int(time.time())
        output_file = f"patents_{timestamp}.json"

    patent_dicts = [p.to_dict() for p in patents]
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(patent_dicts, f, ensure_ascii=False, indent=2)
    print(f"[搜索] 结果已保存到: {output_file}")


if __name__ == "__main__":
    _cli()
