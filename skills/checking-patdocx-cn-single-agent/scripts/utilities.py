#!/usr/bin/env python3
"""
用于编辑 OOXML 文档的工具。

本模块提供 XMLEditor，一个用于操作 XML 文件的工具，支持
基于行号的节点查找和 DOM 操作。
"""

import html
from pathlib import Path
from typing import Optional, Union

import defusedxml.minidom
import defusedxml.sax


class XMLEditor:
    """
    用于操作 OOXML XML 文件的编辑器，支持基于行号的节点查找。
    """

    def __init__(self, xml_path):
        self.xml_path = Path(xml_path)
        if not self.xml_path.exists():
            raise ValueError(f"XML 文件未找到: {xml_path}")

        with open(self.xml_path, "rb") as f:
            header = f.read(200).decode("utf-8", errors="ignore")
        self.encoding = "ascii" if 'encoding="ascii"' in header else "utf-8"

        parser = _create_line_tracking_parser()
        self.dom = defusedxml.minidom.parse(str(self.xml_path), parser)

    def get_node(
        self,
        tag: str,
        attrs: Optional[dict[str, str]] = None,
        line_number: Optional[Union[int, range]] = None,
        contains: Optional[str] = None,
    ):
        matches = []
        for elem in self.dom.getElementsByTagName(tag):
            if line_number is not None:
                parse_pos = getattr(elem, "parse_position", (None,))
                elem_line = parse_pos[0]

                if isinstance(line_number, range):
                    if elem_line not in line_number:
                        continue
                else:
                    if elem_line != line_number:
                        continue

            if attrs is not None:
                if not all(
                    elem.getAttribute(attr_name) == attr_value
                    for attr_name, attr_value in attrs.items()
                ):
                    continue

            if contains is not None:
                elem_text = self._get_element_text(elem)
                normalized_contains = html.unescape(contains)
                if normalized_contains not in elem_text:
                    continue

            matches.append(elem)

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
        if len(matches) > 1:
            raise ValueError(
                f"找到多个节点: <{tag}>。"
                f"添加更多过滤器（attrs、line_number 或 contains）以缩小搜索范围。"
            )
        return matches[0]

    def _get_element_text(self, elem):
        text_parts = []
        for node in elem.childNodes:
            if node.nodeType == node.TEXT_NODE:
                if node.data.strip():
                    text_parts.append(node.data)
            elif node.nodeType == node.ELEMENT_NODE:
                text_parts.append(self._get_element_text(node))
        return "".join(text_parts)

    def replace_node(self, elem, new_content):
        parent = elem.parentNode
        nodes = self._parse_fragment(new_content)
        for node in nodes:
            parent.insertBefore(node, elem)
        parent.removeChild(elem)
        return nodes

    def insert_after(self, elem, xml_content):
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
        parent = elem.parentNode
        nodes = self._parse_fragment(xml_content)
        for node in nodes:
            parent.insertBefore(node, elem)
        return nodes

    def append_to(self, elem, xml_content):
        nodes = self._parse_fragment(xml_content)
        for node in nodes:
            elem.appendChild(node)
        return nodes

    def get_next_rid(self):
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
        content = self.dom.toxml(encoding=self.encoding)
        self.xml_path.write_bytes(content)

    def _parse_fragment(self, xml_content):
        root_elem = self.dom.documentElement
        namespaces = []
        if root_elem and root_elem.attributes:
            for i in range(root_elem.attributes.length):
                attr = root_elem.attributes.item(i)
                if attr.name.startswith("xmlns"):
                    namespaces.append(f'{attr.name}="{attr.value}"')

        ns_decl = " ".join(namespaces)
        wrapper = f"<root {ns_decl}>{xml_content}</root>"
        fragment_doc = defusedxml.minidom.parseString(wrapper)
        nodes = [
            self.dom.importNode(child, deep=True)
            for child in fragment_doc.documentElement.childNodes
        ]
        elements = [n for n in nodes if n.nodeType == n.ELEMENT_NODE]
        assert elements, "片段必须包含至少一个元素"
        return nodes


def _create_line_tracking_parser():
    def set_content_handler(dom_handler):
        def startElementNS(name, tagName, attrs):
            orig_start_cb(name, tagName, attrs)
            cur_elem = dom_handler.elementStack[-1]
            cur_elem.parse_position = (
                parser._parser.CurrentLineNumber,
                parser._parser.CurrentColumnNumber,
            )

        orig_start_cb = dom_handler.startElementNS
        dom_handler.startElementNS = startElementNS
        orig_set_content_handler(dom_handler)

    parser = defusedxml.sax.make_parser()
    orig_set_content_handler = parser.setContentHandler
    parser.setContentHandler = set_content_handler
    return parser
