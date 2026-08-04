import sys
import re

DISCLAIMER = """
⚠️ **免责声明**
本工具的输出仅供初步参考，不构成正式法律意见。
涉及具体权利认定、重大金额或复杂情形时，请务必咨询具备执业资格的专业律师，结合完整事实和最新当地规则进行正式审核。
"""

RISK_PATTERNS = {
    "付款验收": {
        "keywords": ["验收", "付款", "结算", "账期", "发票", "审批"],
        "high_risk": ["单方验收", "无限期拖延", "无逾期责任", "无付款期限", "完全绑定对方判断"],
        "risk_level": "高",
        "description": "付款与验收条款失衡",
        "suggestion": "明确验收标准、验收期限、视为验收规则；明确付款日期和逾期责任"
    },
    "责任赔偿": {
        "keywords": ["赔偿", "责任", "违约金", "损失", "免责"],
        "high_risk": ["无限责任", "单方责任", "赔偿无上限", "违约金过高"],
        "risk_level": "高",
        "description": "责任与赔偿条款失衡",
        "suggestion": "增加责任上限、排除条款、对等责任安排"
    },
    "期限解除": {
        "keywords": ["解除", "终止", "续约", "通知", "提前"],
        "high_risk": ["单方解除权", "无理由解除", "自动续约无退出", "解除成本过高"],
        "risk_level": "中",
        "description": "期限与解除条款失衡",
        "suggestion": "明确解除条件、通知期限、解除后的结算和交接义务"
    },
    "知识产权": {
        "keywords": ["知识产权", "版权", "专利", "著作权", "交付", "源文件"],
        "high_risk": ["无条件转移", "无范围限制", "无使用授权", "交付物定义不清"],
        "risk_level": "中",
        "description": "知识产权归属与交付约定不清",
        "suggestion": "明确所有权、使用权、原始素材、交付标准和验收口径"
    },
    "保密数据": {
        "keywords": ["保密", "机密", "信息", "数据", "隐私", "个人信息"],
        "high_risk": ["无限期保密", "无保密范围", "无责任划分", "数据处理无约定"],
        "risk_level": "中",
        "description": "保密与数据条款不完整",
        "suggestion": "明确保密范围、例外情形、持续期限、返还/删除义务"
    },
    "争议解决": {
        "keywords": ["争议", "诉讼", "仲裁", "管辖", "适用法律"],
        "high_risk": ["单方管辖", "仲裁条款不完整", "管辖矛盾"],
        "risk_level": "中",
        "description": "争议解决条款不完整或偏向一方",
        "suggestion": "统一适用法律、管辖法院/仲裁机构、程序规则"
    }
}

LITIGATION_FEE_RULES = [
    (10000, 50, 0, 0),
    (100000, 250, 200, 0.025),
    (200000, 2300, 300, 0.02),
    (500000, 4300, 1300, 0.015),
    (1000000, 10300, 3800, 0.01),
    (2000000, 22800, 4800, 0.009),
    (5000000, 46800, 6800, 0.008),
    (10000000, 81800, 11800, 0.007),
    (20000000, 141800, 21800, 0.006),
]

def calculate_litigation_fee(amount):
    if amount <= 0:
        return 0
    if amount <= 10000:
        return 50
    elif amount <= 100000:
        return amount * 0.025 - 200
    elif amount <= 200000:
        return amount * 0.02 + 300
    elif amount <= 500000:
        return amount * 0.015 + 1300
    elif amount <= 1000000:
        return amount * 0.01 + 3800
    elif amount <= 2000000:
        return amount * 0.009 + 4800
    elif amount <= 5000000:
        return amount * 0.008 + 6800
    elif amount <= 10000000:
        return amount * 0.007 + 11800
    elif amount <= 20000000:
        return amount * 0.006 + 21800
    else:
        return amount * 0.005 + 41800

def calculate_labor_compensation(monthly_salary, years, scenario="normal"):
    n = min(years, 12)
    base = monthly_salary * n
    if scenario == "illegal":
        return monthly_salary * n * 2
    elif scenario == "n_plus_1":
        return monthly_salary * (n + 1)
    else:
        return monthly_salary * n

def scan_contract_risks(text):
    findings = []
    text_lower = text.lower()
    for category, data in RISK_PATTERNS.items():
        matched_keywords = [kw for kw in data["keywords"] if kw in text_lower]
        if not matched_keywords:
            continue
        risks_found = []
        for risk in data.get("high_risk", []):
            if risk in text_lower:
                risks_found.append(risk)
        risk_level = data["risk_level"]
        if risks_found:
            risk_level = "高"
        elif matched_keywords:
            risk_level = "中"
        findings.append({
            "category": category,
            "risk_level": risk_level,
            "description": data["description"],
            "matched_keywords": matched_keywords,
            "specific_risks": risks_found,
            "suggestion": data["suggestion"]
        })
    if any(kw in text_lower for kw in ["签字", "签章", "盖章"]):
        if not any(f["category"] == "期限解除" for f in findings):
            findings.append({
                "category": "签署程序",
                "risk_level": "低",
                "description": "签署程序和授权确认",
                "matched_keywords": [],
                "specific_risks": [],
                "suggestion": "确认签署人有合法授权，建议保留签署记录和授权文件"
            })
    return findings

def estimate_labor_dispute(user_input):
    result = {
        "facts_needed": [],
        "assumptions": [],
        "scenarios": [],
        "calculation": {}
    }
    text = user_input
    text_lower = user_input.lower()

    # 提取月工资（增强模式：支持"2万""2万元""月薪2万""2万/月"等）
    salary = None
    salary_patterns = [
        r'(\d+(?:\.\d+)?)\s*万\s*元?/?\s*月',
        r'(\d+(?:\.\d+)?)\s*万/?\s*月',
        r'月[薪工][资]?\s*[为是：:：]?\s*(\d+(?:\.\d+)?)\s*[万千]?元?',
        r'每月\s*(\d+(?:\.\d+)?)\s*[万千]?元?',
        r'工资\s*[为是：:：]?\s*(\d+(?:\.\d+)?)\s*[万千]?元?',
        r'(\d+(?:\.\d+)?)\s*千\s*元?/?\s*月',
        r'月[薪工][资]?\s*[为是：:：]?\s*(\d+(?:\.\d+)?)\s*千',
    ]
    for p in salary_patterns:
        m = re.search(p, text_lower)
        if m:
            num = float(m.group(1))
            if '万' in m.group(0):
                salary = num * 10000
            elif '千' in m.group(0):
                salary = num * 1000
            else:
                # 根据数字大小判断：<100 视为万，<1000 视为千
                if num < 100:
                    salary = num * 10000
                elif num < 1000:
                    salary = num * 1000
                else:
                    salary = num
            break

    # 提取年限
    years = None
    year_patterns = [
        r'(\d+)\s*年',
        r'工作\s*(\d+)\s*年',
        r'做了\s*(\d+)\s*年',
        r'入职\s*(\d+)\s*年',
        r'累计\s*(\d+)\s*年',
    ]
    for p in year_patterns:
        m = re.search(p, text)
        if m:
            years = int(m.group(1))
            break

    is_illegal = any(kw in text_lower for kw in ["违法解除", "无故辞退", "非法开除", "违法终止", "被辞退", "被开除"])
    is_economic = any(kw in text_lower for kw in ["经济性裁员", "经济性解除", "经营困难", "公司倒闭", "破产"])

    result["facts_needed"] = ["月工资基数", "工作年限", "解除原因", "是否提前通知"]

    if salary and years:
        result["assumptions"].append(f"月工资：{salary:.0f}元，工作年限：{years}年")
        if is_illegal:
            compensation = calculate_labor_compensation(salary, years, "illegal")
            result["scenarios"].append({
                "scenario": "违法解除（如经仲裁/诉讼确认）",
                "formula": "2N = 2 × 月工资 × 年限",
                "estimate": f"约 {compensation:.0f} 元",
                "note": f"N = {min(years,12)} 个月工资"
            })
        if is_economic:
            compensation = calculate_labor_compensation(salary, years, "normal")
            result["scenarios"].append({
                "scenario": "合法经济性解除",
                "formula": "N = 月工资 × 年限",
                "estimate": f"约 {compensation:.0f} 元",
                "note": "另需提前30天通知或支付代通知金"
            })
        compensation_n = calculate_labor_compensation(salary, years, "normal")
        result["scenarios"].append({
            "scenario": "一般合法解除（支付经济补偿）",
            "formula": "N = 月工资 × 年限（最高12年）",
            "estimate": f"约 {compensation_n:.0f} 元",
            "note": f"年限超过12年按12年计算"
        })
        # N+1场景
        compensation_n1 = calculate_labor_compensation(salary, years, "n_plus_1")
        result["scenarios"].append({
            "scenario": "合法解除（未提前通知）",
            "formula": "N+1 = 月工资 × (年限+1)",
            "estimate": f"约 {compensation_n1:.0f} 元",
            "note": "+1 为1个月代通知金"
        })
    elif salary:
        result["assumptions"].append(f"月工资：{salary:.0f}元（年限未知）")
    elif years:
        result["assumptions"].append(f"工作年限：{years}年（月工资未知）")

    return result

def generate_legal_document(topic, user_input):
    topic_lower = (topic or "").lower() + " " + user_input.lower()
    templates = {
        "起诉状": {
            "purpose": "向法院提起民事诉讼",
            "skeleton": """## 民事起诉状

### 原告信息
- 姓名/名称：
- 身份证号/统一社会信用代码：
- 地址：
- 联系方式：

### 被告信息
- 姓名/名称：
- 身份证号/统一社会信用代码：
- 地址：
- 联系方式：

### 诉讼请求
（明确、具体、可执行）
1.
2.
3.

### 事实与理由
（按时间顺序叙述）
1.
2.
3.

### 证据清单
| 序号 | 证据名称 | 证明内容 | 页码 |
|------|----------|----------|------|
| 1    |          |          |      |

### 管辖法院
（通常为被告住所地或合同履行地法院）

---
此为骨架草稿，完整诉状需补充具体事实和证据"""
        },
        "答辩状": {
            "purpose": "针对原告起诉进行答辩",
            "skeleton": """## 民事答辩状

### 答辩人（被告）信息
- 姓名/名称：
- 身份证号/统一社会信用代码：
- 地址：
- 联系方式：

### 原告信息
- 姓名/名称：

### 答辩请求
（针对原告诉讼请求表明态度）
1. 请求驳回原告第X项诉讼请求
2. 请求驳回原告全部诉讼请求

### 答辩事实与理由
（针对原告主张逐条答辩）
1. 针对原告主张的事实的答辩：
2. 针对原告法律依据的答辩：

### 证据清单
| 序号 | 证据名称 | 证明内容 | 页码 |
|------|----------|----------|------|
| 1    |          |          |      |

---
此为骨架草稿，完整答辩状需结合原告起诉内容针对性答辩"""
        },
        "劳动仲裁": {
            "purpose": "向劳动争议仲裁委员会申请仲裁",
            "skeleton": """## 劳动争议仲裁申请书

### 申请人信息
- 姓名：
- 身份证号：
- 地址：
- 联系方式：

### 被申请人信息
- 单位名称：
- 统一社会信用代码：
- 地址：
- 法定代表人：

### 仲裁请求
（劳动争议需先仲裁后诉讼）
1.
2.

### 事实与理由
（劳动关系的建立、争议的发生过程）
1.
2.

### 证据清单
| 序号 | 证据名称 | 证明内容 | 页码 |
|------|----------|----------|------|
| 1    | 劳动合同 | 劳动关系 |      |
| 2    | 工资流水 | 工资标准 |      |

---
劳动争议需先向区劳动仲裁委申请仲裁，对仲裁不服15日内可起诉
此为骨架草稿"""
        }
    }
    for doc_type, template in templates.items():
        if doc_type in topic_lower or any(kw in topic_lower for kw in ["起诉状", "答辩状", "仲裁"]):
            return {
                "document_type": doc_type,
                "purpose": template["purpose"],
                "skeleton": template["skeleton"],
                "missing_facts": ["具体金额或计算方式", "相关日期（入职时间、事件发生时间）", "相关证据清单"]
            }
    return {
        "document_type": "通用法律文书",
        "purpose": "结构化法律文书",
        "skeleton": "请明确说明需要哪种文书（如：民事起诉状、劳动仲裁申请书、答辩状等）",
        "missing_facts": []
    }

def route_task(user_input, topic=None):
    text_lower = (topic or "").lower() + " " + user_input.lower()
    contract_kws = ["合同", "条款", "协议", "风险", "有没有坑", "审查", "扫描", "协议书"]
    labor_kws = ["辞退", "赔偿", "补偿", "劳动", "工资", "解除", "开除", "经济补偿", "N+1", "2N"]
    lawsuit_fee_kws = ["诉讼费", "仲裁费", "打官司要多少钱", "值不值得起诉", "诉讼成本"]
    document_kws = ["起诉状", "答辩状", "仲裁申请", "法律文书", "起草", "骨架"]
    task_scores = {
        "contract_scan": sum(1 for kw in contract_kws if kw in text_lower),
        "labor_dispute": sum(1 for kw in labor_kws if kw in text_lower),
        "lawsuit_fee": sum(1 for kw in lawsuit_fee_kws if kw in text_lower),
        "document": sum(1 for kw in document_kws if kw in text_lower)
    }
    max_score = max(task_scores.values())
    if max_score == 0:
        return "general"
    return max(task_scores, key=task_scores.get)

def handle(topic, user_input, history=None, args=None):
    if not user_input or not user_input.strip():
        return {"status": "error", "message": "请提供需要处理的法律问题或合同内容"}
    user_input = user_input.strip()
    topic = (topic or "").strip()
    task = route_task(user_input, topic)
    if task == "contract_scan":
        findings = scan_contract_risks(user_input)
        return {
            "status": "success",
            "task_type": "合同风险扫描",
            "findings": findings,
            "summary": f"扫描发现 {len(findings)} 个风险类别",
            "high_risk_count": len([f for f in findings if f['risk_level'] == '高']),
            "disclaimer": DISCLAIMER
        }
    elif task == "labor_dispute":
        result = estimate_labor_dispute(user_input)
        result["task_type"] = "劳动纠纷/补偿估算"
        result["status"] = "success"
        result["disclaimer"] = DISCLAIMER
        return result
    elif task == "lawsuit_fee":
        amounts = re.findall(r'(\d+(?:\.\d+)?)\s*[万千万]?', user_input)
        results = []
        for a in amounts[:3]:
            try:
                num = float(a)
                if num < 100:
                    num *= 10000
                fee = calculate_litigation_fee(num)
                results.append({
                    "claim_amount": f"{num:.0f} 元",
                    "estimated_fee": f"{fee:.0f} 元",
                    "note": "不含律师费、保全费、鉴定费、差旅费等"
                })
            except:
                pass
        return {
            "status": "success",
            "task_type": "诉讼成本估算",
            "results": results if results else [{"note": "未识别到具体金额，请明确标的额"}],
            "disclaimer": DISCLAIMER
        }
    elif task == "document":
        doc = generate_legal_document(topic, user_input)
        doc["status"] = "success"
        doc["disclaimer"] = DISCLAIMER
        return doc
    else:
        return {
            "status": "success",
            "task_type": "一般法律咨询",
            "message": "我目前支持以下法律辅助任务：\n1. 合同风险扫描\n2. 劳动纠纷补偿估算\n3. 诉讼成本估算\n4. 法律文书骨架生成\n\n请告诉我您的具体需求并提供相关事实。",
            "disclaimer": DISCLAIMER
        }

if __name__ == "__main__":
    import json
    if len(sys.argv) > 1:
        user_input = " ".join(sys.argv[1:])
        result = handle(None, user_input)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("Usage:")
        print("  python handler.py '帮我看看这份合同有没有风险'")
        print("  python handler.py '被辞退赔偿多少'")
        print("  python handler.py '10万块诉讼费多少'")
        print("  python handler.py '帮我起草一份民事起诉状'")
