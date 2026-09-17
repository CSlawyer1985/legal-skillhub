---
name: case-archiver
description: 民事案件卷宗归档助手 V3。用户提出归档案件、先归档现有材料、完卷、补齐材料、生成归档表格或合并卷宗 PDF 时使用。按律所配置分类材料、提取字段、可靠填写 Word 表格、生成缺失清单；合并 PDF 必须先取得用户确认。
---

# 民事案件归档助手 V3

使用一套通用引擎和分律所配置整理民事案件卷宗。律所模板、输出路径和字段映射保存在技能包外：

```text
~/.workbuddy/case-archiver/
├─ settings.json
└─ firm_config/<firm>/
   ├─ paths.json
   ├─ preferences.json
   ├─ template_mapping.md
   ├─ archive_plan.json
   └─ field_map.json
```

升级技能不得覆盖该配置目录，也不得把客户材料复制进技能包。

## 路由

| 用户意图 | 动作 |
|---|---|
| 归档案件、先归档现有材料 | 运行 `scripts/archive_case.py` |
| 完卷、补齐新增材料 | 运行 `scripts/status.py`，重新扫描并更新状态 |
| 接入新律所或新模板 | 运行 `scripts/onboard.py`，随后人工审阅低置信度映射 |
| 检查 Word 模板网格和标记 | 运行 `scripts/fill_docx.py 模板.docx --out 检查.json` |
| 合并卷宗、合成 PDF | 先向用户确认，再运行 `scripts/merge_volume.py` 或向主流程传 `--merge yes` |

## 归档流程

1. 读取默认律所及 `paths`、`archive_plan`、`field_map`、`preferences`。
2. 递归扫描案卷；从 PDF、DOCX、DOC 和允许 OCR 的扫描件提取文字。
3. 检查是否混入多份互斥材料；发现时警告，不假装材料属于同一案件。
4. 按 `archive_plan` 处理：填写表格、抽取纯模板页、复制既定文件或跳过。
5. 自动字段按 `from` 和 `key` 提取；`agent` 字段使用调用方提供值；`client` 字段保持空白。
6. 生成 `.归档状态.json` 和 `待补齐材料清单.txt`。
7. 不自动合并 PDF；只有用户明确同意后才执行合并。

案件未结案时允许部分归档。缺失材料记为 `pending`；表格定位或写后校验失败记为 `error`，不得标记为 `done`。

## V3 表格规则

填写 DOCX 时按稳定性选择定位方式：

1. `marker`：模板中的 `{{字段名}}`，首选。
2. `control_tag`：Word 内容控件 Tag/标题。
3. `cell_anchor`：按标签定位同格、右格或下格。
4. `anchor` / `loc`：仅兼容旧配置；`loc` 应附 `expected_text` 防错位。

默认启用严格模式。非空字段找不到、标签不唯一、旧坐标越界或写后验证失败时，保留原输出并把原因写入 manifest 的 `fill_report`。

接入向导生成的 `review_required=true` 映射必须经人工确认。合并单元格、空白装饰格和重复标签不得仅凭猜测投入正式使用。

涉及表格映射、选项框、内容长度或 V2 配置迁移时，读取 [references/table-mapping-v3.md](references/table-mapping-v3.md)。修改其他配置时读取 [references/schema.md](references/schema.md)。

## 业务填写约定

- 当事人指委托人（我方客户）；对方当事人指对立面。
- 收案时间取委托合同落款日期；处理机关取受理法院或仲裁机构。
- 审批表右上角“处理方式”填劳动仲裁、一审、二审等，不填处理机关。
- 空白字段保持空白，不写“待填写”等占位文字。
- 合同明确免收、免费或零元时，收费栏填“免收”。
- 案情简介从诉讼请求、查明事实和处理结果组织 200–400 字摘要；无法可靠提取时转为 `agent`，不编造。
- 案件进程按日期排列委托、立案/仲裁、举证、开庭、裁判或调解等事件。

## 授权材料检查

| 委托人类型 | 必备材料 |
|---|---|
| 自然人 | 身份证、授权委托书、律所公函、律师执业证 |
| 组织 | 营业执照、法定代表人身份证明书、法定代表人身份证、授权委托书、律所公函、律师执业证 |

缺失项记为 `pending`，不得用相似但不等价的材料替代。

## 合并确认边界

- 归档不等于合并。
- 即使 `preferences.merge_pdf` 为 `always`，仍须先获得本次用户确认。
- `--merge yes` 仅表示调用方已经取得本次明确确认。
- 多案件批量操作可汇总确认，但必须清楚列出将合并的案件。

## 依赖与兼容

- `python-docx`：DOCX 模板填写与检查。
- `pypdf`：PDF 文本提取。
- `PyMuPDF`：PDF 合并与页码。
- `pywin32` / Word COM：仅在把 Word 文件转换为 PDF 时需要。
- PaddleOCR 或 Windows OCR：扫描件文字识别；默认只处理白名单文书。

正式归档前先用脱敏案卷试运行。检查 `fill_report.errors`、缺失清单以及生成 DOCX 的实际渲染版面；不要只依据脚本退出码判断表格正确。

