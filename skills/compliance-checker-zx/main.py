#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
行业合规工具 - compliance-checker
提供10个高级合规算法工具：合同智能分析、法规检索引擎(倒排索引+TF-IDF)、
风险评估模型(多因子加权+非线性变换)、合规清单生成、隐私影响评估(PIA)、
数据脱敏器(K-匿名/L-多样性/T-接近性)、法规术语解释器、合规条款生成器、
合规义务追踪器、合规报告生成器。

全部使用Python标准库实现，无外部依赖。
"""

import json
import math
import re
from collections import defaultdict, Counter
from datetime import datetime, timedelta


# ---------------------------------------------------------------------------
# 1. 合同智能分析
# ---------------------------------------------------------------------------
def contract_analyzer(contract_text):
    """
    合同智能分析：解析合同结构并提取关键要素。

    算法原理:
        - 结构解析: 正则识别标题(第X章/条)、附件(附件X)、编号
        - 要素提取: 规则引擎+正则匹配当事人/金额/期限/违约责任/争议解决
        - 条件判断树: 多层规则验证要素完整性

    参数:
        contract_text (str): 合同文本

    返回:
        dict: 合同分析结果，含structure、key_elements、risk_points、completeness。
    """
    # 步骤1: 结构解析
    chapters = re.findall(r'第[一二三四五六七八九十百\d]+章\s*[^\n]+', contract_text)
    articles = re.findall(r'第[一二三四五六七八九十百\d]+条\s*[^\n]+', contract_text)
    attachments = re.findall(r'附件[一二三四五六七八九十\d]+[：:][^\n]*', contract_text)

    # 步骤2: 关键要素提取（规则引擎）
    # 当事人识别
    parties = re.findall(r'(?:甲方|乙方|丙方|发包方|承包方|买方|卖方|出租方|承租方|委托方|受托方)[（(]([^）)]+)[）)]', contract_text)
    if not parties:
        parties = re.findall(r'(?:甲方|乙方|丙方)[：:]\s*([^\n，,。.]+)', contract_text)

    # 金额识别
    amounts = re.findall(r'(?:人民币|金额|总价|合同总价|价款)[：:\s]*([\d,，.]+)\s*元', contract_text)
    amount_numbers = []
    for amt in amounts:
        cleaned = amt.replace(',', '').replace('，', '')
        try:
            amount_numbers.append(float(cleaned))
        except ValueError:
            pass

    # 期限识别
    duration_patterns = [
        r'合同期限[：:\s]*自(\d{4}年\d{1,2}月\d{1,2}日).*(?:至|到)(\d{4}年\d{1,2}月\d{1,2}日)',
        r'有效期为?(\d+)\s*(?:年|个月|月|日|天)',
    ]
    durations = []
    for pattern in duration_patterns:
        durations.extend(re.findall(pattern, contract_text))

    # 违约责任识别
    breach_keywords = ["违约", "违约金", "违约责任", "赔偿", "损失赔偿"]
    breach_clauses = []
    sentences = re.split(r'[。\n；;]', contract_text)
    for sent in sentences:
        if any(kw in sent for kw in breach_keywords) and len(sent.strip()) > 5:
            breach_clauses.append(sent.strip())

    # 争议解决识别
    dispute_keywords = ["仲裁", "诉讼", "管辖", "争议解决", "法院"]
    dispute_clauses = []
    for sent in sentences:
        if any(kw in sent for kw in dispute_keywords) and len(sent.strip()) > 5:
            dispute_clauses.append(sent.strip())

    # 步骤3: 完整性评估（条件判断树）
    required_elements = {
        "当事人": len(parties) > 0,
        "合同金额": len(amount_numbers) > 0,
        "合同期限": len(durations) > 0,
        "违约责任": len(breach_clauses) > 0,
        "争议解决": len(dispute_clauses) > 0,
        "合同条款": len(articles) > 0,
    }
    completeness_score = sum(required_elements.values()) / len(required_elements) * 100

    # 步骤4: 风险点识别
    risk_points = []
    if not required_elements["违约责任"]:
        risk_points.append({"level": "高", "issue": "缺少违约责任条款"})
    if not required_elements["争议解决"]:
        risk_points.append({"level": "中", "issue": "缺少争议解决条款"})
    if not required_elements["合同期限"]:
        risk_points.append({"level": "中", "issue": "缺少明确的合同期限"})
    if amount_numbers and max(amount_numbers) > 1000000:
        risk_points.append({"level": "低", "issue": f"合同金额较大({max(amount_numbers):.0f}元)，建议法律审核"})

    # 自动检测模糊表述
    vague_terms = ["视情况", "另行协商", "适当", "合理", "尽快", "及时"]
    for term in vague_terms:
        if term in contract_text:
            risk_points.append({"level": "低", "issue": f"存在模糊表述：'{term}'"})

    return {
        "structure": {
            "chapters": chapters,
            "articles_count": len(articles),
            "articles": articles[:10],
            "attachments": attachments,
            "total_length": len(contract_text)
        },
        "key_elements": {
            "parties": parties,
            "amounts": amount_numbers,
            "total_amount": sum(amount_numbers) if amount_numbers else None,
            "durations": durations,
            "breach_clauses": breach_clauses[:5],
            "dispute_clauses": dispute_clauses[:3]
        },
        "completeness": {
            "score": round(completeness_score, 1),
            "required_elements": required_elements,
            "missing_elements": [k for k, v in required_elements.items() if not v]
        },
        "risk_points": risk_points,
        "risk_level": "高" if any(r["level"] == "高" for r in risk_points) else ("中" if risk_points else "低")
    }


# ---------------------------------------------------------------------------
# 2. 法规检索引擎 (倒排索引 + TF-IDF)
# ---------------------------------------------------------------------------
def regulation_search_engine(query, regulation_database, top_k=10):
    """
    法规检索引擎：倒排索引 + TF-IDF评分 + 法规层级权重。

    算法原理:
        - 倒排索引: term -> [(doc_id, freq), ...]，支持快速检索
        - TF-IDF评分: tf(t,d) * idf(t) = (词频/文档长度) * log(N/df)
        - 短语匹配: 查询中连续词组匹配加权
        - 法规层级权重: 宪法>法律>行政法规>部门规章>地方性法规

    参数:
        query (str): 查询字符串
        regulation_database (list[dict]): 法规数据库，每条含id, title, content, level
        top_k (int): 返回前K条结果

    返回:
        list[dict]: 按相关度排序的法规列表，含score、matched_terms、snippet。
    """
    # 法规层级权重
    level_weights = {
        "宪法": 5.0, "法律": 4.0, "行政法规": 3.0,
        "部门规章": 2.0, "地方性法规": 1.5, "司法解释": 3.5, "其他": 1.0
    }

    # 步骤1: 分词（简易中文分词 - 按字+词组）
    def tokenize(text):
        # 提取2-4字词组和单字
        tokens = re.findall(r'[\u4e00-\u9fa5]{2,4}|[a-zA-Z]+|\d+', text.lower())
        return tokens

    query_tokens = tokenize(query)
    query_set = set(query_tokens)

    # 步骤2: 构建倒排索引
    inverted_index = defaultdict(list)  # term -> [(doc_idx, tf)]
    doc_lengths = []
    doc_term_sets = []

    for doc_idx, reg in enumerate(regulation_database):
        full_text = reg.get("title", "") + " " + reg.get("content", "")
        tokens = tokenize(full_text)
        doc_lengths.append(len(tokens))
        term_counts = Counter(tokens)
        doc_term_sets.append(set(tokens))
        for term, count in term_counts.items():
            inverted_index[term].append((doc_idx, count))

    # 步骤3: 计算IDF
    N = len(regulation_database)
    idf = {}
    for term in query_set:
        df = len(inverted_index.get(term, []))
        if df > 0:
            idf[term] = math.log((N + 1) / (df + 1)) + 1  # 平滑IDF
        else:
            idf[term] = 0

    # 步骤4: TF-IDF评分
    scores = defaultdict(float)
    matched_terms_map = defaultdict(list)

    for term in query_tokens:
        postings = inverted_index.get(term, [])
        idf_val = idf.get(term, 0)
        for doc_idx, tf in postings:
            # TF归一化: tf / doc_length
            tf_normalized = tf / max(doc_lengths[doc_idx], 1)
            # 法规层级权重
            reg = regulation_database[doc_idx]
            level = reg.get("level", "其他")
            level_weight = level_weights.get(level, 1.0)

            score = tf_normalized * idf_val * level_weight
            scores[doc_idx] += score
            matched_terms_map[doc_idx].append(term)

    # 步骤5: 短语匹配加分
    if len(query_tokens) > 1:
        query_phrase = "".join(query_tokens)
        for doc_idx, reg in enumerate(regulation_database):
            full_text = reg.get("title", "") + reg.get("content", "")
            if query_phrase in full_text:
                scores[doc_idx] *= 1.5  # 短语匹配50%加分

    # 步骤6: 排序并生成结果
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

    results = []
    for doc_idx, score in ranked:
        reg = regulation_database[doc_idx]
        content = reg.get("content", "")
        # 生成摘要片段
        snippet = content[:150] + "..." if len(content) > 150 else content
        # 匹配词高亮
        for term in matched_terms_map[doc_idx]:
            snippet = snippet.replace(term, f"【{term}】")

        results.append({
            "doc_id": reg.get("id"),
            "title": reg.get("title"),
            "level": reg.get("level", "其他"),
            "score": round(score, 4),
            "matched_terms": list(set(matched_terms_map[doc_idx])),
            "match_count": len(set(matched_terms_map[doc_idx])),
            "snippet": snippet
        })

    return results


# ---------------------------------------------------------------------------
# 3. 风险评估模型
# ---------------------------------------------------------------------------
def risk_assessment_model(factors, weights, thresholds):
    """
    风险评估模型：多因子风险评分 + 非线性变换 + 5级分类。

    算法原理:
        - 加权求和: R = Σ(wi * fi)，fi为因子值，wi为权重
        - 非线性变换: 对每个因子应用sigmoid变换 f'(x) = 1/(1+exp(-k*(x-x0)))
          将原始值映射到0-1区间，放大临界区域敏感度
        - 5级分类: 低/中低/中/中高/高，基于阈值划分
        - 风险矩阵: 二维风险矩阵(可能性 x 影响)

    参数:
        factors (dict): 风险因子键值对 {factor_name: value}
        weights (dict): 因子权重 {factor_name: weight}
        thresholds (dict): 风险等级阈值 {level: (min, max)}

    返回:
        dict: 风险评估结果，含total_score、risk_level、risk_matrix、recommendations。
    """
    # 步骤1: 非线性变换（sigmoid）
    transformed_factors = {}
    for name, value in factors.items():
        # 假设值域0-10，中值5，灵敏度k=0.5
        k = 0.5
        x0 = 5.0
        transformed = 1 / (1 + math.exp(-k * (value - x0)))
        # 缩放回0-10
        transformed_factors[name] = transformed * 10

    # 步骤2: 加权求和
    total_weight = sum(weights.values())
    if total_weight == 0:
        total_weight = 1
    weighted_score = sum(transformed_factors.get(name, 0) * weights.get(name, 0) for name in factors) / total_weight * 10

    # 步骤3: 风险等级分类
    risk_levels = [
        ("低", (0, 2)),
        ("中低", (2, 4)),
        ("中", (4, 6)),
        ("中高", (6, 8)),
        ("高", (8, 10))
    ]
    risk_level = "中"
    for level, (lo, hi) in risk_levels:
        if lo <= weighted_score < hi:
            risk_level = level
            break
    if weighted_score >= 10:
        risk_level = "高"

    # 步骤4: 风险矩阵（可能性 x 影响）
    # 将因子分为可能性因子和影响因子
    likelihood_factors = {k: v for k, v in transformed_factors.items() if "频率" in k or "概率" in k or "可能性" in k}
    impact_factors = {k: v for k, v in transformed_factors.items() if k not in likelihood_factors}

    likelihood = sum(likelihood_factors.values()) / max(len(likelihood_factors), 1) if likelihood_factors else weighted_score / 2
    impact = sum(impact_factors.values()) / max(len(impact_factors), 1) if impact_factors else weighted_score / 2

    # 矩阵位置 (1-5 x 1-5)
    matrix_likelihood = min(5, max(1, int(likelihood / 2) + 1))
    matrix_impact = min(5, max(1, int(impact / 2) + 1))
    matrix_score = matrix_likelihood * matrix_impact

    # 步骤5: 处置建议
    recommendations = []
    if risk_level in ("高", "中高"):
        recommendations.append("立即启动风险缓解措施，指定责任人")
        recommendations.append("定期（每周）复查风险因子变化")
    if risk_level in ("中",):
        recommendations.append("制定风险监控计划，每月评估")
    if risk_level in ("低", "中低"):
        recommendations.append("保持常规监控，季度复核")

    # 高风险因子识别
    high_risk_factors = []
    for name, value in transformed_factors.items():
        if value >= 7:
            high_risk_factors.append({"factor": name, "value": round(value, 2), "weight": weights.get(name, 0)})

    return {
        "total_score": round(weighted_score, 2),
        "risk_level": risk_level,
        "risk_matrix": {
            "likelihood": round(likelihood, 2),
            "impact": round(impact, 2),
            "matrix_position": f"{matrix_likelihood}x{matrix_impact}",
            "matrix_score": matrix_score
        },
        "factors_detail": {
            name: {
                "raw_value": factors[name],
                "transformed": round(transformed_factors[name], 2),
                "weight": weights.get(name, 0),
                "contribution": round(transformed_factors[name] * weights.get(name, 0) / total_weight * 10, 2)
            } for name in factors
        },
        "high_risk_factors": high_risk_factors,
        "recommendations": recommendations
    }


# ---------------------------------------------------------------------------
# 4. 合规清单生成器
# ---------------------------------------------------------------------------
def compliance_checklist_generator(industry, regulations, company_profile):
    """
    合规清单生成器：基于行业+法规+公司特征生成结构化合规检查清单。

    算法原理:
        - 行业匹配: 根据行业类型匹配适用法规
        - 规模筛选: 根据公司规模(人数/营收)调整检查项
        - 检查项生成: 从法规条目提取检查要求，分配检查频次/责任人/风险等级
        - 优先级排序: 按风险等级和法规层级排序

    参数:
        industry (str): 行业类型
        regulations (list[dict]): 法规列表，含name, level, requirements
        company_profile (dict): 公司特征 {size, revenue, has_personal_data, ...}

    返回:
        dict: 合规检查清单，含checklist、summary、priority_distribution。
    """
    # 检查频次模板
    frequency_map = {
        "高": "每月", "中高": "每季度", "中": "每半年", "低": "每年"
    }

    # 步骤1: 筛选适用法规
    applicable_regs = []
    for reg in regulations:
        applicable = True
        # 行业过滤
        reg_industries = reg.get("industries", [])
        if reg_industries and industry not in reg_industries:
            applicable = False
        # 规模过滤
        min_size = reg.get("min_company_size", 0)
        if company_profile.get("size", 0) < min_size:
            applicable = False
        if applicable:
            applicable_regs.append(reg)

    # 步骤2: 生成检查项
    checklist = []
    for reg in applicable_regs:
        reg_name = reg.get("name", "")
        reg_level = reg.get("level", "其他")
        requirements = reg.get("requirements", [])

        for req in requirements:
            # 风险等级评估
            risk_keywords = {"禁止": "高", "必须": "高", "应当": "中高", "不得": "高", "可以": "低"}
            risk_level = "中"
            for keyword, level in risk_keywords.items():
                if keyword in req:
                    risk_level = level
                    break

            # 检查频次
            frequency = frequency_map.get(risk_level, "每半年")

            # 责任人分配
            if "数据" in req or "隐私" in req:
                responsible = "数据保护官"
            elif "财务" in req or "税务" in req:
                responsible = "财务负责人"
            elif "安全" in req:
                responsible = "安全负责人"
            elif "人事" in req or "劳动" in req:
                responsible = "HR负责人"
            else:
                responsible = "合规专员"

            checklist.append({
                "id": f"CHK-{len(checklist)+1:03d}",
                "regulation": reg_name,
                "regulation_level": reg_level,
                "requirement": req,
                "risk_level": risk_level,
                "frequency": frequency,
                "responsible": responsible,
                "status": "待检查",
                "industry": industry
            })

    # 步骤3: 优先级排序
    risk_order = {"高": 0, "中高": 1, "中": 2, "中低": 3, "低": 4}
    checklist.sort(key=lambda x: risk_order.get(x["risk_level"], 5))

    # 步骤4: 统计
    priority_dist = defaultdict(int)
    for item in checklist:
        priority_dist[item["risk_level"]] += 1

    return {
        "industry": industry,
        "company_profile": company_profile,
        "checklist": checklist,
        "summary": {
            "total_items": len(checklist),
            "applicable_regulations": len(applicable_regs),
            "priority_distribution": dict(priority_dist),
            "high_risk_items": priority_dist.get("高", 0)
        }
    }


# ---------------------------------------------------------------------------
# 5. 隐私影响评估 (PIA)
# ---------------------------------------------------------------------------
def privacy_impact_assessment(data_processing_activities):
    """
    隐私影响评估(PIA)：分析数据处理活动并识别隐私风险。

    算法原理:
        - 风险识别: 4维度评估（数据最小化/目的限制/存储限制/安全性）
        - 风险评分: 每维度0-10分，加权汇总
        - 风险等级: 低/中/高/极高
        - 缓解措施: 基于风险类型自动推荐

    参数:
        data_processing_activities (list[dict]): 数据处理活动列表，每条含
            activity_name, data_types, purpose, retention_period, recipients, security_measures

    返回:
        dict: PIA评估结果，含risk_assessment、risk_level、mitigation_measures、recommendations。
    """
    # 敏感数据类型
    sensitive_types = {"身份证号", "银行卡号", "健康信息", "生物特征", "种族", "宗教信仰", "政治观点", "性取向", "犯罪记录"}

    all_risks = []
    total_risk_score = 0

    for activity in data_processing_activities:
        data_types = set(activity.get("data_types", []))
        purpose = activity.get("purpose", "")
        retention = activity.get("retention_period", "")
        recipients = activity.get("recipients", [])
        security = activity.get("security_measures", [])

        risks = []

        # 维度1: 数据最小化评估
        collected_types = len(data_types)
        sensitive_count = len(data_types & sensitive_types)
        if collected_types > 5:
            risks.append({"dimension": "数据最小化", "risk": "收集数据类型过多", "score": 7, "level": "中高"})
        if sensitive_count > 0:
            risks.append({"dimension": "数据最小化", "risk": f"涉及{sensitive_count}类敏感数据", "score": 9, "level": "高"})

        # 维度2: 目的限制评估
        if not purpose or len(purpose) < 10:
            risks.append({"dimension": "目的限制", "risk": "处理目的不明确", "score": 8, "level": "高"})
        elif "其他" in purpose or "等" in purpose:
            risks.append({"dimension": "目的限制", "risk": "处理目的过于宽泛", "score": 6, "level": "中高"})

        # 维度3: 存储限制评估
        if not retention:
            risks.append({"dimension": "存储限制", "risk": "未明确数据保留期限", "score": 8, "level": "高"})
        else:
            # 解析保留期限
            if "永久" in retention or "无限期" in retention:
                risks.append({"dimension": "存储限制", "risk": "数据永久保留，无删除机制", "score": 9, "level": "高"})
            elif "年" in retention:
                years = re.findall(r'(\d+)\s*年', retention)
                if years and int(years[0]) > 5:
                    risks.append({"dimension": "存储限制", "risk": f"保留期限过长({years[0]}年)", "score": 6, "level": "中高"})

        # 维度4: 安全性评估
        security_count = len(security)
        required_measures = ["加密", "访问控制", "审计日志", "备份"]
        missing_measures = [m for m in required_measures if not any(m in s for s in security)]
        if len(missing_measures) >= 2:
            risks.append({"dimension": "安全性", "risk": f"缺少{len(missing_measures)}项安全措施", "score": 8, "level": "高"})
        elif len(missing_measures) == 1:
            risks.append({"dimension": "安全性", "risk": f"缺少安全措施: {missing_measures[0]}", "score": 5, "level": "中"})

        # 维度5: 数据共享评估
        if len(recipients) > 3:
            risks.append({"dimension": "数据共享", "risk": f"数据共享方过多({len(recipients)}个)", "score": 6, "level": "中高"})
        if any("境外" in r for r in recipients):
            risks.append({"dimension": "数据共享", "risk": "涉及跨境数据传输", "score": 9, "level": "高"})

        activity_score = max(r["score"] for r in risks) if risks else 2
        total_risk_score = max(total_risk_score, activity_score)

        all_risks.append({
            "activity": activity.get("activity_name", ""),
            "risks": risks,
            "risk_score": activity_score
        })

    # 总体风险等级
    if total_risk_score >= 8:
        overall_level = "极高"
    elif total_risk_score >= 6:
        overall_level = "高"
    elif total_risk_score >= 4:
        overall_level = "中"
    else:
        overall_level = "低"

    # 缓解措施推荐
    mitigation_measures = []
    for risk_activity in all_risks:
        for risk in risk_activity["risks"]:
            if risk["level"] in ("高",):
                if "敏感数据" in risk["risk"]:
                    mitigation_measures.append(f"对敏感数据进行加密脱敏处理（{risk_activity['activity']}）")
                if "保留期限" in risk["risk"]:
                    mitigation_measures.append(f"制定数据保留和删除策略（{risk_activity['activity']}）")
                if "跨境" in risk["risk"]:
                    mitigation_measures.append(f"完成跨境数据传输安全评估（{risk_activity['activity']}）")
                if "安全措施" in risk["risk"]:
                    mitigation_measures.append(f"补充缺失的安全控制措施（{risk_activity['activity']}）")

    return {
        "risk_assessment": all_risks,
        "overall_risk_score": total_risk_score,
        "risk_level": overall_level,
        "mitigation_measures": list(set(mitigation_measures)),
        "recommendations": [
            "建议每半年进行一次PIA复查" if overall_level in ("低", "中") else "建议立即实施风险缓解措施并在3个月内复查",
            "确保所有数据处理活动都有明确的法律依据",
            "建立数据主体权利响应机制"
        ],
        "requires_dpa_notification": overall_level in ("极高", "高")
    }


# ---------------------------------------------------------------------------
# 6. 数据脱敏器 (K-匿名/L-多样性/T-接近性)
# ---------------------------------------------------------------------------
def data_anonymizer(data, methods, sensitive_fields):
    """
    数据脱敏器：支持K-匿名、L-多样性、T-接近性三种匿名化模型。

    算法原理:
        - K-匿名: 通过泛化(Generalization)和抑制(Suppression)使每条记录
          至少与K-1条其他记录在准标识符上无法区分
        - L-多样性: 在K-匿名基础上，每个等价类中敏感属性至少有L个不同值
        - T-接近性: 每个等价类中敏感属性分布与全局分布的距离不超过T
          (使用EMD Earth Mover's Distance度量)

    参数:
        data (list[dict]): 原始数据记录列表
        methods (dict): 脱敏方法配置 {k: 5, l: 3, t: 0.2, generalize_fields: [...]}
        sensitive_fields (list[str]): 敏感字段列表

    返回:
        dict: 脱敏结果，含anonymized_data、anonymization_report、privacy_metrics。
    """
    if not data:
        return {"error": "No data to anonymize"}

    k = methods.get("k", 5)
    l = methods.get("l", 3)
    t_threshold = methods.get("t", 0.2)
    generalize_fields = methods.get("generalize_fields", [])

    # 步骤1: 泛化处理（将精确值替换为区间/类别）
    anonymized = []
    for record in data:
        new_record = record.copy()
        for field in generalize_fields:
            if field in new_record:
                val = new_record[field]
                # 年龄泛化为5岁区间
                if field == "age" or field == "年龄":
                    try:
                        age = int(val)
                        new_record[field] = f"{age // 5 * 5}-{age // 5 * 5 + 4}"
                    except (ValueError, TypeError):
                        pass
                # 邮编泛化为前3位
                elif field == "zipcode" or field == "邮编":
                    sval = str(val)
                    if len(sval) >= 3:
                        new_record[field] = sval[:3] + "***"
                # 其他字段泛化为前缀
                else:
                    sval = str(val)
                    if len(sval) > 2:
                        new_record[field] = sval[:2] + "*"
        anonymized.append(new_record)

    # 步骤2: 构建等价类（准标识符相同的记录分组）
    quasi_identifiers = generalize_fields
    equivalence_classes = defaultdict(list)
    for record in anonymized:
        key = tuple(str(record.get(qi, "")) for qi in quasi_identifiers)
        equivalence_classes[key].append(record)

    # 步骤3: K-匿名验证
    k_violations = []
    for key, group in equivalence_classes.items():
        if len(group) < k:
            k_violations.append({"quasi_identifier": key, "group_size": len(group)})

    # 步骤4: 抑制处理（不满足K-匿名的记录，抑制准标识符）
    suppressed_count = 0
    for key, group in equivalence_classes.items():
        if len(group) < k:
            for record in group:
                for qi in quasi_identifiers:
                    record[qi] = "*"
                suppressed_count += 1

    # 步骤5: L-多样性验证
    l_violations = []
    for key, group in equivalence_classes.items():
        for sf in sensitive_fields:
            values = set(str(r.get(sf, "")) for r in group)
            if len(values) < l:
                l_violations.append({
                    "quasi_identifier": key,
                    "sensitive_field": sf,
                    "distinct_values": len(values)
                })

    # 步骤6: T-接近性验证（使用EMD简化版）
    # 全局敏感属性分布
    global_dist = defaultdict(float)
    total_records = len(anonymized)
    for sf in sensitive_fields:
        sf_values = [str(r.get(sf, "")) for r in anonymized]
        value_counts = Counter(sf_values)
        for val, count in value_counts.items():
            global_dist[(sf, val)] = count / total_records

    t_violations = []
    for key, group in equivalence_classes.items():
        for sf in sensitive_fields:
            sf_values = [str(r.get(sf, "")) for r in group]
            group_dist = Counter(sf_values)
            group_size = len(group)

            # 计算EMD简化版（分布距离）
            all_values = set(list(global_dist.keys()) + [(sf, v) for v in sf_values])
            emd = 0
            for val_key in all_values:
                if val_key[0] == sf:
                    global_p = global_dist.get(val_key, 0)
                    local_p = group_dist.get(val_key[1], 0) / group_size if group_size > 0 else 0
                    emd += abs(global_p - local_p)
            emd /= 2  # EMD = 总变差 / 2

            if emd > t_threshold:
                t_violations.append({
                    "quasi_identifier": key,
                    "sensitive_field": sf,
                    "emd": round(emd, 4)
                })

    # 步骤7: 隐私度量
    privacy_metrics = {
        "k_anonymity": {
            "k_value": k,
            "satisfied": len(k_violations) == 0,
            "violations": len(k_violations),
            "suppressed_records": suppressed_count
        },
        "l_diversity": {
            "l_value": l,
            "satisfied": len(l_violations) == 0,
            "violations": len(l_violations)
        },
        "t_closeness": {
            "t_threshold": t_threshold,
            "satisfied": len(t_violations) == 0,
            "violations": len(t_violations)
        },
        "equivalence_classes": len(equivalence_classes),
        "avg_class_size": round(total_records / max(len(equivalence_classes), 1), 1),
        "information_loss": round(suppressed_count / max(total_records, 1) * 100, 1)
    }

    return {
        "anonymized_data": anonymized,
        "anonymization_report": {
            "methods_applied": list(methods.keys()),
            "generalized_fields": generalize_fields,
            "suppressed_count": suppressed_count,
            "total_records": total_records
        },
        "privacy_metrics": privacy_metrics,
        "violations": {
            "k_anonymity": k_violations[:5],
            "l_diversity": l_violations[:5],
            "t_closeness": t_violations[:5]
        }
    }


# ---------------------------------------------------------------------------
# 7. 法规术语解释器
# ---------------------------------------------------------------------------
def regulatory_term_explainer(term, context):
    """
    法规术语解释器：基于术语词典+上下文分析提供解释。

    算法原理:
        - 术语词典: 内置法律术语知识库
        - 上下文消歧: 同一术语在不同上下文中有不同含义
        - 相关法规引用: 关联适用的法律法规

    参数:
        term (str): 待解释的术语
        context (str): 上下文文本

    返回:
        dict: 术语解释，含definition、applicable_scenarios、related_regulations、context_analysis。
    """
    # 术语知识库
    term_database = {
        "个人信息": {
            "definition": "以电子或者其他方式记录的与已识别或者可识别的自然人有关的各种信息，不包括匿名化处理后的信息。",
            "scenarios": ["数据处理", "隐私保护", "数据安全"],
            "related_laws": ["个人信息保护法", "民法典", "网络安全法"],
            "key_points": ["可识别性是核心特征", "匿名化处理后不再属于个人信息"]
        },
        "敏感个人信息": {
            "definition": "一旦泄露或者非法使用，容易导致自然人的人格尊严受到侵害或者人身、财产安全受到危害的个人信息。",
            "scenarios": ["数据分类分级", "特殊保护", "风险评估"],
            "related_laws": ["个人信息保护法第28条", "数据安全法"],
            "key_points": ["包括生物识别、宗教信仰、特定身份、医疗健康、金融账户、行踪轨迹等", "需取得单独同意"]
        },
        "数据出境": {
            "definition": "将在中华人民共和国境内收集和产生的个人信息和重要数据，传输、存储到中华人民共和国境外。",
            "scenarios": ["跨境数据传输", "国际业务", "数据本地化"],
            "related_laws": ["个人信息保护法第38-40条", "数据出境安全评估办法", "网络安全法第37条"],
            "key_points": ["需通过安全评估或认证", "关键信息基础设施运营者有特殊要求"]
        },
        "匿名化": {
            "definition": "个人信息经过处理无法识别特定自然人且不能复原的过程。",
            "scenarios": ["数据发布", "统计分析", "数据共享"],
            "related_laws": ["个人信息保护法第73条"],
            "key_points": ["不可逆性是关键", "匿名化后数据不再受个保法约束"]
        },
        "最小必要原则": {
            "definition": "处理个人信息应当具有明确、合理的目的，并与处理目的直接相关，采取对个人权益影响最小的方式。",
            "scenarios": ["数据收集", "产品设计", "合规审计"],
            "related_laws": ["个人信息保护法第6条", "数据安全法"],
            "key_points": ["目的明确", "方式最小影响", "收集范围最小化"]
        },
        "数据安全": {
            "definition": "通过采取必要措施，确保数据处于有效保护和合法利用的状态，以及具备保障持续安全状态的能力。",
            "scenarios": ["数据管理", "安全防护", "合规建设"],
            "related_laws": ["数据安全法第3条", "网络安全法"],
            "key_points": ["包括数据收集、存储、使用、加工、传输、提供、公开等全生命周期安全"]
        },
        "算法推荐": {
            "definition": "利用生成合成类、个性化推送类、排序精选类、检索过滤类等算法技术向用户提供信息的服务。",
            "scenarios": ["互联网信息服务", "个性化推荐", "信息过滤"],
            "related_laws": ["互联网信息服务算法推荐管理规定", "电子商务法"],
            "key_points": ["需提供关闭选项", "不得利用算法实施差别待遇"]
        }
    }

    # 模糊匹配
    matched_term = None
    for db_term, info in term_database.items():
        if term in db_term or db_term in term:
            matched_term = db_term
            break

    if not matched_term:
        # 基于上下文推断
        if any(kw in context for kw in ["数据", "处理", "收集"]):
            matched_term = "个人信息"
        elif any(kw in context for kw in ["跨境", "境外", "传输"]):
            matched_term = "数据出境"
        else:
            return {
                "term": term,
                "definition": f"术语'{term}'不在内置知识库中，建议查阅相关法律法规原文。",
                "applicable_scenarios": [],
                "related_regulations": [],
                "context_analysis": f"上下文中未找到明确关联。",
                "in_database": False
            }

    term_info = term_database[matched_term]

    # 上下文分析
    context_analysis = []
    for scenario in term_info["scenarios"]:
        if scenario in context or any(kw in context for kw in scenario):
            context_analysis.append(f"上下文中涉及'{scenario}'场景")

    for law in term_info["related_laws"]:
        if law.split("第")[0] in context:
            context_analysis.append(f"上下文中引用了相关法规：{law}")

    return {
        "term": matched_term,
        "query_term": term,
        "definition": term_info["definition"],
        "applicable_scenarios": term_info["scenarios"],
        "related_regulations": term_info["related_laws"],
        "key_points": term_info["key_points"],
        "context_analysis": context_analysis if context_analysis else ["上下文中未检测到直接关联的场景"],
        "in_database": True
    }


# ---------------------------------------------------------------------------
# 8. 合规条款生成器
# ---------------------------------------------------------------------------
def clause_generator(clause_type, parameters, jurisdiction):
    """
    合规条款生成器：基于模板引擎+参数填充生成合同条款。

    算法原理:
        - 模板引擎: 条件渲染 + 参数插值
        - 法律条款库: 按条款类型和管辖区域组织模板
        - 参数验证: 必填参数检查 + 类型验证

    参数:
        clause_type (str): 条款类型 "confidentiality"/"breach"/"force_majeure"/"ip"/"dispute"
        parameters (dict): 条款参数
        jurisdiction (str): 管辖区 "CN"/"US"/"EU"

    返回:
        dict: 生成的条款，含clause_text、legal_basis、notes。
    """
    # 条款模板库
    templates = {
        "confidentiality": {
            "template": """第X条 保密条款

1. 保密信息定义
双方确认，在本合同履行过程中，{disclosing_party}向{receiving_party}披露的以下信息属于保密信息：
(1) 技术信息：包括但不限于{tech_info}；
(2) 商业信息：包括但不限于{business_info}；
(3) 其他标记为"保密"的信息。

2. 保密义务
{receiving_party}承诺：
(1) 对保密信息予以严格保密，不得向{authorized_personnel_limit}以外的第三方披露；
(2) 仅将保密信息用于本合同约定的目的；
(3) 采取不低于保护其自身保密信息的标准的安全措施。

3. 保密期限
本条保密义务在合同终止后{retention_years}年内持续有效。

4. 违约责任
如{receiving_party}违反本条保密义务，应向{disclosing_party}支付违约金人民币{penalty_amount}元，
并赔偿因此造成的全部损失。""",
            "required_params": ["disclosing_party", "receiving_party", "retention_years", "penalty_amount"],
            "optional_params": ["tech_info", "business_info", "authorized_personnel_limit"],
            "legal_basis": ["合同法第43条", "反不正当竞争法第9条"]
        },
        "breach": {
            "template": """第X条 违约责任

1. 一般违约
任何一方违反本合同约定的义务，应承担违约责任，并赔偿对方因此遭受的损失。

2. 违约金
如{breaching_party}未按约履行义务，应向{non_breaching_party}支付违约金，
金额为合同总价的{penalty_percentage}%，即人民币{penalty_amount}元。

3. 继续履行
支付违约金并不免除{breaching_party}继续履行合同的义务。

4. 解除权
如一方严重违约导致合同目的无法实现，{non_breaching_party}有权解除合同，
并要求违约方赔偿全部损失。""",
            "required_params": ["breaching_party", "non_breaching_party", "penalty_percentage", "penalty_amount"],
            "optional_params": [],
            "legal_basis": ["民法典第577条", "民法典第585条"]
        },
        "force_majeure": {
            "template": """第X条 不可抗力

1. 定义
不可抗力是指不能预见、不能避免且不能克服的客观情况，包括但不限于：
自然灾害（地震、洪水、台风等）、战争、武装冲突、罢工、政府行为、{additional_events}。

2. 通知义务
如一方因不可抗力无法履行合同义务，应在不可抗力发生后{notice_days}日内书面通知对方，
并提供相关证明文件。

3. 豁免
因不可抗力导致合同无法履行的，遭受不可抗力的一方部分或全部免除责任，
但应在不可抗力消除后{resume_days}日内恢复履行。

4. 合同变更或解除
如不可抗力持续超过{termination_days}日，双方可协商变更或解除合同。""",
            "required_params": ["notice_days", "resume_days", "termination_days"],
            "optional_params": ["additional_events"],
            "legal_basis": ["民法典第590条"]
        },
        "ip": {
            "template": """第X条 知识产权

1. 原有知识产权
双方各自在合同签订前已拥有的知识产权，其所有权不因本合同的签订和履行而转移。

2. 新生知识产权
在合同履行过程中产生的{ip_type}，其知识产权归属如下：
(1) {party_a}独立完成的，归{party_a}所有；
(2) 双方合作完成的，由双方共有，各占{ownership_split}。

3. 授权
{ip_owner}授予{ip_user}在{license_scope}范围内使用相关知识产权的非独占、不可转让的许可。

4. 侵权处理
如因使用本合同项下的知识产权侵犯第三方权益，由{infringement_responsible}承担全部责任。""",
            "required_params": ["ip_type", "party_a", "ownership_split", "ip_owner", "ip_user", "license_scope", "infringement_responsible"],
            "optional_params": [],
            "legal_basis": ["民法典第123条", "专利法", "著作权法"]
        },
        "dispute": {
            "template": """第X条 争议解决

1. 协商
因本合同引起的或与本合同有关的任何争议，双方应首先通过友好协商解决。

2. 调解
协商不成的，双方可向{mediation_org}申请调解。

3. {dispute_method}
如调解不成，双方同意按以下方式解决：
(1) 向{court_name}提起诉讼；或
(2) 将争议提交{arbitration_org}，按照其届时有效的仲裁规则在{arbitration_place}进行仲裁。
仲裁裁决为终局裁决，对双方均有约束力。

4. 适用法律
本合同的订立、效力、解释、履行和争议解决均适用{applicable_law}。""",
            "required_params": ["dispute_method", "applicable_law"],
            "optional_params": ["mediation_org", "court_name", "arbitration_org", "arbitration_place"],
            "legal_basis": ["民事诉讼法", "仲裁法"]
        }
    }

    # 管辖区适配
    jurisdiction_config = {
        "CN": {"applicable_law": "中华人民共和国法律", "arbitration_default": "中国国际经济贸易仲裁委员会"},
        "US": {"applicable_law": "适用美国相关州法律", "arbitration_default": "美国仲裁协会(AAA)"},
        "EU": {"applicable_law": "适用欧盟相关法规", "arbitration_default": "国际商会仲裁院(ICC)"}
    }
    jur_config = jurisdiction_config.get(jurisdiction, jurisdiction_config["CN"])

    if clause_type not in templates:
        return {"error": f"Unsupported clause type: {clause_type}", "supported_types": list(templates.keys())}

    template_info = templates[clause_type]
    template = template_info["template"]
    required = template_info["required_params"]
    optional = template_info.get("optional_params", [])

    # 参数验证
    missing_params = [p for p in required if p not in parameters or not parameters[p]]
    if missing_params:
        return {
            "error": "Missing required parameters",
            "missing_params": missing_params,
            "required_params": required
        }

    # 参数填充
    fill_params = {}
    for p in required + optional:
        if p in parameters and parameters[p]:
            fill_params[p] = str(parameters[p])
        else:
            # 默认值
            defaults = {
                "tech_info": "源代码、技术文档、设计图纸",
                "business_info": "客户信息、定价策略、商业计划",
                "authorized_personnel_limit": "需要知情的员工",
                "additional_events": "传染病疫情",
                "mediation_org": "当地商事调解中心",
                "court_name": "合同签订地有管辖权的人民法院",
                "arbitration_org": jur_config["arbitration_default"],
                "arbitration_place": "北京",
                "applicable_law": jur_config["applicable_law"],
                "dispute_method": "仲裁"
            }
            fill_params[p] = defaults.get(p, "【待填写】")

    # 渲染模板
    clause_text = template
    for key, value in fill_params.items():
        clause_text = clause_text.replace("{" + key + "}", value)

    return {
        "clause_type": clause_type,
        "jurisdiction": jurisdiction,
        "clause_text": clause_text,
        "legal_basis": template_info["legal_basis"],
        "notes": [
            "本条款由系统自动生成，建议经法律专业人士审核后使用",
            f"管辖区适用规则: {jur_config['applicable_law']}",
            f"必填参数: {', '.join(required)}"
        ],
        "parameters_used": fill_params
    }


# ---------------------------------------------------------------------------
# 9. 合规义务追踪器
# ---------------------------------------------------------------------------
def obligation_tracker(obligations, deadline, status):
    """
    合规义务追踪器：管理合规义务并自动计算紧急程度。

    算法原理:
        - 紧急度计算: 基于剩余天数/逾期天数的指数衰减模型
          urgency = exp(-days_remaining / tau)，tau=30天时间常数
        - 优先级排序: 紧急度 * 风险权重 * 状态权重
        - SLA监控: 逾期自动升级优先级

    参数:
        obligations (list[dict]): 义务列表，每条含name, deadline, responsible, risk_level
        deadline (str): 当前参考日期 "YYYY-MM-DD"
        status (str): 状态过滤器 "all"/"overdue"/"upcoming"/"completed"

    返回:
        dict: 义务追踪结果，含tracked_obligations、summary、alerts。
    """
    current_date = datetime.strptime(deadline, "%Y-%m-%d")

    # 风险权重
    risk_weights = {"高": 3.0, "中高": 2.0, "中": 1.5, "低": 1.0}
    # 状态权重
    status_weights = {"未开始": 1.0, "进行中": 0.8, "已完成": 0.1, "已逾期": 1.5}

    tracked = []
    for obligation in obligations:
        obl_deadline_str = obligation.get("deadline", deadline)
        obl_deadline = datetime.strptime(obl_deadline_str, "%Y-%m-%d")
        days_remaining = (obl_deadline - current_date).days

        # 计算紧急度（指数衰减模型）
        tau = 30  # 时间常数
        if days_remaining < 0:
            urgency = 1.0  # 已逾期，最大紧急度
            days_status = f"逾期{abs(days_remaining)}天"
            obl_status = "已逾期"
        elif days_remaining == 0:
            urgency = 1.0
            days_status = "今日到期"
            obl_status = obligation.get("status", "进行中")
        else:
            urgency = math.exp(-days_remaining / tau)
            days_status = f"剩余{days_remaining}天"
            obl_status = obligation.get("status", "未开始")

        # 优先级 = 紧急度 * 风险权重 * 状态权重
        risk_weight = risk_weights.get(obligation.get("risk_level", "中"), 1.5)
        status_weight = status_weights.get(obl_status, 1.0)
        priority_score = urgency * risk_weight * status_weight

        # 优先级等级
        if priority_score >= 2.0:
            priority = "P0-紧急"
        elif priority_score >= 1.0:
            priority = "P1-高"
        elif priority_score >= 0.5:
            priority = "P2-中"
        else:
            priority = "P3-低"

        tracked.append({
            "name": obligation.get("name", ""),
            "deadline": obl_deadline_str,
            "responsible": obligation.get("responsible", "未指定"),
            "risk_level": obligation.get("risk_level", "中"),
            "status": obl_status,
            "days_remaining": days_remaining,
            "days_status": days_status,
            "urgency_score": round(urgency, 4),
            "priority_score": round(priority_score, 4),
            "priority": priority,
            "is_overdue": days_remaining < 0
        })

    # 状态过滤
    if status == "overdue":
        tracked = [t for t in tracked if t["is_overdue"]]
    elif status == "upcoming":
        tracked = [t for t in tracked if not t["is_overdue"] and t["status"] != "已完成"]
    elif status == "completed":
        tracked = [t for t in tracked if t["status"] == "已完成"]

    # 优先级排序
    tracked.sort(key=lambda x: -x["priority_score"])

    # 统计
    overdue_count = sum(1 for t in tracked if t["is_overdue"])
    upcoming_7days = sum(1 for t in tracked if 0 <= t["days_remaining"] <= 7)
    completed_count = sum(1 for t in tracked if t["status"] == "已完成")

    # 告警
    alerts = []
    for t in tracked:
        if t["is_overdue"]:
            alerts.append({"type": "逾期", "message": f"'{t['name']}'已逾期{abs(t['days_remaining'])}天", "priority": t["priority"]})
        elif t["days_remaining"] <= 3 and t["status"] != "已完成":
            alerts.append({"type": "即将到期", "message": f"'{t['name']}'将在{t['days_remaining']}天内到期", "priority": t["priority"]})

    return {
        "current_date": deadline,
        "tracked_obligations": tracked,
        "summary": {
            "total": len(tracked),
            "overdue": overdue_count,
            "upcoming_7days": upcoming_7days,
            "completed": completed_count,
            "completion_rate": round(completed_count / max(len(tracked), 1) * 100, 1)
        },
        "alerts": alerts[:10]
    }


# ---------------------------------------------------------------------------
# 10. 合规报告生成器
# ---------------------------------------------------------------------------
def compliance_report_generator(audit_results, format='markdown'):
    """
    合规报告生成器：汇总审计结果生成结构化合规报告。

    算法原理:
        - 数据聚合: 按类型/严重度/状态分组统计
        - 风险评分: 加权汇总各审计项风险分
        - 报告模板: 执行摘要 -> 合规状态 -> 违规详情 -> 整改建议 -> 风险评估
        - 格式化: Markdown/HTML双格式输出

    参数:
        audit_results (list[dict]): 审计结果列表，每条含category, severity, status, description, recommendation
        format (str): 输出格式 "markdown"/"html"

    返回:
        dict: 报告生成结果，含report_text、summary、statistics。
    """
    # 步骤1: 数据聚合
    total = len(audit_results)
    by_category = defaultdict(list)
    by_severity = defaultdict(int)
    by_status = defaultdict(int)

    severity_weights = {"严重": 10, "高": 7, "中": 4, "低": 1}
    total_risk_score = 0

    for result in audit_results:
        cat = result.get("category", "其他")
        sev = result.get("severity", "低")
        stat = result.get("status", "待处理")

        by_category[cat].append(result)
        by_severity[sev] += 1
        by_status[stat] += 1
        total_risk_score += severity_weights.get(sev, 1)

    # 步骤2: 整体合规状态评估
    compliance_rate = by_status.get("合规", 0) / max(total, 1) * 100
    non_compliant = by_status.get("不合规", 0) + by_status.get("违规", 0)

    if compliance_rate >= 90:
        overall_status = "优秀"
    elif compliance_rate >= 75:
        overall_status = "良好"
    elif compliance_rate >= 60:
        overall_status = "需改进"
    else:
        overall_status = "不合格"

    avg_risk = total_risk_score / max(total, 1)
    if avg_risk >= 7:
        risk_level = "高"
    elif avg_risk >= 4:
        risk_level = "中"
    else:
        risk_level = "低"

    # 步骤3: 生成报告内容
    report_date = datetime.now().strftime("%Y-%m-%d %H:%M")

    if format == 'markdown':
        lines = [
            f"# 合规审计报告",
            f"",
            f"**报告日期**: {report_date}",
            f"**审计项总数**: {total}",
            f"**整体合规状态**: {overall_status}",
            f"**合规率**: {compliance_rate:.1f}%",
            f"**风险等级**: {risk_level}",
            f"",
            f"---",
            f"",
            f"## 1. 执行摘要",
            f"",
            f"本次合规审计共检查 **{total}** 个审计项，其中：",
            f"- 合规: {by_status.get('合规', 0)} 项",
            f"- 待整改: {by_status.get('待处理', 0)} 项",
            f"- 不合规: {non_compliant} 项",
            f"- 风险总分: {total_risk_score} (平均: {avg_risk:.1f})",
            f"",
            f"## 2. 合规状态分布",
            f"",
            f"| 状态 | 数量 | 占比 |",
            f"|------|------|------|",
        ]
        for stat, count in sorted(by_status.items(), key=lambda x: -x[1]):
            lines.append(f"| {stat} | {count} | {count/max(total,1)*100:.1f}% |")

        lines.extend([
            f"",
            f"## 3. 风险严重度分布",
            f"",
            f"| 严重度 | 数量 | 风险分 |",
            f"|--------|------|--------|",
        ])
        for sev in ["严重", "高", "中", "低"]:
            count = by_severity.get(sev, 0)
            lines.append(f"| {sev} | {count} | {count * severity_weights.get(sev, 1)} |")

        lines.extend([f"", f"## 4. 违规详情", f""])
        for cat, items in by_category.items():
            issues = [i for i in items if i.get("status") in ("不合规", "违规", "待处理")]
            if issues:
                lines.append(f"### {cat}")
                for issue in issues:
                    lines.append(f"- **[{issue.get('severity', '中')}]** {issue.get('description', '')}")
                    if issue.get("recommendation"):
                        lines.append(f"  - 整改建议: {issue['recommendation']}")
                lines.append("")

        lines.extend([
            f"## 5. 整改建议",
            f"",
        ])
        recommendations_set = set()
        for result in audit_results:
            if result.get("recommendation"):
                recommendations_set.add(result["recommendation"])
        for i, rec in enumerate(recommendations_set, 1):
            lines.append(f"{i}. {rec}")

        lines.extend([
            f"",
            f"## 6. 风险评估",
            f"",
            f"- **总体风险等级**: {risk_level}",
            f"- **平均风险分**: {avg_risk:.1f}",
            f"- **高风险项**: {by_severity.get('严重', 0) + by_severity.get('高', 0)} 个",
            f"- **建议优先处理**: {'是' if non_compliant > 0 else '否'}",
            f"",
            f"---",
            f"*本报告由合规审计系统自动生成*",
        ])

        report_text = "\n".join(lines)

    elif format == 'html':
        html_parts = [
            "<html><head><meta charset='utf-8'><style>",
            "body{font-family:sans-serif;margin:20px} table{border-collapse:collapse;width:100%}",
            "th,td{border:1px solid #ddd;padding:8px;text-align:left} th{background:#f2f2f2}",
            "</style></head><body>",
            f"<h1>合规审计报告</h1>",
            f"<p><strong>报告日期</strong>: {report_date} | <strong>合规状态</strong>: {overall_status} | <strong>合规率</strong>: {compliance_rate:.1f}%</p>",
            f"<h2>状态分布</h2><table><tr><th>状态</th><th>数量</th><th>占比</th></tr>",
        ]
        for stat, count in sorted(by_status.items(), key=lambda x: -x[1]):
            html_parts.append(f"<tr><td>{stat}</td><td>{count}</td><td>{count/max(total,1)*100:.1f}%</td></tr>")
        html_parts.append("</table>")

        html_parts.append("<h2>违规详情</h2>")
        for cat, items in by_category.items():
            issues = [i for i in items if i.get("status") in ("不合规", "违规", "待处理")]
            if issues:
                html_parts.append(f"<h3>{cat}</h3><ul>")
                for issue in issues:
                    html_parts.append(f"<li><strong>[{issue.get('severity','中')}]</strong> {issue.get('description','')}")
                    if issue.get("recommendation"):
                        html_parts.append(f"<br><em>建议: {issue['recommendation']}</em>")
                    html_parts.append("</li>")
                html_parts.append("</ul>")

        html_parts.append(f"<h2>风险评估</h2><p>总体风险等级: <strong>{risk_level}</strong> | 平均风险分: {avg_risk:.1f}</p>")
        html_parts.append("</body></html>")
        report_text = "\n".join(html_parts)
    else:
        report_text = json.dumps({
            "summary": {"total": total, "compliance_rate": compliance_rate, "status": overall_status},
            "by_status": dict(by_status), "by_severity": dict(by_severity),
            "risk_level": risk_level, "avg_risk": avg_risk
        }, ensure_ascii=False, indent=2)

    return {
        "format": format,
        "report_text": report_text,
        "summary": {
            "total_items": total,
            "compliance_rate": round(compliance_rate, 1),
            "overall_status": overall_status,
            "risk_level": risk_level,
            "total_risk_score": total_risk_score,
            "avg_risk_score": round(avg_risk, 2),
            "by_status": dict(by_status),
            "by_severity": dict(by_severity),
            "by_category": {k: len(v) for k, v in by_category.items()}
        }
    }


# ---------------------------------------------------------------------------
# 主程序入口
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("行业合规工具 - compliance-checker")
    print("高级算法版本 (倒排索引/TF-IDF/K-匿名/PIA)")
    print("=" * 60)

    # 测试1: 合同分析
    print("\n[1] 合同智能分析:")
    contract = """甲方（上海XX科技有限公司）与乙方（北京YY服务公司）签订本服务合同。
    第一条 合同期限：自2025年1月1日至2025年12月31日，有效期为1年。
    第二条 合同金额：人民币 500,000 元。
    第三条 违约责任：如一方违约，应支付违约金人民币50,000元。
    第四条 争议解决：双方如有争议，应提交上海仲裁委员会仲裁。"""
    analysis = contract_analyzer(contract)
    print(f"  完整性评分: {analysis['completeness']['score']}%")
    print(f"  风险等级: {analysis['risk_level']}")
    print(f"  风险点: {len(analysis['risk_points'])}个")

    # 测试2: 法规检索
    print("\n[2] 法规检索引擎:")
    reg_db = [
        {"id": "R001", "title": "个人信息保护法", "content": "个人信息处理者应当遵循最小必要原则收集个人信息", "level": "法律"},
        {"id": "R002", "title": "数据安全法", "content": "国家建立数据安全风险评估和应急处置机制", "level": "法律"},
        {"id": "R003", "title": "网络安全审查办法", "content": "网络安全审查重点评估数据出境安全风险", "level": "部门规章"},
    ]
    search_results = regulation_search_engine("个人信息安全", reg_db, top_k=3)
    for r in search_results:
        print(f"  [{r['score']}] {r['title']} ({r['level']}) - 匹配: {r['matched_terms']}")

    # 测试3: 风险评估
    print("\n[3] 风险评估模型:")
    risk = risk_assessment_model(
        factors={"数据泄露频率": 7, "安全措施完善度": 3, "合规历史记录": 5, "第三方风险": 6},
        weights={"数据泄露频率": 0.3, "安全措施完善度": 0.3, "合规历史记录": 0.2, "第三方风险": 0.2},
        thresholds={}
    )
    print(f"  总风险分: {risk['total_score']}, 等级: {risk['risk_level']}")
    print(f"  风险矩阵: 可能性={risk['risk_matrix']['likelihood']}, 影响={risk['risk_matrix']['impact']}")

    # 测试4: 隐私影响评估
    print("\n[4] 隐私影响评估(PIA):")
    activities = [
        {"activity_name": "用户注册", "data_types": ["姓名", "手机号", "身份证号"], "purpose": "身份验证",
         "retention_period": "5年", "recipients": ["云服务商"], "security_measures": ["加密", "访问控制"]},
        {"activity_name": "行为分析", "data_types": ["浏览记录", "位置信息"], "purpose": "个性化推荐和广告投放",
         "retention_period": "永久", "recipients": ["广告平台", "数据分析公司", "第三方SDK"], "security_measures": ["加密"]}
    ]
    pia = privacy_impact_assessment(activities)
    print(f"  总体风险: {pia['overall_risk_score']}/10, 等级: {pia['risk_level']}")
    print(f"  缓解措施: {len(pia['mitigation_measures'])}条")

    # 测试5: 数据脱敏
    print("\n[5] 数据脱敏器:")
    test_data = [
        {"name": "张三", "age": 25, "zipcode": "200001", "disease": "感冒"},
        {"name": "李四", "age": 27, "zipcode": "200001", "disease": "感冒"},
        {"name": "王五", "age": 25, "zipcode": "200002", "disease": "流感"},
        {"name": "赵六", "age": 27, "zipcode": "200002", "disease": "流感"},
        {"name": "钱七", "age": 25, "zipcode": "200001", "disease": "感冒"},
    ]
    anon = data_anonymizer(test_data, {"k": 2, "l": 2, "t": 0.3, "generalize_fields": ["age", "zipcode"]}, ["disease"])
    print(f"  K-匿名满足: {anon['privacy_metrics']['k_anonymity']['satisfied']}")
    print(f"  L-多样性满足: {anon['privacy_metrics']['l_diversity']['satisfied']}")
    print(f"  信息损失: {anon['privacy_metrics']['information_loss']}%")

    print("\n" + "=" * 60)
    print("所有工具已就绪，可通过导入 main 模块使用。")
