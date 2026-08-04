# -*- coding: utf-8 -*-
"""
IMA知识库联动模块

功能：
1. 获取用户知识库列表
2. 在指定知识库中搜索相关内容
3. 检索结果格式化展示
4. 辅助信息提取与专利评估流程集成

使用方式：
    from ima_knowledge_linkage import IMAKnowledgeLinkage

    linkage = IMAKnowledgeLinkage()

    # 检查凭证
    if not linkage.check_credentials():
        print("请先配置 IMA OpenAPI 凭证")
        return

    # 获取知识库列表
    kb_list = linkage.get_knowledge_bases()

    # 搜索知识库
    results = linkage.search_knowledge(kb_id, "淫羊藿 提取 酶解")

    # 格式化展示
    linkage.format_search_results(results)
"""

import json
import os
import subprocess
from typing import List, Dict, Optional, Any

# ============================================================================
# 凭证加载
# ============================================================================

def load_ima_credentials() -> tuple:
    """
    加载 IMA OpenAPI 凭证

    Returns:
        tuple: (client_id, api_key) 或 (None, None) 如果未配置
    """
    client_id = os.environ.get('IMA_OPENAPI_CLIENTID')
    api_key = os.environ.get('IMA_OPENAPI_APIKEY')

    if client_id and api_key:
        return client_id, api_key

    # 尝试从配置文件加载
    config_dir = os.path.expanduser("~/.config/ima")
    client_id_file = os.path.join(config_dir, "client_id")
    api_key_file = os.path.join(config_dir, "api_key")

    try:
        if os.path.exists(client_id_file):
            with open(client_id_file, 'r', encoding='utf-8') as f:
                client_id = f.read().strip()
        if os.path.exists(api_key_file):
            with open(api_key_file, 'r', encoding='utf-8') as f:
                api_key = f.read().strip()
    except Exception:
        pass

    return client_id, api_key


# ============================================================================
# IMA API 调用
# ============================================================================

class IMAKnowledgeLinkage:
    """IMA知识库联动类"""

    BASE_URL = "https://ima.qq.com"

    def __init__(self):
        self.client_id, self.api_key = load_ima_credentials()

    def check_credentials(self) -> bool:
        """检查凭证是否可用"""
        return bool(self.client_id and self.api_key)

    def _call_api(self, path: str, body: dict) -> dict:
        """
        调用 IMA API

        Args:
            path: API路径，如 "openapi/wiki/v1/search_knowledge_base"
            body: 请求体字典

        Returns:
            API响应字典

        Raises:
            Exception: API调用失败时抛出异常
        """
        import urllib.request
        import urllib.error

        url = f"{self.BASE_URL}/{path}"
        headers = {
            "ima-openapi-clientid": self.client_id,
            "ima-openapi-apikey": self.api_key,
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        data = json.dumps(body, ensure_ascii=False).encode('utf-8')

        req = urllib.request.Request(
            url,
            data=data,
            headers=headers,
            method='POST'
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                retcode = result.get('retcode', result.get('code', -1))
                if retcode != 0:
                    errmsg = result.get('errmsg', result.get('msg', 'Unknown error'))
                    raise Exception(f"API调用失败: {errmsg}")
                return result.get('data', {})
        except urllib.error.HTTPError as e:
            raise Exception(f"HTTP错误: {e.code} - {e.reason}")
        except urllib.error.URLError as e:
            raise Exception(f"网络错误: {str(e.reason)}")
        except json.JSONDecodeError as e:
            raise Exception(f"响应解析失败: {str(e)}")

    # =========================================================================
    # 知识库操作
    # =========================================================================

    def get_knowledge_bases(self) -> List[Dict[str, Any]]:
        """
        获取用户的所有知识库列表

        Returns:
            知识库列表，每个元素包含 id, name, description
        """
        if not self.check_credentials():
            raise Exception("IMA凭证未配置，请先配置 Client ID 和 API Key")

        data = self._call_api("openapi/wiki/v1/search_knowledge_base", {
            "query": "",
            "cursor": "",
            "limit": 50
        })

        kb_list = data.get('info_list', [])
        return kb_list

    def search_knowledge_base(self, query: str) -> List[Dict[str, Any]]:
        """
        按关键词搜索知识库

        Args:
            query: 搜索关键词

        Returns:
            匹配的知识库列表
        """
        data = self._call_api("openapi/wiki/v1/search_knowledge_base", {
            "query": query,
            "cursor": "",
            "limit": 20
        })

        return data.get('info_list', [])

    def search_knowledge(self, kb_id: str, query: str, cursor: str = "") -> Dict[str, Any]:
        """
        在指定知识库中搜索内容

        Args:
            kb_id: 知识库ID
            query: 搜索关键词
            cursor: 分页游标，默认为空

        Returns:
            搜索结果字典，包含 list, next_cursor, is_end
        """
        data = self._call_api("openapi/wiki/v1/search_knowledge", {
            "query": query,
            "knowledge_base_id": kb_id,
            "cursor": cursor
        })

        return {
            "list": data.get('info_list', []),
            "next_cursor": data.get('next_cursor', ''),
            "is_end": data.get('is_end', True)
        }

    def get_knowledge_base_info(self, kb_ids: List[str]) -> Dict[str, Any]:
        """
        获取知识库详情

        Args:
            kb_ids: 知识库ID列表（1-20个）

        Returns:
            知识库详情字典 {kb_id: {id, name, description, ...}}
        """
        data = self._call_api("openapi/wiki/v1/get_knowledge_base", {
            "ids": kb_ids
        })

        return data.get('infos', {})

    def browse_knowledge_list(self, kb_id: str, folder_id: str = None,
                             cursor: str = "", limit: int = 50) -> Dict[str, Any]:
        """
        浏览知识库内容列表

        Args:
            kb_id: 知识库ID
            folder_id: 文件夹ID（可选，浏览根目录时不传）
            cursor: 分页游标
            limit: 每页数量（1-50）

        Returns:
            知识库内容列表
        """
        body = {
            "knowledge_base_id": kb_id,
            "cursor": cursor,
            "limit": limit
        }

        if folder_id:
            body["folder_id"] = folder_id

        data = self._call_api("openapi/wiki/v1/get_knowledge_list", body)

        return {
            "list": data.get('knowledge_list', []),
            "current_path": data.get('current_path', []),
            "next_cursor": data.get('next_cursor', ''),
            "is_end": data.get('is_end', True)
        }

    # =========================================================================
    # 格式化展示
    # =========================================================================

    def _remove_emoji(self, text: str) -> str:
        """
        移除文本中的emoji字符

        Args:
            text: 输入文本

        Returns:
            移除emoji后的文本
        """
        import re
        # 移除U+1F000及以上范围的emoji字符
        return re.sub(r'[\U0001F000-\U0001FFFF]', '', text)

    def format_kb_list(self, kb_list: List[Dict]) -> str:
        """
        格式化知识库列表为可读字符串

        Args:
            kb_list: 知识库列表

        Returns:
            格式化的字符串
        """
        if not kb_list:
            return "未找到知识库"

        lines = ["[Knowledge Bases]\n"]

        for i, kb in enumerate(kb_list, 1):
            name = self._remove_emoji(kb.get('name', '未命名'))
            desc = self._remove_emoji(kb.get('description', '暂无描述'))
            kb_id = kb.get('id', '')
            lines.append(f"{i}. **{name}** - {desc}")
            lines.append(f"   ID: {kb_id}\n")

        return "\n".join(lines)

    def format_search_results(self, search_result: Dict, query: str) -> str:
        """
        格式化搜索结果为可读字符串

        Args:
            search_result: search_knowledge 返回的结果
            query: 搜索关键词

        Returns:
            格式化的字符串
        """
        items = search_result.get('list', [])

        if not items:
            return f"[Search] 在知识库中搜索「{query}」的结果：\n\n未找到相关内容"

        lines = [f"[Search] 搜索「{query}」的结果：\n"]

        for i, item in enumerate(items, 1):
            title = self._remove_emoji(item.get('title', '未命名'))
            highlight = self._remove_emoji(item.get('highlight_content', ''))
            folder_id = item.get('parent_folder_id', '')

            # 清理高亮内容中的HTML标签
            if highlight:
                highlight = highlight.replace('<em>', '**').replace('</em>', '**')

            lines.append(f"{i}. [Doc] **{title}**")
            if folder_id:
                lines.append(f"   Folder: {folder_id}")
            if highlight:
                lines.append(f"   > {highlight}")
            lines.append("")

        lines.append(f"---\n共找到 {len(items)} 条相关结果")

        return "\n".join(lines)

    def select_knowledge_base(self, kb_list: List[Dict]) -> Dict:
        """
        交互式选择知识库

        Args:
            kb_list: 知识库列表

        Returns:
            选中的知识库字典

        Note:
            在CLI环境中使用，GUI环境需自行实现选择逻辑
        """
        print(self.format_kb_list(kb_list))

        while True:
            try:
                choice = input("\n请选择知识库（输入编号）: ").strip()
                idx = int(choice) - 1
                if 0 <= idx < len(kb_list):
                    return kb_list[idx]
                else:
                    print("无效选择，请重新输入")
            except ValueError:
                print("请输入有效编号")

    def select_search_results(self, search_result: Dict,
                             max_selections: int = 5) -> List[Dict]:
        """
        交互式选择搜索结果

        Args:
            search_result: search_knowledge 返回的结果
            max_selections: 最大选择数量

        Returns:
            选中的条目列表

        Note:
            在CLI环境中使用，GUI环境需自行实现选择逻辑
        """
        print(self.format_search_results(search_result, ""))

        while True:
            try:
                choice = input(f"\n请选择参考材料（多选用逗号分隔，最多{max_selections}项）: ").strip()
                if choice.lower() == 'n' or choice.lower() == '无':
                    return []

                indices = [int(x.strip()) - 1 for x in choice.split(',')]
                items = search_result.get('list', [])

                selected = [items[i] for i in indices if 0 <= i < len(items)]

                if len(selected) > max_selections:
                    print(f"选择数量超过上限({max_selections})，请重新选择")
                    continue

                return selected
            except (ValueError, IndexError):
                print("无效选择，请重新输入")

    # =========================================================================
    # 专利信息提取
    # =========================================================================

    def extract_patent_info(self, item: Dict) -> Dict:
        """
        从知识条目中提取专利相关信息

        Args:
            item: 知识库条目

        Returns:
            提取的专利信息字典
        """
        info = {
            "title": item.get('title', ''),
            "type": self._guess_doc_type(item.get('title', '')),
            "keywords": [],
            "summary": item.get('highlight_content', '').replace('<em>', '').replace('</em>', ''),
            "source": "IMA知识库"
        }

        return info

    def _guess_doc_type(self, title: str) -> str:
        """根据标题猜测文档类型"""
        title_lower = title.lower()

        if '侵权' in title or 'fto' in title_lower or '风险' in title:
            return "FTO分析报告"
        elif '新颖性' in title or '创造性' in title or '三性' in title:
            return "可专利性评估"
        elif '检索' in title or '查新' in title:
            return "专利检索报告"
        elif '交底' in title or '技术方案' in title:
            return "技术交底书"
        elif '无效' in title or '稳定性' in title:
            return "无效分析报告"
        elif '价值' in title or '培育' in title:
            return "专利价值评价"
        else:
            return "其他文档"

    # =========================================================================
    # 辅助信息生成
    # =========================================================================

    def generate_reference_context(self, selected_items: List[Dict]) -> str:
        """
        生成参考上下文，用于注入专利评估流程

        Args:
            selected_items: 选中的知识库条目

        Returns:
            格式化的参考上下文字符串
        """
        if not selected_items:
            return ""

        lines = ["【知识库参考信息】\n"]

        for i, item in enumerate(selected_items, 1):
            info = self.extract_patent_info(item)
            lines.append(f"{i}. {info['title']} ({info['type']})")
            if info['summary']:
                lines.append(f"   摘要: {info['summary'][:200]}...")
            lines.append("")

        return "\n".join(lines)


# ============================================================================
# CLI 入口
# ============================================================================

def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description='IMA知识库联动模块')
    parser.add_argument('--list-kb', action='store_true',
                        help='列出所有知识库')
    parser.add_argument('--search', type=str,
                        help='搜索知识库内容')
    parser.add_argument('--kb', type=str,
                        help='指定知识库ID或名称')
    parser.add_argument('--output', type=str,
                        help='输出文件路径')

    args = parser.parse_args()

    linkage = IMAKnowledgeLinkage()

    if not linkage.check_credentials():
        print("❌ IMA凭证未配置")
        print("\n请先配置 IMA OpenAPI 凭证：")
        print("1. 打开 https://ima.qq.com/agent-interface 获取 Client ID 和 API Key")
        print("2. 创建配置文件:")
        print("   mkdir -p ~/.config/ima")
        print("   echo 'your_client_id' > ~/.config/ima/client_id")
        print("   echo 'your_api_key' > ~/.config/ima/api_key")
        return

    try:
        if args.list_kb:
            # 列出知识库
            kb_list = linkage.get_knowledge_bases()
            print(linkage.format_kb_list(kb_list))

        elif args.search:
            # 搜索知识库
            if not args.kb:
                # 先获取知识库列表
                kb_list = linkage.get_knowledge_bases()
                print(linkage.format_kb_list(kb_list))
                print("\n请使用 --kb 参数指定知识库ID")
                return

            results = linkage.search_knowledge(args.kb, args.search)
            output = linkage.format_search_results(results, args.search)

            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(output)
                print(f"结果已保存到: {args.output}")
            else:
                print(output)

        else:
            parser.print_help()

    except Exception as e:
        print(f"[ERROR] {str(e)}")


if __name__ == '__main__':
    main()
