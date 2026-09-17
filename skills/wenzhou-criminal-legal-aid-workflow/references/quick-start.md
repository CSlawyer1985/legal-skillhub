# 5分钟快速上手

## 第一步：检查本机环境

在 Skill 根目录运行：

```bash
python3 scripts/doctor.py
```

文书生成必须具备 Python 3.9+ 和 `python-docx`。PDF文字层读取、扫描PDF渲染和中文OCR属于“无台账材料扫描”的可选能力，自检会分别说明是否可用。

## 第二步：选择你的入口

### 已有流程台账

从台账和原始文书中核对案件阶段、羁押状态、指派机构、经办机关及关键日期，将已确认字段填入复制到案件目录的 `case.json`。

### 没有流程台账

先只读扫描本地案件材料：

```bash
python3 scripts/extract_case_timeline.py /path/to/materials \
  --output-dir /path/to/workpaper/timeline
```

脚本会生成：

- `案件流程台账-待核实.md`：方便律师逐项查看和勾选；
- `timeline_candidates.json`：保留来源、页码或段落、提取方式、置信度和核实状态。

所有识别结果默认是“待律师核实”，不能直接写入正式文书。详见 [无台账材料时间线](material-timeline.md)。

### 温州以外地区

先按 [地区模板包替换指南](template-pack-guide.md) 导入当地法援中心的完整母版，不能只修改机构名称后沿用温州格式。

## 第三步：只预览文书计划

先检查罪名是否已经收入 [常见罪名基础说明库](charge-library-guide.md)。未收录时，须核验现行法源后填写 `charge_legal_basis`。

```bash
python3 scripts/generate_criminal_legal_aid_set.py \
  --input /path/to/case.json \
  --output-dir /path/to/output \
  --mode current \
  --dry-run
```

预览不会创建文件。确认阶段和文书组合无误后，去掉 `--dry-run` 正式生成。

## 第四步：逐项复核

生成目录会自动附带 `00-生成结果律师复核清单.md`。先保留可修改 Word，核对事实、日期、签章和版式后，再导出最终 PDF 上传。

## 第五步（归档）：从整册扫描件提取上传 PDF

归档阶段拿到的是整册扫描好的归档材料时，按归档目录切割成独立 PDF 文件再上传（介绍信与对应会见笔录等组合按当地系统栏目合并成一个 PDF）：

```bash
python3 scripts/split_archive_scans.py \
  --input /path/归档扫描材料.pdf \
  --spec /path/切割规则.json \
  --output-dir /path/归档PDF/
```

切割规则 JSON 为 `[{"name":"指派通知书","from":1,"to":2},{"name":"会见材料","pages":[3,7,8]}]` 数组，页码从 1 起、含端点；每项使用连续范围或指定页序二选一。先由 OCR 辅助识别并经律师确认页码，再执行切割。输出目录由使用者指定，可以位于原材料目录内，但不得覆盖原件或已有同名文件。全部规则先校验，失败时清理本次新建的输出；遗漏页码会提示，重复页默认拒绝，仅在律师确认同页确需用于不同栏目时使用 `--allow-overlap`。完成后逐份核对页序、页数与签章再上传。

## 更换承办律师时的初始化

作者信息“李鸿鸿、浙江光正大律师事务所”仅用于公开 Skill 的作品归属。其他律师或律所使用本 Skill 前：

1. 每个案件 JSON 必须显式填写 `lawyer`、`law_firm`。`record_lawyer` 按实际记录人填写，未填时沿用该案承办律师，须核实；`law_firm_website` 无需使用时可留空。
2. 检查生成文书中的律所名称、承办律师和网址是否已全部替换为本所信息。
3. 如需修改模板或身份字段，同步检查 `scripts/generate_criminal_legal_aid_set.py` 中的案件身份校验，并在修改后运行完整测试和模板包校验。

生成器不以作者信息代填案件身份；缺少当前案件的承办律师或律师事务所时停止生成。
