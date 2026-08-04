---
name: requete-cph-licenciement-faute-grave-selim-brihi
description: 起草向法国劳资法庭（Conseil de prud'hommes）提交的诉状，用于质疑因严重过错（faute grave）而作出的解雇。当用户要求起草 CPH 诉状、质疑因严重过错作出的解雇、为与解雇相关的争议准备向 CPH 起诉，或创建法国劳动法下的解雇质疑文件时使用本技能。
metadata:
  author: Sélim Brihi
  license: AGPL-3.0
  version: 2026.01.23
---

# CPH 诉状——质疑因严重过错作出的解雇

本技能指导为一名员工起草向法国劳资法庭（Conseil de prud'hommes，法国劳动司法机构）提交的诉状，该员工质疑其因严重过错（faute grave）而遭解雇，并请求将解雇重新定性为无真实且严肃理由的解雇。

## 开始起草前必须收集的信息

在起草诉状之前，必须向用户收集以下信息：

### 1. 员工信息（原告）
- 姓名
- 出生日期和地点
- 国籍
- 完整地址
- 职业/担任的职位

### 2. 雇主信息（被告）
- 公司名称
- 法律形式（SAS、SARL、SA、协会等）
- SIRET 编号
- RCS 编号及登记城市
- 注册办公地址
- 企业员工规模（< 或 > 11 名员工）
- APE 代码
- 适用的集体协议（名称和 IDCC 编号）

### 3. 劳动关系信息
- 入职日期
- 合同类型（书面无固定期限合同 CDI）
- 职级/职能
- 身份（管理层或非管理层）
- 月平均总工资（按最近 3 或 12 个月计算）
- 工龄（按解雇日期计算）
- 工作地点

### 4. 解雇程序信息
- 预先面谈传唤日期
- 预先面谈日期
- 解雇通知日期（信函日期）
- 雇主在解雇信函中援引的理由
- 解雇信函的确切内容（如可得）

### 5. 事实信息
- 劳动关系的历史（时长、可能的事件、评估）
- 解雇的背景（解雇前发生的事件）
- 雇主提出的指控
- 员工质疑这些指控的论点
- 可用的证据材料（证词、电子邮件、文件等）
- 友好解决尝试（如适用）

### 6. 律师信息（如由律师代理）
- 姓名
- 所属律师公会
- 袍号（如巴黎律师公会）
- 律所地址
- 电话和电子邮件

### 7. 期望的财务请求
向员工解释可能的各种赔偿并帮助其计算：
- 无真实且严肃理由解雇的赔偿金（按工龄和员工规模的法律最低标准）
- 法定解雇补偿金
- 预告期补偿金
- 与预告期相关的带薪假期
- 工资补发（如预防性停职无正当理由）
- 独立损害的精神损害赔偿（如适用）
- 失业救济金返还（如适用）

## 起草工作流

### 第一阶段：信息收集
以交互方式向用户收集上述所有信息。对话示例见 [conseils-variations.md](references/conseils-variations.md)。

### 第二阶段：赔偿金计算
计算各项赔偿金额。公式和标准见 [calculs-indemnites.md](references/calculs-indemnites.md)。

### 第三阶段：起草诉状
按 9 个部分的结构起草诉状。完整模板见 [structure-requete.md](references/structure-requete.md)。

### 第四阶段：核查与定稿
核查文件的连贯性。见 [conseils-variations.md](references/conseils-variations.md) 中的"定稿"一节。

### 第五阶段：创建文件
以 .docx 格式创建最终文件并呈现给用户。

## 详细参考

- **诉状结构**：完整 9 部分模板见 [structure-requete.md](references/structure-requete.md)（页眉、当事人识别、法律警告、事实回顾、理由陈述、请求、据此理由、签名）

- **赔偿金计算**：参考工资、工龄、法定解雇补偿金、预告期的计算公式以及无真实且严肃理由解雇赔偿金的标准见 [calculs-indemnites.md](references/calculs-indemnites.md)

- **建议与变体**：关键判例、起草建议、注意事项、对话示例、按情形的变体以及定稿检查清单见 [conseils-variations.md](references/conseils-variations.md)
