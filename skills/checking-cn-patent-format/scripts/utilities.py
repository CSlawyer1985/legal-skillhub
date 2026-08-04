#!/usr/bin/env python3
"""
用于编辑 OOXML 文档的工具。

本模块提供 XMLEditor，一个用于操作 XML 文件的工具，支持
基于行号的节点查找和 DOM 操作。
"""

# html 模块用于转义 HTML/XML 特殊字符
import html
# Path 用于面向对象的文件路径处理
from pathlib import Path
# Optional 和 Union 用于类型注解
from typing import Optional, Union

# defusedxml 是安全的 XML 解析库，minidom 提供 DOM 操作接口
import defusedxml.minidom
# defusedxml.sax 提供 SAX 解析器接口
import defusedxml.sax


class XMLEditor:
    """
    用于操作 OOXML XML 文件的编辑器，支持基于行号的节点查找。

    这个类封装了 XML DOM 操作，提供了便捷的节点查找和修改方法。
    它是 DocxXMLEditor 的父类，后者添加了 Word 特有的功能。
    """

    def __init__(self, xml_path):
        """
        初始化 XML 编辑器。

        Args:
            xml_path: XML 文件的路径
        """
        self.xml_path = Path(xml_path)
        if not self.xml_path.exists():
            raise ValueError(f"XML 文件未找到: {xml_path}")

        # 检测文件编码（OOXML 文件通常是 UTF-8 或 ASCII）
        with open(self.xml_path, "rb") as f:
            header = f.read(200).decode("utf-8", errors="ignore")
        self.encoding = "ascii" if 'encoding="ascii"' in header else "utf-8"

        # 创建带有行号追踪功能的 SAX 解析器
        parser = _create_line_tracking_parser()
        # 使用 minidom 解析 XML 文件，生成 DOM 对象
        self.dom = defusedxml.minidom.parse(str(self.xml_path), parser)

    def get_node(
        self,
        tag: str,
        attrs: Optional[dict[str, str]] = None,
        line_number: Optional[Union[int, range]] = None,
        contains: Optional[str] = None,
    ):
        """
        根据条件查找单个 XML 节点。

        支持按标签名、属性、行号、包含文本等多种条件组合查找。
        如果找到多个匹配节点，会抛出错误。

        Args:
            tag: 元素标签名（如 "w:p"）
            attrs: 属性字典（如 {"w:id": "1"}）
            line_number: 行号或行号范围
            contains: 包含的文本内容

        Returns:
            匹配的 DOM 元素节点

        Raises:
            ValueError: 未找到节点或找到多个节点
        """
        matches = []
        # 遍历文档中所有指定标签的元素
        for elem in self.dom.getElementsByTagName(tag):
            # 检查行号条件
            if line_number is not None:
                parse_pos = getattr(elem, "parse_position", (None,))
                elem_line = parse_pos[0]

                if isinstance(line_number, range):
                    if elem_line not in line_number:
                        continue
                else:
                    if elem_line != line_number:
                        continue

            # 检查属性条件
            if attrs is not None:
                if not all(
                    elem.getAttribute(attr_name) == attr_value
                    for attr_name, attr_value in attrs.items()
                ):
                    continue

            # 检查包含文本条件
            if contains is not None:
                elem_text = self._get_element_text(elem)
                normalized_contains = html.unescape(contains)
                if normalized_contains not in elem_text:
                    continue

            matches.append(elem)

        # 未找到匹配节点
        if not matches:
            filters = []
            if line_number is not None:
                line_str = (
                    f"第 {line_number.start}-{line_number.stop - 1} 行"
                    if isinstance(line_number, range)
                    else f"第 {line_number} 行"
                )
                filters.append(f"在 {line_str}")
            if attrs is not None:
                filters.append(f"属性为 {attrs}")
            if contains is not None:
                filters.append(f"包含 '{contains}'")

            filter_desc = " ".join(filters) if filters else ""
            base_msg = f"未找到节点: <{tag}> {filter_desc}".strip()

            if contains:
                hint = "文本可能分布在多个元素中或使用了不同的措辞。"
            elif line_number:
                hint = "如果文档被修改，行号可能已更改。"
            elif attrs:
                hint = "请验证属性值是否正确。"
            else:
                hint = "尝试添加过滤器（attrs、line_number 或 contains）。"

            raise ValueError(f"{base_msg}。{hint}")

        # 找到多个匹配节点
        if len(matches) > 1:
            raise ValueError(
                f"找到多个节点: <{tag}>。"
                f"添加更多过滤器（attrs、line_number 或 contains）以缩小搜索范围。"
            )
        return matches[0]

    def _get_element_text(self, elem):
        """
        递归获取元素的所有文本内容。

        遍历元素及其子元素的所有文本节点，拼接成完整文本。
        """
        text_parts = []
        for node in elem.childNodes:
            if node.nodeType == node.TEXT_NODE:
                if node.data.strip():
                    text_parts.append(node.data)
            elif node.nodeType == node.ELEMENT_NODE:
                text_parts.append(self._get_element_text(node))
        return "".join(text_parts)

    def replace_node(self, elem, new_content):
        """
        替换指定元素为新内容。

        Args:
            elem: 要替换的元素
            new_content: 新的 XML 内容字符串

        Returns:
            新插入的节点列表
        """
        parent = elem.parentNode
        nodes = self._parse_fragment(new_content)
        for node in nodes:
            parent.insertBefore(node, elem)
        parent.removeChild(elem)
        return nodes

    def insert_after(self, elem, xml_content):
        """
        在指定元素后插入新内容。

        Args:
            elem: 参考元素
            xml_content: 要插入的 XML 内容字符串

        Returns:
            新插入的节点列表
        """
        parent = elem.parentNode
        next_sibling = elem.nextSibling
        nodes = self._parse_fragment(xml_content)
        for node in nodes:
            if next_sibling:
                parent.insertBefore(node, next_sibling)
            else:
                parent.appendChild(node)
        return nodes

    def insert_before(self, elem, xml_content):
        """
        在指定元素前插入新内容。

        Args:
            elem: 参考元素
            xml_content: 要插入的 XML 内容字符串

        Returns:
            新插入的节点列表
        """
        parent = elem.parentNode
        nodes = self._parse_fragment(xml_content)
        for node in nodes:
            parent.insertBefore(node, elem)
        return nodes

    def append_to(self, elem, xml_content):
        """
        在指定元素末尾追加新内容。

        Args:
            elem: 父元素
            xml_content: 要追加的 XML 内容字符串

        Returns:
            新插入的节点列表
        """
        nodes = self._parse_fragment(xml_content)
        for node in nodes:
            elem.appendChild(node)
        return nodes

    def get_next_rid(self):
        """
        获取下一个可用的关系 ID（rId）。

        遍历所有 Relationship 元素，找到最大的 rId 编号，返回下一个。
        """
        max_id = 0
        for rel_elem in self.dom.getElementsByTagName("Relationship"):
            rel_id = rel_elem.getAttribute("Id")
            if rel_id.startswith("rId"):
                try:
                    max_id = max(max_id, int(rel_id[3:]))
                except ValueError:
                    pass
        return f"rId{max_id + 1}"

    def save(self):
        """
        将修改后的 DOM 保存回 XML 文件。

        使用检测到的编码（UTF-8 或 ASCII）写入文件。
        """
        content = self.dom.toxml(encoding=self.encoding)
        self.xml_path.write_bytes(content)

    def _parse_fragment(self, xml_content):
        """
        解析 XML 片段字符串为 DOM 节点列表。

        由于 XML 片段可能包含命名空间声明，需要将其包装在一个
        带有完整命名空间声明的根元素中，然后解析。

        Args:
            xml_content: XML 片段字符串

        Returns:
            解析后的 DOM 节点列表
        """
        root_elem = self.dom.documentElement
        namespaces = []
        if root_elem and root_elem.attributes:
            for i in range(root_elem.attributes.length):
                attr = root_elem.attributes.item(i)
                if attr.name.startswith("xmlns"):
                    namespaces.append(f'{attr.name}="{attr.value}"')

        ns_decl = " ".join(namespaces)
        # 将片段包装在带有命名空间的根元素中
        wrapper = f"<root {ns_decl}>{xml_content}</root>"
        fragment_doc = defusedxml.minidom.parseString(wrapper)
        # 导入节点到当前文档
        nodes = [
            self.dom.importNode(child, deep=True)
            for child in fragment_doc.documentElement.childNodes
        ]
        elements = [n for n in nodes if n.nodeType == n.ELEMENT_NODE]
        assert elements, "片段必须包含至少一个元素"
        return nodes


def _create_line_tracking_parser():
    """
    创建带有行号追踪功能的 SAX 解析器。

    这个函数通过猴子补丁（monkey-patching）的方式，
    在 SAX 解析器的 startElementNS 回调中记录每个元素的起始行号。

    返回:
        配置好的 SAX 解析器
    """
    def set_content_handler(dom_handler):
        def startElementNS(name, tagName, attrs):
            # 调用原始的 startElementNS 回调
            orig_start_cb(name, tagName, attrs)
            # 获取当前正在处理的元素（栈顶元素）
            cur_elem = dom_handler.elementStack[-1]
            # 记录当前行号和列号
            cur_elem.parse_position = (
                parser._parser.CurrentLineNumber,
                parser._parser.CurrentColumnNumber,
            )

        # 保存原始回调函数
        orig_start_cb = dom_handler.startElementNS
        # 替换为新的回调函数
        dom_handler.startElementNS = startElementNS
        # 调用原始的 setContentHandler
        orig_set_content_handler(dom_handler)

    # 创建 SAX 解析器
    parser = defusedxml.sax.make_parser()
    # 保存原始的 setContentHandler 方法
    orig_set_content_handler = parser.setContentHandler
    # 替换为新的方法
    parser.setContentHandler = set_content_handler
    return parser
