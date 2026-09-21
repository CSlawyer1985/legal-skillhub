# PPTX Operations Reference

Use these helpers for reading and validating `.pptx` work under the `python-pptx-presentation` skill.

## Read Existing PPTX

```bash
python -m markitdown input.pptx
python scripts/office/unpack.py input.pptx unpacked/
```

Use text extraction for content order and raw XML only when you need package-level details.

## Optional Render Slides To Images

Use this section only when the user explicitly asks for deeper visual checking. Do not install LibreOffice or render every slide as part of default validation.

```bash
python scripts/office/soffice.py --headless --convert-to pdf output.pptx
pdftoppm -jpeg -r 150 output.pdf slide
```

For targeted re-checks:

```bash
pdftoppm -jpeg -r 150 -f N -l N output.pdf slide-fixed
```

## Validate Package

```bash
python scripts/office/validate.py output.pptx
python scripts/office/unpack.py output.pptx unpacked/
python scripts/office/pack.py unpacked/ repacked.pptx --original output.pptx
```

Check that `ppt/presentation.xml` exists, generated slides are present, and no placeholder text remains.

## Default Completion Check

Confirm the file exists, is non-zero size, has the expected slide count, uses the brand assets referenced by the skill, and has no obvious placeholder text. Report completion after that lightweight check unless the user asks for a deeper visual review.
