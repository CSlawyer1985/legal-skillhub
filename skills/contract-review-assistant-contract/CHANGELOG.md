# Changelog

## 1.0.1 (2026-07-27)

- 上架准备：补齐 `assets/screenshot-1.png`、`assets/screenshot-2.png` 两张 SkillHub 预览图（风险报告样例 + 对话式体检演示）。
- 更新 `README.md` 目录结构说明，标注 `icon.png`（256×256 上架图标）与预览图。
- 通过 `package_skill.py` 校验并生成可分发 zip（含 14 个文件）。
- 待上架前填写：`_skillhub_meta.json` 与 `SKILL.md` 的 `author` / `homepage` / `repository` 字段（当前为占位符）。

## 1.0.0 (2026-07-24)

- 初版发布：合同检查智能小助手。
- 五大审查维度：完整性检查、风险条款识别、合法合规性审查、歧义/笔误检测、签名核对。
- 内置 `scripts/contract_check.py` 确定性检查（缺失条款、占位符、编号断点、金额/总额一致性、日期、签名行）。
- 金额前后矛盾自动比对，兼容中文大写与阿拉伯写法（含财务大写壹贰叁）。
- 参考库：`contract-basics.md`（民法典要点+必备要素）、`risk-catalog.md`（14 类高风险条款）、`report-format.md`（评分口径+签名比对说明）。
- 输出模板：`assets/report_template.md`。
- 上架规范文件：`README.md`、`_skillhub_meta.json`、`LICENSE`、`CHANGELOG.md`、`assets/icon.svg`。
