---
name: chinese-legal-doc-drafting
description: 中文合同起草与公文撰写 Skill。起草符合中国法律要求的合同（租房/劳务/采购/合作/股权）及党政机关公文（通知/报告/请示/函）。内置 3662+ Word 模板库（98-商业合同/99-劳动合同分类）+ 31 部中国法律（民法典/劳动法/公司法等）+ ZVec 向量知识库，先检索法条 + 匹配模板 + 格式规范生成 .docx。当用户说"起草合同"/"写合同"/"拟合同"/"草拟协议"/"打合同"/"搞个合同"/"做合同"/"弄份合同"/"需要个合同"/"帮我拟个合同"/"签合同"/"来份合同"/"开个合同"/"整份合同"/"给写个合同"/"给拟个合同"/"弄个租房合同"/"出个租房合同"/"写个租房合同"/"出合同"/"拟一份"/"起草通知"/"写通知"/"出个通知"/"写公文"/"发个函"/"搞个通知"/"要个通知"/"写报告"/"写请示"/"发个报告"/"审合同格式"/"更新数据"/"更新数据集"/"刷新数据"/"同步数据"时触发。**注意：本 skill 不提供自动化合同法律风险审查**。
---

# 中文合同起草 & 公文撰写

> 先检索法律和模板，再起草合同/公文。**不审查**法律风险。

⚠️ **免责声明**：本 skill 输出仅作参考，**不构成法律建议**。签署前**必须经执业律师审查**。

## ⚡ 30秒速查（用户原话→skill 行为）

| 用户原话（任一触发） | skill 行为 |
|----------------------|------------|
| "起草合同"/"写合同"/"帮我拟个合同"/"拟合同"/"草拟协议"/"弄个租房合同"/"出个租房合同" | 启动 Step 0-5 合同工作流 |
| "写通知"/"出个通知"/"写公文"/"发个函"/"写报告"/"写请示" | 启动 gov-doc 编写阶段（Step 2b） |
| "编辑公文"/"修改通知"/"改一下报告" | 启动 gov-doc 编辑阶段（Step 2b） |
| "审核公文"/"送审稿"/"出送审版本" | 启动 gov-doc 审核阶段（Step 2b） |
| "审合同风险"/"审查采购合同" | ⚠️ 不支持：告知"本 skill 不提供自动化审查"，仅返回格式规范文档供人工比对 |
| "更新数据"/"更新数据集"/"刷新数据"/"同步数据" | 执行 `bash scripts/download_data.sh` 删除旧数据、下载并解压新数据 |
| "合同格式对吗"/"字号字体规范吗"/"格式审查" | 查 `references/文件合同格式规范.md` 返回格式要点 |

## 🔴 关键关卡（LLM 必扫，5 条关卡集中化）

| 触发条件 | 关卡类型 | 强制动作 |
|----------|----------|----------|
| 用户需求模糊（无金额/期限/标的/身份信息等） | 🔴 CHECKPOINT | 逐项追问，**禁止自行假设** |
| 模板缺少法律强制项 | 🔴 CHECKPOINT | **必须**追问到位才能进入 Step 4 |
| 文档类型为 `gov-doc` | 🔴 CHECKPOINT | 确认工作阶段（编写/编辑/审核，Step 2b）再继续 |
| 涉及未在 31 部法律库覆盖的领域 | 🔴 CHECKPOINT | 提示用户并按行业惯例起草 |
| 合同生成完成 | 🛑 STOP | 提醒用户**建议律师审查**后才能签署 |

> LLM 解析规则：遇到 🔴 CHECKPOINT 必须**停下来等待用户输入**，**禁止跳过**；遇到 🛑 STOP 必须**最后输出提醒**。

## 📄 格式规范（强制）

🔴 **规则：生成任何合同/公文前，必须先用 Read 工具读取 `references/文件合同格式规范.md`，将其全部内容纳入上下文。所有输出的字体、字号、行距、版面、结构必须严格遵循该文件中的规范。`docx_utils.py` 已内置这些格式参数，禁止绕过。**

🔴 **封面页强制规则：合同必须包含封面页，封面页必须单独占一页（封面后插入分页符）。必须使用 `docx_utils.py` 中的 `add_cover_page()` 函数生成封面页，禁止手动拼封面。**

```python
from scripts.docx_utils import add_cover_page

add_cover_page(
    doc,
    title_cn='合同中文名称',
    title_en='Contract English Name',
    contract_no='HT-2026-001',
    party_a_label='甲  方（出卖方）：',
    party_b_label='乙  方（买受方）：'
)
```

## 📦 安装（自动）

```bash
# 1. 确保 cy_data/ 和 cy_templates/ 已放在本目录（预构建的文档/模板向量库）
# 2. 确保 references/文件合同格式规范.md 已存在
# 3. 首次运行任意 Python 脚本时会自动安装依赖（pip install -r requirements.txt）
#    也可以手动运行：
pip install -r requirements.txt
# 4. 首次执行 search.py 时，sentence-transformers 会自动从 HuggingFace 下载
#    BAAI/bge-small-zh-v1.5 模型（~200MB）用于把用户查询编码成向量。
#    索引本身已预构建无需重新向量化。模型缓存在 ~/.cache/huggingface/ 后续运行不再下载。
# 5. 如需完整初始化测试，运行：
bash scripts/setup.sh
# 6. 如需更新向量数据（删除旧数据 + 下载新数据 + 解压到根目录），运行：
bash scripts/download_data.sh
```

## 🔄 数据更新工作流

当用户说"更新数据"/"更新数据集"/"刷新数据"/"同步数据"时，执行以下步骤：

**Step 1**: 检查配置
```bash
# 确认 scripts/config.json 存在且 token 已配置
cat scripts/config.json
```

**Step 2**: 执行更新
```bash
bash scripts/download_data.sh
```

该脚本会：
1. 删除旧的 `cy_data/` 和 `cy_templates/` 目录
2. 从远程下载最新数据压缩包
3. 解压到 skill 根目录
4. 清理临时文件

**Step 3**: 验证更新结果
```bash
# 检查新数据文件数量
ls cy_data/ | wc -l
ls cy_templates/ | wc -l
```

🔴 **规则**：更新完成后，告知用户数据已更新，建议重新测试搜索功能。

## 📋 工作流

### Step 0: 从向量知识库检索

**法律检索** — 获取相关法条作为合同依据：
```bash
python scripts/search.py law --contract-type {type} --query "押金 违约金 必备条款" --topk 5
```

**模板匹配** — 找到最合适的模板：
```bash
python scripts/search.py template --query "用户需求描述" --topk 3
```

🔴 **规则**：Step 0 的搜索结果**必须**纳入上下文。法律条文原文必须逐条审查，选取相关的作为合同条款约束依据。

### Step 1: 确定文档类型

**合同类型：** 租房→rental / 劳务→labor / 采购→procurement / 合作→cooperation / 股权→equity

**公文类型：** 通知/报告/请示/函 → gov-doc

**类型识别决策树（防误判）：**

| 用户原话关键词 | 判定类型 | 关键依据 |
|----------------|----------|----------|
| "租房/出租/承租/房东/租客/月租/押金" | **rental** | 有"租金"或"押金" |
| "雇人干活/打零工/个人提供劳务/劳务报酬" | **labor** | 个人对单位，非劳动关系（无社保/工伤） |
| "招聘/劳动合同/入职/试用期/五险一金" | **labor 升级 → 用 labor 模板 + 劳动法条款** | 劳动关系：必须含社保/工伤/解除条件 |
| "买东西/采购/订购/供货/买卖" | **procurement** | 有"标的物"或"交货" |
| "合伙/合作/共同出资/利润分成" | **cooperation** | 多人共同出资/经营（无公司形式） |
| "股权/股份/转让/代持/投资" | **equity** | 有"股权"或"转让价款" |
| "通知/报告/请示/函/批复" | **gov-doc** | 公文，进入 Step 2b |

🔴 **歧义时必须追问**：用户说"雇人干活"时，区分是"个人劳务"（labor）还是"公司招聘"（labor + 劳动法）。**禁止自行假设**。

从 Step 0 的模板搜索结果中选用最匹配的模板。

### Step 2: 检索法律约束

```bash
python scripts/search.py law --contract-type {type} --query "必备条款 强制要求" --topk 5
```

将法条原文纳入上下文，作为合同条款的约束依据。

### Step 3: 逐项追问缺失信息

对比模板已有条款和法律强制要求，找出缺失项。**每次只问一个问题，法律强制项优先。**

提问顺序：
1. **法律强制要求但在模板中缺失的条款**（押金条款、违约金上限、社保缴纳、租赁物登记）
2. **行业常见但用户未提供的条款**（保密、争议解决、不可抗力）
3. **双方身份信息确认**（出租人/承租人/统一社会信用代码/法定代表人/联系方式）

🔴 **CHECKPOINT** — 未完成法律强制项询问前，禁止进入 Step 4。

### Step 4: 依据格式规范生成合同

🔴 **前置动作：必须已读取 `references/文件合同格式规范.md`，所有格式参数以其为准。**

```python
from scripts.docx_utils import (
    create_formatted_doc, set_page_layout, add_cover_page, add_title, add_body_text,
    add_heading_level1, add_heading_level2, add_clause, add_signature_block, save_as
)

doc = create_formatted_doc()
set_page_layout(doc)

# 封面页（必须单独一页）
add_cover_page(
    doc,
    title_cn='房屋租赁合同',
    title_en='House Lease Contract',
    contract_no='HT-2026-001',
    party_a_label='甲  方（出租方）：',
    party_b_label='乙  方（承租方）：'
)

# 正文标题
add_title(doc, "房屋租赁合同")

# 当事人信息
add_body_text(doc, "甲方（出租方）：xxx")
add_body_text(doc, "乙方（承租方）：xxx")

# 正文主体 — 格式由 docx_utils 函数自动保证
add_heading_level1(doc, "第一条  租赁物")
add_body_text(doc, "出租人将下列房屋出租给承租人……")

# 文尾区域
add_signature_block(doc, party_a_name="出租人：李四", party_b_name="承租人：张三")
save_as(doc, "输出/房屋租赁合同.docx")
```

🔴 **规则**：`docx_utils.py` 中的函数已内置格式规范参数。**禁止**绕过这些函数自行设置格式。

### Step 5: 输出

- 格式：.docx（必须符合 `references/文件合同格式规范.md` 全部要求）
- 文件名使用中文含义名称，**禁止拼音或英文**
- 输出末尾附上检索到的法律依据列表
- 🛑 强制追加："⚠️ 建议聘请执业律师审查本合同后再签署"

### Step 2b: 公文三阶段工作流（如文档类型为 `gov-doc`）

**编写阶段（起草新版）**：
- 严格按 `references/文件合同格式规范.md` 的公文规范（GB/T 9704-2012）生成
- 确认：发文机关、发文字号、标题、主送机关
- 正文 3 号仿宋体首行缩进 2 字；版头（红色发文机关标志）+ 主体 + 版记完整
- 结构层次：一、（黑体）→（一）（楷体）→ 1.（仿宋）→（1）（仿宋）
- 在版记下方添加起草说明

**编辑阶段（修改已有草稿）**：
- 加载已有公文草稿，使用 Word 修订模式
- 新增内容：红色字体 + 下划线；删除内容：红色字体 + 删除线
- 存疑处加批注：`[编辑注：]`
- 每处修改标注修改人缩写 + 日期

**审核阶段（生成送审稿）**：
- 在正文前插入审核签批表（起草/审核/会签/审批四栏）
- 正文采用标准公文版式 + 正文前标注审核提示
- 输出为送审稿 .docx

## 📋 完整示例：起草北京租房合同

> 用户: "帮我起草一份北京朝阳区的租房合同，租客张三，房东李四，月租 5000 元，押一付三，租期 1 年"

**Step 0** — 法律检索：
```bash
python scripts/search.py law --contract-type rental --query "押金 违约金 维修 转租" --topk 3
```
返回：《民法典》第 703-728 条（合同编房屋租赁章）、第 711-721 条等

**Step 1** — 类型：`rental` → 选 Step 0 返回的最相关租赁模板

**Step 2** — 法律再检：
```bash
python scripts/search.py law --contract-type rental --query "必备条款 强制要求" --topk 5
```

**Step 3** — 按优先级追问（每次只问一个）：
1. 🔴 "房产证编号是多少？"（法律强制）
2. 🔴 "出租用途是住宅还是商用？"（影响条款）
3. "押一付三之外还有物业/取暖/网费吗？"
4. "张三身份证号？" / "李四身份证号？"

**Step 4** — 依据格式规范填充：
```python
from scripts.docx_utils import (
    create_formatted_doc, set_page_layout, add_cover_page, add_title, add_contract_info,
    add_body_text, add_heading_level1, add_clause, add_signature_block, save_as
)

doc = create_formatted_doc()
set_page_layout(doc)

# 封面页（必须单独一页）
add_cover_page(
    doc,
    title_cn='房屋租赁合同',
    title_en='House Lease Contract',
    contract_no='HT-2026-001',
    party_a_label='甲  方（出租方）：',
    party_b_label='乙  方（承租方）：'
)

add_title(doc, "房屋租赁合同")
add_contract_info(doc, contract_no="HT-2026-001", date="2026-07-01", party_a="出租人：李四", party_b="承租人：张三")
add_heading_level1(doc, "第一条  租赁物")
add_body_text(doc, "出租人李四将位于北京朝阳区XX路XX号的房屋出租给承租人张三。")
add_clause(doc, "押金条款：押一付三，押金 5000 元，合同终止无违约 7 日内退还。")
add_clause(doc, "法律依据：《中华人民共和国民法典》第七百零三条至第七百二十八条。")
add_signature_block(doc, party_a_name="出租人：李四", party_b_name="承租人：张三")
save_as(doc, "输出/租房合同_北京朝阳_张三李四.docx")
```

**Step 5** — 输出：
```
✅ 已生成 租房合同_北京朝阳_张三李四.docx
🔴 关键条款：押金 5000 元 / 押一付三 / 提前 30 日通知解约
📚 法律依据：《民法典》第 703-728 条、第 711-721 条
🛑 建议聘请执业律师审查本合同后再签署
```

## 🛠 失败模式

> HL-2 三段式：所有失败分支按"触发条件 / 一线修复 / 仍失败兜底"编码，**禁止**只在文末写"如有问题请联系管理员"。

| 场景 | 触发条件 | 一线修复 | 仍失败兜底 |
|------|----------|----------|------------|
| **向量库缺失** | `search` 报 `FileNotFoundError: cy_data` | 确认 `cy_data/` 和 `cy_templates/` 已放在本目录 | 列出 `references/*.docx` 法律清单让用户手动指定条款 |
| **搜索无结果** | `search` 返回 0 条 | 换关键词或去掉 `--contract-type` 过滤重试 | 列出 `templates/98-商业合同/` 和 `99-劳动合同/` 子目录让用户手动选模板 |
| **模型下载慢/超时** | 首次搜索超时 | 设置 `HF_ENDPOINT=https://hf-mirror.com`（默认已设） | 提示用户手动运行 `bash scripts/setup.sh` 重试 |
| **格式规范缺失** | `references/文件合同格式规范.md` 不存在 | 提示用户从 Gitee 仓库下载 | 用 `docx_utils.py` 内置默认格式参数（兜底） |
| **公文类型识别歧义** | 同时匹配"通知"/"请示" | 列出候选让用户选 | 默认按"请示"处理（更正式）+ 标注"⚠️ 类型识别不确定" |
| **`add_body_text` 抛异常** | 段落超长或特殊字符 | 拆分为多次调用 | 用 `add_clause` 替代 + 标注"[转 add_clause]" |
| **模板路径不存在** | `FileNotFoundError: templates/...` | 运行 `bash scripts/setup.sh` 重新拉取模板 | 列出 `templates/` 实际存在的子目录让用户手动指定 |
| **用户中途退出** | Step 3 追问阶段用户停止回复 | 保留已问/已答进度到临时文件 `tmp/progress.json` | 下次启动时读取 `tmp/progress.json` 恢复（如果 24h 内） |
| **生成的 .docx 损坏/打不开** | Word 提示"文件已损坏" | 检查 `docx_utils.py` 版本（`git log scripts/docx_utils.py`）+ 重装 | 用 LibreOffice 验证转 PDF 看错误码，列出 5 个常见 docx 损坏原因让用户自查 |
| **封面页生成失败** | `add_cover_page()` 抛 `AttributeError` 或 `KeyError` | 确认 `docx_utils.py` 版本 >= R12（含 `add_cover_page` 函数） | 跳过封面页直接生成正文，在文末追加 `⚠️ 封面页生成异常，请手动添加` |
| **当事人信息不完整** | Step 3 追问后用户只提供了姓名未提供身份证号/统一信用代码 | 追问时明确说明"请提供身份证号（个人）或统一社会信用代码（单位）" | 在生成的 .docx 末尾追加 `[待补：当事人身份信息（身份证号/统一社会信用代码）]` 黄色高亮占位符 |
| **依赖未安装** | 运行报 `ModuleNotFoundError` | 自动安装已内置在脚本顶部，重试即可 | 手动运行 `pip install -r requirements.txt` |
| **数据下载失败** | `download_data.sh` 报 curl 错误或 token 无效 | 检查 `scripts/config.json` 中 token 是否正确；检查网络连接 | 提示用户手动从 Gitee 仓库下载数据并解压到根目录 |

## 🚫 禁止事项

| # | 禁止行为 | 替代做法 |
|---|----------|----------|
| 1 | 修改模板样式/布局 | 只用 `replace_text` / `append_clause` |
| 2 | 拼音或英文命名 .docx | `劳动合同_张三.docx` |
| 3 | 主动审查合同风险 | 识别"审查"意图时告知不支持 |
| 4 | 跳过 Step 0 检索直接生成 | 必须先搜索法律和模板 |
| 5 | 未追问自行假设法律强制项 | 逐项追问 |
| 6 | 覆盖用户同名文件 | 先提示确认或换名 |
| 7 | 合同正文插 emoji | 禁止 |
| 8 | 口语写入合同正文 | 转换为规范法律用语 |
| 9 | 数字中英文混排 | 阿拉伯数字，金额大写另起 |
| 10 | 绕过 `docx_utils.py` 格式函数自行设置格式 | 必须使用格式化函数 |
| 11 | 不读 `references/文件合同格式规范.md` 就生成 | Step 4 前必须读取 |
| 12 | 手动拼封面页 | 必须使用 `add_cover_page()` 函数 |
| 13 | 封面页与正文混在同一页 | 封面后必须插入分页符 |

## ✅ 验证清单

- [ ] Step 0：已检索法律条款并纳入上下文
- [ ] Step 0：已匹配模板
- [ ] 已逐项追问所有法律强制缺失项
- [ ] 已读取 `references/文件合同格式规范.md` 并纳入上下文
- [ ] 封面页已使用 `add_cover_page()` 生成，且单独占一页
- [ ] 合同已生成并保存为 .docx，格式符合规范
- [ ] 已附法律依据来源
- [ ] 🛑 已追加"建议律师审查"提醒
