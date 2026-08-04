#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件解析器 - 支持多种合同文件格式
支持：TXT, DOCX, PDF, 图片(JPG/PNG) via OCR
"""

import os
from typing import Optional, List
import mimetypes


class FileParser:
    """文件解析器基类"""
    
    def __init__(self):
        self.supported_formats = ['.txt', '.docx', '.pdf', '.jpg', '.jpeg', '.png', '.bmp']
    
    def parse(self, file_path: str) -> str:
        """
        解析文件并返回文本内容
        
        Args:
            file_path: 文件路径
            
        Returns:
            提取的文本内容
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.txt':
            return self._parse_txt(file_path)
        elif ext == '.docx':
            return self._parse_docx(file_path)
        elif ext == '.pdf':
            return self._parse_pdf(file_path)
        elif ext in ['.jpg', '.jpeg', '.png', '.bmp']:
            return self._parse_image(file_path)
        else:
            raise ValueError(f"不支持的文件格式: {ext}")
    
    def _parse_txt(self, file_path: str) -> str:
        """解析TXT文件"""
        encodings = ['utf-8', 'gbk', 'gb2312', 'big5']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        
        raise ValueError("无法识别文件编码")
    
    def _parse_docx(self, file_path: str) -> str:
        """解析DOCX文件"""
        try:
            from docx import Document
            doc = Document(file_path)
            text = []
            for para in doc.paragraphs:
                text.append(para.text)
            return '\n'.join(text)
        except ImportError:
            raise ImportError("需要安装python-docx库: pip install python-docx")
    
    def _parse_pdf(self, file_path: str) -> str:
        """解析PDF文件"""
        # 尝试使用pdfplumber（推荐）
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                text = []
                for page in pdf.pages:
                    text.append(page.extract_text())
                return '\n'.join(filter(None, text))
        except ImportError:
            pass
        
        # 降级使用PyPDF2
        try:
            import PyPDF2
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = []
                for page in reader.pages:
                    text.append(page.extract_text())
                return '\n'.join(text)
        except ImportError:
            raise ImportError("需要安装PDF解析库: pip install pdfplumber 或 pip install PyPDF2")
    
    def _parse_image(self, file_path: str) -> str:
        """解析图片文件（使用OCR）"""
        # 尝试使用pytesseract（本地OCR）
        try:
            import pytesseract
            from PIL import Image
            
            img = Image.open(file_path)
            text = pytesseract.image_to_string(img, lang='chi_sim+eng')
            return text
        except ImportError:
            pass
        
        # 降级使用云OCR API（这里以腾讯云为例）
        try:
            return self._ocr_with_tencent_cloud(file_path)
        except:
            raise ImportError("需要安装OCR库: pip install pytesseract Pillow 或配置云OCR API")
    
    def _ocr_with_tencent_cloud(self, file_path: str) -> str:
        """使用腾讯云OCR API"""
        # 这里需要配置腾讯云OCR API密钥
        # 示例代码片段
        raise NotImplementedError("请配置腾讯云OCR API: https://cloud.tencent.com/product/ocr")
    
    def batch_parse(self, file_paths: List[str]) -> List[str]:
        """
        批量解析文件
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            文本内容列表
        """
        results = []
        for i, file_path in enumerate(file_paths, 1):
            print(f"正在解析第 {i}/{len(file_paths)} 个文件: {os.path.basename(file_path)}")
            try:
                text = self.parse(file_path)
                results.append(text)
            except Exception as e:
                print(f"✗ 解析失败: {e}")
                results.append("")  # 保持索引一致
        
        print(f"✓ 批量解析完成，成功 {len([r for r in results if r])}/{len(file_paths)} 个")
        return results


class SmartFileParser(FileParser):
    """智能文件解析器 - 支持自动格式检测和降级处理"""
    
    def __init__(self, use_ocr: bool = True, use_cloud_ocr: bool = False):
        super().__init__()
        self.use_ocr = use_ocr
        self.use_cloud_ocr = use_cloud_ocr
        
        # 检查可用库
        self.available_libs = self._check_available_libs()
        print(f"✓ 可用库: {', '.join(self.available_libs)}")
    
    def _check_available_libs(self) -> List[str]:
        """检查可用的解析库"""
        available = []
        
        # 检查python-docx
        try:
            import docx
            available.append('python-docx')
        except ImportError:
            pass
        
        # 检查pdfplumber
        try:
            import pdfplumber
            available.append('pdfplumber')
        except ImportError:
            pass
        
        # 检查PyPDF2
        try:
            import PyPDF2
            available.append('PyPDF2')
        except ImportError:
            pass
        
        # 检查pytesseract
        try:
            import pytesseract
            from PIL import Image
            available.append('pytesseract')
        except ImportError:
            pass
        
        return available
    
    def parse(self, file_path: str) -> str:
        """智能解析文件（带降级处理）"""
        ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if ext == '.txt':
                return self._parse_txt(file_path)
            elif ext == '.docx':
                if 'python-docx' in self.available_libs:
                    return self._parse_docx(file_path)
                else:
                    raise ImportError("需要python-docx库")
            elif ext == '.pdf':
                if 'pdfplumber' in self.available_libs:
                    return self._parse_pdf(file_path)
                elif 'PyPDF2' in self.available_libs:
                    return self._parse_pdf_fallback(file_path)
                else:
                    raise ImportError("需要PDF解析库")
            elif ext in ['.jpg', '.jpeg', '.png', '.bmp']:
                if not self.use_ocr:
                    raise ValueError("OCR功能未启用")
                if 'pytesseract' in self.available_libs:
                    return self._parse_image(file_path)
                elif self.use_cloud_ocr:
                    return self._ocr_with_tencent_cloud(file_path)
                else:
                    raise ImportError("需要OCR库")
            else:
                raise ValueError(f"不支持的格式: {ext}")
        except Exception as e:
            print(f"✗ 解析失败 ({os.path.basename(file_path)}): {e}")
            return ""
    
    def _parse_pdf_fallback(self, file_path: str) -> str:
        """PDF解析降级方案"""
        import PyPDF2
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = []
            for page in reader.pages:
                text.append(page.extract_text())
            return '\n'.join(text)


def create_parser(parser_type: str = 'smart', **kwargs) -> FileParser:
    """
    创建文件解析器
    
    Args:
        parser_type: 'basic' 或 'smart'
        **kwargs: 传递给解析器的参数
        
    Returns:
        文件解析器实例
    """
    if parser_type == 'smart':
        return SmartFileParser(**kwargs)
    else:
        return FileParser()


if __name__ == '__main__':
    # 测试代码
    print("="*60)
    print("文件解析器测试")
    print("="*60)
    
    # 创建智能解析器
    parser = create_parser('smart', use_ocr=False)
    
    # 创建测试文件
    test_file = 'test_contract.txt'
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write("""
        测试合同
        甲方：深圳某某科技有限公司
        乙方：北京某某技术服务公司
        合同金额：100万元
        """)
    
    # 解析测试文件
    try:
        text = parser.parse(test_file)
        print(f"\n✓ 解析成功:\n{text[:200]}...")
    except Exception as e:
        print(f"\n✗ 解析失败: {e}")
    
    # 清理测试文件
    if os.path.exists(test_file):
        os.remove(test_file)
    
    print("\n" + "="*60)
    print("建议安装的库:")
    print("  pip install python-docx pdfplumber PyPDF2 pytesseract Pillow")
    print("="*60)
