#!/usr/bin/env python3
"""
用于处理 Word 文档的库：批注、修订追踪和编辑。

用法:
    from scripts.document import Document

    doc = Document('workspace/unpacked', author="docx_typo_checker.skill", initials="DC")
    node = doc["word/document.xml"].get_node(tag="w:r", contains="错字")
    doc.add_comment(start=node, end=node, text="批注文本")
    doc.save()
"""

import html
import random
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from defusedxml import minidom

from .utilities import XMLEditor

TEMPLATE_DIR = Path(__file__).parent / "templates"


class DocxXMLEditor(XMLEditor):
    """自动将 RSID、作者和日期应用到新元素的 XMLEditor。"""

    def __init__(
        self, xml_path, rsid: str, author: str = "checking-patdocx-cn-single-agent", initials: str = "PC"
    ):
        super().__init__(xml_path)
        self.rsid = rsid
        self.author = author
        self.initials = initials

    def _get_next_change_id(self):
        max_id = -1
        for tag in ("w:ins", "w:del"):
            elements = self.dom.getElementsByTagName(tag)
            for elem in elements:
                change_id = elem.getAttribute("w:id")
                if change_id:
                    try:
                        max_id = max(max_id, int(change_id))
                    except ValueError:
                        pass
        return max_id + 1

    def _ensure_w16du_namespace(self):
        root = self.dom.documentElement
        if not root.hasAttribute("xmlns:w16du"):
            root.setAttribute(
                "xmlns:w16du",
                "http://schemas.microsoft.com/office/word/2023/wordml/word16du",
            )

    def _ensure_w16cex_namespace(self):
        root = self.dom.documentElement
        if not root.hasAttribute("xmlns:w16cex"):
            root.setAttribute(
                "xmlns:w16cex",
                "http://schemas.microsoft.com/office/word/2018/wordml/cex",
            )

    def _ensure_w14_namespace(self):
        root = self.dom.documentElement
        if not root.hasAttribute("xmlns:w14"):
            root.setAttribute(
                "xmlns:w14",
                "http://schemas.microsoft.com/office/word/2010/wordml",
            )

    def _inject_attributes_to_nodes(self, nodes):
        timestamp = _get_local_timestamp()

        def is_inside_deletion(elem):
            parent = elem.parentNode
            while parent:
                if parent.nodeType == parent.ELEMENT_NODE and parent.tagName == "w:del":
                    return True
                parent = parent.parentNode
            return False

        def add_rsid_to_p(elem):
            if not elem.hasAttribute("w:rsidR"):
                elem.setAttribute("w:rsidR", self.rsid)
            if not elem.hasAttribute("w:rsidRDefault"):
                elem.setAttribute("w:rsidRDefault", self.rsid)
            if not elem.hasAttribute("w:rsidP"):
                elem.setAttribute("w:rsidP", self.rsid)
            if not elem.hasAttribute("w14:paraId"):
                self._ensure_w14_namespace()
                elem.setAttribute("w14:paraId", _generate_hex_id())
            if not elem.hasAttribute("w14:textId"):
                self._ensure_w14_namespace()
                elem.setAttribute("w14:textId", _generate_hex_id())

        def add_rsid_to_r(elem):
            if is_inside_deletion(elem):
                if not elem.hasAttribute("w:rsidDel"):
                    elem.setAttribute("w:rsidDel", self.rsid)
            else:
                if not elem.hasAttribute("w:rsidR"):
                    elem.setAttribute("w:rsidR", self.rsid)

        def add_tracked_change_attrs(elem):
            if not elem.hasAttribute("w:id"):
                elem.setAttribute("w:id", str(self._get_next_change_id()))
            if not elem.hasAttribute("w:author"):
                elem.setAttribute("w:author", self.author)
            if not elem.hasAttribute("w:date"):
                elem.setAttribute("w:date", timestamp)
            if elem.tagName in ("w:ins", "w:del") and not elem.hasAttribute(
                "w16du:dateUtc"
            ):
                self._ensure_w16du_namespace()
                elem.setAttribute("w16du:dateUtc", timestamp)

        def add_comment_attrs(elem):
            if not elem.hasAttribute("w:author"):
                elem.setAttribute("w:author", self.author)
            if not elem.hasAttribute("w:date"):
                elem.setAttribute("w:date", timestamp)
            if not elem.hasAttribute("w:initials"):
                elem.setAttribute("w:initials", self.initials)

        def add_comment_extensible_date(elem):
            if not elem.hasAttribute("w16cex:dateUtc"):
                self._ensure_w16cex_namespace()
                elem.setAttribute("w16cex:dateUtc", timestamp)

        def add_xml_space_to_t(elem):
            if (
                elem.firstChild
                and elem.firstChild.nodeType == elem.firstChild.TEXT_NODE
            ):
                text = elem.firstChild.data
                if text and (text[0].isspace() or text[-1].isspace()):
                    if not elem.hasAttribute("xml:space"):
                        elem.setAttribute("xml:space", "preserve")

        for node in nodes:
            if node.nodeType != node.ELEMENT_NODE:
                continue

            if node.tagName == "w:p":
                add_rsid_to_p(node)
            elif node.tagName == "w:r":
                add_rsid_to_r(node)
            elif node.tagName == "w:t":
                add_xml_space_to_t(node)
            elif node.tagName in ("w:ins", "w:del"):
                add_tracked_change_attrs(node)
            elif node.tagName == "w:comment":
                add_comment_attrs(node)
            elif node.tagName == "w16cex:commentExtensible":
                add_comment_extensible_date(node)

            for elem in node.getElementsByTagName("w:p"):
                add_rsid_to_p(elem)
            for elem in node.getElementsByTagName("w:r"):
                add_rsid_to_r(elem)
            for elem in node.getElementsByTagName("w:t"):
                add_xml_space_to_t(elem)
            for tag in ("w:ins", "w:del"):
                for elem in node.getElementsByTagName(tag):
                    add_tracked_change_attrs(elem)
            for elem in node.getElementsByTagName("w:comment"):
                add_comment_attrs(elem)
            for elem in node.getElementsByTagName("w16cex:commentExtensible"):
                add_comment_extensible_date(elem)

    def replace_node(self, elem, new_content):
        nodes = super().replace_node(elem, new_content)
        self._inject_attributes_to_nodes(nodes)
        return nodes

    def insert_after(self, elem, xml_content):
        nodes = super().insert_after(elem, xml_content)
        self._inject_attributes_to_nodes(nodes)
        return nodes

    def insert_before(self, elem, xml_content):
        nodes = super().insert_before(elem, xml_content)
        self._inject_attributes_to_nodes(nodes)
        return nodes

    def append_to(self, elem, xml_content):
        nodes = super().append_to(elem, xml_content)
        self._inject_attributes_to_nodes(nodes)
        return nodes

    def suggest_deletion(self, elem):
        if elem.nodeName == "w:r":
            if elem.getElementsByTagName("w:delText"):
                raise ValueError("w:r 元素已包含 w:delText")

            for t_elem in list(elem.getElementsByTagName("w:t")):
                del_text = self.dom.createElement("w:delText")
                while t_elem.firstChild:
                    del_text.appendChild(t_elem.firstChild)
                for i in range(t_elem.attributes.length):
                    attr = t_elem.attributes.item(i)
                    del_text.setAttribute(attr.name, attr.value)
                t_elem.parentNode.replaceChild(del_text, t_elem)

            if elem.hasAttribute("w:rsidR"):
                elem.setAttribute("w:rsidDel", elem.getAttribute("w:rsidR"))
                elem.removeAttribute("w:rsidR")
            elif not elem.hasAttribute("w:rsidDel"):
                elem.setAttribute("w:rsidDel", self.rsid)

            del_wrapper = self.dom.createElement("w:del")
            parent = elem.parentNode
            parent.insertBefore(del_wrapper, elem)
            parent.removeChild(elem)
            del_wrapper.appendChild(elem)

            self._inject_attributes_to_nodes([del_wrapper])
            return del_wrapper

        elif elem.nodeName == "w:p":
            if elem.getElementsByTagName("w:ins") or elem.getElementsByTagName("w:del"):
                raise ValueError("w:p 元素已包含修订追踪")

            pPr_list = elem.getElementsByTagName("w:pPr")
            is_numbered = pPr_list and pPr_list[0].getElementsByTagName("w:numPr")

            if is_numbered:
                pPr = pPr_list[0]
                rPr_list = pPr.getElementsByTagName("w:rPr")

                if not rPr_list:
                    rPr = self.dom.createElement("w:rPr")
                    pPr.appendChild(rPr)
                else:
                    rPr = rPr_list[0]

                del_marker = self.dom.createElement("w:del")
                rPr.insertBefore(
                    del_marker, rPr.firstChild
                ) if rPr.firstChild else rPr.appendChild(del_marker)

            for t_elem in list(elem.getElementsByTagName("w:t")):
                del_text = self.dom.createElement("w:delText")
                while t_elem.firstChild:
                    del_text.appendChild(t_elem.firstChild)
                for i in range(t_elem.attributes.length):
                    attr = t_elem.attributes.item(i)
                    del_text.setAttribute(attr.name, attr.value)
                t_elem.parentNode.replaceChild(del_text, t_elem)

            for run in elem.getElementsByTagName("w:r"):
                if run.hasAttribute("w:rsidR"):
                    run.setAttribute("w:rsidDel", run.getAttribute("w:rsidR"))
                    run.removeAttribute("w:rsidR")
                elif not run.hasAttribute("w:rsidDel"):
                    run.setAttribute("w:rsidDel", self.rsid)

            del_wrapper = self.dom.createElement("w:del")
            for child in [c for c in elem.childNodes if c.nodeName != "w:pPr"]:
                elem.removeChild(child)
                del_wrapper.appendChild(child)
            elem.appendChild(del_wrapper)

            self._inject_attributes_to_nodes([del_wrapper])
            return elem

        else:
            raise ValueError(f"元素必须是 w:r 或 w:p，得到的是 {elem.nodeName}")


def _generate_hex_id() -> str:
    return f"{random.randint(1, 0x7FFFFFFE):08X}"


def _generate_rsid() -> str:
    return "".join(random.choices("0123456789ABCDEF", k=8))


def _get_local_timestamp() -> str:
    now = datetime.now().astimezone()
    offset = now.strftime("%z")
    offset_formatted = f"{offset[:3]}:{offset[3:]}"
    return now.strftime("%Y-%m-%dT%H:%M:%S") + offset_formatted


class Document:
    """管理解压后的 Word 文档中的批注和修订追踪。"""

    def __init__(
        self,
        unpacked_dir,
        rsid=None,
        track_revisions=False,
        author="checking-patdocx-cn-single-agent",
        initials="PC",
    ):
        self.original_path = Path(unpacked_dir)

        if not self.original_path.exists() or not self.original_path.is_dir():
            raise ValueError(f"目录未找到: {unpacked_dir}")

        self.temp_dir = tempfile.mkdtemp(prefix="docx_")
        self.unpacked_path = Path(self.temp_dir) / "unpacked"
        shutil.copytree(self.original_path, self.unpacked_path)

        self.original_docx = Path(self.temp_dir) / "original.docx"
        from ooxml.scripts.pack import pack_document
        pack_document(self.original_path, self.original_docx, validate=False)

        self.word_path = self.unpacked_path / "word"

        self.rsid = rsid if rsid else _generate_rsid()
        print(f"使用 RSID: {self.rsid}")

        self.author = author
        self.initials = initials

        self._editors = {}

        self.comments_path = self.word_path / "comments.xml"
        self.comments_extended_path = self.word_path / "commentsExtended.xml"
        self.comments_ids_path = self.word_path / "commentsIds.xml"
        self.comments_extensible_path = self.word_path / "commentsExtensible.xml"

        self.existing_comments = self._load_existing_comments()
        self.next_comment_id = self._get_next_comment_id()

        self._document = self["word/document.xml"]

        self._setup_tracking(track_revisions=track_revisions)

        self._add_author_to_people(author)

    def __getitem__(self, xml_path: str) -> DocxXMLEditor:
        if xml_path not in self._editors:
            file_path = self.unpacked_path / xml_path
            if not file_path.exists():
                raise ValueError(f"XML 文件未找到: {xml_path}")
            self._editors[xml_path] = DocxXMLEditor(
                file_path, rsid=self.rsid, author=self.author, initials=self.initials
            )
        return self._editors[xml_path]

    def add_comment(self, start, end, text: str) -> int:
        comment_id = self.next_comment_id
        para_id = _generate_hex_id()
        durable_id = _generate_hex_id()
        timestamp = _get_local_timestamp()

        self._document.insert_before(start, self._comment_range_start_xml(comment_id))

        if end.tagName == "w:p":
            self._document.append_to(end, self._comment_range_end_xml(comment_id))
        else:
            self._document.insert_after(end, self._comment_range_end_xml(comment_id))

        self._add_to_comments_xml(
            comment_id, para_id, text, self.author, self.initials, timestamp
        )
        self._add_to_comments_extended_xml(para_id, parent_para_id=None)
        self._add_to_comments_ids_xml(para_id, durable_id)
        self._add_to_comments_extensible_xml(durable_id)

        self.existing_comments[comment_id] = {"para_id": para_id}
        self.next_comment_id += 1
        return comment_id

    def reply_to_comment(
        self,
        parent_comment_id: int,
        text: str,
    ) -> int:
        if parent_comment_id not in self.existing_comments:
            raise ValueError(f"未找到 id={parent_comment_id} 的父批注")

        parent_info = self.existing_comments[parent_comment_id]
        comment_id = self.next_comment_id
        para_id = _generate_hex_id()
        durable_id = _generate_hex_id()
        timestamp = _get_local_timestamp()

        parent_start_elem = self._document.get_node(
            tag="w:commentRangeStart", attrs={"w:id": str(parent_comment_id)}
        )
        parent_ref_elem = self._document.get_node(
            tag="w:commentReference", attrs={"w:id": str(parent_comment_id)}
        )

        self._document.insert_after(
            parent_start_elem, self._comment_range_start_xml(comment_id)
        )
        parent_ref_run = parent_ref_elem.parentNode
        self._document.insert_after(
            parent_ref_run, f'<w:commentRangeEnd w:id="{comment_id}"/>'
        )
        self._document.insert_after(
            parent_ref_run, self._comment_ref_run_xml(comment_id)
        )

        self._add_to_comments_xml(
            comment_id, para_id, text, self.author, self.initials, timestamp
        )
        self._add_to_comments_extended_xml(
            para_id, parent_para_id=parent_info["para_id"]
        )
        self._add_to_comments_ids_xml(para_id, durable_id)
        self._add_to_comments_extensible_xml(durable_id)

        self.existing_comments[comment_id] = {"para_id": para_id}
        self.next_comment_id += 1
        return comment_id

    def __del__(self):
        if hasattr(self, "temp_dir") and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def save(self, destination=None, validate=False):
        if self.comments_path.exists():
            self._ensure_comment_relationships()
            self._ensure_comment_content_types()

        for editor in self._editors.values():
            editor.save()

        if validate:
            try:
                from ooxml.scripts.validation.docx import DOCXSchemaValidator
                from ooxml.scripts.validation.redlining import RedliningValidator

                schema_validator = DOCXSchemaValidator(
                    self.unpacked_path, self.original_docx, verbose=False
                )
                redlining_validator = RedliningValidator(
                    self.unpacked_path, self.original_docx, verbose=False
                )

                if not schema_validator.validate():
                    print("警告：架构验证失败")
                if not redlining_validator.validate():
                    print("警告：红线验证失败")
            except Exception as e:
                print(f"警告：验证时出错: {e}")

        target_path = Path(destination) if destination else self.original_path
        shutil.copytree(self.unpacked_path, target_path, dirs_exist_ok=True)

    def _get_next_comment_id(self):
        if not self.comments_path.exists():
            return 0

        editor = self["word/comments.xml"]
        max_id = -1
        for comment_elem in editor.dom.getElementsByTagName("w:comment"):
            comment_id = comment_elem.getAttribute("w:id")
            if comment_id:
                try:
                    max_id = max(max_id, int(comment_id))
                except ValueError:
                    pass
        return max_id + 1

    def _load_existing_comments(self):
        if not self.comments_path.exists():
            return {}

        editor = self["word/comments.xml"]
        existing = {}

        for comment_elem in editor.dom.getElementsByTagName("w:comment"):
            comment_id = comment_elem.getAttribute("w:id")
            if not comment_id:
                continue

            para_id = None
            for p_elem in comment_elem.getElementsByTagName("w:p"):
                para_id = p_elem.getAttribute("w14:paraId")
                if para_id:
                    break

            if not para_id:
                continue

            existing[int(comment_id)] = {"para_id": para_id}

        return existing

    def _setup_tracking(self, track_revisions=False):
        people_file = self.word_path / "people.xml"
        self._update_people_xml(people_file)

        self._add_content_type_for_people(self.unpacked_path / "[Content_Types].xml")
        self._add_relationship_for_people(
            self.word_path / "_rels" / "document.xml.rels"
        )

        self._update_settings(
            self.word_path / "settings.xml", track_revisions=track_revisions
        )

    def _update_people_xml(self, path):
        if not path.exists():
            shutil.copy(TEMPLATE_DIR / "people.xml", path)

    def _add_content_type_for_people(self, path):
        editor = self["[Content_Types].xml"]

        if self._has_override(editor, "/word/people.xml"):
            return

        root = editor.dom.documentElement
        override_xml = '<Override PartName="/word/people.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.people+xml"/>'
        editor.append_to(root, override_xml)

    def _add_relationship_for_people(self, path):
        editor = self["word/_rels/document.xml.rels"]

        if self._has_relationship(editor, "people.xml"):
            return

        root = editor.dom.documentElement
        root_tag = root.tagName
        prefix = root_tag.split(":")[0] + ":" if ":" in root_tag else ""
        next_rid = editor.get_next_rid()

        rel_xml = f'<{prefix}Relationship Id="{next_rid}" Type="http://schemas.microsoft.com/office/2011/relationships/people" Target="people.xml"/>'
        editor.append_to(root, rel_xml)

    def _update_settings(self, path, track_revisions=False):
        editor = self["word/settings.xml"]
        root = editor.get_node(tag="w:settings")
        prefix = root.tagName.split(":")[0] if ":" in root.tagName else "w"

        if track_revisions:
            track_revisions_exists = any(
                elem.tagName == f"{prefix}:trackRevisions"
                for elem in editor.dom.getElementsByTagName(f"{prefix}:trackRevisions")
            )

            if not track_revisions_exists:
                track_rev_xml = f"<{prefix}:trackRevisions/>"
                inserted = False
                for tag in [f"{prefix}:documentProtection", f"{prefix}:defaultTabStop"]:
                    elements = editor.dom.getElementsByTagName(tag)
                    if elements:
                        editor.insert_before(elements[0], track_rev_xml)
                        inserted = True
                        break
                if not inserted:
                    if root.firstChild:
                        editor.insert_before(root.firstChild, track_rev_xml)
                    else:
                        editor.append_to(root, track_rev_xml)

        rsids_elements = editor.dom.getElementsByTagName(f"{prefix}:rsids")

        if not rsids_elements:
            rsids_xml = f'''<{prefix}:rsids>
  <{prefix}:rsidRoot {prefix}:val="{self.rsid}"/>
  <{prefix}:rsid {prefix}:val="{self.rsid}"/>
</{prefix}:rsids>'''

            inserted = False
            compat_elements = editor.dom.getElementsByTagName(f"{prefix}:compat")
            if compat_elements:
                editor.insert_after(compat_elements[0], rsids_xml)
                inserted = True

            if not inserted:
                clr_elements = editor.dom.getElementsByTagName(
                    f"{prefix}:clrSchemeMapping"
                )
                if clr_elements:
                    editor.insert_before(clr_elements[0], rsids_xml)
                    inserted = True

            if not inserted:
                editor.append_to(root, rsids_xml)
        else:
            rsids_elem = rsids_elements[0]
            rsid_exists = any(
                elem.getAttribute(f"{prefix}:val") == self.rsid
                for elem in rsids_elem.getElementsByTagName(f"{prefix}:rsid")
            )

            if not rsid_exists:
                rsid_xml = f'<{prefix}:rsid {prefix}:val="{self.rsid}"/>'
                editor.append_to(rsids_elem, rsid_xml)

    def _add_to_comments_xml(
        self, comment_id, para_id, text, author, initials, timestamp
    ):
        if not self.comments_path.exists():
            shutil.copy(TEMPLATE_DIR / "comments.xml", self.comments_path)

        editor = self["word/comments.xml"]
        root = editor.get_node(tag="w:comments")

        lines = text.split("\n")
        run_xml_parts = []
        for idx, line in enumerate(lines):
            escaped_line = (
                line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            )
            if idx > 0:
                run_xml_parts.append('<w:r><w:br/></w:r>')
            run_xml_parts.append(
                f'<w:r><w:rPr><w:color w:val="000000"/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr><w:t>{escaped_line}</w:t></w:r>'
            )
        runs_xml = "\n    ".join(run_xml_parts)

        comment_xml = f'''<w:comment w:id="{comment_id}">
  <w:p w14:paraId="{para_id}" w14:textId="77777777">
    <w:r><w:rPr><w:rStyle w:val="CommentReference"/></w:rPr><w:annotationRef/></w:r>
    {runs_xml}
  </w:p>
</w:comment>'''
        editor.append_to(root, comment_xml)

    def _add_to_comments_extended_xml(self, para_id, parent_para_id):
        if not self.comments_extended_path.exists():
            shutil.copy(
                TEMPLATE_DIR / "commentsExtended.xml", self.comments_extended_path
            )

        editor = self["word/commentsExtended.xml"]
        root = editor.get_node(tag="w15:commentsEx")

        if parent_para_id:
            xml = f'<w15:commentEx w15:paraId="{para_id}" w15:paraIdParent="{parent_para_id}" w15:done="0"/>'
        else:
            xml = f'<w15:commentEx w15:paraId="{para_id}" w15:done="0"/>'
        editor.append_to(root, xml)

    def _add_to_comments_ids_xml(self, para_id, durable_id):
        if not self.comments_ids_path.exists():
            shutil.copy(TEMPLATE_DIR / "commentsIds.xml", self.comments_ids_path)

        editor = self["word/commentsIds.xml"]
        root = editor.get_node(tag="w16cid:commentsIds")

        xml = f'<w16cid:commentId w16cid:paraId="{para_id}" w16cid:durableId="{durable_id}"/>'
        editor.append_to(root, xml)

    def _add_to_comments_extensible_xml(self, durable_id):
        if not self.comments_extensible_path.exists():
            shutil.copy(
                TEMPLATE_DIR / "commentsExtensible.xml", self.comments_extensible_path
            )

        editor = self["word/commentsExtensible.xml"]
        root = editor.get_node(tag="w16cex:commentsExtensible")

        xml = f'<w16cex:commentExtensible w16cex:durableId="{durable_id}"/>'
        editor.append_to(root, xml)

    def _comment_range_start_xml(self, comment_id):
        return f'<w:commentRangeStart w:id="{comment_id}"/>'

    def _comment_range_end_xml(self, comment_id):
        return f'''<w:commentRangeEnd w:id="{comment_id}"/>
<w:r>
  <w:rPr><w:rStyle w:val="CommentReference"/></w:rPr>
  <w:commentReference w:id="{comment_id}"/>
</w:r>'''

    def _comment_ref_run_xml(self, comment_id):
        return f'''<w:r>
  <w:rPr><w:rStyle w:val="CommentReference"/></w:rPr>
  <w:commentReference w:id="{comment_id}"/>
</w:r>'''

    def _has_relationship(self, editor, target):
        for rel_elem in editor.dom.getElementsByTagName("Relationship"):
            if rel_elem.getAttribute("Target") == target:
                return True
        return False

    def _has_override(self, editor, part_name):
        for override_elem in editor.dom.getElementsByTagName("Override"):
            if override_elem.getAttribute("PartName") == part_name:
                return True
        return False

    def _has_author(self, editor, author):
        for person_elem in editor.dom.getElementsByTagName("w15:person"):
            if person_elem.getAttribute("w15:author") == author:
                return True
        return False

    def _add_author_to_people(self, author):
        people_path = self.word_path / "people.xml"

        if not people_path.exists():
            raise ValueError("people.xml 应该在 _setup_tracking 之后存在")

        editor = self["word/people.xml"]
        root = editor.get_node(tag="w15:people")

        if self._has_author(editor, author):
            return

        escaped_author = html.escape(author, quote=True)
        person_xml = f'''<w15:person w15:author="{escaped_author}">
  <w15:presenceInfo w15:providerId="None" w15:userId="{escaped_author}"/>
</w15:person>'''
        editor.append_to(root, person_xml)

    def _ensure_comment_relationships(self):
        editor = self["word/_rels/document.xml.rels"]

        if self._has_relationship(editor, "comments.xml"):
            return

        root = editor.dom.documentElement
        root_tag = root.tagName
        prefix = root_tag.split(":")[0] + ":" if ":" in root_tag else ""
        next_rid_num = int(editor.get_next_rid()[3:])

        rels = [
            (
                next_rid_num,
                "http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments",
                "comments.xml",
            ),
            (
                next_rid_num + 1,
                "http://schemas.microsoft.com/office/2011/relationships/commentsExtended",
                "commentsExtended.xml",
            ),
            (
                next_rid_num + 2,
                "http://schemas.microsoft.com/office/2016/09/relationships/commentsIds",
                "commentsIds.xml",
            ),
            (
                next_rid_num + 3,
                "http://schemas.microsoft.com/office/2018/08/relationships/commentsExtensible",
                "commentsExtensible.xml",
            ),
        ]

        for rel_id, rel_type, target in rels:
            rel_xml = f'<{prefix}Relationship Id="rId{rel_id}" Type="{rel_type}" Target="{target}"/>'
            editor.append_to(root, rel_xml)

    def _ensure_comment_content_types(self):
        editor = self["[Content_Types].xml"]

        if self._has_override(editor, "/word/comments.xml"):
            return

        root = editor.dom.documentElement

        overrides = [
            (
                "/word/comments.xml",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml",
            ),
            (
                "/word/commentsExtended.xml",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.commentsExtended+xml",
            ),
            (
                "/word/commentsIds.xml",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.commentsIds+xml",
            ),
            (
                "/word/commentsExtensible.xml",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.commentsExtensible+xml",
            ),
        ]

        for part_name, content_type in overrides:
            override_xml = (
                f'<Override PartName="{part_name}" ContentType="{content_type}"/>'
            )
            editor.append_to(root, override_xml)
