"""
Contract Type Detector
Auto-detects contract type from text content
"""

import re
from typing import Literal

ContractType = Literal["采购合同", "销售合同", "服务合同", "劳动合同", "租赁合同", "保密协议", "其他"]


# Keywords for each contract type (Chinese and English)
CONTRACT_TYPE_KEYWORDS = {
    "采购合同": [
        "采购", "采购合同", "采购协议", "采购订单", "购货", "购货合同",
        "supply agreement", "purchase agreement", "purchase contract",
        "procurement", "supply contract"
    ],
    "销售合同": [
        "销售", "销售合同", "销售协议", "售货", "商品销售",
        "sales agreement", "sales contract", "sale agreement"
    ],
    "服务合同": [
        "服务", "服务合同", "服务协议", "咨询服务", "技术服务",
        "service agreement", "service contract", "consulting service"
    ],
    "劳动合同": [
        "劳动合同", "雇佣合同", "聘用合同", "雇佣协议",
        "labor contract", "employment contract", "雇佣合同", "员工合同"
    ],
    "租赁合同": [
        "租赁", "租赁合同", "租赁协议", "租房", "租借",
        "lease agreement", "lease contract", "rental agreement", "rent agreement"
    ],
    "保密协议": [
        "保密", "保密协议", "保密合同", "保密条款", "保密义务",
        "confidentiality", "confidentiality agreement", "NDA", "non-disclosure"
    ]
}

# Strong indicators (exclusive keywords)
EXCLUSIVE_KEYWORDS = {
    "劳动合同": ["劳动", "雇佣", "聘用", "工资", "社会保险", "住房公积金", "试用期"],
    "保密协议": ["保密", "nda", "non-disclosure", "confidential", "保密义务", "商业秘密"],
    "租赁合同": ["租赁", "租金", "出租", "承租", "租期", "押金", " lease ", "租赁物"],
}


def detect_contract_type(text: str) -> ContractType:
    """
    Auto-detect contract type from text content.

    Args:
        text: Extracted contract text

    Returns:
        Detected contract type
    """
    text_lower = text.lower()

    # First check exclusive indicators (stronger signals)
    for contract_type, keywords in EXCLUSIVE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in text_lower)
        if score >= 2:
            return contract_type  # type: ignore

    # Check primary indicators
    scores = {}
    for contract_type, keywords in CONTRACT_TYPE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in text_lower)
        scores[contract_type] = score

    if not scores or max(scores.values()) == 0:
        return "其他"

    # Return the type with highest score
    detected_type = max(scores, key=scores.get)
    if scores[detected_type] >= 1:
        return detected_type  # type: ignore

    return "其他"


def get_contract_type_display_name(contract_type: ContractType) -> str:
    """Get display name for contract type."""
    names = {
        "采购合同": "采购合同",
        "销售合同": "销售合同",
        "服务合同": "服务合同",
        "劳动合同": "劳动合同",
        "租赁合同": "租赁合同",
        "保密协议": "保密协议",
        "其他": "其他合同"
    }
    return names.get(contract_type, contract_type)
