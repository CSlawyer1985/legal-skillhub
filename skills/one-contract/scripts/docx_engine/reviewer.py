#!/usr/bin/env python3
"""
合同审查文档操作工具

功能：
1. 添加批注（批注模式）
2. 标记删除（修订模式）
3. 建议插入（修订模式）
4. 读取合同文本

使用示例：
    from scripts import ContractReviewer

    # 初始化
    reviewer = ContractReviewer("workspace/unpacked")

    # 添加批注
    node = reviewer.find_text("甲方")
    reviewer.add_comment(node, "建议明确甲方的具体法律主体")

    # 修订模式删除
    reviewer.suggest_deletion(node)

    # 保存
    reviewer.save()

依赖：
    - defusedxml 库
"""

import html
import difflib
import re
import unicodedata

from .document import Document, DocxXMLEditor

MAX_VISIBLE_CHANGE_SEGMENTS = 6
MERGEABLE_EQUAL_SEGMENT_LENGTH = 1
MERGEABLE_EQUAL_SEGMENT_PATTERN = re.compile(
    r'^[\s，。；：、,.!?！？（）()“”"\'《》〈〉【】\[\]\-—/]+$'
)
INVISIBLE_TEXT_CHARS = {"\u200b", "\u200c", "\u200d", "\u2060", "\ufeff"}

#: \u6bb5\u843d/\u5b57\u7b26\u5c5e\u6027\u4e0e\u6279\u6ce8\u951a\u70b9\u7b49**\u975e\u6b63\u6587**\u5143\u7d20\u3002\u6587\u672c\u62bd\u53d6\u5fc5\u987b\u6574\u68f5\u8df3\u8fc7\uff1a
#: \u4e0d\u8df3\u8fc7 `w:pPr` \u4f1a\u628a `w:pPr/w:tabs/w:tab`\uff08\u5236\u8868\u4f4d**\u5b9a\u4e49**\uff09\u8bfb\u6210\u6b63\u6587\u5236\u8868\u7b26 `\t`\uff0c
#: \u6bb5\u843d\u91cd\u5199\u65f6\u53c8\u628a\u5b83\u4eec\u5f53\u6587\u672c\u5199\u56de\uff0c\u4f7f\u4fee\u8ba2\u540e\u7684\u6bb5\u843d\u51ed\u7a7a\u591a\u51fa\u5236\u8868\u7b26
#: \uff08\u5b9e\u6d4b\uff1a\u67d0\u6761\u88ab\u4fee\u8ba2\u7684\u6bb5\u843d\u6bb5\u9996\u591a\u51fa 2 \u4e2a `\t`\uff0c"\u62d2\u7edd\u5168\u90e8\u4fee\u8ba2"\u89c6\u56fe\u56e0\u6b64\u4e0e\u539f\u7a3f\u4e0d\u4e00\u81f4\uff09\u3002
_NON_CONTENT_ELEMENT_TAGS = frozenset(
    {
        "w:pPr",
        "w:rPr",
        "w:sectPr",
        "w:tblPr",
        "w:trPr",
        "w:tcPr",
        "w:commentRangeStart",
        "w:commentRangeEnd",
        "w:commentReference",
        "w:bookmarkStart",
        "w:bookmarkEnd",
        "w:proofErr",
        "w:lastRenderedPageBreak",
    }
)


class ContractReviewer:
    """合同审查操作封装类

    封装 docx 技能的 Document 类，提供合同审查专用 API。
    支持批注模式和修订模式两种操作方式。

    Attributes:
        doc: 底层 Document 实例
    """

    def __init__(self, unpacked_dir, author="合同审查助手", initials="CA"):
        """
        初始化合同审查器

        Args:
            unpacked_dir: 解包后的 DOCX 目录路径
            author: 批注/修订的作者名称（默认"合同审查助手"）
            initials: 作者缩写（默认"CA"）

        Raises:
            ValueError: 如果目录不存在或不是有效的解包 DOCX 目录
        """
        self.doc = Document(
            unpacked_dir,
            track_revisions=True,
            author=author,
            initials=initials,
        )

    def find_text(self, text, tag="w:p", occurrence=None):
        """
        查找包含指定文本的节点

        Args:
            text: 要查找的文本
            tag: XML 标签类型（默认段落 w:p）

        Returns:
            找到的 DOM 节点

        Raises:
            ValueError: 如果未找到匹配节点或找到多个匹配

        Example:
            node = reviewer.find_text("甲方应承担")
            node = reviewer.find_text("金额", tag="w:r")
        """
        try:
            return self.find_node(tag=tag, contains=text, occurrence=occurrence)
        except ValueError:
            if tag != "w:p":
                raise
            matches = self._locate_text_occurrences_in_paragraphs(text)
            if not matches:
                raise
            if occurrence is None and len(matches) != 1:
                raise ValueError(
                    "Multiple normalized paragraph matches found. Add occurrence or selector."
                )
            index = 1 if occurrence is None else int(occurrence)
            if index < 1 or index > len(matches):
                raise ValueError(
                    f"Occurrence {index} out of range. Found {len(matches)} normalized matches."
                )
            return matches[index - 1]["paragraph"]

    def find_node(
        self,
        tag="w:p",
        attrs=None,
        line_number=None,
        contains=None,
        occurrence=None,
    ):
        """
        通用节点查询（支持 attrs / line_number / contains 组合过滤）

        Args:
            tag: XML 标签类型
            attrs: 属性字典
            line_number: 行号或 range
            contains: 文本包含条件

        Returns:
            DOM 节点
        """
        return self.doc["word/document.xml"].get_node(
            tag=tag,
            attrs=attrs,
            line_number=line_number,
            contains=contains,
            occurrence=occurrence,
        )

    def find_by_line(self, line_number, tag="w:p", occurrence=None):
        """
        按行号查找节点

        Args:
            line_number: XML 文件中的行号（1-indexed）
            tag: XML 标签类型

        Returns:
            找到的 DOM 节点

        Raises:
            ValueError: 如果未找到匹配节点

        Example:
            node = reviewer.find_by_line(42)
            node = reviewer.find_by_line(range(40, 50))
        """
        return self.doc["word/document.xml"].get_node(
            tag=tag, line_number=line_number, occurrence=occurrence
        )

    def find_by_attrs(self, tag, attrs, occurrence=None):
        """
        按属性查找节点

        Args:
            tag: XML 标签类型
            attrs: 属性字典

        Returns:
            找到的 DOM 节点

        Raises:
            ValueError: 如果未找到匹配节点

        Example:
            node = reviewer.find_by_attrs("w:p", {"w14:paraId": "12345678"})
        """
        return self.doc["word/document.xml"].get_node(
            tag=tag, attrs=attrs, occurrence=occurrence
        )

    def add_comment(self, node, text, end_node=None):
        """
        添加批注（批注模式）

        在指定节点范围添加批注。适用于指出风险、提供建议等场景。

        Args:
            node: 批注起始节点
            text: 批注内容
            end_node: 批注结束节点（可选，默认与起始相同）

        Returns:
            int: 批注 ID

        Example:
            node = reviewer.find_text("甲方承担全部责任")
            reviewer.add_comment(node, "P0风险：责任条款过重，建议限定损失范围")
        """
        end = end_node if end_node else node
        return self.doc.add_comment(start=node, end=end, text=text)

    def add_comment_by_text(self, target_text, comment_text, tag="w:p", occurrence=None):
        """
        按文本定位并添加批注

        Args:
            target_text: 目标文本（要求唯一匹配）
            comment_text: 批注内容
            tag: 匹配标签类型，默认段落 w:p

        Returns:
            int: 批注 ID
        """
        node = self.find_text(target_text, tag=tag, occurrence=occurrence)
        return self.add_comment(node, comment_text)

    def reply_to_comment(self, parent_comment_id, text):
        """
        回复已有批注

        Args:
            parent_comment_id: 父批注的 ID
            text: 回复内容

        Returns:
            int: 新批注 ID

        Example:
            reviewer.reply_to_comment(0, "已确认修改")
        """
        return self.doc.reply_to_comment(parent_comment_id=parent_comment_id, text=text)

    def suggest_deletion(self, node):
        """
        建议删除（修订模式）

        将节点标记为删除，使用 Track Changes 样式。
        适用于明确错误需要删除的场景。

        Args:
            node: 要标记删除的节点（w:r 或 w:p）

        Returns:
            修改后的节点

        Raises:
            ValueError: 如果节点已包含跟踪修改

        Example:
            run = reviewer.find_text("违约金为全部合同金额", tag="w:r")
            reviewer.suggest_deletion(run)
        """
        return self.doc["word/document.xml"].suggest_deletion(node)

    def suggest_insertion(self, node, xml_content):
        """
        建议插入（修订模式）

        在节点后插入新内容，使用 Track Changes 样式。
        适用于需要添加新内容的场景。

        Args:
            node: 插入位置参考节点
            xml_content: 要插入的 XML 内容（段落格式）

        Returns:
            list: 插入的新节点列表

        Example:
            para = reviewer.find_text("第一条")
            new_content = '<w:p><w:r><w:t>新增条款内容</w:t></w:r></w:p>'
            reviewer.suggest_insertion(para, new_content)
        """
        wrapped = DocxXMLEditor.suggest_paragraph(xml_content)
        return self.doc["word/document.xml"].insert_after(node, wrapped)

    def _clone_context_formatting(self, node):
        """Return ``(pPr_xml, rPr_xml)`` cloned from the anchor paragraph.

        An inserted paragraph should inherit the surrounding formatting —
        font, size, indentation, spacing and list numbering — instead of
        falling back to the document default. Only the nearest ``w:p``
        ancestor is used, and any section break is stripped from the cloned
        paragraph properties so the insertion does not create a nested
        section.

        Args:
            node: 插入锚点节点（通常是 ``w:p``）

        Returns:
            tuple[str, str]: 锚点段落的 ``w:pPr`` 与首个可见 run 的 ``w:rPr``
        """
        para = node
        if getattr(node, "tagName", None) != "w:p":
            cursor = node
            for _ in range(10):
                cursor = getattr(cursor, "parentNode", None)
                if cursor is None:
                    break
                if getattr(cursor, "tagName", None) == "w:p":
                    para = cursor
                    break

        ppr_xml = ""
        rpr_xml = ""
        if getattr(para, "tagName", None) != "w:p":
            return ppr_xml, rpr_xml

        for child in getattr(para, "childNodes", ()):
            if getattr(child, "tagName", None) == "w:pPr":
                cloned = child.cloneNode(True)
                for sub in list(cloned.childNodes):
                    if getattr(sub, "tagName", None) == "w:sectPr":
                        cloned.removeChild(sub)
                ppr_xml = cloned.toxml()
                break

        for run in para.getElementsByTagName("w:r"):
            for child in getattr(run, "childNodes", ()):
                if getattr(child, "tagName", None) == "w:rPr":
                    rpr_xml = child.toxml()
                    break
            if rpr_xml:
                break

        return ppr_xml, rpr_xml

    def insert_text_after(self, node, text, as_paragraph=False):
        """
        在指定节点后插入文本（带修订痕迹）

        Args:
            node: 插入锚点节点
            text: 要插入的纯文本内容
            as_paragraph: 是否按段落插入（默认 False，按 run 插入）

        Returns:
            list: 插入的新节点列表
        """
        escaped = html.escape(text, quote=False)
        if as_paragraph:
            ppr_xml, rpr_xml = self._clone_context_formatting(node)
            paragraph_xml = (
                f"<w:p>{ppr_xml}<w:r>{rpr_xml}<w:t>{escaped}</w:t></w:r></w:p>"
            )
            return self.suggest_insertion(node, paragraph_xml)

        insertion_xml = f"<w:ins><w:r><w:t>{escaped}</w:t></w:r></w:ins>"
        return self.doc["word/document.xml"].insert_after(node, insertion_xml)

    def _get_document_text(self, node):
        return self.doc["word/document.xml"]._get_element_text(node)

    def _get_accepted_text(self, node):
        """Return the final/accepted text view for a node containing revisions.

        **只收正文**：段落属性、字符属性与批注锚点等元素整棵跳过
        （见 `_NON_CONTENT_ELEMENT_TAGS`）。否则 `w:pPr/w:tabs` 里的制表位定义
        会被读成正文制表符，并在段落重写时写回成字面 `\\t`。
        """
        if getattr(node, "nodeType", None) != node.ELEMENT_NODE:
            return ""
        if getattr(node, "tagName", "") in _NON_CONTENT_ELEMENT_TAGS:
            return ""
        if getattr(node, "tagName", "") in {"w:del", "w:moveFrom", "w:delText"}:
            return ""
        if getattr(node, "tagName", "") in {"w:t", "w:instrText"}:
            return "".join(
                child.data
                for child in node.childNodes
                if child.nodeType == child.TEXT_NODE
            )
        if getattr(node, "tagName", "") == "w:tab":
            return "\t"
        return "".join(
            self._get_accepted_text(child)
            for child in node.childNodes
            if child.nodeType == child.ELEMENT_NODE
        )

    def _get_direct_child(self, node, tag_name):
        for child in node.childNodes:
            if child.nodeType == child.ELEMENT_NODE and child.nodeName == tag_name:
                return child
        return None

    def _find_ancestor(self, node, tag_name):
        current = node
        while current is not None:
            if getattr(current, "tagName", None) == tag_name:
                return current
            current = getattr(current, "parentNode", None)
        return None

    def _has_tracked_changes(self, node):
        revision_tags = {"w:ins", "w:del", "w:moveFrom", "w:moveTo"}
        if getattr(node, "tagName", "") in revision_tags:
            return True
        ancestor = getattr(node, "parentNode", None)
        while ancestor is not None:
            if getattr(ancestor, "tagName", "") in revision_tags:
                return True
            ancestor = getattr(ancestor, "parentNode", None)
        return any(node.getElementsByTagName(tag) for tag in revision_tags)

    @staticmethod
    def _normalize_text_with_map(text):
        """Normalize Word-visible text while retaining offsets into the source string.

        Word frequently splits visually continuous text across runs and represents
        spaces using NBSP/full-width spaces. Locators compare a normalized view but
        edits still slice the original paragraph text with the returned offsets.
        """
        normalized = []
        source_indexes = []
        for source_index, char in enumerate(text):
            if char in INVISIBLE_TEXT_CHARS:
                continue
            expanded = unicodedata.normalize("NFKC", char)
            for normalized_char in expanded:
                if normalized_char.isspace():
                    normalized_char = " "
                    if normalized and normalized[-1] == " ":
                        continue
                normalized.append(normalized_char)
                source_indexes.append(source_index)
        return "".join(normalized), source_indexes

    def _get_first_text_run(self, paragraph_node):
        for run in paragraph_node.getElementsByTagName("w:r"):
            if self._get_document_text(run):
                return run
        return None

    def _get_run_properties_xml(self, run_node):
        if run_node is None:
            return ""
        rpr = self._get_direct_child(run_node, "w:rPr")
        return rpr.toxml() if rpr is not None else ""

    def _build_text_element_xml(self, text, *, deleted=False):
        escaped = html.escape(text, quote=False)
        tag_name = "w:delText" if deleted else "w:t"
        preserve_space = text[:1].isspace() or text[-1:].isspace()
        space_attr = ' xml:space="preserve"' if preserve_space else ""
        return f"<{tag_name}{space_attr}>{escaped}</{tag_name}>"

    def _build_run_xml(self, text, template_run=None, *, deleted=False):
        if not text:
            return ""
        rpr_xml = self._get_run_properties_xml(template_run)
        text_xml = self._build_text_element_xml(text, deleted=deleted)
        return f"<w:r>{rpr_xml}{text_xml}</w:r>"

    def _append_revision_segment(self, segments, kind, text):
        if not text:
            return
        if segments and segments[-1][0] == kind:
            previous_kind, previous_text = segments[-1]
            segments[-1] = (previous_kind, previous_text + text)
            return
        segments.append((kind, text))

    def _is_change_segment(self, kind):
        return kind in {"delete", "insert"}

    def _is_mergeable_equal_segment(self, text):
        if not text:
            return False
        if len(text) <= MERGEABLE_EQUAL_SEGMENT_LENGTH:
            return True
        return bool(MERGEABLE_EQUAL_SEGMENT_PATTERN.fullmatch(text))

    def _project_revision_block_text(self, segments, *, include_equal, include_delete, include_insert):
        parts = []
        for kind, text in segments:
            if kind == "equal" and include_equal:
                parts.append(text)
            elif kind == "delete" and include_delete:
                parts.append(text)
            elif kind == "insert" and include_insert:
                parts.append(text)
        return "".join(parts)

    def _merge_revision_change_blocks(self, segments, equal_index):
        left = equal_index - 1
        while left - 1 >= 0 and self._is_change_segment(segments[left - 1][0]):
            left -= 1

        right = equal_index + 1
        while right + 1 < len(segments) and self._is_change_segment(segments[right + 1][0]):
            right += 1

        block = segments[left : right + 1]
        old_text = self._project_revision_block_text(
            block,
            include_equal=True,
            include_delete=True,
            include_insert=False,
        )
        new_text = self._project_revision_block_text(
            block,
            include_equal=True,
            include_delete=False,
            include_insert=True,
        )

        replacement = []
        if old_text == new_text:
            self._append_revision_segment(replacement, "equal", old_text)
        else:
            self._append_revision_segment(replacement, "delete", old_text)
            self._append_revision_segment(replacement, "insert", new_text)

        compacted = []
        for kind, text in segments[:left] + replacement + segments[right + 1 :]:
            self._append_revision_segment(compacted, kind, text)
        return compacted

    def _count_visible_change_segments(self, segments):
        return sum(1 for kind, _ in segments if self._is_change_segment(kind))

    def _compact_revision_segments(self, segments):
        compacted = list(segments)

        merged = True
        while merged:
            merged = False
            for index in range(1, len(compacted) - 1):
                kind, text = compacted[index]
                if kind != "equal":
                    continue
                if not self._is_change_segment(compacted[index - 1][0]):
                    continue
                if not self._is_change_segment(compacted[index + 1][0]):
                    continue
                if not self._is_mergeable_equal_segment(text):
                    continue
                compacted = self._merge_revision_change_blocks(compacted, index)
                merged = True
                break

        while self._count_visible_change_segments(compacted) > MAX_VISIBLE_CHANGE_SEGMENTS:
            candidates = []
            for index in range(1, len(compacted) - 1):
                kind, text = compacted[index]
                if kind != "equal":
                    continue
                if not self._is_change_segment(compacted[index - 1][0]):
                    continue
                if not self._is_change_segment(compacted[index + 1][0]):
                    continue
                candidates.append((len(text), index))
            if not candidates:
                break
            _, merge_index = min(candidates)
            compacted = self._merge_revision_change_blocks(compacted, merge_index)

        return compacted

    def _build_revision_segments(self, old_text, new_text):
        matcher = difflib.SequenceMatcher(a=old_text, b=new_text, autojunk=False)
        segments = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                self._append_revision_segment(segments, "equal", old_text[i1:i2])
            elif tag == "delete":
                self._append_revision_segment(segments, "delete", old_text[i1:i2])
            elif tag == "insert":
                self._append_revision_segment(segments, "insert", new_text[j1:j2])
            elif tag == "replace":
                self._append_revision_segment(segments, "delete", old_text[i1:i2])
                self._append_revision_segment(segments, "insert", new_text[j1:j2])
        return self._compact_revision_segments(segments)

    def _surround_revision_segments(self, segments, before_text="", after_text=""):
        combined = []
        self._append_revision_segment(combined, "equal", before_text)
        for kind, text in segments:
            self._append_revision_segment(combined, kind, text)
        self._append_revision_segment(combined, "equal", after_text)
        return combined

    def _build_change_fragment_xml(self, segments, template_run=None):
        parts = []
        for kind, text in segments:
            if kind == "equal":
                parts.append(self._build_run_xml(text, template_run))
            elif kind == "delete":
                parts.append(
                    f"<w:del>{self._build_run_xml(text, template_run, deleted=True)}</w:del>"
                )
            elif kind == "insert":
                parts.append(f"<w:ins>{self._build_run_xml(text, template_run)}</w:ins>")
        return "".join(parts)

    def _find_first_change_node(self, nodes):
        queue = list(nodes)
        while queue:
            node = queue.pop(0)
            if getattr(node, "tagName", None) in {"w:ins", "w:del", "w:p", "w:r"}:
                if getattr(node, "tagName", None) in {"w:ins", "w:del"}:
                    return node
            for child in getattr(node, "childNodes", []):
                if getattr(child, "nodeType", None) == child.ELEMENT_NODE:
                    queue.append(child)
        return nodes[0] if nodes else None

    def _build_paragraph_xml(self, paragraph_node, text):
        """整段重写：保留段落属性与**首个正文 run 的字符格式**。

        此前这里产出的是裸 `<w:r>`，会丢掉原段落的字体/字号等字符格式；
        段落属性里的制表位定义也一度被当成正文制表符（见 `_get_accepted_text`）。
        """
        ppr = self._get_direct_child(paragraph_node, "w:pPr")
        ppr_xml = ppr.toxml() if ppr is not None else ""
        template_run = self._get_first_text_run(paragraph_node)
        return f"<w:p>{ppr_xml}{self._build_run_xml(text, template_run)}</w:p>"

    def _build_fragment_paragraph_xml(
        self,
        paragraph_node,
        *,
        segments,
        template_run=None,
    ):
        ppr = self._get_direct_child(paragraph_node, "w:pPr")
        ppr_xml = ppr.toxml() if ppr is not None else ""
        body_xml = self._build_change_fragment_xml(segments, template_run=template_run)
        comment_starts = "".join(
            node.toxml()
            for node in paragraph_node.getElementsByTagName("w:commentRangeStart")
        )
        comment_ends = "".join(
            node.toxml()
            for node in paragraph_node.getElementsByTagName("w:commentRangeEnd")
        )
        reference_runs = []
        seen_reference_ids = set()
        for reference in paragraph_node.getElementsByTagName("w:commentReference"):
            comment_id = reference.getAttribute("w:id")
            if comment_id in seen_reference_ids:
                continue
            run = self._find_ancestor(reference, "w:r")
            if run is not None:
                reference_runs.append(run.toxml())
                seen_reference_ids.add(comment_id)
        return (
            f"<w:p>{ppr_xml}{comment_starts}{body_xml}"
            f"{comment_ends}{''.join(reference_runs)}</w:p>"
        )

    def _replace_within_run(
        self,
        run_node,
        *,
        old_text,
        new_text,
        comment_text=None,
    ):
        if self._has_tracked_changes(run_node):
            raise ValueError("run already contains tracked changes")

        run_text = self._get_document_text(run_node)
        start = run_text.find(old_text)
        if start < 0:
            raise ValueError("target text not found inside run")

        revision_segments = self._build_revision_segments(old_text, new_text)
        replacement_xml = self._build_change_fragment_xml(
            self._surround_revision_segments(
                revision_segments,
                before_text=run_text[:start],
                after_text=run_text[start + len(old_text) :],
            ),
            template_run=run_node,
        )
        nodes = self.doc["word/document.xml"].replace_node(run_node, replacement_xml)
        anchor = self._find_first_change_node(nodes)
        if comment_text and anchor is not None:
            self.add_comment(anchor, comment_text)
        return {
            "deleted": anchor,
            "inserted": nodes,
            "fallback": "run_fragment",
        }

    def _locate_text_occurrences_in_paragraphs(self, text):
        normalized_target, _ = self._normalize_text_with_map(str(text))
        if not normalized_target:
            raise ValueError("target text is empty after normalization")
        matches = []
        for paragraph in self.get_paragraphs():
            # Locate against the accepted view. This keeps later findings stable
            # after an earlier finding has inserted w:del/w:ins segments.
            paragraph_text = self._get_accepted_text(paragraph)
            normalized_text, source_indexes = self._normalize_text_with_map(paragraph_text)
            start = 0
            while True:
                index = normalized_text.find(normalized_target, start)
                if index < 0:
                    break
                raw_start = source_indexes[index]
                raw_end = source_indexes[index + len(normalized_target) - 1] + 1
                matches.append(
                    {
                        "paragraph": paragraph,
                        "paragraph_text": paragraph_text,
                        "start": raw_start,
                        "end": raw_end,
                        "normalized_target": normalized_target,
                    }
                )
                start = index + len(normalized_target)
        return matches

    def replace_text_via_paragraph_rewrite(
        self,
        old_text,
        new_text,
        occurrence=None,
        comment_text=None,
    ):
        matches = self._locate_text_occurrences_in_paragraphs(old_text)
        if not matches:
            raise ValueError(
                f"Node not found: <w:p> containing '{old_text}'. "
                "Text may be split across elements or use different wording."
            )
        if occurrence is None and len(matches) > 1:
            raise ValueError(
                "Multiple paragraph matches found for spanning text. "
                "Add occurrence or selector to narrow the search."
            )

        index = 1 if occurrence is None else int(occurrence)
        if index < 1 or index > len(matches):
            raise ValueError(
                f"Occurrence {index} out of range for spanning text. "
                f"Only {len(matches)} match(es) found."
            )

        match = matches[index - 1]
        paragraph = match["paragraph"]
        if self._has_tracked_changes(paragraph):
            raise ValueError(
                "目标段落含既有修订；请使用 --existing-revisions accept-existing "
                "先固定基线，或仅添加批注。为避免嵌套/覆盖历史修订，本次未改写。"
            )
        paragraph_text = match["paragraph_text"]
        start = match["start"]
        end = match["end"]
        updated_text = (
            paragraph_text[:start]
            + new_text
            + paragraph_text[end:]
        )
        replacement_xml = self._build_paragraph_xml(paragraph, updated_text)
        deleted = self.suggest_deletion(paragraph)
        inserted = self.suggest_insertion(deleted, replacement_xml)

        if comment_text and inserted:
            self.add_comment(inserted[0], comment_text)

        return {
            "deleted": deleted,
            "inserted": inserted,
            "fallback": "paragraph_rewrite",
        }

    def replace_text_via_paragraph(
        self,
        old_text,
        new_text,
        occurrence=None,
        comment_text=None,
    ):
        matches = self._locate_text_occurrences_in_paragraphs(old_text)
        if not matches:
            raise ValueError(
                f"Node not found: <w:p> containing '{old_text}'. "
                "Text may be split across elements or use different wording."
            )
        if occurrence is None and len(matches) > 1:
            raise ValueError(
                "Multiple paragraph matches found for spanning text. "
                "Add occurrence or selector to narrow the search."
            )

        index = 1 if occurrence is None else int(occurrence)
        if index < 1 or index > len(matches):
            raise ValueError(
                f"Occurrence {index} out of range for spanning text. "
                f"Only {len(matches)} match(es) found."
            )

        match = matches[index - 1]
        paragraph = match["paragraph"]
        if self._has_tracked_changes(paragraph):
            raise ValueError(
                "目标段落含既有修订；请使用 --existing-revisions accept-existing "
                "先固定基线，或仅添加批注。为避免嵌套/覆盖历史修订，本次未修改。"
            )

        paragraph_text = match["paragraph_text"]
        start = match["start"]
        end = match["end"]
        revision_segments = self._build_revision_segments(old_text, new_text)
        template_run = self._get_first_text_run(paragraph)
        replacement_xml = self._build_fragment_paragraph_xml(
            paragraph,
            segments=self._surround_revision_segments(
                revision_segments,
                before_text=paragraph_text[:start],
                after_text=paragraph_text[end:],
            ),
            template_run=template_run,
        )
        nodes = self.doc["word/document.xml"].replace_node(paragraph, replacement_xml)
        anchor = self._find_first_change_node(nodes)
        if comment_text and anchor is not None:
            self.add_comment(anchor, comment_text)

        return {
            "deleted": anchor,
            "inserted": nodes,
            "fallback": "paragraph_fragment",
        }

    def replace_text(
        self,
        old_text,
        new_text,
        tag="w:r",
        comment_text=None,
        occurrence=None,
    ):
        """
        替换文本（删除旧文本 + 插入新文本）

        Args:
            old_text: 需替换的原文本（唯一匹配）
            new_text: 替换后的新文本
            tag: 匹配标签，默认 w:r；段落替换可用 w:p
            comment_text: 可选，替换后在新节点添加批注

        Returns:
            dict: {"deleted": 删除节点, "inserted": 插入节点列表}
        """
        try:
            target = self.find_text(old_text, tag=tag, occurrence=occurrence)
            if tag == "w:r":
                return self._replace_within_run(
                    target,
                    old_text=old_text,
                    new_text=new_text,
                    comment_text=comment_text,
                )
            if tag == "w:p":
                return self.replace_text_via_paragraph(
                    old_text=old_text,
                    new_text=new_text,
                    occurrence=occurrence,
                    comment_text=comment_text,
                )
        except ValueError as exc:
            if tag == "w:r":
                return self.replace_text_via_paragraph(
                    old_text=old_text,
                    new_text=new_text,
                    occurrence=occurrence,
                    comment_text=comment_text,
                )
            raise exc
        deleted = self.suggest_deletion(target)

        anchor = deleted
        if (
            tag == "w:r"
            and getattr(deleted, "parentNode", None) is not None
            and getattr(deleted.parentNode, "tagName", "") == "w:del"
        ):
            anchor = deleted.parentNode

        inserted = self.insert_text_after(anchor, new_text, as_paragraph=(tag == "w:p"))

        if comment_text and inserted:
            self.add_comment(inserted[0], comment_text)

        return {"deleted": deleted, "inserted": inserted}

    def delete_text(self, target_text, tag="w:r", comment_text=None, occurrence=None):
        try:
            node = self.find_text(target_text, tag=tag, occurrence=occurrence)
            if tag == "w:r":
                return self._replace_within_run(
                    node,
                    old_text=target_text,
                    new_text="",
                    comment_text=comment_text,
                )
            if tag == "w:p":
                return self.replace_text_via_paragraph(
                    old_text=target_text,
                    new_text="",
                    occurrence=occurrence,
                    comment_text=comment_text,
                )
            deleted = self.suggest_deletion(node)
            if comment_text:
                self.add_comment(node, comment_text)
            return {"deleted": deleted, "fallback": None}
        except ValueError as exc:
            if tag == "w:r":
                return self.replace_text_via_paragraph(
                    old_text=target_text,
                    new_text="",
                    occurrence=occurrence,
                    comment_text=comment_text,
                )
            raise exc

    def replace_node(self, node, new_text, tag="w:r", comment_text=None):
        """
        按节点替换文本（删除目标节点 + 插入新文本）

        Args:
            node: 要替换的目标节点
            new_text: 替换后的新文本
            tag: 目标标签类型，用于判断插入模式（w:p 段落 / w:r run）
            comment_text: 可选，替换后在新节点添加批注

        Returns:
            dict: {"deleted": 删除节点, "inserted": 插入节点列表}
        """
        deleted = self.suggest_deletion(node)

        anchor = deleted
        if (
            tag == "w:r"
            and getattr(deleted, "parentNode", None) is not None
            and getattr(deleted.parentNode, "tagName", "") == "w:del"
        ):
            anchor = deleted.parentNode

        inserted = self.insert_text_after(anchor, new_text, as_paragraph=(tag == "w:p"))

        if comment_text and inserted:
            self.add_comment(inserted[0], comment_text)

        return {"deleted": deleted, "inserted": inserted}

    def revert_insertion(self, node):
        """
        撤销插入（修订模式）

        拒绝已有的插入，将其转为删除标记。

        Args:
            node: 要处理的 w:ins 节点或包含 w:ins 的容器

        Returns:
            list: 处理后的节点列表

        Raises:
            ValueError: 如果节点不包含 w:ins 元素
        """
        return self.doc["word/document.xml"].revert_insertion(node)

    def revert_deletion(self, node):
        """
        撤销删除（修订模式）

        拒绝已有的删除，恢复被删除的内容。

        Args:
            node: 要处理的 w:del 节点或包含 w:del 的容器

        Returns:
            list: 处理后的节点列表

        Raises:
            ValueError: 如果节点不包含 w:del 元素
        """
        return self.doc["word/document.xml"].revert_deletion(node)

    def save(self, destination=None, validate=True):
        """
        保存修改后的文档

        Args:
            destination: 输出目录（可选，默认覆盖原目录）
            validate: 是否验证文档有效性（默认 True）

        Raises:
            ValueError: 如果验证失败
        """
        self.doc.save(destination=destination, validate=validate)

    def get_full_text(self):
        """
        获取合同全文文本

        Returns:
            str: 文档的纯文本内容

        Example:
            text = reviewer.get_full_text()
            print(f"合同共 {len(text)} 字")
        """
        text_parts = []
        for elem in self.doc["word/document.xml"].dom.getElementsByTagName("w:t"):
            if elem.firstChild:
                text_parts.append(elem.firstChild.data)
        return "".join(text_parts)

    def get_paragraphs(self):
        """
        获取所有段落节点

        Returns:
            list: w:p 节点列表

        Example:
            for para in reviewer.get_paragraphs():
                # 处理每个段落
                pass
        """
        return list(self.doc["word/document.xml"].dom.getElementsByTagName("w:p"))

    def validate(self):
        """
        验证文档有效性

        Raises:
            ValueError: 如果验证失败
        """
        self.doc.validate()

    def set_operation_timestamp(self, timestamp):
        self.doc.set_operation_timestamp(timestamp)

    def clear_operation_timestamp(self):
        self.doc.clear_operation_timestamp()
