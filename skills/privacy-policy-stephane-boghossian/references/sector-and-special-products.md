# 已核实参考资料包——行业叠加、安全／违规与特殊产品类型

> **零幻觉规则：** 只引用本资料包或实时查询的内容。下文若干条目为“片段核实”（主站阻止了自动抓取，但其文本由搜索返回）或标记为未核实——均已标注。未经确认，不得引用法定损害赔偿数字。对**所有**行业叠加，skill 都应标记需要专家／律师——不要泛泛起草这些通知。最后核实于 2026 年 6 月。

---

## 1. 安全与违规（该说什么＋其背后的义务）

### GDPR
- **第 32 条（处理安全）：** 实施与风险相适应的“适当的技术和组织措施”——示例措施：假名化／加密；保密性、完整性、可用性、韧性；事件后恢复能力；定期测试／评估。
  https://gdpr-info.eu/art-32-gdpr/
- **第 33 条（通知监管机构）：** 知悉后“无不当迟延，可行时**不迟于 72 小时**”，除非不太可能对个人权利构成风险。处理者无不当迟延地通知其控制者。https://gdpr-info.eu/art-33-gdpr/
- **第 34 条（通知个人）：** 违规很可能导致**高风险**时，以平实语言无不当迟延地通知受影响个人——如数据已加密／不可理解、风险已缓解，或需要不成比例的努力（则改为公开告知），则不要求。https://gdpr-info.eu/art-34-gdpr/

### 美国
- **全部 50 个州＋哥伦比亚特区／领地**都有违规通知法律；**无一般联邦法律**。主导性时限标准是**“无不合理迟延”**；一些州设有硬上限（常被引用的为 30／45／60 天——陈述具体数字前须核实各州具体法规；各州天数在此**未核实**）。加密数据豁免很常见。https://www.ncsl.org/technology-and-communication/security-breach-notification-laws

### 建议的安全条款措辞（真实、非绝对）
- “我们实施旨在保护您个人信息的合理行政、技术和物理保障措施。”仅在实际属实时才引用具体控制措施（传输中／静态加密、访问控制）——虚假安全主张属于 FTC 认定的欺骗行为。
- 始终包含缓饰：“没有任何传输或存储方法 100% 安全；我们无法保证绝对安全。”**禁用**“军事级”“银行级”“完全安全”“保证”。
- 违规响应行：“我们将按适用法律要求通知您和／或监管机构。”

---

## 2. 儿童产品
- **COPPA**（16 CFR 第 312 部分）：面向 13 岁以下受众需要在线通知＋**直接家长通知**＋**收集前的可验证家长同意**、数据最小化、保留限制、家长查阅／删除。2025 年修订（合规期限 **2026 年 4 月 22 日**）：生物识别和政府 ID 现属个人信息；**向第三方披露需单独同意**；**不得无限期保留**；新的 VPC 方法。
  https://www.ecfr.gov/current/title-16/chapter-I/subchapter-C/part-312
- **GDPR 第 8 条：** 数字同意年龄默认 **16 岁**，成员国可降至 **13 岁**；低于门槛需家长授权。https://gdpr-info.eu/art-8-gdpr/
- **英国适龄设计规范（“儿童规范”）：** 适用于在英国**可能被 18 岁以下者访问**的任何在线服务；15 项标准，包括默认高隐私、默认关闭地理位置和画像、无暗黑模式、适龄通知。
  https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/childrens-information/childrens-code-guidance-and-resources/

> 任何儿童产品 → **“发布前须咨询律师”硬性标记。**

---

## 3. 健康／保健
- **HIPAA 仅适用于受保实体／业务伙伴**——多数直接面向消费者的健康／健身应用**不受 HIPAA 约束**。如受约束：需要单独的**《隐私实践通知》**（网站隐私政策 ≠ HIPAA NPP）。
- **FTC《健康违规通知规则》（HBNR，16 CFR 第 318 部分）**填补非 HIPAA 缺口：个人健康记录／健康应用的供应商必须在 **60 个日历日内**通知受影响个人和 FTC 关于**未加密**可识别健康数据的违规（500 人以上→10 个工作日内通知 FTC；同一地区 500 人以上→通知显著媒体）。2024 年修订确认健康应用／互联设备在范围内。https://www.ftc.gov/business-guidance/resources/complying-ftcs-health-breach-notification-rule-0
- **华盛顿州《我的健康我的数据法》（MHMDA，RCW 19.373）：** 保护 HIPAA 之外的消费者健康数据；收集须**选择加入同意**、共享须**单独同意**、出售须签署**授权书**；要求**独立的《消费者健康数据隐私政策》**（单独文件、首页链接、仅含该法要求的内容、指明特定关联公司）。https://app.leg.wa.gov/RCW/default.aspx?cite=19.373&full=true

> 健康／PHI → **硬性律师标记**；如同时涉及生物识别／基因，见 §5。

---

## 4. 金融科技
- **GLBA《金融隐私规则》：** “金融机构”必须在关系开始时＋**每年**提供清晰的书面临私通知，说明共享情况，并在与某些非关联第三方共享 NPI 前提供**选择退出**；《保障规则》强制制定书面信息安全计划。
  https://www.ftc.gov/business-guidance/privacy-security/gramm-leach-bliley-act
- **PCI-DSS** 是**合同性**的（卡组织），不是法律，本身也不是隐私政策披露——但常被引用。（该定性属一般知识——依赖前请确认。）

> 超出标准处理商的金融科技／支付 → **硬性律师标记。**

---

## 5. 生物识别
- **伊利诺伊州 BIPA**（740 ILCS 14）：要求**公开可得的书面政策**，含**保留期限表＋销毁指引**（目的达成时或**最后一次互动后 3 年内**销毁，以先到者为准）；收集前书面通知＋**书面同意**；限制披露／出售。**私人诉权**附法定损害赔偿——这是主要诉讼驱动力（**不要**引用具体损害赔偿数字）。https://www.ilga.gov/Legislation/ILCS/Articles?ActID=3004&ChapterID=57
- **得克萨斯州 CUBI**（Bus. & Com. §503.001）：**采集前**告知并同意（同意无需书面）；目的终止后约 1 年内销毁；**无私人诉权**（得州总检察长执法；民事罚款最高每起违规 2.5 万美元）。https://statutes.capitol.texas.gov/Docs/BC/htm/BC.503.htm
- **华盛顿州**（RCW 19.375）：为商业目的登记生物识别标识符前须通知／同意（本轮具体细节**未核实**）。

> 生物识别数据 → **硬性律师标记**（尤其是伊利诺伊／得克萨斯／华盛顿）。

---

## 6. 浏览器扩展
- **Chrome 网上应用店开发者计划（隐私＋有限使用）：** 任何处理用户数据的扩展都需要准确、最新的隐私政策，披露收集／使用／共享情况及**所有当事方**；**有限使用**政策将数据限制于已披露的实践；**禁止收集网页浏览活动**，除非是突出描述的用户功能所必需；需要关于 Google API 数据的肯定性合规声明。https://developer.chrome.com/docs/webstore/program-policies/limited-use

---

## 7. 物联网／互联设备
- **加利福尼亚州 SB-327**（《民法典》§§1798.91.04-.06）：互联设备制造商必须包含**合理安全功能**（例如每设备唯一密码或首次使用时强制改密）。这是对制造商的**安全**要求，而非隐私披露规则；无私人诉权。https://leginfo.legislature.ca.gov/faces/billTextClient.xhtml?bill_id=201720180SB327
- 物联网数据最小化是 GDPR 最佳实践（第 5(1)(c) 条），不是 SB-327 要求。联邦《2020 年物联网网络安全改进法》仅涉及联邦采购（本轮**未核实**）。

---

## 8. 基于位置的服务
- **CCPA／CPRA：** **精确地理位置**（约 1,850 英尺内）属**敏感个人信息** → 消费者可以**限制**其使用；披露收集、目的、敏感处理和“限制使用我的敏感个人信息”选择退出。在 GDPR 下，与个人关联的精确位置是个人数据，通常需要同意。https://oag.ca.gov/privacy/ccpa

---

## 9. 教育科技
- **FERPA** 管辖接受联邦资金的学校／机构；对机构执行（教育部）。
- **加利福尼亚州 SOPIPA：** K-12 在线运营者直接责任——**不得向学生投放定向广告、不得出售学生数据、不得进行非教育性画像**；合理安全；**应学校请求删除**。
  https://iapp.org/news/a/state-student-privacy-laws-a-game-changer-for-service-providers
- COPPA 也适用于面向 13 岁以下者的教育科技（学校可在教育情境中提供同意——本轮具体细节**未核实**）。

> 面向未成年人的教育科技 → **硬性律师标记**（FERPA＋SOPIPA＋COPPA 叠加）。

### 一手来源（已核实／片段核实）
- GDPR 第 32／33／34／8 条：https://gdpr-info.eu/
- NCSL 美国违规法律：https://www.ncsl.org/technology-and-communication/security-breach-notification-laws
- COPPA：https://www.ecfr.gov/current/title-16/chapter-I/subchapter-C/part-312
- FTC HBNR：https://www.ftc.gov/business-guidance/resources/complying-ftcs-health-breach-notification-rule-0
- 华盛顿州 MHMDA：https://app.leg.wa.gov/RCW/default.aspx?cite=19.373&full=true
- GLBA：https://www.ftc.gov/business-guidance/privacy-security/gramm-leach-bliley-act
- BIPA：https://www.ilga.gov/Legislation/ILCS/Articles?ActID=3004&ChapterID=57 · 得州 CUBI：https://statutes.capitol.texas.gov/Docs/BC/htm/BC.503.htm
- Chrome 网上应用店：https://developer.chrome.com/docs/webstore/program-policies/limited-use
- 加州 SB-327（物联网）：https://leginfo.legislature.ca.gov/faces/billTextClient.xhtml?bill_id=201720180SB327
- 英国儿童规范：https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/childrens-information/childrens-code-guidance-and-resources/
