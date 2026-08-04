# 变更日志

对 `icty-ictr-irmct` 技能的所有重要变更均记录在本文件中。

格式遵循 [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)，本技能遵循[语义化版本](https://semver.org/spec/v2.0.0.html)。

## [1.0.0] —— 初始发布

### 新增
- `SKILL.md` —— 入口、验证优先纪律、标准工作流、ICTY、ICTR 和余留机制的制度架构、基础文本、来源层级、引用格式概览、审计模式、实质性法理指引、敏感情境指引（保护措施）
- `references/authoritative-sources.md` —— 第一层级 / 第二层级 / 绝不可作为权威的层级，含 irmct.org、判例数据库（cld.irmct.org）、统一法院记录（ucr.irmct.org）、遗留 icty.org 和 unictr.irmct.org 以及 legal-tools.org 的入口
- `references/citation-format.md` —— 案号结构（IT- / ICTR- / MICT-）、阶段后缀（-T、-A、-AR72、-S、-R、-ES）、当事方指定和变音符号惯例、上诉的 IT→MICT 过渡（Karadžić、Mladić），以及带已核实案号和日期的常用引用权威规范表
- `references/verification-workflow.md` —— 后备阶梯（irmct.org → CLD → UCR → 遗留网站 → legal-tools.org → 二手 → 询问）、验证层级匹配，以及一条硬性保护措施规则（绝不确定受保护证人身份；优先使用公开删节版本）
- `references/foundational-texts.md` —— ICTY 规约（Res. 827，1993 年）、ICTR 规约（Res. 955，1994 年）、IRMCT 规约和过渡安排（Res. 1966，2010 年）、三套《程序与证据规则》，以及解释 IT/MICT 划分的能力规则
- `references/jurisprudence-map.md` —— 标志性判旨的逐主题图谱：管辖权（Tadić AR72）、灭绝种族罪（Akayesu、Krstić、Karadžić、Mladić）、煽动（Akayesu、媒体案）、危害人类罪（Tadić、Kunarac）、共同犯罪企业（JCE，Tadić 上诉）、指挥官责任（Čelebići、Blaškić）、酷刑（Furundžija）、性暴力（Akayesu、Kunarac、Furundžija）、高级领导人认罪（Kambanda）、余留/逃犯职能（Kabuga）
- `examples/example-verification.md` —— Krstić / 斯雷布雷尼察灭绝种族罪引用的端到端验证，包括审判与上诉的区分
- `examples/example-audit.md` —— 工作草稿审计（Tadić JCE 日期/分庭错误；Akayesu/JCE III 误述）和定稿记录审计（Mladić 上诉判决，IT/MICT 配对）

### v1.0.0 时的技能范围
- 将 ICTY（1993–2017）、ICTR（1994–2015）和 IRMCT / 余留机制（2010 年至今）作为单一综合技能覆盖，因为余留机制延续两个法庭的职能、托管其档案，并以 MICT 案号裁决后期上诉
- 编码与本仓库 `icc` 和 `eccc` 技能共享的验证优先方法论

### 已知限制
- 《程序与证据规则》修订追踪：技能指示模型识别被引决定日期时生效的修订版，但不包含修订版 × 日期对照表。诉讼争议点取决于特定修订版的用户，应将相应修订版提供给项目知识库。
- 权威引用表覆盖最常引用的标志性判决；它不是完整案卷。许多重要案件（Galić、Stakić、Stanišić & Simatović、Bagosora 等人、Nahimana 等人、Butare）在判例图谱中被引用，但没有完整引用行——引用前逐一对照第一层级来源核实。
- 权威表中的日期在编写时已对照第一层级来源核实；由于公开删节版本有时晚于口头宣判日期，引用前务必对照 irmct.org 重新确认生效日期和版本。
