# 德国（DSGVO + BDSG + TDDDG）

## 目录
1. [法律框架](#legal-framework)
2. [监管机构](#supervisory-authorities)
3. [语言与形式要件](#language--formalities)
4. [法律依据——德国特殊规定](#legal-bases)
5. [保留期限](#retention-periods)
6. [Cookie 与跟踪规则（TDDDG）](#cookie--tracking-rules)
7. [儿童数据](#childrens-data)
8. [DPO 要求](#dpo-requirements)
9. [标准措辞模板](#standard-wording)

---

## 法律框架

| 法律 | 范围 |
|-----|-------|
| **DSGVO**（= GDPR） | 直接适用的欧盟条例 |
| **BDSG**（联邦数据保护法） | 联邦补充法律；员工数据（第 26 条）、DPO（第 38 条）、评分（第 31 条）、视频监控（第 4 条） |
| **TDDDG**（电信-数字服务-数据保护法） | Cookie 同意（第 25 条）、电信/数字服务隐私——取代 TTDSG（后者取代了 TMG/TKG 的相关条款） |
| **UWG**（反不正当竞争法） | 与直接营销/商业电子邮件同意相关 |
| **HGB / AO** | 商法和税法保留义务 |

## 监管机构

德国有 **18 个监管机构**（1 个联邦 BfDI + 16 个州数据保护专员 + 1 个教会特定 BfD EKD）。

起草时，依据控制者的注册所在地引用正确的机构：

| 州 | 机构 | 缩写 |
|-------|-----------|-------------|
| 联邦（电信、邮政、联邦机构） | BfDI | Bundesbeauftragter für den Datenschutz |
| 巴登-符腾堡 | LfDI BW | |
| 巴伐利亚（私营部门） | BayLDA | Bayerisches Landesamt für Datenschutzaufsicht |
| 巴伐利亚（公共部门） | BayLfD | |
| 柏林 | BlnBDI | |
| 勃兰登堡 | LDA Brandenburg | |
| 不来梅 | LfDI Bremen | |
| 汉堡 | HmbBfDI | |
| 黑森 | HBDI | |
| 梅克伦堡-前波美拉尼亚 | LfDI M-V | |
| 下萨克森 | LfD Niedersachsen | |
| 北莱茵-威斯特法伦 | LDI NRW | |
| 莱茵兰-普法尔茨 | LfDI RLP | |
| 萨尔 | ULD Saarland | |
| 萨克森 | SächsDSB | |
| 萨克森-安哈尔特 | LfD LSA | |
| 石勒苏益格-荷尔斯泰因 | ULD | |
| 图林根 | TLfDI | |

附正确的机构名称和 URL 的投诉权。

## 语言与形式要件

- 面向德国用户时，隐私声明**必须**为**德语**
- 使用"Sie"（正式）为标准；仅当品牌一贯使用非正式语气时才用"Du"
- 国际服务建议双语声明（DE + EN）
- Impressum（§ 5 TMG / DDG）在法律上独立，但常并列链接
- 常见标题：**"Datenschutzerklärung"**（而非"Datenschutzrichtlinie"）
- 从任何页面最多 **2 次点击**即可访问（BGH 判决）

## 法律依据

### 员工数据（BDSG 第 26 条）
如隐私声明涵盖员工（例如招聘门户、候选人追踪）：
- 法律依据：**BDSG 第 26 条第 1 款**（雇佣关系所需的处理）
- 特殊类别：**BDSG 第 26 条第 3 款**（明确同意或必要性）
- 职工委员会协议可作法律依据

### 特殊类别数据（BDSG 第 26 条第 3 款 + DSGVO 第 9 条）
德国劳动法产生几种常见的第 9 条处理场景：
- **教会税（Kirchensteuer）**：宗教是第 9 条数据。法律依据：DSGVO 第 6 条第 1 款第(c)项 + 第 9 条第 2 款第(b)项 + BDSG 第 26 条第 3 款 + EStG 第 51a 条。雇主必须为薪资处理宗教信仰；在声明中披露。
- **残疾状态（Schwerbehinderung）**：第 9 条下的健康数据。法律依据：DSGVO 第 6 条第 1 款第(c)项 + 第 9 条第 2 款第(b)项 + BDSG 第 26 条第 3 款 + SGB IX 第 164、168 条。为额外休假、特别解雇保护所需。
- **病假证明（AU-Bescheinigungen）**：健康数据。法律依据：DSGVO 第 6 条第 1 款第(c)项 + 第 9 条第 2 款第(b)项 + BDSG 第 26 条第 3 款 + EFZG 第 5 条。保留：通常为日历年结束后 1 年。
- **职业整合管理（BEM）**：健康数据。法律依据：DSGVO 第 6 条第 1 款第(c)项 + 第 9 条第 2 款第(b)项 + BDSG 第 26 条第 3 款 + SGB IX 第 167 条第 2 款。BEM 文件必须与人事档案分开存放。
- **工会会费**：工会会员身份是第 9 条数据。如通过薪资扣缴：DSGVO 第 6 条第 1 款第(b)/(c)项 + 第 9 条第 2 款第(b)项 + BDSG 第 26 条第 3 款。
- **生物识别门禁**：用于建筑出入的指纹/人脸识别。通常要求第 9 条第 2 款第(a)项明确同意（BDSG 第 26 条第 3 款第 2 句）。适用职工委员会共决权（BetrVG 第 87 条第 1 款第 6 项）。建议进行 DPIA。

### 视频监控（BDSG 第 4 条）
如场所被监控：
- 入口处需单独通知
- DSGVO 第 6 条第 1 款第(f)项 + BDSG 第 4 条
- 保留：通常 48-72 小时，以目的为限的最大值

### 评分与信用评估（BDSG 第 31 条）
与带信用检查的电子商务或金融服务相关。

### TDDDG 第 25 条下的同意
- Cookie/跟踪同意遵循 **TDDDG 第 25 条**（实施 ePrivacy 指令第 5 条第 3 款）
- 同意必须满足 DSGVO 第 7 条标准
- 适用 Planet49（欧洲法院）和 Cookie-Einwilligung II（BGH）判例

## 保留期限

| 数据类别 | 期限 | 法律依据 |
|---|---|---|
| 商业往来函件 | 6 年 | HGB 第 257 条 |
| 涉税记录、发票 | 10 年 | AO 第 147 条、HGB 第 257 条 |
| 候选人数据（被拒） | 拒后 6 个月 | AGG 诉讼时效 |
| 员工数据 | 雇佣期间 + 3 年（时效） | BDSG 第 26 条 |
| 服务器日志文件 | 7-30 天 | DSGVO 第 6 条第 1 款第(f)项 |
| 合同数据 | 期间 + 3 年（一般时效） | BGB 第 195、199 条 |
| 活跃客户账户 | 关系存续期间 | DSGVO 第 6 条第 1 款第(b)项 |
| 不活跃潜在客户 | 无互动 3 年 | DSGVO 第 6 条第 1 款第(f)项——平衡测试 |
| Cookie 同意记录 | 3 年（同意证明） | DSGVO 第 7 条第 1 款 |
| 闭路电视录像 | 48-72 小时（标准）、有理由的最大值 | BDSG 第 4 条 |
| 电信流量数据 | 10 周（TKG 第 176 条） | TDDDG/TKG |

## Cookie 与跟踪规则

### TDDDG 第 25 条框架
- 对终端用户设备上信息的任何访问或存储**均需同意**，除非严格必要
- "严格必要"作狭义解释（会话 Cookie、购物车、负载均衡——是；分析、广告——否）
- 服务端分析（例如无 Cookie 的 Matomo）可能不属第 25 条范围，但仍需第 6 条第 1 款第(f)项评估
- 同意横幅必须提供与**全部接受**同等突出的**全部拒绝**（Planet49、BGH）

### 常见德国 CMP 解决方案
Usercentrics、Cookiebot、Consentmanager、Borlabs Cookie（WordPress）

### Google Analytics 特殊说明
DSK（数据保护会议）反复提出关切。如使用：
- 确保 Google Analytics 4 带 IP 匿名化
- 首选服务端标记
- 需要同意（无合法利益）
- 考虑 Matomo/Plausible 作为合规替代方案

## 儿童数据

- GDPR 第 8 条门槛：德国设定为 **16 岁**（TDDDG 第 2 条第 17 款，国内实施）
- 如服务面向未成年人：需要父母同意机制
- 隐私声明必须使用适龄语言

## DPO 要求

### 强制 DPO（BDSG 第 38 条）
- **≥ 20 人**持续从事自动化处理
- 核心活动：大规模处理特殊类别（DSGVO 第 9/10 条）
- 核心活动：系统性监测（DSGVO 第 37 条第 1 款第(c)项）

如已任命，始终在隐私声明中附 DPO 联系方式。使用功能性邮箱（datenschutz@...、dpo@...）。

## 标准措辞

### 投诉权（德语）
```
Sie haben das Recht, sich bei einer Datenschutzaufsichtsbehörde über die Verarbeitung Ihrer personenbezogenen Daten zu beschweren. Die für uns zuständige Aufsichtsbehörde ist:

[Name der Aufsichtsbehörde]
[Adresse]
[URL]
```

### 反对权（第 21 条——强制性单独告知）
```
WIDERSPRUCHSRECHT

Sie haben das Recht, aus Gründen, die sich aus Ihrer besonderen Situation ergeben, jederzeit gegen die Verarbeitung Sie betreffender personenbezogener Daten, die auf Grundlage von Art. 6 Abs. 1 lit. e oder f DSGVO erfolgt, Widerspruch einzulegen.

Werden Ihre personenbezogenen Daten verarbeitet, um Direktwerbung zu betreiben, haben Sie das Recht, jederzeit Widerspruch gegen die Verarbeitung einzulegen.
```

### 责任方引言（德语）
```
Verantwortlich im Sinne der Datenschutz-Grundverordnung (DSGVO) ist:

[Firmenname]
[Rechtsform]
[Straße, PLZ Ort]
Vertreten durch: [Geschäftsführer/Vorstand]
E-Mail: [E-Mail]
Telefon: [Telefon]
```
