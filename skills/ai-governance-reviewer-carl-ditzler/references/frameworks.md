# 框架参考

在作出监管、治理或引用性主张时使用本文件。

## 优先考虑的主要来源

1. 欧盟《AI 法案》
- 包括欧盟通用 AI（GPAI）实践准则
2. GDPR
3. NIST AI RMF 1.0
4. OECD AI 原则
5. ISO/IEC 23894:2023
6. 用户提供的任何公司政策、AI 标准或 AI 禁区清单

次要来源可以补充，但不得凌驾于主要法律或所提供的公司政策之上。

对实质性法律分析，优先考虑法律和公司政策。将 NIST AI RMF 1.0 和 ISO/IEC 23894:2023 视为支持风险管理和控制设计的治理框架来源。在本技能中，NIST AI RMF 和 ISO/IEC 23894:2023 是后备治理框架，而非主要法律权威。

## 负责任 AI 实践参考

对治理计划设计、升级纪律、证据预期和操作性负责任 AI 实践，另请阅读：
- [responsible-ai-practice.md](responsible-ai-practice.md)

将这些实践参考用作治理指导，而非约束性法律的替代品。

## 捆绑的源文件

使用捆绑的本地源文件进行框架审查。优先使用 `working/` Markdown 文件进行检索、提取和起草。如措辞、编号、结构或范围有任何不一致，以对应的 `official/` PDF 为准。

### 文件映射

| 框架或法律 | 工作 Markdown | 官方来源 |
|---|---|---|
| 欧盟《AI 法案》 | `references/working/EU AI ACT.md` | `references/official/EU AI ACT.pdf` |
| 欧盟 GPAI 实践准则——著作权章 | `references/working/EU GPAI Code_of_Practice_for_GeneralPurpose_AI_Models_Copyright_Chapter.md` | `references/official/EU GPAI Code_of_Practice_for_GeneralPurpose_AI_Models_Copyright_Chapter.pdf` |
| 欧盟 GPAI 实践准则——安全与保障章 | `references/working/EU GPAI Code_of_Practice_for_GeneralPurpose_AI_Models_Safety_and_Security_Chapter.md` | `references/official/EU GPAI Code_of_Practice_for_GeneralPurpose_AI_Models_Safety_and_Security_Chapter.pdf` |
| 欧盟 GPAI 实践准则——透明度章 | `references/working/EU GPAI Code_of_Practice_for_GeneralPurpose_AI_Models_Transparency_Chapter.md` | `references/official/EU GPAI Code_of_Practice_for_GeneralPurpose_AI_Models_Transparency_Chapter.pdf` |
| GDPR | `references/working/GDPR.md` | `references/official/GDPR.pdf` |
| NIST AI RMF 1.0 | `references/working/NIST AI RMF 100-1.md` | `references/official/NIST AI RMF 100-1.pdf` |
| OECD AI 原则 | `references/working/OECD-LEGAL-0449-en.md` | `references/official/OECD-LEGAL-0449-en.pdf` |
| ISO/IEC 23894:2023 | `https://www.iso.org/standard/77304.html` | `https://cdn.standards.iteh.ai/samples/77304/cb803ee4e9624430a5db177459158b24/ISO-IEC-23894-2023.pdf` |

当用例涉及通用 AI 模型或基础模型义务时，将欧盟《AI 法案》与三个 GPAI 实践准则章节文件结合使用。
将 ISO/IEC 23894:2023 和 NIST AI RMF 用作操作性分析的补充 AI 风险管理框架。

## 来源验证协议

在作出监管主张之前：
1. 识别适用的法律、框架或公司政策，并加载上面映射的捆绑文件。
2. 确认该主张是否得到捆绑源材料或其他已验证的主要来源的支持。
3. 尽可能引用法规、条文、章节、条款、框架功能或公司政策章节。
4. 区分：
   - 约束性法律或法规
   - 治理框架
   - 内部公司政策
   - 最佳实践指南

如工作 Markdown 文件与官方 PDF 不一致，以官方 PDF 为准，并在此不一致影响分析时注明。

对 ISO/IEC 23894:2023：
- 本技能不依赖捆绑的本地文件；
- 改用 ISO 标准页面和提供的 iTeh 样张/PDF 链接；
- 将 ISO/IEC 23894:2023 视为 AI 风险管理结构的治理框架来源。

如无法确认精确的条文或章节支持，声明：
> 精确引文未经验证；指导源自摘要、先前知识或次要来源。依赖此输出前请先核验。

## 置信水平

| 级别 | 含义 |
|---|---|
| 高 | 规则得到已验证的主要来源或明确提供的公司政策的支持 |
| 中 | 规则得到权威框架或部分验证来源的支持 |
| 低 | 规则不确定、未完全验证，或依赖缺失的背景 |

## 核心映射

| 领域 | 主要框架 |
|---|---|
| 风险分类和禁止做法 | 欧盟《AI 法案》 |
| 隐私、个人数据和转移 | GDPR |
| AI 风险管理控制 | NIST AI RMF；ISO/IEC 23894:2023 |
| 负责任 AI 原则 | OECD AI 原则 |
| 操作性 AI 风险治理 | ISO/IEC 23894:2023；NIST AI RMF |

## 解释护栏

- 绝不虚构法律要求。
- 除非指导实际是法律或公司政策，否则绝不声称其具有法律约束力。
- 如未提供公司规则，绝不推断公司特定的禁止使用规则。
- 如公司政策缺失，说明公司特定禁令不可用，并仅以法律和治理最佳实践继续。
- 不让 `working/` Markdown 文件凌驾于对应的 `official/` PDF。

## 常见审查提示

在映射事实时使用这些提示：
- 组织扮演什么角色：提供者、部署者、集成者、分销商、进口商、内部业务用户或供应商的客户？
- 用例是否触及受监管或高影响的领域，如就业、法律服务、金融、医疗、教育、住房、保险、安全、生物识别或公共部门决策？
- 系统是否处理个人数据、特殊类别数据、机密数据或客户数据？
- 是否存在透明度、人工审查、文件记录、测试和监测义务？

## 法律审查触发示例

当用例涉及以下情形时，强烈升级进行法律审查：
- 高风险或禁止使用分析
- 个人或敏感数据
- 受监管行业
- 实质性客户依赖
- 供应商训练权不明确
- 跨境数据转移问题
- 就业或歧视风险敞口
