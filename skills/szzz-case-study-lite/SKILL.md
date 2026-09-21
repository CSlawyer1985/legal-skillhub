---
name: szzz-case-study-lite
description: SZZZ Case Study Lite 免费版。用于对用户已有的本地 PDF、DOCX、DOC 民事裁判文书执行批量提取、案号去重、增量入库、逐案专家摘要、Master Report、案例库问答和原文回溯。用户要求分析判决书、整理本地案例库、追加新案例或向已提取材料提问时使用；不包含外部案例检索和 Obsidian 导出。
---

# SZZZ Case Study Lite：本地民事案例研究

把用户已有的本地裁判文书整理为准确、可溯源、可持续增量更新的案例库。

## 执行协议

不要自行另写临时代码扫描或统计文件。提取、去重、进度和数量对账均以 `scripts/main.py` 为准。

运行脚本时，将工作目录设为本 `SKILL.md` 所在的技能目录。不要假定技能安装在 `~/.claude`；以下相对路径适用于任意安装位置。

### Step 1：扫描与建库

用户提供包含 `.pdf`、`.docx` 或 `.doc` 的文件夹后，运行：

```bash
python3 scripts/main.py init "[项目路径]"
```

PDF 保留页码标记；DOCX 直接提取；DOC 在 macOS 使用 `textutil`，其他系统优先使用 LibreOffice。转换器不可用或提取为空时，如实报告，不生成空白 raw 文件。

### Step 2：去重与纳入范围

`init` 自动执行：

- 对民事判决书、民事裁定书按“案号 + 文书类型”去重；
- 纳入执行异议、案外人异议、执行复议等实质争议类执行裁定；
- 纳入典型案例、指导性案例、裁判要旨等参考材料；
- 无标准案号时使用正文相似度辅助去重；
- 把重复、范围排除和提取失败情况写入 `law_analysis_results/dedup_report.txt`。

### Step 3：逐案专家摘要

初始化后运行：

```bash
python3 scripts/main.py focus "[项目路径]"
```

每批只处理脚本派发的材料。读取 `prompts/analyzer-logic.md`，穷尽原文中的全部争议焦点，逐份生成摘要。

摘要必须：

- 保存到 `law_analysis_results/individual_cases/`；
- 使用 `案号-文书类型-当事人简称-案由-摘要.md`；
- 无法确认的信息写“原文未披露”，不得推测；
- 每批落盘后再次运行 `focus`，直到脚本明确提示队列清空。

### Step 4：三个后续方向

队列清空并完成数量对账后，先阅读全部单案摘要，提炼三个高频、重要的争议焦点 A、B、C，再向用户提供：

1. 提供具体案情或问题，从案例库检索并在必要时回溯原文；
2. 从 A/B/C 中选择一个，作为 Master Report 的重点专题；
3. 提供自定义报告关键词。

不要默认直接生成 Master Report。

### Step 5：Master Report

用户确认专题后运行：

```bash
python3 scripts/main.py report "[专题词]" "[项目路径]"
```

读取脚本生成的 `master_data.json`、全部单案摘要及 `prompts/master-report-logic.md`，生成与 Pro 相同结构、带案号来源的实务报告，并保存为：

```text
law_analysis_results/Master_Report.md
```

## 增量处理

既有项目加入新文书后再次运行 `init`。如果发现唯一的新材料，立即运行：

```bash
python3 scripts/main.py focus_incremental "[项目路径]"
```

持续处理到增量队列清空。汇报时必须分别说明“本轮增量数量”和“全库累计数量”。增量完成后，除三个常规方向外，还应提供“只围绕本轮增量案件提问”的选项；除非用户要求，不扩大到全库。

## 既有案例库问答

用户向已提取材料提问时，按问题精度逐层回溯：

1. **宏观统计、趋势和分布**：优先读取 `Master_Report.md`；没有报告时汇总 `individual_cases/`。
2. **案件比较、裁判规则和法律适用**：读取相关单案摘要进行交叉分析。
3. **最相似案件、特定事实、抗辩原话、证据或日期金额**：必须读取对应 `source_texts/*-raw.md`，不能只依赖摘要。

回答采用“结论—原文证据对齐—实务评论”结构，明确说明来自哪份摘要或 raw 原文。摘要与 raw 不一致时以 raw 为准；原文没有披露时明确回答“判决书原文未披露此细节”。

再次运行 `init` 且没有新材料时，向用户提供：案例库问答、重写 Master Report、结束本轮或明确确认后重置。

## 功能边界

Lite 只处理用户已有的本地材料，不调用元典或其他外部案例库，也不写入 Obsidian Vault。需要外部类案检索、动态选案、元典归档或 Obsidian 知识库时，使用 SZZZ Case Study Pro。
