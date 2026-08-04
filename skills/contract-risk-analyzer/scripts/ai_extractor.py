"""
AI-powered Contract Field Extractor
Uses OpenAI-compatible API for structured field extraction
"""

import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


# Contract type specific extraction prompts
CONTRACT_FIELD_PROMPTS = {
    "采购合同": """
请从以下采购合同文本中提取关键信息，输出JSON格式：

{
  "summary": "合同摘要（200字以内）",
  "key_terms": [
    {"category": "当事人-甲方", "content": "甲方信息", "risk": ""},
    {"category": "当事人-乙方", "content": "乙方信息", "risk": ""},
    {"category": "采购内容", "content": "采购产品/服务详情", "risk": ""},
    {"category": "合同金额", "content": "具体金额", "risk": "金额未明确或留空"},
    {"category": "付款方式", "content": "付款条件", "risk": "无明确付款时间节点"},
    {"category": "交货条款", "content": "交货时间/地点/方式", "risk": ""},
    {"category": "质量标准", "content": "质量要求", "risk": ""},
    {"category": "违约责任", "content": "违约条款", "risk": "违约责任不对等"},
    {"category": "争议解决", "content": "管辖法院/仲裁", "risk": "管辖法院在外地"},
    {"category": "合同期限", "content": "合同有效期", "risk": ""}
  ],
  "extracted_raw": {"金额": "", "付款": "", "违约": "", "其他": ""}
}

要求：
- 只提取文本中明确存在的信息，不要推测
- risk字段填写该条款的潜在风险（无风险则留空字符串）
- summary用简洁的中文概括合同核心内容
- 如果某字段在合同中未找到，content填写"未找到"，risk填写具体风险
""",

    "销售合同": """
请从以下销售合同文本中提取关键信息，输出JSON格式：

{
  "summary": "合同摘要（200字以内）",
  "key_terms": [
    {"category": "当事人-甲方", "content": "甲方（卖方）信息", "risk": ""},
    {"category": "当事人-乙方", "content": "乙方（买方）信息", "risk": ""},
    {"category": "销售内容", "content": "销售产品/服务详情", "risk": ""},
    {"category": "合同金额", "content": "具体金额", "risk": "金额未明确或留空"},
    {"category": "付款方式", "content": "付款条件", "risk": "无明确付款时间节点"},
    {"category": "交货条款", "content": "交货时间/地点/方式", "risk": ""},
    {"category": "质量保证", "content": "质量保证条款", "risk": ""},
    {"category": "违约责任", "content": "违约条款", "risk": "违约责任不对等"},
    {"category": "争议解决", "content": "管辖法院/仲裁", "risk": "管辖法院在外地"},
    {"category": "合同期限", "content": "合同有效期", "risk": ""}
  ]
}
""",

    "服务合同": """
请从以下服务合同文本中提取关键信息，输出JSON格式：

{
  "summary": "合同摘要（200字以内）",
  "key_terms": [
    {"category": "当事人-甲方", "content": "甲方（委托方）信息", "risk": ""},
    {"category": "当事人-乙方", "content": "乙方（服务方）信息", "risk": ""},
    {"category": "服务内容", "content": "服务范围/内容", "risk": ""},
    {"category": "合同金额", "content": "服务费用", "risk": "金额未明确或留空"},
    {"category": "付款方式", "content": "付款条件", "risk": "无明确付款时间节点"},
    {"category": "服务期限", "content": "服务开始/结束时间", "risk": ""},
    {"category": "验收标准", "content": "验收条件", "risk": ""},
    {"category": "违约责任", "content": "违约条款", "risk": "违约责任不对等"},
    {"category": "知识产权", "content": "IP归属条款", "risk": "知识产权归属模糊"},
    {"category": "争议解决", "content": "管辖法院/仲裁", "risk": "管辖法院在外地"}
  ]
}
""",

    "劳动合同": """
请从以下劳动合同文本中提取关键信息，输出JSON格式：

{
  "summary": "合同摘要（200字以内）",
  "key_terms": [
    {"category": "用人单位", "content": "雇主信息", "risk": ""},
    {"category": "劳动者", "content": "员工信息", "risk": ""},
    {"category": "职位", "content": "工作岗位", "risk": ""},
    {"category": "工作地点", "content": "工作地点", "risk": ""},
    {"category": "工作时间", "content": "工作时间制度", "risk": ""},
    {"category": "薪资待遇", "content": "工资/福利", "risk": ""},
    {"category": "合同期限", "content": "合同有效期", "risk": ""},
    {"category": "试用期", "content": "试用期条款", "risk": ""},
    {"category": "社会保险", "content": "社保缴纳", "risk": ""},
    {"category": "解除条款", "content": "解除条件", "risk": "解除条件过严"},
    {"category": "竞业限制", "content": "竞业条款", "risk": "竞业限制范围过宽"},
    {"category": "争议解决", "content": "管辖法院/仲裁", "risk": ""}
  ]
}
""",

    "租赁合同": """
请从以下租赁合同文本中提取关键信息，输出JSON格式：

{
  "summary": "合同摘要（200字以内）",
  "key_terms": [
    {"category": "出租方", "content": "甲方信息", "risk": ""},
    {"category": "承租方", "content": "乙方信息", "risk": ""},
    {"category": "租赁物", "content": "租赁物品/房产", "risk": ""},
    {"category": "租金", "content": "租金金额", "risk": "租金金额未明确"},
    {"category": "押金", "content": "押金条款", "risk": ""},
    {"category": "租期", "content": "租赁期限", "risk": ""},
    {"category": "付款方式", "content": "付款周期", "risk": ""},
    {"category": "续租条款", "content": "续租条件", "risk": ""},
    {"category": "维修责任", "content": "维修/维护", "risk": ""},
    {"category": "违约责任", "content": "违约条款", "risk": "违约责任不对等"},
    {"category": "解除条款", "content": "解除条件", "risk": "解除条件过严"},
    {"category": "争议解决", "content": "管辖法院/仲裁", "risk": "管辖法院在外地"}
  ]
}
""",

    "保密协议": """
请从以下保密协议文本中提取关键信息，输出JSON格式：

{
  "summary": "合同摘要（200字以内）",
  "key_terms": [
    {"category": "披露方", "content": "甲方信息", "risk": ""},
    {"category": "接收方", "content": "乙方信息", "risk": ""},
    {"category": "保密内容", "content": "保密信息范围", "risk": ""},
    {"category": "保密期限", "content": "保密时长", "risk": "保密期限超过2年"},
    {"category": "保密义务", "content": "具体保密要求", "risk": ""},
    {"category": "使用限制", "content": "使用范围限制", "risk": ""},
    {"category": "返还/销毁", "content": "信息返还/销毁条款", "risk": ""},
    {"category": "违约责任", "content": "违约赔偿", "risk": ""},
    {"category": "争议解决", "content": "管辖法院/仲裁", "risk": "管辖法院在外地"}
  ]
}
""",

    "其他": """
请从以下合同文本中提取关键信息，输出JSON格式：

{
  "summary": "合同摘要（200字以内）",
  "key_terms": [
    {"category": "当事人-甲方", "content": "甲方信息", "risk": ""},
    {"category": "当事人-乙方", "content": "乙方信息", "risk": ""},
    {"category": "合同金额", "content": "金额", "risk": "金额未明确或留空"},
    {"category": "付款方式", "content": "付款条件", "risk": ""},
    {"category": "履约期限", "content": "履行时间", "risk": ""},
    {"category": "违约责任", "content": "违约条款", "risk": "违约责任不对等"},
    {"category": "解除条款", "content": "解除条件", "risk": ""},
    {"category": "争议解决", "content": "管辖法院/仲裁", "risk": "管辖法院在外地"},
    {"category": "其他条款", "content": "其他重要条款", "risk": ""}
  ]
}
"""
}


def build_extraction_prompt(contract_type: str, user_focus: Optional[str] = None) -> str:
    """Build the prompt for AI extraction based on contract type."""
    prompt = CONTRACT_FIELD_PROMPTS.get(contract_type, CONTRACT_FIELD_PROMPTS["其他"])

    if user_focus:
        prompt += f"\n\n用户特别关注条款：{user_focus}\n请在提取时特别注意这些条款的内容和潜在风险。"

    return prompt


def extract_fields(
    text: str,
    contract_type: str,
    api_key: str,
    base_url: str = "https://api.openai.com/v1",
    model: str = "gpt-4o-mini",
    user_focus: Optional[str] = None,
) -> dict:
    """
    Extract structured fields from contract text using AI.

    Args:
        text: Contract text content
        contract_type: Type of contract
        api_key: OpenAI-compatible API key
        base_url: API base URL
        model: Model name
        user_focus: Optional user-specified focus areas

    Returns:
        Dict with summary, key_terms, and extracted_raw
    """
    import openai

    # Initialize client
    client = openai.OpenAI(api_key=api_key, base_url=base_url)

    prompt = build_extraction_prompt(contract_type, user_focus)
    full_prompt = f"""请分析以下合同文本，提取关键信息。

合同文本：
---
{text[:15000]}  # Limit text length to avoid token overflow
---

{prompt}"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "你是一个专业的合同审查助手。你的职责是结构化提取合同信息，不做法律判断，只客观呈现合同内容和潜在风险。"
                },
                {
                    "role": "user",
                    "content": full_prompt
                }
            ],
            temperature=0.1,
            max_tokens=4000,
        )

        result_text = response.choices[0].message.content

        # Parse JSON from response
        # Try to extract JSON block if present
        json_match = None
        if "```json" in result_text:
            json_match = result_text.split("```json")[1].split("```")[0]
        elif "```" in result_text:
            json_match = result_text.split("```")[1].split("```")[0]
        else:
            # Try to find JSON directly
            import re
            json_match = re.search(r'\{[\s\S]*\}', result_text)
            if json_match:
                json_match = json_match.group()

        if json_match:
            result = json.loads(json_match)
        else:
            result = {"raw_response": result_text}

        # Ensure required keys exist
        result.setdefault("summary", "")
        result.setdefault("key_terms", [])

        return result

    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        return {
            "summary": "解析失败，请检查API响应",
            "key_terms": [],
            "error": str(e),
            "raw_response": result_text if 'result_text' in dir() else ""
        }
    except Exception as e:
        logger.error(f"AI extraction error: {e}")
        raise


def call_ai_api(
    prompt: str,
    api_key: str,
    base_url: str = "https://api.openai.com/v1",
    model: str = "gpt-4o-mini",
) -> str:
    """
    Generic AI API call for any prompt.

    Args:
        prompt: The prompt to send
        api_key: API key
        base_url: API base URL
        model: Model name

    Returns:
        API response text
    """
    import openai

    client = openai.OpenAI(api_key=api_key, base_url=base_url)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "你是一个专业的合同审查助手。"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
        max_tokens=4000,
    )

    return response.choices[0].message.content
