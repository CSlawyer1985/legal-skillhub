#!/usr/bin/env python3
"""
将 Markdown 中的 **mermaid** 围栏与（默认）**LaTeX 公式** 转为 PNG，或将 mermaid
围栏改写为专利附图风格的生图提示词 / 调用 OpenAI-compatible 图片接口自动生图；
再写定稿 `.md`，并可生成 Word；可选在 Word 成功后继续转 PDF。

**公式**：默认先调用同目录 **`math_render.py`**（``matplotlib``；``--no-math`` 可跳过）。
**Mermaid** 默认逐块渲染为 PNG，**保留** `` ```mermaid`` … `` ``` `` 源码，并在其后追加 HTML 注释
``<!-- ![图示](相对路径) -->``（预览不显示图），便于 ``md_to_docx.py`` 将图嵌入 Word（Word **仅**嵌 PNG，不写 mermaid 代码块）。
使用 ``--diagram-mode prompt`` 时，mermaid 围栏会改写为专利附图风格提示词，由用户自行复制到 gpt-image 等工具生图后替换。
使用 ``--diagram-mode image-api`` 时，脚本会调用 OpenAI-compatible ``/images/generations`` 接口自动生成图片并嵌入 Word。

**Mermaid 渲染后端（``mmdc``）**检测顺序见 ``_find_mmdc_invocation``：
1. ``tools/node_modules``（``npm install`` 官方 ``@mermaid-js/mermaid-cli``）；
2. **PATH 上的 ``mmdc``**（通常为 ``npm install -g @mermaid-js/mermaid-cli``）；
3. **Node.js + npx** 临时拉取 ``@mermaid-js/mermaid-cli``（无本地安装时）。

交底书中的方法流程图、系统结构图和关键子流程图均使用 fenced mermaid；**不要** ASCII「文字箭头」流程图或框图。

**PNG 降级**：某一围栏 ``mmdc`` 生图失败时**不中断**：该处**保留原** `` ```mermaid`` … `` ``` `` 围栏；其余块照常渲染。仍写出 .md 并**照常尝试** ``md_to_docx.py``（Word 中失败块以代码块形式出现）。

**清晰度**：默认对 ``mmdc`` 传入较大视口（``-w`` / ``-H``）与 ``-s 2``（Puppeteer 像素密度），PNG 在 Word 中按约 5.5 英寸宽嵌入时更锐利。可用 ``--mmdc-scale 3`` 等进一步提高（文件更大）。

用法：
  python tools/mermaid_render.py -i draft.md -o disclosure.md
  # 默认在同目录生成 disclosure.docx；失败时 stderr 会给出可复制的 md_to_docx 命令
  python tools/mermaid_render.py -i draft.md -o out/disclosure.md --docx out/custom.docx
  python tools/mermaid_render.py -i draft.md -o disclosure.md --pdf   # 同名 Word + PDF
  python tools/mermaid_render.py -i draft.md -o disclosure.md --no-docx   # 仅 Markdown
  python tools/mermaid_render.py -i draft.md -o disclosure.md --diagram-mode prompt
  python tools/mermaid_render.py --check-image-env
  OPENAI_API_KEY=... OPENAI_BASE_URL=... python tools/mermaid_render.py -i draft.md -o disclosure.md --diagram-mode image-api

写出 .md 后**默认**调用 ``md_to_docx.py``；传入 ``--pdf`` 时，在 Word 成功后尝试调用
LibreOffice / soffice 转 PDF。Word 或 PDF 失败不导致进程失败（退出码 0），并提示手动转换。
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path


def _local_mmdc() -> tuple[list[str], bool] | None:
    """``tools/npm install`` 后可用 ``node_modules/.bin/mmdc``，避免每次 npx 拉包。"""
    here = Path(__file__).resolve().parent
    if sys.platform == "win32":
        cand = here / "node_modules" / ".bin" / "mmdc.cmd"
    else:
        cand = here / "node_modules" / ".bin" / "mmdc"
    if cand.is_file():
        return [str(cand)], False
    return None


def _find_mmdc_invocation() -> tuple[list[str], bool]:
    """
    返回 (argv 前缀, use_shell)。
    Windows 上 npx 常为 .ps1，无独立 .exe，需 shell=True 调用 ``npx ...``。
    PATH 中的 ``mmdc`` 一般为 npm 全局安装的官方 CLI。
    """
    local = _local_mmdc()
    if local:
        return local
    mmdc = shutil.which("mmdc")
    if mmdc and Path(mmdc).suffix.lower() not in (".ps1",):
        return [mmdc], False
    if sys.platform == "win32":
        return ["npx", "-y", "@mermaid-js/mermaid-cli"], True
    return ["npx", "-y", "@mermaid-js/mermaid-cli"], False


def _mmdc_extra_args(
    *,
    scale: float,
    width: int,
    height: int,
) -> list[str]:
    """传给 mmdc 的分辨率相关参数（-s 为 Puppeteer deviceScaleFactor，显著影响 PNG 清晰度）。"""
    return [
        "-s",
        str(scale),
        "-w",
        str(width),
        "-H",
        str(height),
    ]


def _render_one_mermaid(
    mermaid_source: str,
    png_path: Path,
    mmdc_base: list[str],
    *,
    use_shell: bool,
    scale: float,
    width: int,
    height: int,
) -> None:
    png_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".mmd",
        delete=False,
        encoding="utf-8",
    ) as tmp:
        tmp.write(mermaid_source.strip() + "\n")
        tmp_path = Path(tmp.name)
    try:
        extra = _mmdc_extra_args(scale=scale, width=width, height=height)
        if use_shell:
            parts = [
                *mmdc_base,
                "-i",
                str(tmp_path),
                "-o",
                str(png_path),
                "-b",
                "white",
                *extra,
            ]
            cmd = " ".join(shlex.quote(p) for p in parts)
            r = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=180,
            )
        else:
            cmd = [
                *mmdc_base,
                "-i",
                str(tmp_path),
                "-o",
                str(png_path),
                "-b",
                "white",
                *extra,
            ]
            r = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=180,
            )
        if r.returncode != 0:
            err = (r.stderr or r.stdout or "").strip()
            raise RuntimeError(f"mmdc 失败 (exit {r.returncode}): {err[:2000]}")
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass


_MMD_START = re.compile(r"^```mermaid\s*$", re.IGNORECASE)
_MMD_END = re.compile(r"^```\s*$")
_MERMAID_HIDDEN_COMMENT_RE = re.compile(
    r"<!--\s*!\[([^\]]*)\]\(([^)]+)\)\s*-->"
)
_PROMPT_HEADING_RE = re.compile(r"^\*\*图示生成提示词（图示\s+\d+", re.IGNORECASE)


def _patent_diagram_prompt(mermaid_source: str, index: int) -> str:
    """生成适合 gpt-image 等工具的专利附图提示词。"""
    source = mermaid_source.strip()
    return (
        f"**图示生成提示词（图示 {index}，请用 gpt-image 等工具生成后替换本段）：**\n\n"
        "```text\n"
        "请生成一张用于中国发明专利技术交底书 / 专利说明书附图的技术示意图，"
        "根据下方结构关系绘制系统框图或流程图。\n"
        "风格要求：白色背景，黑色或深灰色细线，二维平面线稿，矩形或圆角矩形节点，"
        "箭头清晰，布局规整，层级分明，留白充足，适合插入 Word 文档；"
        "不要照片、3D、渐变、阴影、装饰图标、复杂纹理、品牌标识或卡通风格。\n"
        "文字要求：使用简体中文，节点文字简短清晰，尽量沿用结构中的模块名 / 步骤名，"
        "不要把 Mermaid 语法字符、代码符号或反引号画进图片。\n"
        "画面规格：横向 16:10 或接近 A4 横版，高分辨率，线条和文字在打印后仍可辨认。\n\n"
        "结构依据（只按拓扑关系绘制，不要原样显示为代码）：\n"
        f"{source}\n"
        "```\n"
    )


def _patent_diagram_prompt_text(mermaid_source: str) -> str:
    """只返回适合图片模型的提示词文本（不含 Markdown 标题和代码围栏）。"""
    source = mermaid_source.strip()
    return (
        "请生成一张用于中国发明专利技术交底书 / 专利说明书附图的技术示意图，"
        "根据下方结构关系绘制系统框图或流程图。\n"
        "风格要求：白色背景，黑色或深灰色细线，二维平面线稿，矩形或圆角矩形节点，"
        "箭头清晰，布局规整，层级分明，留白充足，适合插入 Word 文档；"
        "不要照片、3D、渐变、阴影、装饰图标、复杂纹理、品牌标识或卡通风格。\n"
        "文字要求：使用简体中文，节点文字简短清晰，尽量沿用结构中的模块名 / 步骤名，"
        "不要把 Mermaid 语法字符、代码符号或反引号画进图片。\n"
        "画面规格：横向 16:10 或接近 A4 横版，高分辨率，线条和文字在打印后仍可辨认。\n\n"
        "结构依据（只按拓扑关系绘制，不要原样显示为代码）：\n"
        f"{source}\n"
    )


def _normalize_base_url(base_url: str | None) -> str:
    raw = (base_url or os.environ.get("OPENAI_BASE_URL") or "").strip()
    return raw.rstrip("/")


def _images_generations_url(base_url: str) -> str:
    if base_url.rstrip("/").endswith("/images/generations"):
        return base_url.rstrip("/")
    return base_url.rstrip("/") + "/images/generations"


def _image_api_env_values(args: argparse.Namespace) -> dict[str, str | None]:
    return {
        "OPENAI_API_KEY": args.image_api_key or os.environ.get("OPENAI_API_KEY"),
        "OPENAI_BASE_URL": args.image_api_base or os.environ.get("OPENAI_BASE_URL"),
        "OPENAI_IMAGE_MODEL": args.image_model or os.environ.get("OPENAI_IMAGE_MODEL") or "gpt-image-1",
        "OPENAI_IMAGE_SIZE": args.image_size or os.environ.get("OPENAI_IMAGE_SIZE") or "1536x1024",
    }


def _print_image_env_help(missing: list[str]) -> None:
    shell_name = Path(os.environ.get("SHELL", "")).name
    is_windows = os.name == "nt"
    print("自动生图模式缺少必要环境变量，尚未生成文档。", file=sys.stderr)
    print("缺少：" + "、".join(missing), file=sys.stderr)
    print("", file=sys.stderr)
    if is_windows:
        print("PowerShell 示例：", file=sys.stderr)
        print('  $env:OPENAI_BASE_URL="https://你的图片接口/v1"', file=sys.stderr)
        print('  $env:OPENAI_API_KEY="你的 key"', file=sys.stderr)
        print('  $env:OPENAI_IMAGE_MODEL="gpt-image-1"', file=sys.stderr)
        print('  $env:OPENAI_IMAGE_SIZE="1536x1024"', file=sys.stderr)
    elif shell_name in ("fish",):
        print("fish 示例：", file=sys.stderr)
        print('  set -x OPENAI_BASE_URL "https://你的图片接口/v1"', file=sys.stderr)
        print('  set -x OPENAI_API_KEY "你的 key"', file=sys.stderr)
        print('  set -x OPENAI_IMAGE_MODEL "gpt-image-1"', file=sys.stderr)
        print('  set -x OPENAI_IMAGE_SIZE "1536x1024"', file=sys.stderr)
    else:
        print("zsh / bash 示例：", file=sys.stderr)
        print('  export OPENAI_BASE_URL="https://你的图片接口/v1"', file=sys.stderr)
        print('  export OPENAI_API_KEY="你的 key"', file=sys.stderr)
        print('  export OPENAI_IMAGE_MODEL="gpt-image-1"', file=sys.stderr)
        print('  export OPENAI_IMAGE_SIZE="1536x1024"', file=sys.stderr)
    print("", file=sys.stderr)
    print("设置后重新运行原命令，或用 --image-api-base / --image-api-key 显式传入。", file=sys.stderr)


def check_image_api_env(args: argparse.Namespace) -> bool:
    values = _image_api_env_values(args)
    missing = [
        name
        for name in ("OPENAI_BASE_URL", "OPENAI_API_KEY")
        if not (values.get(name) or "").strip()
    ]
    if missing:
        _print_image_env_help(missing)
        return False
    redacted_key = (values["OPENAI_API_KEY"] or "")[:6] + "..."
    print("自动生图环境检查通过：", file=sys.stderr)
    print(f"  OPENAI_BASE_URL={values['OPENAI_BASE_URL']}", file=sys.stderr)
    print(f"  OPENAI_API_KEY={redacted_key}", file=sys.stderr)
    print(f"  OPENAI_IMAGE_MODEL={values['OPENAI_IMAGE_MODEL']}", file=sys.stderr)
    print(f"  OPENAI_IMAGE_SIZE={values['OPENAI_IMAGE_SIZE']}", file=sys.stderr)
    return True


def _extract_image_from_response(data: dict) -> tuple[bytes, str]:
    """
    兼容 OpenAI Image API 与常见 OpenAI-compatible 响应：
    - {"data": [{"b64_json": "..."}]}
    - {"data": [{"url": "https://..."}]}
    - Responses API 风格的 output / image_generation_call.result
    """
    candidates: list[dict | str] = []
    raw_data = data.get("data")
    if isinstance(raw_data, list):
        candidates.extend(raw_data)
    raw_output = data.get("output")
    if isinstance(raw_output, list):
        candidates.extend(raw_output)

    for item in candidates:
        if isinstance(item, dict):
            b64 = item.get("b64_json") or item.get("result")
            if isinstance(b64, str) and b64.strip():
                try:
                    return base64.b64decode(b64), "base64"
                except Exception as e:
                    raise RuntimeError(f"图片接口返回了无法解码的 base64：{e}") from e
            url = item.get("url")
            if isinstance(url, str) and url.startswith(("http://", "https://")):
                with urllib.request.urlopen(url, timeout=120) as r:
                    return r.read(), url

    b64 = data.get("b64_json") or data.get("result")
    if isinstance(b64, str) and b64.strip():
        try:
            return base64.b64decode(b64), "base64"
        except Exception as e:
            raise RuntimeError(f"图片接口返回了无法解码的 base64：{e}") from e
    url = data.get("url")
    if isinstance(url, str) and url.startswith(("http://", "https://")):
        with urllib.request.urlopen(url, timeout=120) as r:
            return r.read(), url

    raise RuntimeError("图片接口响应中未找到 data[0].b64_json、data[0].url 或 output[].result")


def _generate_one_image_api(
    prompt: str,
    png_path: Path,
    *,
    api_key: str,
    base_url: str,
    model: str,
    size: str,
    quality: str | None,
    output_format: str | None,
    timeout: int,
) -> None:
    if not api_key:
        raise RuntimeError("缺少 API key：请设置 OPENAI_API_KEY 或传入 --image-api-key")
    png_path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, object] = {
        "model": model,
        "prompt": prompt,
        "n": 1,
        "size": size,
    }
    if quality:
        payload["quality"] = quality
    if output_format:
        payload["output_format"] = output_format

    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        _images_generations_url(base_url),
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"图片接口 HTTP {e.code}: {detail[:1200]}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"图片接口请求失败：{e}") from e

    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception as e:
        raise RuntimeError(f"图片接口返回非 JSON 响应：{raw[:200]!r}") from e

    image_bytes, source = _extract_image_from_response(data)
    if not image_bytes:
        raise RuntimeError("图片接口返回空图片")
    png_path.write_bytes(image_bytes)
    print(
        f"[mermaid_render] 图片接口已生成 {png_path.name}（来源：{source}）",
        file=sys.stderr,
    )


def render_markdown_mermaid_prompts(md_text: str) -> tuple[str, int]:
    """
    将 mermaid 围栏改写为可复制到 gpt-image 等工具的专利附图提示词。
    返回 (新 markdown 全文, 提示词数量)。
    """
    lines = md_text.splitlines(keepends=True)
    out: list[str] = []
    i = 0
    count = 0

    while i < len(lines):
        line = lines[i]
        if _MMD_START.match(line):
            i += 1
            body: list[str] = []
            while i < len(lines) and not _MMD_END.match(lines[i]):
                body.append(lines[i])
                i += 1
            if i < len(lines):
                i += 1

            # 已生成过提示词时保持幂等，不重复追加。
            j = i
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            if j < len(lines) and _PROMPT_HEADING_RE.match(lines[j].strip()):
                out.append(line)
                out.extend(body)
                out.append("```\n")
                while i < len(lines):
                    out.append(lines[i])
                    i += 1
                continue

            count += 1
            out.append(_patent_diagram_prompt("".join(body), count))
            continue

        out.append(line)
        i += 1

    return "".join(out), count


def _is_mermaid_figure_comment(alt: str, src: str) -> bool:
    s = src.strip().replace("\\", "/")
    if "mermaid_figures" in s:
        return True
    a = alt.strip()
    return a.startswith("图示") or a.startswith("图 ")


def render_markdown_mermaid(
    md_text: str,
    *,
    out_md_path: Path,
    assets_rel: str,
    mmdc_scale: float = 2.0,
    mmdc_width: int = 1400,
    mmdc_height: int = 1050,
) -> tuple[str, int, int]:
    """
    返回 (新 markdown 全文, 成功转为 PNG 的块数, 生图失败而保留围栏的块数)。
    资源目录为 out_md_path.parent / assets_rel。
    失败的块原样写回 `` ```mermaid`` … `` ``` ``，不抛错。
    成功的块写回围栏源码 + 紧随其后的 ``<!-- ![图示](…) -->``（与 ``math_render`` 保留 LaTeX 原文同理）。
    若围栏后已有 mermaid 图示注释，则视为已处理，原样跳过（可重复跑脚本）。
    """
    lines = md_text.splitlines(keepends=True)
    out: list[str] = []
    i = 0
    ok = 0
    failed = 0
    block_idx = 0
    assets_dir = out_md_path.parent / assets_rel
    mmdc_base, use_shell = _find_mmdc_invocation()

    while i < len(lines):
        line = lines[i]
        if _MMD_START.match(line):
            fence_open = line
            i += 1
            body: list[str] = []
            while i < len(lines) and not _MMD_END.match(lines[i]):
                body.append(lines[i])
                i += 1
            closing = lines[i] if i < len(lines) else "```\n"
            if i < len(lines):
                i += 1

            # 已定稿：围栏 + 图示注释，不重复渲染
            j = i
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            if j < len(lines):
                cm = _MERMAID_HIDDEN_COMMENT_RE.match(lines[j].strip())
                if cm and _is_mermaid_figure_comment(cm.group(1), cm.group(2)):
                    out.append(fence_open)
                    out.extend(body)
                    if not closing.endswith("\n"):
                        closing = closing + "\n"
                    out.append(closing)
                    while i < j:
                        out.append(lines[i])
                        i += 1
                    out.append(lines[i])
                    i += 1
                    ok += 1
                    continue

            block_idx += 1
            fname = f"fig_{ok + 1:03d}.png"
            png_path = assets_dir / fname
            try:
                _render_one_mermaid(
                    "".join(body),
                    png_path,
                    mmdc_base,
                    use_shell=use_shell,
                    scale=mmdc_scale,
                    width=mmdc_width,
                    height=mmdc_height,
                )
            except Exception as e:
                failed += 1
                print(
                    f"[mermaid_render] 第 {block_idx} 个 mermaid 围栏生图失败（已保留源码）：{e}",
                    file=sys.stderr,
                )
                out.append(fence_open)
                out.extend(body)
                if not closing.endswith("\n"):
                    closing = closing + "\n"
                out.append(closing)
                continue
            ok += 1
            rel = f"{assets_rel.strip('/')}/{fname}".replace("\\", "/")
            out.append(fence_open)
            out.extend(body)
            if not closing.endswith("\n"):
                closing = closing + "\n"
            out.append(closing)
            out.append(f"<!-- ![图示 {ok}]({rel}) -->\n")
            continue
        out.append(line)
        i += 1

    return "".join(out), ok, failed


def render_markdown_mermaid_image_api(
    md_text: str,
    *,
    out_md_path: Path,
    assets_rel: str,
    api_key: str,
    base_url: str,
    model: str,
    size: str,
    quality: str | None = None,
    output_format: str | None = "png",
    timeout: int = 300,
) -> tuple[str, int, int]:
    """
    将 mermaid 围栏转换为专利附图提示词后调用 OpenAI-compatible 图片接口生成图片。
    成功时写回围栏源码 + 隐藏图片注释，便于 Word 只嵌图片；失败块保留 mermaid 源码。
    """
    lines = md_text.splitlines(keepends=True)
    out: list[str] = []
    i = 0
    ok = 0
    failed = 0
    block_idx = 0
    assets_dir = out_md_path.parent / assets_rel

    while i < len(lines):
        line = lines[i]
        if _MMD_START.match(line):
            fence_open = line
            i += 1
            body: list[str] = []
            while i < len(lines) and not _MMD_END.match(lines[i]):
                body.append(lines[i])
                i += 1
            closing = lines[i] if i < len(lines) else "```\n"
            if i < len(lines):
                i += 1

            # 已定稿：围栏 + 图示注释，不重复调用图片接口。
            j = i
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            if j < len(lines):
                cm = _MERMAID_HIDDEN_COMMENT_RE.match(lines[j].strip())
                if cm and _is_mermaid_figure_comment(cm.group(1), cm.group(2)):
                    out.append(fence_open)
                    out.extend(body)
                    if not closing.endswith("\n"):
                        closing = closing + "\n"
                    out.append(closing)
                    while i < j:
                        out.append(lines[i])
                        i += 1
                    out.append(lines[i])
                    i += 1
                    ok += 1
                    continue

            block_idx += 1
            fname = f"fig_{ok + 1:03d}.png"
            png_path = assets_dir / fname
            prompt = _patent_diagram_prompt_text("".join(body))
            try:
                _generate_one_image_api(
                    prompt,
                    png_path,
                    api_key=api_key,
                    base_url=base_url,
                    model=model,
                    size=size,
                    quality=quality,
                    output_format=output_format,
                    timeout=timeout,
                )
            except Exception as e:
                failed += 1
                print(
                    f"[mermaid_render] 第 {block_idx} 个 mermaid 围栏调用图片接口失败（已保留源码）：{e}",
                    file=sys.stderr,
                )
                out.append(fence_open)
                out.extend(body)
                if not closing.endswith("\n"):
                    closing = closing + "\n"
                out.append(closing)
                continue

            ok += 1
            rel = f"{assets_rel.strip('/')}/{fname}".replace("\\", "/")
            out.append(fence_open)
            out.extend(body)
            if not closing.endswith("\n"):
                closing = closing + "\n"
            out.append(closing)
            out.append(f"<!-- ![图示 {ok}]({rel}) -->\n")
            continue

        out.append(line)
        i += 1

    return "".join(out), ok, failed


def _print_manual_docx_hint(out_md: Path, docx_out: Path, base_dir: Path, md_script: Path) -> None:
    print(
        "提示：可手动将上述 Markdown 转为 Word（需已 pip install -r requirements.txt）：",
        file=sys.stderr,
    )
    if md_script.is_file():
        parts = [
            sys.executable,
            str(md_script),
            "-i",
            str(out_md),
            "-o",
            str(docx_out),
            "--base-dir",
            str(base_dir),
        ]
        print("  " + " ".join(shlex.quote(p) for p in parts), file=sys.stderr)
    else:
        print(
            "  python tools/md_to_docx.py -i <上述.md> -o <输出.docx> --base-dir <.md 所在目录>",
            file=sys.stderr,
        )


def try_write_docx(out_md: Path, docx_out: Path) -> bool:
    """
    调用同目录下的 md_to_docx.py。成功返回 True；失败打印警告与手动命令，返回 False。
    """
    tools_dir = Path(__file__).resolve().parent
    md_script = tools_dir / "md_to_docx.py"
    base_dir = out_md.parent
    docx_out.parent.mkdir(parents=True, exist_ok=True)

    if not md_script.is_file():
        print("警告：未找到 md_to_docx.py，跳过 Word。", file=sys.stderr)
        _print_manual_docx_hint(out_md, docx_out, base_dir, md_script)
        return False

    cmd = [
        sys.executable,
        str(md_script),
        "-i",
        str(out_md),
        "-o",
        str(docx_out),
        "--base-dir",
        str(base_dir),
    ]
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        print("警告：生成 Word 超时（300s）。", file=sys.stderr)
        _print_manual_docx_hint(out_md, docx_out, base_dir, md_script)
        return False
    except OSError as e:
        print(f"警告：无法启动 md_to_docx：{e}", file=sys.stderr)
        _print_manual_docx_hint(out_md, docx_out, base_dir, md_script)
        return False

    if r.returncode != 0:
        print(f"警告：md_to_docx 失败（退出码 {r.returncode}）。", file=sys.stderr)
        err = (r.stderr or r.stdout or "").strip()
        if err:
            print(err[:2000], file=sys.stderr)
        _print_manual_docx_hint(out_md, docx_out, base_dir, md_script)
        return False

    print(f"已写入 Word: {docx_out}", file=sys.stderr)
    return True


def _find_soffice_invocation() -> list[str] | None:
    """查找 LibreOffice / soffice；优先 PATH，再兼容 macOS 常见安装位置。"""
    for name in ("soffice", "libreoffice"):
        exe = shutil.which(name)
        if exe:
            return [exe]
    mac_candidates = [
        Path("/Applications/LibreOffice.app/Contents/MacOS/soffice"),
        Path.home() / "Applications/LibreOffice.app/Contents/MacOS/soffice",
    ]
    for cand in mac_candidates:
        if cand.is_file():
            return [str(cand)]
    return None


def _print_manual_pdf_hint(docx_in: Path, pdf_out: Path) -> None:
    print("提示：可手动将 Word 转为 PDF。推荐安装 LibreOffice 后执行：", file=sys.stderr)
    print(
        "  "
        + " ".join(
            shlex.quote(p)
            for p in [
                "soffice",
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(pdf_out.parent),
                str(docx_in),
            ]
        ),
        file=sys.stderr,
    )


def try_write_pdf(docx_in: Path, pdf_out: Path) -> bool:
    """
    调用 LibreOffice / soffice 将 docx 转 PDF。成功返回 True；失败打印提示，返回 False。
    """
    if not docx_in.is_file():
        print(f"警告：找不到 Word 文件，跳过 PDF：{docx_in}", file=sys.stderr)
        _print_manual_pdf_hint(docx_in, pdf_out)
        return False

    soffice = _find_soffice_invocation()
    if not soffice:
        print("警告：未找到 LibreOffice / soffice，跳过 PDF。", file=sys.stderr)
        _print_manual_pdf_hint(docx_in, pdf_out)
        return False

    pdf_out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        *soffice,
        "--headless",
        "--convert-to",
        "pdf",
        "--outdir",
        str(pdf_out.parent),
        str(docx_in),
    ]
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=240,
        )
    except subprocess.TimeoutExpired:
        print("警告：Word 转 PDF 超时（240s）。", file=sys.stderr)
        _print_manual_pdf_hint(docx_in, pdf_out)
        return False
    except OSError as e:
        print(f"警告：无法启动 LibreOffice / soffice：{e}", file=sys.stderr)
        _print_manual_pdf_hint(docx_in, pdf_out)
        return False

    generated = pdf_out.parent / (docx_in.stem + ".pdf")
    if r.returncode != 0 or not generated.is_file():
        print(f"警告：Word 转 PDF 失败（退出码 {r.returncode}）。", file=sys.stderr)
        err = (r.stderr or r.stdout or "").strip()
        if err:
            print(err[:2000], file=sys.stderr)
        _print_manual_pdf_hint(docx_in, pdf_out)
        return False

    if generated.resolve() != pdf_out.resolve():
        try:
            generated.replace(pdf_out)
        except OSError as e:
            print(f"警告：PDF 已生成但无法移动到目标路径：{e}", file=sys.stderr)
            return False

    print(f"已写入 PDF: {pdf_out}", file=sys.stderr)
    return True


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Markdown 内 mermaid 围栏 → PNG 或专利附图提示词，默认再生成同名 Word"
    )
    p.add_argument("-i", "--input", type=Path, help="含 mermaid 围栏的 .md")
    p.add_argument("-o", "--output", type=Path, help="输出 .md（图片引用）")
    p.add_argument(
        "--check-image-env",
        action="store_true",
        help="仅检查自动生图所需环境变量 / 参数，不生成文档",
    )
    p.add_argument(
        "--assets-dir",
        default="mermaid_figures",
        help="mermaid 生成 PNG 的相对子目录（默认 mermaid_figures）",
    )
    p.add_argument(
        "--docx",
        type=Path,
        default=None,
        metavar="PATH",
        help="输出 .docx 路径（默认与 -o 同主文件名、扩展名 .docx）",
    )
    p.add_argument(
        "--no-docx",
        action="store_true",
        help="不生成 Word，仅输出处理后的 Markdown",
    )
    p.add_argument(
        "--pdf",
        action="store_true",
        help="Word 成功后继续转同名 PDF（需 LibreOffice / soffice）",
    )
    p.add_argument(
        "--pdf-path",
        type=Path,
        default=None,
        metavar="PATH",
        help="输出 .pdf 路径；传入后等同启用 --pdf",
    )
    p.add_argument(
        "--diagram-mode",
        choices=("png", "prompt", "image-api"),
        default="png",
        help="mermaid 图示处理方式：png=本地 mmdc 渲染 PNG；prompt=改写为专利附图风格生图提示词；image-api=调用 OpenAI-compatible 图片接口自动生图（默认 png）",
    )
    p.add_argument(
        "--image-api-key",
        default=None,
        help="图片接口 API key；默认读取 OPENAI_API_KEY。建议优先用环境变量，避免 key 留在 shell history。",
    )
    p.add_argument(
        "--image-api-base",
        default=None,
        help="图片接口 base URL；默认读取 OPENAI_BASE_URL。可直接传到 /images/generations。",
    )
    p.add_argument(
        "--image-model",
        default=None,
        help="图片模型；默认读取 OPENAI_IMAGE_MODEL，否则 gpt-image-1。",
    )
    p.add_argument(
        "--image-size",
        default=None,
        help="图片尺寸；默认读取 OPENAI_IMAGE_SIZE，否则 1536x1024。",
    )
    p.add_argument(
        "--image-quality",
        default=None,
        help="图片质量参数；默认读取 OPENAI_IMAGE_QUALITY。为空则不发送。",
    )
    p.add_argument(
        "--image-output-format",
        default=None,
        help="图片输出格式；默认读取 OPENAI_IMAGE_OUTPUT_FORMAT，否则 png。若兼容接口不支持，可传空字符串。",
    )
    p.add_argument(
        "--image-timeout",
        type=int,
        default=300,
        help="图片接口请求超时秒数（默认 300）",
    )
    p.add_argument(
        "--no-math",
        action="store_true",
        help="不渲染 LaTeX 公式（默认先 math_render 再 mermaid）",
    )
    p.add_argument(
        "--math-assets-dir",
        default="math_figures",
        help="公式 PNG 相对 -o 输出 .md 的子目录（默认 math_figures）",
    )
    p.add_argument(
        "--mmdc-scale",
        type=float,
        default=2.0,
        metavar="N",
        help="mmdc -s：Puppeteer 缩放（默认 2，约 2 倍像素密度；越大越清晰但文件更大）",
    )
    p.add_argument(
        "--mmdc-width",
        type=int,
        default=1400,
        metavar="PX",
        help="mmdc -w：渲染视口宽度像素（默认 1400，复杂 flowchart 不易裁切）",
    )
    p.add_argument(
        "--mmdc-height",
        type=int,
        default=1050,
        metavar="PX",
        help="mmdc -H：渲染视口高度像素（默认 1050）",
    )
    args = p.parse_args(argv)
    if args.check_image_env:
        return 0 if check_image_api_env(args) else 2
    if args.input is None or args.output is None:
        p.error("除 --check-image-env 外，必须同时提供 -i/--input 与 -o/--output")
    if args.no_docx and (args.pdf or args.pdf_path is not None):
        p.error("PDF 需要先生成 Word；不能同时使用 --no-docx 与 --pdf/--pdf-path")
    if args.mmdc_scale <= 0:
        print("错误：--mmdc-scale 须为正数", file=sys.stderr)
        return 1
    if args.mmdc_width < 400 or args.mmdc_height < 400:
        print("错误：--mmdc-width / --mmdc-height 建议不小于 400", file=sys.stderr)
        return 1

    in_path = args.input.resolve()
    if not in_path.is_file():
        print(f"错误：找不到输入 {in_path}", file=sys.stderr)
        return 1

    out_path = args.output.resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if args.diagram_mode == "image-api" and not check_image_api_env(args):
        return 2

    try:
        md = in_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        md = in_path.read_text(encoding="utf-8", errors="replace")

    math_ok = math_fail = 0
    if not getattr(args, "no_math", False):
        try:
            from math_render import render_markdown_math

            md, math_ok, math_fail = render_markdown_math(
                md,
                out_md_path=out_path,
                assets_rel=getattr(args, "math_assets_dir", "math_figures"),
            )
            if math_ok or math_fail:
                parts_m = [f"公式：{math_ok} 处已转为 PNG"]
                if math_fail:
                    parts_m.append(f"，{math_fail} 处失败已保留原文")
                print("[mermaid_render] " + "".join(parts_m), file=sys.stderr)
        except ImportError:
            print(
                "[mermaid_render] 未安装 matplotlib，跳过公式渲染（pip install matplotlib）",
                file=sys.stderr,
            )

    if args.diagram_mode == "prompt":
        new_md, n_prompt = render_markdown_mermaid_prompts(md)
        out_path.write_text(new_md, encoding="utf-8")
        print(
            f"已写入 {out_path}（mermaid：{n_prompt} 处已改写为专利附图生图提示词）",
            file=sys.stderr,
        )
    elif args.diagram_mode == "image-api":
        values = _image_api_env_values(args)
        api_key = (values["OPENAI_API_KEY"] or "").strip()
        base_url = _normalize_base_url(values["OPENAI_BASE_URL"])
        model = values["OPENAI_IMAGE_MODEL"] or "gpt-image-1"
        size = values["OPENAI_IMAGE_SIZE"] or "1536x1024"
        quality = args.image_quality
        if quality is None:
            quality = os.environ.get("OPENAI_IMAGE_QUALITY")
        output_format = args.image_output_format
        if output_format is None:
            output_format = os.environ.get("OPENAI_IMAGE_OUTPUT_FORMAT", "png")
        if output_format == "":
            output_format = None
        new_md, n_ok, n_fail = render_markdown_mermaid_image_api(
            md,
            out_md_path=out_path,
            assets_rel=args.assets_dir.strip("/\\") or "mermaid_figures",
            api_key=api_key,
            base_url=base_url,
            model=model,
            size=size,
            quality=quality,
            output_format=output_format,
            timeout=args.image_timeout,
        )
        out_path.write_text(new_md, encoding="utf-8")
        parts = [f"已写入 {out_path}（mermaid：{n_ok} 处已通过图片接口生成 PNG"]
        if n_fail:
            parts.append(f"，{n_fail} 处失败已保留 fenced 源码")
        parts.append("）")
        print("".join(parts), file=sys.stderr)
        if n_fail:
            print(
                "[mermaid_render] 已继续生成 Markdown"
                + (" 并将尝试 Word" if not args.no_docx else "")
                + "；请检查图片接口站点、key、模型或额度后重跑本脚本。",
                file=sys.stderr,
            )
    else:
        new_md, n_ok, n_fail = render_markdown_mermaid(
            md,
            out_md_path=out_path,
            assets_rel=args.assets_dir.strip("/\\") or "mermaid_figures",
            mmdc_scale=args.mmdc_scale,
            mmdc_width=args.mmdc_width,
            mmdc_height=args.mmdc_height,
        )

        out_path.write_text(new_md, encoding="utf-8")
        parts = [f"已写入 {out_path}（mermaid：{n_ok} 处已转为 PNG"]
        if n_fail:
            parts.append(f"，{n_fail} 处生图失败已保留 fenced 源码")
        parts.append("）")
        print("".join(parts), file=sys.stderr)
        if n_fail:
            print(
                "[mermaid_render] 已继续生成 Markdown"
                + (" 并将尝试 Word" if not args.no_docx else "")
                + "；请检查 Node/mmdc 或修正语法后重跑本脚本。",
                file=sys.stderr,
            )

    if args.no_docx:
        return 0

    docx_path = (
        args.docx.resolve()
        if args.docx is not None
        else out_path.with_suffix(".docx")
    )
    docx_ok = try_write_docx(out_path, docx_path)
    if (args.pdf or args.pdf_path is not None) and docx_ok:
        pdf_path = (
            args.pdf_path.resolve()
            if args.pdf_path is not None
            else docx_path.with_suffix(".pdf")
        )
        try_write_pdf(docx_path, pdf_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
