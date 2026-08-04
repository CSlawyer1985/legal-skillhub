#!/usr/bin/env python3
"""88查公司风险查询服务"""

from _http import api_post
from _errors import ServiceError


def company_risk(
    social_credit_code: str = "",
    company_id: str = "",
    page: int = 1,
    page_size: int = 10,
) -> dict:
    """根据统一社会信用代码或 companyId 查询企业风险信息

    Args:
        social_credit_code: 统一社会信用代码（与 company_id 二选一）
        company_id:         企业 ID（与 social_credit_code 二选一）
        page:               页码，默认 1
        page_size:          每页数量，默认 10

    Returns:
        API 响应的 data 字段，包含 total / riskMap / pageNo / pageSize
    """
    body = {
        "companyId": company_id or "",
        "pageSize": str(page_size),
        "page": str(page),
        "socialCreditCode": social_credit_code or "",
    }

    data = api_post("/api/companyRisk/1.0.0", body)

    if not isinstance(data, dict):
        raise ServiceError("格式异常，请稍后重试")

    # 网关返回再多嵌套一层 data：{"data": {"data": {total, riskMap, ...}}}
    inner = data.get("data")
    if isinstance(inner, dict) and ("riskMap" in inner or "total" in inner):
        return inner
    return data
