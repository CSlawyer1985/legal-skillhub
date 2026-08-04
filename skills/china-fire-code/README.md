# china-fire-code

> 中国消防**法律法规与技术标准**条文智能检索 Skill。
> 覆盖：法律（消防法/安全生产法等）、行政法规、部门规章（部令）、国家标准（GB）、行业标准（XF/GA）。
> **纯索引 + 在线优先**：仓库不捆绑任何 PDF，只维护官方 URL 目录；联网检索为主、本地 PDF 可选兜底、知识回流自动沉淀。

一个面向中国消防法律法规体系的 **Skill**：用自然语言提问，即可获得精确的条文引用
（文档名/编号 + 条款号 + 版本 + 官方来源链接）。优先适配 **WorkBuddy**，纯 markdown + 可选 Python 脚本，
可发布于 GitHub 并被各类 agent 环境复用。

## 特性
- 覆盖**全部消防法律法规体系**：法律 / 行政法规 / 部门规章 / 国标 GB / 行标 XF，见 `references/catalog.md`
- 自然语言 → 精确条文（第 0 步目录发现 + 模式一 联网 / 模式二 本地 PDF 检索 / 模式三 知识回流 / 模式四 术语记忆回流）
- 精准性铁律：只引权威源、原文摘录不转述、标识门禁、效力层级与上位法优先、显式不确定、多源核对 + 术语记忆回流
- 检索式：不预拆条文，agent 用到时按需检索/抽取，保留原始编号
- 知识回流：联网新发现按白名单 + 版本校验沉淀回本地 golden（默认 ⏳ 待核对，确认后晋升 ✅ 金标准可零摩擦调用）
- 术语记忆回流：字符级损坏（如「大于」→「大千」）由人工核对确认后沉淀进 `term_memory.md`，后续自动复用、持续纠错
- 多源核对：`reconcile.py` 对同一条款多份官方副本逐字符 diff，分歧标 ⚠️ 绝不静默采纳
- **金标准库（golden）**：人工确认的条款沉淀为 ✅ 金标准，再次引用时 `golden.py lookup` 直接调用、零摩擦且绝对准确；`refresh_golden.py` 每周定时核验官网是否更新/废止，确保"绝对准确"可续命（采标标准仅 detect 不 auto-pull）
- **纯索引 + 在线优先**：仓库零 PDF，体积小、易分发；标准 PDF 由使用者按官方 URL 自行下载
- **模式五 金标准定时刷新**：`refresh_golden.py` 每周核验官网是否更新/废止，确保「绝对准确」可续命（采标标准仅 detect 不 auto-pull）
- **模式六 社区校验问答参考**：从 HuggingFace `sdzjoy/fire-safety-sft-dataset`（Apache-2.0）抽取社区 Q&A 作交叉核对参考，仅署名再分发、不复制标准正文
- **模式七 用户纠错/评分回流**：`feedback.py` 把用户信号（纠错 / 评分）汇入复核队列，反哺 golden，形成社区化闭环
- **罚则 + 典型案例库**：`penalty_cases.md` 速查消防法及主要部门规章罚则 + 公开可溯源案例，覆盖落地最高频的「罚多少 / 有何后果 / 有无先例」
- **离线索引**：`extract_pdf.py --build-index` 从用户本地 PDF 生成条款目录索引（落用户主目录 `~/.firecode_offline/`，不进仓库），离线亦可快速定位

## 目录结构
```
china-fire-code/
├── SKILL.md                # 核心指令（目录驱动流程/精准铁律/输出模板）
├── references/
│   ├── catalog.md          # ★ 全部消防法律法规机器可读目录（国家/地方/专业领域·类型/效力层级/官方URL）
│   ├── online_readability.md # 📖 在线可读性例外清单（采标/仅下载PDF/不提供公开文本）
│   ├── 规范速查表.md         # 核心规范版本真相（编号/版本/强条/替代关系）
│   ├── term_memory.md       # 字符纠错记忆（人工核对沉淀 · skill 记忆）
│   ├── golden/             # ★ 金标准库（⏳ 待核对 / ✅ 已核对·可零摩擦调用）见其 README
│   │   ├── README.md
│   │   ├── seed_hf_sft.md  # 社区校验问答（HF-SFT·Apache-2.0 署名·⏳待核对·仅交叉核对）
│   │   └── penalty_cases.md # 罚则速查 + 典型案例参考索引（⏳待核对·非金标准）
│   └── archive/            # 历史废止条款归档库见其 README
├── scripts/
│   ├── extract_pdf.py      # 模式二（可选）：本地 PDF 按需检索 + 离线索引（--build-index，自动加载 term_memory）
│   ├── golden.py           # 金标准库：write / lookup / confirm / abolish
│   ├── refresh_golden.py   # 模式五：定时核验 golden 中 ✅ 条目是否更新/废止
│   ├── import_hf_sft.py    # 模式六：从 HF 数据集抽取社区 Q&A seed，带 Apache-2.0 署名
│   ├── term_memory.py      # 模式四：字符纠错记忆 add / list / remove
│   ├── reconcile.py        # 多源核对：同条款逐字符 diff，标 ⚠️
│   └── feedback.py         # 模式七：用户纠错/评分回流（JSONL → 复核队列）
├── requirements.txt        # pymupdf(可选·模式二) / paddleocr(可选·最高精度)
└── README.md
```

## 依赖与安装
```
# 纯在线场景（默认）：无需安装任何依赖，agent 直接用「第 0 步 + 模式一」联网检索。
# 仅当用户有本地 PDF 语料、需启用模式二时才装：
pip install -r requirements.txt
# pymupdf 可选（模式二基线）；paddleocr 可选（最高精度 OCR，安装较大）
```

## 使用（WorkBuddy）
将 `china-fire-code/` 整个文件夹放入 WorkBuddy 的 skill 目录：
```
D:\Workbuddy\Uses\skill\china-fire-code\
```
WorkBuddy 会自动识别并在相关提问时调用。查询时先查 `catalog.md` 定位文档，再联网抓取官方条文。

## 适配其他 agent 环境
- **纯在线 agent（默认）**：直接用「第 0 步目录发现 + 模式一联网检索」，无需本地依赖。
- 本地 Python agent（WorkBuddy / Cursor / CLI）且有本地 PDF：可启用 `scripts/extract_pdf.py` 等。
- 云端无运行时 agent（Dify 等）：用户在本机跑脚本、把输出贴回；或走平台自带知识库能力。

## 精准保证机制
见 `SKILL.md` 的「精准性铁律」：来源白名单（npc/gov/openstd/samr/mohurd/mem/119 等）、原文摘录、标识门禁、
**效力层级与上位法优先**、本地基准优先、显式不确定 + 知识回流；
**多源核对 + 术语记忆回流**：字符级损坏只能由人工核对确认后沉淀进 `references/term_memory.md`，机器绝不臆测改字，
记忆仅作自动修正线索、抽取时仍标红供人复核。

## 版权与数据声明
- 本仓库**不捆绑任何 PDF / 标准原文**，仅维护 `catalog.md`（官方 URL 索引）+ skill 记忆 + golden 金标准库（用户确认沉淀）。
- 标准 PDF 再分发受版权与平台条款限制；使用者应凭 `catalog.md` 中的官方 URL **自行下载**到本地私有语料，勿随本 skill 公开分发。
- **采标（采用 ISO/IEC 国际标准）类 GB / GB/T 标准**，文本版权归国际标准组织，官方平台通常**不提供免费在线阅读**，仅可下载 / 购正式出版物。此类例外统一见 `references/online_readability.md`，命中时按 SKILL.md「模式一·例外处理」引导用户自行获取，本 skill 不臆测、不替代权威源。
- 法律、法规文本属公开信息，可自由引用，但仍以正式出版物及主管部门解释为准。

## 免责声明
本 skill 为检索与排版工具，**不提供合规判断、不出具法律意见**。
所有内容仅供参考，不具有法律效力，以正式出版物及主管部门解释为准。

## License
待定（建议 MIT，归属个人）。
