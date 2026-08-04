"""md_to_docx：已渲染 mermaid 图进入 Word，源码不进入正文。"""
from __future__ import annotations

import base64
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from md_to_docx import convert_md_to_docx  # noqa: E402


_ONE_PIXEL_PNG = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMB"
    "/6X7qHcAAAAASUVORK5CYII="
)


def _save_docx_from_md(md: str, base_dir: Path, out_path: Path) -> str:
    doc = convert_md_to_docx(md, base_dir=base_dir)
    doc.save(out_path)
    with zipfile.ZipFile(out_path) as zf:
        return zf.read("word/document.xml").decode("utf-8")


def test_rendered_mermaid_embeds_image_without_source(tmp_path: Path) -> None:
    figures = tmp_path / "mermaid_figures"
    figures.mkdir()
    (figures / "fig_001.png").write_bytes(base64.b64decode(_ONE_PIXEL_PNG))
    md = """## 3.2 系统框图

```mermaid
flowchart TB
  A["采集模块"] --> B["处理模块"]
```
<!-- ![图示 1](mermaid_figures/fig_001.png) -->

正文继续。
"""

    out_path = tmp_path / "out.docx"
    xml = _save_docx_from_md(md, tmp_path, out_path)

    assert "flowchart TB" not in xml
    assert "采集模块" not in xml
    assert "<w:drawing>" in xml
    with zipfile.ZipFile(out_path) as zf:
        assert any(name.startswith("word/media/") for name in zf.namelist())


def test_missing_rendered_mermaid_image_keeps_source_as_fallback(tmp_path: Path) -> None:
    md = """```mermaid
flowchart LR
  A["开始"] --> B["结束"]
```
<!-- ![图示 1](mermaid_figures/missing.png) -->
"""

    xml = _save_docx_from_md(md, tmp_path, tmp_path / "fallback.docx")

    assert "flowchart LR" in xml
    assert "开始" in xml
    assert "<w:drawing>" not in xml
