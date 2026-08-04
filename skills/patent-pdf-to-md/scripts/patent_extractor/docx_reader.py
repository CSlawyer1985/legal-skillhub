"""DOCX/DOC 文件文本提取模块。

本模块负责从 .docx 和 .doc 格式的专利文档中提取文本内容，
输出与 PDFReader 兼容的 PageText 列表，使后续的章节解析、
JSON 生成和 Markdown 生成流程无需修改即可复用。

提取策略：
1. .docx 文件：使用 OOXML 直接解析，支持以下布局：
   - 常规段落（按文档顺序）
   - 绝对定位框架（w:framePr，PDF 转 DOCX 常见，按 y/x 坐标排序）
   - 表格（提取单元格文本）
   - 文本框（wps:txbx/w:txbxContent）
2. .doc 文件：按优先级检测并使用已安装的办公软件转换为 .docx
   - 优先级：WPS Office > Microsoft Office > LibreOffice
   - 支持 Windows 和 macOS 平台

输出格式与 PDFReader.extract_pages() 一致：
    List[PageText]，每个 PageText 包含 page_num、text、text_no_space、source
"""

import logging
import os
import platform
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import List, Optional, Tuple
from xml.etree import ElementTree as ET

from .pdf_reader import PageText

logger = logging.getLogger('patent_extractor')

# OOXML 命名空间
W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
R_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
WP_NS = 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'
WPS_NS = 'http://schemas.microsoft.com/office/word/2010/wordprocessingShape'
MC_NS = 'http://schemas.openxmlformats.org/markup-compatibility/2006'
V_NS = 'urn:schemas-microsoft-com:vml'


class DocxReader:
    """DOCX/DOC 文件文本提取器。

    支持从 .docx 和 .doc 格式的专利文档中提取文本，
    输出与 PDFReader 兼容的 PageText 列表。

    特别处理 PDF 转 DOCX 产生的绝对定位框架（w:framePr），
    通过 y/x 坐标排序恢复正确的阅读顺序。
    """

    def __init__(self):
        self._is_image_based = False

    @property
    def is_image_based(self) -> bool:
        return False

    def extract_pages(self, file_path: str) -> List[PageText]:
        """从 DOCX/DOC 文件中提取文本，返回 PageText 列表。

        Args:
            file_path: DOCX/DOC 文件路径

        Returns:
            List[PageText]: 按虚拟页面分组的文本列表
        """
        path = Path(file_path)
        ext = path.suffix.lower()

        if ext == '.docx':
            return self._extract_from_docx(file_path)
        elif ext == '.doc':
            return self._extract_from_doc(file_path)
        else:
            logger.error(f"不支持的文件格式: {ext}，仅支持 .docx 和 .doc")
            return []

    # ------------------------------------------------------------------
    # .doc → .docx 转换：多引擎检测与转换
    # ------------------------------------------------------------------

    def _extract_from_doc(self, file_path: str) -> List[PageText]:
        """从 .doc 文件提取文本（先转换为 .docx）。

        按优先级检测系统中已安装的办公软件并执行转换：
        1. WPS Office（中国用户最常用）
        2. Microsoft Office（全球用户常用）
        3. LibreOffice（开源方案，作为兜底）

        Args:
            file_path: .doc 文件路径

        Returns:
            List[PageText]: 提取的页面文本列表
        """
        converter = self._detect_office_converter()
        if not converter:
            logger.error(
                "无法处理 .doc 文件：未检测到可用的办公软件。\n"
                "请安装以下任一软件后重试：\n"
                "  - WPS Office（推荐，https://www.wps.cn）\n"
                "  - Microsoft Office（https://www.office.com）\n"
                "  - LibreOffice（https://www.libreoffice.org）\n"
                "或将 .doc 手动另存为 .docx 后再处理。"
            )
            return []

        office_name = converter['name']
        logger.info(f"检测到 {office_name}，使用其进行 .doc → .docx 转换")

        with tempfile.TemporaryDirectory(prefix='doc_convert_') as tmp_dir:
            logger.info(f"正在将 .doc 转换为 .docx: {file_path}")
            try:
                result = converter['convert'](file_path, tmp_dir)
                if not result:
                    logger.error(f"{office_name} 转换失败")
                    return []
            except subprocess.TimeoutExpired:
                logger.error(f"{office_name} 转换超时（60秒）")
                return []
            except Exception as e:
                logger.error(f"{office_name} 转换异常: {e}")
                return []

            docx_name = Path(file_path).stem + '.docx'
            docx_path = os.path.join(tmp_dir, docx_name)
            if not os.path.isfile(docx_path):
                logger.error(f"转换后未找到 .docx 文件: {docx_path}")
                return []

            return self._extract_from_docx(docx_path)

    def _detect_office_converter(self) -> Optional[dict]:
        """检测系统中已安装的办公软件，返回转换器信息。

        检测优先级：WPS Office > Microsoft Office > LibreOffice

        Returns:
            dict: 包含 'name' 和 'convert' 函数的字典，未检测到则返回 None
        """
        system = platform.system()

        # 1. 检测 WPS Office
        wps = self._detect_wps(system)
        if wps:
            return wps

        # 2. 检测 Microsoft Office
        ms_office = self._detect_ms_office(system)
        if ms_office:
            return ms_office

        # 3. 检测 LibreOffice（兜底方案）
        libreoffice = self._detect_libreoffice()
        if libreoffice:
            return libreoffice

        return None

    def _detect_wps(self, system: str) -> Optional[dict]:
        """检测 WPS Office 安装路径。

        Args:
            system: 操作系统类型（'Windows', 'Darwin', 'Linux'）

        Returns:
            dict: WPS 转换器信息，未检测到则返回 None
        """
        if system == 'Windows':
            wps_paths = self._find_wps_windows()
        elif system == 'Darwin':
            wps_paths = self._find_wps_macos()
        else:
            wps_paths = self._find_wps_linux()

        if not wps_paths:
            return None

        # 优先使用 et（WPS 表格），但 doc 转换需要 wps（WPS 文字）
        wps_exe = wps_paths.get('wps') or wps_paths.get('et')
        if not wps_exe:
            return None

        logger.info(f"检测到 WPS Office: {wps_exe}")
        return {
            'name': 'WPS Office',
            'convert': lambda src, outdir: self._convert_with_wps(wps_exe, src, outdir),
        }

    def _find_wps_windows(self) -> dict:
        """在 Windows 系统中查找 WPS Office 安装路径。

        Returns:
            dict: 包含 'wps' 键的路径字典，未找到则返回空字典
        """
        # 通过注册表或常见安装路径查找
        search_dirs = []

        # 方法1：通过注册表获取安装路径
        try:
            result = subprocess.run(
                ['reg', 'query',
                 r'HKLM\SOFTWARE\Kingsoft\Office\6.0\common',
                 '/v', 'InstallRoot', '/reg:32'],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if 'REG_SZ' in line:
                        install_root = line.split('REG_SZ')[-1].strip()
                        if install_root and os.path.isdir(install_root):
                            search_dirs.append(install_root)
        except Exception:
            pass

        # 方法2：常见安装路径
        common_paths = [
            os.path.join(os.environ.get('ProgramFiles', r'C:\Program Files'),
                         'Kingsoft', 'WPS Office'),
            os.path.join(os.environ.get('ProgramFiles(x86)', r'C:\Program Files (x86)'),
                         'Kingsoft', 'WPS Office'),
            os.path.join(os.environ.get('LOCALAPPDATA', ''),
                         'Kingsoft', 'WPS Office'),
        ]
        for p in common_paths:
            if p and os.path.isdir(p):
                search_dirs.append(p)

        # 在安装目录中查找 wps.exe
        for base_dir in search_dirs:
            for root, dirs, files in os.walk(base_dir):
                if 'wps.exe' in files:
                    return {'wps': os.path.join(root, 'wps.exe')}
                if 'et.exe' in files:
                    return {'et': os.path.join(root, 'et.exe')}

        return {}

    def _find_wps_macos(self) -> dict:
        """在 macOS 系统中查找 WPS Office 安装路径。

        Returns:
            dict: 包含 'wps' 键的路径字典，未找到则返回空字典
        """
        mac_paths = [
            '/Applications/wpsoffice.app',
            os.path.expanduser('~/Applications/wpsoffice.app'),
        ]
        for app_path in mac_paths:
            if os.path.isdir(app_path):
                # WPS macOS 命令行工具路径
                cli_path = os.path.join(app_path, 'Contents', 'MacOS', 'wps')
                if os.path.isfile(cli_path):
                    return {'wps': cli_path}
                # 尝试主可执行文件
                main_path = os.path.join(app_path, 'Contents', 'MacOS', 'wpsoffice')
                if os.path.isfile(main_path):
                    return {'wps': main_path}

        # 通过 mdfind（Spotlight）搜索
        try:
            result = subprocess.run(
                ['mdfind', 'kMDItemCFBundleIdentifier == com.kingsoft.wpsoffice.mac'],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                app_path = result.stdout.strip().splitlines()[0]
                cli_path = os.path.join(app_path, 'Contents', 'MacOS', 'wps')
                if os.path.isfile(cli_path):
                    return {'wps': cli_path}
                main_path = os.path.join(app_path, 'Contents', 'MacOS', 'wpsoffice')
                if os.path.isfile(main_path):
                    return {'wps': main_path}
        except Exception:
            pass

        return {}

    def _find_wps_linux(self) -> dict:
        """在 Linux 系统中查找 WPS Office 安装路径。

        Returns:
            dict: 包含 'wps' 键的路径字典，未找到则返回空字典
        """
        # 通过 which 查找
        wps_bin = shutil.which('wps')
        if wps_bin:
            return {'wps': wps_bin}

        # 常见安装路径
        linux_paths = [
            '/usr/bin/wps',
            '/opt/kingsoft/wps-office/office6/wps',
            '/opt/wps-office/office6/wps',
        ]
        for p in linux_paths:
            if os.path.isfile(p):
                return {'wps': p}

        return {}

    def _convert_with_wps(self, wps_exe: str, src_file: str, out_dir: str) -> bool:
        """使用 WPS Office 将 .doc 转换为 .docx。

        WPS Office 支持通过命令行参数进行格式转换，
        使用 --headless 模式避免启动 GUI 界面。

        Args:
            wps_exe: WPS 可执行文件路径
            src_file: 源 .doc 文件路径
            out_dir: 输出目录

        Returns:
            bool: 转换是否成功
        """
        try:
            cmd = [wps_exe, '--headless', '--convert-to', 'docx',
                   '--outdir', out_dir, src_file]
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=60,
            )
            if result.returncode != 0:
                logger.error(f"WPS Office 转换失败: {result.stderr}")
                return False
            return True
        except subprocess.TimeoutExpired:
            logger.error("WPS Office 转换超时")
            return False
        except Exception as e:
            logger.error(f"WPS Office 转换异常: {e}")
            return False

    def _detect_ms_office(self, system: str) -> Optional[dict]:
        """检测 Microsoft Office 安装路径。

        Args:
            system: 操作系统类型（'Windows', 'Darwin', 'Linux'）

        Returns:
            dict: MS Office 转换器信息，未检测到则返回 None
        """
        if system == 'Windows':
            return self._detect_ms_office_windows()
        elif system == 'Darwin':
            return self._detect_ms_office_macos()
        # Linux 不支持 Microsoft Office 桌面版
        return None

    def _detect_ms_office_windows(self) -> Optional[dict]:
        """在 Windows 系统中查找 Microsoft Office 安装路径。

        Returns:
            dict: MS Office 转换器信息，未检测到则返回 None
        """
        # 查找 WINWORD.EXE
        word_paths = []

        # 方法1：通过注册表查找
        try:
            result = subprocess.run(
                ['reg', 'query',
                 r'HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\WINWORD.EXE',
                 '/ve'],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if 'REG_SZ' in line:
                        path = line.split('REG_SZ')[-1].strip().strip('"')
                        if path and os.path.isfile(path):
                            word_paths.append(path)
        except Exception:
            pass

        # 方法2：常见安装路径
        program_dirs = [
            os.environ.get('ProgramFiles', r'C:\Program Files'),
            os.environ.get('ProgramFiles(x86)', r'C:\Program Files (x86)'),
        ]
        for prog_dir in program_dirs:
            if not prog_dir:
                continue
            # Microsoft 365 / Office 2019+ / Office 2021+
            for office_dir_name in ['Microsoft Office', 'Microsoft Office 15', 'Microsoft Office 16']:
                base = os.path.join(prog_dir, 'Microsoft Office', 'root', 'Office16')
                word_exe = os.path.join(base, 'WINWORD.EXE')
                if os.path.isfile(word_exe):
                    word_paths.append(word_exe)
                # 旧版路径
                for version in ['Office16', 'Office15', 'Office14']:
                    base = os.path.join(prog_dir, 'Microsoft Office', version)
                    word_exe = os.path.join(base, 'WINWORD.EXE')
                    if os.path.isfile(word_exe):
                        word_paths.append(word_exe)

        if not word_paths:
            return None

        word_exe = word_paths[0]
        logger.info(f"检测到 Microsoft Office Word: {word_exe}")
        return {
            'name': 'Microsoft Office',
            'convert': lambda src, outdir: self._convert_with_ms_word(word_exe, src, outdir),
        }

    def _detect_ms_office_macos(self) -> Optional[dict]:
        """在 macOS 系统中查找 Microsoft Office 安装路径。

        Returns:
            dict: MS Office 转换器信息，未检测到则返回 None
        """
        mac_paths = [
            '/Applications/Microsoft Word.app',
            os.path.expanduser('~/Applications/Microsoft Word.app'),
        ]
        for app_path in mac_paths:
            if os.path.isdir(app_path):
                cli_path = os.path.join(app_path, 'Contents', 'MacOS', 'Microsoft Word')
                if os.path.isfile(cli_path):
                    logger.info(f"检测到 Microsoft Word: {cli_path}")
                    return {
                        'name': 'Microsoft Office',
                        'convert': lambda src, outdir: self._convert_with_ms_word_macos(
                            cli_path, src, outdir),
                    }

        # 通过 mdfind 搜索
        try:
            result = subprocess.run(
                ['mdfind', 'kMDItemCFBundleIdentifier == com.microsoft.Word'],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                app_path = result.stdout.strip().splitlines()[0]
                cli_path = os.path.join(app_path, 'Contents', 'MacOS', 'Microsoft Word')
                if os.path.isfile(cli_path):
                    logger.info(f"检测到 Microsoft Word: {cli_path}")
                    return {
                        'name': 'Microsoft Office',
                        'convert': lambda src, outdir: self._convert_with_ms_word_macos(
                            cli_path, src, outdir),
                    }
        except Exception:
            pass

        return None

    def _convert_with_ms_word(self, word_exe: str, src_file: str, out_dir: str) -> bool:
        """使用 Microsoft Word (Windows) 将 .doc 转换为 .docx。

        通过 COM 自动化或命令行参数执行转换。
        Windows 下 Word 支持通过 /mFileSaveAs 宏命令进行格式转换。

        Args:
            word_exe: WINWORD.EXE 路径
            src_file: 源 .doc 文件路径
            out_dir: 输出目录

        Returns:
            bool: 转换是否成功
        """
        # 方法1：尝试使用 PowerShell COM 自动化（更可靠）
        try:
            docx_name = Path(src_file).stem + '.docx'
            docx_path = os.path.join(out_dir, docx_name)

            # wdFormatXMLDocument = 12 (docx 格式)
            ps_script = (
                f"$word = New-Object -ComObject Word.Application; "
                f"$word.Visible = $false; "
                f"$doc = $word.Documents.Open('{os.path.abspath(src_file)}'); "
                f"$doc.SaveAs2('{os.path.abspath(docx_path)}', 12); "
                f"$doc.Close(); "
                f"$word.Quit(); "
                f"[System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null"
            )
            result = subprocess.run(
                ['powershell', '-NoProfile', '-Command', ps_script],
                capture_output=True, text=True, timeout=60,
            )
            if result.returncode == 0 and os.path.isfile(docx_path):
                return True
            logger.warning(f"PowerShell COM 转换未成功: {result.stderr}")
        except subprocess.TimeoutExpired:
            logger.warning("PowerShell COM 转换超时")
        except Exception as e:
            logger.warning(f"PowerShell COM 转换异常: {e}")

        # 方法2：尝试使用命令行参数（部分版本支持）
        try:
            cmd = [word_exe, '/mFileSaveAs', '/q', src_file]
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=60,
            )
            docx_name = Path(src_file).stem + '.docx'
            docx_path = os.path.join(out_dir, docx_name)
            if os.path.isfile(docx_path):
                return True
        except Exception:
            pass

        logger.error("Microsoft Word 转换失败，建议手动将 .doc 另存为 .docx")
        return False

    def _convert_with_ms_word_macos(self, word_exe: str, src_file: str, out_dir: str) -> bool:
        """使用 Microsoft Word (macOS) 将 .doc 转换为 .docx。

        macOS 下 Microsoft Word 通过 AppleScript 或命令行执行转换。

        Args:
            word_exe: Microsoft Word 可执行文件路径
            src_file: 源 .doc 文件路径
            out_dir: 输出目录

        Returns:
            bool: 转换是否成功
        """
        docx_name = Path(src_file).stem + '.docx'
        docx_path = os.path.abspath(os.path.join(out_dir, docx_name))
        src_abs = os.path.abspath(src_file)

        # 方法1：AppleScript 自动化
        try:
            apple_script = (
                f'tell application "Microsoft Word"\n'
                f'  open POSIX file "{src_abs}"\n'
                f'  save as active document format format document97 '
                f'file name "{docx_path}"\n'
                f'  close active document saving no\n'
                f'end tell'
            )
            result = subprocess.run(
                ['osascript', '-e', apple_script],
                capture_output=True, text=True, timeout=60,
            )
            if result.returncode == 0 and os.path.isfile(docx_path):
                return True
            logger.warning(f"AppleScript 转换未成功: {result.stderr}")
        except subprocess.TimeoutExpired:
            logger.warning("AppleScript 转换超时")
        except Exception as e:
            logger.warning(f"AppleScript 转换异常: {e}")

        # 方法2：使用 python-docx 或直接命令行（降级方案）
        logger.error(
            "Microsoft Word (macOS) 自动转换失败。\n"
            "建议手动操作：用 Word 打开 .doc 文件，另存为 .docx 格式后重试。"
        )
        return False

    def _detect_libreoffice(self) -> Optional[dict]:
        """检测 LibreOffice 安装路径。

        Returns:
            dict: LibreOffice 转换器信息，未检测到则返回 None
        """
        system = platform.system()
        soffice = None

        # 方法1：通过 which/where 查找
        soffice = shutil.which('soffice') or shutil.which('libreoffice')

        # 方法2：macOS 应用程序路径
        if not soffice and system == 'Darwin':
            mac_paths = [
                '/Applications/LibreOffice.app/Contents/MacOS/soffice',
                os.path.expanduser('~/Applications/LibreOffice.app/Contents/MacOS/soffice'),
            ]
            for p in mac_paths:
                if os.path.isfile(p):
                    soffice = p
                    break

        # 方法3：Windows 常见路径
        if not soffice and system == 'Windows':
            win_paths = [
                os.path.join(os.environ.get('ProgramFiles', r'C:\Program Files'),
                             'LibreOffice', 'program', 'soffice.exe'),
                os.path.join(os.environ.get('ProgramFiles(x86)', r'C:\Program Files (x86)'),
                             'LibreOffice', 'program', 'soffice.exe'),
            ]
            for p in win_paths:
                if p and os.path.isfile(p):
                    soffice = p
                    break

        if not soffice:
            return None

        logger.info(f"检测到 LibreOffice: {soffice}")
        return {
            'name': 'LibreOffice',
            'convert': lambda src, outdir: self._convert_with_libreoffice(soffice, src, outdir),
        }

    def _convert_with_libreoffice(self, soffice: str, src_file: str, out_dir: str) -> bool:
        """使用 LibreOffice 将 .doc 转换为 .docx。

        Args:
            soffice: LibreOffice 可执行文件路径
            src_file: 源 .doc 文件路径
            out_dir: 输出目录

        Returns:
            bool: 转换是否成功
        """
        try:
            cmd = [
                soffice, '--headless', '--convert-to', 'docx',
                '--outdir', out_dir, src_file,
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=60,
            )
            if result.returncode != 0:
                logger.error(f"LibreOffice 转换失败: {result.stderr}")
                return False
            return True
        except subprocess.TimeoutExpired:
            logger.error("LibreOffice 转换超时")
            return False
        except Exception as e:
            logger.error(f"LibreOffice 转换异常: {e}")
            return False

    def _extract_from_docx(self, file_path: str) -> List[PageText]:
        """从 .docx 文件提取文本。

        使用 OOXML 直接解析，支持绝对定位框架的坐标排序。

        Args:
            file_path: .docx 文件路径

        Returns:
            List[PageText]: 按虚拟页面分组的文本列表
        """
        try:
            return self._extract_with_ooxml(file_path)
        except Exception as e:
            logger.error(f"OOXML 解析失败: {e}")
            return []

    def _extract_with_ooxml(self, file_path: str) -> List[PageText]:
        """使用 OOXML 解析提取文本，支持绝对定位框架排序。

        处理流程：
        1. 解压 docx，读取 document.xml
        2. 遍历 body 子元素，提取段落文本和位置信息（保留文档顺序）
        3. 检测是否使用了绝对定位框架（w:framePr）
        4. 按分页符先分组为虚拟页面
        5. 每页内：若全部为框架段落则按坐标排序；否则保持文档顺序
        6. 提取文本框内容（wps:txbx/w:txbxContent）

        Args:
            file_path: .docx 文件路径

        Returns:
            List[PageText]: 按虚拟页面分组的文本列表
        """
        with zipfile.ZipFile(file_path, 'r') as zf:
            try:
                with zf.open('word/document.xml') as f:
                    tree = ET.parse(f)
            except KeyError:
                logger.error("docx 文件中未找到 word/document.xml")
                return []

        root = tree.getroot()
        body = root.find(f'{{{W_NS}}}body')
        if body is None:
            return []

        # 收集所有段落信息，保留文档顺序
        # 每个元素：(doc_order, y, x, text, has_page_break, is_framed)
        all_paragraphs_raw = []
        doc_order = 0
        has_framed_content = False

        for child in body:
            tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag

            if tag == 'p':
                text = self._extract_paragraph_text(child)
                has_page_break = self._has_page_break(child)

                # 检查是否有 framePr（绝对定位框架）
                frame_pr = self._find_frame_pr(child)
                if frame_pr is not None:
                    has_framed_content = True
                    x, y = self._get_frame_position(frame_pr)
                    all_paragraphs_raw.append((doc_order, y, x, text, has_page_break, True))
                else:
                    all_paragraphs_raw.append((doc_order, 0, 0, text, has_page_break, False))
                doc_order += 1

            elif tag == 'tbl':
                table_text = self._extract_table_text(child)
                if table_text:
                    all_paragraphs_raw.append((doc_order, 0, 0, table_text, False, False))
                    doc_order += 1

        # 提取文本框内容
        textbox_texts = self._extract_textbox_texts(root)
        for tb_text in textbox_texts:
            all_paragraphs_raw.append((doc_order, 0, 0, tb_text, False, False))
            doc_order += 1

        # 先按分页符分组为虚拟页面，再在每页内决定排序策略
        pages = self._group_and_sort_pages(all_paragraphs_raw, has_framed_content)

        logger.info(f"OOXML 解析完成: {len(pages)} 页, "
                     f"绝对定位框架: {has_framed_content}")
        return pages

    @staticmethod
    def _extract_paragraph_text(p_element) -> str:
        """从段落 XML 元素中提取文本。

        Args:
            p_element: w:p XML 元素

        Returns:
            str: 段落文本（去除首尾空白）
        """
        texts = []
        for t in p_element.iter(f'{{{W_NS}}}t'):
            if t.text:
                texts.append(t.text)
        return ''.join(texts).strip()

    @staticmethod
    def _has_page_break(p_element) -> bool:
        """检查段落是否包含分页符。

        Args:
            p_element: w:p XML 元素

        Returns:
            bool: 是否包含分页符
        """
        # 检查 run 中的分页符
        for br in p_element.iter(f'{{{W_NS}}}br'):
            if br.get(f'{{{W_NS}}}type') == 'page':
                return True

        # 检查段落属性中的分页符
        pPr = p_element.find(f'{{{W_NS}}}pPr')
        if pPr is not None:
            if pPr.find(f'.//{{{W_NS}}}pageBreakBefore') is not None:
                return True

        return False

    @staticmethod
    def _find_frame_pr(p_element):
        """查找段落的 framePr 属性。

        Args:
            p_element: w:p XML 元素

        Returns:
            framePr 元素，或 None
        """
        pPr = p_element.find(f'{{{W_NS}}}pPr')
        if pPr is not None:
            return pPr.find(f'{{{W_NS}}}framePr')
        return None

    @staticmethod
    def _get_frame_position(frame_pr) -> Tuple[int, int]:
        """从 framePr 中提取 x/y 坐标。

        OOXML 中 framePr 的坐标属性：
        - x: 水平位置（EMU 单位，1 EMU = 1/914400 英寸）
        - y: 垂直位置

        Args:
            frame_pr: w:framePr XML 元素

        Returns:
            (x, y) 坐标元组
        """
        try:
            x = int(frame_pr.get(f'{{{W_NS}}}x', '0'))
        except (ValueError, TypeError):
            x = 0
        try:
            y = int(frame_pr.get(f'{{{W_NS}}}y', '0'))
        except (ValueError, TypeError):
            y = 0
        return x, y

    @staticmethod
    def _extract_table_text(tbl_element) -> str:
        """从表格 XML 元素中提取文本。

        Args:
            tbl_element: w:tbl XML 元素

        Returns:
            str: 表格文本（每行用换行分隔，每列用 | 分隔）
        """
        rows = []
        for row in tbl_element.iter(f'{{{W_NS}}}tr'):
            cells = []
            for cell in row.iter(f'{{{W_NS}}}tc'):
                cell_texts = []
                for t in cell.iter(f'{{{W_NS}}}t'):
                    if t.text:
                        cell_texts.append(t.text)
                cell_text = ''.join(cell_texts).strip()
                cells.append(cell_text)
            if any(cells):
                rows.append(' | '.join(cells))
        return '\n'.join(rows)

    @staticmethod
    def _extract_textbox_texts(root) -> List[str]:
        """提取文档中所有文本框的内容。

        文本框可能出现在 wps:txbx/w:txbxContent 或 v:textbox 中。

        Args:
            root: document.xml 的根元素

        Returns:
            List[str]: 文本框文本列表
        """
        texts = []

        # 方式1：wps:txbx/w:txbxContent（现代格式）
        for txbx_content in root.iter(f'{{{WPS_NS}}}txbxContent'):
            # 跳过，因为 txbxContent 通常在 w:hdr/w:ftr 中
            # 但如果出现在 body 中也需要提取
            para_texts = []
            for t in txbx_content.iter(f'{{{W_NS}}}t'):
                if t.text:
                    para_texts.append(t.text)
            if para_texts:
                texts.append(''.join(para_texts).strip())

        # 方式2：v:textbox（旧版 VML 格式）
        for textbox in root.iter(f'{{{V_NS}}}textbox'):
            for t in textbox.iter(f'{{{W_NS}}}t'):
                if t.text:
                    texts.append(t.text.strip())

        return texts

    @staticmethod
    def _group_and_sort_pages(paragraphs: list, has_framed_content: bool) -> List[PageText]:
        """将段落按分页符分组为虚拟页面，并在每页内按策略排序。

        排序策略：
        - 若页面内全部为框架段落（is_framed=True），按 (y, x) 坐标排序恢复阅读顺序
        - 若页面内混合了普通段落和框架段落，保持文档原始顺序
          （普通段落无坐标信息，全局排序会将其错误地排到顶部）

        Args:
            paragraphs: 段落列表，每个元素为 (doc_order, y, x, text, has_page_break, is_framed)
            has_framed_content: 是否存在绝对定位框架

        Returns:
            List[PageText]: 按页面分组的文本列表
        """
        if not paragraphs:
            return []

        # 第一步：按分页符将段落分组为页面
        page_groups = []  # 每个元素是一个页面内的段落列表
        current_group = []

        for p in paragraphs:
            doc_order, y, x, text, has_page_break, is_framed = p
            if has_page_break and current_group:
                page_groups.append(current_group)
                current_group = []
            current_group.append(p)

        if current_group:
            page_groups.append(current_group)

        # 第二步：对每个页面内的段落决定排序策略
        pages = []
        for page_num, group in enumerate(page_groups, start=1):
            if has_framed_content:
                framed_count = sum(1 for p in group if p[5])  # p[5] = is_framed
                normal_count = len(group) - framed_count

                if framed_count > 0 and normal_count == 0:
                    # 全部为框架段落：按坐标排序恢复阅读顺序
                    group.sort(key=lambda p: (p[1], p[2]))  # p[1]=y, p[2]=x
                else:
                    # 混合段落：保持文档原始顺序
                    group.sort(key=lambda p: p[0])  # p[0]=doc_order
            # 无框架内容时，段落已按文档顺序排列，无需额外排序

            page_text = '\n'.join(p[3] for p in group if p[3])  # p[3]=text
            if page_text:
                pages.append(PageText(
                    page_num=page_num,
                    text=page_text,
                    text_no_space=page_text.replace(' ', ''),
                    source='docx',
                ))

        return pages

    @staticmethod
    def _group_into_pages(paragraphs: list) -> List[PageText]:
        """将段落列表按分页符分组为虚拟页面。

        Args:
            paragraphs: 段落列表，每个元素为 (y, x, text, has_page_break)

        Returns:
            List[PageText]: 按页面分组的文本列表
        """
        if not paragraphs:
            return []

        pages = []
        current_page_num = 1
        current_texts = []

        for y, x, text, has_page_break in paragraphs:
            if has_page_break and current_texts:
                # 分页符：保存当前页面，开始新页面
                page_text = '\n'.join(current_texts)
                pages.append(PageText(
                    page_num=current_page_num,
                    text=page_text,
                    text_no_space=page_text.replace(' ', ''),
                    source='docx',
                ))
                current_page_num += 1
                current_texts = []

            if text:
                current_texts.append(text)

        # 保存最后一个页面
        if current_texts:
            page_text = '\n'.join(current_texts)
            pages.append(PageText(
                page_num=current_page_num,
                text=page_text,
                text_no_space=page_text.replace(' ', ''),
                source='docx',
            ))

        # 如果没有提取到任何内容，返回空列表
        if not pages:
            return []

        return pages
