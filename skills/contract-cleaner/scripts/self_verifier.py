#!/usr/bin/env python3
"""
合同清洗结果自检模块

根据global_text_processing.md规范，对AI清洗结果进行验证
"""

import re
from typing import List, Tuple, Dict, Set
from dataclasses import dataclass, field


@dataclass
class VerificationIssue:
    """验证问题记录"""
    rule: str          # 规则名称
    severity: str      # 严重程度: ERROR, WARNING, INFO
    message: str       # 问题描述
    location: str      # 位置（文本片段）
    suggestion: str    # 修复建议
    spec_ref: str = ""           # 规范条款引用（如"1.1"、"2.3.2"）
    prompt_location: str = ""    # Prompt中的位置（如"义务Prompt-必须添加应当的场景"）


@dataclass
class VerificationReport:
    """验证报告"""
    issues: List[VerificationIssue] = field(default_factory=list)
    
    def add_issue(self, issue: VerificationIssue):
        self.issues.append(issue)
    
    @property
    def passed(self) -> int:
        """通过数 = 非ERROR级别的问题数"""
        return sum(1 for issue in self.issues if issue.severity != "ERROR")
    
    @property
    def failed(self) -> int:
        """失败数 = ERROR级别的问题数"""
        return sum(1 for issue in self.issues if issue.severity == "ERROR")
    
    @property
    def total_checks(self) -> int:
        """总检查数 = 通过 + 失败"""
        return len(self.issues)
    
    @property
    def success_rate(self) -> float:
        if self.total_checks == 0:
            return 100.0  # 没有issue表示100%通过
        return (self.passed / self.total_checks) * 100
    
    def __str__(self) -> str:
        lines = [
            "=" * 60,
            "合同清洗自检报告",
            "=" * 60,
            f"总检查项: {self.total_checks}",
            f"通过: {self.passed}",
            f"失败: {self.failed}",
            f"成功率: {self.success_rate:.1f}%",
            "",
        ]
        
        if self.issues:
            lines.append("发现的问题:")
            lines.append("-" * 60)
            for i, issue in enumerate(self.issues, 1):
                lines.append(f"\n{i}. [{issue.severity}] {issue.rule}")
                lines.append(f"   问题: {issue.message}")
                lines.append(f"   位置: {issue.location[:80]}...")
                lines.append(f"   建议: {issue.suggestion}")
        else:
            lines.append("✓ 所有检查项通过！")
        
        lines.append("=" * 60)
        return "\n".join(lines)


class ContractSelfVerifier:
    """
    合同清洗结果自检器
    
    v4.0变更: 术语表和委托白名单从rule_engine单一数据源引用，
    不再在verifier中重复定义（消除S-03数据不一致风险）
    
    v5.1变更: 新增 FEEDBACK_ATLAS 映射表，自检不通过时精确定位到
    规范条款号和Prompt原文位置，让AI重做时无需猜测"哪里错了"。
    """
    
    # ============================================================
    # 反馈定位图谱：rule → (规范条款, Prompt位置)
    # 
    # 设计原则：从节约token的角度出发，AI重做时只需看到：
    #   "规范X.X要求……你在Prompt的'XXX'段落中已有此规则"
    # 而不是模糊的"请修正"。
    # ============================================================
    FEEDBACK_ATLAS = {
        # --- 术语规范 ---
        "术语替换": {
            "spec_ref": "1.1",
            "prompt_location": "义务Prompt-⛔不得修改已有内容",
            "resolution_hint": "术语替换应由规则引擎完成；若AI覆盖了规则引擎的修改，需恢复",
        },
        "委托术语白名单": {
            "spec_ref": "1.2",
            "prompt_location": "义务Prompt-⛔不得修改已有内容",
            "resolution_hint": "委托术语白名单外的'委托'应替换为'约定'/'服务内容'等",
        },
        "术语一致性": {
            "spec_ref": "1.3",
            "prompt_location": "义务Prompt-术语一致性规则（规范1.3）",
            "resolution_hint": "同一概念全文必须使用同一术语",
        },
        "指代明确": {
            "spec_ref": "1.4",
            "prompt_location": "结构Prompt-指代明确",
            "resolution_hint": "首次全称+禁止模糊'其'+跨条款明确指向",
        },
        "嵌套应当": {
            "spec_ref": "1.5.2",
            "prompt_location": "义务Prompt-⛔嵌套禁止（规范1.5.2）",
            "resolution_hint": "同一主语同一句中删除内层'应当'，或合并为'并'+动词",
        },
        "近义术语": {
            "spec_ref": "1.6",
            "prompt_location": "结构Prompt-无法确定时的处理",
            "resolution_hint": "定金/订金、撤回/撤销不应同时出现",
        },
        # --- 义务句式 ---
        "义务句式": {
            "spec_ref": "1.5",
            "prompt_location": "义务Prompt-必须添加应当的场景（逐条检查）",
            "resolution_hint": "甲/乙方义务动词前必须加'应当'，孤立的'应'/'须'统一为'应当'",
        },
        # --- 结构规范 ---
        "首部保护": {
            "spec_ref": "2.3.1/2.4",
            "prompt_location": "结构Prompt-首部保护",
            "resolution_hint": "合同标题/甲乙方/鉴于条款不得编入任何条款编号",
        },
        "层级递进": {
            "spec_ref": "2.2",
            "prompt_location": "结构Prompt-层级递进",
            "resolution_hint": "一级编号后不得直接用三级编号，应改用自然段落",
        },
        "签署区保护": {
            "spec_ref": "2.3.2",
            "prompt_location": "结构Prompt-签署区保护",
            "resolution_hint": "签署区独立展示，不得添加编号",
        },
        "附件保护": {
            "spec_ref": "2.3.3",
            "prompt_location": "结构Prompt-附件保护",
            "resolution_hint": "附件标题独立，不与主合同连续编号",
        },
        "内容添加检测": {
            "spec_ref": "2.4",
            "prompt_location": "结构Prompt-禁止内容添加",
            "resolution_hint": "不得添加原文不存在的概括性标题/甲乙方名称/合并压缩内容",
        },
        "表格保护": {
            "spec_ref": "结构Prompt-表格保护",
            "prompt_location": "结构Prompt-表格保护",
            "resolution_hint": "表格结构必须完整保留，不得转为自然语言",
        },
        "结构重组": {
            "spec_ref": "2.2",
            "prompt_location": "结构Prompt-必须执行的修改（删除非标准小标题）",
            "resolution_hint": "删除非标准小标题，建立1.1/1.2层级",
        },
        "日期格式": {
            "spec_ref": "2.1",
            "prompt_location": "义务Prompt-⛔不得修改已有内容",
            "resolution_hint": "日期应统一为YYYY年M月D日格式",
        },
        # --- 句式规范 ---
        "句式完整性": {
            "spec_ref": "3.1",
            "prompt_location": "义务Prompt-句式完整性规则（规范3.1）",
            "resolution_hint": "禁止'小标题+冒号+内容'句式，必须改写为完整主谓宾句子",
        },
        # --- 格式规范 ---
        "格式清理": {
            "spec_ref": "6.7",
            "prompt_location": "格式Prompt-格式清理规则",
            "resolution_hint": "移除非条款Markdown标记，保留`**第X条 标题**`和`**第X条**`的整体加粗，不得拆分或截断",
        },
        "格式统一": {
            "spec_ref": "2.2/6.7",
            "prompt_location": "格式Prompt-格式清理规则",
            "resolution_hint": "条款标题应整体加粗（`**第X条 标题**`），第X条后加空格",
        },
        "括号格式": {
            "spec_ref": "2.3",
            "prompt_location": "格式Prompt-格式清理规则",
            "resolution_hint": "不改变原合同的全角半角（已禁用括号转换）",
        },
        "标点统一": {
            "spec_ref": "格式Prompt-标点符号",
            "prompt_location": "格式Prompt-标点符号",
            "resolution_hint": "不改变原合同的全角半角（已禁用标点转换）",
        },
        "标记保留": {
            "spec_ref": "6.6",
            "prompt_location": "结构Prompt-无法确定时的处理",
            "resolution_hint": "【近义术语待统一】等标记不得被AI删除",
        },
        "标记处理": {
            "spec_ref": "3.1/6.6",
            "prompt_location": "义务Prompt-句式完整性规则（规范3.1）",
            "resolution_hint": "【句式待改写】标记处应改写为完整句子后移除标记",
        },
        # --- 修复验证 ---
        "修复验证": {
            "spec_ref": "全文",
            "prompt_location": "全文所有Prompt",
            "resolution_hint": "清洗后问题数量应少于原始，否则AI清洗可能未执行",
        },
        # --- 金额格式 ---
        "金额格式": {
            "spec_ref": "2.1",
            "prompt_location": "义务Prompt-⛔不得修改已有内容",
            "resolution_hint": "¥/￥→人民币XXXX.00元（人民币X元整），不加千分位逗号",
        },
        # --- 全角半角 ---
        "全角字符": {
            "spec_ref": "格式Prompt-⛔不得改变全角半角",
            "prompt_location": "格式Prompt-⛔不得改变全角半角",
            "resolution_hint": "数字和英文字母必须使用半角（如1.1不能写成１．１），由规则引擎apply_fullwidth_to_halfwidth兜底修正",
        },
    }
    
    def __init__(self):
        self.report = VerificationReport()
        # 从rule_engine单一数据源引入术语表
        from rule_engine import RuleEngine
        rule_engine = RuleEngine()
        self.TERM_REPLACEMENTS = dict(rule_engine.UNCONDITIONAL_TERMS)
        # 条件术语也纳入验证
        for old, rule in rule_engine.CONDITIONAL_TERMS.items():
            self.TERM_REPLACEMENTS[old] = rule["replacement"]
        # 政府场景例外关键词（来自rule_engine.CONDITIONAL_TERMS["滞纳金"]["keep_if_context"]）
        self.DEBT_CONTEXT_KEYWORDS = rule_engine.CONDITIONAL_TERMS.get("滞纳金", {}).get("keep_if_context", [])
        # 债务清偿场景关键词
        self.DEBT_DEDUCT_KEYWORDS = rule_engine.CONDITIONAL_TERMS.get("抵消", {}).get("if_context", [])
        # 委托术语白名单（来自rule_engine.ENTRUST_WHITELIST）
        self.ENTRUST_WHITELIST = list(rule_engine.ENTRUST_WHITELIST)
    
    # 义务句式模式（应该出现"应当"的场景）
    OBLIGATION_PATTERNS = [
        r"[甲乙]方(?:负责|提供|承担|保证|确保|完成|遵守|维护|保密)",
        r"(?:负责|提供|承担|保证|确保|完成|遵守|维护|保密).{0,10}(?:工作|服务|义务|责任)",
    ]
    
    # 金额格式模式
    AMOUNT_PATTERNS = {
        "currency_symbol": re.compile(r'[¥￥]\s*\d'),
        "proper_format": re.compile(r'人民币\d+(?:\.\d{2})?元'),
        "with_chinese": re.compile(r'人民币\d+(?:\.\d{2})?元\s*（人民币[一二三四五六七八九十百千万亿]+元整?）'),
    }
    
    def _make_issue(self, rule: str, severity: str, message: str,
                    location: str, suggestion: str) -> VerificationIssue:
        """
        构建带规范定位的验证问题
        
        自动从 FEEDBACK_ATLAS 查找 spec_ref 和 prompt_location，
        确保每个 ERROR/WARNING 都能精确指向规范条款和 Prompt 位置。
        """
        atlas_entry = self.FEEDBACK_ATLAS.get(rule, {})
        return VerificationIssue(
            rule=rule,
            severity=severity,
            message=message,
            location=location,
            suggestion=suggestion,
            spec_ref=atlas_entry.get("spec_ref", ""),
            prompt_location=atlas_entry.get("prompt_location", ""),
        )
    
    def verify(self, original: str, cleaned: str) -> VerificationReport:
        """
        执行完整验证
        
        Args:
            original: 原始文本
            cleaned: 清洗后的文本
        
        Returns:
            验证报告
        """
        self.report = VerificationReport()
        
        # 1. 术语替换验证
        self._verify_term_replacements(cleaned)
        
        # 2. 义务句式验证
        self._verify_obligation_syntax(cleaned)
        
        # 3. 金额格式验证
        self._verify_amount_format(cleaned)
        
        # 4. 格式验证
        self._verify_formatting(cleaned)
        
        # 5. 结构验证
        self._verify_structure(cleaned)
        
        # 6. 反向验证（原始中的问题是否已修复）
        self._verify_fixes_applied(original, cleaned)
        
        # 7. 委托术语白名单验证
        self._verify_entrust_terms(cleaned)
        
        # 8. 首部保护验证
        self._verify_header_protection(cleaned)
        
        # 9. 层级递进验证
        self._verify_hierarchy(cleaned)
        
        # 10. 内容添加检测
        self._verify_no_content_addition(original, cleaned)
        
        # 11. 日期格式验证（规范2.1）
        self._verify_date_format(cleaned)
        
        # 12. 近义术语验证（规范1.6）
        self._verify_near_synonyms(cleaned)
        
        # 13. 句式完整性验证（规范3.1）
        self._verify_sentence_completeness(cleaned)
        
        # 14. 指代明确性验证（规范1.4）
        self._verify_reference_clarity(cleaned)
        
        # 15. 签署区/附件验证（规范2.3.2/2.3.3）
        self._verify_signature_and_appendix(cleaned)
        
        # 16. 嵌套"应当"验证（规范1.5.2）
        self._verify_nested_yingdang(cleaned)
        
        # 17. 术语一致性验证（规范1.3）
        self._verify_term_consistency(cleaned)
        
        # 18. 表格保护验证（结构Prompt）
        self._verify_table_protection(original, cleaned)
        
        # 19. 标点统一验证（格式Prompt）
        self._verify_punctuation(cleaned)
        
        # 20. 全角字符检测（数字/英文/编号不得为全角）
        self._verify_fullwidth_characters(cleaned)
        
        # 21. 无法确定标记保留验证（规范6.6）
        self._verify_uncertainty_markers(original, cleaned)
        
        return self.report
    
    def _verify_term_replacements(self, text: str):
        """验证术语替换是否完整"""
        for old_term, new_term in self.TERM_REPLACEMENTS.items():
            if old_term == "滞纳金":
                # 特殊检查：滞纳金在某些场景下允许保留
                for match in re.finditer(re.escape(old_term), text):
                    start_pos = match.start()
                    end_pos = match.end()
                    # 提取上下文（前后各50字符）
                    context = text[max(0, start_pos-50):min(len(text), end_pos+50)]
                    # 检查是否在政府/能源场景中
                    if any(keyword in context for keyword in self.DEBT_CONTEXT_KEYWORDS):
                        continue  # 政府场景允许保留
                    # 非政府场景，报错
                    self.report.add_issue(self._make_issue(
                        rule="术语替换",
                        severity="ERROR",
                        message=f"发现未替换的旧术语: '{old_term}'（非政府/能源场景）",
                        location=text[max(0, start_pos-30):min(len(text), end_pos+30)],
                        suggestion=f"应替换为: '{new_term}'"
                    ))
            elif old_term == "抵消":
                for match in re.finditer(re.escape(old_term), text):
                    start_pos = match.start()
                    end_pos = match.end()
                    context = text[max(0, start_pos-30):min(len(text), end_pos+30)]
                    # 债务清偿上下文关键词（来自rule_engine单一数据源）
                    if any(keyword in context for keyword in self.DEBT_DEDUCT_KEYWORDS):
                        # 债务场景，应替换为"抵销"
                        self.report.add_issue(self._make_issue(
                            rule="术语替换",
                            severity="ERROR",
                            message=f"债务清偿场景中应使用'抵销': '{old_term}'",
                            location=context,
                            suggestion=f"应替换为: '{new_term}'"
                        ))
                    # 非债务场景（如"抵消影响"），允许保留"抵消"
            else:
                # 其他术语：检查是否还有残留
                if old_term in text:
                    for match in re.finditer(re.escape(old_term), text):
                        start_pos = match.start()
                        end_pos = match.end()
                        self.report.add_issue(self._make_issue(
                            rule="术语替换",
                            severity="ERROR",
                            message=f"发现未替换的旧术语: '{old_term}'",
                            location=text[max(0, start_pos-30):min(len(text), end_pos+30)],
                            suggestion=f"应替换为: '{new_term}'"
                        ))
    
    def _verify_obligation_syntax(self, text: str):
        """验证义务句式"""
        lines = text.split('\n')
        for line_num, line in enumerate(lines, 1):
            for pattern in self.OBLIGATION_PATTERNS:
                matches = re.finditer(pattern, line)
                for match in matches:
                    # 检查前面是否有"应当"
                    start_pos = match.start()
                    # BUG-R03修复：扩大上下文窗口到整行前部（最多30字符）
                    context_before = line[max(0, start_pos-30):start_pos]
                    
                    has_yingdang = "应当" in context_before
                    # 更精确的"应"检测：避免"应付款"等词中的"应"
                    has_ying = False
                    if not has_yingdang:
                        # 查找独立的情态动词"应"（后面接动词）
                        import re as re_module
                        ying_pattern = r'应\s*(?:当|该|当且仅当)?\s*$'
                        if re_module.search(ying_pattern, context_before):
                            has_ying = True
                    
                    if not has_yingdang and not has_ying:
                        # 检查是否是例外情况
                        if not self._is_obligation_exception(match.group(), context_before):
                            self.report.add_issue(self._make_issue(
                                rule="义务句式",
                                severity="WARNING",
                                message=f"可能的义务表述缺少'应当'",
                                location=line.strip(),
                                suggestion=f"建议改为: '...应当{match.group()}...'"
                            ))
    
    def _is_obligation_exception(self, matched_text: str, context_before: str = "") -> bool:
        """检查是否是义务句式的例外"""
        # 基于匹配文本的例外
        text_exceptions = [
            "应当",  # 已经有应当
            "有权",  # 权利而非义务
            "可以",  # 可选而非义务
            "双方",  # 共同行为
        ]
        if any(exc in matched_text for exc in text_exceptions):
            return True
        
        # 基于上下文的例外（BUG-R04部分修复：事实描述句/被动归属句）
        context_exceptions = [
            "如",      # 条件句：如甲方...
            "由",      # 被动归属：由甲方负责
            "最高", "最低", "为",  # 事实描述：设备最高功率为...
            "总额", "共计", "合计", # 金额描述
        ]
        if any(exc in context_before for exc in context_exceptions):
            return True
        
        return False
    
    def _verify_amount_format(self, text: str):
        """验证金额格式"""
        # 检查是否还有¥符号
        if self.AMOUNT_PATTERNS["currency_symbol"].search(text):
            matches = list(self.AMOUNT_PATTERNS["currency_symbol"].finditer(text))
            for match in matches[:3]:  # 只报告前3个
                self.report.add_issue(self._make_issue(
                    rule="金额格式",
                    severity="ERROR",
                    message="发现使用¥符号的金额表示",
                    location=text[max(0, match.start()-20):match.end()+20],
                    suggestion="应改为: 人民币XXXX.00元（人民币X元整）格式"
                ))
        
        # 检查是否有规范的金额格式
        proper_matches = self.AMOUNT_PATTERNS["proper_format"].findall(text)
        if not proper_matches and re.search(r'\d{4,}', text):  # 有数字但没有规范格式
            self.report.add_issue(self._make_issue(
                rule="金额格式",
                severity="WARNING",
                message="可能存在未格式化的金额",
                location="全文",
                suggestion="检查所有金额是否符合'人民币XXXX.00元'格式"
            ))
    
    def _verify_formatting(self, text: str):
        """验证格式规范"""
        # 检查Markdown残留（但保留**第X条**的合法加粗）
        protected_text = text
        placeholder = "##PROTECTED_BOLD##"
        # 保护 **第X条** 和 **第X条 标题** 格式
        CHINESE_NUM = r'[一二三四五六七八九十百千万零〇壹贰叁肆伍陆柒捌玖拾佰仟]+'
        # 保护整个"**第X条 xxx**"加粗块（规则引擎输出格式）
        protected_text = re.sub(rf'\*\*第{CHINESE_NUM}条\s*[^*]*\*\*', lambda m: placeholder + m.group().replace('**', '') + placeholder, protected_text)
        protected_text = re.sub(rf'\*\*第\d+条\s*[^*]*\*\*', lambda m: placeholder + m.group().replace('**', '') + placeholder, protected_text)
        
        md_patterns = [
            (r'\*\*', "粗体标记"),
            (r'^#+\s', "标题标记"),
            (r'^\s*[-*]\s', "列表标记"),
        ]
        
        for pattern, desc in md_patterns:
            if re.search(pattern, protected_text, re.MULTILINE):
                matches = list(re.finditer(pattern, protected_text, re.MULTILINE))
                for match in matches[:2]:
                    self.report.add_issue(self._make_issue(
                        rule="格式清理",
                        severity="ERROR" if desc != "列表标记" else "WARNING",
                        message=f"发现Markdown {desc}残留",
                        location=protected_text[max(0, match.start()-20):match.end()+20],
                        suggestion="应移除所有Markdown标记（**第X条**格式除外）"
                    ))
        
        # 检查英文方括号 — 已禁用（不改变原合同的全角半角）
        # 原合同用英文方括号是合法的，不做转换也不报错
    
    def _verify_structure(self, text: str):
        """验证结构层级"""
        # 检查小标题残留
        bad_headings = ["租赁说明", "租赁售后", "说明", "备注"]
        for heading in bad_headings:
            if heading in text:
                self.report.add_issue(self._make_issue(
                    rule="结构重组",
                    severity="WARNING",
                    message=f"发现可能的小标题残留: '{heading}'",
                    location=text[max(0, text.find(heading)-20):text.find(heading)+len(heading)+20],
                    suggestion="应删除此类小标题，改用1.1/1.2层级结构"
                ))
        
        # 检查层级格式
        # 第一条应该加粗
        CHINESE_NUM = r'[一二三四五六七八九十百千万零〇壹贰叁肆伍陆柒捌玖拾佰仟]+'
        if re.search(rf'^第{CHINESE_NUM}条[^（]', text, re.MULTILINE):
            lines = text.split('\n')
            for line in lines:
                match = re.search(rf'^(第{CHINESE_NUM}条)([^【]|$)', line)
                if match and '**' not in line:
                    self.report.add_issue(self._make_issue(
                        rule="格式统一",
                        severity="INFO",
                        message="'第X条'建议使用加粗格式",
                        location=line.strip()[:50],
                        suggestion="应改为: '**第X条** ...'"
                    ))
    
    def _verify_fixes_applied(self, original: str, cleaned: str):
        """验证原始问题是否已修复"""
        # 统计原始文本中的问题
        original_issues = self._count_issues(original)
        cleaned_issues = self._count_issues(cleaned)
        
        # 检查修复率
        for issue_type, original_count in original_issues.items():
            cleaned_count = cleaned_issues.get(issue_type, 0)
            if cleaned_count >= original_count and original_count > 0:
                self.report.add_issue(self._make_issue(
                    rule="修复验证",
                    severity="ERROR",
                    message=f"{issue_type}未减少: 原始{original_count}处 → 清洗后{cleaned_count}处",
                    location="全文统计",
                    suggestion="AI清洗可能未完全执行该规则"
                ))
    
    # 中文数字字符集（完整版，包含零〇壹贰等）
    CHINESE_NUM = r'[一二三四五六七八九十百千万零〇壹贰叁肆伍陆柒捌玖拾佰仟]+'
    
    def _count_issues(self, text: str) -> Dict[str, int]:
        """
        统计文本中的各类问题数量
        
        BUG-D03修复：复用_verify_term_replacements的条件逻辑，
        而不是简单地用text.count()
        """
        issues = {}
        
        # 统计旧术语（复用条件判断逻辑）
        for old_term, new_term in self.TERM_REPLACEMENTS.items():
            if old_term == "滞纳金":
                # 特殊处理：只在非政府场景计数
                count = 0
                for match in re.finditer(re.escape(old_term), text):
                    start_pos = match.start()
                    end_pos = match.end()
                    context = text[max(0, start_pos-50):min(len(text), end_pos+50)]
                    if not any(keyword in context for keyword in self.DEBT_CONTEXT_KEYWORDS):
                        count += 1
                if count > 0:
                    issues[f"旧术语'{old_term}'"] = count
            elif old_term == "抵消":
                # 特殊处理：只在债务场景计数（来自rule_engine单一数据源）
                count = 0
                for match in re.finditer(re.escape(old_term), text):
                    start_pos = match.start()
                    end_pos = match.end()
                    context = text[max(0, start_pos-30):min(len(text), end_pos+30)]
                    if any(keyword in context for keyword in self.DEBT_DEDUCT_KEYWORDS):
                        count += 1
                if count > 0:
                    issues[f"旧术语'{old_term}'"] = count
            else:
                count = text.count(old_term)
                if count > 0:
                    issues[f"旧术语'{old_term}'"] = count
        
        # 统计¥符号
        issues['¥符号'] = len(self.AMOUNT_PATTERNS["currency_symbol"].findall(text))
        
        # 统计Markdown（保护**第X条**后再统计）
        protected_text = text
        placeholder = "##PROTECTED_BOLD##"
        CHINESE_NUM_CHARS = "一二三四五六七八九十百千万零〇壹贰叁肆伍陆柒捌玖拾佰仟"
        protected_text = re.sub(rf'\*\*(第[{CHINESE_NUM_CHARS}]+条)\*\*', lambda m: f'{placeholder}{m.group(1)}{placeholder}', protected_text)
        protected_text = re.sub(r'\*\*(第\d+条)\*\*', lambda m: f'{placeholder}{m.group(1)}{placeholder}', protected_text)
        issues['Markdown标记'] = len(re.findall(r'\*\*|^#+\s', protected_text, re.MULTILINE))
        
        return issues
    
    # ============================================================
    # 新增验证方法
    # ============================================================
    
    def _verify_entrust_terms(self, text: str):
        """验证委托术语是否按白名单处理"""
        # 检查不在白名单中的"委托"用法
        # 先保护白名单词组
        protected_text = text
        placeholder_prefix = "##ENTRUST_WL_##"
        for i, wl_word in enumerate(self.ENTRUST_WHITELIST):
            protected_text = protected_text.replace(wl_word, f"{placeholder_prefix}{i}{placeholder_prefix}")
        
        # 检查剩余的"委托"
        remaining_entrust = list(re.finditer(r'委托', protected_text))
        for match in remaining_entrust:
            start_pos = match.start()
            end_pos = match.end()
            context = protected_text[max(0, start_pos-30):min(len(protected_text), end_pos+30)]
            # 恢复占位符为原始文本用于显示
            display_context = context
            for i, wl_word in enumerate(self.ENTRUST_WHITELIST):
                display_context = display_context.replace(f"{placeholder_prefix}{i}{placeholder_prefix}", wl_word)
            
            self.report.add_issue(self._make_issue(
                rule="委托术语白名单",
                severity="WARNING",
                message=f"发现未在白名单中的'委托'用法",
                location=display_context[:80],
                suggestion="应替换为'约定'或对应称谓（白名单词组除外）"
            ))
    
    def _verify_header_protection(self, text: str):
        """验证合同首部是否被正确保护"""
        lines = text.split('\n')
        CHINESE_NUM = r'[一二三四五六七八九十百千万零〇壹贰叁肆伍陆柒捌玖拾佰仟\d]+'
        
        # 检查是否有甲乙方信息被编入条款
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            
            # 检测"第X条 甲方为XX公司"这种模式
            article_match = re.search(rf'第{CHINESE_NUM}条', stripped)
            if article_match:
                after_article = stripped[article_match.end():].strip()
                # 检查条款正文是否包含甲乙方主体信息
                party_patterns = [
                    r'[甲乙丙丁]方[为是]',          # "甲方为XX公司"
                    r'[甲乙丙丁]方[（(].*?[)）].*?公司',  # "甲方（服务接受方）XX公司"
                ]
                for pattern in party_patterns:
                    if re.search(pattern, after_article):
                        self.report.add_issue(self._make_issue(
                            rule="首部保护",
                            severity="ERROR",
                            message="甲乙方信息被错误编入条款正文",
                            location=stripped[:80],
                            suggestion="甲乙方信息应在首部独立展示，不得编入条款编号"
                        ))
                        break
    
    def _verify_hierarchy(self, text: str):
        """验证层级递进是否正确"""
        lines = text.split('\n')
        CHINESE_NUM = r'[一二三四五六七八九十百千万零〇壹贰叁肆伍陆柒捌玖拾佰仟\d]+'
        
        i = 0
        while i < len(lines):
            stripped = lines[i].strip()
            
            # 检测一级编号
            if re.search(rf'^\*{{0,2}}第{CHINESE_NUM}条', stripped):
                # 检查后续行是否有三级编号但没有二级编号
                has_secondary = False
                has_tertiary_only = False
                j = i + 1
                
                while j < len(lines):
                    next_stripped = lines[j].strip()
                    
                    # 空行跳过
                    if not next_stripped:
                        j += 1
                        continue
                    
                    # 遇到下一个一级编号停止
                    if re.search(rf'^\*{{0,2}}第{CHINESE_NUM}条', next_stripped):
                        break
                    
                    # 检测二级编号
                    if re.search(r'^\d+\.\d+\s', next_stripped):
                        has_secondary = True
                    
                    # 检测三级编号
                    if re.search(r'^[（(]\d+[）)]\s*', next_stripped):
                        if not has_secondary:
                            has_tertiary_only = True
                    
                    j += 1
                
                if has_tertiary_only:
                    self.report.add_issue(self._make_issue(
                        rule="层级递进",
                        severity="ERROR",
                        message="一级编号后直接使用三级编号，缺少二级编号",
                        location=stripped[:60],
                        suggestion="一级编号后若无二级分层需要，内容应使用自然段落书写"
                    ))
            
            i += 1
    
    def _verify_no_content_addition(self, original: str, cleaned: str):
        """验证AI是否添加了原文不存在的内容"""
        orig_len = len(original.strip())
        clean_len = len(cleaned.strip())
        
        # 长度检测
        if orig_len > 0:
            growth_rate = (clean_len - orig_len) / orig_len
            if growth_rate > 0.15:
                self.report.add_issue(self._make_issue(
                    rule="内容添加检测",
                    severity="WARNING",
                    message=f"输出比输入长{growth_rate*100:.1f}%，AI可能添加了内容",
                    location="全文统计",
                    suggestion="检查是否有原文不存在的内容被添加"
                ))
        
        # 甲乙方信息编入条款检测
        party_names = []
        for match in re.finditer(
            r'[甲乙丙丁]方[（(][^）)]+[)）][：:]\s*([\w\u4e00-\u9fff（）()]+?(?:公司|有限|集团|企业|单位|部门|院|所|中心|协会|基金))',
            original
        ):
            name = match.group(1).strip()
            if name and len(name) >= 4:
                party_names.append(name)
        
        if party_names:
            CHINESE_NUM = r'[一二三四五六七八九十百千万零〇壹贰叁肆伍陆柒捌玖拾佰仟\d]+'
            first_article = re.search(rf'第{CHINESE_NUM}条', cleaned)
            if first_article:
                article_body = cleaned[first_article.start():]
                # 排除签署区
                sig_match = re.search(r'[甲乙丙丁]方.*?盖章', article_body)
                before_sig = article_body[:sig_match.start()] if sig_match else article_body
                
                for name in party_names:
                    if name in before_sig:
                        self.report.add_issue(self._make_issue(
                            rule="内容添加检测",
                            severity="ERROR",
                            message=f"甲乙方名称'{name}'出现在条款正文中",
                            location=name,
                            suggestion="甲乙方信息应在首部独立展示，不应写入条款正文"
                        ))
    
    # ============================================================
    # ============================================================

    def _verify_date_format(self, text: str):
        """验证日期格式是否统一（规范2.1）"""
        non_standard_patterns = [
            (re.compile(r'\d{4}\s*[-/]\s*\d{1,2}\s*[-/]\s*\d{1,2}'), "YYYY-MM-DD/YYYY/MM/DD"),
            (re.compile(r'\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*号'), "YYYY年M月D号"),
        ]

        for pattern, desc in non_standard_patterns:
            matches = list(pattern.finditer(text))
            for match in matches[:3]:
                self.report.add_issue(self._make_issue(
                    rule="日期格式",
                    severity="ERROR",
                    message=f"发现非标准日期格式（{desc}）",
                    location=match.group(),
                    suggestion="应改为: YYYY年M月D日 格式"
                ))

    def _verify_near_synonyms(self, text: str):
        """验证近义术语是否统一（规范1.6）"""
        near_synonym_pairs = [
            ("定金", "订金"),
            ("撤回", "撤销"),
        ]

        for word_a, word_b in near_synonym_pairs:
            has_a = word_a in text
            has_b = word_b in text
            if has_a and has_b:
                # 检查是否已经有标记（说明规则引擎已处理过）
                has_marker = f"【近义术语待统一" in text
                if not has_marker:
                    self.report.add_issue(self._make_issue(
                        rule="近义术语",
                        severity="WARNING",
                        message=f"'{word_a}'与'{word_b}'同时出现，可能混用",
                        location=f"'{word_a}'和'{word_b}'均在文中出现",
                        suggestion=f"应根据法律含义统一使用，或标注【待确认】"
                    ))

    def _verify_sentence_completeness(self, text: str):
        """验证句式是否完整（规范3.1）"""
        lines = text.split('\n')
        # 规则引擎加标记后，行变成"付款时间：【句式待改写...】"，不是纯冒号结尾
        # 所以需要两种检测模式
        colon_heading_pattern = re.compile(r'^([\u4e00-\u9fff]{2,8})[：:]\s*$')
        marked_heading_pattern = re.compile(r'^([\u4e00-\u9fff]{2,8})[：:]\s*【句式待改写')
        legit_headings = {"甲方", "乙方", "丙方", "丁方", "鉴于", "附件", "说明"}

        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                continue

            # 模式1: 带【句式待改写】标记的行（规则引擎已标记，AI未改写）
            marked_match = marked_heading_pattern.match(stripped)
            if marked_match:
                heading = marked_match.group(1)
                if heading not in legit_headings and not re.search(r'[甲乙丙丁]方', heading):
                    self.report.add_issue(self._make_issue(
                        rule="句式完整性",
                        severity="ERROR",
                        message=f"'{heading}：'句式未改写，仍保留【句式待改写】标记",
                        location=stripped[:60],
                        suggestion="应改写为完整的主谓宾句子"
                    ))
                continue

            # 模式2: 纯冒号结尾的行（未被规则引擎标记的新问题）
            match = colon_heading_pattern.match(stripped)
            if not match:
                continue

            heading = match.group(1)
            if heading in legit_headings:
                continue
            if re.search(r'[甲乙丙丁]方', heading):
                continue
            if re.search(r'第[一二三四五六七八九十百千万\d]+条', heading):
                continue

            # 没有标记但有小标题+冒号模式
            next_has_content = (i + 1 < len(lines) and
                                len(lines[i + 1].strip()) > 5)
            if next_has_content:
                self.report.add_issue(self._make_issue(
                    rule="句式完整性",
                    severity="WARNING",
                    message=f"发现'小标题+冒号'句式: '{heading}：'",
                    location=stripped[:60],
                    suggestion="应改写为完整的主谓宾句子"
                ))

    def _verify_reference_clarity(self, text: str):
        """验证指代是否明确（规范1.4）"""
        lines = text.split('\n')

        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                continue

            # 检测模糊指代"其"（排除合法用法如"其他""其中""其实"）
            its_matches = re.finditer(r'(?<![其])其(?![他她它中事实上])', stripped)
            for match in its_matches:
                # 获取上下文
                context = stripped[max(0, match.start()-10):match.end()+10]
                # 排除"尤其""极其"等
                if re.search(r'[尤极]其', context):
                    continue
                # 只对可能引起歧义的"其"报WARNING（不是所有"其"都有问题）
                # 如果"其"后面直接跟名词，可能是模糊指代
                after_its = stripped[match.end():match.end()+4]
                if re.search(r'^[^他她它中事实上].*?[的将]', after_its):
                    self.report.add_issue(self._make_issue(
                        rule="指代明确",
                        severity="WARNING",
                        message=f"发现可能模糊的指代'其'",
                        location=context[:60],
                        suggestion="应明确指代对象，如'甲方''乙方''该设备'等"
                    ))
                    break  # 每行只报一次

    def _verify_signature_and_appendix(self, text: str):
        """验证签署区和附件格式（规范2.3.2/2.3.3）"""
        CHINESE_NUM = r'[一二三四五六七八九十百千万零〇壹贰叁肆伍陆柒捌玖拾佰仟\d]+'

        # 检查签署区是否被编号
        sig_match = re.search(r'[甲乙丙丁]方.*?[（(].*?[)）][：:]', text)
        if sig_match:
            # 检查签署区前是否有条款编号
            before_sig = text[:sig_match.start()]
            last_article = list(re.finditer(rf'第{CHINESE_NUM}条', before_sig))
            if last_article:
                # 检查签署区和最后一条之间是否还有内容
                between = before_sig[last_article[-1].end():].strip()
                # 如果中间内容很少（<50字符），签署区紧跟最后一条
                if len(between) < 50:
                    self.report.add_issue(self._make_issue(
                        rule="签署区保护",
                        severity="WARNING",
                        message="签署区可能未被独立处理",
                        location=text[sig_match.start():sig_match.start()+40],
                        suggestion="签署区应在最后一条之后独立展示，不得添加编号"
                    ))

        # 检查附件标题是否独立
        appendix_match = re.search(r'附件[一二三四五六七八九十\d]', text)
        if appendix_match:
            appendix_start = appendix_match.start()
            # 检查附件标题前是否有多余编号
            before_appendix = text[:appendix_start].strip()
            if before_appendix.endswith('。') or before_appendix.endswith('；'):
                pass  # 正常：前文结束
            elif re.search(rf'第{CHINESE_NUM}条\s*$', before_appendix[-30:]):
                self.report.add_issue(self._make_issue(
                    rule="附件保护",
                    severity="ERROR",
                    message="附件标题紧跟条款编号，未独立处理",
                    location=before_appendix[-30:] + text[appendix_start:appendix_start+20],
                    suggestion="附件应在主合同签署区之后另起，拥有独立标题"
                ))

    def _verify_nested_yingdang(self, text: str):
        """验证是否存在嵌套应当（规范1.5.2）
        
        v4.2改进: 区分真嵌套和伪嵌套
        - 真嵌套：同一主语在一句中出现两次"应当"（应删除内层）
        - 伪嵌套：不同主语各自带"应当"（合法的并列义务，放行）
        - 伪嵌套：同一主语不同义务被句号/分号隔开（合法的连续义务，放行）
        """
        subject_pattern = r'(?:甲方|乙方|双方|任一方|违约方|遭遇方|遭受方|非违约方|守约方)'
        lines = text.split('\n')
        
        for line in lines:
            # 跳过条款标题行
            if re.match(r'\*\*第.{1,5}条', line):
                continue
            
            yingdang_positions = [m.start() for m in re.finditer('应当', line)]
            
            if len(yingdang_positions) < 2:
                continue
            
            for i in range(len(yingdang_positions) - 1):
                pos1 = yingdang_positions[i]
                pos2 = yingdang_positions[i + 1]
                between = line[pos1 + 2:pos2]
                
                # 中间有句号/分号 → 不同句子，伪嵌套
                if re.search(r'[。；]', between):
                    continue
                
                # 找第一个应当前的最近主语（用findall取最后一个，即离"应当"最近的）
                before_first = line[max(0, pos1 - 20):pos1]
                first_subjects = re.findall(subject_pattern, before_first)
                first_subject = first_subjects[-1] if first_subjects else None
                
                # 找第二个应当前的最近主语
                before_second = line[max(0, pos2 - 20):pos2]
                second_subjects = re.findall(subject_pattern, before_second)
                second_subject = second_subjects[-1] if second_subjects else None
                
                # 不同主语 → 伪嵌套（各自义务），放行
                if first_subject and second_subject and first_subject != second_subject:
                    continue
                
                # 同一主语/无主语 + 同一句 → 真嵌套
                context = line[max(0, pos1 - 10):min(len(line), pos2 + 10)]
                self.report.add_issue(self._make_issue(
                    rule="嵌套应当",
                    severity="ERROR",
                    message="发现嵌套的'应当'，违反规范1.5.2",
                    location=context[:80],
                    suggestion=f"只保留最外层的'应当'，内层删除。位置：'{line[max(0, pos2-5):pos2+7]}' → 删除'{line[pos2:pos2+2]}'"
                ))

    # ============================================================
    # 新增验证方法（第十轮优化：每条Prompt规则必须有自检）
    # ============================================================

    def _verify_term_consistency(self, text: str):
        """验证术语一致性（规范1.3）——检测同义混用"""
        # 已知的同义混用对（和义务Prompt中列的一致）
        synonym_pairs = [
            ("项目所在地", "工程地点"),
            ("合同", "协议"),  # 仅当指同一文件时才算混用
        ]
        
        for word_a, word_b in synonym_pairs:
            has_a = word_a in text
            has_b = word_b in text
            if has_a and has_b:
                # "合同"和"协议"同时出现是正常的（如"本合同和协议附件"）
                # 只有在可能指同一概念时才警告
                if word_a == "合同" and word_b == "协议":
                    # 检查是否有"本合同"和"本协议"同时出现（说明指同一文件）
                    has_ben_contract = "本合同" in text
                    has_ben_agreement = "本协议" in text
                    if has_ben_contract and has_ben_agreement:
                        self.report.add_issue(self._make_issue(
                            rule="术语一致性",
                            severity="WARNING",
                            message=f"'本合同'与'本协议'同时出现，可能指同一文件",
                            location=f"'本合同'和'本协议'均在文中出现",
                            suggestion="如果指同一文件，应全文统一为'本合同'或'本协议'"
                        ))
                else:
                    self.report.add_issue(self._make_issue(
                        rule="术语一致性",
                        severity="WARNING",
                        message=f"'{word_a}'与'{word_b}'同时出现，可能混用",
                        location=f"'{word_a}'和'{word_b}'均在文中出现",
                        suggestion=f"应统一使用一个术语"
                    ))

    def _verify_table_protection(self, original: str, cleaned: str):
        """验证表格结构是否被AI破坏（结构Prompt）"""
        # 检测 pipe 表格（|...|...|）
        orig_pipe_rows = len(re.findall(r'^\|.*\|$', original, re.MULTILINE))
        clean_pipe_rows = len(re.findall(r'^\|.*\|$', cleaned, re.MULTILINE))
        
        if orig_pipe_rows > 0:
            # 原文有表格，检查清洗后是否还在
            if clean_pipe_rows == 0:
                self.report.add_issue(self._make_issue(
                    rule="表格保护",
                    severity="ERROR",
                    message=f"原文有{orig_pipe_rows}行pipe表格，清洗后完全消失",
                    location="全文",
                    suggestion="表格结构被破坏，应恢复表格格式"
                ))
            elif clean_pipe_rows < orig_pipe_rows - 2:
                # 允许小幅变化（如标题行合并），但大幅减少说明被拆散
                self.report.add_issue(self._make_issue(
                    rule="表格保护",
                    severity="WARNING",
                    message=f"pipe表格行数从{orig_pipe_rows}减少到{clean_pipe_rows}，可能被拆散",
                    location="全文",
                    suggestion="检查表格结构是否完整保留"
                ))
        
        # 检测 grid 表格（+---+---+）
        orig_grid_rows = len(re.findall(r'^\+[-=+]+\+', original, re.MULTILINE))
        clean_grid_rows = len(re.findall(r'^\+[-=+]+\+', cleaned, re.MULTILINE))
        
        if orig_grid_rows > 0 and clean_grid_rows == 0:
            self.report.add_issue(self._make_issue(
                rule="表格保护",
                severity="ERROR",
                message=f"原文有{orig_grid_rows}行grid表格，清洗后完全消失",
                location="全文",
                suggestion="grid表格结构被破坏，应恢复表格格式"
            ))

    def _verify_punctuation(self, text: str):
        """验证标点 — 已禁用（不改变原合同的全角半角）"""
        # 不再检查英文标点残留，原合同用什么标点是合法的
        pass

    def _verify_fullwidth_characters(self, text: str):
        """验证是否残留全角数字/英文字母/全角间隔号"""
        issues = []

        # 检查全角数字 ０-９（U+FF10-U+FF19）
        fullwidth_digit_pattern = re.compile(r'[\uff10-\uff19]')
        digit_matches = list(fullwidth_digit_pattern.finditer(text))
        if digit_matches:
            examples = []
            for m in digit_matches[:3]:
                ctx = text[max(0, m.start()-5):m.end()+5]
                examples.append(ctx)
            issues.append(f"发现{len(digit_matches)}处全角数字（如{examples}），应使用半角数字")

        # 检查全角英文字母 Ａ-Ｚ（U+FF21-U+FF3A）、ａ-ｚ（U+FF41-U+FF5A）
        fullwidth_alpha_pattern = re.compile(r'[\uff21-\uff3a\uff41-\uff5a]')
        alpha_matches = list(fullwidth_alpha_pattern.finditer(text))
        if alpha_matches:
            examples = []
            for m in alpha_matches[:3]:
                ctx = text[max(0, m.start()-5):m.end()+5]
                examples.append(ctx)
            issues.append(f"发现{len(alpha_matches)}处全角英文字母（如{examples}），应使用半角字母")

        # 检查全角间隔号 ．（U+FF0E）在数字上下文中
        fullwidth_period_pattern = re.compile(r'\d\uff0e\d')
        period_matches = list(fullwidth_period_pattern.finditer(text))
        if period_matches:
            examples = [m.group() for m in period_matches[:3]]
            issues.append(f"发现{len(period_matches)}处全角间隔号(．)用于编号（如{examples}），应使用半角句号(.)")

        for issue_msg in issues:
            self.report.add_issue(self._make_issue(
                rule="全角字符",
                severity="ERROR",
                message=issue_msg,
                location="全文",
                suggestion="数字和英文字母必须使用半角（规则引擎会自动修正）"
            ))

    def _verify_uncertainty_markers(self, original: str, cleaned: str):
        """验证无法确定时的标记是否被保留（规范6.6）"""
        # 检查规则引擎添加的标记是否被AI删除
        markers = [
            "【近义术语待统一",
            "【句式待改写",
            "【待确认】",
            "【需人工审核】",
            "【修正说明】",
        ]
        
        for marker in markers:
            if marker in original and marker not in cleaned:
                self.report.add_issue(self._make_issue(
                    rule="标记保留",
                    severity="ERROR",
                    message=f"规则引擎标记'{marker}'被AI删除",
                    location=f"原文有'{marker}'，清洗后消失",
                    suggestion="应保留标记直到人工审核，或由AI正确处理后移除"
                ))
        
        # 反向检查：【句式待改写】标记应该被AI处理掉（改写句子），不应原样保留
        if "【句式待改写" in cleaned:
            # 如果标记还在，说明AI没处理
            self.report.add_issue(self._make_issue(
                rule="标记处理",
                severity="ERROR",
                message="【句式待改写】标记仍未被处理",
                location="全文",
                suggestion="AI应将标记处的句式改写为完整句子后移除标记"
            ))

    def quick_check(self, text: str) -> Tuple[bool, List[str]]:
        """
        快速检查，返回是否通过和错误列表
        
        Args:
            text: 清洗后的文本
        
        Returns:
            (是否通过, 错误列表)
        """
        errors = []
        
        # 检查关键术语
        for old_term, new_term in self.TERM_REPLACEMENTS.items():
            if old_term in text:
                errors.append(f"术语未替换: '{old_term}' → 应为'{new_term}'")
        
        # 检查金额格式
        if self.AMOUNT_PATTERNS["currency_symbol"].search(text):
            errors.append("金额格式错误: 发现¥符号，应使用'人民币X元'格式")
        
        # 检查Markdown（但要保护**第X条**格式）
        protected_text = text
        placeholder = "##PROTECTED_BOLD##"
        CHINESE_NUM = r'[一二三四五六七八九十百千万零〇壹贰叁肆伍陆柒捌玖拾佰仟]+'
        protected_text = re.sub(rf'\*\*(第{CHINESE_NUM}条)\*\*', lambda m: f'{placeholder}{m.group(1)}{placeholder}', protected_text)
        protected_text = re.sub(r'\*\*(第\d+条)\*\*', lambda m: f'{placeholder}{m.group(1)}{placeholder}', protected_text)
        
        if '**' in protected_text or re.search(r'^#+\s', protected_text, re.MULTILINE):
            errors.append("格式错误: 发现Markdown标记残留")
        
        return len(errors) == 0, errors


def verify_cleaned_contract(original: str, cleaned: str, verbose: bool = True) -> bool:
    """
    便捷函数：验证清洗后的合同
    
    Args:
        original: 原始文本
        cleaned: 清洗后的文本
        verbose: 是否打印详细报告
    
    Returns:
        是否通过验证（无ERROR级别问题）
    """
    verifier = ContractSelfVerifier()
    report = verifier.verify(original, cleaned)
    
    if verbose:
        print(report)
    
    # 如果有ERROR级别的问题，返回失败
    error_count = sum(1 for issue in report.issues if issue.severity == "ERROR")
    return error_count == 0


if __name__ == '__main__':
    # 测试示例
    original = """
第一条 乙方应缴纳服务费用¥5000元
乙方**提供**技术支持
"""
    
    cleaned = """
**第一条** 乙方应当支付服务费用人民币5000.00元（人民币伍仟元整）
乙方应当提供技术支持
"""
    
    verify_cleaned_contract(original, cleaned)
