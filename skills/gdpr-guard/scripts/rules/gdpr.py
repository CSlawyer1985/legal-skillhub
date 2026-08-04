#!/usr/bin/env python3
"""GDPR 护栏规则包 (gdpr)。

覆盖《通用数据保护条例》(GDPR) 语境下的个人数据类别与特殊类别数据 (Art. 9)。
纯数据定义，无副作用、无网络、无动态执行。
字段定义与通用内核一致：
    PATTERNS: (id, regex, label, category, severity, validate, mask)
    KEYWORDS: (keyword, label, category, severity)
"""

PROFILE = {
    "id": "gdpr",
    "name": "GDPR 护栏规则",
    "version": "1.0.0",
    "basis": "GDPR Art. 4 (个人数据定义)、Art. 9 (特殊类别数据)、Art. 10 (刑事定罪数据)",
}

# ============ 模式规则 ============
PATTERNS = [
    # —— 通用（适用于所有法域）——
    ("email",
     r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}",
     "Email address", "Contact", "medium", None, "partial"),
    ("ipv4",
     r"(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)",
     "IPv4 address", "Network identifier", "low", "ipv4", "partial"),
    ("mac_addr",
     r"(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}",
     "MAC address", "Network identifier", "low", None, "partial"),

    # —— EU 联系方式 ——
    ("eu_phone",
     r"(?:\+|00)[1-9]\d{1,3}[-\s]?\d{4,14}",
     "EU phone number (E.164)", "Contact", "high", None, "partial"),

    # —— 金融标识 ——
    ("iban",
     r"[A-Z]{2}\d{2}[-\s]?(?:\d{4}[-\s]?){2,}\d{2}",
     "IBAN (International Bank Account Number)", "Financial", "high", None, "partial"),
    ("credit_card",
     r"(?:4\d{3}|5[1-5]\d{2}|3[47]\d{2}|6011|65\d{2})\d{10,15}",
     "Credit card number (Luhn)", "Financial", "high", "luhn", "partial"),

    # —— EU 身份标识 ——
    ("uk_ni",
     r"[A-Za-z]{2}\s?\d{2}\s?\d{2}\s?\d{2}\s?[A-Da-d]",
     "UK National Insurance number", "National identifier", "high", None, "partial"),
    ("uk_nhs",
     r"\b\d{10}\b",
     "UK NHS number (10-digit)", "Health identifier", "high", None, "partial"),
]

# ============ 关键词规则（GDPR Art. 9 特殊类别数据 + Art. 10）============
KEYWORDS = [
    # Art. 9(a) — 种族或民族出身
    ("racial origin", "Racial or ethnic origin (Art.9a)", "Special category", "high"),
    ("ethnic origin", "Racial or ethnic origin (Art.9a)", "Special category", "high"),

    # Art. 9(b) — 政治观点
    ("political opinion", "Political opinion (Art.9b)", "Special category", "high"),
    ("political affiliation", "Political affiliation (Art.9b)", "Special category", "high"),

    # Art. 9(c) — 宗教信仰或哲学信仰
    ("religious belief", "Religious or philosophical belief (Art.9c)", "Special category", "high"),
    ("philosophical belief", "Religious or philosophical belief (Art.9c)", "Special category", "high"),

    # Art. 9(d) — 工会成员身份
    ("trade union", "Trade union membership (Art.9d)", "Special category", "high"),

    # Art. 9(e) — 基因数据
    ("genetic data", "Genetic data (Art.9e)", "Special category", "high"),
    ("genetic test", "Genetic data (Art.9e)", "Special category", "high"),
    ("DNA", "Genetic data (Art.9e)", "Special category", "high"),

    # Art. 9(f) — 生物识别数据（用于身份识别）
    ("biometric data", "Biometric data for identification (Art.9f)", "Special category", "high"),
    ("fingerprint", "Biometric data (Art.9f)", "Special category", "high"),
    ("facial recognition", "Biometric data (Art.9f)", "Special category", "high"),

    # Art. 9(g) — 健康数据
    ("health data", "Health data (Art.9g)", "Special category", "high"),
    ("medical record", "Health data (Art.9g)", "Special category", "high"),
    ("diagnosis", "Health data (Art.9g)", "Special category", "high"),
    ("medical history", "Health data (Art.9g)", "Special category", "high"),
    ("patient", "Health data indicator", "Special category", "medium"),

    # Art. 9(h) — 性生活或性取向
    ("sexual orientation", "Sex life or sexual orientation (Art.9h)", "Special category", "high"),
    ("sex life", "Sex life or sexual orientation (Art.9h)", "Special category", "high"),

    # Art. 10 — 刑事定罪和犯罪
    ("criminal conviction", "Criminal conviction data (Art.10)", "Criminal data", "high"),
    ("criminal record", "Criminal conviction data (Art.10)", "Criminal data", "high"),
    ("offence", "Criminal conviction data (Art.10)", "Criminal data", "medium"),

    # GDPR Art. 4 其他个人数据类别
    ("personal data breach", "Data breach indicator", "Breach", "high"),
    ("data subject", "Data subject indicator", "Rights", "medium"),
    ("consent", "Consent processing indicator", "Lawful basis", "low"),
    ("profiling", "Automated profiling indicator", "Automated decision", "medium"),
]
