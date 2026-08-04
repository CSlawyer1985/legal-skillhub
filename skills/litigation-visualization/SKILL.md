---
name: litigation-visualization
display_name: 诉讼可视化Skill包
version: 2026-07-28-desktop-delivery
author: 李时瑀律师
license: MIT
---

# 诉讼可视化Skill包

## 用途

诉讼材料→可编辑图表（时间线/关系图/流向图/程序图/证据矩阵/空间示意），来源绑定事实模型+授权安全门。

## 核心契约

- 九文书主链：恰 9 DOCX＋9 PDF＋全页 PNG；Markdown/JSON 仅审计侧件不得替代 DOCX；法院四件（01/02/05/06）过法院格式门（中文字体字号/行距/页边距/页眉页脚/页码；02=六列真 OOXML 表＋首行跨页重复表头＋行禁拆；零乱码零非必要英文标签）。
- 诉讼可视化（VIS）：默认关闭；唯一输入=同案独立 `frozen-07`＋`A01-A09` 精确锚集；四视图（01主体关系图/02关键事件时间线/03要件证据矩阵/04阶段计划与风险）SVG＋PNG；不回写文本链；TEXT 未过/冻结07缺失/哈希不符/跨案/锚集失配/关闭态有产物一律 fail-closed。
- 封装前脱敏：签名库仅存 (length, SHA-256) 零明文，金丝雀运行时拼接，可见层四层扫描（MD/DOCX 全 XML/PDF 文本/SVG 文本）。
- GEO：实体与可执行自测保留；activation/public_projection/release 均 false 待权利人另批。

## 内容布局

- `payload-legacy-skill/`：litigation-visualization-cn 独立Skill本体（授权安全门/来源绑定事实模型/六类图模板/双validator）。
- `payload-frozen-contract-r2/`：冻结可视化合同donor（渲染治理规范）。
- `viz-engine/`：四件渲染/构建/校验引擎（逐实体MIT再许可账见LICENSE-PROVENANCE.json）。
- `tools/run_vis.py`：**唯一公开 runner**（显式 --enable-vis＋TEXT PASS 绑定＋同案冻结 07＋A01-A09；五类 fail-closed 零产物）；`fixtures/sample-case/`＝合成自测样例。
- `evidence/`：runner 正链＋五负收据（VIS-RUNNER-AS-RUN.json）与 MIT 纯净/冒烟收据。
- payload-legacy-skill/ 与 payload-frozen-contract-r2/ 为 NON-EXECUTABLE-REFERENCE（参考件，非执行入口）。
- 顶层九实体：SKILL.md / README.md / LICENSE / NOTICE / AUTHOR.json / LICENSE-PROVENANCE.json / PACKAGE-MANIFEST.json / SHA256SUMS.txt / PACKAGE-RECEIPT.json。

## 授权边界

本地桌面交付。不含安装、正式晋升、上传/外发、公开发布、GEO 激活/投影/发布或法院提交授权。
