# 版权声明

## 声明摘要

本 Skill 为**完全重写版本**，不包含任何原版的文字表达。

---

## 一、核心方法论来源

### 法律审核通用实践（行业公共知识）

以下内容属于法律审核领域的通用方法论，不受版权保护：

- **审核维度概念**：准确性、逻辑性、规范性等（行业通用标准）
- **风险分级概念**：高风险、中风险、低风险（行业标准实践）
- **问题分类概念**：法律风险、商业风险、表述问题等（行业通用分类）
- **批注结构概念**：问题、风险、建议、条款（行业通行做法）
- **合同结构识别**：定义、标的、价款、违约等（法律逻辑）
- **定金限制**：不超过 20%（法律规定）
- **违约金合理范围**：实际损失的 30% 以内（司法实践）

上述内容为法律审核行业的公共知识，任何人均可自由使用。

---

## 二、本版本创作声明

### 完全原创内容

以下内容由 WUDI 编写，以 GPL-3.0 协议发布：

| 文件 | 内容 | 原创性 |
|------|------|--------|
| `scripts/contract_parser.py` | 合同结构解析引擎 | 100% 新代码 |
| `scripts/apply_changes.py` | 修订痕迹与批注写入引擎 | 100% 新代码 |
| `scripts/generate_clean.py` | 清洁版生成引擎 | 100% 新代码 |
| `scripts/iteration_manager.py` | 多轮迭代管理引擎 | 100% 新代码 |
| `scripts/prepare_output_paths.py` | 路径准备工具 | 100% 新代码 |
| `references/engine-guide.md` | 引擎使用指南 | 100% 新文档 |

### 重新表述内容

以下内容基于法律审核通用方法论，由 WUDI 重新表述：

| 文件 | 说明 |
|------|------|
| `SKILL.md` | 基于通用审核方法论，使用全新表达 |
| `references/review-playbook.md` | 基于通用审核实践，重新编写 |
| `references/output-spec.md` | 基于通用输出规范，重新编写 |

**重写方法**：
- 思想来源：法律审核通用方法论（行业公共知识）
- 表达方式：完全重新编写，不复制任何原版文字
- 结构组织：重新设计文件结构和内容组织

---

## 三、与原版的关系

### 不构成侵权的理由

1. **思想与表达二分法**
   - 审核方法论属于"思想"，不受版权保护
   - 本版本使用全新的"表达"，不存在复制

2. **原创代码**
   - 原版只有 29 行 Python 代码
   - 本版本包含 1700+ 行全新 Python 代码
   - 代码部分不存在任何复制

3. **重新表述**
   - 所有文档均使用新的文字表达
   - 不存在逐字复制或改写
   - 结构和编排完全重新设计

4. **功能增强**
   - 新增四大引擎模块
   - 新增多轮迭代管理
   - 原版不具备执行能力，本版本提供完整实现

---

## 四、许可证

### GNU General Public License v3.0

```
GNU GENERAL PUBLIC LICENSE
Version 3, 29 June 2007

Copyright (C) 2026 WUDI

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
```

完整许可证文本请参阅：https://www.gnu.org/licenses/gpl-3.0.txt

### GPL-3.0 核心约束

- ✅ 自由使用、研究、修改、分发
- ✅ 可用于商业用途
- ⚠️ **修改后的版本必须同样以 GPL-3.0 协议开源**
- ⚠️ **分发时必须提供源代码或获取源代码的方式**
- ⚠️ **必须保留原始版权声明和许可证**

---

## 五、致谢

本 Skill 的审核方法论基于法律审核通用实践，属于行业公共知识。感谢所有法律从业者对本领域的贡献。

---

## 六、版本信息

- **版本**: 2.0.0
- **发布日期**: 2026-04-15
- **作者**: WUDI
- **许可证**: GPL-3.0
- **原创性**: 100% 重写

---

*本声明旨在明确版权归属，避免争议。*
