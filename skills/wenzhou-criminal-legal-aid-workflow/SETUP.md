# 安装与运行

## 环境

- Python 3.9 或更高版本
- `python-docx`
- 可选：Poppler（`pdftotext`、`pdftoppm`、`pdfinfo`），用于读取PDF文字层和渲染扫描PDF
- 可选：Tesseract及简体中文语言包 `chi_sim`，用于本地扫描件OCR
- 可选：LibreOffice，用于把生成的 DOCX 渲染为 PDF/图片做版式检查

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install python-docx
python3 scripts/doctor.py
```

不要把 `.venv/`、真实案件 JSON、生成文书或测试输出提交到公开仓库。

## 在 Agent 中使用

将整个目录导入支持 Skill 的 Agent，或让 Agent 读取 `SKILL.md`。不同平台的安装入口可以不同，但核心运行不依赖专有 API。

## 上传 SkillHub

将根目录完整打包为 ZIP，确保解压后可以直接看到 `SKILL.md`，不要在 ZIP 外再套一层无关目录。上传前运行下列本地验证。SkillHub 页面中的作者信息仅填写“李鸿鸿、浙江光正大律师事务所”，不填写个人手机号、律师证号或上传个人印章。页面同时应明确作者署名不等于具体案件承办或作者审核。

## 本地验证

```bash
python3 scripts/doctor.py
python3 scripts/check_platform_compatibility.py --platform codex
python3 scripts/validate_charge_library.py
python3 scripts/validate_template_pack.py assets/template-packs/wenzhou
python3 scripts/audit_distribution_package.py .
python3 -m unittest discover -s tests -v
```

将 `codex` 替换为 `workbuddy`、`claude`、`gemini`、`opencode` 或 `web`，可以查看对应运行级别和安装注意事项。详细说明见 `references/platform-compatibility.md`。
