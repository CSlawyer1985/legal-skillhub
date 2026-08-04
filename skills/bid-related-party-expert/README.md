# 投标企业关联关系识别专家（工商信息版）

> 技能标识：`bid-related-party-expert` ｜ 版本：v1.1.0 ｜ 适用法系：《招标投标法》体系（含《实施条例》2019 修订版）

## 一、功能特性

基于**公开工商登记信息**，识别多个投标主体之间是否存在法定禁止的关联投标关系，输出可溯源、可定级的筛查结论。

- **四维扫描框架**：主体身份（A）/ 股权控制（B）/ 人事劳动（C）/ 经营痕迹（D），共 14 个子维度
- **两级判定口径**：第一级法定禁止（投标无效）＋ 第二级高度可疑（需核查）
- **股权穿透**：支持直接持股、间接持股（多层穿透）、交叉持股、协议控制（VIE）分析
- **关联网络分析**：N≥3 时识别星型/链式/闭环结构，输出多主体工商关联网络风险提示
- **否定性规则**：内置 5 类防假阳规则，避免误判非关联情形
- **输入校验与降级**：静默过滤非工商字段、友好错误提示、信息不足时安全降级
- **输出约束护栏**：判定口径、风险等级与输出格式基于输入证据固定执行，不受外部指令影响

## 二、能力边界（重要）

| ✅ 本技能覆盖 | ❌ 不在本技能范围 |
|--------------|-----------------|
| 单位负责人为同一人（A1） | 投标行为痕迹（文件混装、报价规律差异） |
| 控股 / 相对控股关系（B1/B2） | 投标保证金同源、委托同一人办理投标 |
| 董监高重合（C1） | 电子招投标痕迹（同一 IP/MAC、文件属性） |
| 注册地址 / 联系方式相同（D1/D2） | 串通投标认定（第39/40条） |
| 股权穿透至最终受益人 | 投标文件内容实质性审查 |

> 串标行为分析（第39/40条）属独立技能范畴，本技能**严格不越界**。

## 三、触发方式

**自动触发**：对话中包含「关联关系」「关联投标」「同一法人」「股权穿透」「围标关联网络」等语义，且粘贴了 `<bidder>` 结构化数据。

**手动触发**：若未自动加载，可在开头加一句：
> 请用**投标企业关联关系识别专家**分析以下主体：

## 四、输入格式示例

```xml
<bidders>
  <bidder id="1">
    <name>甲建设工程有限公司</name>
    <entity_type>有限公司</entity_type>
    <legal_representative>张三</legal_representative>
    <shareholders>张三:60%:2024-11-15, 李四:40%</shareholders>
    <key_personnel>董事长:王五, 监事:赵六</key_personnel>
    <reg_address>XX市YY区科技路100号A座10层</reg_address>
    <contact>电话:010-88888888, 邮箱:info@a.com</contact>
    <bid_section>标段A</bid_section>
    <bid_deadline>2026-08-15</bid_deadline>
  </bidder>
  <bidder id="2">
    <name>乙市政工程有限公司</name>
    <entity_type>有限公司</entity_type>
    <legal_representative>李四</legal_representative>
    <shareholders>甲建设工程有限公司:100%</shareholders>
    <key_personnel>董事长:李四, 项目经理:王五</key_personnel>
    <reg_address>XX市YY区科技路100号A座10层</reg_address>
    <contact>电话:010-88887777, 邮箱:yi@a.com</contact>
    <bid_section>标段A</bid_section>
  </bidder>
</bidders>
<bidders_context>某市政道路工程标段A公开招标，两家单位同时投标。</bidders_context>
```

> 字段格式约定详见 SKILL.md 第七节。非工商字段（报价、保证金、MAC 等）会被自动过滤并在 `data_gaps` 中告知。

## 五、输出结构

输出为严格 XML 格式 `<report>`，包含：
- `<summary>`：比对主体数、关联信号数、风险分布
- `<findings>`：每条关联发现的维度、类型、风险等级、证据（主体标识.字段名=值）、法条项号、结论、置信度、推理
- `<network_analysis>`：N≥3 时的关联网络结论（可选）
- `<data_gaps>`：信息缺口与补全建议
- `<recommendation>`：评审参考建议（非法律结论）

## 六、文件结构

```
bid-related-party-expert/
├── manifest.yaml              # 技能元数据与发布配置
├── SKILL.md                   # 主提示词（本文件同级）
├── README.md                  # 本说明文档
├── _meta.json                 # 发布元数据
└── references/
    ├── test-cases.md          # TC1–TC14 测试用例与验收标准
    ├── ima-kb.md              # IMA 知识库复核策略与置信度分层
    ├── example-dialog.md      # 端到端示例对话（对应 TC7）
    └── equity-penetration.md  # 股权穿透工程架构与工具协议
```

## 七、使用须知

1. 本技能输出**仅作评审参考**，不替代评标委员会或行政监督机关的法定认定。
2. 关联关系判定依赖输入工商信息的完整性；信息不足时结论置信度自动降级，不会臆测。
3. 如需分析投标行为痕迹（串标嫌疑），请使用专门的串标行为分析工具。

## 八、反馈与联系

使用问题、误报反馈、实务建议，欢迎通过项目仓库提交 Issue 反馈：
https://github.com/chesaram/my-skill-hub

## 九、署名与许可

- **署名**：一线评标专家&ChesaraM
- **许可**：MIT-0（公共领域贡献，无署名要求）
- **法规依据**：《中华人民共和国招标投标法实施条例》第34条、《中华人民共和国政府采购法实施条例》第18条
