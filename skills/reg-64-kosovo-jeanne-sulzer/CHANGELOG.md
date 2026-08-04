# 变更日志——reg-64-kosovo 技能

本文件记录了第 64 号条例审判庭（科索沃）技能的所有重要变更。

格式遵循 [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)，项目遵循 [语义化版本控制](https://semver.org/spec/v2.0.0.html)。

## [1.0.0-draft] — 2026-06-02

### 修复
- `references/verification-workflow.md`（陷阱 1）：将 KSC 设立文书编号更正为 **第 05/L-053 号法律**（原为“04/L-274”）。

### 新增

- `reg-64-kosovo` 技能初稿——《国际司法技能系列》第十三个技能
- `SKILL.md` 涵盖：
  - 第 64 号条例审判庭验证纪律（存在性 / 内容 / 段落层级）
  - 制度架构：第一阶段（2000 年初，特设）、第二阶段（2000 年 2 月 15 日 UNMIK 第 2000/6 号条例）、第三阶段（2000 年 12 月 15 日 UNMIK 第 2000/64 号条例）
  - 第 64 号条例审判庭组成：3 名专业法官，至少 2 名国际法官，主审法官为国际法官
  - 逐案指定机制：申请 → DJA 建议 → SRSG 批准 → DJA 指定
  - KWECC 于 2000 年秋放弃，改用一体化第 64 号条例机制
  - UNMIK 向 EULEX 的过渡（2008 年 2 月 17 日独立；2008 年 12 月 9 日 EULEX 全面运作能力）
  - 第 64 号条例与 KSC 的区别（制度、时间、地域）——显式标记
- `references/foundational-texts.md` — 联合国安理会第 1244 号决议（1999 年）、UNMIK 第 1999/1、2000/6、2000/64、2001/2、2001/9（宪法框架）、2003/25（临时刑法典）、2003/26（临时刑事诉讼法典）号条例；1976 年南斯拉夫联邦刑法典的连续性；第 2008/124/CFSP 号联合行动（EULEX）；第 2008/03-L053 号法律；科索沃共和国宪法
- `references/authoritative-sources.md` — 来源层级：unmik.unmissions.org 遗留档案、EULEX 档案、legal-tools.org、USIP Michael Hartmann 报告、欧安组织科索沃特派团庭审监测、ICTJ 报告、学术专著（Cerone、Reidy、Cohen、Strohmeyer）
- `references/citation-format.md` — 地区法院案号惯例、第 64 号条例审判庭标记、多语言（阿尔巴尼亚语 / 塞尔维亚语 / 英语）引用形式
- `references/verification-workflow.md` — 回退阶梯、第 64 号条例特定陷阱（KSC 区别、KWECC 被放弃而非建立、EULEX 在科索沃而非海牙、实体法的时间适用、审判庭组成精确性、第 64 号条例 ≠ 普通地区法院审判庭）
- `references/jurisprudence-map.md` — 制度时期（阶段 0-3）、实体覆盖（战争罪、族裔间犯罪、有组织犯罪、恐怖主义）、案件类型学（复活、变更审判地点、混合审判庭、重审、合并起诉）、比较定位（SPSC、WCC-BiH、KSC、ICTY）
- `examples/example-verification.md` — 对第 2000/64 号条例第 2.2 节组成规则的端到端验证，含三个常见变体陷阱
- `examples/example-audit.md` — 审计用户提供的段落，含六类错误（制度误认、生效日期、组成框架、实体法时间性、KWECC 错误归因、EULEX 地域错误）

### 咨询的来源（项目级研究笔记）

- UNMIK 官方档案 — unmik.unmissions.org
- USIP — Michael E. Hartmann，《科索沃的国际法官和检察官》报告
- ECFR 关于科索沃法治的报告
- ICTJ — 科索沃过渡司法报告
- 欧安组织科索沃特派团 — 法律体系监测科报告
- Hybrid Justice 项目 — 比较学术研究
- John Cerone — 载于《Journal of International Criminal Justice》的关于第 64 号条例审判庭的学术文章
- Hansjörg Strohmeyer — 载于《American Journal of International Law》的关于 UNMIK 和 UNTAET 平行行政管理的文章
- David Cohen — 东西方中心关于国际化司法机制的比较报告
- Reed Brody — 关于国际化起诉的比较学术研究
- Romano、Nouwen、Stahn — 混合刑事管辖权的分类学

### 已知局限

- 第 64 号条例审判庭的判例**档案支离破碎**；不存在可媲美 ICC CourtRecords 或 ICTY Records Database 的单一权威案件索引
- 案件验证通常需要查阅多个来源
- 高质量学术文献以英文存在；主要案件材料以阿尔巴尼亚语、塞尔维亚语和英语存在；实体性主张可能需要在不同语言版本之间交叉验证
- 2008-2009 年过渡期在独立的第 64 号条例框架下归档尤其贫乏（大量相关材料在 EULEX 档案中，后者有自己的访问限制）

### 验证方法论

本技能遵循父仓库 `METHODOLOGY.md` 中定义的验证优先方法论。适用了选择法域的五项累积标准：

1. **对国际罪行的属事管辖权** — 第 64 号条例审判庭根据 1976 年南斯拉夫联邦刑法典（第十六章）起诉战争罪，自 2004 年起根据临时刑法典起诉；也处理族裔犯罪
2. **结构性国际化要素** — UNMIK 第 2000/64 号条例法律基础（联合国管理框架）、多数国际法官的组成要求、SRSG 批准机制
3. **有限的时间和属物管辖权** — 运营期 2000-2008/2009；对“重要或敏感”案件逐案指定；特定于科索沃领土范围
4. **结构化公开文档** — UNMIK 官方档案、EULEX 档案、legal-tools.org、欧安组织庭审监测、学术专著（零散但大量）
5. **对国际刑事司法的实质性学说贡献** — 第 64 号条例是国际化司法行政“一体化模式”的原型；对后续设计辩论具有影响力（在 Romano/Nouwen/Stahn 的渐进混合类型学中被引用）；是冲突后转型期法治文献中的实证案例研究

### 状态

**草稿——尚未经科索沃本地或 UNMIK 资深国际刑事律师验证。** 鼓励出版前审查。

---

## 未来版本说明

- v1.1 候选：新增知名第 64 号条例起诉的结构化案件表（米特罗维察变更审判地点案件、2004 年 3 月骚乱起诉）；更深入处理 EULEX 延续案件
- v2.0 候选：整合 2018 年后 EULEX 加强特派团及向国家司法的全面过渡；整合 Cerone、Reidy、Cohen 的已核实学术引注，达到段落级准确度
