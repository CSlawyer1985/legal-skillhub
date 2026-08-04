# 关税税率摘要模板

## 结构

按此结构生成关税税率摘要。遵循 `references/formatting-standards.md` 中的格式约定。

---

### 页眉块

```
DUTY RATE SUMMARY — DRAFT WORK PRODUCT

Date:               {current date}
HTS Revision:       {revision identifier}
HTS Source:         {Data.gov catalog URL or fallback source}
HTS JSON URL:       {selected JSON download URL}
Product:            {product name/identifier}
HTS Subheading:     {XXXX.XX.XXXX}
Country of Origin:  {country}
Prepared by:        AI Classification Research Assistant
Status:             DRAFT — For Attorney/Broker Review
```

---

### 1. 归类依据

- **HTS 子目：** {XXXX.XX.XXXX}，HTSUS
- **描述：** {HTS 描述文本}
- **数量单位：** {来自 HTS 数据的单位}
- **归类来源：** {工作流 1 分析 / 用户提供 / 假定}
- **HTS 来源记录：** {目录 URL、选定的修订版本、JSON URL、分析日期}

如果归类不是本分析的一部分，注明："Classification was provided by the user and has not been independently verified."

---

### 2. 关税税率明细

| # | 组成部分 | 税率 | 第 99 章 / 命令编号 | 依据 | 生效日期 | 备注 |
|---|-----------|------|----------------------|-----------|---------------|-------|
| 1 | 第 1 栏普通（MFN） | {税率} | 不适用 | HTSUS {子目} | 现行修订版本 | 标准 NTR 税率 |
| 2 | Section 301 | {税率或不适用} | {9903.XX.XX} | 贸易法 § 301 | {日期} | {清单编号，如适用} |
| 3 | Section 232 | {税率或不适用} | {9903.XX.XX} | 贸易扩展法 § 232 | {日期} | {钢铁/铝} |
| 4 | Section 201 | {税率或不适用} | {9903.XX.XX} | 贸易法 § 201 | {日期} | {保障措施产品} |
| 5 | 反倾销税 | {税率或不适用} | {A-XXX-XXX} | 19 U.S.C. § 1673 | {日期} | {公司特定或其他所有} |
| 6 | 反补贴税 | {税率或不适用} | {C-XXX-XXX} | 19 U.S.C. § 1671 | {日期} | {公司特定或其他所有} |
| | **总估算关税** | **{总计}** | | | | **所有关税组成部分之和** |
| 7 | MPF（费用） | {税率/最低/最高（需核实）} | 不适用 | 19 CFR § 24.23 | 现行 | 正式申报费 |
| 8 | HMF（费用） | {税率（需核实）} | 不适用 | 26 U.S.C. § 4461 | 现行 | 仅海运 |

---

### 3. 特别项目资格

| 项目代码 | 项目名称 | 税率 | 合格？ | 要求 |
|-------------|-------------|------|-----------|-------------|
| {代码} | {fta-program-codes.json 中的名称} | {税率} | {是/否/核实} | {关键原产地规则} |

**适用特别税率：** {税率和项目，或"无——适用普通税率"}

**注意：** 特别项目税率替代第 1 栏普通税率，但**不**消除第 99 章附加关税或 AD/CVD 关税。

---

### 4. 关税计算示例

如果海关价值已知或可估算：

```
Customs Value (Transaction Value):    ${amount}

Column 1 General:  {rate}% × ${value} = ${amount}
Section 301:       {rate}% × ${value} = ${amount}
Section 232:       {rate}% × ${value} = ${amount}
AD Duty:           {rate}% × ${value} = ${amount}
CVD:               {rate}% × ${value} = ${amount}
                                        ──────────
TOTAL ESTIMATED DUTY:                   ${total}
Effective Rate:                         {total/value}%

Fees (not included in duty total):
MPF:               {rate (verify)}% × ${value} = ${amount} (min/max per entry applies)
HMF:               {rate (verify)}% × ${value} = ${amount} (ocean shipments only)
```

如果海关价值未知："Duty calculation requires the customs value (transaction value). Provide the commercial invoice value for a dollar-amount estimate."

---

### 5. 排除项与例外

- **Section 301 排除项：** {适用 / 不适用 / 需核查}
- **Section 232 排除项：** {适用 / 不适用 / 需核查}
- **临时关税暂停：** {任何适用的 MTB 条款}
- **对外贸易区潜力：** {高税率时相关}

---

### 6. 税率核实说明

- [ ] 税率已对照现行 HTS 修订版本核实（{修订版本日期}）
- [ ] 已记录 Data.gov 目录或后备来源
- [ ] 已在 HTS API 结果中检查第 99 章脚注
- [ ] 已在 HTS JSON 中检查 `additionalDuties` / `addiitionalDuties`（如可用）
- [ ] 已核实产品-国家组合的 AD/CVD 命令
- [ ] 已通过当前年度搜索核实 Section 301/232 状态
- [ ] 已通过当前年度搜索核实 MPF 税率/最低/最高
- [ ] 已核实 HMF 税率（仅海运）
- [ ] 已评估特别项目资格

**咨询的数据来源：** {列出使用的具体搜索和 API 调用}

---

### 7. 证据与时效附录

| 关税组成部分 | 来源 | 证据标签 | 检索日期 | 时效/生效日期 | 限制 |
|----------------|--------|----------------|-----------|----------------------------|------------|
| 第 1 栏普通 | {HTS 来源} | {Verified/Retrieved} | {日期} | {修订版本} | {无} |
| 第 99 章 | {来源} | {Verified/Retrieved/Identified/Unverified} | {日期} | {生效/到期} | {备注} |
| AD/CVD | {来源} | {Verified/Retrieved/Identified/Unverified} | {日期} | {命令/税率日期} | {范围备注} |

---

### 8. 免责声明

包含 `references/disclaimers.md` 中的**精简免责声明**。
