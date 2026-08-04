"""
AI-powered contract comparison engine.
Handles clause-by-clause diff, risk assessment, and clause summarization.
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class DiffError(Exception):
    """Raised when contract comparison fails."""
    pass


def call_ai(prompt: str, api_key: str = None, model: str = None) -> str:
    """Call AI API to process a prompt.

    Args:
        prompt: The prompt to send
        api_key: API key (from env if not provided)
        model: Model name (from env if not provided)

    Returns:
        AI response text

    Raises:
        DiffError: If API call fails
    """
    from src.config import DEFAULT_MODEL

    if api_key is None:
        api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    if model is None:
        model = DEFAULT_MODEL

    if not api_key:
        raise DiffError("No API key configured. Set OPENAI_API_KEY or ANTHROPIC_API_KEY")

    # Detect provider from key format
    if api_key.startswith("sk-ant"):
        provider = "anthropic"
    elif api_key.startswith("sk-"):
        provider = "openai"
    else:
        provider = "openai"

    try:
        if provider == "anthropic":
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model=model,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        else:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
    except Exception as e:
        raise DiffError(f"AI API error: {e}")


def extract_clauses(text: str, api_key: str = None, model: str = None) -> List[Dict[str, Any]]:
    """Extract numbered clauses from contract text using AI.

    Args:
        text: Contract text content
        api_key: API key
        model: Model name

    Returns:
        List of clause dicts with keys: number, title, content
    """
    prompt = f"""You are a legal document analyst. Extract all numbered clauses from the following contract text.
For each clause, identify:
- clause_number: The article/section number (e.g., "第一条", "Article 1", "第3条")
- clause_title: The title/heading of this clause (in Chinese)
- content: The full text content of this clause

Return a JSON array of clauses. Example:
[
  {{"number": "第一条", "title": "合同双方", "content": "甲方为..."}},
  {{"number": "第二条", "title": "服务内容", "content": "乙方为甲方提供..."}}
]

Rules:
- Extract ALL clauses found
- Preserve complete clause text
- Use Chinese for titles if original is Chinese
- If a clause has no clear number, use the section heading as title and assign a sequential number
- If no clauses found, return []

Contract text:
{text[:8000]}

JSON:"""

    try:
        response = call_ai(prompt, api_key, model)
        # Try to extract JSON from response
        json_str = extract_json(response)
        if json_str:
            clauses = json.loads(json_str)
            if isinstance(clauses, list):
                return clauses
        # Fallback: return raw text split by common patterns
        return naive_clause_split(text)
    except Exception as e:
        logger.warning(f"Clause extraction failed: {e}")
        return naive_clause_split(text)


def naive_clause_split(text: str) -> List[Dict[str, Any]]:
    """Fallback clause splitting using regex patterns.

    Args:
        text: Contract text

    Returns:
        List of clause dicts
    """
    import re
    clauses = []

    # Match patterns like 第X条, Article X, 第X章, etc.
    patterns = [
        r'(第[一二三四五六七八九十百千\d]+条[^\n]*(?:\n(?![第一二三四五六七八九十百千\d]+条).*)*)',
        r'(Article\s+\d+[^\n]*(?:\n(?![Aa]rticle\s+\d+).*)*)',
        r'(第[一二三四五六七八九十百千\d]+章[^\n]*(?:\n(?![第一二三四五六七八九十百千\d]+章).*)*)',
    ]

    combined = f"{text}"

    for pattern in patterns:
        matches = re.finditer(pattern, combined, re.MULTILINE)
        for i, m in enumerate(matches):
            num_match = re.search(r'([第A-Za-z][^\s]+)', m.group(0))
            clauses.append({
                "number": num_match.group(1) if num_match else f"Section {i+1}",
                "title": f"条款 {i+1}",
                "content": m.group(0).strip()
            })
        if clauses:
            break

    if not clauses:
        # Split by double newlines
        paras = text.split('\n\n')
        for i, p in enumerate(paras):
            p = p.strip()
            if p:
                clauses.append({
                    "number": f"Part {i+1}",
                    "title": p[:30],
                    "content": p
                })

    return clauses


def extract_json(text: str) -> Optional[str]:
    """Extract JSON string from AI response.

    Args:
        text: Raw AI response

    Returns:
        JSON string if found, None otherwise
    """
    import re
    # Try to find JSON array/object
    match = re.search(r'\[[\s\S]*\]|\{[\s\S]*\}', text)
    if match:
        return match.group(0)
    return None


def compare_clauses(clauses_a: List[Dict], clauses_b: List[Dict], api_key: str = None, model: str = None) -> List[Dict[str, Any]]:
    """Compare two sets of clauses and identify differences.

    Args:
        clauses_a: Clauses from contract A
        clauses_b: Clauses from contract B
        api_key: API key
        model: Model name

    Returns:
        List of diff items with keys: type (new/modified/deleted/same), clause_a, clause_b, diff_content
    """
    prompt = f"""You are a legal document comparison AI. Compare two contract clause lists and identify differences.

Contract A clauses:
{json.dumps(clauses_a, ensure_ascii=False, indent=2)}

Contract B clauses:
{json.dumps(clauses_b, ensure_ascii=False, indent=2)}

For each clause, determine:
- type: "new" (exists only in B), "deleted" (exists only in A), "modified" (exists in both but different), or "same"
- For modified clauses: describe exactly WHAT changed (use Chinese for legal terms)

Return a JSON array of results. Example:
[
  {{"type": "same", "clause_a": {{"number": "第一条", "title": "合同双方"}}, "clause_b": {{"number": "第一条", "title": "合同双方"}}, "diff_content": null}},
  {{"type": "modified", "clause_a": {{"number": "第三条", "title": "服务费用"}}, "clause_b": {{"number": "第三条", "title": "服务费用"}}, "diff_content": "原条款：服务费用为每月1000元\\n新条款：服务费用为每月1500元（增加50%）"}},
  {{"type": "new", "clause_a": null, "clause_b": {{"number": "第八条", "title": "新增条款"}}, "diff_content": null}},
  {{"type": "deleted", "clause_a": {{"number": "第九条", "title": "已删除"}}, "clause_b": null, "diff_content": null}}
]

Rules:
- Match clauses by semantic content (not just number) when possible
- For modified clauses, provide a clear before/after comparison
- Return ALL clauses (same + different)

JSON:"""

    try:
        response = call_ai(prompt, api_key, model)
        json_str = extract_json(response)
        if json_str:
            result = json.loads(json_str)
            if isinstance(result, list):
                return result
        return fallback_compare(clauses_a, clauses_b)
    except Exception as e:
        logger.warning(f"Clause comparison failed: {e}")
        return fallback_compare(clauses_a, clauses_b)


def fallback_compare(clauses_a: List[Dict], clauses_b: List[Dict]) -> List[Dict[str, Any]]:
    """Fallback comparison when AI fails.

    Args:
        clauses_a: Clauses from contract A
        clauses_b: Clauses from contract B

    Returns:
        List of diff items
    """
    result = []
    all_numbers = set()

    for c in clauses_a:
        num = c.get("number", "")
        all_numbers.add(num)
        result.append({
            "type": "deleted",
            "clause_a": c,
            "clause_b": None,
            "diff_content": None
        })

    for c in clauses_b:
        num = c.get("number", "")
        if num not in all_numbers:
            result.append({
                "type": "new",
                "clause_a": None,
                "clause_b": c,
                "diff_content": None
            })
        else:
            result.append({
                "type": "modified",
                "clause_a": c,
                "clause_b": c,
                "diff_content": None
            })

    return result


def assess_risk(diff_items: List[Dict], api_key: str = None, model: str = None) -> List[Dict[str, Any]]:
    """Assess legal risk level for each changed clause.

    Args:
        diff_items: List of diff items from compare_clauses
        api_key: API key
        model: Model name

    Returns:
        List of risk assessments with keys: clause, risk_level (high/medium/low), risk_reason
    """
    # Filter to only changed clauses
    changed = [d for d in diff_items if d["type"] in ("new", "modified", "deleted")]
    if not changed:
        return []

    prompt = f"""You are a legal risk analyst. Assess the legal risk level for each contract clause change.

Changed clauses:
{json.dumps(changed, ensure_ascii=False, indent=2)}

For each clause, determine:
- risk_level: "high" (significant legal/financial impact), "medium" (moderate impact), or "low" (minimal impact)
- risk_reason: Brief explanation of why this poses this level of risk (in Chinese)

Consider:
- 责任条款变更 (liability clause changes) → HIGH
- 违约条款变更 → HIGH
- 费用/付款条款变更 → HIGH
- 保密条款 → MEDIUM
- 期限/续约条款 → MEDIUM
- 格式/表述调整，无实质影响 → LOW
- 新增一般性条款 → LOW

Return a JSON array of assessments in the same order as input:
[
  {{"clause": {{...}}, "risk_level": "high", "risk_reason": "该条款增加了甲方责任..."}},
  ...
]

JSON:"""

    try:
        response = call_ai(prompt, api_key, model)
        json_str = extract_json(response)
        if json_str:
            result = json.loads(json_str)
            if isinstance(result, list):
                return result
        return [{"clause": d, "risk_level": "low", "risk_reason": "AI评估不可用"} for d in changed]
    except Exception as e:
        logger.warning(f"Risk assessment failed: {e}")
        return [{"clause": d, "risk_level": "low", "risk_reason": f"评估失败: {e}"} for d in changed]


def summarize_key_clauses(clauses: List[Dict], api_key: str = None, model: str = None) -> List[Dict[str, str]]:
    """Extract and summarize key clauses from a contract.

    Args:
        clauses: List of contract clauses
        api_key: API key
        model: Model name

    Returns:
        List of summaries with keys: number, title, summary
    """
    if not clauses:
        return []

    prompt = f"""You are a legal document analyst. Summarize the key clauses of this contract in concise Chinese.

Contract clauses:
{json.dumps(clauses, ensure_ascii=False, indent=2)[:6000]}

Identify and summarize ONLY the most important clauses (typically 5-10):
- 合同双方/当事人
- 核心权利义务
- 费用/报酬条款
- 违约责任
- 争议解决
- 保密义务
- 合同期限

For each key clause provide:
- number: The clause number
- title: The clause title
- summary: 1-2 sentence summary in Chinese

Return a JSON array:
[
  {{"number": "第一条", "title": "合同双方", "summary": "本合同双方为甲方XX公司和乙方YY公司..."}},
  ...
]

If no significant clauses found, return [].

JSON:"""

    try:
        response = call_ai(prompt, api_key, model)
        json_str = extract_json(response)
        if json_str:
            result = json.loads(json_str)
            if isinstance(result, list):
                return result
        return []
    except Exception as e:
        logger.warning(f"Key clause summarization failed: {e}")
        return []
