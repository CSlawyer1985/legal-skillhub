# 美国制裁及出口管制清单完整覆盖指南

本文档列出所有需要在官方浏览器校验中覆盖的美国联邦清单，确保尽职调查的穷举性。

## 核心清单（必查）

### 1. OFAC Sanctions List (财政部)

| 属性 | 值 |
|------|---|
| 官网 | https://sanctionssearch.ofac.treas.gov/ |
| 子清单 | SDN, Non-SDN CMIC, Non-SDN NS-MBS 等 |
| 验证方式 | 直连搜索，启用 Fuzzy (Min Score=70) |

**法律影响:** SDN 名单命中 = 全面资产冻结 + 交易禁令。Non-SDN CMIC = 证券投资禁令 (EO 13959)。

### 2. BIS Consolidated Screening List (商务部)

| 属性 | 值 |
|------|---|
| 官网 | https://www.trade.gov/consolidated-screening-list |
| 覆盖子清单 | Entity List, Denied Persons List (DPL), Unverified List (UVL), Military End User (MEU), Non-SDN CMIC, ITAR Debarred, ISN, FSE, SSI, PLC, CAPTA, AECA, SDN |
| 验证方式 | 搜索关键词，展开 Sources 下拉确认穷举性 |

**法律影响:**
- **Entity List**: 需 BIS 许可证出口受控物项，**审查政策：推定拒绝**
- **DPL**: 完全禁止出口
- **UVL**: 需增强尽职调查 (Enhanced Due Diligence)
- **MEU**: 军事终端用户限制

**关键提示:** CSL 一次性搜索所有子清单。如搜索后仅返回 Entity List + CMIC 两条命中，即可证明该实体**不在** DPL/UVL/MEU/ITAR 等其余 11 个子清单中。务必截图 Sources 下拉菜单以证明穷举性。

### 3. DoD 1260H Chinese Military Companies List (国防部)

| 属性 | 值 |
|------|---|
| 来源 | https://www.defense.gov (新闻稿公布) |
| 验证方式 | 搜索 defense.gov 新闻稿或 PDF |

**法律影响:** 被认定为"中国涉军企业" (CMC)。目前无直接交易禁令，但常为后续 SDN 制裁的前兆信号。

### 4. SAM.gov Federal Exclusions (总务管理局)

| 属性 | 值 |
|------|---|
| 官网 | https://sam.gov |
| 验证方式 | Entity Information → Exclusions 搜索 |

**法律影响:** 列入排除名单的实体不得参与任何美国联邦政府合同、赠款和合作协议。

### 5. FCC Covered List (联邦通信委员会)

| 属性 | 值 |
|------|---|
| 官网 | https://www.fcc.gov/supplychain/coveredlist |
| 验证方式 | 浏览器访问页面，检查实体或类别 |

**法律影响:** 使用 USF 资金不得采购该清单上设备。部分实体通过 NDAA 条款类别性列入。

## 辅助清单（通过 CSL 穷举覆盖）

以下清单在 BIS CSL 搜索时已自动覆盖，无需单独搜索：

- OFAC SDN List
- Denied Persons List (DPL)
- Unverified List (UVL)
- Military End User List (MEU)
- ITAR Debarred List
- Nonproliferation Sanctions (ISN)
- Foreign Sanctions Evaders (FSE)
- Sectoral Sanctions (SSI)
- Palestinian Legislative Council (PLC)
- CAPTA List
- AECA Debarred List

## 法律影响摘要模板

针对每个命中清单，报告应包含以下三部分：

1. **法律影响 (Legal Impact):** 引用具体法规/行政令，说明法律后果
2. **审批政策 (Licensing Policy):** 推定拒绝/逐案审查/推定批准
3. **咨询建议 (Advisory):** 对客户的具体行动建议
