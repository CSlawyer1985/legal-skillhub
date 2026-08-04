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

# html 模块用于转义 HTML 特殊字符
import html
# random 用于生成随机数
import random
# shutil 用于文件和目录的复制、删除等操作
import shutil
# tempfile 用于创建临时目录
import tempfile
# datetime 用于处理日期和时间
from datetime import datetime, timezone
# Path 用于面向对象的文件路径处理
from pathlib import Path

# defusedxml 是安全的 XML 解析库，minidom 提供 DOM 操作接口
from defusedxml import minidom

# 从同级目录的 utilities 模块导入 XMLEditor 类
from .utilities import XMLEditor

# 模板目录路径，位于当前脚本所在目录的 templates 文件夹下
TEMPLATE_DIR = Path(__file__).parent / "templates"


class DocxXMLEditor(XMLEditor):
    """
    自动将 RSID、作者和日期应用到新元素的 XMLEditor。
    继承自 XMLEditor，添加了 Word 文档特有的属性注入功能。
    """

    def __init__(
        self, xml_path, rsid: str, author: str = "checking-cn-patent-format", initials: str = "MA"
    ):
        # 调用父类构造函数，初始化 XML 编辑器
        super().__init__(xml_path)
        # RSID 是 Word 用于标识修订来源的随机字符串
        self.rsid = rsid
        # 作者名称，用于批注和修订追踪
        self.author = author
        # 作者缩写，用于批注显示
        self.initials = initials

    def _get_next_change_id(self):
        """
        获取下一个修订追踪的 ID 号。
        Word 使用 w:id 属性来唯一标识每个修订（插入/删除）。
        """
        max_id = -1
        # 遍历所有插入（w:ins）和删除（w:del）元素
        for tag in ("w:ins", "w:del"):
            elements = self.dom.getElementsByTagName(tag)
            for elem in elements:
                change_id = elem.getAttribute("w:id")
                if change_id:
                    try:
                        # 更新最大 ID
                        max_id = max(max_id, int(change_id))
                    except ValueError:
                        pass
        # 返回下一个可用 ID
        return max_id + 1

    def _ensure_w16du_namespace(self):
        """
        确保 XML 根元素包含 w16du 命名空间声明。
        w16du 是 Word 用于存储 UTC 时间戳的扩展命名空间。
        """
        root = self.dom.documentElement
        if not root.hasAttribute("xmlns:w16du"):
            root.setAttribute(
                "xmlns:w16du",
                "http://schemas.microsoft.com/office/word/2023/wordml/word16du",
            )

    def _ensure_w16cex_namespace(self):
        """
        确保 XML 根元素包含 w16cex 命名空间声明。
        w16cex 是 Word 用于可扩展批注的命名空间。
        """
        root = self.dom.documentElement
        if not root.hasAttribute("xmlns:w16cex"):
            root.setAttribute(
                "xmlns:w16cex",
                "http://schemas.microsoft.com/office/word/2018/wordml/cex",
            )

    def _ensure_w14_namespace(self):
        """
        确保 XML 根元素包含 w14 命名空间声明。
        w14 是 Word 2010 引入的扩展命名空间，用于段落 ID 等功能。
        """
        root = self.dom.documentElement
        if not root.hasAttribute("xmlns:w14"):
            root.setAttribute(
                "xmlns:w14",
                "http://schemas.microsoft.com/office/word/2010/wordml",
            )

    def _inject_attributes_to_nodes(self, nodes):
        """
        为新创建的节点注入 Word 所需的属性（RSID、作者、日期等）。
        这是确保 Word 能正确显示修订和批注的关键步骤。
        """
        # 获取当前本地时间戳
        timestamp = _get_local_timestamp()

        # 判断元素是否在删除标记内部
        def is_inside_deletion(elem):
            parent = elem.parentNode
            while parent:
                if parent.nodeType == parent.ELEMENT_NODE and parent.tagName == "w:del":
                    return True
                parent = parent.parentNode
            return False

        # 为段落（w:p）元素添加 RSID 和段落 ID 属性
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

        # 为文本运行（w:r）元素添加 RSID 属性
        def add_rsid_to_r(elem):
            if is_inside_deletion(elem):
                if not elem.hasAttribute("w:rsidDel"):
                    elem.setAttribute("w:rsidDel", self.rsid)
            else:
                if not elem.hasAttribute("w:rsidR"):
                    elem.setAttribute("w:rsidR", self.rsid)

        # 为修订追踪元素（w:ins, w:del）添加 ID、作者、日期属性
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

        # 为批注元素添加作者、日期、缩写属性
        def add_comment_attrs(elem):
            if not elem.hasAttribute("w:author"):
                elem.setAttribute("w:author", self.author)
            if not elem.hasAttribute("w:date"):
                elem.setAttribute("w:date", timestamp)
            if not elem.hasAttribute("w:initials"):
                elem.setAttribute("w:initials", self.initials)

        # 为可扩展批注元素添加 UTC 日期
        def add_comment_extensible_date(elem):
            if not elem.hasAttribute("w16cex:dateUtc"):
                self._ensure_w16cex_namespace()
                elem.setAttribute("w16cex:dateUtc", timestamp)

        # 为文本元素（w:t）添加 xml:space="preserve" 属性（如果文本包含首尾空格）
        def add_xml_space_to_t(elem):
            if (
                elem.firstChild
                and elem.firstChild.nodeType == elem.firstChild.TEXT_NODE
            ):
                text = elem.firstChild.data
                if text and (text[0].isspace() or text[-1].isspace()):
                    if not elem.hasAttribute("xml:space"):
                        elem.setAttribute("xml:space", "preserve")

        # 遍历所有传入的节点，根据节点类型应用不同的属性注入
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

            # 同时处理节点内部的所有子元素
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

    # 重写父类的节点操作方法，在操作后自动注入属性
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
        """
        建议删除指定元素，将其包装在修订追踪的删除标记中。
        支持 w:r（文本运行）和 w:p（段落）两种元素。
        """
        if elem.nodeName == "w:r":
            # 如果元素已包含删除文本，抛出错误
            if elem.getElementsByTagName("w:delText"):
                raise ValueError("w:r 元素已包含 w:delText")

            # 将 w:t 元素替换为 w:delText 元素（表示删除的文本）
            for t_elem in list(elem.getElementsByTagName("w:t")):
                del_text = self.dom.createElement("w:delText")
                while t_elem.firstChild:
                    del_text.appendChild(t_elem.firstChild)
                for i in range(t_elem.attributes.length):
                    attr = t_elem.attributes.item(i)
                    del_text.setAttribute(attr.name, attr.value)
                t_elem.parentNode.replaceChild(del_text, t_elem)

            # 更新 RSID 属性，将 w:rsidR 改为 w:rsidDel
            if elem.hasAttribute("w:rsidR"):
                elem.setAttribute("w:rsidDel", elem.getAttribute("w:rsidR"))
                elem.removeAttribute("w:rsidR")
            elif not elem.hasAttribute("w:rsidDel"):
                elem.setAttribute("w:rsidDel", self.rsid)

            # 创建删除标记（w:del）并将元素包装其中
            del_wrapper = self.dom.createElement("w:del")
            parent = elem.parentNode
            parent.insertBefore(del_wrapper, elem)
            parent.removeChild(elem)
            del_wrapper.appendChild(elem)

            # 注入修订追踪所需的属性
            self._inject_attributes_to_nodes([del_wrapper])
            return del_wrapper

        elif elem.nodeName == "w:p":
            # 段落级别的删除处理
            if elem.getElementsByTagName("w:ins") or elem.getElementsByTagName("w:del"):
                raise ValueError("w:p 元素已包含修订追踪")

            # 检查段落是否是编号列表项
            pPr_list = elem.getElementsByTagName("w:pPr")
            is_numbered = pPr_list and pPr_list[0].getElementsByTagName("w:numPr")

            if is_numbered:
                # 对于编号段落，在段落属性中添加删除标记
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

            # 将段落内所有 w:t 替换为 w:delText
            for t_elem in list(elem.getElementsByTagName("w:t")):
                del_text = self.dom.createElement("w:delText")
                while t_elem.firstChild:
                    del_text.appendChild(t_elem.firstChild)
                for i in range(t_elem.attributes.length):
                    attr = t_elem.attributes.item(i)
                    del_text.setAttribute(attr.name, attr.value)
                t_elem.parentNode.replaceChild(del_text, t_elem)

            # 更新所有文本运行的 RSID 属性
            for run in elem.getElementsByTagName("w:r"):
                if run.hasAttribute("w:rsidR"):
                    run.setAttribute("w:rsidDel", run.getAttribute("w:rsidR"))
                    run.removeAttribute("w:rsidR")
                elif not run.hasAttribute("w:rsidDel"):
                    run.setAttribute("w:rsidDel", self.rsid)

            # 创建删除包装器，将段落内容移入其中
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
    """生成一个随机的十六进制 ID（8位大写），用于段落标识。"""
    return f"{random.randint(1, 0x7FFFFFFE):08X}"


def _generate_rsid() -> str:
    """生成一个随机的 RSID（8位十六进制字符串），用于标识修订来源。"""
    return "".join(random.choices("0123456789ABCDEF", k=8))


def _get_local_timestamp() -> str:
    """
    获取当前本地时间戳，格式为 ISO 8601（含时区偏移）。
    例如：2024-01-15T09:30:00+08:00
    """
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
        author="checking-cn-patent-format",
        initials="MA",
    ):
        # 保存原始解压目录路径
        self.original_path = Path(unpacked_dir)

        # 检查目录是否存在
        if not self.original_path.exists() or not self.original_path.is_dir():
            raise ValueError(f"目录未找到: {unpacked_dir}")

        # 创建临时目录，用于存放工作副本
        self.temp_dir = tempfile.mkdtemp(prefix="docx_")
        self.unpacked_path = Path(self.temp_dir) / "unpacked"
        # 将原始目录复制到临时目录，避免修改原始文件
        shutil.copytree(self.original_path, self.unpacked_path)

        # 打包原始目录为一个参考用的 docx 文件
        self.original_docx = Path(self.temp_dir) / "original.docx"
        from ooxml.scripts.pack import pack_document
        pack_document(self.original_path, self.original_docx, validate=False)

        # Word 文档的主要内容目录
        self.word_path = self.unpacked_path / "word"

        # 生成或使用传入的 RSID
        self.rsid = rsid if rsid else _generate_rsid()
        print(f"使用 RSID: {self.rsid}")

        # 保存作者信息
        self.author = author
        self.initials = initials

        # 缓存已创建的 XML 编辑器实例
        self._editors = {}

        # 记录包含批注的非正文XML文件（如页眉），保存时需确保其关系文件正确
        self._commented_files = set()

        # 批注相关文件路径
        self.comments_path = self.word_path / "comments.xml"
        self.comments_extended_path = self.word_path / "commentsExtended.xml"
        self.comments_ids_path = self.word_path / "commentsIds.xml"
        self.comments_extensible_path = self.word_path / "commentsExtensible.xml"

        # 加载已存在的批注信息
        self.existing_comments = self._load_existing_comments()
        # 获取下一个可用的批注 ID
        self.next_comment_id = self._get_next_comment_id()

        # 初始化主文档编辑器
        self._document = self["word/document.xml"]

        # 设置修订追踪和人员信息
        self._setup_tracking(track_revisions=track_revisions)

        # 将当前作者添加到人员列表
        self._add_author_to_people(author)

    def __getitem__(self, xml_path: str) -> DocxXMLEditor:
        """
        通过路径获取 XML 编辑器实例（支持缓存）。
        用法: doc["word/document.xml"]
        """
        if xml_path not in self._editors:
            file_path = self.unpacked_path / xml_path
            if not file_path.exists():
                raise ValueError(f"XML 文件未找到: {xml_path}")
            self._editors[xml_path] = DocxXMLEditor(
                file_path, rsid=self.rsid, author=self.author, initials=self.initials
            )
        return self._editors[xml_path]

    def add_comment(self, start, end, text: str) -> int:
        """
        在文档中添加批注。

        Args:
            start: 批注范围的起始节点
            end: 批注范围的结束节点
            text: 批注文本内容

        Returns:
            新创建批注的 ID
        """
        comment_id = self.next_comment_id
        para_id = _generate_hex_id()
        durable_id = _generate_hex_id()
        timestamp = _get_local_timestamp()

        # 在起始位置前插入批注范围开始标记
        self._document.insert_before(start, self._comment_range_start_xml(comment_id))

        # 在结束位置后插入批注范围结束标记和批注引用
        if end.tagName == "w:p":
            self._document.append_to(end, self._comment_range_end_xml(comment_id))
        else:
            self._document.insert_after(end, self._comment_range_end_xml(comment_id))

        # 将批注内容添加到各个批注相关 XML 文件中
        self._add_to_comments_xml(
            comment_id, para_id, text, self.author, self.initials, timestamp
        )
        self._add_to_comments_extended_xml(para_id, parent_para_id=None)
        self._add_to_comments_ids_xml(para_id, durable_id)
        self._add_to_comments_extensible_xml(durable_id)

        # 记录批注信息并递增 ID
        self.existing_comments[comment_id] = {"para_id": para_id}
        self.next_comment_id += 1
        return comment_id

    def add_comment_in_file(self, xml_path, start, end, text: str) -> int:
        """
        在指定XML文件（如页眉header）中添加批注。

        与add_comment类似，但批注范围标记插入到指定的XML文件中，
        而非默认的document.xml。适用于页眉、页脚等非正文区域的批注。

        Args:
            xml_path: XML文件相对路径（如"word/header1.xml"）
            start: 批注范围的起始节点
            end: 批注范围的结束节点
            text: 批注文本内容

        Returns:
            新创建批注的 ID
        """
        comment_id = self.next_comment_id
        para_id = _generate_hex_id()
        durable_id = _generate_hex_id()
        timestamp = _get_local_timestamp()

        editor = self[xml_path]

        editor.insert_before(start, self._comment_range_start_xml(comment_id))

        if end.tagName == "w:p":
            editor.append_to(end, self._comment_range_end_xml(comment_id))
        else:
            editor.insert_after(end, self._comment_range_end_xml(comment_id))

        self._add_to_comments_xml(
            comment_id, para_id, text, self.author, self.initials, timestamp
        )
        self._add_to_comments_extended_xml(para_id, parent_para_id=None)
        self._add_to_comments_ids_xml(para_id, durable_id)
        self._add_to_comments_extensible_xml(durable_id)

        self._commented_files.add(xml_path)

        self.existing_comments[comment_id] = {"para_id": para_id}
        self.next_comment_id += 1
        return comment_id

    def reply_to_comment(
        self,
        parent_comment_id: int,
        text: str,
    ) -> int:
        """
        对已有批注添加回复。

        Args:
            parent_comment_id: 父批注的 ID
            text: 回复文本内容

        Returns:
            新创建回复批注的 ID
        """
        if parent_comment_id not in self.existing_comments:
            raise ValueError(f"未找到 id={parent_comment_id} 的父批注")

        parent_info = self.existing_comments[parent_comment_id]
        comment_id = self.next_comment_id
        para_id = _generate_hex_id()
        durable_id = _generate_hex_id()
        timestamp = _get_local_timestamp()

        # 查找父批注的起始和引用元素
        parent_start_elem = self._document.get_node(
            tag="w:commentRangeStart", attrs={"w:id": str(parent_comment_id)}
        )
        parent_ref_elem = self._document.get_node(
            tag="w:commentReference", attrs={"w:id": str(parent_comment_id)}
        )

        # 在父批注范围内插入回复批注的范围标记
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

        # 添加回复批注到各个 XML 文件
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
        """析构函数：清理临时目录。"""
        if hasattr(self, "temp_dir") and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def save(self, destination=None, validate=False):
        """
        保存文档修改到目标位置。

        Args:
            destination: 目标目录路径，默认覆盖原始目录
            validate: 是否进行架构验证
        """
        # 如果存在批注文件，确保关系和内容类型正确
        if self.comments_path.exists():
            self._ensure_comment_relationships()
            self._ensure_comment_content_types()
            for xml_path in self._commented_files:
                self._ensure_comment_relationships_for_file(xml_path)

        # 保存所有已编辑的 XML 文件
        for editor in self._editors.values():
            editor.save()

        # 如果启用验证，执行架构和红线验证
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

        # 将修改后的文件复制到目标位置
        target_path = Path(destination) if destination else self.original_path
        shutil.copytree(self.unpacked_path, target_path, dirs_exist_ok=True)

    def _get_next_comment_id(self):
        """获取下一个可用的批注 ID。"""
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
        """加载已存在的批注信息，返回批注 ID 到段落 ID 的映射。"""
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
        """设置修订追踪和人员信息。"""
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
        """如果 people.xml 不存在，从模板复制一份。"""
        if not path.exists():
            shutil.copy(TEMPLATE_DIR / "people.xml", path)

    def _add_content_type_for_people(self, path):
        """在 [Content_Types].xml 中添加 people.xml 的内容类型声明。"""
        editor = self["[Content_Types].xml"]

        if self._has_override(editor, "/word/people.xml"):
            return

        root = editor.dom.documentElement
        override_xml = '<Override PartName="/word/people.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.people+xml"/>'
        editor.append_to(root, override_xml)

    def _add_relationship_for_people(self, path):
        """在 document.xml.rels 中添加 people.xml 的关系声明。"""
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
        """更新文档设置，包括修订追踪和 RSID 列表。"""
        editor = self["word/settings.xml"]
        root = editor.get_node(tag="w:settings")
        prefix = root.tagName.split(":")[0] if ":" in root.tagName else "w"

        # 如果启用修订追踪，添加 trackRevisions 元素
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

        # 添加或更新 RSID 列表
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
        """将批注内容添加到 comments.xml 文件。"""
        if not self.comments_path.exists():
            shutil.copy(TEMPLATE_DIR / "comments.xml", self.comments_path)

        editor = self["word/comments.xml"]
        root = editor.get_node(tag="w:comments")

        # 将文本按行分割，每行生成一个文本运行
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
        """将批注扩展信息添加到 commentsExtended.xml 文件。"""
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
        """将批注 ID 映射添加到 commentsIds.xml 文件。"""
        if not self.comments_ids_path.exists():
            shutil.copy(TEMPLATE_DIR / "commentsIds.xml", self.comments_ids_path)

        editor = self["word/commentsIds.xml"]
        root = editor.get_node(tag="w16cid:commentsIds")

        xml = f'<w16cid:commentId w16cid:paraId="{para_id}" w16cid:durableId="{durable_id}"/>'
        editor.append_to(root, xml)

    def _add_to_comments_extensible_xml(self, durable_id):
        """将可扩展批注信息添加到 commentsExtensible.xml 文件。"""
        if not self.comments_extensible_path.exists():
            shutil.copy(
                TEMPLATE_DIR / "commentsExtensible.xml", self.comments_extensible_path
            )

        editor = self["word/commentsExtensible.xml"]
        root = editor.get_node(tag="w16cex:commentsExtensible")

        xml = f'<w16cex:commentExtensible w16cex:durableId="{durable_id}"/>'
        editor.append_to(root, xml)

    def _comment_range_start_xml(self, comment_id):
        """生成批注范围开始标记的 XML 字符串。"""
        return f'<w:commentRangeStart w:id="{comment_id}"/>'

    def _comment_range_end_xml(self, comment_id):
        """生成批注范围结束标记和批注引用的 XML 字符串。"""
        return f'''<w:commentRangeEnd w:id="{comment_id}"/>
<w:r>
  <w:rPr><w:rStyle w:val="CommentReference"/></w:rPr>
  <w:commentReference w:id="{comment_id}"/>
</w:r>'''

    def _comment_ref_run_xml(self, comment_id):
        """生成批注引用运行的 XML 字符串。"""
        return f'''<w:r>
  <w:rPr><w:rStyle w:val="CommentReference"/></w:rPr>
  <w:commentReference w:id="{comment_id}"/>
</w:r>'''

    def _has_relationship(self, editor, target):
        """检查关系文件中是否已存在指向指定目标的关系。"""
        for rel_elem in editor.dom.getElementsByTagName("Relationship"):
            if rel_elem.getAttribute("Target") == target:
                return True
        return False

    def _has_override(self, editor, part_name):
        """检查 [Content_Types].xml 中是否已存在指定部件的覆盖声明。"""
        for override_elem in editor.dom.getElementsByTagName("Override"):
            if override_elem.getAttribute("PartName") == part_name:
                return True
        return False

    def _has_author(self, editor, author):
        """检查 people.xml 中是否已存在指定作者。"""
        for person_elem in editor.dom.getElementsByTagName("w15:person"):
            if person_elem.getAttribute("w15:author") == author:
                return True
        return False

    def _add_author_to_people(self, author):
        """将作者添加到 people.xml 文件中。"""
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
        """确保 document.xml.rels 中包含所有批注相关文件的关系声明。"""
        editor = self["word/_rels/document.xml.rels"]

        if self._has_relationship(editor, "comments.xml"):
            return

        root = editor.dom.documentElement
        root_tag = root.tagName
        prefix = root_tag.split(":")[0] + ":" if ":" in root_tag else ""
        next_rid_num = int(editor.get_next_rid()[3:])

        # 定义所有批注相关文件的关系
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

    def _ensure_comment_relationships_for_file(self, xml_path):
        """
        确保指定XML文件的关系文件中包含所有批注相关文件的关系声明。

        对于页眉等非document.xml的XML文件，需要在其自己的.rels文件中
        添加对comments.xml等批注文件的关系声明，否则Word无法正确显示
        该文件中的批注。
        """
        xml_path_obj = Path(xml_path)
        rels_dir = str(xml_path_obj.parent / "_rels")
        rels_filename = f"{xml_path_obj.stem}.xml.rels"
        rels_path = f"{rels_dir}/{rels_filename}"

        rels_full_path = self.unpacked_path / rels_path

        if not rels_full_path.exists():
            rels_full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(rels_full_path, "w", encoding="utf-8") as f:
                f.write(
                    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                    "</Relationships>"
                )

        editor = self[rels_path]

        comment_targets = [
            (
                "comments.xml",
                "http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments",
            ),
            (
                "commentsExtended.xml",
                "http://schemas.microsoft.com/office/2011/relationships/commentsExtended",
            ),
            (
                "commentsIds.xml",
                "http://schemas.microsoft.com/office/2016/09/relationships/commentsIds",
            ),
            (
                "commentsExtensible.xml",
                "http://schemas.microsoft.com/office/2018/08/relationships/commentsExtensible",
            ),
        ]

        for target, rel_type in comment_targets:
            if not (self.unpacked_path / "word" / target).exists():
                continue
            if not self._has_relationship(editor, target):
                root = editor.dom.documentElement
                root_tag = root.tagName
                prefix = (
                    root_tag.split(":")[0] + ":" if ":" in root_tag else ""
                )
                next_rid = editor.get_next_rid()
                rel_xml = (
                    f'<{prefix}Relationship Id="{next_rid}" '
                    f'Type="{rel_type}" Target="{target}"/>'
                )
                editor.append_to(root, rel_xml)

    def _ensure_comment_content_types(self):
        """确保 [Content_Types].xml 中包含所有批注相关文件的内容类型声明。"""
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
