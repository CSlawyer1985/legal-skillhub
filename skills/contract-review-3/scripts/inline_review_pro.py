"""
Word 文档修订工具 - 最终版 v7.0
直接在解压后的 XML 文件上使用 lxml 操作

v7.0 方法：
1. 解压原始 docx
2. 使用 python-docx 打开保存一次（确保格式兼容）
3. 在解压的 XML 上直接使用 lxml 添加修订标记
4. 重新打包

这种方法避免 python-docx 过滤修订标记的问题。
"""
import os
import shutil
import zipfile
import tempfile
import re
from datetime import datetime
from typing import List, Dict, Tuple
from docx import Document
from lxml import etree

# 命名空间
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
W_NS = f'{{{W}}}'
XML_NS = 'http://www.w3.org/XML/1998/namespace'

DATE_FORMAT = '%Y-%m-%dT%H:%M:%SZ'


def make_element(tag_name, text=None, **attrs):
    """创建带命名空间的元素"""
    elem = etree.Element(W_NS + tag_name)
    for key, val in attrs.items():
        if key.startswith('_'):
            # 以 _ 开头的属性使用 XML 命名空间
            elem.set('{' + XML_NS + '}' + key[1:], str(val))
        elif key.startswith('w:'):
            elem.set(W_NS + key[2:], str(val))
        else:
            elem.set(key, str(val))
    if text is not None:
        elem.text = text
    return elem


def make_r(text):
    """创建 <w:r><w:t>"""
    r = etree.Element(W_NS + 'r')
    t = etree.SubElement(r, W_NS + 't')
    t.set('{' + XML_NS + '}space', 'preserve')
    t.text = text
    return r


def make_del(text, rev_id, author, date):
    """创建 <w:del><w:r><w:delText>"""
    del_elem = etree.Element(W_NS + 'del')
    del_elem.set(W_NS + 'id', str(rev_id))
    del_elem.set(W_NS + 'author', author)
    del_elem.set(W_NS + 'date', date)

    r = etree.SubElement(del_elem, W_NS + 'r')
    del_text = etree.SubElement(r, W_NS + 'delText')
    del_text.set('{' + XML_NS + '}space', 'preserve')
    del_text.text = text
    return del_elem


def make_ins(text, ins_id, author, date):
    """创建 <w:ins><w:r><w:t>"""
    ins_elem = etree.Element(W_NS + 'ins')
    ins_elem.set(W_NS + 'id', str(ins_id))
    ins_elem.set(W_NS + 'author', author)
    ins_elem.set(W_NS + 'date', date)

    r = etree.SubElement(ins_elem, W_NS + 'r')
    t = etree.SubElement(r, W_NS + 't')
    t.set('{' + XML_NS + '}space', 'preserve')
    t.text = text
    return ins_elem


def make_comment_range(cid):
    """创建批注范围元素"""
    cs = etree.Element(W_NS + 'commentRangeStart')
    cs.set(W_NS + 'id', str(cid))

    ce = etree.Element(W_NS + 'commentRangeEnd')
    ce.set(W_NS + 'id', str(cid))

    crr = etree.Element(W_NS + 'r')
    ref = etree.SubElement(crr, W_NS + 'commentReference')
    ref.set(W_NS + 'id', str(cid))

    return cs, ce, crr


def escape_xml(text):
    """XML 转义"""
    if not text:
        return ""
    return (text
        .replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '&quot;')
        .replace("'", '&apos;'))


class WordRevisionToolV7:
    """直接在 XML 上操作的修订工具"""

    def __init__(self, original_path: str, output_path: str = None, author: str = "AI审核助手"):
        self.original_path = original_path
        self.output_path = output_path or original_path.replace('.docx', '_修订版.docx')
        self.author = author
        self.date = datetime.now().strftime(DATE_FORMAT)
        self.temp_dir = None
        self.revisions: List[Dict] = []
        self.comments: List[Dict] = []
        self.next_id = 1

    def _extract(self) -> str:
        """解压 docx"""
        self.temp_dir = tempfile.mkdtemp(prefix='word_rev7_')
        with zipfile.ZipFile(self.original_path, 'r') as zf:
            zf.extractall(self.temp_dir)
        return self.temp_dir

    def _pack(self) -> str:
        """重新打包 docx"""
        with zipfile.ZipFile(self.output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(self.temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, self.temp_dir)
                    zf.write(file_path, arcname)

        shutil.rmtree(self.temp_dir)
        self.temp_dir = None
        return self.output_path

    def _get_id(self) -> int:
        self.next_id += 1
        return self.next_id

    def add_revision(self, old_text: str, new_text: str, reason: str = "",
                    clause: str = "", legal_basis: str = "",
                    suggestion: str = "", change_type: str = "modify"):
        """添加修订"""
        self.revisions.append({
            'old_text': old_text,
            'new_text': new_text,
            'reason': reason,
            'clause': clause,
            'legal_basis': legal_basis,
            'suggestion': suggestion,
        })

        if reason or legal_basis or suggestion:
            self.comments.append({
                'clause': clause,
                'text': reason,
                'legal_basis': legal_basis,
                'suggestion': suggestion,
                'author': self.author,
                'date': self.date
            })

    def _apply_revisions(self) -> bool:
        """在 XML 上应用修订"""
        doc_path = os.path.join(self.temp_dir, 'word', 'document.xml')

        # 读取并解析 XML
        parser = etree.XMLParser(remove_blank_text=False)
        tree = etree.parse(doc_path, parser)
        root = tree.getroot()

        applied_count = 0

        for i, rev in enumerate(self.revisions):
            old_text = rev['old_text']
            new_text = rev.get('new_text', '')
            cid = i + 1 if i < len(self.comments) else None

            # 查找包含 old_text 的段落
            for para in root.iter(W_NS + 'p'):
                # 收集段落文本
                para_text = ''.join([
                    t.text for t in para.iter(W_NS + 't')
                    if t.text
                ])

                if old_text not in para_text:
                    continue

                # 在段落中查找包含 old_text 的 run
                for run in para.iter(W_NS + 'r'):
                    run_text = ''.join([
                        t.text for t in run.iter(W_NS + 't')
                        if t.text
                    ])

                    if old_text not in run_text:
                        continue

                    # 找到目标 run，执行替换
                    success = self._replace_run_with_revision(
                        para, run, old_text, new_text, cid
                    )

                    if success:
                        print(f"  ✓ 已修订: {old_text[:30]}...")
                        applied_count += 1
                    break

                break  # 找到段落后跳出

        # 写回 XML
        tree.write(doc_path, xml_declaration=True, encoding='UTF-8', standalone=True)

        # 验证
        try:
            with open(doc_path, 'r') as f:
                etree.fromstring(f.read().encode('utf-8'))
            print("  ✓ XML 验证通过")
        except etree.XMLSyntaxError as e:
            print(f"  ⚠️ XML 验证警告: {e}")

        return applied_count > 0

    def _replace_run_with_revision(self, para, run, old_text, new_text, cid=None):
        """替换 run 为修订标记"""
        run_text = ''.join([
            t.text for t in run.iter(W_NS + 't')
            if t.text
        ])

        idx = run_text.find(old_text)
        if idx < 0:
            return False

        # 分割文本
        before = run_text[:idx]
        after = run_text[idx + len(old_text):]

        # 获取修订 ID
        rev_id = self._get_id()
        ins_id = self._get_id()

        # 获取 run 的位置
        run_index = list(para).index(run)

        # 创建新元素
        new_elements = []

        if before:
            new_elements.append(make_r(before))

        if cid:
            cs, ce, crr = make_comment_range(cid)
            new_elements.append(cs)

        new_elements.append(make_del(old_text, rev_id, self.author, self.date))
        new_elements.append(make_ins(new_text, ins_id, self.author, self.date))

        if cid:
            new_elements.append(ce)
            new_elements.append(crr)

        if after:
            new_elements.append(make_r(after))

        # 插入并删除原 run
        for j, elem in enumerate(new_elements):
            para.insert(run_index + j, elem)
        para.remove(run)

        return True

    def _create_comments_xml(self) -> str:
        """创建批注 XML"""
        lines = [
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
            '<w:comments xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        ]

        for i, comment in enumerate(self.comments):
            cid = i + 1
            content_parts = []
            if comment.get('clause'):
                content_parts.append(f"【{comment['clause']}】")
            if comment.get('text'):
                content_parts.append(f"【问题】{comment['text']}")
            if comment.get('legal_basis'):
                content_parts.append(f"【法律依据】{comment['legal_basis']}")
            if comment.get('suggestion'):
                content_parts.append(f"【修改建议】{comment['suggestion']}")

            content = escape_xml('\n'.join(content_parts))

            lines.append(f'  <w:comment w:id="{cid}" w:author="{escape_xml(comment["author"])}" w:date="{comment["date"]}" w:initials="AI">')
            lines.append('    <w:p>')
            lines.append('      <w:r>')
            lines.append(f'        <w:t xml:space="preserve">{content}</w:t>')
            lines.append('      </w:r>')
            lines.append('    </w:p>')
            lines.append('  </w:comment>')

        lines.append('</w:comments>')
        return '\n'.join(lines)

    def _update_content_types(self):
        """更新 Content_Types.xml"""
        ct_path = os.path.join(self.temp_dir, '[Content_Types].xml')
        with open(ct_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if '/word/comments.xml' not in content:
            insert_pos = content.rfind('</Types>')
            new_override = '<Override PartName="/word/comments.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"/>'
            content = content[:insert_pos] + new_override + content[insert_pos:]
            with open(ct_path, 'w', encoding='utf-8') as f:
                f.write(content)

    def _update_rels(self):
        """更新关系文件"""
        rels_path = os.path.join(self.temp_dir, 'word', '_rels', 'document.xml.rels')
        with open(rels_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if 'comments' not in content:
            ids = re.findall(r'Id="rId(\d+)"', content)
            max_id = max([int(i) for i in ids]) if ids else 0
            insert_pos = content.rfind('</Relationships>')
            new_rel = f'<Relationship Id="rId{max_id + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments" Target="comments.xml"/>'
            content = content[:insert_pos] + new_rel + content[insert_pos:]
            with open(rels_path, 'w', encoding='utf-8') as f:
                f.write(content)

    def process(self) -> Tuple[bool, str]:
        """处理文档"""
        try:
            self._extract()

            self._apply_revisions()

            if self.comments:
                comments_xml = self._create_comments_xml()
                comments_path = os.path.join(self.temp_dir, 'word', 'comments.xml')
                with open(comments_path, 'w', encoding='utf-8') as f:
                    f.write(comments_xml)

                self._update_content_types()
                self._update_rels()

            return (True, self._pack())

        except Exception as e:
            import traceback
            traceback.print_exc()
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
            return (False, str(e))


def review_contract(input_path: str, output_path: str = None,
                   reviews: List[Dict] = None, author: str = "AI审核助手") -> Tuple[bool, str]:
    """审核合同并生成修订稿"""
    tool = WordRevisionToolV7(input_path, output_path, author)

    if reviews:
        for review in reviews:
            tool.add_revision(
                old_text=review.get('old_text', ''),
                new_text=review.get('new_text', ''),
                reason=review.get('reason', ''),
                clause=review.get('clause', ''),
                legal_basis=review.get('legal_basis', ''),
                suggestion=review.get('suggestion', '')
            )

    return tool.process()


def test():
    """测试"""
    print("\n" + "="*60)
    print("测试 WordRevisionTool v7.0 (直接 XML 操作)")
    print("="*60)

    tool = WordRevisionToolV7(
        "/Users/gaoshengjie/WorkBuddy/20260414170047/悉宠&星期八辣产品策划服务合同0415.docx",
        "/Users/gaoshengjie/WorkBuddy/20260414170047/测试_v7.docx",
        "AI审核助手"
    )

    tool.add_revision(
        old_text="原告所在地人民法院",
        new_text="合同签订地有管辖权的人民法院",
        clause="第十条 争议解决",
        reason="根据《民事诉讼法》第35条",
        legal_basis="《民事诉讼法》第35条",
        suggestion="增加协议管辖条款"
    )

    tool.add_revision(
        old_text="万分之三每日",
        new_text="万分之一点五每日",
        clause="第八条 违约责任",
        reason="年化利率约10.95%，可能偏高",
        legal_basis="《民法典》第585条",
        suggestion="调低比例"
    )

    tool.add_revision(
        old_text="视情况",
        new_text="因乙方原因给甲方造成重大负面影响时",
        clause="第八条 违约责任",
        reason="'视情况'表述过于模糊",
        legal_basis="《民法典》第563条",
        suggestion="明确认定标准"
    )

    success, path = tool.process()

    if success:
        print(f"\n✓ 成功生成: {path}")
    else:
        print(f"\n✗ 失败: {path}")


if __name__ == '__main__':
    test()
