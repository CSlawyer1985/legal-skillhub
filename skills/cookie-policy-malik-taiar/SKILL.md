---
name: cookie-policy-malik-taiar
description: 起草符合 GDPR 和 ePrivacy 指令的 Cookie 政策的指南。包含 CNIL 2020 建议、参考模板和最佳实践。在起草或修订网站或应用的 Cookie 政策时使用。
metadata:
  author: Malik Taiar
  license: AGPL-3.0
  version: 2025.12.24
---

# Cookie 政策指南

## 概述

Cookie 政策向用户告知其设备上放置的 Cookie 和追踪器。它与隐私政策有别，但可并入其中。它必须符合 CNIL 2020 指南。

### Cookie 政策目标

| 目标 | 要求 |
|-----------|-------------|
| **透明度** | 告知使用的 Cookie 及其目的 |
| **同意** | 获得自由、知情且事先的同意 |
| **控制** | 允许用户管理其偏好 |
| **合规** | 遵守 GDPR + ePrivacy + CNIL 建议 |

---

## 参考资料

### 模板

| 模板 | 描述 |
|----------|-------------|
| `assets/sample_template_politique_cookies.docx` | 未提供私人模板时使用的默认模板 |
| 律师提供的内部模板 | 律师有更合适的私人模板时使用 |

### CNIL 文档

| 需阅读的 PDF 文件（Read 工具） | 需查阅的 URL（WebFetch 工具） | 主题 |
|------------------------------|--------------------------------|-------|
| `assets/CNIL_lignes_directrices_cookies_et_traceurs.pdf` | - | Cookie 指南 |
| `assets/CNIL_recommandation_cookies_et_traceurs.pdf` | https://www.cnil.fr/fr/cookies-et-autres-traceurs/regles/cookies | Cookie 建议 |
| `assets/CNIL_faq_cookies_et_traceurs.pdf` | https://www.cnil.fr/fr/cookies-et-autres-traceurs/regles/cookies/FAQ | Cookie 常见问题 |
| `assets/CNIL_evolution_regles_utilisation_cookies.pdf` | https://www.cnil.fr/fr/evolution-des-regles-dutilisation-des-cookies-quels-changements-pour-les-internautes | 规则演变 |
| `assets/CNIL_transparence.pdf` | - | 信息告知与透明度指南 |
| `assets/CNIL_principes_rgpd.pdf` | - | GDPR 基本原则 |
| `assets/RGPD_texte_officiel.pdf` | - | 欧盟条例 2016/679 全文 |

> **要求**：对于任何有关 Cookie、同意、保存期限、豁免或最佳实践的信息：
> 1. 就监管要点作答**之前**，先用 Read 工具**阅读 PDF 文件**
> 2. 用 WebFetch **查阅在线 URL** 以核验最新信息
> 3. 提及规则或期限时，在回答中**引用 CNIL URL**
> 4. 未经来源核验，**绝不编造**期限或规则

### 知识库

| 文档 | 内容 |
|----------|---------|
| **[COOKIES.md](references/COOKIES.md)** | Cookie 类别、横幅、CNIL 处罚、保存期限 |
| **[BASES_LEGALES_COOKIES.md](references/BASES_LEGALES_COOKIES.md)** | Cookie 特定法律依据（同意、豁免） |
| **[DROITS_PERSONNES.md](references/DROITS_PERSONNES.md)** | 数据主体权利 |
| **[DUREES_CONSERVATION.md](references/DUREES_CONSERVATION.md)** | 保存期限（CNIL 建议同意 Cookie 6 个月，最长 13 个月） |

---

## 需向客户收集的信息

> **重要**：起草政策前，收集以下信息。

### 1. 网站发布者信息

- [ ] 完整公司名称
- [ ] 法律形式（SAS、SARL、Ltd 等）
- [ ] 注册办公地址
- [ ] 联系邮箱
- [ ] 网站 URL

### 2. 使用的 Cookie

严格必要 COOKIE（免于同意）
- [ ] 会话 Cookie
- [ ] 认证 Cookie
- [ ] 购物车 Cookie
- [ ] 安全 Cookie（CSRF）
- [ ] 语言偏好 Cookie
- [ ] 记忆 Cookie 选择的 Cookie

分析 COOKIE
- [ ] Google Analytics
- [ ] Matomo
- [ ] AT Internet
- [ ] 其他：___________

广告 / 营销 COOKIE
- [ ] Google Ads
- [ ] Facebook Pixel
- [ ] LinkedIn Insight Tag
- [ ] Criteo
- [ ] 其他：___________

社交媒体 COOKIE
- [ ] Facebook 分享按钮
- [ ] Twitter/X 分享按钮
- [ ] LinkedIn 分享按钮
- [ ] 嵌入 YouTube 视频
- [ ] 其他：___________

功能 COOKIE
- [ ] 在线聊天（如 Intercom、Crisp）
- [ ] 视频播放器
- [ ] 界面个性化
- [ ] 其他：___________

### 3. 同意管理平台（CMP）

- [ ] 无
- [ ] Axeptio
- [ ] Didomi
- [ ] Cookiebot
- [ ] OneTrust
- [ ] 其他：___________

### 4. 保存期限

> **阅读 CNIL 来源**：`assets/CNIL_recommandation_cookies_et_traceurs.pdf` + https://www.cnil.fr/fr/cookies-et-autres-traceurs/regles/cookies
> **重要**：CNIL 建议同意 Cookie 为 **6 个月**。默认使用 6 个月。

| Cookie | CNIL 建议期限 | 最长期限 |
|--------|---------------------------|------------------|
| 同意 Cookie | 6 个月 | 13 个月 |
| 分析 Cookie | 视目的而定 | 13 个月 |
| 广告 Cookie | 视目的而定 | 13 个月 |

---

## 起草工作流

### 步骤 1：选择模板（强制）

> **绝不从零起草政策。**
> 起草必须始终基于给定模板，即：
> - `assets/sample_template_politique_cookies.docx` 中的默认模板；
> - 或用户提供的其他内部模板。
>
> 该模板是你的基准参考。你必须：
> - **忠实复现模板的结构和措辞**
> - **保留模板的精确表述**（它们经过验证）
> - **仅将占位符替换为**客户信息
> - **不要重写句子**，即使你认为自己可以表达得更好
> - **不要添加**模板中没有的章节
>
> 收集的信息（使用的 Cookie、CMP 等）用于**填充**模板，**而非重写**模板。

**1. 首要行动：在任何起草之前确认要使用的模板。询问用户：**
```
“我将基于提供的默认模板起草 Cookie 政策。您是否有更适合作起点的内部模板？”
```

| 选项 | 行动 |
|--------|--------|
| 默认模板 | 使用 `assets/sample_template_politique_cookies.docx` |
| 内部模板 | 使用律师提供的文档 |

**2. 考虑用户的选择并选定起始模板。**

---

### 步骤 2：了解网站和使用的 Cookie

> **主要目标**：精确识别网站放置的所有 Cookie。

**1. 向律师索取其掌握的信息：**
```
“为起草一份完美适配的 Cookie 政策，请提供：
- 网站 URL
- 使用的 Cookie 列表（如已知）
- 使用的同意管理平台（CMP）
- 集成的第三方工具（分析、广告、社交媒体等）
- 网站 Cookie 的任何现有文档

如需保密，您可以将这些信息匿名化。

您提供的信息越多，政策就越适配。否则，我们将自行研究，但研究将仅限于公开可获取的信息。”
```

**2. 对网站进行研究（如可访问）：**
- 访问网站并观察 Cookie 横幅
- 识别使用的 CMP
- 列出可见的 Cookie（经浏览器工具）
- 记录第三方集成（YouTube、社交媒体、分析等）
- 阅读现有 Cookie 政策（如有）

**3. 起草前的综合：**
```
网站：[URL]
使用的 CMP：[解决方案名称]
严格必要 Cookie：[列表]
分析 Cookie：[列表 + 供应商]
广告 Cookie：[列表 + 供应商]
社交媒体 Cookie：[列表 + 供应商]
功能 Cookie：[列表]
保存期限：[符合 13 个月上限？]
律师关键要点：[必须包含的内容]
```

> 综合完成后 → 进入草稿 1。

---

### 步骤 3：草稿 1

> **绝对规则**：参考模板是经过验证的基础。
>
> - **从模板出发**：结构、措辞、语气 → 这是你的参考
> - **适配客户案例**：纳入识别到的具体 Cookie
> - **不要全盘重写**：保留模板措辞，仅适配需要适配之处
>
> 总结：模板 + 客户 Cookie = 草稿 1。而非完整重写。

逐节填写模板：

1. **什么是 Cookie？**（定义）
2. **谁放置 Cookie？**（发布者 + 第三方）
3. **严格必要 Cookie**（详细表格）
4. **分析 Cookie**（表格 + 目的）
5. **广告 Cookie**（表格 + 目的）
6. **社交媒体 Cookie**（表格 + 目的）
7. **如何管理您的偏好？**（横幅 + 浏览器）
8. **保存期限**
9. **政策更新**
10. **联系方式**

> **即时合规检查：** 在呈现草稿 1 之前，核验 Cookie 合规清单（CNIL 2020）：
> - [ ] 含名称、供应商、期限、目的的穷尽式 Cookie 列表
> - [ ] 区分必要 Cookie 与需同意的 Cookie
> - [ ] 告知拒绝与接受同样简单
> - [ ] 保存期限 ≤ 13 个月
> - [ ] 清晰解释横幅的运作方式
> - [ ] 经浏览器管理 Cookie 的说明
> - [ ] 修改偏好的 CMP 链接
> - [ ] 文档更新日期
> - [ ] 问题联系方式
>
> 若草稿 1 合规 → 进入步骤 3。

---

### 步骤 4：交付草稿 1 + 基准比较 + 改进建议

**1. 交付草稿 1 并附说明：**
```
“这是 Cookie 政策的草稿 1。

**我考虑的内容：**
- [识别到的 Cookie 列表]
- [使用的 CMP]
- [保存期限]

**合规性：** 该文档符合 CNIL 2020 指南。”
```

**2. 呈现基准比较（系统性）：**

研究同一行业 3-5 家公司的 Cookie 政策，然后呈现：
```
“**已完成的基准比较：**

我分析了以下公司的 Cookie 政策：
- [公司 1] - [我们注意到的内容]
- [公司 2] - [我们注意到的内容]
- [公司 3] - [我们注意到的内容]

**识别到的可能改进：**
- [改进 1]：[说明]
- [改进 2]：[说明]

您是否希望将这些要素纳入所提供草稿？”
```

**3. 若律师批准改进 → 产出草稿 2**

---

### 步骤 5：最终核验

最终交付前的最后一次审阅：

- [ ] 网站所有 Cookie 均已列出
- [ ] 必要 / 需同意 Cookie 的区分得到遵守
- [ ] 保存期限 ≤ 13 个月
- [ ] 清晰的管理说明（横幅 + 浏览器）
- [ ] 最终文档中无内部引用
- [ ] 更新日期存在

---

## CNIL 参考处罚

| 公司 | 金额 | 理由 |
|---------|--------|--------|
| Google | €150M | 拒绝 Cookie 比接受更困难 |
| Facebook | €60M | 无可见的“全部拒绝”按钮 |
| Amazon | €35M | 未经事先同意放置 Cookie |
| Microsoft | €60M | 未经同意放置 Cookie |

> 这些处罚说明合规 Cookie 政策与遵守“拒绝必须与接受同样简单”原则的横幅的重要性。

---

## 应避免的常见错误

| 错误 | 可能的处罚 | 解决方案 |
|---------|-------------------|----------|
| 同意前放置 Cookie | 罚款 | 等待“接受”点击 |
| 无可见“拒绝”按钮 | 罚款 | 按钮与“接受”同级 |
| 严格 Cookie 墙 | 罚款 | 提供替代方案 |
| 期限 > 13 个月 | 正式催告 | 遵守最长期限 |
| 无 Cookie 列表 | 不合规 | 详细表格为强制 |
| 暗黑模式（Dark patterns） | 罚款 | 中立清晰的设计 |
| Cookie 列表不完整 | 不合规 | 完整网站审计 |

---

## 使用本指南

1. **步骤 1 - 选择模板**：默认参考模板，或律师的内部模板
2. **步骤 2 - 识别 Cookie**：收集律师信息 + 网站分析
3. **步骤 3 - 起草草稿 1**：填写模板 + 合规检查
4. **步骤 4 - 交付 + 基准比较**：呈现草稿 1 + 系统性基准比较 + 改进建议
5. **步骤 5 - 定稿**：纳入批准的改进 + 最终核验

> **模板提醒**：绝不从零起草。始终基于参考模板并适配。
> **期限提醒**：CNIL 建议同意 Cookie 为 **6 个月**（最长 13 个月）。提及期限前，始终在 CNIL 来源中核验。
