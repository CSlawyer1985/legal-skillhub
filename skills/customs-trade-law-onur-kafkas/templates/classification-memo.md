# 归类备忘录模板

## 结构

按此结构生成归类备忘录。遵循 `references/formatting-standards.md` 中的引文和格式约定。

---

### 页眉块

```
TARIFF CLASSIFICATION MEMORANDUM — DRAFT WORK PRODUCT

Date:           {current date}
HTS Revision:   {revision identifier}
HTS Source:     {Data.gov catalog URL or fallback source}
HTS JSON URL:   {selected JSON download URL}
Product:        {product name/identifier}
Country of Origin: {country}
Prepared by:    AI Classification Research Assistant
Status:         DRAFT — For Attorney/Broker Review
```

---

### 1. 执行摘要

2-3 句摘要，包含：
- **建议归类：** 带统计后缀的完整 HTS 子目
- **总估算关税：** 所有组成部分之和（普通 + 附加关税 + AD/CVD）
- **置信度：** 高 / 中 / 低，附简要说明
- **关键风险因素：** 触发的任何标记的一行摘要

---

### 2. 产品描述

货物的结构化描述：
- **通用名称/商业名称**
- **材料与成分**（如已知，含百分比）
- **功能与运行机理**
- **最终用途/预期目的**
- **物理特性**（尺寸、重量）
- **原产地与制造工艺**
- **任何额外的产品特定细节**

注明任何被假定或用户未提供的信息。

---

### 3. GRI 分析

按 `references/gri-analysis.md` 记录《解释总规则》的逐步适用：

#### HTS 来源记录
- **目录/来源 URL：** {Data.gov 目录 URL 或后备来源}
- **目录检查/采集日期：** {日期或"不可用"}
- **选定的 HTS 发布版：** {修订版本标题}
- **JSON 下载 URL：** {URL}
- **分析日期：** {日期}
- **来源限制：** {无 / 使用了后备 / API 不可用 / 备注}

#### 考虑的候选品目
| 品目 | 描述 | 考虑依据 |
|---------|-------------|----------------------|
| {XXXX} | {品目文本} | {考虑此品目的原因} |

#### GRI 1 分析
- 引用相关品目文本
- 引用适用的类注释
- 引用适用的章注释
- **结论：** GRI 1 是否解决？是 → 说明是哪个品目。否 → 继续。

#### GRI 2-5 分析（如需要）
- 仅适用解决问题所必需的 GRI
- 记录每一步及其结论
- 如果涉及 GRI 3(b) 本质特征，适用多因素测试

#### GRI 6：子目确定
- 展示已解决品目的缩进层级
- 比较同一缩进层级的子目
- 在品目内适用 GRI 1-5 原则
- **建议子目：** {XXXX.XX.XXXX}

#### 解决的 GRI
- **归类依据：** GRI {X}
- **关键认定：** {一句话说明决定性分析}

---

### 4. CROSS 裁决研究

按 `references/cross-ruling-research.md` 呈现发现：

#### 相关裁决

每个裁决（目标 3-5 个）：
```
**CBP Ruling {NY/HQ} {Number} (dated {Date})**
- Product: {description}
- Classification: {HTS subheading}
- GRI Applied: {GRI number}
- Key Reasoning: {1-2 sentences}
- Factual Similarity: {High/Medium/Low}
- Evidence Quality: {Verified/Retrieved/Identified/Unverified}
- Status: {Active/Revoked/Modified}
```

注意："关键引文"（具体推理摘录）要求 **Verified** 证据质量。完整证据质量协议见 `references/cross-ruling-research.md`。

#### 裁决分析
- 裁决支持的共识归类
- 任何离群值或冲突
- 裁决如何为建议归类提供依据

---

### 5. CIT/CAFC 判例（如适用）

如果按 `references/cit-decision-analysis.md` 找到了相关司法判决：

- 以 Bluebook 格式的判例引文
- 判决要旨的简要摘要
- 对建议归类的影响
- 与 CROSS 裁决的任何冲突

如果未找到相关判决，说明："No CIT/CAFC decisions were found directly addressing the classification of this product or the candidate headings."

---

### 6. 关税税率摘要

按 `references/duty-rate-compilation.md`：

| 组成部分 | 税率 | 依据 | 备注 |
|-----------|------|-----------|-------|
| 第 1 栏普通 | {税率} | HTSUS {子目} | MFN/NTR 税率 |
| 特别项目 | {税率} | {项目代码} | 如原产地符合资格 |
| Section 301 | {税率} | 9903.XX.XX | 如适用 |
| Section 232 | {税率} | 9903.XX.XX | 如适用 |
| Section 201 | {税率} | 9903.XX.XX | 如适用（保障措施） |
| 反倾销税 | {税率} | A-XXX-XXX | 如适用 |
| 反补贴税 | {税率} | C-XXX-XXX | 如适用 |
| **总估算关税** | **{税率}** | | **所有关税组成部分之和** |
| MPF（费用） | {税率/最低/最高（需核实）} | 19 CFR § 24.23 | 正式申报费 |
| HMF（费用） | {税率（需核实）} | 26 U.S.C. § 4461 | 仅海运 |

---

### 7. 风险因素与建议

#### 触发的标记
列出 `references/human-review-triggers.md` 中任何被触发的标记，附完整标记文本和建议的下一步。

#### 建议
- 是否应申请 CBP 约束性裁决
- 是否应审查现有申报
- 任何时间敏感考虑（即将到期的排除项、待定贸易行动）
- 为律师/报关行建议的下一步

---

### 8. 证据与时效附录

为每个重大结论包含一个紧凑的证据台账：

| 结论 | 来源 | 权威级别 | 证据标签 | 检索日期 | 时效/修订版本 | 限制 |
|------------|--------|-----------------|----------------|-----------|----------------------|------------|
| {归类} | {URL/标题} | {HTSUS/CROSS/CIT 等} | {Verified/Retrieved/Identified/Unverified} | {日期} | {现行修订版本/状态} | {无/备注} |

---

### 9. 免责声明

包含 `references/disclaimers.md` 中的**标准免责声明**，填充 `[DATE]` 和 `[REV]`。
