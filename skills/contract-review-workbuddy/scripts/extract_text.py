#!/usr/bin/env python3
"""
多格式文本提取模块 v2.0
支持 PDF（文字版/扫描版）、Word、图片、纯文本
安全特性：魔术字节校验、文件大小限制、日志脱敏
"""

import sys
from pathlib import Path
from typing import Dict, Any
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 安全的文件类型魔术字节映射（防止恶意文件伪装）
MAGIC_BYTES = {
    b'%PDF': '.pdf',
    b'PK\x03\x04': '.docx',
    b'\x89PNG': '.png',
    b'\xff\xd8\xff': '.jpg',
    b'BM': '.bmp',
    b'II*\x00': '.tiff',
    b'MM\x00*': '.tiff',
    b'PK\x03\x04': '.docx',
    b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1': '.doc',
}

# 最大允许文件大小（50MB）
MAX_FILE_SIZE = 50 * 1024 * 1024

# ===== v3.0 新增：禁止文件类型拦截 =====
# Windows 可执行 / 批处理脚本
_BLOCKED_EXEC_EXT = {'.bat', '.cmd', '.ps1', '.vbs', '.exe', '.dll', '.lnk', '.msi'}

# Office 二进制文档（老版本，.doc/.ppt/.xls 等，但 .docx 允许因为合同需要）
_BLOCKED_OFFICE_EXT = {'.doc', '.xls', '.ppt', '.xlsm', '.docm', '.pptm'}

# 二进制镜像 / 安装包
_BLOCKED_ARCHIVE_EXT = {'.iso', '.dmg', '.zip', '.rar', '.7z', '.tar', '.gz', '.apk', '.jar'}

# 系统缓存 / 隐藏文件
_BLOCKED_SYSTEM_EXT = {'.ds_store', '.log', '.tmp'}

# 其他风险脚本
_BLOCKED_SCRIPT_EXT = {'.sh', '.com', '.scr', '.hta', '.reg'}

# 合并所有禁止后缀
BLOCKED_EXTENSIONS = (
    _BLOCKED_EXEC_EXT
    | _BLOCKED_OFFICE_EXT
    | _BLOCKED_ARCHIVE_EXT
    | _BLOCKED_SYSTEM_EXT
    | _BLOCKED_SCRIPT_EXT
)

# 禁止文件的魔术字节（用于深层拦截伪装文件）
BLOCKED_MAGIC_SIGNATURES = [
    (b'MZ', 'Windows 可执行文件 (.exe/.dll)'),      # PE 文件
    (b'\x7fELF', 'Linux 可执行文件'),               # ELF 文件
    (b'PK\x03\x04', '压缩包伪装 (zip/rar/docx)'),   # ZIP 家族（docx 会单独放行）
    (b'\x1f\x8b', 'Gzip 压缩文件'),                 # gzip
    (b'Rar', 'RAR 压缩文件'),                       # RAR
    (b'7z', '7z 压缩文件'),                         # 7z
    (b'{\\rtf', 'RTF 文档（可能含宏）'),             # RTF
]


def _validate_file_safety(file_path: str) -> None:
    """
    验证文件安全性，拦截所有危险文件类型
    
    Raises:
        ValueError: 文件类型被禁止或类型不匹配
        FileNotFoundError: 文件不存在
        RuntimeError: 文件大小超限
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    if not path.is_file():
        raise ValueError(f"路径不是文件: {file_path}")
    
    file_size = path.stat().st_size
    if file_size > MAX_FILE_SIZE:
        raise RuntimeError(
            f"文件过大 ({file_size/1024/1024:.1f}MB)，最大允许 {MAX_FILE_SIZE/1024/1024:.0f}MB"
        )
    
    if file_size == 0:
        raise ValueError("文件为空")
    
    # ===== v3.0 新增：禁止文件后缀拦截 =====
    ext = path.suffix.lower()
    
    if ext in BLOCKED_EXTENSIONS:
        # 分类提示
        if ext in _BLOCKED_EXEC_EXT:
            category = "Windows 可执行/批处理脚本"
        elif ext in _BLOCKED_OFFICE_EXT:
            category = "老版本 Office 二进制格式"
        elif ext in _BLOCKED_ARCHIVE_EXT:
            category = "压缩包/镜像文件"
        elif ext in _BLOCKED_SYSTEM_EXT:
            category = "系统缓存/临时文件"
        elif ext in _BLOCKED_SCRIPT_EXT:
            category = "脚本文件"
        else:
            category = "危险文件类型"
        
        raise PermissionError(
            f"🚫 安全拦截：{category} ({ext}) 被禁止上传。\n"
            f"原因：{category} 可能包含恶意代码或宏，存在安全风险。\n"
            f"建议：请将合同内容复制为纯文本后重新审查。"
        )
    
    # ===== v3.0 新增：魔术字节深层拦截 =====
    # 对非 docx 文件检查魔术字节（docx 是 zip 家族，单独处理）
    if ext != '.docx':
        with open(file_path, 'rb') as f:
            header = f.read(32)
        
        for signature, description in BLOCKED_MAGIC_SIGNATURES:
            if header.startswith(signature):
                raise PermissionError(
                    f"🚫 安全拦截：文件实际内容为 {description}，但被伪装为 {ext} 扩展名。\n"
                    f"原因：文件魔术字节与后缀不匹配，存在安全风险。\n"
                    f"建议：请将合同内容复制为纯文本后重新审查。"
                )
    
    # 检查魔术字节与后缀一致性
    if ext in ('.pdf', '.docx', '.doc', '.png', '.jpg', '.jpeg', '.bmp', '.tiff'):
        expected_exts = []
        for magic, magic_ext in MAGIC_BYTES.items():
            if magic_ext == ext:
                expected_exts.append(True)
        
        if expected_exts:
            with open(file_path, 'rb') as f:
                header = f.read(16)
            
            is_valid = False
            for magic, magic_ext in MAGIC_BYTES.items():
                if header.startswith(magic) and magic_ext == ext:
                    is_valid = True
                    break
            
            if not is_valid:
                # 尝试找到匹配的扩展名
                actual_ext = None
                for magic, magic_ext in MAGIC_BYTES.items():
                    if header.startswith(magic):
                        actual_ext = magic_ext
                        break
                
                if actual_ext:
                    raise ValueError(
                        f"文件类型不匹配：文件后缀为 {ext}，但内容识别为 {actual_ext}。"
                        f"您是否应该使用 {actual_ext} 扩展名？"
                    )


def _safe_snippet(text: str, max_len: int = 100) -> str:
    """
    安全地截取文本片段，不在中文字符中间截断
    
    Args:
        text: 原文
        max_len: 最大长度
        
    Returns:
        截断后的文本（不会在UTF-8多字节字符中间截断）
    """
    if len(text) <= max_len:
        return text
    
    # 确保不在UTF-8中间截断
    truncated = text[:max_len]
    # 如果最后一个字节是续字节（0b10xxxxxx），向后找到字符起始
    while truncated and (ord(truncated[-1]) & 0xC0) == 0x80:
        truncated = truncated[:-1]
    
    return truncated + "..."


class TextExtractor:
    """多格式文本提取器"""
    
    # 类级别的 OCR 实例缓存
    _ocr_instance = None
    
    def __init__(self, enable_security: bool = True):
        """
        初始化提取器
        
        Args:
            enable_security: 是否启用安全校验（魔术字节、大小限制）
        """
        self.enable_security = enable_security
        # v3.0: .doc 已移至 BLOCKED_LIST，不再支持（安全风险：可能含宏）
        self.supported_formats = {
            '.pdf': self._extract_pdf,
            '.docx': self._extract_docx,
            '.txt': self._extract_txt,
            '.md': self._extract_txt,
            '.jpg': self._extract_image,
            '.jpeg': self._extract_image,
            '.png': self._extract_image,
            '.bmp': self._extract_image,
            '.tiff': self._extract_image,
            '.tif': self._extract_image,
        }
    
    @classmethod
    def _get_ocr(cls):
        """获取或创建 OCR 实例"""
        if cls._ocr_instance is None:
            try:
                from paddleocr import PaddleOCR
                print("  ⏳ 初始化 OCR 引擎（首次使用需加载模型，约10-30秒）...", flush=True)
                cls._ocr_instance = PaddleOCR(use_angle_cls=True, lang='ch', show_log=False)
                print("  ✅ OCR 引擎初始化完成", flush=True)
            except ImportError:
                logger.error("paddleocr 未安装，请运行: pip install paddleocr")
                raise RuntimeError(
                    "OCR 功能需要 paddleocr 库。\n"
                    "安装方法：pip install paddleocr\n"
                    "安装后首次运行会自动下载模型（约 100MB）。"
                )
        return cls._ocr_instance
    
    def extract(self, file_path: str) -> Dict[str, Any]:
        """
        提取文件中的文本（含安全校验）
        
        Args:
            file_path: 文件路径
            
        Returns:
            {
                'text': str,
                'pages': list,
                'file_type': str,
                'ocr_confidence': float,
                'metadata': dict,
                'warnings': list,  # v2.0 新增：安全/质量警告
            }
        """
        # 安全校验
        warnings = []
        
        if self.enable_security:
            try:
                _validate_file_safety(file_path)
            except (ValueError, RuntimeError) as e:
                logger.error(f"安全校验失败: {e}")
                raise
        
        path = Path(file_path)
        ext = path.suffix.lower()
        if ext not in self.supported_formats:
            raise ValueError(
                f"不支持的文件格式: {ext}，支持的格式: {sorted(set(self.supported_formats.keys()))}"
            )
        
        # 注意：日志中不输出完整路径（仅文件名），保护隐私
        filename = path.name
        logger.info(f"正在提取文件: {filename} (格式: {ext})")
        
        result = self.supported_formats[ext](file_path)
        result['warnings'] = warnings
        
        return result
    
    def _extract_pdf(self, file_path: str) -> Dict[str, Any]:
        """提取 PDF 文本"""
        try:
            import pdfplumber
        except ImportError:
            raise ImportError(
                "PDF 提取需要 pdfplumber 库。\n"
                "安装方法：pip install pdfplumber"
            )
        
        pages_text = []
        
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                pages_text.append({
                    'page_num': i + 1,
                    'text': text,
                    'words': len(text),
                })
        
        total_pages = len(pages_text)
        
        full_text = '\n'.join([p['text'] for p in pages_text])
        
        # 判断是文字版还是扫描版
        is_scanned = self._is_scanned_pdf(pages_text)
        
        if is_scanned:
            logger.info("检测到扫描版 PDF，切换到 OCR 模式（可能较慢）")
            return self._extract_pdf_with_ocr(file_path)
        
        return {
            'text': full_text,
            'pages': pages_text,
            'file_type': 'pdf_text',
            'ocr_confidence': None,
            'metadata': {
                'total_pages': total_pages,
                'total_words': len(full_text),
                'is_scanned': False,
            }
        }
    
    def _is_scanned_pdf(self, pages_text: list) -> bool:
        """判断 PDF 是否为扫描版"""
        if not pages_text:
            return True
        
        sample_pages = pages_text[:3]
        avg_words = sum(p['words'] for p in sample_pages) / len(sample_pages)
        return avg_words < 10
    
    def _extract_pdf_with_ocr(self, file_path: str) -> Dict[str, Any]:
        """使用 OCR 提取扫描版 PDF（带进度显示）"""
        try:
            from paddleocr import PaddleOCR
            import fitz  # PyMuPDF
        except ImportError:
            raise ImportError(
                "OCR 功能需要 paddleocr 和 PyMuPDF。\n"
                "安装方法：pip install paddleocr PyMuPDF"
            )
        
        ocr = self._get_ocr()
        
        pages_text = []
        confidences = []
        
        doc = fitz.open(file_path)
        total_pages = len(doc)
        
        for i, page in enumerate(doc):
            print(f"    OCR 识别: 第 {i+1}/{total_pages} 页...", flush=True)
            
            pix = page.get_pixmap(dpi=300)
            img_data = pix.tobytes("png")
            
            result = ocr.ocr(img_data, cls=True)
            
            page_text = ""
            page_confidences = []
            if result and result[0]:
                for line in result[0]:
                    text = line[1][0]
                    confidence = line[1][1]
                    page_text += text + " "
                    page_confidences.append(confidence)
            
            pages_text.append({
                'page_num': i + 1,
                'text': page_text.strip(),
                'words': len(page_text),
            })
            
            if page_confidences:
                confidences.extend(page_confidences)
        
        doc.close()
        
        full_text = '\n'.join([p['text'] for p in pages_text])
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        warnings = []
        if avg_confidence < 0.80:
            warnings.append(f"OCR 置信度较低 ({avg_confidence:.0%})，建议人工核对扫描件页面")
        
        result = {
            'text': full_text,
            'pages': pages_text,
            'file_type': 'pdf_scan',
            'ocr_confidence': round(avg_confidence, 4),
            'metadata': {
                'total_pages': len(pages_text),
                'total_words': len(full_text),
                'is_scanned': True,
            },
            'warnings': warnings,
        }
        
        return result
    
    def _extract_docx(self, file_path: str) -> Dict[str, Any]:
        """提取 Word 文档文本"""
        try:
            from docx import Document
        except ImportError:
            raise ImportError(
                "Word 提取需要 python-docx 库。\n"
                "安装方法：pip install python-docx"
            )
        
        doc = Document(file_path)
        paragraphs = []
        
        for i, para in enumerate(doc.paragraphs):
            if para.text.strip():
                paragraphs.append({
                    'index': i,
                    'text': para.text,
                    'style': para.style.name if para.style else 'Normal',
                })
        
        full_text = '\n'.join([p['text'] for p in paragraphs])
        
        return {
            'text': full_text,
            'pages': [{'page_num': 1, 'text': full_text, 'words': len(full_text)}],
            'file_type': 'docx',
            'ocr_confidence': None,
            'metadata': {
                'total_pages': 1,
                'total_words': len(full_text),
                'total_paragraphs': len(paragraphs),
                'is_scanned': False,
            }
        }
    
    def _extract_txt(self, file_path: str) -> Dict[str, Any]:
        """提取纯文本"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        except UnicodeDecodeError:
            # 尝试 GBK 编码
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    text = f.read()
            except Exception:
                raise ValueError("无法识别文件编码，请确保文件为 UTF-8 或 GBK 编码的纯文本")
        
        return {
            'text': text,
            'pages': [{'page_num': 1, 'text': text, 'words': len(text)}],
            'file_type': 'txt',
            'ocr_confidence': None,
            'metadata': {
                'total_pages': 1,
                'total_words': len(text),
                'is_scanned': False,
            }
        }
    
    def _extract_image(self, file_path: str) -> Dict[str, Any]:
        """使用 OCR 提取图片中的文本"""
        try:
            from paddleocr import PaddleOCR
        except ImportError:
            raise ImportError(
                "OCR 功能需要 paddleocr 库。\n"
                "安装方法：pip install paddleocr"
            )
        
        ocr = self._get_ocr()
        
        result = ocr.ocr(file_path, cls=True)
        
        texts = []
        confidences = []
        if result and result[0]:
            for line in result[0]:
                text = line[1][0]
                confidence = line[1][1]
                texts.append(text)
                confidences.append(confidence)
        
        full_text = ' '.join(texts)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        warnings = []
        if avg_confidence < 0.80:
            warnings.append(f"OCR 置信度较低 ({avg_confidence:.0%})，建议核对原图")
        
        return {
            'text': full_text,
            'pages': [{'page_num': 1, 'text': full_text, 'words': len(full_text)}],
            'file_type': 'image',
            'ocr_confidence': round(avg_confidence, 4),
            'metadata': {
                'total_pages': 1,
                'total_words': len(full_text),
                'is_scanned': True,
            },
            'warnings': warnings,
        }


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("用法: python extract_text.py <文件路径>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    extractor = TextExtractor(enable_security=True)
    
    try:
        result = extractor.extract(file_path)
        print(f"文件类型: {result['file_type']}")
        print(f"总页数: {result['metadata']['total_pages']}")
        print(f"总字数: {result['metadata']['total_words']}")
        if result['ocr_confidence']:
            print(f"OCR置信度: {result['ocr_confidence']:.0%}")
        if result.get('warnings'):
            for w in result['warnings']:
                print(f"⚠️ {w}")
        print(f"\n--- 提取的文本预览 ---\n{_safe_snippet(result['text'], 500)}")
    except Exception as e:
        logger.error(f"提取失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
