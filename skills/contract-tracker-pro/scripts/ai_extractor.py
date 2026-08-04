"""
AI Contract Node Extractor for Contract Tracker Pro
Uses OpenAI-compatible API to extract payment/due/delivery nodes from contract text
"""

import json
import logging
import urllib.request
import urllib.error
from typing import Optional, Any

logger = logging.getLogger(__name__)


EXTRACTION_PROMPT = """
你是一个专业的合同履约管理助手。请从以下合同文本中提取所有履约节点。

## 需要提取的节点类型

1. **付款节点（payment）**：合同中规定的付款时间点，包含金额和日期
2. **交期/交付节点（delivery）**：货物或服务交付的时间点，包含内容和日期
3. **合同到期日（expiry）**：合同有效期截止日期
4. **验收节点（acceptance）**：验收时间点（如有）
5. **质保节点（warranty）**：质保期截止时间（如有）

## 输出格式（严格JSON）

```json
{
  "contract_name": "合同名称（如合同中有）",
  "contract_number": "合同编号（如有）",
  "sign_date": "签署日期 格式YYYY-MM-DD（如有）",
  "expiry_date": "合同到期日 格式YYYY-MM-DD（如有）",
  "parties": {
    "party_a": "甲方名称",
    "party_b": "乙方名称"
  },
  "nodes": [
    {
      "id": "node-1",
      "type": "payment",
      "description": "首付款30%",
      "amount": 30000.00,
      "due_date": "2026-04-30",
      "raw_text": "对应的合同原文（可选）"
    },
    {
      "id": "node-2",
      "type": "delivery",
      "description": "货物交付",
      "amount": null,
      "due_date": "2026-05-15",
      "raw_text": ""
    }
  ],
  "penalty_clause": "违约金条款摘要（如有）",
  "summary": "合同整体摘要（100字以内）"
}
```

## 重要规则

- **日期格式必须为 YYYY-MM-DD**，无法确定时写 null
- **金额用数字**，单位元，无法确定时写 null（不要写"待定"）
- **description** 用简洁的中文描述这个节点
- **节点类型** 必须为：payment / delivery / expiry / acceptance / warranty 之一
- 只提取合同中**明确提到**的节点，不要推测
- 如果合同中没有某个节点，该类型字段可以为空数组/null
- 如果完全无法提取，返回所有字段为空/null的默认结构

合同文本内容：
---
{contract_text}
---
"""

FALLBACK_RESPONSE = {
    "contract_name": None,
    "contract_number": None,
    "sign_date": None,
    "expiry_date": None,
    "parties": {"party_a": None, "party_b": None},
    "nodes": [],
    "penalty_clause": None,
    "summary": None,
}


def extract_contract_nodes(
    contract_text: str,
    api_key: str,
    base_url: str = "https://api.openai.com/v1",
    model: str = "gpt-4o-mini",
    timeout: int = 60,
) -> dict:
    """
    Extract contract履约节点 from text using AI.

    Args:
        contract_text: Full text of the contract (or excerpt)
        api_key: OpenAI-compatible API key (user provides)
        base_url: API base URL (user configures)
        model: Model name (user configures)
        timeout: Request timeout in seconds

    Returns:
        Dict with contract metadata and nodes list
    """
    if not contract_text or len(contract_text.strip()) < 50:
        logger.warning("Contract text too short for extraction")
        return {**FALLBACK_RESPONSE, "summary": "合同文本过短，无法提取节点"}

    prompt = EXTRACTION_PROMPT.format(contract_text=contract_text[:8000])

    messages = [
        {"role": "system", "content": "你是一个专业的合同履约管理助手，输出严格JSON格式。"},
        {"role": "user", "content": prompt},
    ]

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": 2000,
    }

    # Build endpoint URL
    if base_url.endswith("/"):
        base_url = base_url[:-1]
    endpoint = f"{base_url}/chat/completions"

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            endpoint,
            method="POST",
            data=data,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )

        with urllib.request.urlopen(req) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            content = body.get("choices", [{}])[0].get("message", {}).get("content", "")

        # Parse JSON from response
        # Sometimes model wraps in ```json ... ``` or just outputs raw JSON
        content = content.strip()
        if content.startswith("```"):
            # Strip markdown code blocks
            lines = content.split("\n")
            content = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

        result = json.loads(content)
        logger.info(f"Extracted {len(result.get('nodes', []))} nodes from contract")

        # Normalize and validate result
        return _normalize_result(result)

    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        logger.error(f"AI extraction failed (network): {e}")
        return {**FALLBACK_RESPONSE, "summary": f"AI提取失败：网络错误（{e}）"}

    except json.JSONDecodeError as e:
        logger.error(f"AI extraction failed (parse): {e}, content: {content[:200]}")
        return {**FALLBACK_RESPONSE, "summary": f"AI提取失败：响应解析错误"}

    except Exception as e:
        logger.error(f"AI extraction failed: {e}")
        return {**FALLBACK_RESPONSE, "summary": f"AI提取失败：{e}"}


def _normalize_result(result: dict) -> dict:
    """
    Normalize and validate the AI extraction result.
    Ensures all required fields exist and have correct types.
    """
    # Ensure nodes is a list
    nodes = result.get("nodes", [])
    if not isinstance(nodes, list):
        nodes = []

    # Assign sequential IDs if missing
    for i, node in enumerate(nodes):
        if not node.get("id"):
            node["id"] = f"node-{i + 1}"
        # Ensure type is valid
        valid_types = {"payment", "delivery", "expiry", "acceptance", "warranty"}
        if node.get("type") not in valid_types:
            node["type"] = "payment"  # default

    return {
        "contract_name": result.get("contract_name"),
        "contract_number": result.get("contract_number"),
        "sign_date": result.get("sign_date"),
        "expiry_date": result.get("expiry_date"),
        "parties": {
            "party_a": result.get("parties", {}).get("party_a"),
            "party_b": result.get("parties", {}).get("party_b"),
        },
        "nodes": nodes,
        "penalty_clause": result.get("penalty_clause"),
        "summary": result.get("summary"),
    }


def extract_contract_nodes_from_pdf(
    pdf_path: str,
    api_key: str,
    base_url: str = "https://api.openai.com/v1",
    model: str = "gpt-4o-mini",
) -> dict:
    """
    Convenience wrapper: extract nodes directly from a PDF file.

    Args:
        pdf_path: Path to PDF file
        api_key: OpenAI-compatible API key
        base_url: API base URL
        model: Model name

    Returns:
        Same as extract_contract_nodes
    """
    from .pdf_extractor import extract_text

    text = extract_text(pdf_path)
    return extract_contract_nodes(
        contract_text=text,
        api_key=api_key,
        base_url=base_url,
        model=model,
    )
