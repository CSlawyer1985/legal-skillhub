#!/usr/bin/env python3
"""88查企业搜索服务"""

from _http import api_post
from _errors import ServiceError


def company_search(query: str, pageNo: int = 1, pageSize: int = 10) -> dict:
    """根据公司名称搜索企业列表

    Args:
        query: 公司名称关键词
        pageNo: 页码，默认 1
        pageSize: 每页数量，默认 10

    Returns:
        API 响应的 data 字段
    """
    data = api_post("/api/companySearch/1.0.0",
                    {"query": query, "pageNo": pageNo, "pageSize": pageSize})

    if not isinstance(data, dict):
        raise ServiceError("格式异常，请稍后重试")
    return data
