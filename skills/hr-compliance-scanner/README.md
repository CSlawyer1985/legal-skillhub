---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: 5c0fa478708bf2c9ec3bd0adf95ae3f0_ce63e4a77b7211f1aac35254006c9bbf
    ReservedCode1: ANFP0LQqROim2TLKU1ezXjlj7eD1VVluIoJOwDRpLT0/5VF+DB3ECAUcl3qUvAZn40wLNlWGcwbXVq0pGJ3F23p5YcswGrcsvaJ+T5yqXoi5PQHXw9rgr43l0lUs1YdARqXeI8ucBxX9Jm1JIYx9gAod3JGCJCYW3gqL9M3Ou1I/jqHjpw8zb8Fa3k8=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: 5c0fa478708bf2c9ec3bd0adf95ae3f0_ce63e4a77b7211f1aac35254006c9bbf
    ReservedCode2: ANFP0LQqROim2TLKU1ezXjlj7eD1VVluIoJOwDRpLT0/5VF+DB3ECAUcl3qUvAZn40wLNlWGcwbXVq0pGJ3F23p5YcswGrcsvaJ+T5yqXoi5PQHXw9rgr43l0lUs1YdARqXeI8ucBxX9Jm1JIYx9gAod3JGCJCYW3gqL9M3Ou1I/jqHjpw8zb8Fa3k8=
---

# HR 合规风险扫描器

## 技能简介

面向中小企业 HR 的自动化合规风险扫描工具，覆盖劳动合同、员工手册、规章制度、裁员方案四大场景，检测 48+ 个风险点，输出五板块合规报告。

## 核心功能

- **四大场景**：劳动合同 / 员工手册 / 规章制度 / 裁员方案
- **风险检测**：48 个检测点，覆盖试用期、违约金、竞业限制、加班费、裁员程序、民主程序等
- **五板块报告**：风险标注 → 合规等级判定 → 修改建议 → 法规条文 → 报告摘要
- **快速参考卡**：法规速查表、风险等级判定表、常见违规条款速查

## 文件清单

| 文件 | 路径 |
|------|------|
| 主技能文件 | `HR合规风险扫描器/SKILL.md` |
| 需求说明书 | `HR合规风险扫描器/需求说明书.md` |
| 本说明 | `HR合规风险扫描器/README.md` |

## SkillHub 提交字段对照表

| 字段 | 填入内容 |
|------|----------|
| **Skill 文件** | 上传 `HR合规风险扫描器/` 整个文件夹 |
| **Slug** | `hr-compliance-scanner` |
| **显示名称** | HR 合规风险扫描器 |
| **图标** | 建议选择 `legal` 或 `safety` 类图标 |
| **描述** | 中小企业 HR 合规风险扫描工具，覆盖劳动合同、员工手册、规章制度、裁员方案四大场景，检测 48+ 风险点，输出五板块合规报告。 |
| **版本号** | 1.0.0 |
| **变更说明** | 初始版本，覆盖劳动合同/员工手册/规章制度/裁员方案四大场景，合计 48 个检测点，输出五板块合规报告。 |

## 使用示例

```
用户：帮我扫描这份劳动合同的合规风险
上传：劳动合同.pdf
输出：五板块合规报告，含风险标注、修改建议、法规依据
```

## 模块归属

本 Skill 属于 **员工关系** 模块，填补 HR 合规类 Skill 市场空白。

## 后续迭代方向

- 增加地方性法规差异识别（如上海/广东/北京）
- 支持批量文件扫描
- 增加合规趋势分析（如近三年高频风险点）
- 与电子签系统集成（如腾讯电子签）
*（内容由AI生成，仅供参考）*
