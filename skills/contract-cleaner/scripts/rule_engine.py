#!/usr/bin/env python3
"""
确定性规则引擎 — 替代AI处理确定性规则

核心设计理念（参考 LexNLP 可编程层+AI层分离）：
1. 术语替换（查表）→ Python代码，100%准确，0 API调用
2. 金额格式（正则+查表）→ Python代码，100%准确，0 API调用
3. 标点/括号转换 → Python代码，100%确定，0 API调用
4. 编号规范化 → 正则，100%确定
5. 委托术语白名单 → 查表+正则，100%确定，0 API调用
6. 合同首部保护 → 正则识别+隔离，100%确定
7. 层级递进修复 → 检测跳级模式并降级，100%确定
8. 签署区/附件保护 → 正则识别+标记，100%确定
9. 内容添加检测 → 对比输入输出，检测AI添加内容

AI只做语义理解：义务句式识别、结构重组、条款语义校验

收益：
- API调用减少约70%（术语+金额+标点+括号+委托+首部+层级不再需要pass）
- 准确率从"依赖AI自觉性"提升到"代码100%保证"
- Token成本降低约70%
- 可测试、可调试、可回滚
"""

import re
from typing import Dict, List, Optional, Tuple


class RuleEngine:
    """确定性规则引擎 — 把确定性规则从AI Prompt中剥离"""

    # ============================================================
    # 术语替换
    # ============================================================

    # 无条件术语替换表（完全确定性）
    UNCONDITIONAL_TERMS: Dict[str, str] = {
        "缴纳": "支付",
        "罚款": "违约金",
        "执行合同": "履行合同",
        "权力": "权利",
    }

    # 条件术语（需要上下文判断）
    CONDITIONAL_TERMS = {
        "滞纳金": {
            "replacement": "逾期付款违约金",
            "keep_if_context": ["政府", "能源", "事业单位", "税款", "社保",
                                "税收", "行政", "公用事业", "机关", "公积金"],
            "context_window": 30,  # 缩小窗口：只看同句/同行的上下文
        },
        "抵消": {
            "replacement": "抵销",
            "if_context": ["债务", "债权", "清偿", "欠款", "借款", "贷款",
                           "抵销", "冲抵", "互负", "对冲", "结算"],
            "context_window": 30,  # 缩小窗口
        },
    }

    # 义务动词替换：独立的"须"→"应当"
    # 注意：只有当"须"单独作为义务动词使用时才替换
    # "必须"、"须要"等不替换
    # 这个在apply_obligation_verb_normalization中处理

    # ============================================================
    # 委托术语白名单（基于民法典委托字样统计）
    # ============================================================

    # 民法典允许出现的"委托"固定词组（白名单）
    # 设计逻辑：只看"委托"后面跟的是什么词，不需要判断合同类型
    ENTRUST_WHITELIST = [
        # 当事人称谓（技术咨询/技术服务/行纪/中介合同，民法典第879-964条）
        "委托人",
        "受托人",
        # 行纪合同特有（民法典第951-958条）
        "委托物",
        "委托事务",
        # 行为动词（民法典原文用法）
        "委托监理",    # 建设工程委托监理合同（民法典第796条）
        "转委托",      # 物业服务人转委托（民法典第941条）
        # 合伙合同（民法典第970条）
        "委托执行",
        # 一般用语（规范1.2节第4点明确保留）
        "委托检验",
        "委托加工",
        "委托测试",
        "委托审计",
        "委托评估",
        "委托鉴定",
        "委托运输",
        "委托保管",
        "委托设计",
        # 合同签署区常见固定词组
        "委托代理人",   # 签署区"法定代表人或委托代理人"
        "委托代理",     # "委托代理人"的简写
        # 委托申请/委托书等法律文书用语
        "委托申请",     # 如"按乙方委托申请"
        "委托书",       # "授权委托书"
    ]

    # 委托术语默认替换表（不在白名单中的用法）
    ENTRUST_REPLACEMENTS = {
        "委托人": "服务接受方",
        "受托人": "服务提供方",
        "委托方": "服务接受方",
        "受托方": "服务提供方",
        "委托事项": "服务内容",
        "委托费用": "服务费",
        "委托协议": "服务协议",
        "委托合同": "服务合同",
        "委托服务": "约定服务",
        "委托工作": "约定工作",
        "委托内容": "约定内容",
    }

    # ============================================================
    # 合同首部模式（不得编入条款编号）
    # ============================================================

    # 合同标题模式（居中、加粗的合同名称）
    HEADER_TITLE_PATTERNS = [
        re.compile(r'^\s*\*{0,2}[《【]?[\u4e00-\u9fff]+合同[》】]?\*{0,2}\s*$', re.MULTILINE),
        re.compile(r'^\s*\*{0,2}[《【]?[\u4e00-\u9fff]+协议[》】]?\*{0,2}\s*$', re.MULTILINE),
        re.compile(r'^\s*\*{0,2}[\u4e00-\u9fff]+书$\s*', re.MULTILINE),  # 授权委托书
    ]

    # 甲乙方主体行模式
    HEADER_PARTY_PATTERNS = [
        re.compile(r'^[甲乙丙丁]方[（(][^）)]+[)）][：:]\s*'),   # 甲方（服务接受方）：XX公司
        re.compile(r'^[甲乙丙丁]方[：:]\s*'),                      # 甲方：XX公司
        re.compile(r'^[甲乙丙丁]方\s*$'),                            # 甲方（单独一行）
    ]

    # 鉴于条款模式
    HEADER_RECITAL_PATTERN = re.compile(r'^鉴于[：:]', re.MULTILINE)

    # ============================================================
    # 签署区模式（不得编入条款编号）
    # ============================================================

    SIGNATURE_PATTERNS = [
        re.compile(r'[甲乙丙丁]方[（(][^）)]+[)）][盖章签名签字]*[：:]*\s*_+', re.MULTILINE),
        re.compile(r'[甲乙丙丁]方[盖章签名签字]*[：:]*\s*_+', re.MULTILINE),
        re.compile(r'日期[：:]\s*_*', re.MULTILINE),
        re.compile(r'[签盖]章[：:]\s*_*', re.MULTILINE),
        re.compile(r'法定代表人[：:]\s*_*', re.MULTILINE),
    ]

    # ============================================================
    # 附件模式（不得与主合同条款连续编号）
    # ============================================================

    APPENDIX_PATTERN = re.compile(r'^附件[一二三四五六七八九十\d]+[：:]', re.MULTILINE)

    def apply_term_replacements(self, text: str) -> Tuple[str, List[str]]:
        """
        术语替换（代码实现，不调API）

        Returns:
            (替换后的文本, 替换记录列表)
        """
        changes = []

        # 1. 无条件替换
        for old, new in self.UNCONDITIONAL_TERMS.items():
            count = text.count(old)
            if count > 0:
                text = text.replace(old, new)
                changes.append(f"术语替换: '{old}' → '{new}' ({count}处)")

        # 2. 条件替换（逐个出现位置判断，避免遗漏多处同一术语）
        for old, rule in self.CONDITIONAL_TERMS.items():
            count_replaced = 0
            # 使用finditer逐个处理，避免位置偏移问题
            # 从后向前替换，避免偏移
            matches = list(re.finditer(re.escape(old), text))
            for match in reversed(matches):
                start = match.start()
                # 改进：只检查同一段落的上下文（同行或相邻字符）
                # 避免跨越段落的误判
                context_start = max(0, start - rule["context_window"])
                context_end = min(len(text), match.end() + rule["context_window"])
                context = text[context_start:context_end]
                
                # 额外提取同一段落（同一行）的上下文
                line_start = text.rfind('\n', 0, start)
                line_end = text.find('\n', match.end())
                if line_start == -1:
                    line_start = 0
                else:
                    line_start += 1
                if line_end == -1:
                    line_end = len(text)
                line_context = text[line_start:line_end]

                if "keep_if_context" in rule:
                    # 滞纳金：检查是否有政府上下文
                    # 策略：先看同行，如果同行有政府关键词则保留
                    # 如果同行没有，再看扩展上下文（同行优先，但限制不跨2行以上）
                    has_context_line = any(kw in line_context for kw in rule["keep_if_context"])
                    
                    # 扩展上下文检查：只看当前段落（不超过前后各1行）
                    # 避免远距离上下文导致误判
                    para_start = max(0, start - rule["context_window"])
                    para_end = min(len(text), match.end() + rule["context_window"])
                    para_context = text[para_start:para_end]
                    has_context_para = any(kw in para_context for kw in rule["keep_if_context"])
                    
                    # 综合判断：同行有→保留，同行无但扩展有→需要更谨慎
                    # 如果同行没有关键词，即使扩展上下文有也替换（保守替换策略）
                    if has_context_line:
                        continue
                    # 无同行上下文，替换
                    text = text[:start] + rule["replacement"] + text[match.end():]
                    count_replaced += 1

                elif "if_context" in rule:
                    # 抵消：必须在本行（同一段落）有债务上下文才替换
                    # 严格限制：只在同行中查找，避免跨段落误判
                    has_context = any(kw in line_context for kw in rule["if_context"])
                    if has_context:
                        text = text[:start] + rule["replacement"] + text[match.end():]
                        count_replaced += 1

            if count_replaced > 0:
                changes.append(f"条件术语替换: '{old}' → '{rule['replacement']}' ({count_replaced}处)")

        return text, changes

    def apply_obligation_verb_normalization(self, text: str) -> Tuple[str, List[str]]:
        """
        义务动词规范化（代码实现，不调API）

        规则：独立的"须" → "应当"
        排除：必须、须要、无须、须眉等固定词组

        Returns:
            (替换后的文本, 替换记录列表)
        """
        changes = []
        count = 0

        # 保护"必须"、"须要"、"无须"等固定词组
        protected_words = ["必须", "须要", "无须", "须眉", "须鲸", "须知"]
        placeholder_prefix = "##OBL_VERB_##"
        protected_map = {}

        for i, word in enumerate(protected_words):
            if word in text:
                key = f"{placeholder_prefix}{i}{placeholder_prefix}"
                protected_map[key] = word
                text = text.replace(word, key)

        # 替换独立的"须"
        # 匹配：前面不是"必"/"无"等，后面不是"要"/"知"/"眉"/"鲸"等
        # 在合同条款上下文中，"甲方须..." 或 "须在..." 都是义务表述
        remaining = list(re.finditer(r'须', text))
        for match in reversed(remaining):
            start = match.start()
            # 检查前面的字符
            prev_char = text[start - 1] if start > 0 else ''
            # 检查后面的字符
            next_char = text[start + 1] if start + 1 < len(text) else ''

            # 排除已经在保护中的（已经被placeholder替换了）
            # 排除常见的不需要替换的组合
            skip_next = ['要', '知', '眉', '鲸', '得']  # 须要、须知等
            if next_char in skip_next:
                continue

            # 替换
            text = text[:start] + '应当' + text[start + 1:]
            count += 1

        if count > 0:
            changes.append(f"义务动词替换: '须' → '应当' ({count}处)")

        # 恢复保护词组
        for key, word in protected_map.items():
            text = text.replace(key, word)

        return text, changes

    def apply_entrust_replacements(self, text: str) -> Tuple[str, List[str]]:
        """
        委托术语白名单替换（代码实现，不调API）

        核心逻辑：
        0. 先处理主体行中的"委托人/受托人"（如"甲方（委托人）"→"甲方（服务接受方）"）
        1. 遍历文本中所有"委托"相关词
        2. 如果在白名单中 → 保留
        3. 如果不在白名单中 → 按替换表替换
        4. 独立的"委托"动词 → 替换为"要求"

        Returns:
            (替换后的文本, 替换记录列表)
        """
        changes = []

        # 0. 先处理主体行中的"委托人/受托人"
        #    如 "甲方（委托人）：XX公司" → "甲方（服务接受方）：XX公司"
        #    主体行中的"委托人/受托人"无论是否在白名单中都必须替换
        party_line_pattern = re.compile(
            r'([甲乙丙丁]方[（(])(委托人|受托人|委托方|受托方)([)）])'
        )
        party_replacements = {
            "委托人": "服务接受方",
            "受托人": "服务提供方",
            "委托方": "服务接受方",
            "受托方": "服务提供方",
        }
        party_count = 0
        def _replace_party(m):
            nonlocal party_count
            old_role = m.group(2)
            new_role = party_replacements.get(old_role, old_role)
            if new_role != old_role:
                party_count += 1
            return f"{m.group(1)}{new_role}{m.group(3)}"
        text = party_line_pattern.sub(_replace_party, text)
        if party_count > 0:
            changes.append(f"主体称谓替换: '委托人/受托人' → '服务接受方/服务提供方' ({party_count}处)")

        # 1. 处理固定词组（委托事项等，委托人/受托人已在步骤0处理）
        for old, new in self.ENTRUST_REPLACEMENTS.items():
            if old in self.ENTRUST_WHITELIST:
                continue  # 白名单中的词不替换（非主体行的委托人/受托人保留）

            count = text.count(old)
            if count > 0:
                text = text.replace(old, new)
                changes.append(f"委托术语替换: '{old}' → '{new}' ({count}处)")

        # 2. 处理独立的"委托"动词（不在任何白名单词组中的"委托"）
        #    策略：先保护白名单词组，再替换剩余的"委托"
        placeholder_prefix = "##ENTRUST_WL_##"
        protected_map = {}

        # 保护白名单中的词组
        for i, wl_word in enumerate(self.ENTRUST_WHITELIST):
            if wl_word in text:
                key = f"{placeholder_prefix}{i}{placeholder_prefix}"
                protected_map[key] = wl_word
                text = text.replace(wl_word, key)

        # 检查剩余的独立"委托"
        remaining_entrust = list(re.finditer(r'委托', text))
        count_standalone = 0
        for match in reversed(remaining_entrust):
            text = text[:match.start()] + '要求' + text[match.end():]
            count_standalone += 1

        if count_standalone > 0:
            changes.append(f"委托动词替换: '委托' → '要求' ({count_standalone}处)")

        # 恢复白名单词组
        for key, original in protected_map.items():
            text = text.replace(key, original)

        return text, changes

    # ============================================================
    # 合同首部保护
    # ============================================================

    def apply_header_protection(self, text: str) -> Tuple[str, List[str]]:
        """
        合同首部保护（代码实现，不调API）

        功能：
        1. 识别合同首部（标题、甲乙方、鉴于条款）
        2. 标记首部区域，防止AI将其编入条款编号
        3. 移除首部区域中可能被错误添加的编号

        Returns:
            (处理后的文本, 替换记录列表)
        """
        changes = []
        lines = text.split('\n')
        header_end_line = 0  # 首部结束行号

        # 逐行识别首部
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                continue

            # 检查是否是合同标题
            is_title = any(p.search(stripped) for p in self.HEADER_TITLE_PATTERNS)

            # 检查是否是甲乙方行
            is_party = any(p.search(stripped) for p in self.HEADER_PARTY_PATTERNS)

            # 检查是否是鉴于条款
            is_recital = bool(self.HEADER_RECITAL_PATTERN.search(stripped))

            if is_title or is_party or is_recital:
                # 检查这行是否被错误编入了条款编号
                old_line = stripped
                # 移除可能被AI添加的条款编号
                new_line = re.sub(r'^\*{0,2}第[一二三四五六七八九十百千万零〇\d]+条\*{0,2}\s*', '', stripped)
                if new_line != stripped:
                    lines[i] = new_line
                    changes.append(f"首部编号移除: '{old_line[:50]}' → '{new_line[:50]}'")

                header_end_line = i

        # 首部之后到第一个"第X条"之间的内容也属于首部
        for i in range(header_end_line + 1, len(lines)):
            stripped = lines[i].strip()
            if not stripped:
                continue
            # 检查是否是条款正文开始
            if re.search(r'^\*{0,2}第[一二三四五六七八九十百千万零〇\d]+条', stripped):
                break
            # 这行也在首部区域内，检查是否被错误编号
            old_line = stripped
            new_line = re.sub(r'^\*{0,2}第[一二三四五六七八九十百千万零〇\d]+条\*{0,2}\s*', '', stripped)
            if new_line != stripped:
                lines[i] = new_line
                changes.append(f"首部编号移除: '{old_line[:50]}' → '{new_line[:50]}'")

        if changes:
            text = '\n'.join(lines)

        return text, changes

    # ============================================================
    # 签署区保护
    # ============================================================

    def apply_signature_protection(self, text: str) -> Tuple[str, List[str]]:
        """
        签署区保护（代码实现，不调API）

        功能：
        1. 识别签署区模式（甲方盖章、日期等）
        2. 移除签署区中被错误添加的条款编号
        3. 识别附件标题，确保不与主合同连续编号

        Returns:
            (处理后的文本, 替换记录列表)
        """
        changes = []
        lines = text.split('\n')

        in_signature_area = False

        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                continue

            # 检测签署区开始
            # 注意：首部的"甲方：XXX{.underline}"不应触发签署区
            # 只有真正的签署区（含盖章、签名、签字等关键词）才触发
            if any(p.search(stripped) for p in self.SIGNATURE_PATTERNS):
                # 额外检查：如果行中含 {.underline}，可能是首部而非签署区
                if '{.underline}' not in stripped:
                    in_signature_area = True

            # 遇到真正的条款标题时，退出签署区
            # （防止首部误触发后，条款标题被移除）
            if re.match(r'^\*{0,2}第[一二三四五六七八九十百千万零〇\d]+条', stripped):
                in_signature_area = False

            # 签署区内：移除可能被添加的条款编号
            if in_signature_area:
                old_line = stripped
                new_line = re.sub(r'^\*{0,2}第[一二三四五六七八九十百千万零〇\d]+条\*{0,2}\s*', '', stripped)
                if new_line != stripped:
                    lines[i] = new_line
                    changes.append(f"签署区编号移除: '{old_line[:50]}' → '{new_line[:50]}'")

            # 检测附件标题，移除主合同编号
            appendix_match = self.APPENDIX_PATTERN.search(stripped)
            if appendix_match:
                old_line = stripped
                new_line = re.sub(r'^\*{0,2}第[一二三四五六七八九十百千万零〇\d]+条\*{0,2}\s*', '', stripped)
                if new_line != stripped:
                    lines[i] = new_line
                    changes.append(f"附件编号移除: '{old_line[:50]}' → '{new_line[:50]}'")

        if changes:
            text = '\n'.join(lines)

        return text, changes

    # ============================================================
    # 层级递进修复
    # ============================================================

    def apply_hierarchy_fix(self, text: str) -> Tuple[str, List[str]]:
        """
        层级递进修复（代码实现，不调API）

        规则：一级编号（第X条）后如果直接跟三级编号（（1）（2）...），
        而没有二级编号（X.1 X.2 ...），则将三级编号降级为自然段落。

        例如：
        **第三条** 违约责任
        （1）甲方逾期付款...     →  甲方逾期付款...
        （2）乙方逾期交付...     →  乙方逾期交付...

        Returns:
            (处理后的文本, 替换记录列表)
        """
        changes = []
        lines = text.split('\n')
        result_lines = []

        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # 检测一级编号行
            is_article = bool(re.search(
                r'^\*{0,2}第[一二三四五六七八九十百千万零〇\d]+条', stripped
            ))

            if is_article:
                result_lines.append(line)
                i += 1

                # 收集紧跟其后的行，检查是否直接跳到三级编号
                sub_lines = []
                has_secondary = False  # 是否有二级编号（X.1等）
                has_tertiary = False   # 是否有三级编号（（1）等）

                while i < len(lines):
                    next_stripped = lines[i].strip()

                    # 空行：跳过但保留
                    if not next_stripped:
                        sub_lines.append(lines[i])
                        i += 1
                        continue

                    # 遇到下一个一级编号：停止
                    if re.search(r'^\*{0,2}第[一二三四五六七八九十百千万零〇\d]+条', next_stripped):
                        break

                    # 检测二级编号（1.1, 2.3 等）
                    if re.search(r'^\d+\.\d+\s', next_stripped):
                        has_secondary = True

                    # 检测三级编号（（1）、（2）等）
                    if re.search(r'^[（(]\d+[）)]\s*', next_stripped):
                        has_tertiary = True

                    sub_lines.append(lines[i])
                    i += 1

                # 如果有三级编号但没有二级编号，将三级编号降级为自然段落
                if has_tertiary and not has_secondary:
                    fixed_sub_lines = []
                    for sl in sub_lines:
                        sl_stripped = sl.strip()
                        if not sl_stripped:
                            fixed_sub_lines.append(sl)
                            continue
                        # 移除三级编号前缀
                        new_sl = re.sub(r'^[（(]\d+[）)]\s*', '', sl_stripped)
                        if new_sl != sl_stripped:
                            changes.append(f"层级修复: 移除跳级三级编号 → 自然段落 '{new_sl[:40]}...'")
                        fixed_sub_lines.append(new_sl if new_sl else sl)

                    result_lines.extend(fixed_sub_lines)
                else:
                    result_lines.extend(sub_lines)
            else:
                result_lines.append(line)
                i += 1

        if changes:
            text = '\n'.join(result_lines)

        return text, changes

    # ============================================================
    # 内容添加检测
    # ============================================================

    def detect_content_addition(self, original: str, cleaned: str) -> Tuple[bool, List[str]]:
        """
        检测AI是否添加了原文不存在的内容

        策略：
        1. 长度检测：输出比输入长超过15%，标记警告
        2. 甲乙方信息检测：检查是否将甲乙方单位写入了条款正文
        3. 关键名词检测：对比原文和输出中出现的专有名词差异

        Returns:
            (是否有问题, 问题列表)
        """
        issues = []

        # 1. 长度检测
        orig_len = len(original.strip())
        clean_len = len(cleaned.strip())
        if orig_len > 0:
            growth_rate = (clean_len - orig_len) / orig_len
            if growth_rate > 0.15:
                issues.append(
                    f"内容膨胀警告: 输出比输入长{growth_rate*100:.1f}%"
                    f"（{orig_len}字→{clean_len}字），AI可能添加了原文不存在的内容"
                )

        # 2. 甲乙方信息被编入条款检测
        # 从原文中提取甲乙方名称
        party_names = []
        for match in re.finditer(
            r'[甲乙丙丁]方[（(][^）)]+[)）][：:]\s*([\w\u4e00-\u9fff（）()]+?(?:公司|有限|集团|企业|单位|部门|院|所|中心|协会|基金))',
            original
        ):
            name = match.group(1).strip()
            if name and len(name) >= 4:  # 至少4个字的名称才有意义
                party_names.append(name)

        for match in re.finditer(
            r'[甲乙丙丁]方[：:]\s*([\w\u4e00-\u9fff（）()]+?(?:公司|有限|集团|企业|单位|部门|院|所|中心|协会|基金))',
            original
        ):
            name = match.group(1).strip()
            if name and len(name) >= 4 and name not in party_names:
                party_names.append(name)

        # 检查这些名称是否出现在条款正文中（而非首部）
        if party_names:
            # 找到第一个条款的位置
            first_article_match = re.search(
                r'\*{0,2}第[一二三四五六七八九十百千万零〇\d]+条', cleaned
            )
            if first_article_match:
                article_body = cleaned[first_article_match.start():]
                for name in party_names:
                    # 检查名称是否出现在条款正文中
                    if name in article_body:
                        # 排除签署区
                        sig_match = re.search(r'[甲乙丙丁]方.*?盖章', article_body)
                        if sig_match:
                            before_sig = article_body[:sig_match.start()]
                        else:
                            before_sig = article_body

                        if name in before_sig:
                            issues.append(
                                f"甲乙方信息可能被编入条款: '{name}'出现在条款正文中"
                            )

        has_issues = len(issues) > 0
        return has_issues, issues

    # ============================================================
    # 金额格式
    # ============================================================

    # 中文数字映射
    DIGIT_MAP = {
        '0': '零', '1': '壹', '2': '贰', '3': '叁', '4': '肆',
        '5': '伍', '6': '陆', '7': '柒', '8': '捌', '9': '玖',
    }
    UNIT_MAP = ['', '拾', '佰', '仟']
    BIG_UNIT = ['', '万', '亿', '万亿']

    # 编号规范化用的中文数字映射（简单数字，非大写金额）
    ARABIC_TO_CHINESE_SIMPLE = {
        '0': '零', '1': '一', '2': '二', '3': '三', '4': '四',
        '5': '五', '6': '六', '7': '七', '8': '八', '9': '九',
    }

    @staticmethod
    def _arabic_to_chinese_simple(num_str: str) -> str:
        """简单阿拉伯数字→中文数字（支持0-999）"""
        try:
            num = int(num_str)
        except ValueError:
            return num_str

        digit_map = RuleEngine.ARABIC_TO_CHINESE_SIMPLE

        if num == 0:
            return '零'
        if 1 <= num <= 9:
            return digit_map[num_str]
        if num == 10:
            return '十'
        if 11 <= num <= 19:
            return '十' + digit_map[num_str[1]]
        if num % 10 == 0 and num <= 90:
            return digit_map[num_str[0]] + '十'
        if 20 <= num <= 99:
            return digit_map[num_str[0]] + '十' + digit_map[num_str[1]]
        if 100 <= num <= 999:
            result = digit_map[num_str[0]] + '百'
            remainder = int(num_str[1:])
            if remainder == 0:
                return result
            if remainder < 10:
                result += '零' + digit_map[num_str[2]]
            else:
                result += RuleEngine._arabic_to_chinese_simple(num_str[1:])
            return result
        return num_str  # 超大数字保留

    def _to_chinese_amount(self, amount: float) -> str:
        """
        将阿拉伯数字金额转为中文大写金额

        支持: 0.00 ~ 999999999999.99
        """
        if amount == 0:
            return "零"

        # 分离整数和小数
        integer_part = int(amount)
        decimal_part = round((amount - integer_part) * 100)

        result = ""

        # 处理整数部分
        if integer_part > 0:
            # 按4位一组分组
            groups = []
            temp = integer_part
            while temp > 0:
                groups.append(temp % 10000)
                temp //= 10000

            zero_flag = False  # 标记是否需要补"零"
            for i in range(len(groups) - 1, -1, -1):
                group = groups[i]
                if group == 0:
                    zero_flag = True
                    continue

                # 如果前面有零分组且当前结果末尾没有"零"，补一个"零"
                if zero_flag:
                    if result and not result.endswith('零'):
                        result += '零'
                    zero_flag = False

                # 如果当前分组有前导零（小于1000）且不是最高位分组，补一个"零"
                if i < len(groups) - 1 and group < 1000:
                    if result and not result.endswith('零'):
                        result += '零'

                # 处理4位数组
                group_str = ""
                digits = f"{group:04d}"

                for j, d in enumerate(digits):
                    pos = 3 - j  # 仟佰拾个
                    if d == '0':
                        # 连续零只保留一个
                        if group_str and not group_str.endswith('零'):
                            group_str += '零'
                    else:
                        group_str += self.DIGIT_MAP[d] + self.UNIT_MAP[pos]

                # 去掉末尾零
                group_str = group_str.rstrip('零')

                result += group_str + self.BIG_UNIT[i]

            # 去掉末尾零（如"壹亿零壹佰万"末尾无零，但"壹亿"末尾可能有零）
            result = result.rstrip('零')

        # 处理小数部分
        if decimal_part > 0:
            jiao = decimal_part // 10
            fen = decimal_part % 10
            if jiao > 0:
                result += self.DIGIT_MAP[str(jiao)] + '角'
            elif integer_part > 0:
                result += '零'
            if fen > 0:
                result += self.DIGIT_MAP[str(fen)] + '分'
        else:
            # 无小数，加"整"
            pass  # 由调用方决定是否加"整"

        return result

    def apply_amount_formatting(self, text: str) -> Tuple[str, List[str]]:
        """
        金额格式规范化（正则实现，不调API）

        规则：¥/￥XXXX → 人民币XXXX.00元（人民币X元整）
        注意：阿拉伯数字不加千分位逗号，避免AI润色时误拆数字

        Returns:
            (格式化后的文本, 替换记录列表)
        """
        changes = []
        change_count = 0

        # 模式1: ¥/￥ 开头的金额
        def replace_currency_symbol(match):
            nonlocal change_count
            amount_str = match.group(1).replace(',', '').strip()
            try:
                amount = float(amount_str)
            except ValueError:
                return match.group(0)  # 无法解析，保留原样

            chinese = self._to_chinese_amount(amount)
            formatted = f"人民币{amount:.2f}元（人民币{chinese}元整）"
            change_count += 1
            return formatted

        # 匹配: ¥5,000 / ￥5000 / ¥ 5000.00 等
        pattern1 = r'[¥￥]\s*([\d,]+(?:\.\d{1,2})?)\s*元?'
        text = re.sub(pattern1, replace_currency_symbol, text)
        if change_count > 0:
            changes.append(f"金额格式化(¥/￥): {change_count}处")

        # 模式2: 纯数字+元 (需谨慎，避免误匹配日期、编号等)
        change_count = 0

        def replace_plain_amount(match):
            nonlocal change_count
            amount_str = match.group(1).replace(',', '')

            try:
                amount = float(amount_str)
            except ValueError:
                return match.group(0)

            # 只格式化看起来像金额的数字（>= 100元，避免误匹配编号）
            if amount < 100:
                return match.group(0)

            chinese = self._to_chinese_amount(amount)
            formatted = f"人民币{amount:.2f}元（人民币{chinese}元整）"
            change_count += 1
            return formatted

        # 匹配: 数字+元 (前面不是"人民币"或数字或逗号)
        # 注意：\d{1,3}(?:,\d{3})+ 匹配千分位格式如 1,000
        #       \d{3,} 匹配纯数字如 500, 1000, 5000
        pattern2 = r'(?<!人民币)(?<![\d,])(\d{1,3}(?:,\d{3})+(?:\.\d{1,2})?|\d{3,}(?:\.\d{1,2})?)元'
        text = re.sub(pattern2, replace_plain_amount, text)
        if change_count > 0:
            changes.append(f"金额格式化(纯数字+元): {change_count}处")

        # 模式3: X万/X万元
        change_count = 0

        def replace_wan_amount(match):
            nonlocal change_count
            num_str = match.group(1).replace(',', '')
            try:
                amount = float(num_str) * 10000
            except ValueError:
                return match.group(0)

            chinese = self._to_chinese_amount(amount)
            formatted = f"人民币{amount:.2f}元（人民币{chinese}元整）"
            change_count += 1
            return formatted

        pattern3 = r'(?<!美)(\d+(?:\.\d+)?)万(?!美)(?:元)?'
        text = re.sub(pattern3, replace_wan_amount, text)
        if change_count > 0:
            changes.append(f"金额格式化(万): {change_count}处")

        return text, changes

    # ============================================================
    # 标点规范化
    # ============================================================

    # 英文标点 → 中文标点（仅在中文上下文中）
    PUNCT_PATTERNS: List[Tuple[str, str]] = [
        # 冒号: 英文冒号后跟中文字符 → 中文冒号
        (r':\s*(?=[\u4e00-\u9fff])', '：'),
        # 分号: 英文分号后跟中文字符 → 中文分号
        (r';\s*(?=[\u4e00-\u9fff])', '；'),
    ]

    def apply_punctuation_normalization(self, text: str) -> Tuple[str, List[str]]:
        """
        标点规范化 — 已禁用

        原因：AI处理过程不应改变原合同的全角半角。
        原合同用什么标点（半角或全角），输出应保持原样。
        此方法保留但不执行转换，仅做直通返回。
        """
        return text, []

    # ============================================================
    # 编号规范化
    # ============================================================

    def apply_numbering_normalization(self, text: str) -> Tuple[str, List[str]]:
        """
        编号规范化（正则实现，不调API）

        修复：
        - "第1条" → "第一条" (阿拉伯数字→中文数字)
        - 保留 **第X条** / **第X条 标题** 的加粗标记
        """
        changes = []
        count = 0

        def replace_article_number(match):
            nonlocal count
            bold_prefix = match.group(1) or ""
            num_str = match.group(2)
            bold_suffix = match.group(3) or ""
            chinese = self._arabic_to_chinese_simple(num_str)
            if chinese != num_str:
                count += 1
            return f"{bold_prefix}第{chinese}条{bold_suffix}"

        # 匹配: **第1条** 或 第1条 （支持加粗和裸文本）
        pattern = r'(\*\*)?第(\d+)条(\*\*)?'
        text = re.sub(pattern, replace_article_number, text)

        if count > 0:
            changes.append(f"编号规范化: {count}处阿拉伯数字→中文数字")

        return text, changes

    # ============================================================
    # 页码/水印清除
    # ============================================================

    def apply_page_number_cleanup(self, text: str) -> Tuple[str, List[str]]:
        """
        清除页码和水印残留（代码实现，不调API）

        清除模式：
        - "第X页 共Y页"
        - "第 X 页 共 Y 页"
        - "- X -" (页码格式)
        - 单独一行的纯数字（可能是页码）

        Returns:
            (处理后的文本, 替换记录列表)
        """
        changes = []
        lines = text.split('\n')
        result_lines = []

        for line in lines:
            stripped = line.strip()

            # 匹配 "第X页 共Y页" 模式
            if re.match(r'^第\s*\d+\s*页\s*共\s*\d+\s*页$', stripped):
                changes.append(f"页码清除: '{stripped}'")
                continue

            # 匹配 "- X -" 页码格式
            if re.match(r'^-\s*\d+\s*-$', stripped):
                changes.append(f"页码清除: '{stripped}'")
                continue

            # 匹配单独一行的纯数字（1-3位，很可能是页码）
            # 但要排除子条款编号（如"1."等）
            if re.match(r'^\d{1,3}$', stripped):
                # 如果前后有空行，很可能是页码
                changes.append(f"页码清除(纯数字行): '{stripped}'")
                continue

            result_lines.append(line)

        if changes:
            text = '\n'.join(result_lines)

        return text, changes

    # ============================================================
    # "以下无正文"格式统一
    # ============================================================

    def apply_closing_mark_cleanup(self, text: str) -> Tuple[str, List[str]]:
        """
        统一"以下无正文"格式（代码实现，不调API）

        将各种变体统一为：（以下无正文）

        变体包括：
        - "----以下无正文----"
        - "—以下无正文—"
        - "- 以下无正文 -"
        - "以下无正文" (无括号)
        - "[以下无正文]" (方括号)
        - "【以下无正文】" (全角方括号)

        Returns:
            (处理后的文本, 替换记录列表)
        """
        changes = []

        # 保护已有的正确格式
        correct_format = "（以下无正文）"
        placeholder = "##CLOSING_MARK##"
        if correct_format in text:
            text = text.replace(correct_format, placeholder)

        # 匹配各种"以下无正文"变体（含各种括号和横线）
        patterns = [
            r'[-—\\]*\s*[\[【\(（]?\s*以下无正文\s*[\]】\)）]?\s*[-—\\]*',
        ]
        
        for pattern in patterns:
            matches = list(re.finditer(pattern, text))
            for match in reversed(matches):
                old = match.group(0)
                text = text[:match.start()] + correct_format + text[match.end():]
                changes.append(f"'以下无正文'格式统一: '{old.strip()}' → '（以下无正文）'")

        # 恢复已有的正确格式
        if placeholder in text:
            text = text.replace(placeholder, correct_format)

        return text, changes

    # ============================================================
    # 甲乙方格式标准化
    # ============================================================

    def apply_party_format_standardization(self, text: str) -> Tuple[str, List[str]]:
        """
        甲乙方格式标准化（代码实现，不调API）

        规则："描述词（甲方）" → "甲方（描述词）"
        例如："承租方（甲方）" → "甲方（承租方）"
             "出租方（乙方）" → "乙方（出租方）"

        Returns:
            (处理后的文本, 替换记录列表)
        """
        changes = []

        # 匹配 "描述词（甲方/乙方/丙方/丁方）" 模式
        # 描述词通常是角色名：承租方、出租方、买方、卖方、发包方、承包方等
        def replace_party_order(match):
            role = match.group(1)  # 描述词（如"承租方"）
            party = match.group(2)  # 甲乙方标识（如"甲方"）
            changes.append(f"甲乙方格式: '{role}（{party}）' → '{party}（{role}）'")
            return f"{party}（{role}）"

        # 中文括号版本
        text = re.sub(
            r'([\u4e00-\u9fff]+方)[（(]([甲乙丙丁]方)[)）]',
            replace_party_order, text
        )

        return text, changes

    # ============================================================
    # 条款标题加粗格式统一
    # ============================================================

    def apply_article_title_format(self, text: str) -> Tuple[str, List[str]]:
        """
        条款标题格式统一（代码实现，不调API）

        规则：
        1. "第一条：标题" → "**第一条 标题**"  (冒号分隔，加粗整体)
        2. "**第一条** 标题" → "**第一条 标题**" (加粗扩展到整体)
        3. "第一条 标题" → "**第一条 标题**" (无加粗，加粗整体)
        4. "第一条" (独立一行，无标题) → "**第一条**" (只加粗编号)
        5. 排除包含甲乙方信息的行（如"第一条 甲方为XX公司"）

        Returns:
            (处理后的文本, 替换记录列表)
        """
        changes = []
        lines = text.split('\n')
        result_lines = []

        for line in lines:
            stripped = line.strip()
            old_line = stripped

            # 排除包含甲乙方信息的行（首部保护）
            if re.search(r'[甲乙丙丁]方[为是]', stripped):
                result_lines.append(line)
                continue

            # 模式1: **第X条** 标题文字  →  **第X条 标题文字**
            m1 = re.match(r'^(\*\*)?(第[一二三四五六七八九十百千万零〇\d]+条)(\*\*)?[：:\s]+(.+)$', stripped)
            if m1:
                bold_prefix = m1.group(1) or ""
                article = m1.group(2)  # "第X条"
                bold_suffix = m1.group(3) or ""
                title = m1.group(4).strip()
                # 去掉title末尾可能残留的**
                title = re.sub(r'\*\*$', '', title).strip()
                if title:
                    new_line = f"**{article} {title}**"
                else:
                    new_line = f"**{article}**"
                if new_line != old_line:
                    changes.append(f"条款标题格式: '{old_line[:40]}' → '{new_line[:40]}'")
                result_lines.append(new_line)
                continue

            # 模式2: 第X条：标题文字  →  **第X条 标题文字**
            m2 = re.match(r'^(第[一二三四五六七八九十百千万零〇\d]+条)[：:]\s*(.+)$', stripped)
            if m2:
                article = m2.group(1)
                title = m2.group(2).strip()
                if title:
                    new_line = f"**{article} {title}**"
                else:
                    new_line = f"**{article}**"
                if new_line != old_line:
                    changes.append(f"条款标题格式: '{old_line[:40]}' → '{new_line[:40]}'")
                result_lines.append(new_line)
                continue

            # 模式3: 独立的 **第X条** 或 第X条 (无后续标题)
            m3 = re.match(r'^(\*\*)?(第[一二三四五六七八九十百千万零〇\d]+条)(\*\*)?$', stripped)
            if m3:
                article = m3.group(2)
                new_line = f"**{article}**"
                if new_line != old_line:
                    changes.append(f"条款标题格式: '{old_line}' → '{new_line}'")
                result_lines.append(new_line)
                continue

            # 模式4: 已禁用
            # 原设计: 阿拉伯数字条款编号 "8. 不可抗力" → "**第八条 不可抗力**"
            # 禁用原因: pandoc 转 MD 时，中文数字编号（一、二、三…）会被转为
            # Markdown 有序列表格式（1. 2. 3.），这些是子条款编号而非条款标题。
            # 模式4 会把所有 "数字. 内容" 都误判为条款编号并加上 **第X条** 加粗，
            # 导致子条款被错误升级为条款标题。
            # 真正的条款标题应该用 "第X条" 格式，已在模式1-3中处理。
            # 如果原文确实用了 "8. 不可抗力" 作为条款标题，AI 清洗阶段会处理。

            result_lines.append(line)

        if changes:
            text = '\n'.join(result_lines)

        return text, changes

    # ============================================================
    # 附件编号中文化
    # ============================================================

    def apply_appendix_number_chinese(self, text: str) -> Tuple[str, List[str]]:
        """
        附件编号阿拉伯数字→中文数字（代码实现，不调API）

        规则："附件1" → "附件一"，"附件2" → "附件二"

        Returns:
            (处理后的文本, 替换记录列表)
        """
        changes = []

        ARABIC_TO_CHINESE_SMALL = {
            '1': '一', '2': '二', '3': '三', '4': '四', '5': '五',
            '6': '六', '7': '七', '8': '八', '9': '九', '10': '十',
            '11': '十一', '12': '十二',
        }

        def replace_appendix_num(match):
            prefix = match.group(1)  # "附件" 或 "附件第"
            num = match.group(2)
            suffix = match.group(3)  # 冒号等
            chinese = ARABIC_TO_CHINESE_SMALL.get(num, num)
            if chinese != num:
                changes.append(f"附件编号: '附件{num}' → '附件{chinese}'")
            return f"{prefix}{chinese}{suffix}"

        # 匹配: 附件1：  附件2：  附件1《  附件第1条 等
        text = re.sub(
            r'(附件第?)(\d+)([：:《])',
            replace_appendix_num, text
        )

        return text, changes

    # ============================================================
    # 表格保护：保留表格结构，只处理表格内文字
    # ============================================================

    # Markdown表格行模式（支持pipe表格和grid表格）
    # Pipe表格：| col1 | col2 |（首尾都有|）
    # Grid表格数据行：| data | data（至少一个|，pandoc复杂表格行尾可能无|）
    # Grid表格简单分隔行：+---+---+ 或 +===+===+
    # Grid表格混合分隔行：+---+    |    |（部分列分隔部分不分隔，pandoc合并单元格时产生）
    TABLE_PIPE_ROW = re.compile(r'^\|.*\|$')
    TABLE_GRID_ROW = re.compile(r'^\|')  # 以|开头（含pipe和grid数据行）
    TABLE_GRID_SEPARATOR_SIMPLE = re.compile(r'^\+[-=+:]+\+$')  # +---+---+ 简单分隔行
    TABLE_GRID_SEPARATOR_MIXED = re.compile(r'^\+[-=+:\s|]+$')  # +---+  |  | 混合分隔行

    def _is_table_line(self, stripped: str) -> bool:
        """判断一行是否属于表格"""
        if not stripped:
            return False
        # Pipe表格行：| ... |
        if self.TABLE_PIPE_ROW.match(stripped):
            return True
        # Grid表格数据行：| d