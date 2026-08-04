"""
一键式专利申请前评估流水线主脚本
整合模块A/B/C/D/E，实现上传交底书→自动解析→联网检索→三性评估→报告生成
"""

import os
import sys
from typing import Dict, Optional
from dataclasses import dataclass

# 添加脚本目录到路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

# 导入各模块
try:
    from parse_disclosure import parse_disclosure_document, DisclosureElements
    from search_strategy import generate_search_queries, SearchQuery
    from patent_search import patent_search, SearchResult
    from three_criteria_evaluation import evaluate_three_criteria, ThreeCriteriaEvaluation
    from report_generator import generate_three_criteria_report
    MODULES_LOADED = True
except ImportError as e:
    MODULES_LOADED = False
    IMPORT_ERROR = str(e)


@dataclass
class PipelineConfig:
    """流水线配置"""
    # 检索配置
    databases: list = None
    min_search_results: int = 50

    # 报告配置
    report_format: str = "markdown"  # markdown / word
    output_dir: str = "./output"

    def __post_init__(self):
        if self.databases is None:
            self.databases = ["CNIPA", "EPO Espacenet", "WIPO Patentscope"]


class PatentAssessmentPipeline:
    """
    一键式专利申请前评估流水线

    使用流程：
    1. pipeline = PatentAssessmentPipeline()
    2. result = pipeline.run("技术交底书.docx")
    3. print(result.report)
    """

    def __init__(self, config: PipelineConfig = None):
        self.config = config or PipelineConfig()

    def run(self, file_path: str) -> Dict:
        """
        执行完整流水线
        :param file_path: 技术交底书文件路径
        :return: 执行结果字典
        """
        if not MODULES_LOADED:
            return {
                "success": False,
                "error": f"模块加载失败: {IMPORT_ERROR}",
                "message": "请确保已安装所需依赖: pip install python-docx pdfplumber"
            }

        result = {
            "success": False,
            "steps": {},
            "report": None,
            "message": ""
        }

        # Step 1: 解析交底书
        print("[1/5] 正在解析技术交底书...")
        try:
            elements = parse_disclosure_document(file_path)
            result["steps"]["parsing"] = {
                "success": True,
                "tech_field": elements.tech_field,
                "tech_field_ipc": elements.tech_field_ipc,
                "tech_problems_count": len(elements.tech_problems),
                "tech_features_count": len(elements.tech_features),
                "compliance_warnings": len(elements.compliance_warnings)
            }
        except Exception as e:
            result["steps"]["parsing"] = {"success": False, "error": str(e)}
            result["message"] = f"交底书解析失败: {e}"
            return result

        # Step 2: 生成检索策略
        print("[2/5] 正在生成检索策略...")
        try:
            elements_dict = elements.to_dict()
            queries = generate_search_queries(elements_dict)
            result["steps"]["search_strategy"] = {
                "success": True,
                "queries_count": len(queries),
                "queries": [q.query for q in queries]
            }
        except Exception as e:
            result["steps"]["search_strategy"] = {"success": False, "error": str(e)}
            result["message"] = f"检索策略生成失败: {e}"
            return result

        # Step 3: 联网检索
        print("[3/5] 正在进行联网检索...")
        try:
            query_dicts = [{"type": q.type, "query": q.query, "database": ",".join(q.databases)} for q in queries]
            search_result = patent_search(
                queries=query_dicts,
                databases=self.config.databases,
                min_results=self.config.min_search_results
            )
            result["steps"]["search"] = {
                "success": True,
                "total_results": search_result.total_count,
                "databases_used": search_result.databases_used,
                "exhaustive_check": search_result.exhaustive_check
            }
        except Exception as e:
            result["steps"]["search"] = {"success": False, "error": str(e)}
            result["message"] = f"联网检索失败: {e}"
            return result

        # Step 4: 三性评估
        print("[4/5] 正在进行三性评估...")
        try:
            prior_art_list = [
                {
                    "patent_no": p.patent_no,
                    "title": p.title,
                    "abstract": p.abstract,
                    "applicant": p.applicant,
                    "similarity": p.similarity
                }
                for p in search_result.results
            ]
            evaluation = evaluate_three_criteria(elements_dict, prior_art_list)
            result["steps"]["evaluation"] = {
                "success": True,
                "novelty": evaluation.novelty.conclusion,
                "creativity": evaluation.creativity.conclusion,
                "creativity_score": evaluation.creativity.overall_score,
                "utility": evaluation.utility.conclusion,
                "overall": evaluation.overall_conclusion
            }
        except Exception as e:
            result["steps"]["evaluation"] = {"success": False, "error": str(e)}
            result["message"] = f"三性评估失败: {e}"
            return result

        # Step 5: 生成报告
        print("[5/5] 正在生成报告...")
        try:
            search_results_dict = {
                "databases": search_result.databases_used,
                "exhaustive_pass": search_result.exhaustive_check.get("overall") == "通过",
                "queries": query_dicts,
                "prior_art": prior_art_list
            }
            evaluation_dict = {
                "novelty": {"conclusion": evaluation.novelty.conclusion, "reason": evaluation.novelty.reason},
                "creativity": {"conclusion": evaluation.creativity.conclusion, "reason": evaluation.creativity.reason, "score": evaluation.creativity.overall_score},
                "utility": {"conclusion": evaluation.utility.conclusion, "reason": evaluation.utility.reason},
                "overall": evaluation.overall_conclusion,
                "suggestions": evaluation.suggestions
            }
            report = generate_three_criteria_report(
                disclosure_elements=elements_dict,
                search_results=search_results_dict,
                evaluation_result=evaluation_dict,
                output_format=self.config.report_format
            )
            result["steps"]["report"] = {"success": True}
            result["report"] = report
        except Exception as e:
            result["steps"]["report"] = {"success": False, "error": str(e)}
            result["message"] = f"报告生成失败: {e}"
            return result

        result["success"] = True
        result["message"] = "评估完成"
        return result


def run_pipeline(file_path: str, config: PipelineConfig = None) -> Dict:
    """
    便捷函数：执行专利申请前评估流水线
    :param file_path: 技术交底书文件路径
    :param config: 流水线配置
    :return: 执行结果
    """
    pipeline = PatentAssessmentPipeline(config)
    return pipeline.run(file_path)


if __name__ == "__main__":
    print("=" * 60)
    print("一键式专利申请前评估流水线 v3.3.0")
    print("=" * 60)
    print("\n使用方法:")
    print("  from patent_pipeline import run_pipeline")
    print("  result = run_pipeline('技术交底书.docx')")
    print("  print(result['report'])")
    print("\n依赖模块:")
    print("  - parse_disclosure.py (模块A)")
    print("  - search_strategy.py (模块B)")
    print("  - patent_search.py (模块C)")
    print("  - three_criteria_evaluation.py (模块D)")
    print("  - report_generator.py (模块E)")