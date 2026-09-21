---
name: cross-examination-opinion-civil-admin
description: 根据对方证据清单，生成格式规范的专业质证意见书（.docx）。支持民事、行政案件类型。
metadata:
  display_name: 质证意见（民事或行政案件AI撰写）Plus
  author: 浙江金道律师事务所龚家勇律师（微信：13967182079）
  author_public: false
  agent_created: true
---

# 质证意见生成

## 使用场景

诉讼律师在庭审前需要就对方当事人提交的证据逐一发表质证意见，形成书面《质证意见》提交法庭。本 Skill 根据用户提供的对方证据，自动分析并生成一份格式规范、逻辑严谨的 .docx 质证意见文件。

## 输入信息

用户需要提供以下信息（可以在对话中逐项提供，也可以一次性提供）：

### 必填信息
1. **案件类型**：民事 / 行政
2. **质证方**：发表质证意见的一方当事人姓名/名称
3. **举证方**：提交证据的一方当事人姓名/名称
4. **证据提供方式**：逐份提供 / 整体提供（详见「生成流程」）

### 证据信息
5. **证据清单**：每条证据包含：
   - 证据编号（如"证据1"、"证据2"）
   - 证据名称（如《XX合同》《XX发票》）
   - 页码范围（如"第1-8页"）

### 逐条质证内容（每条证据，方式 A 由用户提供，方式 B 由 AI 分析生成）
6. **对真实性的意见**：认可/不认可/部分认可 + 理由
7. **对合法性的意见**：认可/不认可/部分认可 + 理由
8. **对关联性的意见**：认可/不认可/部分认可 + 理由
9. **对证明对象的异议**（核心部分）：
   - 首先，……（第一层论证）
   - 其次，……（第二层论证）
   - 最后，……（第三层论证）
   - 可继续扩展"此外""同时"等层次
10. **特别说明**（可选，须用户提供己方证据材料）：关联己方证据的交叉引用。格式为：「特别说明，{质证方}陈述的如上异议意见，不仅可以从{举证方}提交的证据中体现，还可以从{质证方}提交的{己方证据编号}所证明的……内容中体现（详见{质证方}证据第…页）。」
    - **【强制规则】**：撰写「特别说明」前，必须先提醒用户上传其己方证据材料（证据清单、证明内容、对应页码）。如果用户未上传或未提供，则该部分直接省略，不在 .docx 中生成。

## 文档结构

生成的 .docx 文件按以下结构组织：

```
┌─────────────────────────────────────────────┐
│ 标题：{质证方}对{举证方}证据{N}-{M}的质证意见    │
│ （居中、宋体、22pt/四号、加粗）                  │
│ 其中 N 为证据清单中首份证据的编号（如"1"），       │
│ M 为末份证据的编号（如"5"）。如仅质证单份证据，    │
│ 则标题为「证据{N}」而非「证据{N}-{M}」。           │
├─────────────────────────────────────────────┤
│                                             │
│ {举证方}证据1：《……》（第X-Y页）。               │
│                                             │
│ {质证方}质证意见：                            │
│   1.对真实性的意见：……                        │
│   2.对合法性的意见：……                        │
│   3.对关联性的意见：……                        │
│   4.对证明对象有异议，具体：                    │
│      首先，……                                │
│      其次，……                                │
│      最后，……                                │
│                                             │
│   特别说明，……（可选）                         │
│                                             │
│ ---（分页或分段分隔）---                       │
│                                             │
│ {举证方}证据2：《……》（第X-Y页）。               │
│ {质证方}质证意见：……                          │
│                                             │
├─────────────────────────────────────────────┤
│ 落款（右对齐）：                               │
│   质证人：{质证方}                             │
│   特别授权代理人：                             │
│   年    月    日                              │
├─────────────────────────────────────────────┤
│ 【风险告知】（加粗、居中标题）                   │
│                                              │
│ 本《质证意见》由 AI 辅助生成，请务必人工核对     │
│ 以下事项：                                     │
│                                              │
│ ☐ 诉讼时效是否已届满                            │
│ ☐ 保证期间是否已过                              │
│ ☐ 除斥期间是否已过                              │
│ ☐ 其他法定期间/约定期间是否已届满                 │
│                                              │
│ AI 已根据用户提供的材料进行分析，但无法替代       │
│ 律师的专业判断。如 AI 分析结论与您的判断不一致，   │
│ 请以您的专业判断为准并修改相关内容。              │
│                                              │
│ 如 AI 无法从材料中确定上述事项，已在下方明确标注   │
│ 为「无法判断」，请您人工核实。                    │
│                                              │
│ 分析结果：                                     │
│ · 诉讼时效：{AI分析结论或「无法判断」}            │
│ · 保证期间：{AI分析结论或「无法判断」}            │
│ · 除斥期间：{AI分析结论或「无法判断」}            │
│ · 其他期间：{AI分析结论或「无法判断」}            │
└─────────────────────────────────────────────┘
```

## 格式规范

使用 docx-js（npm 包 `docx`）生成 .docx 文件，严格遵循以下格式：

| 元素 | 字体 | 字号 | 加粗 | 对齐 |
|------|------|------|------|------|
| 标题 | 宋体 | 22pt (44 half-pts) | 是 | 居中 |
| 正文 | 宋体 | 12pt (24 half-pts) | 否 | 两端对齐 (both) |
| 落款 | 宋体 | 12pt (24 half-pts) | 否 | 右对齐 |
| 风险告知标题 | 宋体 | 14pt (28 half-pts) | 是 | 居中 |
| 风险告知正文 | 宋体 | 12pt (24 half-pts) | 否 | 两端对齐 (both) |

- 纸张：A4
- 页边距：上下 2.54cm（1440 DXA），左右 3.17cm（1800 DXA）——Word 默认值
- 行距：正文段后 120 DXA（约 6pt）

## 质证逻辑规范

### 质证三性标准

**真实性**：
- 认可：证据原件已核对，无伪造、变造痕迹
- 不认可：应说明理由（如：无原件核对、签章不实、内容矛盾等）
- 部分认可：区分认可与不认可的部分

**合法性**：
- 认可：证据来源、形式、收集程序合法
- 不认可：应说明理由（如：证据来源不明、收集程序不合法、形式要件欠缺等）

**关联性**：
- 认可：证据与待证事实存在逻辑关联
- 不认可：说明证据与案件争点无关的理由

**证明对象异议**（质证的核心）：
- 不认可对方对证据的解读或从中推导的结论
- 应采用"首先—其次—最后"的递进结构
- 每层论证应有逻辑支撑，避免空泛断言

### 案件类型差异

**民事案件**：
- 侧重证据的真实性、合法性、关联性以及证明力大小
- 质证重点：证据的证明力是否足以支持对方主张的待证事实
- 语言相对中性，以事实和逻辑论证为主
- 注意区分证据能力与证明力两个层次
- 如需援引法律依据，连接「华宇元典法律数据 MCP」检索最新法规条文

**行政案件**：
- 强调被告对行政行为合法性的举证责任（《行政诉讼法》第34条）
- 质证重点：被告证据是否在行政程序中已收集、是否在法定期限内提交、收集程序是否合法
- 优先审查证据的行政收集程序合法性——证据来源、取证主体、取证方式、是否侵犯相对人合法权益
- 关注行政程序的合法性、证据的行政收集程序
- 可质疑被告在诉讼中补充收集的证据不具有合法性
- **注意**：在行政赔偿、补偿案件及行政机关不履行法定职责案件中，原告对损害事实、提出申请等事实负有举证责任。此时质证策略应相应调整——如我方为被告，可重点质证原告证据的证明力是否充分。
- 如需援引法律依据，连接「华宇元典法律数据 MCP」检索最新法规条文

## 时效与期间分析

### 分析范围

在撰写质证意见过程中，必须从用户提供的对方证据、己方意见及证据中，尝试分析以下内容：

1. **诉讼时效**：是否已届满（普通诉讼时效3年，特殊规定除外）
2. **保证期间**：是否已过（一般保证/连带保证的保证期间）
3. **除斥期间**：是否已过（如撤销权、解除权等形成权的除斥期间）
4. **其他法定/约定期间**：是否存在可能影响案件实体权利的其他期间

### 分析规则

- **能分析出明确结论的**：将结论写入质证意见正文相关位置（如在「证明对象异议」或「关联性」意见中论证时效已过/未过），同时在尾部「风险告知」中标注分析结论。
- **无法分析出明确结论的**：不在正文中写入任何关于时效/期间的断言，但在尾部「风险告知」中对应条目标注为「无法判断，请人工核实」。
- **分析依据仅限于用户提供的材料**。不得凭空推测任何日期、事件或期间。

### 分析提示

在撰写质证意见前，从用户提供的材料中提取以下关键日期（如有）：
- 合同签订日期、履行期限
- 债务到期日
- 保证合同约定的保证期间
- 权利发生日（如知道或应当知道撤销事由之日）
- 起诉日/申请仲裁日（如有）

如上述日期均无法从材料中获取，则所有条目均标注「无法判断」。

## 文件格式处理

用户上传的证据文件可能为多种格式，根据格式采用对应的处理方式：

| 格式 | 处理方式 |
|------|----------|
| `.docx` | 使用 `python-docx` 或直接调用系统命令提取文本 |
| `.pdf` | 使用 `pdftotext` 或 PyMuPDF（fitz）提取文本；如为扫描件则需 OCR |
| 图片（`.jpg`/`.png` 等） | 如为扫描件/照片，优先使用 OCR 提取文字；如为照片证据则描述图像内容 |
| 文字描述 | 用户直接在对话中提供的文字描述，直接使用 |
| `.txt` / `.md` | 直接读取文本内容 |

**OCR 处理**：如 PDF 为扫描件或图片无法直接提取文本，使用 macOS 内置 OCR 或 Tesseract 进行文字识别。如 OCR 结果不理想，提醒用户提供文字版本。

**多文件整合**：如用户一次上传多个文件，先逐一提取/读取内容，再汇总分析。

## 生成流程

### 第一阶段：基础信息收集

1. 向用户说明三种启动方式，由用户选择：

   > 请选择启动方式：
   > **方式 1**：您先告诉我案件类型（民事/行政）、质证方名称、举证方名称，我再询问后续信息。
   > **方式 2**：您直接上传对方证据清单及证据文件，并说明贵方主体是谁、对方主体是谁、案件类型（民事/行政）。
   > **方式 3**：您直接上传对方证据清单及证据文件，由我根据材料分析推断贵方主体和对方主体，再请您确认。

2. 根据用户选择执行：

   **方式 1**：依次询问并接收案件类型、质证方名称、举证方名称。

   **方式 2**：等待用户上传证据并说明双方主体及案件类型（民事/行政），确认后跳过第二阶段，直接进入第三阶段方式 B 的第 2b 步（询问是否提供贵方材料）。

   **方式 3**：
   - 阅读用户上传的证据材料，从中分析推断：
     - 对方主体（举证方）：通常为证据清单中标注的提交方
     - 我方主体（质证方）：通常为证据清单中标注的质证对象或行政裁判文书中的相对方
   - 将分析结果展示给用户确认，例如：
     > 根据材料分析，我推断：
     > - 举证方（对方）：XXX
     > - 质证方（贵方）：XXX
     > - 案件类型：民事（默认，如材料显示为行政案件则推断为行政）
     >
     > 请确认以上信息是否正确？如有误请修正。
   - 用户确认或修正后，跳过第二阶段，直接进入第三阶段方式 B 的第 2b 步（询问是否提供贵方材料）。

### 第二阶段：证据提供方式选择

> **注意**：本阶段仅适用于第一阶段选择「方式 1」的用户。选择「方式 2」或「方式 3」的用户已在第一阶段上传了证据，直接进入第三阶段方式 B 的第 2b 步。

3. 在收集证据清单之前，**必须询问用户选择证据提供方式**：

   > 请问您希望以哪种方式提供对方证据？
   > **A. 逐份提供**：您一份一份提供对方证据及质证意见，我逐一撰写质证意见文本，您核对后我再处理下一份，最后汇总生成完整《质证意见》。
   > **B. 整体提供**：您一次性提供所有对方证据，我根据证据独立分析并撰写完整《质证意见》初稿，再请您核对修改。

### 第三阶段：按选定方式执行

#### 方式 A：逐份提供

1a. 用户提供第1份证据（编号、名称、页码）及对应的质证意见（真实性/合法性/关联性/证明对象异议）
2a. 撰写该份证据的质证意见文本，展示给用户核对
3a. 用户确认无误后，询问：是否需要为此条证据撰写「特别说明」？
   - 如需，请用户提供己方证据材料（己方证据编号、名称、证明内容、对应页码）
   - 如不需要或未提供，跳过
4a. 询问用户：「下一份证据？」重复步骤 1a–3a，直到用户表示全部证据处理完毕
5a. **时效与期间分析**：汇总所有证据及意见，执行「时效与期间分析」流程，将分析结论填入「风险告知」
6a. 汇总所有已确认的质证意见 + 风险告知，展示完整文本供用户最终确认
7a. **最后补充机会**：再次询问用户是否需要为任何证据补充「特别说明」（如已在步骤 3a 中提供过，则无需重复）。如需补充，请提供己方证据材料；如不需要，则跳过
8a. 询问用户：「是否需要将《质证意见》转化为 .docx 文件并保存到您的桌面？」
9a. 用户确认后，文件命名为《质证意见》（{质证方}VS{举证方}）.docx，例如《质证意见》（张三VSXX公司）.docx
10a. 检查桌面是否已有同名文件，如有则询问是否覆盖
11a. 使用 docx-js 生成 .docx 文件，保存至 `/Users/gongjiayong/Desktop/质证意见（{质证方}VS{举证方}）.docx`
12a. 调用 `python scripts/office/validate.py` 验证文件有效性
13a. 用 `present_files` 展示给用户

#### 方式 B：整体提供

1b. 提醒用户一次性提供对方提交的所有证据清单及证据文件（不限制格式：PDF、Word、图片、文字描述均可）。**（如用户通过第一阶段方式 2/3 已上传证据，则跳过此步。）**
2b. 用户提供对方证据后，**必须询问用户以下选择**：

   > 请问您是否需要提供贵方材料以辅助 AI 分析？
   > **选项 1**：我上传贵方材料（起诉状、答辩状、代理词、质证方证据等）。AI 将结合贵方意见及证据综合撰写。
   > **选项 2**：我暂不提供。AI 仅根据对方证据独立分析撰写，不影响《质证意见》的生成。

3b. 根据用户选择执行：

   **如用户选择选项 1**：
   - 等待用户提供贵方材料（不限格式）
   - 综合分析：对方证据 + 贵方初步意见（即起诉状、答辩状、代理词等文书中已表达的质证立场和观点） + 贵方证据，从中提取质证观点
   - 询问用户：「以上证据中，哪些需要撰写『特别说明』？」请用户逐条指定，并提供对应的己方证据材料（己方证据编号、名称、证明内容、对应页码）。未指定的证据则不写特别说明。
   - 一次性撰写完整《质证意见》初稿（文本形式），展示给用户

   **如用户选择选项 2**：
   - 直接根据对方证据独立分析，提取可质证的观点
   - 询问用户：「以上证据中，哪些需要撰写『特别说明』？」请用户逐条指定，并提供对应的己方证据材料（己方证据编号、名称、证明内容、对应页码）。未指定的证据则不写特别说明。
   - 一次性撰写完整《质证意见》初稿（文本形式），展示给用户

4b. **时效与期间分析**：在初稿尾部附上「风险告知」，展示分析结论。如任何条目为「无法判断」，在风险告知中明确标注并提醒用户人工核实
5b. 初稿展示完毕后，告知用户：「以上为初稿，请核对并提出修改意见。如需调整论证角度、补充具体理由或修改措辞，请告知。」
6b. 根据用户反馈修改至用户满意（包括风险告知内容）。如用户表示无需修改，则询问：「是否需要将《质证意见》转化为 .docx 文件并保存到您的桌面？」
7b. 用户确认后，文件命名为《质证意见》（{质证方}VS{举证方}）.docx，例如《质证意见》（张三VSXX公司）.docx
8b. 检查桌面是否已有同名文件，如有则询问是否覆盖
9b. 使用 docx-js 生成 .docx 文件，保存至 `/Users/gongjiayong/Desktop/质证意见（{质证方}VS{举证方}）.docx`
10b. 调用 `python scripts/office/validate.py` 验证文件有效性
11b. 用 `present_files` 展示给用户

## 代码模板

生成时使用以下 docx-js 代码框架。**注意**：docx 包安装在 `/Users/gongjiayong/.workbuddy/binaries/node/workspace/node_modules/`，执行脚本时必须设置 `NODE_PATH`：

```javascript
// 执行方式：
// NODE_PATH=/Users/gongjiayong/.workbuddy/binaries/node/workspace/node_modules \
//   /Users/gongjiayong/.workbuddy/binaries/node/versions/22.12.0/bin/node gen_doc.js

const { Document, Packer, Paragraph, TextRun, AlignmentType } = require('docx');
const fs = require('fs');

const doc = new Document({
  styles: {
    default: {
      document: {
        run: { font: "宋体", size: 24 }, // 12pt 正文
      },
    },
  },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 }, // A4
        margin: { top: 1440, bottom: 1440, left: 1800, right: 1800 },
      },
    },
    children: [
      // 标题
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 360 },
        children: [
          new TextRun({
            text: "张三对XXX公司证据1-2的质证意见",
            font: "宋体",
            size: 44,
            bold: true,
          }),
        ],
      }),

      // 证据1
      new Paragraph({
        alignment: AlignmentType.JUSTIFIED,
        spacing: { after: 120 },
        children: [
          new TextRun({ text: "XXX公司证据1：《……合同》（第1-8页）。", font: "宋体", size: 24 }),
        ],
      }),

      new Paragraph({
        alignment: AlignmentType.JUSTIFIED,
        spacing: { before: 200, after: 120 },
        children: [
          new TextRun({ text: "张三质证意见：", font: "宋体", size: 24 }),
        ],
      }),

      // 1. 真实性
      new Paragraph({
        alignment: AlignmentType.JUSTIFIED,
        spacing: { after: 120 },
        children: [
          new TextRun({ text: "1.对真实性的意见：……", font: "宋体", size: 24 }),
        ],
      }),

      // 2. 合法性
      new Paragraph({
        alignment: AlignmentType.JUSTIFIED,
        spacing: { after: 120 },
        children: [
          new TextRun({ text: "2.对合法性的意见：……", font: "宋体", size: 24 }),
        ],
      }),

      // 3. 关联性
      new Paragraph({
        alignment: AlignmentType.JUSTIFIED,
        spacing: { after: 120 },
        children: [
          new TextRun({ text: "3.对关联性的意见：……", font: "宋体", size: 24 }),
        ],
      }),

      // 4. 证明对象异议
      new Paragraph({
        alignment: AlignmentType.JUSTIFIED,
        spacing: { after: 120 },
        children: [
          new TextRun({ text: "4.对证明对象有异议，具体：", font: "宋体", size: 24 }),
        ],
      }),
      new Paragraph({
        alignment: AlignmentType.JUSTIFIED,
        spacing: { after: 120 },
        indent: { firstLine: 480 },
        children: [
          new TextRun({ text: "首先，……", font: "宋体", size: 24 }),
        ],
      }),
      new Paragraph({
        alignment: AlignmentType.JUSTIFIED,
        spacing: { after: 120 },
        indent: { firstLine: 480 },
        children: [
          new TextRun({ text: "其次，……", font: "宋体", size: 24 }),
        ],
      }),
      new Paragraph({
        alignment: AlignmentType.JUSTIFIED,
        spacing: { after: 120 },
        indent: { firstLine: 480 },
        children: [
          new TextRun({ text: "最后，……", font: "宋体", size: 24 }),
        ],
      }),

      // 特别说明（可选）
      new Paragraph({
        alignment: AlignmentType.JUSTIFIED,
        spacing: { after: 360 },
        children: [
          new TextRun({ text: "特别说明，……", font: "宋体", size: 24 }),
        ],
      }),

      // ===== 证据分隔（仅2份及以上证据时使用）=====
      // 在每两份证据之间插入分隔线，即证据N的特别说明之后、证据N+1之前。
      // 单份证据时跳过此段。实际生成代码时应以循环结构控制。
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 400, after: 400 },
        children: [
          new TextRun({ text: "————————————————————", font: "宋体", size: 24 }),
        ],
      }),

      // 证据2（示例：分隔线后紧跟下一份证据）
      new Paragraph({
        alignment: AlignmentType.JUSTIFIED,
        spacing: { after: 120 },
        children: [
          new TextRun({ text: "XXX公司证据2：《……》（第X-Y页）。", font: "宋体", size: 24 }),
        ],
      }),

      // 落款
      new Paragraph({ spacing: { before: 600 }, children: [] }),
      new Paragraph({
        alignment: AlignmentType.RIGHT,
        spacing: { after: 120 },
        children: [
          new TextRun({ text: "质证人：张三", font: "宋体", size: 24 }),
        ],
      }),
      new Paragraph({
        alignment: AlignmentType.RIGHT,
        spacing: { after: 120 },
        children: [
          new TextRun({ text: "特别授权代理人：", font: "宋体", size: 24 }),
        ],
      }),
      new Paragraph({
        alignment: AlignmentType.RIGHT,
        spacing: { after: 120 },
        children: [
          new TextRun({ text: "年    月    日", font: "宋体", size: 24 }),
        ],
      }),

      // ===== 风险告知 =====
      new Paragraph({ spacing: { before: 600 }, children: [] }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 240 },
        children: [
          new TextRun({ text: "【风险告知】", font: "宋体", size: 28, bold: true }),
        ],
      }),
      new Paragraph({
        alignment: AlignmentType.JUSTIFIED,
        spacing: { after: 120 },
        children: [
          new TextRun({ text: "本《质证意见》由 AI 辅助生成，请务必人工核对以下事项：", font: "宋体", size: 24 }),
        ],
      }),
      new Paragraph({
        alignment: AlignmentType.JUSTIFIED,
        spacing: { after: 120 },
        children: [
          new TextRun({ text: "☐ 诉讼时效是否已届满", font: "宋体", size: 24 }),
        ],
      }),
      new Paragraph({
        alignment: AlignmentType.JUSTIFIED,
        spacing: { after: 120 },
        children: [
          new TextRun({ text: "☐ 保证期间是否已过", font: "宋体", size: 24 }),
        ],
      }),
      new Paragraph({
        alignment: AlignmentType.JUSTIFIED,
        spacing: { after: 120 },
        children: [
          new TextRun({ text: "☐ 除斥期间是否已过", font: "宋体", size: 24 }),
        ],
      }),
      new Paragraph({
        alignment: AlignmentType.JUSTIFIED,
        spacing: { after: 120 },
        children: [
          new TextRun({ text: "☐ 其他法定期间/约定期间是否已届满", font: "宋体", size: 24 }),
        ],
      }),
      new Paragraph({ spacing: { after: 120 }, children: [] }),
      new Paragraph({
        alignment: AlignmentType.JUSTIFIED,
        spacing: { after: 120 },
        children: [
          new TextRun({ text: "AI 已根据用户提供的材料进行分析，但无法替代律师的专业判断。如 AI 分析结论与您的判断不一致，请以您的专业判断为准并修改相关内容。", font: "宋体", size: 24 }),
        ],
      }),
      new Paragraph({
        alignment: AlignmentType.JUSTIFIED,
        spacing: { after: 120 },
        children: [
          new TextRun({ text: "如 AI 无法从材料中确定上述事项，已明确标注为「无法判断」，请您人工核实。", font: "宋体", size: 24 }),
        ],
      }),
      new Paragraph({ spacing: { after: 120 }, children: [] }),
      new Paragraph({
        alignment: AlignmentType.JUSTIFIED,
        spacing: { after: 120 },
        children: [
          new TextRun({ text: "分析结果：", font: "宋体", size: 24, bold: true }),
        ],
      }),
      new Paragraph({
        alignment: AlignmentType.JUSTIFIED,
        spacing: { after: 120 },
        children: [
          new TextRun({ text: "· 诉讼时效：{AI分析结论或「无法判断，请人工核实」}", font: "宋体", size: 24 }),
        ],
      }),
      new Paragraph({
        alignment: AlignmentType.JUSTIFIED,
        spacing: { after: 120 },
        children: [
          new TextRun({ text: "· 保证期间：{AI分析结论或「无法判断，请人工核实」}", font: "宋体", size: 24 }),
        ],
      }),
      new Paragraph({
        alignment: AlignmentType.JUSTIFIED,
        spacing: { after: 120 },
        children: [
          new TextRun({ text: "· 除斥期间：{AI分析结论或「无法判断，请人工核实」}", font: "宋体", size: 24 }),
        ],
      }),
      new Paragraph({
        alignment: AlignmentType.JUSTIFIED,
        spacing: { after: 120 },
        children: [
          new TextRun({ text: "· 其他期间：{AI分析结论或「无法判断，请人工核实」}", font: "宋体", size: 24 }),
        ],
      }),
    ],
  }],
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("/Users/gongjiayong/Desktop/质证意见（张三VSXXX公司）.docx", buffer);
});
```

## 注意事项

1. **【重要】措辞规范**：质证意见是正式法律文书，措辞必须严谨、准确，避免口语化。不得使用感叹号、问号等非正式标点，不得使用比喻、夸张等修辞手法。
2. **【重要】真实性核查**：对真实性的质证，如涉及原件核对情况，必须如实说明是否已核对原件。如未核对原件，应明确表述「未核对原件」。
3. **【重要】避免三性重复**：「证明对象异议」部分应避免仅重复三性意见，应针对对方欲证明的待证事实展开反驳，从逻辑、事实、法律适用等层面独立论证。
4. **【重要】页码标注**：证据超过一页时，页码范围用「第X-Y页」格式标注。单页证据标注「第X页」。
5. **【重要】多份证据合并**：如质证涉及多份证据但意见相近，可在单条质证中合并处理，但需在开头明确列出所有涉及的证据编号（如「证据1、3、5」），再撰写统一的质证意见。
6. **【重要】质证意见正文中一般不引用法律法规、司法解释的具体条文**。质证理由应从事实和逻辑层面展开论证，而非罗列法条。如果确有必要引用（例如涉及法定证据排除规则等），应连接「华宇元典法律数据 MCP」检索相关条文原文，确保引用准确。
7. **【重要】「特别说明」部分依赖用户己方证据材料**。在生成质证意见过程中，必须询问用户是否需要撰写「特别说明」。如用户选择需要，则要求其提供己方证据编号、名称、证明内容及对应页码；如用户未提供材料或明确表示不需要，则「特别说明」部分直接省略，不在最终文档中生成。
8. **【重要】尾部「风险告知」为必填内容**。每份《质证意见》尾部必须附上风险告知，内容包含：
   - 明确声明本文件由 AI 辅助生成，需人工核对
   - 列出诉讼时效、保证期间、除斥期间、其他法定/约定期间四项核查清单
   - 逐项标注 AI 分析结论或「无法判断，请人工核实」
   - 如 AI 无法从材料中确定某一项，必须标注「无法判断」而非凭空推测
9. **【重要】时效与期间分析仅依据用户提供的材料**。不得引入材料之外的任何日期、事件或法律推定。如果材料中缺少关键日期（如合同签订日、债务到期日、起诉日等），相关分析条目应标注「无法判断」。
10. **【重要】生成 docx 前检查桌面文件是否存在**。文件命名格式为《质证意见》（{质证方}VS{举证方}）.docx。如果桌面已存在同名文件，必须先询问用户是否覆盖，再继续生成。
