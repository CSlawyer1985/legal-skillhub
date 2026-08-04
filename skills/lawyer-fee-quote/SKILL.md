---
name: lawyer-fee-quote
description: 根据案件类型、财产标的、难度等信息自动生成专业的律师费报价方案Word文档；当用户需要生成律师费报价方案、制作法律服务报价、制定案件收费方案时使用
dependency:
  python:
    - python-docx==1.1.0
---

# 律师费报价方案生成器

## 任务目标

- 本 Skill 用于：生成专业格式的律师费报价方案 Word 文档
- 能力包含：
  - 自动识别案件类型并生成对应标题
  - 根据财产标的额计算三种标准报价方案
  - 自动格式化排版（字体、间距、标题层次）
  - 支持自定义律所和律师信息
- 触发条件：用户需要生成律师费报价、收费方案、法律服务报价文档时

## 前置准备

- 依赖库：`python-docx==1.1.0`（已在 dependency 中声明）
- 输出文件：生成的 Word 文档保存到用户指定路径或当前目录

## 操作步骤

### 步骤一：收集案件基本信息

向用户收集以下信息（根据实际案例选择填写）：

| 参数 | 说明 | 示例 |
|------|------|------|
| `--case-type` | 案件类型 | 离婚纠纷、合同纠纷、劳动争议、交通事故、刑事辩护等 |
| `--property-amount` | 财产标的额（万元） | 500、3500 |
| `--difficulty-level` | 难度等级（1-5） | 1=简单、3=中等、5=极难 |
| `--law-firm` | 律所名称 | 浙江XX律师事务所 |
| `--lawyer-name` | 律师姓名 | 张三 |
| `--province` | 省份（用于参照收费标准） | 浙江、北京、上海、广东 |
| `--output-path` | 输出文件路径（可选） | ./律师费报价方案.docx |

### 步骤二：收集核心难点（可选）

如用户提供了具体难点，使用 `--core-difficulties` 参数传入 JSON 数组格式：

```json
["难点1描述", "难点2描述", "难点3描述"]
```

如用户未提供，脚本将根据案件类型和难度等级自动生成。

### 步骤三：收集工作量估算（可选）

如用户提供了工作量估算，使用 `--work-hours` 参数传入 JSON 格式：

```json
{"证据筹备": "35-45", "法律策略": "25-30", "庭审谈判": "20-25", "成果落地": "10-15"}
```

如用户未提供，脚本将根据难度等级自动估算。

### 步骤四：调用脚本生成文档

根据收集的信息，执行脚本：

**基础用法（最小参数）：**
```bash
python scripts/generate_quote.py --case-type "离婚纠纷" --property-amount 3500 --law-firm "浙江XX律师事务所" --lawyer-name "张三"
```

**完整参数用法：**
```bash
python scripts/generate_quote.py \
  --case-type "离婚纠纷" \
  --property-amount 3500 \
  --difficulty-level 5 \
  --law-firm "浙江XX律师事务所" \
  --lawyer-name "张三" \
  --province "浙江" \
  --core-difficulties '["跨境股权分割难度高","大额财产举证复杂","多子女抚养权争夺"]' \
  --work-hours '{"证据筹备":"40-50","法律策略":"30-35","庭审谈判":"25-30","成果落地":"15-20"}' \
  --output-path "./律师费报价方案.docx"
```

### 步骤五：验证输出

检查生成的 Word 文档，包含：
- 标题（案件类型 + 律师费报价方案）
- 第一部分：案件核心难度与专属工作量分析
- 第二部分：优化后律师费报价方案（三种方案）
- 第三部分：其他重要说明
- 落款：律所名称 + 律师姓名

## 使用示例

### 示例 1：离婚纠纷案件
- **场景**：用户需要为一起涉及3500万财产的离婚纠纷案件生成报价方案
- **输入**：
  ```bash
  python scripts/generate_quote.py --case-type "离婚纠纷" --property-amount 3500 --difficulty-level 5 --law-firm "浙江XX律师事务所" --lawyer-name "张三"
  ```
- **预期产出**：包含跨境股权分割、抚养权争夺等难度的专业报价方案

### 示例 2：合同纠纷案件
- **场景**：用户需要为一起500万标的的合同纠纷生成报价
- **输入**：
  ```bash
  python scripts/generate_quote.py --case-type "合同纠纷" --property-amount 500 --difficulty-level 3 --law-firm "北京XX律师事务所" --lawyer-name "李四" --province "北京"
  ```
- **预期产出**：标准合同纠纷报价方案

### 示例 3：完整参数
- **场景**：用户提供完整信息
- **输入**：
  ```bash
  python scripts/generate_quote.py --case-type "离婚纠纷" --property-amount 800 --difficulty-level 4 --law-firm "上海XX律师事务所" --lawyer-name "王五" --province "上海" --core-difficulties '["隐匿财产调查","跨境资产追踪","公司股权分割"]' --work-hours '{"证据筹备":"50-60","法律策略":"35-40","庭审谈判":"30-35","成果落地":"20-25"}' --output-path "./离婚案件报价.docx"
  ```
- **预期产出**：完全定制化的报价方案文档

## 资源索引

- 脚本：见 [scripts/generate_quote.py](scripts/generate_quote.py)（用途：生成律师费报价方案 Word 文档，参数：见上表）
- 参考：见 [references/fee_standards.md](references/fee_standards.md)（何时读取：需要了解各省律师费收费标准时）

## 注意事项

- 财产标的额单位为"万元"，如标的额为500万则输入 500
- 省份影响方案一中的政府指导价计算，默认为浙江省标准
- 难度等级 1-5 影响自动生成的难点描述和工作量估算
- 输出路径如不指定，默认保存到当前目录
- 生成的文档格式已预设，可直接打印或发送给客户
