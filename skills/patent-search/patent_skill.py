#!/usr/bin/env python3
"""
专利检索技能主逻辑
"""

import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

_SKILL_DIR = Path(__file__).resolve().parent
_excel_mod: Any = None


def _load_excel_export() -> Any:
    global _excel_mod
    if _excel_mod is not None:
        return _excel_mod
    path = _SKILL_DIR / "excel_export.py"
    spec = importlib.util.spec_from_file_location(
        "skill_excel_export_patent_search", path
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"无法加载 {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _excel_mod = mod
    return mod

class PatentSkill:
    """专利检索技能"""
    
    def __init__(self, api):
        """初始化技能"""
        self.api = api
        
        # 命令映射
        self.commands = {
            'search': self.handle_search,
            'detail': self.handle_patent,
            'claims': self.handle_claims,
            'description': self.handle_desc,
            'legal': self.handle_law,
            'citing': self.handle_citing,
            'similar': self.handle_similar,
            'company': self.handle_company,
            'copyright': self.handle_copyright,
            'trademark': self.handle_trademark,
            'analysis': self.handle_analysis,
            'export': self.handle_export,
            'export_analysis': self.handle_export_analysis,
            'help': self.handle_help,
        }
    
    def _export_result(
        self, filename: str, headers: list, rows: list, sheet_name: str, summary: str
    ) -> Any:
        if not rows:
            return "❌ 无数据可导出"
        try:
            xl = _load_excel_export()
            asset, fmt = xl.export_table(
                filename,
                headers,
                rows,
                sheet_name=sheet_name,
                subdir="patent-exports",
            )
        except Exception as e:
            return {
                "error": f"导出失败: {e}",
                "hint": "专利检索、详情、权利要求等命令不受影响，请继续使用 search / detail。",
            }
        return {
            "message": (
                f"✅ 已导出 **{len(rows)}** 条记录（{fmt}）：{asset['name']}"
            ),
            "content": summary,
            "outbound_assets": [asset],
        }

    def handle_export(self, args) -> Any:
        """导出检索结果为 Excel"""
        if not args.query:
            return "❌ 请输入查询条件（export 需 query）"
        page_size = min(max(int(getattr(args, "page_size", None) or 50), 1), 100)
        page = max(int(getattr(args, "page", None) or 1), 1)
        try:
            result = self.api.search(
                query=args.query,
                page=page,
                page_size=page_size,
                data_scope=getattr(args, "scope", None) or "cn",
                sort=getattr(args, "sort", None) or "relation",
            )
            if not result.get("success"):
                return f"❌ 搜索失败: {self.api.error_message(result)}"
            patents = result.get("patents") or []
            total = result.get("total", len(patents))
            headers = [
                "序号",
                "公开号",
                "标题",
                "申请人",
                "发明人",
                "申请日",
                "公开日",
                "IPC",
                "法律状态",
                "摘要",
            ]
            rows = []
            xl = _load_excel_export()
            for i, p in enumerate(patents, 1):
                rows.append(
                    [
                        i,
                        p.get("id", ""),
                        xl.strip_markup(p.get("title", "")),
                        xl.strip_markup(p.get("applicant", "")),
                        xl.strip_markup(p.get("inventor", "")),
                        p.get("applicationDate", ""),
                        p.get("documentDate", ""),
                        p.get("ipc", ""),
                        p.get("legalStatus", ""),
                        xl.strip_markup(p.get("summary", ""))[:500],
                    ]
                )
            safe_q = re.sub(r"[^\w\u4e00-\u9fff\-]+", "_", str(args.query))[:24]
            fname = f"专利检索-{safe_q}-p{page}"
            summary = (
                f"检索式：{args.query}\n共 {total:,} 条，本页导出 {len(rows)} 条（第 {page} 页）。"
            )
            return self._export_result(
                fname, headers, rows, "专利检索", summary
            )
        except Exception as e:
            return f"❌ 导出失败: {e}"

    def handle_export_analysis(self, args) -> Any:
        """导出统计分析为 Excel"""
        if not args.query:
            return "❌ 请输入查询条件"
        dimension = getattr(args, "dimension", None)
        if not dimension:
            return "❌ export_analysis 需指定 dimension（如 applicant、applicationYear）"
        try:
            result = self.api.get_analysis(
                query=args.query,
                dimension=dimension,
                data_scope=getattr(args, "scope", None) or "cn",
            )
            if not result.get("success"):
                return f"❌ 统计分析失败: {self.api.error_message(result)}"
            items = self.api.format_analysis(result)
            if not items:
                return "❌ 无分析数据可导出"
            headers = ["序号", "维度项", "专利数量"]
            rows = [
                [i, it.get("key", ""), it.get("count", 0)]
                for i, it in enumerate(items, 1)
            ]
            safe_q = re.sub(r"[^\w\u4e00-\u9fff\-]+", "_", str(args.query))[:20]
            fname = f"专利统计-{dimension}-{safe_q}"
            summary = f"维度：{dimension}，检索式：{args.query}，共 {len(rows)} 项。"
            return self._export_result(
                fname, headers, rows, "统计分析", summary
            )
        except Exception as e:
            return f"❌ 导出失败: {e}"

    def handle_search(self, args) -> str:
        """处理搜索命令"""
        if not args.query:
            return "❌ 请输入查询条件"
        
        try:
            result = self.api.search(
                query=args.query,
                page=args.page or 1,
                page_size=args.page_size or 10,
                data_scope=args.scope or 'cn',
                sort=args.sort or 'relation'
            )
            
            if not result.get("success"):
                return f"❌ 搜索失败: {self.api.error_message(result)}"

            return self.api.format_search_result(
                result,
                detailed=args.details,
                page=args.page or 1,
                page_size=args.page_size or 10,
            )
            
        except Exception as e:
            return f"❌ 搜索失败: {e}"
    
    def handle_patent(self, args) -> str:
        """处理专利详情命令"""
        if not args.patent_id:
            return "❌ 请输入专利ID"
        
        try:
            result = self.api.get_patent_base(args.patent_id)
            
            if not result.get('success'):
                return f"❌ 获取专利详情失败: {result.get('message', '未知错误')}"
            
            patent = result.get('patent', {})
            return self.api.format_patent_detail(args.patent_id, patent)
            
        except Exception as e:
            return f"❌ 获取专利详情失败: {e}"
    
    def handle_claims(self, args) -> str:
        """处理权利要求命令"""
        if not args.patent_id:
            return "❌ 请输入专利ID"
        
        try:
            result = self.api.get_patent_claims(args.patent_id)
            
            if not result.get('success'):
                return f"❌ 获取权利要求失败: {self.api.error_message(result)}"
            
            patent = self.api.unwrap_patent(result)
            claims = self.api.format_claims_text(patent.get('claims', ''))
            
            output = []
            output.append(f"📜 权利要求: {args.patent_id}")
            if patent.get('documentNumber'):
                output.append(f"📄 公开号: {patent.get('documentNumber')}")
            output.append("=" * 50)
            
            if claims:
                output.append(claims)
            else:
                output.append("无权利要求信息（请确认使用检索返回的专利 id，或该文献无权利要求全文）")
            
            return "\n".join(output)
            
        except Exception as e:
            return f"❌ 获取权利要求失败: {e}"
    
    def handle_desc(self, args) -> str:
        """处理说明书命令"""
        if not args.patent_id:
            return "❌ 请输入专利ID"
        
        try:
            result = self.api.get_patent_desc(args.patent_id)
            
            if not result.get('success'):
                return f"❌ 获取说明书失败: {self.api.error_message(result)}"
            
            patent = self.api.unwrap_patent(result)
            description = self.api.format_description_text(
                patent.get('description') or patent.get('desc', '')
            )
            
            output = []
            output.append(f"📖 说明书: {args.patent_id}")
            if patent.get('documentNumber'):
                output.append(f"📄 公开号: {patent.get('documentNumber')}")
            output.append("=" * 50)
            
            if description:
                output.append(description)
            else:
                output.append("无说明书信息（请确认专利 id 正确，或该文献无说明书全文）")
            
            return "\n".join(output)
            
        except Exception as e:
            return f"❌ 获取说明书失败: {e}"
    
    def handle_law(self, args) -> str:
        """处理法律信息命令"""
        if not args.patent_id:
            return "❌ 请输入专利ID"
        
        try:
            result = self.api.get_patent_tx(args.patent_id)
            
            if not result.get('success'):
                return f"❌ 获取法律信息失败: {self.api.error_message(result)}"
            
            transactions = result.get('transactions') or []
            
            output = []
            output.append(f"⚖️ 法律信息: {args.patent_id}")
            output.append("=" * 50)
            
            if transactions:
                output.append(f"📅 法律事件 ({len(transactions)} 条):")
                for tx in transactions[:15]:
                    if not isinstance(tx, dict):
                        continue
                    date = tx.get('date', '未知')
                    typ = tx.get('type', '')
                    content = tx.get('content', '')
                    line = f"  • {date}"
                    if typ:
                        line += f" [{typ}]"
                    if content:
                        c = str(content)
                        if len(c) > 80:
                            c = c[:80] + "..."
                        line += f" {c}"
                    output.append(line)
                if len(transactions) > 15:
                    output.append(f"  还有 {len(transactions) - 15} 条未显示")
            else:
                output.append("无法律事务记录")
            
            return "\n".join(output)
            
        except Exception as e:
            return f"❌ 获取法律信息失败: {e}"
    
    def handle_citing(self, args) -> str:
        """处理引用分析命令"""
        if not args.patent_id:
            return "❌ 请输入专利ID"
        
        try:
            result = self.api.get_patent_citing(args.patent_id)
            
            if not result.get('success'):
                return f"❌ 获取引用分析失败: {self.api.error_message(result)}"
            
            citing_patents = result.get('patentXref') or result.get('citingPatents') or []
            cited_patents = result.get('citedList') or result.get('citedPatents') or []
            
            output = []
            output.append(f"🔗 引用分析: {args.patent_id}")
            output.append("=" * 50)
            
            output.append(f"📊 被引用: {len(cited_patents)} 件")
            if cited_patents:
                output.append("📄 引用本专利的文献:")
                for i, patent in enumerate(cited_patents[:5], 1):
                    if not isinstance(patent, dict):
                        continue
                    title = (patent.get('title') or '未知')[:50]
                    output.append(
                        f"  {i}. {patent.get('documentNumber') or patent.get('id', '')} - {title}"
                    )
                if len(cited_patents) > 5:
                    output.append(f"  还有 {len(cited_patents)-5} 条未显示")
            
            output.append(f"\n📊 本专利引用: {len(citing_patents)} 件")
            if citing_patents:
                output.append("📄 本专利引用的文献:")
                for i, patent in enumerate(citing_patents[:5], 1):
                    if not isinstance(patent, dict):
                        continue
                    title = (patent.get('title') or '未知')[:50]
                    output.append(
                        f"  {i}. {patent.get('documentNumber') or patent.get('id', '')} - {title}"
                    )
                if len(citing_patents) > 5:
                    output.append(f"  还有 {len(citing_patents)-5} 条未显示")
            
            return "\n".join(output)
            
        except Exception as e:
            return f"❌ 获取引用分析失败: {e}"
    
    def handle_similar(self, args) -> str:
        """处理相似专利命令"""
        if not args.patent_id:
            return "❌ 请输入专利ID"
        
        try:
            result = self.api.get_patent_like(args.patent_id)
            
            if not result.get('success'):
                return f"❌ 获取相似专利失败: {self.api.error_message(result)}"
            
            similar_patents = result.get('patentLikeList') or result.get('similarPatents') or []
            
            output = []
            output.append(f"🔍 相似专利: {args.patent_id}")
            output.append("=" * 50)
            
            output.append(f"📊 找到相似专利: {len(similar_patents)} 条")
            
            if similar_patents:
                for i, patent in enumerate(similar_patents[:5], 1):
                    if not isinstance(patent, dict):
                        continue
                    rank = patent.get('rank', '')
                    title = patent.get('title', '未知标题')
                    if len(title) > 60:
                        title = title[:60] + "..."
                    
                    output.append(f"\n{i}. 相关度: {rank}")
                    output.append(f"   🆔 {patent.get('documentNumber') or patent.get('id', '未知')}")
                    output.append(f"   📝 {title}")
                    output.append(f"   👤 {patent.get('applicant', '未知')}")
                
                if len(similar_patents) > 5:
                    output.append(f"\n📄 还有 {len(similar_patents)-5} 条相似专利未显示")
            
            return "\n".join(output)
            
        except Exception as e:
            return f"❌ 获取相似专利失败: {e}"
    
    def handle_company(self, args) -> str:
        """处理企业画像命令"""
        if not args.company_name:
            return "❌ 请输入企业名称"
        
        try:
            name = str(args.company_name).strip()
            result = self.api.get_company_portrait(name)

            if not self.api.result_ok(result):
                msg = self.api.error_message(result) or result.get("message", "未知错误")
                return (
                    f"❌ 获取企业画像失败: {msg}\n\n"
                    f"💡 请使用**企业工商全称**（如「华为技术有限公司」），简称或缺字常导致无数据。"
                )

            portrait = result.get("enterprisePortrait") or result.get("enterprise_portrait")
            if not isinstance(portrait, dict) or not portrait:
                return (
                    f"❌ 未找到企业「{name}」的画像数据。\n\n"
                    "请确认：\n"
                    "- 企业名称为工商**全称**\n"
                    "- Token 已开通企业画像接口（/api/a/portrait）"
                )

            return self.api.format_company_portrait(name, result)
            
        except Exception as e:
            return f"❌ 获取企业画像失败: {e}"
    
    def handle_copyright(self, args) -> str:
        """处理著作权搜索命令"""
        if not args.query:
            return "❌ 请输入查询条件"
        
        try:
            result = self.api.search_copyright(
                query=args.query,
                copyright_type=args.type,
                field=args.field,
                page=args.page or 1,
                page_size=args.page_size or 10
            )
            
            if not result.get('success'):
                return f"❌ 搜索著作权失败: {result.get('message', '未知错误')}"
            
            copyrights = result.get('copyrights', [])
            total = result.get('total', 0)
            
            output = []
            output.append(f"📚 著作权搜索结果")
            output.append(f"📊 总数: {total} 条")
            output.append(f"🔍 查询条件: {args.query}")
            output.append(f"📄 类型: {args.type}")
            output.append("=" * 50)
            
            if not copyrights:
                output.append("未找到相关著作权")
                return "\n".join(output)
            
            for i, copyright in enumerate(copyrights[:10], 1):
                output.append(f"{i}. 登记号: {copyright.get('registrationNumber', '未知')}")
                output.append(f"   作品名称: {copyright.get('workName', '未知')}")
                output.append(f"   著作权人: {copyright.get('copyrightOwner', '未知')}")
                output.append(f"   登记日期: {copyright.get('registrationDate', '未知')}")
                output.append(f"   作品类别: {copyright.get('workCategory', '未知')}")
                output.append("")  # 空行分隔
            
            return "\n".join(output)
            
        except Exception as e:
            return f"❌ 搜索著作权失败: {e}"
    
    def handle_trademark(self, args) -> str:
        """处理商标搜索命令"""
        if args.detail and args.trademark_id:
            # 查看商标详情
            try:
                result = self.api.get_trademark_detail(args.trademark_id)
                
                if not result.get('success'):
                    return f"❌ 获取商标详情失败: {result.get('message', '未知错误')}"
                
                trademark = result.get('trademark', {})
                
                output = []
                output.append(f"🏷️ 商标详情: {args.trademark_id}")
                output.append("=" * 50)
                
                output.append(f"📝 商标名称: {trademark.get('trademarkName', '未知')}")
                output.append(f"🔢 申请号: {trademark.get('applicationNumber', '未知')}")
                output.append(f"👤 申请人: {trademark.get('applicantLabel', '未知')}")
                output.append(f"📅 申请日: {trademark.get('applicationDate', '未知')}")
                output.append(f"🏷️ 国际分类: {', '.join(trademark.get('ncl', []))}")
                output.append(f"⚖️ 法律状态: {trademark.get('lawStatus', '未知')}")
                output.append(f"🏢 代理机构: {trademark.get('agentLabel', '未知')}")
                
                return "\n".join(output)
                
            except Exception as e:
                return f"❌ 获取商标详情失败: {e}"
        else:
            # 搜索商标
            if not args.query:
                return "❌ 请输入查询条件"
            
            try:
                result = self.api.search_trademark(
                    query=args.query,
                    page=args.page or 1,
                    page_size=args.page_size or 10,
                    sort=args.sort
                )
                
                if not result.get('success'):
                    return f"❌ 搜索商标失败: {result.get('message', '未知错误')}"
                
                trademarks = result.get('trademarks', [])
                total = result.get('total', 0)
                
                output = []
                output.append(f"🏷️ 商标搜索结果")
                output.append(f"📊 总数: {total} 条")
                output.append(f"🔍 查询条件: {args.query}")
                output.append("=" * 50)
                
                if not trademarks:
                    output.append("未找到相关商标")
                    return "\n".join(output)
                
                for i, trademark in enumerate(trademarks[:10], 1):
                    output.append(f"{i}. 商标名称: {trademark.get('trademarkName', '未知')}")
                    output.append(f"   申请号: {trademark.get('applicationNumber', '未知')}")
                    output.append(f"   申请人: {trademark.get('applicantLabel', '未知')}")
                    output.append(f"   申请日: {trademark.get('applicationDate', '未知')}")
                    output.append("")  # 空行分隔
                
                return "\n".join(output)
                
            except Exception as e:
                return f"❌ 搜索商标失败: {e}"
    
    def handle_analysis(self, args) -> str:
        """处理统计分析命令"""
        if not args.query:
            return "❌ 请输入查询条件"
        
        try:
            result = self.api.get_analysis(
                query=args.query,
                dimension=args.dimension,
                data_scope=args.scope or 'cn'
            )
            
            if not result.get('success'):
                code = result.get('code') or result.get('errorCode', '')
                msg = result.get('message') or result.get('msg', '未知错误')
                return f"❌ 统计分析失败: {msg}" + (f" (code={code})" if code else "")

            items = self.api.format_analysis(result)

            output = []
            output.append(f"📊 统计分析 - {args.dimension}")
            output.append(f"🔍 查询条件: {args.query}")
            output.append("=" * 50)

            if not items:
                output.append("无分析数据")
                return "\n".join(output)

            limit = getattr(args, 'limit', 20)
            output.append(f"📈 分布情况 (前{limit}项):")
            for i, item in enumerate(items[:limit], 1):
                key = item.get('key', '未知')
                count = item.get('count', 0)
                output.append(f"{i:2d}. {key}: {count:,}件")

            return "\n".join(output)
            
        except Exception as e:
            return f"❌ 统计分析失败: {e}"
    
    def handle_help(self, args) -> str:
        """处理帮助命令"""
        help_text = """
🏢 专利检索技能 - 使用指南
==================================================

🔍 基本命令:
  patent search <查询条件>      - 搜索专利
  patent detail <专利ID>       - 查看专利详情
  patent claims <专利ID>       - 获取权利要求
  patent description <专利ID>  - 获取说明书
  patent legal <专利ID>        - 查看法律信息

📊 分析命令:
  patent analysis <查询条件> --dimension <维度>  - 统计分析
  patent company <企业名称>                     - 企业画像

📚 扩展命令:
  patent copyright <查询条件>    - 搜索著作权
  patent trademark <查询条件>    - 搜索商标
  patent citing <专利ID>        - 引用分析
  patent similar <专利ID>       - 相似专利

🛠️ 常用参数:
  --page, -p <页码>            - 指定页码
  --page-size, -ps <条数>      - 每页显示条数
  --scope, -s <cn/all>         - 数据范围
  --sort, -st <relation/date>  - 排序方式
  --details, -d               - 显示详细信息

📖 示例:
  patent search "锂电池" --page-size 5 --details
  patent detail CN112968234A
  patent analysis "锂电池" --dimension applicant
  patent company "比亚迪股份有限公司"

🔧 配置说明:
  1. 申请API Token: https://www.9235.net/api/open
  2. 配置Token:
     openclaw config set skills.entries.patent-search.apiKey '您的Token'
  3. 重启服务: openclaw gateway restart

📞 支持:
  • 文档: https://docs.openclaw.ai
  • 社区: https://discord.com/invite/clawd
  • GitHub: https://github.com/openclaw/openclaw
    """
        return help_text