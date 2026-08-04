# 引擎使用指南

本文档详细说明四大引擎模块的使用方法和注意事项。

---

## 引擎一：结构解析引擎（contract_parser.py）

### 功能

解析 .docx 合同文件，提取结构化信息，帮助 AI 审核时精确定位条款。

### 输出字段说明

```json
{
  "file": "/path/to/合同.docx",
  "file_name": "合同.docx",
  "file_stem": "合同",
  "parsed_at": "2026-04-15T11:00:00Z",
  "statistics": {
    "total_paragraphs": 150,
    "non_empty_paragraphs": 120,
    "total_words": 5000,
    "total_definitions": 15,
    "total_cross_references": 25,
    "total_clauses": 30
  },
  "structure": {
    "paragraphs": [
      {
        "index": 0,
        "text": "第一条 定义",
        "style": "Heading1",
        "clause_number": "第一条",
        "definitions": ["合同", "甲方", "乙方"],
        "cross_references": [],
        "categories": ["定义"],
        "word_count": 10
      }
    ],
    "clause_index": {
      "第一条": [0, 1, 2],
      "第二条": [3, 4, 5]
    }
  },
  "definitions": ["合同", "甲方", "乙方", "服务", "交付物"],
  "cross_references": ["详见第一条", "参见第二条"],
  "category_summary": {
    "定义": 5,
    "标的": 3,
    "价款": 4
  }
}
```

### 使用场景

1. **审核前**：先解析合同结构，了解条款分布
2. **定位问题**：通过 paragraph_index 精确定位需要修改的段落
3. **检查定义词**：通过 definitions 列表检查定义是否统一
4. **检查交叉引用**：通过 cross_references 列表检查引用是否准确

### 注意事项

- 解析结果保存为 JSON，供后续步骤使用
- paragraph_index 是 0-based，从文档开头开始计数
- clause_number 可能为空（非条款编号段落）
- definitions 检测基于正则表达式，可能有误报/漏报

---

## 引擎二 & 三：修订与批注引擎（apply_changes.py）

### 前置条件

必须先使用 docx skill 的 `unpack.py` 解压 docx：

```bash
python3 ~/.../docx/scripts/unpack.py 合同.docx unpacked/
```

### changes.json 格式详解

```json
{
  "author": "Claude",
  "date": "2026-04-15T11:00:00Z",
  "revisions": [
    {
      "paragraph_index": 42,
      "original_text": "违约金为合同总金额的 30%",
      "revised_text": "违约金为合同总金额的 20%",
      "reason": "30% 过高，可能被认定为惩罚性违约金"
    }
  ],
  "comments": [
    {
      "paragraph_index": 55,
      "highlight_text": "争议解决",
      "comment": "仅约定诉讼，建议增加仲裁选项",
      "severity": "中风险",
      "suggestion": "建议修改为：因本合同引起的争议，双方协商解决；协商不成的，提交 XX 仲裁委员会仲裁或向有管辖权的人民法院提起诉讼。"
    }
  ]
}
```

### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| author | string | 否 | 修订作者，默认 "Claude" |
| date | string | 否 | ISO 8601 日期，默认当前时间 |
| revisions | array | 否 | 修订列表 |
| revisions[].paragraph_index | int | 是 | 段落索引（0-based） |
| revisions[].original_text | string | 是 | 原文（将标记为删除） |
| revisions[].revised_text | string | 是 | 修订文（将标记为插入） |
| revisions[].reason | string | 否 | 修订原因（仅用于报告） |
| comments | array | 否 | 批注列表 |
| comments[].paragraph_index | int | 是 | 段落索引 |
| comments[].highlight_text | string | 否 | 被批注的文本，省略则整段批注 |
| comments[].comment | string | 是 | 批注内容 |
| comments[].severity | string | 否 | 风险等级（高风险/中风险/低风险） |
| comments[].suggestion | string | 否 | 建议条款 |

### 使用流程

```bash
# 1. 解压 docx
python3 ~/.../docx/scripts/unpack.py 合同.docx unpacked/

# 2. 准备 changes.json
# （AI 生成或手动编写）

# 3. 应用变更
python3 scripts/apply_changes.py unpacked/ changes.json

# 4. 重新打包
python3 ~/.../docx/scripts/pack.py unpacked/ 合同-修订批注版.docx --original 合同.docx
```

### 验证模式

```bash
# 仅验证，不写入（检查 changes.json 是否可应用）
python3 scripts/apply_changes.py unpacked/ changes.json --dry-run
```

### 注意事项

1. **文本匹配**：original_text 和 highlight_text 必须与文档中的文本完全一致（包括空格）
2. **跨 run 文本**：如果目标文本跨越多个 run（格式变化处），引擎会尝试智能合并
3. **批注位置**：highlight_text 用于定位批注位置，如果找不到则整段批注
4. **ID 冲突**：引擎会自动检测并避免修订 ID 和批注 ID 冲突

---

## 引擎四：清洁版生成引擎（generate_clean.py）

### 功能

从带修订痕迹的 docx 生成清洁版（接受所有修订，移除所有批注）。

### 模式说明

| 模式 | 说明 |
|------|------|
| accept_and_remove_comments | 接受所有修订 + 移除批注（默认） |
| accept_only | 仅接受修订，保留批注标记 |
| remove_comments_only | 保留修订，移除批注 |
| remove_all | 接受修订 + 移除批注（同默认） |

### 使用方式

```bash
# 方式一：直接处理 docx 文件
python3 scripts/generate_clean.py 合同-修订批注版.docx 合同-清洁版.docx

# 方式二：处理 unpacked 目录
python3 scripts/generate_clean.py unpacked/ 合同-清洁版.docx --unpacked

# 指定模式
python3 scripts/generate_clean.py 合同-修订批注版.docx 合同-清洁版.docx --mode accept_only
```

### 注意事项

- 清洁版生成是**不可逆**的，建议先备份修订批注版
- 如果输入文件有损坏的 XML，可能生成失败
- 批注移除后，comments.xml 也会被删除

---

## 引擎五：多轮迭代管理引擎（iteration_manager.py）

### 目录结构

```
合同名称-Output/
  manifest.json           # 迭代管理清单
  round-1/                # 第一轮
    合同-修订批注版.docx
    合同-清洁版.docx
    合同-审查报告.txt
    changes.json
  round-2/                # 第二轮
    ...
```

### 命令详解

#### init — 初始化项目

```bash
python3 scripts/iteration_manager.py init 合同名称-Output --name "合同名称"
```

创建 manifest.json，记录项目基本信息。

#### new-round — 创建新一轮

```bash
python3 scripts/iteration_manager.py new-round 合同名称-Output \
  --revised round-2/合同-修订批注版.docx \
  --clean round-2/合同-清洁版.docx \
  --report round-2/合同-审查报告.txt \
  --changes round-2/changes.json
```

自动创建 round-N 目录，复制文件，更新 manifest。

#### status — 查看状态

```bash
python3 scripts/iteration_manager.py status 合同名称-Output
```

输出当前轮次、总轮次、每轮文件列表。

#### compare — 对比两轮

```bash
python3 scripts/iteration_manager.py compare 合同名称-Output 1 2
```

对比第 1 轮和第 2 轮的 summary 差异。

#### rollback — 回滚

```bash
python3 scripts/iteration_manager.py rollback 合同名称-Output 1
```

回滚到第 1 轮，删除第 2 轮及之后的所有数据。

#### export — 导出文件

```bash
python3 scripts/iteration_manager.py export 合同名称-Output --round 2 --output ./
```

将第 2 轮的文件导出到指定目录（默认项目根目录）。

### manifest.json 格式

```json
{
  "project_name": "合同名称",
  "created_at": "2026-04-15T10:00:00Z",
  "current_round": 2,
  "rounds": [
    {
      "round": 1,
      "created_at": "2026-04-15T10:00:00Z",
      "files": {
        "revised": "round-1/合同-修订批注版.docx",
        "clean": "round-1/合同-清洁版.docx",
        "report": "round-1/合同-审查报告.txt",
        "changes": "round-1/changes.json"
      },
      "summary": {
        "revisions_count": 15,
        "comments_count": 8,
        "high_risk": 3,
        "medium_risk": 5,
        "low_risk": 7
      }
    }
  ]
}
```

### 注意事项

- manifest.json 是核心文件，不要手动修改
- 每轮文件建议通过 new-round 命令归档，便于版本管理
- rollback 是**不可逆**的，删除的数据无法恢复
- 导出操作是复制，不是移动，原文件保留

---

## 完整工作流示例

### 第一轮审核

```bash
# 1. 准备输出目录
python3 scripts/prepare_output_paths.py 合同.docx
# → 返回 output_dir 等路径

# 2. 解析合同结构
python3 scripts/contract_parser.py 合同.docx 合同名称-Output/合同-结构.json

# 3. AI 审核（读取结构.json，生成审查结论和 changes.json）
# ... AI 工作 ...

# 4. 应用变更
python3 ~/.../docx/scripts/unpack.py 合同.docx unpacked/
python3 scripts/apply_changes.py unpacked/ 合同名称-Output/changes.json
python3 ~/.../docx/scripts/pack.py unpacked/ 合同名称-Output/合同-修订批注版.docx --original 合同.docx

# 5. 生成清洁版
python3 scripts/generate_clean.py 合同名称-Output/合同-修订批注版.docx 合同名称-Output/合同-清洁版.docx

# 6. 生成 txt 报告（AI 生成）
# ... AI 工作 ...

# 7. 初始化并归档
python3 scripts/iteration_manager.py init 合同名称-Output --name "合同名称"
python3 scripts/iteration_manager.py new-round 合同名称-Output \
  --revised 合同名称-Output/合同-修订批注版.docx \
  --clean 合同名称-Output/合同-清洁版.docx \
  --report 合同名称-Output/合同-审查报告.txt \
  --changes 合同名称-Output/changes.json
```

### 第二轮审核

```bash
# 1. 查看上一轮状态
python3 scripts/iteration_manager.py status 合同名称-Output

# 2. 读取上一轮 changes.json
# ... AI 工作 ...

# 3. 对比新版本与上一轮清洁版
# ... AI 工作 ...

# 4. 生成本轮 changes.json
# ... AI 工作 ...

# 5. 应用变更（同第一轮步骤 4-6）
# ...

# 6. 归档本轮
python3 scripts/iteration_manager.py new-round 合同名称-Output \
  --revised 合同名称-Output/合同-修订批注版-R2.docx \
  --clean 合同名称-Output/合同-清洁版-R2.docx \
  --report 合同名称-Output/合同-审查报告-R2.txt \
  --changes 合同名称-Output/changes-R2.json
```

---

## 故障排除

### 修订痕迹未显示

1. 检查 Word 的"审阅"选项卡 → "显示标记"是否开启
2. 检查修订作者是否为 Claude（或其他指定作者）
3. 检查 document.xml 中是否有 w:ins/w:del 元素

### 批注气泡未显示

1. 检查 comments.xml 是否存在且已注册到 [Content_Types].xml
2. 检查 document.xml.rels 中是否有 comments.xml 的关系
3. 检查批注标记（commentRangeStart/End）是否正确插入

### 清洁版生成失败

1. 检查输入文件是否为有效的 docx
2. 检查是否有损坏的 XML
3. 尝试使用 LibreOffice 的 `--accept-all-revisions` 参数

### 多轮迭代状态丢失

1. 检查 manifest.json 是否存在且格式正确
2. 检查 round-N 目录是否存在
3. 如需恢复，手动重建 manifest.json

---

## 高级用法

### 批量处理多个合同

```bash
for docx in *.docx; do
  python3 scripts/contract_parser.py "$docx" "${docx%.docx}.json"
done
```

### 从上一轮继承部分变更

```bash
# 复制上一轮的 changes.json 作为基础
cp round-1/changes.json round-2/changes-base.json

# 修改后应用
python3 scripts/apply_changes.py unpacked/ round-2/changes-base.json
```

### 生成对比报告

```bash
# 对比两轮审查报告
diff round-1/合同-审查报告.txt round-2/合同-审查报告.txt > 对比报告.txt
```

---

## 整合工作流引擎（full_pipeline.py）

### 功能

一键执行完整合同审查流程，自动处理 .doc → .docx 转换、解压、应用变更、打包、生成清洁版。

### 命令

```bash
python3 scripts/full_pipeline.py <输入文件> <changes.json> [选项]

选项:
  --output-dir, -o   输出目录（默认与输入文件同目录）
  --suffix           输出文件后缀（默认：-审查版）
  --keep-tmp         保留临时解压目录
```

### 示例

```bash
# 标准用法（输出到输入文件同目录）
python3 scripts/full_pipeline.py 合同.docx changes.json

# 指定输出目录
python3 scripts/full_pipeline.py 合同.docx changes.json -o ~/Desktop

# 指定后缀
python3 scripts/full_pipeline.py 合同.docx changes.json --suffix "-终版"
```

### 自动处理

1. **格式转换**：自动将 .doc 转换为 .docx（使用 macOS textutil 或 LibreOffice）
2. **解压**：自动解压 docx
3. **应用变更**：自动调用 apply_changes.py
4. **打包**：自动生成修订批注版 .docx
5. **生成清洁版**：自动调用 generate_clean.py
6. **清理**：自动删除临时解压目录

### 注意事项

- 如果输入是 .doc，会自动转换，无需手动处理
- 批注因文本匹配问题失败时，会降级为整段批注
- 清洁版生成失败不影响修订批注版的生成


──────────────────────────────────────────
## 引擎六：多轮迭代分析引擎（round_analyzer.py）
──────────────────────────────────────────

### ⚠️ 触发条件（必须同时满足）

**round_analyzer.py 只在以下条件同时满足时启用：**
1. 你发来的文件是**对方的修改批注版**（对方律师已添加批注/修订的 docx）
2. 你**明确告诉我你站在哪一方**（如："我是甲方" / "我是承包方"）

**不满足条件时**，round_analyzer 不启动，当作新一轮合同审核处理。

### 概述

自动读取对方修改后的 docx，识别批注立场，生成下一轮回应策略，
输出符合 SKILL 规范的 `changes.json`，无需人工编写 JSON。

### 输入输出

```
输入：对方修改后的含批注 docx
      上一轮 changes.json（可选，提供我方原始立场）

输出：本轮 changes.json（含完整回应策略）
```

### 使用方式

```bash
python3 scripts/round_analyzer.py <对方回复版.docx> \
    --our-previous round-1/changes.json \
    --output round-2/changes.json \
    --round 2 \
    --author "Claude AI 法律审核"
```

### 核心功能

#### 1. 批注立场分类

自动识别对方每条批注的立场：

| 分类 | 含义 | 我方策略 |
|------|------|---------|
| `acceptance` | 对方接受我方建议 | 确认，无争议 |
| `partial_acceptance` | 部分接受，有条件 | 接受部分，分歧继续论证 |
| `rebuttal` | 对方拒绝/反驳 | 坚守底线，给出法律论据 |
| `counter_proposal` | 对方提出折中方案 | 评估合理性，寻求平衡 |
| `new_issue` | 对方提出新问题 | 单独评估，给出意见 |
| `needs_analysis` | 立场不明 | 提示人工跟进 |

#### 2. 法律反驳库

内置针对常见问题的法律论据和让步空间：

| 问题类型 | 反驳论据 | 让步底线 |
|---------|---------|---------|
| 违约金过高（30%） | 超过损失30%即可能触发司法调减 | 可接受20-25%，但要求甲方对等封顶 |
| 3天补款 | 属于不公平格式条款 | 底线7个工作日 |
| 审计无限期 | 影响承包方资金回收 | 90日报送+督促条款 |
| 发票类型 | 专票/普票税额差异涉及实际利益 | 坚持专票 |
| 管辖条款 | 专属管辖+送达地址确认 | 接受管辖，坚持送达确认条款 |

#### 3. 回应生成逻辑

每条回应包含：
- `comment`：对方立场 + 我方法律论据
- `reason`：谈判策略说明
- `legal_basis`：引用法条
- `suggestion`：底线方案 / 备选方案

### 完整多轮工作流

```
round_analyzer.py ──→ round-N/changes.json ──→ full_pipeline.py ──→ 批注版.docx
     ↑                                                      │
     └──────────── 对方修改后再次输入 ◄──────────────────────┘
```

### 已知局限

- `paragraph_index` 通过批注文本推断，可能与实际段落有偏差
- 新增问题需要人工确认高亮文本范围
- 复杂谈判（如多议题捆绑）建议人工审核后使用

### 依赖

无外部依赖，仅使用 Python 标准库（json, re, zipfile, xml.etree.ElementTree）。
