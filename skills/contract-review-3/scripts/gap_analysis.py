#!/usr/bin/env python3
"""
差异比对引擎 - Phase 2.5 / Phase 3
功能：
1. 对比待审核合同与模板，发现缺失条款和实质性差异
2. 结合法律、司法解释、行政法规进行法律合规审核

法律合规审核逻辑：
- 民法典规定的必要条款
- 最高人民法院司法解释的具体要求
- 国务院行政法规的强制性规定
- 行业监管规则的特别要求
"""

import re
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


# ============================================================================
# 数据结构定义
# ============================================================================

class GapType(Enum):
    """差异类型"""
    MISSING = "缺失"           # 模板有，合同没有
    DIFFERENT = "偏离"         # 两者都有但内容不同
    EXTRA = "多余"             # 合同有，模板没有
    SIMILAR = "相似"           # 内容相似但表述不同


class Importance(Enum):
    """重要性等级"""
    ESSENTIAL = "必要条款"      # 法律强制性规定或核心权利义务
    IMPORTANT = "重要条款"      # 实务中应注意
    OPTIONAL = "可选条款"       # 一般性条款


class LegalSource(Enum):
    """法律依据来源"""
    CIVIL_CODE = "民法典"
    JUDICIAL_INTERPRETATION = "司法解释"
    ADMINISTRATIVE_REGULATION = "行政法规"
    INDUSTRY_RULES = "行业规范"


@dataclass
class GapItem:
    """差异条目"""
    gap_type: GapType
    importance: Importance
    clause_name: str           # 条款名称
    template_content: str      # 模板原文
    contract_content: str      # 合同原文
    difference: str            # 差异说明
    suggestion: str            # 修改建议
    legal_basis: str = ""      # 法律依据
    legal_source: LegalSource = LegalSource.CIVIL_CODE  # 法律来源


@dataclass
class LegalComplianceResult:
    """法律合规审核结果"""
    clause_name: str
    requirement: str            # 法律要求
    legal_basis: str           # 法律依据
    legal_source: LegalSource
    status: str               # compliant / missing / non_compliant
    findings: str             # 审核发现
    suggestion: str           # 建议


# ============================================================================
# 法律规则加载器
# ============================================================================

class LegalRulesLoader:
    """法律规则加载器 - 从规则包加载法律合规要求"""

    def __init__(self, rules_dir: str = None):
        """
        初始化规则加载器

        Args:
            rules_dir: 规则目录路径，默认使用skill内置路径
        """
        if rules_dir is None:
            # 默认路径：skill目录下的references/rule-packs
            skill_dir = Path(__file__).parent.parent
            rules_dir = skill_dir / "references" / "rule-packs"

        self.rules_dir = Path(rules_dir)
        self._cache: Dict[str, dict] = {}

    def load_rules(self, contract_type: str) -> Optional[dict]:
        """
        加载指定合同类型的法律规则

        Args:
            contract_type: 合同类型（如"买卖合同"、"建设工程合同"）

        Returns:
            规则字典，如果不存在则返回None
        """
        # 清理类型名称（移除空格等）
        type_name = contract_type.strip()

        # 尝试从缓存获取
        if type_name in self._cache:
            return self._cache[type_name]

        # 查找规则文件
        rule_path = self.rules_dir / type_name / "legal_rules.json"

        if not rule_path.exists():
            # 尝试模糊匹配
            for child in self.rules_dir.iterdir():
                if child.is_dir() and type_name in child.name:
                    rule_path = child / "legal_rules.json"
                    break

        if not rule_path.exists():
            return None

        try:
            with open(rule_path, 'r', encoding='utf-8') as f:
                rules = json.load(f)
            self._cache[type_name] = rules
            return rules
        except Exception as e:
            print(f"加载法律规则失败: {e}")
            return None

    def get_essential_clauses(self, contract_type: str) -> Dict:
        """
        获取必要条款清单及其法律依据

        Args:
            contract_type: 合同类型

        Returns:
            必要条款字典 {条款名: {legal_basis, requirement, keywords}}
        """
        rules = self.load_rules(contract_type)
        if rules and 'essential_clauses' in rules:
            return rules['essential_clauses']
        return {}

    def get_special_rules(self, contract_type: str) -> Dict:
        """
        获取特殊规则（如分期付款、样品买卖等）

        Args:
            contract_type: 合同类型

        Returns:
            特殊规则字典
        """
        rules = self.load_rules(contract_type)
        if rules and 'special_rules' in rules:
            return rules['special_rules']
        return {}

    def get_common_gaps(self, contract_type: str) -> List[Dict]:
        """
        获取常见缺失问题清单

        Args:
            contract_type: 合同类型

        Returns:
            常见问题列表
        """
        rules = self.load_rules(contract_type)
        if rules and 'common_gaps' in rules:
            return rules['common_gaps']
        return []

    def get_penalty_rules(self, contract_type: str) -> Dict:
        """
        获取违约金/定金规则

        Args:
            contract_type: 合同类型

        Returns:
            惩罚性条款规则
        """
        rules = self.load_rules(contract_type)
        if rules and 'penalty_provisions' in rules:
            return rules['penalty_provisions']
        return {}


# ============================================================================
# 法律合规审核引擎
# ============================================================================

class LegalComplianceChecker:
    """法律合规审核引擎 - 基于法律规则进行合规检查"""

    def __init__(self, contract_text: str, contract_type: str,
                 rules_loader: LegalRulesLoader = None):
        """
        初始化合规审核引擎

        Args:
            contract_text: 待审核合同文本
            contract_type: 合同类型
            rules_loader: 法律规则加载器
        """
        self.contract = contract_text
        self.contract_type = contract_type
        self.rules_loader = rules_loader or LegalRulesLoader()
        self.results: List[LegalComplianceResult] = []

    def check_all(self) -> List[LegalComplianceResult]:
        """
        执行全面法律合规审核

        Returns:
            合规审核结果列表
        """
        self.results = []

        # 1. 检查必要条款
        self._check_essential_clauses()

        # 2. 检查特殊规则（如适用）
        self._check_special_rules()

        # 3. 检查惩罚性条款
        self._check_penalty_provisions()

        # 4. 检查常见问题
        self._check_common_gaps()

        # 5. 检查行业特定要求
        self._check_industry_requirements()

        return self.results

    def _check_essential_clauses(self):
        """检查必要条款是否满足法律要求"""
        essential = self.rules_loader.get_essential_clauses(self.contract_type)

        for clause_name, rule in essential.items():
            legal_basis = rule.get('legal_basis', '')
            requirement = rule.get('requirement', '')
            keywords = rule.get('keywords', [])
            importance = rule.get('importance', 'important')

            # 检测合同中是否有相关条款
            clause_found, clause_content = self._find_clause_content(keywords)

            if not clause_found:
                self.results.append(LegalComplianceResult(
                    clause_name=clause_name,
                    requirement=requirement,
                    legal_basis=legal_basis,
                    legal_source=LegalSource.CIVIL_CODE,
                    status='missing',
                    findings=f"合同中未发现{clause_name}相关内容",
                    suggestion=f"根据{legal_basis}，建议补充：{requirement[:50]}..."
                ))
            else:
                # 检查是否符合法律要求
                compliance = self._check_clause_compliance(
                    clause_name, clause_content, rule
                )
                if compliance:
                    self.results.append(compliance)

    def _check_special_rules(self):
        """检查特殊交易规则是否适用"""
        special = self.rules_loader.get_special_rules(self.contract_type)

        for rule_name, rule_info in special.items():
            # 检查是否属于该特殊类型
            keywords = rule_info.get('clause_keywords', [])
            if any(kw in self.contract for kw in keywords):
                # 特殊规则适用，检查具体要求
                requirements = rule_info.get('requirements', [])
                legal_basis = rule_info.get('legal_basis', '')

                for req in requirements:
                    if not self._check_requirement_met(req):
                        self.results.append(LegalComplianceResult(
                            clause_name=f"【{rule_name}】特殊要求",
                            requirement=req,
                            legal_basis=legal_basis,
                            legal_source=LegalSource.JUDICIAL_INTERPRETATION,
                            status='non_compliant',
                            findings="该特殊交易类型的要求未完全满足",
                            suggestion=req
                        ))

    def _check_penalty_provisions(self):
        """检查惩罚性条款是否符合法律规定"""
        penalties = self.rules_loader.get_penalty_rules(self.contract_type)

        # 检查违约金比例
        if '违约金上限' in penalties:
            rule = penalties['违约金上限']
            legal_basis = rule.get('legal_basis', '')
            recommended = rule.get('recommended_ratio', '')

            # 查找合同中的违约金约定
            penalty_ratio = re.search(r'违约金[^\d]*(\d+(?:\.\d+)?)\s*%', self.contract)
            if penalty_ratio:
                ratio = float(penalty_ratio.group(1))
                # 超过30%可能被认为是过高的
                if ratio > 30:
                    self.results.append(LegalComplianceResult(
                        clause_name="违约金约定",
                        requirement=rule.get('rule', ''),
                        legal_basis=legal_basis,
                        legal_source=LegalSource.CIVIL_CODE,
                        status='non_compliant',
                        findings=f"合同约定违约金比例为{ratio}%，可能被认定为过高",
                        suggestion=f"建议将违约金比例调整至{recommended}"
                    ))

        # 检查定金比例
        if '定金规则' in penalties:
            rule = penalties['定金规则']
            legal_basis = rule.get('legal_basis', '')
            recommended = rule.get('recommended_ratio', '')

            # 查找定金约定
            deposit_ratio = re.search(r'定金[^\d]*(\d+(?:\.\d+)?)\s*%', self.contract)
            if deposit_ratio:
                ratio = float(deposit_ratio.group(1))
                if ratio > 20:
                    self.results.append(LegalComplianceResult(
                        clause_name="定金约定",
                        requirement=rule.get('rule', ''),
                        legal_basis=legal_basis,
                        legal_source=LegalSource.CIVIL_CODE,
                        status='non_compliant',
                        findings=f"合同约定定金比例为{ratio}%，超过法律规定的20%上限",
                        suggestion=f"建议将定金比例调整至{recommended}"
                    ))

    def _check_common_gaps(self):
        """检查常见缺失问题"""
        common = self.rules_loader.get_common_gaps(self.contract_type)

        for gap in common:
            issue = gap.get('issue', '')
            risk = gap.get('risk', '')
            suggestion = gap.get('suggestion', '')

            # 简单检查 - 如果问题相关关键词都不存在
            issue_keywords = self._extract_keywords(issue)
            if issue_keywords and not any(
                kw in self.contract for kw in issue_keywords
            ):
                self.results.append(LegalComplianceResult(
                    clause_name=issue,
                    requirement=risk,
                    legal_basis="实务经验总结",
                    legal_source=LegalSource.INDUSTRY_RULES,
                    status='missing',
                    findings="该常见问题未在合同中明确约定",
                    suggestion=suggestion
                ))

    def _check_industry_requirements(self):
        """检查行业特定要求"""
        # 根据合同类型添加行业特定检查
        industry_checks = {
            '买卖合同': self._check_sales_industry,
            '建设工程合同': self._check_construction_industry,
            '借款合同': self._check_lending_industry,
            '委托合同': self._check_consulting_industry,
        }

        checker = industry_checks.get(self.contract_type)
        if checker:
            checker()

    def _check_sales_industry(self):
        """买卖合同行业检查"""
        # 检查是否涉及网络购物
        if any(kw in self.contract for kw in ['网络', '电商', '网购', '平台', 'APP']):
            if '七日' not in self.contract and '7日' not in self.contract:
                if '无理由退货' in self.contract or '退货' in self.contract:
                    self.results.append(LegalComplianceResult(
                        clause_name="七日无理由退货",
                        requirement="根据《消费者权益保护法》第25条，网络购物消费者享有七天无理由退货权（特定商品除外）",
                        legal_basis="《消费者权益保护法》第25条；《网络消费纠纷司法解释》",
                        legal_source=LegalSource.ADMINISTRATIVE_REGULATION,
                        status='missing',
                        findings="合同涉及网络购物场景，但未明确约定七日无理由退货规则",
                        suggestion="建议明确约定不适用无理由退货的商品范围"
                    ))

    def _check_construction_industry(self):
        """建设工程合同行业检查"""
        # 检查是否涉及工程款支付
        if '工程款' in self.contract or '进度款' in self.contract:
            if '审计' not in self.contract:
                self.results.append(LegalComplianceResult(
                    clause_name="工程款审计条款",
                    requirement="根据《建设工程施工合同纠纷司法解释(一)》第19条，当事人对建设工程的计价标准或者计价方法有约定的，按照约定结算工程款",
                    legal_basis="《建设工程施工合同纠纷司法解释(一)》第19条",
                    legal_source=LegalSource.JUDICIAL_INTERPRETATION,
                    status='missing',
                    findings="合同涉及工程款支付，但未明确约定审计方式",
                    suggestion="建议明确工程款的计价方式和审计程序"
                ))

    def _check_lending_industry(self):
        """借款合同行业检查"""
        # 检查民间借贷利率
        rate_match = re.search(r'(?:年)?利率\s*[为是]?\s*(\d+(?:\.\d+)?)\s*%', self.contract)
        if rate_match:
            rate = float(rate_match.group(1))
            if rate > 14.8:  # 4倍LPR（假设LPR为3.7%）
                self.results.append(LegalComplianceResult(
                    clause_name="民间借贷利率",
                    requirement="根据《民间借贷司法解释》第25条，借贷合同成立时一年期贷款市场报价利率四倍以内的利率受法律保护",
                    legal_basis="《最高人民法院关于审理民间借贷案件适用法律若干问题的规定》第25条",
                    legal_source=LegalSource.JUDICIAL_INTERPRETATION,
                    status='non_compliant',
                    findings=f"合同约定年利率为{rate}%，超过法律保护上限（约为14.8%）",
                    suggestion="建议将利率调整至合法范围内，或明确说明该借款不属于民间借贷范畴"
                ))

    def _check_consulting_industry(self):
        """咨询服务合同行业检查"""
        # 检查是否有成果交付约定
        if any(kw in self.contract for kw in ['咨询', '服务', '顾问']):
            if '交付' not in self.contract and '成果' not in self.contract:
                self.results.append(LegalComplianceResult(
                    clause_name="成果交付条款",
                    requirement="委托合同应当明确委托事务的具体内容和成果形式",
                    legal_basis="《民法典》第919条",
                    legal_source=LegalSource.CIVIL_CODE,
                    status='missing',
                    findings="咨询服务合同未明确约定服务成果的交付形式",
                    suggestion="建议明确约定服务成果的内容、形式和交付时间"
                ))

    def _find_clause_content(self, keywords: List[str]) -> Tuple[bool, str]:
        """查找条款内容"""
        for kw in keywords:
            idx = self.contract.find(kw)
            if idx >= 0:
                # 提取周围上下文
                start = max(0, idx - 100)
                end = min(len(self.contract), idx + 200)
                return True, self.contract[start:end]
        return False, ""

    def _check_clause_compliance(self, clause_name: str,
                                clause_content: str,
                                rule: dict) -> Optional[LegalComplianceResult]:
        """检查条款是否符合法律要求"""
        importance = rule.get('importance', 'important')

        # 根据条款类型进行具体检查
        if clause_name == '质量条款':
            # 检查是否有质量标准
            if not any(std in clause_content for std in ['标准', '规格', '国标', '行业标准']):
                return LegalComplianceResult(
                    clause_name=clause_name,
                    requirement=rule.get('requirement', ''),
                    legal_basis=rule.get('legal_basis', ''),
                    legal_source=LegalSource.CIVIL_CODE,
                    status='non_compliant',
                    findings="质量条款未明确具体标准",
                    suggestion="建议明确产品的质量标准（如国家标准、行业标准或双方约定标准）"
                )

        elif clause_name == '检验条款':
            # 检查是否有检验期限
            if '检验' in clause_content and not any(
                kw in clause_content for kw in ['期限', '日内', '天内', '工作日']
            ):
                return LegalComplianceResult(
                    clause_name=clause_name,
                    requirement=rule.get('requirement', ''),
                    legal_basis=rule.get('legal_basis', ''),
                    legal_source=LegalSource.CIVIL_CODE,
                    status='non_compliant',
                    findings="检验条款未约定检验期限",
                    suggestion="建议明确约定检验期限（建议不少于收货后15个工作日）"
                )

        return None

    def _check_requirement_met(self, requirement: str) -> bool:
        """检查特定要求是否被满足"""
        # 简化检查：查找关键词
        keywords = self._extract_keywords(requirement)
        return any(kw in self.contract for kw in keywords[:5])

    def _extract_keywords(self, text: str) -> List[str]:
        """从文本中提取关键词"""
        # 简单分词：去除停用词，保留实词
        stopwords = ['的', '了', '在', '是', '和', '或', '以及', '等', '应当', '可以', '应当']
        words = re.findall(r'[\u4e00-\u9fa5a-zA-Z0-9]{2,}', text)
        return [w for w in words if w not in stopwords and len(w) >= 2]


# ============================================================================
# 差异比对引擎（整合法律合规审核）
# ============================================================================

class GapAnalysisEngine:
    """
    差异比对引擎 - 整合模板比对与法律合规审核
    """

    def __init__(self, contract_text: str, template_text: str = "",
                 contract_type: str = None,
                 enable_legal_check: bool = True):
        """
        初始化比对引擎

        Args:
            contract_text: 待审核合同文本
            template_text: 模板合同文本（可选）
            contract_type: 合同类型
            enable_legal_check: 是否启用法律合规审核
        """
        self.contract = contract_text
        self.template = template_text
        self.contract_type = contract_type or '通用'
        self.enable_legal_check = enable_legal_check
        self.gaps: List[GapItem] = []
        self.legal_results: List[LegalComplianceResult] = []

        # 初始化法律规则加载器
        self.rules_loader = LegalRulesLoader()

    def analyze(self) -> Dict:
        """
        执行完整差异分析（包括法律合规审核）

        Returns:
            分析结果字典
        """
        self.gaps = []
        self.legal_results = []

        # 1. 模板差异分析（如果有模板）
        if self.template:
            self._check_essential_clauses()
            self._check_important_clauses()
            self._check_substantive_differences()

        # 2. 法律合规审核
        if self.enable_legal_check:
            self._run_legal_compliance_check()

        # 3. 按重要性排序
        self.gaps.sort(key=lambda x: (
            self._importance_order(x.importance),
            self._gap_type_order(x.gap_type)
        ))

        return {
            'summary': self._generate_summary(),
            'gaps': [self._gap_to_dict(g) for g in self.gaps],
            'legal_compliance': self._generate_legal_report(),
            'missing_clauses': self._get_missing_clauses(),
            'different_clauses': self._get_different_clauses(),
        }

    def _run_legal_compliance_check(self):
        """运行法律合规审核"""
        checker = LegalComplianceChecker(
            self.contract,
            self.contract_type,
            self.rules_loader
        )
        self.legal_results = checker.check_all()

        # 将法律合规结果转换为gap items
        for result in self.legal_results:
            if result.status in ['missing', 'non_compliant']:
                importance = Importance.IMPORTANT
                if '必要' in result.legal_basis or '强制性' in result.requirement:
                    importance = Importance.ESSENTIAL

                source = LegalSource.CIVIL_CODE
                if '司法解释' in result.legal_basis:
                    source = LegalSource.JUDICIAL_INTERPRETATION
                elif any(x in result.legal_basis for x in ['条例', '办法', '规定']):
                    source = LegalSource.ADMINISTRATIVE_REGULATION

                self.gaps.append(GapItem(
                    gap_type=GapType.MISSING if result.status == 'missing' else GapType.DIFFERENT,
                    importance=importance,
                    clause_name=result.clause_name,
                    template_content="",
                    contract_content=result.findings,
                    difference=result.findings,
                    suggestion=result.suggestion,
                    legal_basis=result.legal_basis,
                    legal_source=source,
                ))

    def _check_essential_clauses(self):
        """检查必要条款是否缺失（基于模板）"""
        # 保持原有逻辑
        type_clauses = self._get_type_clauses()

        for clause_name, keywords in type_clauses.items():
            if not self._clause_exists(self.contract, keywords):
                self.gaps.append(GapItem(
                    gap_type=GapType.MISSING,
                    importance=Importance.ESSENTIAL,
                    clause_name=clause_name,
                    template_content=self._get_template_clause(keywords),
                    contract_content="【未找到相关条款】",
                    difference=f"合同中未发现{clause_name}相关内容",
                    suggestion=self._generate_suggestion(clause_name, 'missing'),
                    legal_basis=self._get_legal_basis(clause_name),
                    legal_source=LegalSource.CIVIL_CODE,
                ))

    def _check_important_clauses(self):
        """检查重要条款是否缺失"""
        for clause_name in self.IMPORTANT_CLAUSES:
            keywords = self._get_keywords_for_clause(clause_name)
            if not self._clause_exists(self.contract, keywords):
                self.gaps.append(GapItem(
                    gap_type=GapType.MISSING,
                    importance=Importance.IMPORTANT,
                    clause_name=clause_name,
                    template_content=self._get_template_clause(keywords),
                    contract_content="【未找到相关条款】",
                    difference=f"合同中未发现{clause_name}",
                    suggestion=self._generate_suggestion(clause_name, 'missing'),
                ))

    def _check_substantive_differences(self):
        """检测实质性差异"""
        self._compare_payment_terms()
        self._compare_penalty_terms()
        self._compare_dispute_terms()

    def _compare_payment_terms(self):
        """比对付款条款"""
        payment_keywords = ['付款', '支付', '价款', '货款', '金额']

        if self._clause_exists(self.contract, payment_keywords):
            contract_payment = self._extract_clause(self.contract, payment_keywords)
            template_payment = self._extract_clause(self.template, payment_keywords)

            if contract_payment and template_payment:
                contract_has_amount = bool(re.search(r'[¥￥]?\s*[\d,]+', contract_payment))
                template_has_amount = bool(re.search(r'[¥￥]?\s*[\d,]+', template_payment))

                if template_has_amount and not contract_has_amount:
                    self.gaps.append(GapItem(
                        gap_type=GapType.DIFFERENT,
                        importance=Importance.ESSENTIAL,
                        clause_name='价款条款（金额不明）',
                        template_content=template_payment[:200],
                        contract_content=contract_payment[:200],
                        difference="模板明确了具体金额，合同中金额约定不明确",
                        suggestion="建议明确合同总价款或计价方式",
                    ))

    def _compare_penalty_terms(self):
        """比对违约条款"""
        penalty_keywords = ['违约', '违约金', '责任']

        if self._clause_exists(self.contract, penalty_keywords):
            contract_penalty = self._extract_clause(self.contract, penalty_keywords)

            if contract_penalty:
                contract_ratio = re.search(r'(\d+(?:\.\d+)?)\s*%', contract_penalty)
                if contract_ratio:
                    ratio = float(contract_ratio.group(1))
                    if ratio > 30:
                        self.gaps.append(GapItem(
                            gap_type=GapType.DIFFERENT,
                            importance=Importance.IMPORTANT,
                            clause_name='违约金比例偏高',
                            template_content="",
                            contract_content=contract_penalty[:200],
                            difference=f"合同约定违约金比例为{ratio}%，可能偏高",
                            suggestion="建议将违约金比例调整至实际损失的30%以内",
                            legal_basis="《民法典》第585条；《九民纪要》第50条",
                            legal_source=LegalSource.CIVIL_CODE,
                        ))

    def _compare_dispute_terms(self):
        """比对争议解决条款"""
        dispute_keywords = ['争议', '仲裁', '诉讼', '管辖', '法院']

        contract_has = self._clause_exists(self.contract, dispute_keywords)
        template_has = self._clause_exists(self.template, dispute_keywords)

        if template_has and not contract_has:
            self.gaps.append(GapItem(
                gap_type=GapType.MISSING,
                importance=Importance.IMPORTANT,
                clause_name='争议解决条款',
                template_content=self._extract_clause(self.template, dispute_keywords)[:200],
                contract_content="【未约定争议解决方式】",
                difference="合同未约定争议解决方式",
                suggestion="建议明确约定仲裁或管辖法院",
            ))

    # =========================================================================
    # 辅助方法
    # =========================================================================

    def _get_type_clauses(self) -> Dict:
        """获取合同类型的必要条款"""
        # 基础必要条款
        base_clauses = {
            '买卖合同': {
                '标的条款': ['标的', '产品', '货物', '商品', '标的物'],
                '数量条款': ['数量', '数量为', '共'],
                '价款条款': ['价款', '价格', '货款', '金额', '总价'],
                '交付条款': ['交付', '交付时间', '交付地点', '交货'],
                '验收条款': ['验收', '检验', '签收'],
            },
            '委托合同': {
                '委托事项': ['委托', '事项', '服务', '处理'],
                '报酬条款': ['报酬', '费用', '服务费', '咨询费'],
                '成果交付': ['交付', '成果', '报告'],
            },
            '借款合同': {
                '借款金额': ['借款', '本金', '金额'],
                '利率条款': ['利率', '利息', '年利率'],
                '还款条款': ['还款', '偿还', '期限'],
            },
        }

        return base_clauses.get(
            self.contract_type,
            base_clauses.get('买卖合同', {})
        )

    IMPORTANT_CLAUSES = [
        '违约条款', '保密条款', '知识产权条款', '不可抗力条款',
        '争议解决条款', '通知条款', '终止条款', '合同变更条款',
    ]

    def _get_keywords_for_clause(self, clause_name: str) -> List[str]:
        """获取条款对应的关键词"""
        keywords_map = {
            '违约条款': ['违约', '违约金', '责任'],
            '保密条款': ['保密', '机密'],
            '知识产权条款': ['知识产权', '专利', '版权', '权属'],
            '不可抗力条款': ['不可抗力'],
            '争议解决条款': ['争议', '仲裁', '诉讼', '管辖'],
            '通知条款': ['通知', '送达', '地址'],
            '终止条款': ['终止', '解除', '期满'],
            '合同变更条款': ['变更', '修改', '补充'],
        }
        return keywords_map.get(clause_name, [clause_name.replace('条款', '')])

    def _get_legal_basis(self, clause_name: str) -> str:
        """获取条款的法律依据"""
        legal_bases = {
            '标的条款': '《民法典》第595条',
            '数量条款': '《民法典》第512条',
            '价款条款': '《民法典》第628条',
            '交付条款': '《民法典》第608条',
            '验收条款': '《民法典》第619条',
        }
        return legal_bases.get(clause_name, '《民法典》合同编通则')

    def _clause_exists(self, text: str, keywords: List[str]) -> bool:
        """检查条款是否存在"""
        return any(kw in text for kw in keywords)

    def _extract_clause(self, text: str, keywords: List[str],
                       context: int = 200) -> str:
        """提取条款内容"""
        for kw in keywords:
            idx = text.find(kw)
            if idx >= 0:
                start = max(0, idx - 50)
                end = min(len(text), idx + context)
                return text[start:end].strip()
        return ""

    def _get_template_clause(self, keywords: List[str]) -> str:
        """从模板中提取条款"""
        return self._extract_clause(self.template, keywords)

    def _generate_suggestion(self, clause_name: str, action: str) -> str:
        """生成建议"""
        suggestions = {
            '违约条款': {'missing': '建议增加违约条款，明确违约情形和违约金计算方式'},
            '保密条款': {'missing': '建议增加保密条款，约定保密范围和期限'},
            '争议解决条款': {'missing': '建议明确约定仲裁或管辖法院'},
            '不可抗力条款': {'missing': '建议增加不可抗力条款，约定通知义务和后果'},
            '价款条款': {'missing': '建议明确合同价款或计价方式'},
        }
        return suggestions.get(clause_name, {}).get(
            action, f'建议参照模板补充{clause_name}'
        )

    def _importance_order(self, imp: Importance) -> int:
        """重要性排序"""
        return {Importance.ESSENTIAL: 0, Importance.IMPORTANT: 1, Importance.OPTIONAL: 2}[imp]

    def _gap_type_order(self, gap: GapType) -> int:
        """差异类型排序"""
        return {GapType.MISSING: 0, GapType.DIFFERENT: 1, GapType.EXTRA: 2, GapType.SIMILAR: 3}[gap]

    def _generate_summary(self) -> Dict:
        """生成摘要"""
        return {
            'total_gaps': len(self.gaps),
            'missing_count': len([g for g in self.gaps if g.gap_type == GapType.MISSING]),
            'different_count': len([g for g in self.gaps if g.gap_type == GapType.DIFFERENT]),
            'essential_gaps': len([g for g in self.gaps if g.importance == Importance.ESSENTIAL]),
            'legal_compliance_issues': len(self.legal_results),
            'contract_type': self.contract_type,
        }

    def _generate_legal_report(self) -> List[Dict]:
        """生成法律合规报告"""
        return [
            {
                'clause': r.clause_name,
                'requirement': r.requirement,
                'legal_basis': r.legal_basis,
                'legal_source': r.legal_source.value,
                'status': r.status,
                'findings': r.findings,
                'suggestion': r.suggestion,
            }
            for r in self.legal_results
        ]

    def _get_missing_clauses(self) -> List[str]:
        """获取缺失条款列表"""
        return [g.clause_name for g in self.gaps if g.gap_type == GapType.MISSING]

    def _get_different_clauses(self) -> List[str]:
        """获取偏离条款列表"""
        return [g.clause_name for g in self.gaps if g.gap_type == GapType.DIFFERENT]

    def _gap_to_dict(self, gap: GapItem) -> Dict:
        """将差异条目转为字典"""
        return {
            'type': gap.gap_type.value,
            'importance': gap.importance.value,
            'clause': gap.clause_name,
            'template_content': gap.template_content[:500] if gap.template_content else '',
            'contract_content': gap.contract_content[:500] if gap.contract_content else '',
            'difference': gap.difference,
            'suggestion': gap.suggestion,
            'legal_basis': gap.legal_basis,
            'legal_source': gap.legal_source.value if gap.legal_source else '',
        }


# ============================================================================
# 主入口函数
# ============================================================================

def analyze(contract_text: str, template_text: str = "",
            contract_type: str = None,
            enable_legal_check: bool = True) -> Dict:
    """
    差异分析与法律合规审核主入口

    Args:
        contract_text: 待审核合同文本
        template_text: 模板合同文本（可选）
        contract_type: 合同类型
        enable_legal_check: 是否启用法律合规审核

    Returns:
        分析结果
    """
    engine = GapAnalysisEngine(
        contract_text, template_text, contract_type, enable_legal_check
    )
    return engine.analyze()


def main():
    """测试函数"""
    import json

    contract = """
    采购合同

    甲方（买方）：某科技有限公司
    乙方（卖方）：某供应商

    第一条 产品描述
    甲方向乙方采购服务器设备10台。

    第二条 付款条件
    甲方应于收货后30日内付款。

    第三条 交付时间
    乙方应于合同签订后15日内交付产品。

    第四条 违约责任
    任何一方违约应承担相应法律责任，违约金为合同总价的50%。
    """

    print("=== 法律合规审核测试 ===\n")
    result = analyze(contract, "", "买卖合同", enable_legal_check=True)

    print("【摘要】")
    summary = result['summary']
    print(f"  总问题数: {summary['total_gaps']}")
    print(f"  缺失条款: {summary['missing_count']}")
    print(f"  偏离条款: {summary['different_count']}")
    print(f"  必要条款缺失: {summary['essential_gaps']}")
    print(f"  法律合规问题: {summary['legal_compliance_issues']}")

    print("\n【差异分析】")
    for gap in result['gaps'][:5]:
        print(f"  - [{gap['importance']}] {gap['clause']}")
        print(f"    {gap['difference']}")
        if gap.get('legal_basis'):
            print(f"    法律依据: {gap['legal_basis']}")

    print("\n【法律合规报告】")
    for item in result['legal_compliance'][:5]:
        print(f"  - [{item['status']}] {item['clause']}")
        print(f"    法律依据: {item['legal_basis']}")
        print(f"    建议: {item['suggestion'][:50]}...")


if __name__ == '__main__':
    main()
