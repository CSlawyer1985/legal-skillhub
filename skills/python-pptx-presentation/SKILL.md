---
name: python-pptx-presentation
description: 制作、修改、检查或质检 PowerPoint/PPTX/deck/presentation，尤其适用于 Dentons/Dacheng/大成品牌法律汇报。
metadata:
  displayName: 制作 PPT
  group: pptx
---

# Python PPTX Presentation

Create editable `.pptx` decks with `python-pptx` as the primary route. Use `write_pptx` only as the no-Python fallback described below.

## Source And Outline Gate

1. Confirm topic, audience, target slide count, output path, and source files.
2. Read `assets/brand.md` and `assets/deck-structure.md`; do not hardcode brand values in this file.
3. Read all source materials before summarizing. 多份素材要分别记录来源；for multiple sources, record each source separately and cite the source or basis for every planned slide.
4. If `read_pdf` or `read_docx` returns `⟦SCANNED_PDF⟧`, stop and ask whether to use `ocr_document`. Explain that OCR sends page images to the configured vision service and may involve 数据出境. Do not call OCR until the user agrees.
5. Treat `ocr_document` output marked `⟦视觉识别·非逐字引用级⟧` as non-verbatim recognition. Flag dates, amounts, parties, negative terms, article numbers, and other key facts for manual source checking.
6. 先产出文字大纲，不要直接生成 PPT. Each slide outline must include layout, title, key points, notes, and source basis.
7. 必须等用户确认或调整后再生成 `.pptx`.

## Primary Python Route

- Use the SDK built-in `Write` tool for Python source files and the SDK built-in `Bash` tool for execution.
- Install packages only in the app-managed isolated Python runtime. Before install/run, verify:

```bash
python -c "import os, sys; print(sys.executable); print(sys.prefix); print(os.environ.get('VIRTUAL_ENV')); print(os.environ.get('PIP_REQUIRE_VIRTUALENV'))"
```

- `VIRTUAL_ENV` must be non-empty, `PIP_REQUIRE_VIRTUALENV` must be `true`, and `python` must point inside the isolated runtime.
- Install required packages with exactly:

```bash
python -m pip install python-pptx Pillow
```

- Do not use `pip`, `pip3`, `sudo`, `brew`, `apt`, or system Python package locations.
- For Dentons/Dacheng decks, read `references/dentons-style.md` and adapt `references/dentons_deck_template.py` instead of inventing coordinates from scratch.
- Use native PowerPoint objects: text boxes, shapes, tables, lines, fills, and notes. Do not render whole slides or tables as screenshots.

## PPTX Operations And QA

Use `references/pptx-ops.md` for mechanical operations:

- `markitdown` extraction for existing `.pptx` files.
- package validation with the migrated `scripts/office/*` utilities.
- optional rendering helpers only when the user explicitly asks for deeper visual checking.

## 无 Python Fallback

Use this only when the isolated runtime cannot be used: `VIRTUAL_ENV` is empty, `PIP_REQUIRE_VIRTUALENV` is not `true`, or `python -m pip install python-pptx Pillow` fails.

When this happens, call `write_pptx` only to generate a clearly labeled draft. The title or opening note must include:

`草稿（未走 python-pptx，版式精度有限）`

Tell the user that the file is a fallback draft and should be regenerated with `python-pptx-presentation` after Python is ready.

## Validation Checklist

Default validation is a lightweight check / 默认只做轻量校验:

- Confirm the `.pptx` exists, is non-zero size, and contains `ppt/presentation.xml`.
- Confirm brand values came from `assets/brand.md` / `assets/brand.json`, not ad hoc constants.
- Confirm Dentons/Dacheng decks follow `references/dentons-style.md`: cover, contents, content pages, ending page, fixed title/footer conventions, and no page logo or text watermark.
- Confirm slide count, title/footer structure, source basis, and absence of obvious placeholders before final reporting.
- Do not install LibreOffice, convert every slide to images, or spawn extra review tasks for default validation. If the user explicitly asks for deeper visual checking, use the optional rendering helpers in `references/pptx-ops.md`.
