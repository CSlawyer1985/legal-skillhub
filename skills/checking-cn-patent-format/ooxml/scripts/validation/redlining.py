"""
用于验证 Word 文档中修订追踪的验证器。
"""

import subprocess
import tempfile
import zipfile
from pathlib import Path


class RedliningValidator:
    """用于验证 Word 文档中修订追踪的验证器。"""

    def __init__(self, unpacked_dir, original_docx, verbose=False):
        self.unpacked_dir = Path(unpacked_dir)
        self.original_docx = Path(original_docx)
        self.verbose = verbose
        self.namespaces = {
            "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
        }

    def validate(self):
        modified_file = self.unpacked_dir / "word" / "document.xml"
        if not modified_file.exists():
            print(f"失败 - 未找到修改后的 document.xml: {modified_file}")
            return False

        try:
            import xml.etree.ElementTree as ET

            tree = ET.parse(modified_file)
            root = tree.getroot()

            del_elements = root.findall(".//w:del", self.namespaces)
            ins_elements = root.findall(".//w:ins", self.namespaces)

            has_tracked_changes = bool(del_elements or ins_elements)

            if not has_tracked_changes:
                if self.verbose:
                    print("通过 - 未发现修订追踪。")
                return True

        except Exception:
            pass

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            try:
                with zipfile.ZipFile(self.original_docx, "r") as zip_ref:
                    zip_ref.extractall(temp_path)
            except Exception as e:
                print(f"失败 - 解压原始 docx 时出错: {e}")
                return False

            original_file = temp_path / "word" / "document.xml"
            if not original_file.exists():
                print(f"失败 - 在 {self.original_docx} 中未找到原始 document.xml")
                return False

            try:
                import xml.etree.ElementTree as ET

                modified_tree = ET.parse(modified_file)
                modified_root = modified_tree.getroot()
                original_tree = ET.parse(original_file)
                original_root = original_tree.getroot()
            except ET.ParseError as e:
                print(f"失败 - 解析 XML 文件时出错: {e}")
                return False

            self._remove_all_tracked_changes(original_root)
            self._remove_all_tracked_changes(modified_root)

            modified_text = self._extract_text_content(modified_root)
            original_text = self._extract_text_content(original_root)

            if modified_text != original_text:
                error_message = self._generate_detailed_diff(
                    original_text, modified_text
                )
                print(error_message)
                return False

            if self.verbose:
                print("通过 - 所有更改都已正确追踪")
            return True

    def _generate_detailed_diff(self, original_text, modified_text):
        error_parts = [
            "失败 - 移除修订追踪后文档文本不匹配",
            "",
            "可能的原因:",
            "  1. 修改了其他作者 <w:ins> 或 <w:del> 标签内的文本",
            "  2. 未使用正确的修订追踪进行编辑",
            "",
        ]

        git_diff = self._get_git_word_diff(original_text, modified_text)
        if git_diff:
            error_parts.extend(["差异:", "============", git_diff])
        else:
            error_parts.append("无法生成单词差异（git 不可用）")

        return "\n".join(error_parts)

    def _get_git_word_diff(self, original_text, modified_text):
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                original_file = temp_path / "original.txt"
                modified_file = temp_path / "modified.txt"

                original_file.write_text(original_text, encoding="utf-8")
                modified_file.write_text(modified_text, encoding="utf-8")

                result = subprocess.run(
                    [
                        "git", "diff", "--word-diff=plain",
                        "--word-diff-regex=.", "-U0", "--no-index",
                        str(original_file), str(modified_file),
                    ],
                    capture_output=True, text=True,
                )

                if result.stdout.strip():
                    lines = result.stdout.split("\n")
                    content_lines = []
                    in_content = False
                    for line in lines:
                        if line.startswith("@@"):
                            in_content = True
                            continue
                        if in_content and line.strip():
                            content_lines.append(line)

                    if content_lines:
                        return "\n".join(content_lines)

        except (subprocess.CalledProcessError, FileNotFoundError, Exception):
            pass

        return None

    def _remove_all_tracked_changes(self, root):
        ins_tag = f"{{{self.namespaces['w']}}}ins"
        del_tag = f"{{{self.namespaces['w']}}}del"

        for parent in root.iter():
            to_remove = []
            for child in parent:
                if child.tag == ins_tag:
                    to_remove.append(child)
            for elem in to_remove:
                parent.remove(elem)

        deltext_tag = f"{{{self.namespaces['w']}}}delText"
        t_tag = f"{{{self.namespaces['w']}}}t"

        for parent in root.iter():
            to_process = []
            for child in parent:
                if child.tag == del_tag:
                    to_process.append((child, list(parent).index(child)))

            for del_elem, del_index in reversed(to_process):
                for elem in del_elem.iter():
                    if elem.tag == deltext_tag:
                        elem.tag = t_tag

                for child in reversed(list(del_elem)):
                    parent.insert(del_index, child)
                parent.remove(del_elem)

    def _extract_text_content(self, root):
        p_tag = f"{{{self.namespaces['w']}}}p"
        t_tag = f"{{{self.namespaces['w']}}}t"

        paragraphs = []
        for p_elem in root.findall(f".//{p_tag}"):
            text_parts = []
            for t_elem in p_elem.findall(f".//{t_tag}"):
                if t_elem.text:
                    text_parts.append(t_elem.text)
            paragraph_text = "".join(text_parts)
            if paragraph_text:
                paragraphs.append(paragraph_text)

        return "\n".join(paragraphs)


if __name__ == "__main__":
    raise RuntimeError("此模块不应直接运行。")
