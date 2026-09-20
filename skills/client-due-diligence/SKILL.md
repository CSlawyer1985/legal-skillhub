---
name: client-due-diligence
description: 律师事务所客户背调与法律顾问切入 Skill。输入公司名称 + 自然语言指令，自动生成「Word 主报告 + PDF 附件」。核心能力：(1) 多源数据对齐基准表（收敛口径冲突）；(2) 9 维度风险评分；(3) 利益冲突审查 8 项强制门槛（不过关不出报告）；(4) 法律顾问切入备忘录（切入话术 + 需求矩阵 + 首见问题清单）。数据优先通过真实 MCP connector 拉取，未连接时 fallback 到权威公开网站。触发词：客户背调、客户尽调、尽职调查、谈客户、接法律顾问、法律顾问切入、公司背调报告。
---

# client-due-diligence（客户背调 + 法律顾问切入报告生成器）

律师事务所用于在正式接洽客户前：① 完成客户背景调查与法律风险评级；② 收敛多源数据口径冲突（数据对齐）；③ 通过利益冲突审查门槛；④ 生成可直接用于谈客户、接法律顾问的洽谈备忘录。

**最终交付（2 份）**：
- **O1 主报告（.docx）** — 完整背调报告，含数据对齐基准表 + 风险评级 + 法律顾问切入建议
- **O2 附件（.pdf）** — 利益冲突审查表 + 数据对齐基准表 + 风险摘要矩阵 + 待核实事项清单 合并为单份 PDF

---

## Inputs

| 字段 | 必填 | 说明 |
|---|---|---|
| `company_name` | ✅ | 客户公司完整法定名称（如"苏州仕净科技股份有限公司"）。支持模糊匹配；如同时给出简称/股票代码，应核验后回填全称。 |
| `instruction` | ✅ | 用户自然语言指令，决定报告深度、关注点与输出范围。详见 `references/instruction-playbook.md`。 |
| `report_level` | ⭕ | 可选；指令已隐含时无需指定。`summary / standard / full`，默认 `standard`。 |
| `conflict_check` | ✅ | 利益冲突审查结果（8 项自查）。**缺失或存在未豁免冲突时，禁止生成正式报告**（见 Hard Rules R8）。 |

---

## Hard Rules（不可破坏的硬约束）

| # | 规则 | 落地 |
|---|---|---|
| **R1** | 信息只允许来自权威公开渠道 + 真实 MCP。URL 域名必须在 `references/data-sources-catalog.md` 的《权威网站白名单》内，**屏蔽**百度/搜狗/360 百科/微信公众号/自媒体。 | 脚本入口强校验域名；非白名单直接 `sys.exit` |
| **R2** | 每条关键数据标注来源 + 时点，紧跟原文 URL。 | docx hyperlink / pdf 链接 |
| **R3** | 主报告必须 .docx，排版规范（封面/目录/标题级/表格边框/页眉页脚/页码）。 | python-docx 标准样式 |
| **R4** | 附件必须 PDF，合并为单份。 | reportlab 原生 Drawing + TTF 中文字体 |
| **R5** | 不输出 Markdown 给用户；.md 仅作内部模板。 | 删除 .md 交付路径 |
| **R6** | 数据冲突单独列"待核实事项"，不掩盖差异。 | 对齐表 + 待核实清单 |
| **R7** | 免责声明固定写入末页。 | 固定段落 |
| **R8** | **利益冲突审查是承接前的强制门槛**：8 项自查任一"是"且未书面豁免，报告结论自动置为"禁止承接"，且风险等级强制标红。 | 脚本读取 `conflict_check`，有未豁免冲突则阻断正文建议、输出"冲突待决"状态 |

---

## Step 1 — 解析输入 + 选深度

1. 核验公司法定全称（MCP 优先：`qcc-company` / `tyc-mcp` / `qixinhuiyan-mcp`）
2. 解析 `instruction` 关键词 → `references/instruction-playbook.md` 推导：
   - `report_level`：summary / standard / full
   - `extra_focus`：诉讼/知识产权/财务/监管/重整/退市 等
   - 每个 B1-B11 模块 depth：quick / standard / deep
3. 已上市公司自动启用 `B9 上市专项`；出现"预重整/重整/退市/立案"自动启用 `B10 重整与监管专项`

## Step 2 — 并行抓取 B1-B11 数据模块（MCP 优先，权威源 fallback）

| # | 模块 | MCP（优先） | 权威源（fallback） |
|---|---|---|---|
| B1 | 工商基础 | qcc-company / tyc-mcp | gsxt.gov.cn |
| B2 | 股东/实控人/对外投资 | qcc-company / qixinhuiyan-mcp | gsxt.gov.cn、cninfo.com.cn |
| B3 | 董监高/主要人员 | qcc-company / tyc-mcp | gsxt.gov.cn、cninfo.com.cn |
| B4 | 经营异常/严重违法 | qcc-company / shuidi-credit | gsxt.gov.cn、creditchina.gov.cn |
| B5 | 司法风险（裁判文书） | jufa-mcp-server / qcc-legal / pkulaw | wenshu.court.gov.cn |
| B6 | 执行/失信/限高 | qcc-legal / qcc-company | zxgk.court.gov.cn |
| B7 | 知识产权 | mzl-trademark / patsnap-search | sbj.cnipa.gov.cn、pss-system.cnipa.gov.cn |
| B8 | 行政处罚 | qcc-company / shuidi-credit | creditchina.gov.cn、gsxt.gov.cn |
| B9 | 上市专项 | westock-data / neodata-financial-search | szse.cn / sse.com.cn / cninfo.com.cn |
| B10 | 重整/立案/监管处分 | qcc-legal / fazhi-law | csrc.gov.cn、szse.cn、全国企业破产重整案件信息网 |
| B11 | 舆情（限权威媒体） | — | xinhuanet.com、people.com.cn、cctv.com、jrj.com.cn、gmw.cn、chinacourt.org |

**执行规则**：
1. 先探测目标 MCP connector 是否 connected；已连接则直接调用并记录返回字段。
2. 未连接则 WebFetch 对应权威站点，保留原文 URL。
3. 同一字段有多个来源时，全部录入，供 Step 3 数据对齐。

## Step 3 — 数据对齐 + 冲突审查 + 风险评分

### 3.1 数据对齐（关键环节）
按 `references/data-alignment-protocol.md`，对每个关键字段：
1. 列出所有来源的值 + 来源 + 时点；
2. 判定"一致 / 口径差异 / 实质冲突"；
3. 输出**权威基准值**（优先级：政府登记 > 交易所披露 > 一手公告 > 权威媒体 > 商业数据库）；
4. 冲突字段进入"待核实事项"清单。

### 3.2 利益冲突审查（强制门槛，见 Hard Rules R8）
按 `references/conflict-check-protocol.md` 的 8 项自查，逐项判"是/否"：
1. 是否曾/正在代理目标公司；2. 是否代理其债权人（金融/供应商）；3. 是否代理其竞争对手；4. 是否代理其股东/实控人；5. 是否与临时管理人/清算组及其成员存在关联；6. 是否代理其他重整参与方（投资人/出资人）；7. 本所律师是否存在个人利害关系；8. 其他影响独立客观履职的情形。
**任一"是"且无书面豁免 → 阻断承接，报告结论="禁止承接"，风险强制标红。**

### 3.3 风险评分
按 `references/risk-framework.md` 的 9 维度加权。等级：绿 <30 / 黄 30-60 / 红 ≥60；任一维度加权分 ≥25 直接判红。

## Step 4 — 生成交付物

| 编号 | 文件 | 格式 | 内容 |
|---|---|---|---|
| **O1** | `<CompanyName>-客户背调报告.docx` | Word | 封面/目录 + 正文（数据对齐基准表 + 风险评级 + 法律顾问切入备忘录） |
| **O2** | `<CompanyName>-客户背调附件.pdf` | PDF | 利益冲突审查表 + 数据对齐基准表 + 风险摘要矩阵 + 待核实事项清单 |

章节结构见 `references/report-outline.md`；洽谈备忘录骨架见 `assets/memo-template.md`。

**生成完毕后必须调用 `present_files`**，将 2 份交付一次性回传用户。

---

## Quality Checklist（present_files 前自检）

- [ ] 公司名称已核验为法定全称
- [ ] 统一社会信用代码等关键字段已通过数据对齐，采用权威基准值（不是早前编造值）
- [ ] 每个数据块的来源 URL 域名属于《权威网站白名单》，无百度/搜狗/360 百科/公众号/自媒体
- [ ] **利益冲突审查 8 项已逐项判"是/否"，存在未豁免冲突时结论="禁止承接"**
- [ ] 司法/执行/监管/知识产权/财务模块已覆盖（deep 时）
- [ ] 已上市公司启用 B9/B10 专项
- [ ] 风险评分有具体依据，无空泛断言
- [ ] 洽谈备忘录含：切入话术 + 需求矩阵 + 首见问题清单
- [ ] docx 排版规范；pdf 中文无乱码（TTF 字体嵌入 + 原生 Drawing）
- [ ] 免责声明固定末页

---

## Resources

### references/
- `data-sources-catalog.md` — 11 模块对应 MCP + 权威源白名单 + 字段映射；**生成前必读**
- `data-alignment-protocol.md` — 数据对齐基准表规范（口径冲突收敛规则 + 优先级）
- `conflict-check-protocol.md` — 利益冲突审查 8 项门槛 + 阻断规则
- `instruction-playbook.md` — instruction 关键词解析 + 模块深度对照
- `report-outline.md` — O1 主报告完整章节结构
- `risk-framework.md` — 9 维度加权评分 + 阈值

### assets/
- `report-template.md` — O1 内部 Markdown 骨架（不外发）
- `memo-template.md` — 法律顾问切入备忘录骨架（切入话术/需求矩阵/问题清单）

### scripts/
- `generate_cdd.py` — 端到端生成：读取 `case_data.json` → 校验 R1/R8 → 输出 .docx + .pdf
- `case_data.example.json` — 对齐后数据结构示例（含 conflict_check + data_alignment 字段）

**一行调用**：按 `case_data.example.json` 结构整理数据为 `case_data.json`，放到 `scripts/` 同目录：

```bash
python scripts/generate_cdd.py
# 严格模式（非权威源 URL / 存在未豁免冲突 → 直接拒绝生成）：
python scripts/generate_cdd.py --strict-legal
```