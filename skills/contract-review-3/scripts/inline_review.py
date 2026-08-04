"""
原文件修订工具 - 直接在原文件上添加修订和批注
直接在原 .docx 文件上操作，保留原文档格式
"""
import os
import sys
import shutil
import zipfile
from datetime import datetime
from xml.etree import ElementTree as ET
from typing import List, Dict, Optional, Tuple

# OOXML 命名空间
NAMESPACES = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'w14': 'http://schemas.microsoft.com/office/word/2010/wordml',
    'w15': 'http://schemas.microsoft.com/office/word/2012/wordml',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'mc': 'http://schemas.openxmlformats.org/markup-compatibility/2006',
    'cp': 'http://schemas.openxmlformats.org/package/2006/metadata/core-properties',
    'dc': 'http://purl.org/dc/elements/1.1/',
}

# 注册命名空间
for prefix, uri in NAMESPACES.items():
    ET.register_namespace(prefix, uri)


class RevisionItem:
    """修订项"""
    def __init__(self, old_text: str, new_text: str, reason: str, 
                 change_type: str = "modify", clause_title: str = ""):
        self.old_text = old_text
        self.new_text = new_text
        self.reason = reason
        self.change_type = change_type  # insert, delete, modify
        self.clause_title = clause_title


class CommentItem:
    """批注项"""
    def __init__(self, text: str, reason: str, location: str = "", 
                 legal_basis: str = "", suggestion: str = ""):
        self.text = text
        self.reason = reason
        self.location = location
        self.legal_basis = legal_basis
        self.suggestion = suggestion


class InlineReviewer:
    """
    原文件修订工具
    直接在原 .docx 文件上添加修订和批注
    """
    
    def __init__(self, original_docx_path: str, output_path: str = None, 
                 author: str = "AI审核助手"):
        self.original_docx_path = original_docx_path
        self.output_path = output_path or original_docx_path.replace('.docx', '_修订版.docx')
        self.author = author
        self.date = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # 临时解压目录
        self.temp_dir = None
        
        # 修订和批注列表
        self.revisions: List[RevisionItem] = []
        self.comments: List[CommentItem] = []
        
        # 修订/批注ID计数器
        self.revision_id = 100
        self.comment_id = 100
        
        # 记录所有批注（用于生成 comments.xml）
        self.comment_records = []
    
    def _extract_docx(self) -> str:
        """解压 docx 文件"""
        import tempfile
        self.temp_dir = tempfile.mkdtemp(prefix='docx_review_')
        
        with zipfile.ZipFile(self.original_docx_path, 'r') as zip_ref:
            zip_ref.extractall(self.temp_dir)
        
        return self.temp_dir
    
    def _pack_docx(self) -> bool:
        """重新打包 docx 文件"""
        if not self.temp_dir:
            return False
        
        # 创建新的 docx 文件
        with zipfile.ZipFile(self.output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_name = os.path.relpath(file_path, self.temp_dir)
                    zipf.write(file_path, arc_name)
        
        # 清理临时目录
        shutil.rmtree(self.temp_dir)
        self.temp_dir = None
        
        return True
    
    def _read_xml(self, xml_path: str) -> Optional[str]:
        """读取 XML 文件"""
        full_path = os.path.join(self.temp_dir, xml_path)
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        return None
    
    def _write_xml(self, xml_path: str, content: str):
        """写入 XML 文件"""
        full_path = os.path.join(self.temp_dir, xml_path)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _create_comment_xml(self) -> str:
        """创建 comments.xml"""
        if not self.comment_records:
            return ""
        
        comments_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:comments xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
            xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml"
            xmlns:w15="http://schemas.microsoft.com/office/word/2012/wordml">'''
        
        for i, comment in enumerate(self.comment_records):
            comment_id = i + 1
            comment_date = comment.get('date', self.date)
            comment_author = comment.get('author', self.author)
            comment_text = self._escape_xml(comment.get('text', ''))
            comment_reason = self._escape_xml(comment.get('reason', ''))
            comment_legal = self._escape_xml(comment.get('legal_basis', ''))
            comment_suggestion = self._escape_xml(comment.get('suggestion', ''))
            
            # 组合批注内容
            full_comment = f"{comment_text}"
            if comment_reason:
                full_comment += f"\n\n【修改理由】\n{comment_reason}"
            if comment_legal:
                full_comment += f"\n\n【法律依据】\n{comment_legal}"
            if comment_suggestion:
                full_comment += f"\n\n【修改建议】\n{comment_suggestion}"
            
            comments_xml += f'''
  <w:comment w:id="{comment_id}" w:author="{comment_author}" w:date="{comment_date}" w:initials="AI">
    <w:p>
      <w:r>
        <w:t xml:space="preserve">{self._escape_xml(full_comment)}</w:t>
      </w:r>
    </w:p>
  </w:comment>'''
        
        comments_xml += '''
</w:comments>'''
        
        return comments_xml
    
    def _escape_xml(self, text: str) -> str:
        """转义 XML 特殊字符"""
        if not text:
            return ""
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        text = text.replace('"', '&quot;')
        text = text.replace("'", '&apos;')
        return text
    
    def _ensure_comments_files(self):
        """确保批注相关文件存在"""
        word_dir = os.path.join(self.temp_dir, 'word')
        
        # 1. 创建 comments.xml
        comments_xml = self._create_comment_xml()
        if comments_xml:
            self._write_xml('word/comments.xml', comments_xml)
        
        # 2. 更新 [Content_Types].xml
        content_types = self._read_xml('[Content_Types].xml')
        if content_types and 'comments.xml' not in content_types:
            # 添加 comments.xml 内容类型
            insert_pos = content_types.find('</Types>')
            if insert_pos > 0:
                new_content = content_types[:insert_pos] + \
                    '<Override PartName="/word/comments.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"/>' + \
                    content_types[insert_pos:]
                self._write_xml('[Content_Types].xml', new_content)
        
        # 3. 更新 word/_rels/document.xml.rels
        rels_path = 'word/_rels/document.xml.rels'
        rels = self._read_xml(rels_path)
        if rels and 'comments.xml' not in rels:
            # 找到下一个可用的 rId
            import re
            rids = re.findall(r'Id="rId(\d+)"', rels)
            max_rid = max([int(r) for r in rids]) if rids else 0
            new_rid = max_rid + 1
            
            insert_pos = rels.find('</Relationships>')
            if insert_pos > 0:
                new_rels = rels[:insert_pos] + \
                    f'<Relationship Id="rId{new_rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments" Target="comments.xml"/>' + \
                    rels[insert_pos:]
                self._write_xml(rels_path, new_rels)
    
    def add_revision(self, revision: RevisionItem):
        """添加修订项"""
        self.revisions.append(revision)
    
    def add_comment(self, comment: CommentItem):
        """添加批注项"""
        self.comments.append(comment)
        self.comment_records.append({
            'text': comment.text,
            'reason': comment.reason,
            'legal_basis': comment.legal_basis,
            'suggestion': comment.suggestion,
            'author': self.author,
            'date': self.date
        })
    
    def add_revision_with_comment(self, old_text: str, new_text: str, 
                                   reason: str, clause_title: str = "",
                                   legal_basis: str = "", suggestion: str = "",
                                   change_type: str = "modify"):
        """添加带批注的修订"""
        revision = RevisionItem(old_text, new_text, reason, change_type, clause_title)
        self.add_revision(revision)
        
        comment = CommentItem(
            text=f"建议修改：{new_text if new_text else '(删除)'}",
            reason=reason,
            legal_basis=legal_basis,
            suggestion=suggestion
        )
        self.add_comment(comment)
    
    def process_document(self) -> bool:
        """
        处理文档：应用修订和批注
        
        策略：
        1. 解压原文档
        2. 解析 document.xml
        3. 在指定位置添加修订标记和批注
        4. 更新相关配置文件
        5. 重新打包
        """
        try:
            # 1. 解压文档
            self._extract_docx()
            
            # 2. 读取 document.xml
            doc_xml = self._read_xml('word/document.xml')
            if not doc_xml:
                print("❌ 无法读取 document.xml")
                return False
            
            # 3. 应用修订和批注
            modified_xml = self._apply_revisions_and_comments(doc_xml)
            
            # 4. 确保批注文件存在
            self._ensure_comments_files()
            
            # 5. 写回 document.xml
            self._write_xml('word/document.xml', modified_xml)
            
            # 6. 重新打包
            return self._pack_docx()
            
        except Exception as e:
            print(f"❌ 处理文档时出错: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _apply_revisions_and_comments(self, doc_xml: str) -> str:
        """
        应用修订和批注到 document.xml
        
        对于简单的文本替换，我们采用以下策略：
        1. 找到包含目标文本的 <w:t> 元素
        2. 将文本替换为带有修订标记的 XML
        """
        # 为了简化，我们使用字符串替换方式
        # 对于复杂的修订，需要使用 DOM 解析
        
        result = doc_xml
        
        # 处理修订
        for i, revision in enumerate(self.revisions):
            self.revision_id = 100 + i
            
            if revision.change_type == "delete":
                # 替换为删除标记
                old = self._escape_xml(revision.old_text)
                new_content = f'''<w:del w:id="{self.revision_id}" w:author="{self.author}" w:date="{self.date}"><w:r><w:delText xml:space="preserve">{old}</w:delText></w:r></w:del>'''
                result = result.replace(old, new_content, 1)
                
            elif revision.change_type == "insert":
                # 替换为插入标记
                new = self._escape_xml(revision.new_text)
                new_content = f'''<w:ins w:id="{self.revision_id}" w:author="{self.author}" w:date="{self.date}"><w:r><w:t xml:space="preserve">{new}</w:t></w:r></w:ins>'''
                result = result.replace(revision.old_text, new_content, 1) if revision.old_text else result.replace('<w:t>', f'<w:t>{new_content}', 1)
                
            elif revision.change_type == "modify":
                # 先删除旧文本，再插入新文本
                old = self._escape_xml(revision.old_text)
                new = self._escape_xml(revision.new_text)
                
                # 创建修订标记
                del_id = self.revision_id
                ins_id = self.revision_id + 1
                
                del_content = f'''<w:del w:id="{del_id}" w:author="{self.author}" w:date="{self.date}"><w:r><w:delText xml:space="preserve">{old}</w:delText></w:r></w:del>'''
                ins_content = f'''<w:ins w:id="{ins_id}" w:author="{self.author}" w:date="{self.date}"><w:r><w:t xml:space="preserve">{new}</w:t></w:r></w:ins>'''
                
                result = result.replace(old, del_content + ins_content, 1)
        
        # 处理批注
        if self.comment_records:
            # 为批注添加标记
            for i, comment in enumerate(self.comment_records):
                comment_id = i + 1
                comment_text = self._escape_xml(comment.get('text', '')[:50])  # 取前50字符作为定位
                
                # 查找并添加批注范围
                # 注意：这里需要精确定位，实际使用时需要更好的定位逻辑
                search_text = self._escape_xml(comment.get('text', ''))
                if search_text and search_text in result:
                    # 找到文本位置，添加批注标记
                    # 这是一个简化版本，实际使用需要更精确的定位
                    pass
        
        return result
    
    def create_inline_review(self, revisions: List[Dict], comments: List[Dict] = None) -> bool:
        """
        创建带修订和批注的文档
        
        Args:
            revisions: 修订列表，每项包含 old_text, new_text, reason, change_type
            comments: 批注列表
        
        Returns:
            bool: 是否成功
        """
        # 添加修订
        for rev in revisions:
            self.add_revision(RevisionItem(
                old_text=rev.get('old_text', ''),
                new_text=rev.get('new_text', ''),
                reason=rev.get('reason', ''),
                change_type=rev.get('change_type', 'modify'),
                clause_title=rev.get('clause_title', '')
            ))
            
            # 添加对应的批注
            if rev.get('reason') or rev.get('legal_basis') or rev.get('suggestion'):
                self.add_comment(CommentItem(
                    text=f"建议修改：{rev.get('new_text', '(删除)')}",
                    reason=rev.get('reason', ''),
                    legal_basis=rev.get('legal_basis', ''),
                    suggestion=rev.get('suggestion', '')
                ))
        
        # 添加独立批注
        if comments:
            for comm in comments:
                self.add_comment(CommentItem(
                    text=comm.get('text', ''),
                    reason=comm.get('reason', ''),
                    legal_basis=comm.get('legal_basis', ''),
                    suggestion=comm.get('suggestion', '')
                ))
        
        return self.process_document()


def review_and_markup(docx_path: str, output_path: str = None, 
                      reviews: List[Dict] = None, author: str = "AI审核助手") -> Tuple[bool, str]:
    """
    审核并标记文档
    
    Args:
        docx_path: 原文档路径
        output_path: 输出路径
        reviews: 审核修订列表
        author: 修订作者
    
    Returns:
        (成功标志, 输出路径/错误信息)
    """
    reviewer = InlineReviewer(docx_path, output_path, author)
    
    if reviews:
        for review in reviews:
            reviewer.add_revision_with_comment(
                old_text=review.get('old_text', ''),
                new_text=review.get('new_text', ''),
                reason=review.get('reason', ''),
                clause_title=review.get('clause_title', ''),
                legal_basis=review.get('legal_basis', ''),
                suggestion=review.get('suggestion', ''),
                change_type=review.get('change_type', 'modify')
            )
    
    success = reviewer.process_document()
    
    if success:
        return (True, reviewer.output_path)
    else:
        return (False, "处理失败")


if __name__ == '__main__':
    # 测试代码
    print("原文件修订工具 - 直接在原文件上添加修订和批注")
