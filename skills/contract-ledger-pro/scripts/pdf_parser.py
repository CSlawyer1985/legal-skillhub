"""
合同台账管理 - PDF 解析模块
使用 PyMuPDF (fitz) 提取文本
"""
import re
import fitz  # PyMuPDF
from datetime import datetime
from typing import Optional


def extract_text_from_pdf(pdf_path: str) -> str:
    """从 PDF 提取全部文本"""
    doc = fitz.open(pdf_path)
    text_parts = []
    for page in doc:
        text_parts.append(page.get_text())
    doc.close()
    return "\n".join(text_parts)


def extract_contract_fields(text: str, filename: str = "") -> dict:
    """
    从合同文本中 AI 提取关键字段
    返回字段：合同名称、金额、日期、对方、关键节点
    """
    # Extract contract name (usually first non-empty line or from filename)
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    contract_name = ""
    if lines:
        # Look for title-like patterns
        for line in lines[:5]:
            if len(line) > 5 and not line.startswith("第") and "条" not in line:
                contract_name = line
                break
        if not contract_name and filename:
            contract_name = filename.replace(".pdf", "").replace("_", " ")

    # Extract amount (RMB)
    amount = extract_amount(text)

    # Extract dates
    sign_date = extract_date(text, ["签订日期", "签署日期", "签约日期", "签订于"])
    start_date = extract_date(text, ["开始日期", "生效日期", "起始日期", "开始于"])
    end_date = extract_date(text, ["结束日期", "到期日期", "终止日期", "届满日期", "到期于"])

    # Extract counterparty
    counterparty = extract_counterparty(text)

    # Extract key nodes (payment terms, renewal, etc.)
    key_nodes = extract_key_nodes(text)

    return {
        "contract_name": contract_name,
        "amount": amount,
        "sign_date": sign_date,
        "start_date": start_date,
        "end_date": end_date,
        "counterparty": counterparty,
        "key_nodes": key_nodes,
        "status": determine_status(end_date),
    }


def extract_amount(text: str) -> Optional[float]:
    """提取合同金额"""
    patterns = [
        r"合同金额[：:]\s*([\d,，.]+)",
        r"总价款?[：:]\s*([\d,，.]+)",
        r"总价[：:]\s*([\d,，.]+)",
        r"([\d,，.]+)\s*元",
        r"¥\s*([\d,，.]+)",
        r"RMB\s*([\d,，.]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            amount_str = match.group(1).replace(",", "").replace("，", ".")
            try:
                return float(amount_str)
            except ValueError:
                continue
    return None


def extract_date(text: str, keywords: list) -> Optional[str]:
    """提取日期"""
    date_pattern = r"(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?)"
    for kw in keywords:
        idx = text.find(kw)
        if idx != -1:
            snippet = text[idx:idx+50]
            match = re.search(date_pattern, snippet)
            if match:
                return normalize_date(match.group(1))
    # Fallback: find any date in text
    match = re.search(date_pattern, text)
    if match:
        return normalize_date(match.group(1))
    return None


def normalize_date(date_str: str) -> str:
    """标准化日期格式"""
    date_str = date_str.replace("年", "-").replace("月", "-").replace("日", "")
    # Ensure YYYY-MM-DD
    parts = re.split(r"[-/]", date_str)
    if len(parts) == 3:
        return f"{int(parts[0]):04d}-{int(parts[1]):02d}-{int(parts[2]):02d}"
    return date_str


def extract_counterparty(text: str) -> Optional[str]:
    """提取对方公司名称"""
    patterns = [
        r"乙方[：:]\s*([^\s，。,，]+)",
        r"对方[：:]\s*([^\s，。,，]+)",
        r"供应商[：:]\s*([^\s，。,，]+)",
        r"服务商[：:]\s*([^\s，。,，]+)",
        r"委托方[：:]\s*([^\s，。,，]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    return None


def extract_key_nodes(text: str) -> list:
    """提取关键节点"""
    nodes = []
    # Payment terms
    payment_patterns = [
        r"付款方式[：:][^\n。]+",
        r"支付方式[：:][^\n。]+",
        r"付款条件[：:][^\n。]+",
    ]
    for p in payment_patterns:
        m = re.search(p, text)
        if m:
            nodes.append(m.group(0).strip())

    # Renewal terms
    renewal_patterns = [
        r"续约[^\n。]+",
        r"自动续期[^\n。]+",
        r"期满后[^\n。]+",
    ]
    for p in renewal_patterns:
        m = re.search(p, text)
        if m:
            nodes.append(m.group(0).strip())

    return nodes[:5]  # Limit to 5 nodes


def determine_status(end_date: Optional[str]) -> str:
    """根据到期日期判断状态"""
    if not end_date:
        return "执行中"
    try:
        end = datetime.strptime(end_date, "%Y-%m-%d")
        now = datetime.now()
        if end < now:
            return "已到期"
        return "执行中"
    except ValueError:
        return "执行中"
