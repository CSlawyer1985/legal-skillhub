# 法国（RGPD + 《信息技术与自由法》+ LCEN）

## 目录
1. [法律框架](#legal-framework)
2. [监管机构](#supervisory-authority)
3. [语言与手续](#language--formalities)
4. [法律依据——法国特殊性](#legal-bases)
5. [保留期限](#retention-periods)
6. [Cookie 与追踪规则](#cookie--tracking-rules)
7. [儿童数据](#childrens-data)
8. [DPO 要求](#dpo-requirements)
9. [标准措辞模板](#standard-wording)

---

## 法律框架

| 法律 | 范围 |
|-----|-------|
| **RGPD**（= GDPR） | 直接适用的欧盟条例 |
| **《信息技术与自由法》**（LIL，经修订的第 78-17 号法律） | 国家实施法律；健康数据、研究、刑事数据 |
| **LCEN**（《数字经济信任法》） | 日志保留义务（1 年）、托管责任 |
| **《邮政与电子通信法典》** | ePrivacy 转化、cookie 同意 |

## 监管机构

| 机构 | 详情 |
|-----------|---------|
| **CNIL**（法国国家信息技术与自由委员会） | 单一国家监管机构 |
| 地址 | 3 Place de Fontenoy – TSA 80715 – 75334 Paris Cedex 07 |
| 在线投诉 | https://www.cnil.fr/fr/plaintes |

## 语言与手续

- 如面向法国用户，隐私通知**必须为法语**
- 「Vous」（尊称）为标准用法
- 常见标题：**「Politique de confidentialité」**或**「Protection des données personnelles」**
- Mentions légales（法律声明，LCEN 第 6 条）在法律上独立，但常同页呈现
- CNIL 建议**分层方法**：摘要 + 全文

## 法律依据

### 商业推销（prospection commerciale）
- **B2C 电子邮件**：须同意（《邮政与电子通信法典》第 L.34-5 条），除非现有客户 + 类似产品 + 退出选项（软选择加入）
- **B2B 电子邮件**：如与专业职能相关，合法利益可能成立，须提供退出
- **短信/彩信**：始终须同意

### 健康数据
- LIL 第 44 条及以下：健康数据的额外保障
- 健康数据托管须 HDS（健康数据托管）认证
- 就业前体检：《通用数据保护条例》第 9(2)(h) 条 + 《劳动法典》第 R.4624-10 条。仅向雇主披露适合/不适合的结果，而非诊断。

### 特殊类别数据——法国特殊性（GDPR 第 9 条 + LIL）
- **生物识别数据**：CNIL《标准条例》（第 2019-001 号审议决定）规范工作场所生物识别门禁。要求 DPIA、严格必要性测试和事先告知员工。明确同意或第 9(2)(b) 条雇佣法依据。
- **工会会员**：《劳动法典》第 L.2141-5 条禁止基于工会活动的歧视。如涉工资（工会会费扣缴）：第 9(2)(b) 条 + 第 6(1)(c) 条。访问须严格限制。
- **宗教数据**：法国的世俗原则限制宗教数据的收集。一般禁止，除非法律要求（如特定情境下的饮食安排）。无与德国教会税对应的制度。
- **雇佣中的健康数据**：病假（arrêt maladie）：雇主仅收到证明，而非诊断。职业健康（médecine du travail）：GDPR 第 9(2)(h) 条 + 《劳动法典》。CNIL 建议分开存储并限制访问。
- **基因数据**：LIL 第 75 条提供额外限制。仅允许为医疗、科学研究或司法目的处理。

### 研究与统计
- LIL 第三章为科学研究提供特定制度
- CNIL 简化程序（参考方法论 MR-001 至 MR-006）

## 保留期限

| 数据类别 | 期限 | 法律依据 |
|---|---|---|
| 活跃客户数据 | 合同关系存续期 | GDPR 第 6(1)(b) 条 |
| 不活跃潜在客户 | 自最后联系起 3 年 | CNIL 建议 |
| 发票与会计 | 10 年 | 《商法典》第 L.123-22 条 |
| 商业合同 | 结束后 5 年 | 《民法典》第 2224 条 |
| 连接日志（托管） | 1 年 | LCEN 第 6 条 II、第 2011-219 号法令 |
| 工资数据 | 5 年 | 《劳动法典》第 L.3243-4 条 |
| 申请者数据（被拒） | 最多 2 年 | CNIL 建议 |
| Cookie 同意证明 | 6 年（合同时效） | 《民法典》第 2224 条 |
| 监控录像 | 最多 30 天 | 《国内安全法典》第 L.252-3 条 |
| 医疗记录 | 自最后一次就诊起 20 年 | 《公共卫生法典》第 R.1112-7 条 |

## Cookie 与追踪规则

### CNIL 2020 年指南
CNIL 的《cookie 和追踪器指南》（第 2020-091 号审议决定）和《cookie 建议》（第 2020-092 号审议决定）设定标准：

- 所有非必要 cookie/追踪器**均须同意**
- 「继续浏览」不构成有效同意
- 拒绝必须与接受一样容易（无暗黑模式）
- Cookie 墙：一般禁止，除非存在访问替代方案
- 最大 cookie 寿命：**13 个月**；建议每 **6 个月**续期同意
- 必须存储同意证明

### CNIL 制裁参考
| 公司 | 金额 | 理由 |
|---------|--------|--------|
| Google LLC 与 Ireland | 1.5 亿欧元 | 拒绝 cookie 比接受更复杂 |
| Facebook Ireland | 6000 万欧元 | 无「全部拒绝」按钮 |
| Amazon Europe | 3500 万欧元 | 未经事先同意放置 cookie |
| Microsoft Ireland | 6000 万欧元 | 未经同意放置 cookie |
| Criteo | 4000 万欧元 | cookie 同意和信息缺陷 |
| TikTok | 500 万欧元 | cookie 拒绝机制过于复杂 |

### 豁免 cookie（无需同意）
- 会话/身份验证 cookie
- 购物车 cookie
- 负载均衡 cookie
- cookie 同意选择存储
- 满足 CNIL 特定条件的受众测量（特定配置的 Matomo）

### CNIL 合规分析
CNIL 维护一份在特定配置下豁免同意的分析工具清单。Matomo（采用 CNIL 推荐设置）是主要示例。

## 儿童数据

- 法国：**15 岁**（LIL 第 45 条，实施 GDPR 第 8 条）
- 15 岁以下：双重同意（儿童 + 父母监护权持有人）
- 通知必须以未成年人可理解的语言书写

## DPO 要求

与 GDPR 第 37 条相同——无额外法国门槛（不同于德国《联邦数据保护法》第 38 条）。

以下情形强制：
- 公共机关/机构
- 核心活动：大规模定期/系统性监测
- 核心活动：大规模处理特殊类别数据

CNIL 强烈建议在所有情况下自愿任命。

## 标准措辞

### 投诉权（法语）
```
Vous disposez du droit d'introduire une réclamation auprès de la Commission Nationale de l'Informatique et des Libertés (CNIL) :

CNIL
3 Place de Fontenoy – TSA 80715
75334 Paris Cedex 07
www.cnil.fr
```

### 反对权（法语）
```
DROIT D'OPPOSITION

Vous pouvez vous opposer à tout moment au traitement de vos données personnelles fondé sur l'intérêt légitime (article 6.1.f du RGPD), pour des raisons tenant à votre situation particulière.

Si vos données personnelles sont traitées à des fins de prospection commerciale, vous pouvez vous y opposer à tout moment, sans avoir à justifier de motifs particuliers.
```

### 责任方介绍（法语）
```
Le responsable du traitement de vos données personnelles est :

[Dénomination sociale]
[Forme juridique], au capital de [montant] euros
Immatriculée au RCS de [ville] sous le numéro [SIREN/SIRET]
Siège social : [adresse complète]
Représentée par [Nom], en qualité de [fonction]
E-mail : [email]
Téléphone : [téléphone]
```
