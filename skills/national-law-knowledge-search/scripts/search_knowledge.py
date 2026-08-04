#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
国家法律法规知识库检索脚本

功能：调用向量检索接口查询法律知识库，返回与查询最相关的法律条文
参数：query（查询文本），topk（返回数量）
"""

import sys
import json
import argparse


def search_knowledge(query: str, topk: int = 5) -> dict:
    """
    调用国家法律法规向量检索接口
    
    参数：
        query: 查询文本（字符串类型）
        topk: 返回结果数量（整数类型），默认5
    
    返回：
        dict: JSON格式的检索结果
    """
    # 延迟导入requests，避免不必要的依赖检查
    try:
        import requests
    except ImportError:
        return {
            "success": False,
            "error": "缺少requests库，请执行：pip install requests==2.31.0"
        }
    
    # 向量检索接口配置
    url = "https://chat2.orientlaw.cn/api/v1/embedding/search"
    headers = {
        "Authorization": "Bearer akmHjUkJfrqhLE2v3dXBN9YCM896kL5y",
        "Content-Type": "application/json"
    }
    
    # 构建请求体（严格按照格式）
    payload = {
        "query": str(query),  # 确保query是字符串
        "topk": int(topk)     # 确保topk是整数
    }
    
    try:
        # 发起POST请求
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        # 检查HTTP状态码
        response.raise_for_status()
        
        # 解析JSON响应
        data = response.json()
        
        return {
            "success": True,
            "data": data,
            "query": query,
            "topk": topk
        }
        
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "请求超时，请稍后重试"
        }
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "error": "网络连接失败，请检查网络状态"
        }
    except requests.exceptions.HTTPError as e:
        return {
            "success": False,
            "error": f"HTTP错误：{e.response.status_code}",
            "detail": e.response.text if hasattr(e.response, 'text') else ""
        }
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "API返回数据格式错误"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"未知错误：{str(e)}"
        }


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="国家法律法规知识库检索工具",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--query",
        type=str,
        required=True,
        help="查询文本（字符串）"
    )
    
    parser.add_argument(
        "--topk",
        type=int,
        default=5,
        help="返回结果数量（整数），默认5"
    )
    
    args = parser.parse_args()
    
    # 参数验证
    if not args.query or not args.query.strip():
        print(json.dumps({
            "success": False,
            "error": "查询文本不能为空"
        }, ensure_ascii=False, indent=2))
        sys.exit(1)
    
    if args.topk <= 0 or args.topk > 50:
        print(json.dumps({
            "success": False,
            "error": "topk参数必须在1-50之间"
        }, ensure_ascii=False, indent=2))
        sys.exit(1)
    
    # 调用检索
    result = search_knowledge(args.query, args.topk)
    
    # 输出结果（JSON格式）
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 返回码
    sys.exit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()
