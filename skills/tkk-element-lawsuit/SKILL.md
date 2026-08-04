---
name: tkk-element-lawsuit
description: "TKK 要素式起诉状转换工具——从传统起诉状 DOCX/PDF 自动提取要素，AI 驱动填写并生成规范的要素式文书。33个民事起诉状案由全支持，数据驱动表布局（基于 法〔2025〕82号 官方模板），4步流程（上传→AI分析→编辑校对→预览导出），输出 DOCX。当用户需要将传统起诉状转换为要素式格式、修改案由模板字段定义时使用此 skill。"
author: 汤康康律师
agent_created: true
---

# TKK · 要素式起诉状转换工具

## 概述

Web 端单页应用 + Python DOCX 生成器，将传统格式的起诉状 DOCX/PDF 转换为法院要求的**要素式文书**。

### 核心能力
- **对话式一键转换**：发 DOCX/PDF → AI 自动提取 → 生成要素式 DOCX
- **33个案由全覆盖**：所有民事起诉状案由，基于 法〔2025〕82号 官方模板
- **精确格式复刻**：页边距/表格列宽/边框/字体严格对齐官方格式
- **数据驱动架构**：`table_layouts.json` 定义表结构，`templates.json` 定义字段，生成器自动适配

## 触发条件

- 用户需要将传统起诉状转换为要素式起诉状
- 用户想修改案由模板的字段定义
- 用户想了解工具的架构以便二次开发

## 使用方式

### 对话式转换（唯一推荐方式）

直接将起诉状 DOCX/PDF 文件发给 WorkBuddy，说"帮我转换为要素式起诉状"。

**工作流**：
1. **提取文本** — `scripts/extract_text.py` 提取全文
2. **AI 分析** — WorkBuddy 阅读起诉状文本，识别案由、提取当事人/诉请/事实
3. **生成 DOCX** — 写入结构化 JSON，`scripts/generate_docx.py` 输出要素式文书

## ⚠️ 深度经验与格式规范（必读）

以下经验源自与 法〔2025〕82号 官方模板的逐项对比分析，是决定输出质量的关键。

### 1. 表格结构铁律

- **6张独立表格**，表间**零间隔、零段落、零空行**，直接首尾相连（`</tbl>`→`<tbl>`）
- 每表含 2 列：标签列（~2270 twips）+ 数据列（~7074 twips），总宽 9344 twips
- 不同案由表格数量不同（4~13 张），但所有民事起诉状的前 2 张表结构一致

### 2. 精确格式参数

| 参数 | 值 | 说明 |
|------|-----|------|
| 页面尺寸 | A4 (11906×16838 twips) | 21.00×29.70 cm |
| 上边距 | 2.524cm | Emu(908685) |
| 下边距 | 1.760cm | Emu(633730) |
| 左边距 | 2.499cm | Emu(899795) |
| 右边距 | 1.998cm | Emu(719455) |
| 边框 | single, #231F20, sz=2 | 6面 (top/left/bottom/right/insideH/insideV) |
| 正文 | 宋体 10.5pt | 不加粗 |
| 节标题 | 宋体 15pt | **不加粗**（官方模板不加粗！） |
| 大标题 | 宋体 22pt | 加粗，居中 |
| 副标题 | 宋体 18pt | 居中 |
| 标签列对齐 | 左对齐, 顶部对齐 | vAlign=top |
| 单元格内边距 | 0 | 无额外边距 |

### 3. 常见错误与教训

| 错误 | 根因 | 正确做法 |
|------|------|---------|
| 表格间有空行 | 误以为需要 spacer paragraphs | **严禁**在表间插入任何 `<p>` 元素 |
| 页边距随意设置 | 凭感觉写 0.5/1.0/1.5cm | 从官方 XML 精确提取 Emu 值 |
| 节标题加粗 | 觉得标题应该加粗 | 官方模板节标题 15pt **不加粗** |
| 单一超大表格 | 把所有内容塞一张表 | 严格按 6 表分拆 |
| 列宽硬编码 | 所有行用固定值 | 管辖权行用不同列宽（2332/7012） |
| 说明书浓缩为1段 | 布局提取合并了段落 | 说明书必须输出为独立多段 |

### 4. 不同案由的表结构差异

核心结构（4~6 表案由，占 80%+）：

```
T0: 说明 + 当事人信息 + 原告(自然人) + 原告(法人)
T1: 代理人 + 被告(自然人) + 被告(法人) + 第三人(自然人) + 第三人(法人)
T2: 第三人org类型 + 诉讼请求(header) + claims + 管辖/保全(header) + 2项
T3: 事实与理由(header) + facts part 1
T4: facts part 2 + 调解意愿(header) + mediation items
T5: mediation 续（benefit 5 + 是否考虑调解）
```

复杂案由（7~13 表，IP/海事/垄断等）额外添加：涉外/港澳台、关联案件/程序、鉴定申请等专有表。

### 5. 数据驱动架构说明

- `references/table_layouts.json`（104KB）：33个案由的完整表布局，逐行记录类型（merged/section_header/label_data）和标签文本
- `references/templates.json`（174KB）：67个案由的字段定义（claims/facts 的 key-label-hint 三元组）
- `scripts/generate_docx.py`（v8）：读取 layout + 数据 JSON，自动匹配案由并生成正确表结构

## 案由 ID 对照表

| ID | 名称 | ID | 名称 |
|----|------|----|------|
| `mjjd` | 民间借贷纠纷 | `jrjk` | 金融借款合同纠纷 |
| `maimai` | 买卖合同纠纷 | `fwmm` | 房屋买卖合同纠纷 |
| `fwzl` | 房屋租赁合同纠纷 | `jsgc` | 建设工程施工合同纠纷 |
| `wyfw` | 物业服务合同纠纷 | `xyk` | 信用卡纠纷 |
| `rongzi` | 融资租赁合同纠纷 | `jishu` | 技术合同纠纷 |
| `lihun` | 离婚纠纷 | `ldzy` | 劳动争议纠纷 |
| `jtsg` | 机动车交通事故责任纠纷 | `bxcss` | 财产损失保险合同纠纷 |
| `bzxbx` | 保证保险合同纠纷 | `rsbx` | 人身保险合同纠纷 |
| `zebx` | 责任保险合同纠纷 | `zqxjcs` | 证券虚假陈述责任纠纷 |
| `shangbiao` | 侵害商标权纠纷 | `fmzl` | 侵害发明专利权纠纷 |
| `wgsj` | 侵害外观设计专利权纠纷 | `zhuzuoquan` | 侵害著作权及邻接权纠纷 |
| `zwxpz` | 侵害植物新品种权纠纷 | `bzdj` | 不正当竞争纠纷 |
| `longduan` | 垄断纠纷 | `syms` | 侵害商业秘密纠纷 |
| `hjwr` | 环境污染民事公益诉讼 | `stph` | 生态破坏民事公益诉讼 |
| `stsh` | 生态环境损害赔偿诉讼 | `cbpz` | 船舶碰撞损害责任纠纷 |
| `hsrs` | 海上通海水域人身损害 | `hshyd` | 海上货运代理合同纠纷 |
| `cylw` | 船员劳务合同纠纷 | `general` | 通用模板 |

## 对话式转换工作流

### Step 1：提取文本

```bash
python "~/.workbuddy/skills/bude-element-lawsuit/scripts/extract_text.py" "<文件路径>"
```

### Step 2：AI 分析

阅读起诉状全文，输出 JSON。关键规则：
- 从 `references/templates.json` 读取该 caseType 的 claims/facts 字段定义
- 所有字段值严格对应模板，不得自创字段
- 起诉状中没有的信息留空字符串 `""`，不得编造
- 性别/出生日期可从身份证号推断
- claims 中的 lawyerFee/preservation 为 "yes"/"no"
- jurisdiction.mediation 为 "yes"/"no"

```json
{
  "caseType": "jrjk",
  "caseTypeName": "金融借款合同纠纷",
  "court": "合肥市包河区人民法院",
  "plaintiffs": [
    {"type": "org", "name": "", "legalRep": "", "addr": "", "regAddr": "",
     "job": "", "phone": "", "creditCode": "", "orgType": "有限责任公司", "ownership": "民营"},
    {"type": "person", "name": "", "gender": "男", "birth": "", "nation": "汉族",
     "idNum": "", "addr": "", "phone": "", "work": "", "job": ""}
  ],
  "defendants": [],
  "thirds": [],
  "agent": {"has": false, "name": "", "job": "", "firm": "", "phone": "", "auth": "general"},
  "claims": {"full": "", "total": "", "lawyerFee": "no", "preservation": "no",
             "claim_01": "", "claim_02": "", "claim_03": "", "claim_04": "",
             "claim_05": "", "claim_06": "", "claim_07": "", "claim_08": ""},
  "facts": {"facts_00": "", "facts_01": "", "facts_02": "", "facts_03": "",
            "facts_04": "", "facts_05": "", "facts_06": "", "facts_07": "",
            "facts_08": "", "facts_09": "", "facts_10": "", "facts_11": "",
            "facts_12": "", "facts_13": "", "facts_14": "", "facts_15": "",
            "facts_16": "", "facts_17": "", "facts_18": ""},
  "jurisdiction": {"court": "", "basis": "", "date": "", "mediation": "no"}
}
```

### Step 3：生成 DOCX

```bash
python "~/.workbuddy/skills/bude-element-lawsuit/scripts/generate_docx.py" \
  "<临时JSON路径>" "<输出DOCX路径>"
```

### Step 4：交付

告知文件路径，提供简要摘要（案由、当事人数量、关键诉请）。

## 目录结构

```
bude-element-lawsuit/
├── SKILL.md                    # 本文件（含经验和规范）
├── assets/
│   ├── index.html              # Web版入口
│   └── bude-convert-v10.2-reference.html  # 原始参考
│   ├── css/style.css
│   └── js/app.js
├── references/
│   ├── table_layouts.json      # ⭐ 33个案由完整表布局（从82号模板提取）
│   ├── templates.json          # ⭐ 67个案由字段定义
│   └── fields-structure.md     # 字段定义结构说明
├── scripts/
│   ├── extract_text.py         # Step 1: DOCX/PDF 文本提取
│   ├── generate_docx.py        # Step 3: 数据驱动 DOCX 生成器 (v8)
│   ├── extract_templates_json.js  # 从 app.js 提取模板
│   └── extract.py              # CSS/JS 拆分工具
└── outputs/                    # 生成的 DOCX
```
