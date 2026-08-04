"""Markdown文件生成模块。

基于提取的JSON文件生成规范的Markdown文档。
标题名称随专利类型自适应。

本模块负责将结构化的专利JSON数据转换为人类可读的Markdown格式文档。
生成的Markdown文档遵循中国专利文档的标准结构，使用层级标题组织内容，
著录项目以表格形式展示，说明书附图以Markdown图片语法嵌入。

主要特点：
1. 标题名称根据专利类型自适应（发明名称/实用新型名称/外观设计名称）
2. 著录项目使用Markdown表格展示，自动转义特殊字符
3. 权利要求书按编号分段，每条之间有空行
4. 说明书子章节中的段落号以[XXXX]格式保留
5. 附图引用自动去重，避免同一图片被重复加载
"""

# logging: 用于记录模块运行时的日志信息
# os: 用于创建输出目录等文件系统操作
# re: 用于正则表达式匹配，主要在权利要求编号识别时使用
import logging
import os
import re
from typing import Dict

# 使用模块专属的logger，便于在日志中区分来源
logger = logging.getLogger('patent_extractor')


class MarkdownGenerator:
    """Markdown文档生成器。

    负责将专利JSON数据转换为格式规范的Markdown文档。生成的文档结构如下：
    - # 专利名称（一级标题）
    - ## 专利类型
    - ## 公开类型
    - ## 著录项目（表格形式）
    - ## 摘要
    - ## 权利要求书
    - ## 说明书
      - ### 说明书标题
      - ### 技术领域
      - ### 背景技术
      - ### 发明内容/实用新型内容
      - ### 附图说明
      - ### 具体实施方式
    - ## 说明书附图
    """

    # 续行词列表：句号后紧跟这些词时，不进行分段
    # 这些词表明后续内容是对前文的补充说明，而非新段落
    _CONTINUATION_WORDS = (
        '其特征在于', '所述', '其中', '该', '本发明', '本实用新型',
        '即', '亦即', '也就是', '指的是', '包括', '包含', '具有',
    )

    # 段落起始标记：以这些模式开头的行通常是一个新段落的开始
    _PARAGRAPH_START_PATTERNS = re.compile(
        r'^(?:'
        r'根据|基于|针对|关于|此外|另外|同时|并且|而且|'
        r'但是|然而|不过|因此|所以|综上|总之|由此可见|'
        r'首先|其次|再次|最后|第一步|第二步|'
        r'当|如果|假设|若|倘若|假如|'
        r'在|对|将|由|从|经|通过|利用|采用|使用|'
        r'权利要求|对比文件|实施例|实施方案|具体实施|'
        r'[（(]\s*[一二三四五六七八九十\d]+\s*[）)]|'  # 编号列表 (一) (1)
        r'\d+[.．、]'  # 数字编号 1. 2、
        r')'
    )

    def _format_body_content(self, text: str) -> str:
        """智能分段：确保Markdown正文中不同语义段落之间有适当的换行符。

        分析当前段落未正确分行的原因：
        1. OCR提取的文本中，段落内换行被 _clean_ocr_in_body 合并，导致不同语义
           段落被拼接在一起
        2. Markdown生成器直接输出 section_content，未添加段落间的空行分隔
        3. 审查文件正文中，不同论点/论述之间缺少视觉分隔

        解决方案：
        1. 调整正文中的标题级别（OCR 产生的 ## 标记应降为 #####）
        2. 保留已有的空行分段（\\n\\n）
        3. 对没有空行分隔的长文本，在句号后检测段落边界并插入空行
        4. 使用续行词和段落起始标记避免在句子中间断开

        Args:
            text: 待格式化的正文文本

        Returns:
            格式化后的文本，不同语义段落之间以空行分隔
        """
        if not text:
            return text

        # 调整正文中的标题级别：
        # OCR（如 MinerU）可能在正文中产生 ## 或 ### 标题标记，
        # 但正文章节标题为 ####，子标题应为 #####（比章节标题低一级）。
        # 将所有 Markdown 标题标记统一转换为 #####。
        text = re.sub(r'^#{1,6}\s+', '##### ', text, flags=re.MULTILINE)

        # 如果文本已经包含空行分段，先按现有分段处理
        paragraphs = re.split(r'\n\n+', text)
        result_paragraphs = []

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # 对每个段落检查是否需要进一步细分
            # 中文文本较紧凑，50字符以上的段落就可能需要分段
            if len(para) < 50:
                result_paragraphs.append(para)
                continue

            # 检查段落中是否包含多个句子且缺少分段
            # 策略：在句号（。）后检测是否应分段
            sub_paragraphs = self._split_by_sentence_boundary(para)
            result_paragraphs.extend(sub_paragraphs)

        return '\n\n'.join(result_paragraphs)

    def _split_by_sentence_boundary(self, text: str) -> list:
        """在句号后检测段落边界，将长文本拆分为语义段落。

        分段规则：
        1. 遇到句号（。）时，检查后续文本是否为新段落起始
        2. 如果句号后紧跟续行词（如"其特征在于"、"所述"），不分段
        3. 如果句号后紧跟段落起始标记（如"根据"、"基于"），分段
        4. 如果句号后紧跟引号/括号闭合，不分段

        Args:
            text: 待拆分的长文本

        Returns:
            拆分后的段落列表
        """
        result = []
        current_start = 0
        i = 0

        while i < len(text):
            if text[i] != '。':
                i += 1
                continue

            # 找到句号，检查是否应该在此处分段
            next_pos = i + 1

            # 跳过句号后紧跟的引号/括号
            while next_pos < len(text) and text[next_pos] in '"\u201d\u300b）\u2019':
                next_pos += 1

            if next_pos >= len(text):
                # 句号是文本末尾，不分段
                break

            # 获取句号后的文本
            after_period = text[next_pos:]

            # 检查续行词
            is_continuation = any(
                after_period.startswith(word) for word in self._CONTINUATION_WORDS
            )
            if is_continuation:
                i = next_pos
                continue

            # 检查段落起始标记
            first_line = after_period.split('\n')[0].strip()
            if first_line and self._PARAGRAPH_START_PATTERNS.match(first_line):
                segment = text[current_start:next_pos].strip()
                if segment:
                    result.append(segment)
                current_start = next_pos

            i = next_pos

        # 添加剩余文本
        remaining = text[current_start:].strip()
        if remaining:
            result.append(remaining)

        return result if result else [text]

    def generate(self, data: Dict) -> str:
        """
        从JSON数据生成Markdown文档。

        将专利JSON字典转换为完整的Markdown格式字符串，按照中国专利文档的
        标准结构组织内容。各部分的处理逻辑如下：
        - 专利名称：从JSON中自适应获取（发明名称/实用新型名称/外观设计名称）
        - 著录项目：以Markdown表格形式展示，自动转义管道符和换行符
        - 权利要求书：按编号分段，每条权利要求之间添加空行
        - 说明书：按子章节生成三级标题，段落号以[XXXX]格式保留
        - 说明书附图：以Markdown图片语法嵌入，自动去重

        Args:
            data: 专利信息JSON字典，通常由 JSONGenerator.generate() 生成，
                  包含'专利类型'、'公开类型'、'著录项目'、'摘要'、'权利要求书'、
                  '说明书'、'说明书附图'等顶层键

        Returns:
            str: 完整的Markdown格式字符串，可直接写入文件
        """
        # 使用列表逐行收集Markdown内容，最后用换行符拼接
        # 这种方式比字符串拼接更高效，避免了频繁的字符串复制
        lines = []

        # 一级标题：专利名称（根据专利类型自适应字段名）
        patent_name = self._get_patent_name(data)
        lines.append(f"# {patent_name}")
        lines.append("")  # 标题后添加空行，符合Markdown规范

        # 专利类型
        lines.append("## 专利类型")
        lines.append("")
        lines.append(data.get('专利类型', '未知'))  # 若缺失则显示"未知"
        lines.append("")

        # 公开类型
        lines.append("## 公开类型")
        lines.append("")
        lines.append(data.get('公开类型', '未知'))
        lines.append("")

        # 著录项目：以Markdown表格形式展示
        lines.append("## 著录项目")
        lines.append("")
        biblio = data.get('著录项目', {})
        if biblio:
            # 使用表格展示著录项目，包含"项目"和"内容"两列
            lines.append("| 项目 | 内容 |")
            lines.append("|------|------|")
            for key, value in biblio.items():
                # 转义表格中的特殊字符：
                # - 管道符 | 需转义为 \|，否则会破坏表格结构
                # - 换行符 \n 替换为空格，因为表格单元格不支持换行
                value_escaped = str(value).replace('|', '\\|').replace('\n', ' ')
                lines.append(f"| {key} | {value_escaped} |")
            lines.append("")
        else:
            lines.append("（无著录项目信息）")
            lines.append("")

        # 摘要：专利技术方案的简要概述
        lines.append("## 摘要")
        lines.append("")
        abstract = data.get('摘要', '')
        if abstract:
            lines.append(abstract)
        else:
            lines.append("（无摘要内容）")
        lines.append("")

        # 权利要求书：定义专利保护范围的法律文本
        lines.append("## 权利要求书")
        lines.append("")
        claims = data.get('权利要求书', '')
        if claims:
            # 按权利要求编号分段，每条之间添加空行
            # 权利要求书格式示例："1.一种xxx，其特征在于...\n2.根据权利要求1..."
            claim_lines = claims.split('\n')
            for claim_line in claim_lines:
                stripped = claim_line.strip()
                if stripped:
                    lines.append(stripped)
                    # 在权利要求编号开头的行之后添加空行
                    # 匹配以数字+点号开头的行，如"1."或"2．"（支持中英文句号）
                    if re.match(r'\d+[.．]', stripped):
                        lines.append("")
            # 确保权利要求书末尾有空行
            if lines and lines[-1] != "":
                lines.append("")
        else:
            lines.append("（无权利要求书内容）")
            lines.append("")

        # 说明书（含子章节）：按层级结构生成三级标题和段落内容
        lines.append("## 说明书")
        lines.append("")
        description = data.get('说明书', {})
        if description:
            # 说明书标题
            lines.append("### 说明书标题")
            lines.append("")
            title = description.get('说明书标题', '') or '（无）'
            lines.append(title)
            lines.append("")

            # 各子章节（段落对象列表）
            # 遍历所有可能的子章节键名，包括三种专利类型的"内容"字段
            section_keys = ['技术领域', '背景技术', '发明内容', '实用新型内容',
                           '外观设计内容', '附图说明', '具体实施方式']
            for section_key in section_keys:
                section_data = description.get(section_key)
                # 跳过JSON中不存在的子章节（不同专利类型有不同的子章节）
                if section_data is None:
                    continue
                lines.append(f"### {section_key}")
                lines.append("")
                if isinstance(section_data, list):
                    # 段落对象列表：每个元素是 {"段落号": "XXXX", "内容": "..."}
                    for para in section_data:
                        para_num = para.get('段落号', '')
                        content = para.get('内容', '')
                        if para_num:
                            # 有段落号时，格式为 [XXXX] 内容
                            lines.append(f"[{para_num}] {content}")
                        else:
                            # 无段落号时，直接输出内容
                            lines.append(content)
                        # 每个段落之间添加空行，确保预览时行间距正常
                        lines.append("")
                else:
                    # 非列表类型（如纯字符串），直接输出
                    lines.append(str(section_data) or '（无）')
                    lines.append("")
        else:
            lines.append("（无说明书内容）")
            lines.append("")

        # 说明书附图（带唯一性校验，确保每张图片仅加载一次）
        # 由于PDF中同一张图片可能被多次引用（如不同页面引用同一附图），
        # 需要通过文件路径去重，避免Markdown中重复加载同一图片
        lines.append("## 说明书附图")
        lines.append("")
        drawings = data.get('说明书附图', [])
        if drawings:
            # seen_paths: 已加载图片的文件路径集合，用于去重判断
            seen_paths = set()
            # duplicate_count: 被跳过的重复图片引用计数
            duplicate_count = 0
            for img in drawings:
                file_path = img.get('文件路径', '')
                # 跳过没有文件路径的图片记录
                if not file_path:
                    continue
                # 若该图片路径已被引用过，跳过并计数
                if file_path in seen_paths:
                    duplicate_count += 1
                    logger.debug(f"跳过重复图片引用: {file_path}")
                    continue
                # 记录已使用的路径，并生成Markdown图片语法
                seen_paths.add(file_path)
                lines.append(f"![]({file_path})")
                lines.append("")
            # 若存在重复引用，记录警告日志
            if duplicate_count > 0:
                logger.warning(
                    f"Markdown 附图引用去重: 跳过 {duplicate_count} 个重复引用，"
                    f"实际加载 {len(seen_paths)} 张图片"
                )
        else:
            lines.append("（无说明书附图）")
            lines.append("")

        # 将所有行用换行符拼接为完整的Markdown字符串
        return "\n".join(lines)

    def generate_office_action(self, data: Dict) -> str:
        """从审查文件JSON数据生成Markdown文档（分发器）。

        根据文档类型调用对应的独立生成方法，每种审查文件拥有
        完全独立的Markdown结构，不再套用专利公开公告的格式。

        Args:
            data: 审查文件信息JSON字典，由 JSONGenerator.generate_office_action() 生成

        Returns:
            str: 完整的Markdown格式字符串
        """
        doc_type = data.get('文档类型', '')
        if doc_type == '审查意见通知书':
            return self._generate_office_action_notification(data)
        elif doc_type == '驳回决定':
            return self._generate_rejection_decision(data)
        elif doc_type == '复审决定书':
            return self._generate_reexamination_decision(data)
        elif doc_type == '无效宣告请求审查决定书':
            return self._generate_invalidation_decision(data)
        else:
            return self._generate_generic_office_action(data)

    def _generate_office_action_notification(self, data: Dict) -> str:
        """生成审查意见通知书的独立Markdown结构。

        审查意见通知书的Markdown结构反映其文档特性：
        标题 → 基本信息 → 通知书首页事项 → 对比文件 → 结论性意见 → 正文
        """
        lines = []

        name = data.get('发明创造名称', '未知')
        lines.append(f"# {name}")
        lines.append("")
        lines.append("## 审查意见通知书")
        lines.append("")

        # 基本信息表格
        lines.append("### 基本信息")
        lines.append("")
        lines.append("| 项目 | 内容 |")
        lines.append("|------|------|")
        basic_fields = [
            ('申请号', '申请号'),
            ('申请人', '申请人'),
            ('发文日', '发文日'),
            ('发文序号', '发文序号'),
            ('审查次数', '审查次数'),
            ('审查员', '审查员'),
            ('审查部门', '审查部门'),
            ('联系电话', '联系电话'),
        ]
        for label, key in basic_fields:
            value = data.get(key, '')
            if value:
                value_escaped = str(value).replace('|', '\\|').replace('\n', ' ')
                lines.append(f"| {label} | {value_escaped} |")
        lines.append("")

        # 通知书首页事项
        notice = data.get('通知书首页事项', '')
        if notice:
            lines.append("### 通知书首页事项")
            lines.append("")
            lines.append(self._format_body_content(notice))
            lines.append("")

        # 对比文件
        refs = data.get('对比文件', [])
        if refs:
            lines.append("### 对比文件")
            lines.append("")
            lines.append("| 编号 | 文件号 | 公开日期 |")
            lines.append("|------|--------|----------|")
            for ref in refs:
                num = ref.get('编号', '')
                file_no = ref.get('文件号', '').replace('|', '\\|')
                date = ref.get('公开日期', '')
                lines.append(f"| {num} | {file_no} | {date} |")
            lines.append("")

        # 结论性意见
        conclusion = data.get('结论性意见', '')
        if conclusion:
            lines.append("### 结论性意见")
            lines.append("")
            lines.append(conclusion)
            lines.append("")

        # 正文
        lines.append("### 正文")
        lines.append("")
        body = data.get('正文', {})
        if body:
            for section_title, section_content in body.items():
                lines.append(f"#### {section_title}")
                lines.append("")
                if section_content:
                    lines.append(self._format_body_content(section_content))
                else:
                    lines.append("（无内容）")
                lines.append("")
        else:
            lines.append("（无正文内容）")
            lines.append("")

        return "\n".join(lines)

    def _generate_rejection_decision(self, data: Dict) -> str:
        """生成驳回决定的独立Markdown结构。

        驳回决定的Markdown结构反映其文档特性：
        标题 → 基本信息 → 驳回决定首页事项 → 驳回依据 → 针对的申请文件 →
        对比文件 → 正文（案由+驳回理由）
        """
        lines = []

        name = data.get('发明创造名称', '未知')
        lines.append(f"# {name}")
        lines.append("")
        lines.append("## 驳回决定")
        lines.append("")

        # 基本信息表格
        lines.append("### 基本信息")
        lines.append("")
        lines.append("| 项目 | 内容 |")
        lines.append("|------|------|")
        basic_fields = [
            ('申请号', '申请号'),
            ('申请人', '申请人'),
            ('发文日', '发文日'),
            ('审查员', '审查员'),
            ('审查部门', '审查部门'),
            ('审查员代码', '审查员代码'),
        ]
        for label, key in basic_fields:
            value = data.get(key, '')
            if value:
                value_escaped = str(value).replace('|', '\\|').replace('\n', ' ')
                lines.append(f"| {label} | {value_escaped} |")
        lines.append("")

        # 驳回决定首页事项
        front_items = data.get('驳回决定首页事项', '')
        if front_items:
            lines.append("### 驳回决定首页事项")
            lines.append("")
            lines.append(self._format_body_content(front_items))
            lines.append("")

        # 驳回依据
        basis = data.get('驳回依据', '')
        if basis:
            lines.append("### 驳回依据")
            lines.append("")
            lines.append(basis)
            lines.append("")

        # 针对的申请文件
        target_files = data.get('针对的申请文件', '')
        if target_files:
            lines.append("### 针对的申请文件")
            lines.append("")
            lines.append(target_files)
            lines.append("")

        # 对比文件
        refs = data.get('对比文件', [])
        if refs:
            lines.append("### 对比文件")
            lines.append("")
            lines.append("| 编号 | 文件号 | 公开日期 |")
            lines.append("|------|--------|----------|")
            for ref in refs:
                num = ref.get('编号', '')
                file_no = ref.get('文件号', '').replace('|', '\\|')
                date = ref.get('公开日期', '')
                lines.append(f"| {num} | {file_no} | {date} |")
            lines.append("")

        # 正文
        lines.append("### 正文")
        lines.append("")
        body = data.get('正文', {})
        if body:
            for section_title, section_content in body.items():
                lines.append(f"#### {section_title}")
                lines.append("")
                if section_content:
                    lines.append(self._format_body_content(section_content))
                else:
                    lines.append("（无内容）")
                lines.append("")
        else:
            lines.append("（无正文内容）")
            lines.append("")

        return "\n".join(lines)

    def _generate_reexamination_decision(self, data: Dict) -> str:
        """生成复审决定书的独立Markdown结构。

        复审决定书的Markdown结构反映其文档特性：
        标题 → 基本信息 → 合议组 → 决定摘要 → 决定结果 → 法律依据 →
        决定要点 → 对比文件 → 正文（案由+决定理由）
        """
        lines = []

        name = data.get('发明创造名称', '未知')
        lines.append(f"# {name}")
        lines.append("")
        lines.append("## 复审决定书")
        lines.append("")

        # 基本信息表格
        lines.append("### 基本信息")
        lines.append("")
        lines.append("| 项目 | 内容 |")
        lines.append("|------|------|")
        basic_fields = [
            ('申请号', '申请号'),
            ('复审请求人', '复审请求人'),
            ('案件编号', '案件编号'),
            ('决定号', '决定号'),
            ('决定日', '决定日'),
            ('申请日', '申请日'),
            ('公开日', '公开日'),
            ('复审请求日', '复审请求日'),
            ('国际主分类号', '国际主分类号'),
        ]
        for label, key in basic_fields:
            value = data.get(key, '')
            if value:
                value_escaped = str(value).replace('|', '\\|').replace('\n', ' ')
                lines.append(f"| {label} | {value_escaped} |")
        lines.append("")

        # 合议组
        panel = data.get('合议组', {})
        if panel:
            lines.append("### 合议组")
            lines.append("")
            lines.append("| 角色 | 姓名 |")
            lines.append("|------|------|")
            role_map = [('组长', '组长'), ('主审员', '主审员'), ('参审员', '参审员')]
            for label, key in role_map:
                if key in panel:
                    lines.append(f"| {label} | {panel[key]} |")
            lines.append("")

        # 决定摘要
        summary = data.get('决定摘要', '')
        if summary:
            lines.append("### 决定摘要")
            lines.append("")
            lines.append(self._format_body_content(summary))
            lines.append("")

        # 决定结果
        result = data.get('决定结果', '')
        if result:
            lines.append("### 决定结果")
            lines.append("")
            lines.append(result)
            lines.append("")

        # 法律依据
        legal_basis = data.get('法律依据', '')
        if legal_basis:
            lines.append("### 法律依据")
            lines.append("")
            lines.append(legal_basis)
            lines.append("")

        # 决定要点
        key_points = data.get('决定要点', '')
        if key_points:
            lines.append("### 决定要点")
            lines.append("")
            lines.append(self._format_body_content(key_points))
            lines.append("")

        # 对比文件
        refs = data.get('对比文件', [])
        if refs:
            lines.append("### 对比文件")
            lines.append("")
            lines.append("| 编号 | 文件号 | 公开日期 |")
            lines.append("|------|--------|----------|")
            for ref in refs:
                num = ref.get('编号', '')
                file_no = ref.get('文件号', '').replace('|', '\\|')
                date = ref.get('公开日期', '')
                lines.append(f"| {num} | {file_no} | {date} |")
            lines.append("")

        # 正文
        lines.append("### 正文")
        lines.append("")
        body = data.get('正文', {})
        if body:
            for section_title, section_content in body.items():
                lines.append(f"#### {section_title}")
                lines.append("")
                if section_content:
                    lines.append(self._format_body_content(section_content))
                else:
                    lines.append("（无内容）")
                lines.append("")
        else:
            lines.append("（无正文内容）")
            lines.append("")

        return "\n".join(lines)

    def _generate_invalidation_decision(self, data: Dict) -> str:
        """生成无效宣告请求审查决定书的独立Markdown结构。

        无效宣告请求审查决定书的Markdown结构反映其文档特性：
        标题 → 基本信息 → 合议组 → 决定摘要 → 决定结果 → 法律依据 →
        决定要点 → 对比文件 → 正文（案由+决定的理由+决定）
        """
        lines = []

        name = data.get('发明创造名称', '未知')
        lines.append(f"# {name}")
        lines.append("")
        lines.append("## 无效宣告请求审查决定书")
        lines.append("")

        # 基本信息表格
        lines.append("### 基本信息")
        lines.append("")
        lines.append("| 项目 | 内容 |")
        lines.append("|------|------|")
        basic_fields = [
            ('申请号', '申请号'),
            ('专利号', '专利号'),
            ('专利权人', '专利权人'),
            ('无效宣告请求人', '无效宣告请求人'),
            ('案件编号', '案件编号'),
            ('决定号', '决定号'),
            ('决定日', '决定日'),
            ('申请日', '申请日'),
            ('授权公告日', '授权公告日'),
            ('无效宣告请求日', '无效宣告请求日'),
            ('国际分类号', '国际分类号'),
        ]
        for label, key in basic_fields:
            value = data.get(key, '')
            if value:
                value_escaped = str(value).replace('|', '\\|').replace('\n', ' ')
                lines.append(f"| {label} | {value_escaped} |")
        lines.append("")

        # 合议组
        panel = data.get('合议组', {})
        if panel:
            lines.append("### 合议组")
            lines.append("")
            lines.append("| 角色 | 姓名 |")
            lines.append("|------|------|")
            role_map = [('组长', '组长'), ('主审员', '主审员'), ('参审员', '参审员')]
            for label, key in role_map:
                if key in panel:
                    lines.append(f"| {label} | {panel[key]} |")
            lines.append("")

        # 决定摘要
        summary = data.get('决定摘要', '')
        if summary:
            lines.append("### 决定摘要")
            lines.append("")
            lines.append(self._format_body_content(summary))
            lines.append("")

        # 决定结果
        result = data.get('决定结果', '')
        if result:
            lines.append("### 决定结果")
            lines.append("")
            lines.append(result)
            lines.append("")

        # 法律依据
        legal_basis = data.get('法律依据', '')
        if legal_basis:
            lines.append("### 法律依据")
            lines.append("")
            lines.append(legal_basis)
            lines.append("")

        # 决定要点
        key_points = data.get('决定要点', '')
        if key_points:
            lines.append("### 决定要点")
            lines.append("")
            lines.append(self._format_body_content(key_points))
            lines.append("")

        # 对比文件
        refs = data.get('对比文件', [])
        if refs:
            lines.append("### 对比文件")
            lines.append("")
            lines.append("| 编号 | 文件号 | 公开日期 |")
            lines.append("|------|--------|----------|")
            for ref in refs:
                num = ref.get('编号', '')
                file_no = ref.get('文件号', '').replace('|', '\\|')
                date = ref.get('公开日期', '')
                lines.append(f"| {num} | {file_no} | {date} |")
            lines.append("")

        # 正文
        lines.append("### 正文")
        lines.append("")
        body = data.get('正文', {})
        if body:
            for section_title, section_content in body.items():
                lines.append(f"#### {section_title}")
                lines.append("")
                if section_content:
                    lines.append(self._format_body_content(section_content))
                else:
                    lines.append("（无内容）")
                lines.append("")
        else:
            lines.append("（无正文内容）")
            lines.append("")

        return "\n".join(lines)

    def _generate_generic_office_action(self, data: Dict) -> str:
        """未知审查文件类型的通用Markdown结构。"""
        lines = []

        name = data.get('发明创造名称', '未知')
        doc_type = data.get('文档类型', '未知')
        lines.append(f"# {name}")
        lines.append("")
        lines.append(f"## {doc_type}")
        lines.append("")

        # 基本信息
        lines.append("### 基本信息")
        lines.append("")
        lines.append("| 项目 | 内容 |")
        lines.append("|------|------|")
        for key in ['申请号', '申请人', '发文日']:
            value = data.get(key, '')
            if value:
                value_escaped = str(value).replace('|', '\\|').replace('\n', ' ')
                lines.append(f"| {key} | {value_escaped} |")
        lines.append("")

        # 正文
        lines.append("### 正文")
        lines.append("")
        body = data.get('正文', {})
        if body:
            for section_title, section_content in body.items():
                lines.append(f"#### {section_title}")
                lines.append("")
                if section_content:
                    lines.append(self._format_body_content(section_content))
                else:
                    lines.append("（无内容）")
                lines.append("")
        else:
            lines.append("（无正文内容）")
            lines.append("")

        return "\n".join(lines)

    def save(self, data: Dict, output_path: str) -> str:
        """
        生成Markdown并保存到文件。

        先调用 generate() 方法将JSON数据转换为Markdown字符串，
        然后以UTF-8编码写入指定文件，自动创建所需的目录结构。

        Args:
            data: 专利信息JSON字典，通常由 JSONGenerator.generate() 生成
            output_path: 输出文件的绝对或相对路径，例如 "/output/patent.md"

        Returns:
            str: 实际保存的文件路径（与 output_path 相同）
        """
        # 根据数据类型选择生成方法
        if '文档类型' in data:
            markdown_content = self.generate_office_action(data)
        else:
            markdown_content = self.generate(data)
        # 确保输出目录存在，若不存在则自动创建（包括所有中间目录）
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

        # 以UTF-8编码写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        logger.info(f"Markdown已保存: {output_path}")
        return output_path

    def _get_patent_name(self, data: Dict) -> str:
        """获取专利名称（自适应字段名）。

        不同类型的专利使用不同的字段名存储名称：
        - 实用新型 → "实用新型名称"
        - 发明 → "发明名称"
        - 外观设计 → "外观设计名称"

        按优先级依次查找，返回第一个非空的名称值。

        Args:
            data: 专利信息JSON字典

        Returns:
            str: 专利名称；若所有字段名都不存在或值为空，则返回"未知专利"
        """
        for key in ['实用新型名称', '发明名称', '外观设计名称']:
            if key in data and data[key]:
                return data[key]
        return '未知专利'
