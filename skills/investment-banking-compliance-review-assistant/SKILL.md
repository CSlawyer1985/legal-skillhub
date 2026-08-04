---
name: Investment Banking Compliance Review Assistant
slug: security-ib-compliance
description: AI-powered investment banking compliance review assistant for China market — covers IPO sponsorship, M&A advisory, bond issuance, PE investment, and daily compliance monitoring. Built for IBD compliance officers, in-house counsel, and deal team members. Updated 2026 with latest CSRC/NASDAQ-style regulations, AML screening, and cross-border transaction compliance. Keywords: investment banking compliance, IBD compliance, IPO sponsorship, M&A advisory, securities regulation, CSRC compliance, China IBD, 合规审查, 投行合规, IPO保荐, 并购顾问, 证券合规, 债券发行, PE投资, 反洗钱, 尽调合规, 监管报备.
version: "3.0.1"
---

# Investment Banking Compliance Review Assistant / 投行合规审查助手

> **English:** AI-powered investment banking compliance review assistant — covers IPO sponsorship, M&A advisory, bond issuance, PE investment compliance, and real-time regulatory monitoring. Solves pain points: complex multi-jurisdiction rules, tight deal timelines, and escalating regulatory scrutiny. Built for IBD compliance officers and deal teams.
>
> **中文:** 投行合规审查助手——覆盖IPO保荐、并购顾问、债券发行、私募投资合规及实时监管动态跟踪。解决痛点：复杂多辖区规则、紧迫交易时限、监管升级压力。适用：投行合规人员、交易团队、内核律师。

---


### 证券监管最新动态 [2026-05-25更新]

| 动态类型 | 内容摘要 | 影响范围 |
|---------|---------|---------|
| 证券监管 | 2026年Q1：证监会加强投行业务合规监管，处罚力度加大 | 投行合规审查清单需纳入2026年新规要点 |
| 证券监管 | 信息披露质量监管升级，IPO保荐责任进一步压实 | 投行合规审查清单需纳入2026年新规要点 |
| 证券监管 | 中证协/中基协发布新自律规范，合规标准提升 | 投行合规审查清单需纳入2026年新规要点 |

> **数据截止**: 2026-05-25 | 来源：证监会、NFRA、中证协、安永Q1分析
> **声明**: 以上动态供参考，具体以官方最新发布为准

## Industry Pain Points / 行业痛点

| Pain Point / 痛点 | Impact / 影响 | Solution / 本Skill解决方案 |
|------------------|-------------|------------------------|
| **监管规则碎片化** | 证监会/交易所/协会规则分散，遗漏风险高 | 规则库智能检索+关联提醒 |
| **交易时间紧迫** | 并购交易窗口期短，合规审查时间压缩 | 交易阶段合规清单+自动预检 |
| **跨境合规复杂** | 境外投资涉及多国监管，核查难度大 | 跨境合规检查框架+清单 |
| **内核意见回复** | 内核会议后整改耗时，影响上会 | 内核问题库+整改建议生成 |
| **持续督导压力** | IPO后持续督导2-3年，任务繁重 | 持续督导日历+到期提醒 |

---

## Trigger Keywords / 触发关键词

**English Triggers:** IBD compliance, investment banking compliance, IPO sponsorship, M&A advisory, bond issuance, PE investment compliance, CSRC compliance, securities regulation, China IBD, compliance checklist, internal control review, regulatory filing

**中文触发词（优先）：** 投行合规 / 合规审查 / IPO保荐 / 保荐业务 / 并购顾问 / 债券发行 / 私募投资 / 合规检查清单 / 内部控制 / 监管报备 / 内核意见 / 持续督导 / 监管动态 / 证监会 / 交易所规则 / 证券业协会 / 反洗钱 / KYC / 受益人识别 / 制裁筛查 / 境外投资合规 / FDI审查

---

## Core Capabilities / 核心能力

### 1. IPO Sponsorship Compliance / IPO保荐合规

#### 1.1 Pre-IPO Compliance Checklist / 上市前合规检查

```markdown
## IPO保荐合规检查清单

### 一、主体资格
- [ ] 发行人依法设立且持续经营3年以上
- [ ] 注册资本已足额缴纳
- [ ] 主要资产不存在重大权属纠纷
- [ ] 股权清晰，不存在重大控制权变更

### 二、规范运作
- [ ] 公司治理结构健全（三会一层）
- [ ] 内部控制制度完善
- [ ] 董事、监事、高管具备任职资格
- [ ] 最近36个月内无重大违法违规

### 三、财务与会计
- [ ] 最近3年财务报表无虚假记载
- [ ] 收入确认符合准则
- [ ] 关联交易定价公允
- [ ] 不存在重大担保/诉讼/处罚

### 四、信息披露
- [ ] 招股说明书披露完整
- [ ] 重大事项已如实披露
- [ ] 不存在应披露未披露事项
```

#### 1.2 Due Diligence Framework / 尽调合规框架

```python
def ipo_compliance_review(company_info: dict, financial_data: dict, 
                         legal_docs: list) -> dict:
    """
    IPO合规审查主函数
    Args:
        company_info: 公司基本信息
        financial_data: 财务数据
        legal_docs: 法律文件清单
    Returns:
        合规审查报告
    """
    results = {
        "主体资格": check_subject_qualification(company_info),
        "规范运作": check_corporate_governance(company_info),
        "财务会计": check_financial_compliance(financial_data),
        "法律合规": check_legal_compliance(legal_docs),
        "信息披露": check_disclosure_compliance(company_info, financial_data),
        "整体风险": assess_overall_risk(company_info, financial_data)
    }
    
    # 风险评级
    risk_score = calculate_risk_score(results)
    risk_level = (
        "低风险" if risk_score < 30 else
        "中风险" if risk_score < 60 else
        "高风险" if risk_score < 80 else
        "不合格"
    )
    
    return {
        "检查结果": results,
        "风险评分": risk_score,
        "风险等级": risk_level,
        "整改建议": generate_remediation_suggestions(results),
        "合规建议书": generate_compliance_letter(results)
    }

def check_subject_qualification(info: dict) -> dict:
    """检查主体资格"""
    checks = {
        "设立年限": info.get("established_years", 0) >= 3,
        "注册资本缴纳": info.get("paid_capital_ratio", 0) >= 100,
        "资产权属清晰": info.get("asset_disputes", False) == False,
        "股权清晰": info.get("equity_clear", False) == True
    }
    
    return {
        "通过项": [k for k, v in checks.items() if v],
        "未通过项": [k for k, v in checks.items() if not v],
        "结论": "通过" if all(checks.values()) else "需整改"
    }
```

### 2. M&A Advisory Compliance / 并购顾问合规

#### 2.1 M&A Compliance Timeline / 并购合规时间轴

```markdown
## 并购交易合规时间轴

### 阶段一：意向阶段（D-90 至 D-60）
- [ ] 客户适当性评估（KYC/KYP）
- [ ] 利益冲突筛查
- [ ] 保密协议签署
- [ ] 交易结构初步设计
- [ ] 反垄断申报评估（营业额门槛）

### 阶段二：尽调阶段（D-60 至 D-30）
- [ ] 法律尽调（目标公司合规历史）
- [ ] 财务尽调（或有负债识别）
- [ ] 业务尽调（核心资产/人员）
- [ ] 监管审批路径确认
- [ ] 国家安全审查（如涉及关键基础设施）

### 阶段三：交易文件（D-30 至 D-0）
- [ ] SPA/M&A协议审查
- [ ] 陈述与保证条款核查
- [ ] 交割条件清单确认
- [ ] 监管审批条件梳理
- [ ] 融资合规审查（如适用）

### 阶段四：交割与整合（D+0 至 D+180）
- [ ] 监管审批完成确认
- [ ] 交割条件满足核查
- [ ] 反垄断交割后义务
- [ ] 人员整合合规（劳动法）
- [ ] 知识产权转让登记
```

#### 2.2 Anti-Monopoly Review / 反垄断审查

```python
def anti_monopoly_review(transactions: list, target_revenue: float,
                        buyer_revenue: float) -> dict:
    """
    反垄断审查评估
    基于经营者集中申报标准
    """
    # 申报门槛（中国）
    CHINA_THRESHOLD_OLD = 10  # 老标准：合计20亿+单家4亿
    CHINA_THRESHOLD_NEW = 8   # 新标准：合计40亿+单家8亿
    
    total_revenue = target_revenue + buyer_revenue
    
    # 计算HHI（赫芬达尔指数简化版）
    market_shares = [0.15, 0.12, 0.10, 0.08, 0.05]  # 假设市场前5名份额
    hhi = sum([s**2 for s in market_shares]) * 10000
    
    # ΔHHI计算（简化）
    post_merger_hhi = hhi + 2 * 0.12 * 0.15 * 10000  # 假设买方份额12%，目标15%
    delta_hhi = post_merger_hhi - hhi
    
    assessment = {
        "是否达到申报门槛": total_revenue >= 40,  # 新标准
        "预估HHI": round(hhi, 0),
        "ΔHHI": round(delta_hhi, 0),
        "反垄断风险": "高" if (hhi > 2500 and delta_hhi > 200) else
                    "中" if delta_hhi > 100 else "低",
        "建议": [
            "建议提前与反垄断局沟通" if delta_hhi > 200 else "",
            "准备申报材料，周期约30个工作日" if total_revenue >= 40 else "",
            "关注后续整合限制性条件" if delta_hhi > 150 else ""
        ]
    }
    
    return assessment
```

### 3. Bond Issuance Compliance / 债券发行合规

```markdown
## 债券发行合规检查框架

### 一、发行人资格
| 检查项 | 公司债 | 企业债 | 资产支持证券 |
|-------|--------|--------|-------------|
| 净资产要求 | ≥12个月均值 | 有要求 | 无 | 
| 盈利要求 | 最近3年可分配利润≥1年利息 | 最近3年盈利 | 特定 | 
| 评级要求 | AA以上 | AA以上 | 优先A档 | 
| 限制条件 | 银行间+交易所互斥 | 发改委审批 | 特定主体 | 

### 二、信息披露
- [ ] 募集说明书完整性
- [ ] 财务报告时效性（6个月内）
- [ ] 评级报告披露
- [ ] 担保/抵押情况披露

### 三、承销合规
- [ ] 承销协议条款审查
- [ ] 簿记建档合规
- [ ] 利益冲突管理
- [ ] 投资者适当性确认
```

### 4. AML/KYC Compliance / 反洗钱与KYC

```python
def aml_kyc_review(client_info: dict, transaction_data: list,
                   sanctioned_lists: list) -> dict:
    """
    反洗钱/KYC审查
    """
    results = {
        # 制裁名单筛查
        "sanction_screening": {
            "name_match": check_name_match(client_info['name'], sanctioned_lists),
            "pep_check": check_pep(client_info.get('pep', False)),
            "adverse_media": check_adverse_media(client_info['name'])
        },
        
        # 交易监控
        "transaction_monitoring": {
            "structuring_check": detect_structuring(transaction_data),
            "high_risk_region": check_high_risk_regions(client_info['regions']),
            "unusual_pattern": detect_unusual_patterns(transaction_data)
        },
        
        # 风险评级
        "risk_assessment": calculate_aml_risk(
            results["sanction_screening"],
            results["transaction_monitoring"]
        )
    }
    
    return results

def check_name_match(client_name: str, sanctioned_lists: list) -> dict:
    """制裁名单筛查"""
    for entity in sanctioned_lists:
        similarity = calculate_name_similarity(client_name, entity['name'])
        if similarity > 0.85:
            return {
                "match": True,
                "matched_entity": entity,
                "similarity": similarity,
                "action": "人工复核" if similarity < 0.95 else "立即上报"
            }
    return {"match": False}
```

### 5. Regulatory Monitoring / 监管动态跟踪

```markdown
## 2026年投行合规监管重点关注

### CSRC最新规则
| 发布日期 | 规则名称 | 核心变化 | 影响业务 |
|---------|---------|---------|---------|
| 2026-01 | 证券公司内部控制指引修订 | 内控评价体系升级 | 所有业务 |
| 2026-03 | 注册制配套规则完善 | 信息披露要求强化 | IPO/再融资 |
| 2026-04 | 跨境证券业务指引 | 境外子公司合规 | 跨境业务 |

### 交易所审核关注
| 板块 | 审核重点 | 高频问询点 |
|-----|---------|-----------|
| 科创板 | 科创属性 | 发明专利/研发投入/技术领先性 |
| 创业板 | "三创四新" | 创新性/成长性/真实性 |
| 主板 | 大盘蓝筹 | 业绩稳定性/行业地位 |

### 违规案例警示
- 案例1：尽调不充分导致虚假陈述
- 案例2：内幕交易防控漏洞
- 案例3：利益冲突未披露
```

---

## Quick Command Templates / 快速指令模板

**IPO合规预检：**
```
对[公司名称]做IPO合规预检，关注以下3点：
1. [重点关注项1]
2. [重点关注项2]
3. [重点关注项3]
```

**并购合规评估：**
```
评估[并购交易]的合规风险：
- 买方：[买方名称]
- 卖方：[卖方名称]
- 交易金额：[X]亿元
- 涉及行业：[行业]
- 是否涉及境外：[是/否]
```

**债券发行合规清单：**
```
生成[债券类型]发行合规清单，重点关注：
- 发行人：[名称]
- 发行规模：[X]亿
- 评级：[评级]
- 担保方式：[方式]
```

---

## Disclaimer

This skill provides compliance review frameworks and checklists for educational and reference purposes. All compliance decisions must be made by qualified compliance officers in accordance with applicable laws and regulations. This skill does not constitute legal advice.
