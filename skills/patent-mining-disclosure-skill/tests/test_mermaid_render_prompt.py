"""mermaid_render：支持将图示改写为专利附图生图提示词 / 图片 API。"""
from __future__ import annotations

import base64
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import mermaid_render  # noqa: E402
from mermaid_render import (  # noqa: E402
    check_image_api_env,
    render_markdown_mermaid_image_api,
    render_markdown_mermaid_prompts,
)


_ONE_PIXEL_PNG = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMB"
    "/6X7qHcAAAAASUVORK5CYII="
)


def test_mermaid_prompt_mode_outputs_patent_style_prompt() -> None:
    md = """### 3.2 系统框图

```mermaid
flowchart TB
  A["采集模块"] --> B["处理模块"]
```
"""

    out, count = render_markdown_mermaid_prompts(md)

    assert count == 1
    assert "图示生成提示词（图示 1" in out
    assert "中国发明专利技术交底书 / 专利说明书附图" in out
    assert "白色背景，黑色或深灰色细线" in out
    assert "不要照片、3D、渐变、阴影" in out
    assert "A[\"采集模块\"] --> B[\"处理模块\"]" in out
    assert "```mermaid" not in out


def test_mermaid_prompt_mode_keeps_non_mermaid_content() -> None:
    md = "正文\n\n```python\nprint('x')\n```\n"
    out, count = render_markdown_mermaid_prompts(md)

    assert count == 0
    assert out == md


def test_mermaid_image_api_mode_writes_png_and_hidden_reference(
    tmp_path: Path,
    monkeypatch,
) -> None:
    calls: list[str] = []

    def fake_generate(prompt: str, png_path: Path, **kwargs) -> None:
        calls.append(prompt)
        png_path.parent.mkdir(parents=True, exist_ok=True)
        png_path.write_bytes(base64.b64decode(_ONE_PIXEL_PNG))

    monkeypatch.setattr(mermaid_render, "_generate_one_image_api", fake_generate)
    md = """## 附图说明

```mermaid
flowchart TB
  A["采集模块"] --> B["处理模块"]
```
"""

    out, ok, failed = render_markdown_mermaid_image_api(
        md,
        out_md_path=tmp_path / "out.md",
        assets_rel="mermaid_figures",
        api_key="test-key",
        base_url="https://example.test/v1",
        model="gpt-image-1",
        size="1536x1024",
    )

    assert ok == 1
    assert failed == 0
    assert calls and "中国发明专利技术交底书" in calls[0]
    assert "<!-- ![图示 1](mermaid_figures/fig_001.png) -->" in out
    assert (tmp_path / "mermaid_figures" / "fig_001.png").is_file()


def test_image_api_env_check_requires_base_url_and_key(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    args = mermaid_render.argparse.Namespace(
        image_api_base=None,
        image_api_key=None,
        image_model=None,
        image_size=None,
    )

    assert check_image_api_env(args) is False


def test_main_image_api_missing_env_exits_before_writing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    src = tmp_path / "draft.md"
    out = tmp_path / "out.md"
    src.write_text(
        "```mermaid\nflowchart LR\n  A[\"开始\"] --> B[\"结束\"]\n```\n",
        encoding="utf-8",
    )

    rc = mermaid_render.main(
        [
            "-i",
            str(src),
            "-o",
            str(out),
            "--diagram-mode",
            "image-api",
            "--no-math",
            "--no-docx",
        ]
    )

    assert rc == 2
    assert not out.exists()


def test_main_rejects_pdf_without_docx(tmp_path: Path) -> None:
    src = tmp_path / "draft.md"
    out = tmp_path / "out.md"
    src.write_text("正文\n", encoding="utf-8")

    try:
        mermaid_render.main(
            [
                "-i",
                str(src),
                "-o",
                str(out),
                "--no-docx",
                "--pdf",
            ]
        )
    except SystemExit as e:
        assert e.code == 2
    else:
        raise AssertionError("expected argparse SystemExit")


def test_main_pdf_runs_after_docx_success(tmp_path: Path, monkeypatch) -> None:
    src = tmp_path / "draft.md"
    out = tmp_path / "out.md"
    src.write_text("正文\n", encoding="utf-8")
    calls: list[tuple[Path, Path]] = []

    def fake_docx(out_md: Path, docx_out: Path) -> bool:
        docx_out.write_bytes(b"fake docx")
        return True

    def fake_pdf(docx_in: Path, pdf_out: Path) -> bool:
        calls.append((docx_in, pdf_out))
        pdf_out.write_bytes(b"fake pdf")
        return True

    monkeypatch.setattr(mermaid_render, "try_write_docx", fake_docx)
    monkeypatch.setattr(mermaid_render, "try_write_pdf", fake_pdf)

    rc = mermaid_render.main(
        [
            "-i",
            str(src),
            "-o",
            str(out),
            "--no-math",
            "--pdf",
        ]
    )

    assert rc == 0
    assert calls == [(out.with_suffix(".docx"), out.with_suffix(".pdf"))]
    assert out.with_suffix(".pdf").is_file()
