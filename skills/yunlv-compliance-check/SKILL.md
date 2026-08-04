---
name: yunlv-compliance-check
description: >-
  Use when user needs to check import/export compliance requirements for specific products and countries.
  Use when verifying product certifications, tariffs, sanctions, or regulatory requirements.
  Use when screening business partners against trade sanctions or embargo lists.
  Use when user mentions "合规检查", "进出口合规", "产品认证", "关税", "制裁名单", "禁运", "清关", "认证要求", "compliance", "import regulations".
homepage: https://yunlvai.com
license: MIT-0
version: 1.0.3
progressive:
  layers:
    - name: metadata
      tokens: 200
      loaded: startup
      description: "技能基础配置、支持的法规体系、定价信息"
    - name: instructions
      tokens: 4500
      loaded: trigger
      description: "进出口合规检查全流程、产品认证、关税、制裁筛查、预警"
    - name: resources
      tokens: variable
      loaded: on-demand
      description: "认证要求清单、制裁名单参考、合规报告模板"
  resource_paths:
    - references/certification_requirements.md
    - references/sanctions_screening.md
    - references/compliance_report_template.md
metadata:
  yunlv:
    homepage: https://yunlvai.com
    primaryEnv: TRADEGPT_API_KEY
    category: compliance-risk
    subCategory: import-export-compliance
    tags: ["进出口合规", "产品认证", "关税", "制裁名单", "禁运", "清关", "认证要求", "合规检查", "出口管制", "进口许可"]
    requires:
      env:
        - TRADEGPT_API_KEY
    apis:
      - name: 云旅AI TradeGPT API
        url: https://api.yunlvai.com
        purpose: "合规要求查询和风险评估"
        auth: Bearer Token (TRADEGPT_API_KEY)
    emoji: "🛡️"
    author: "云旅AI团队"
    pricing:
      free:
        features: ["每次3项合规检查", "基础认证清单", "通用关税查询"]
      basic:
        price: 399
        currency: CNY
        period: month
        features: ["无限合规检查", "完整认证要求", "制裁名单筛查", "合规报告生成"]
      pro:
        price: 999
        currency: CNY
        period: month
        features: ["实时法规更新", "客户背调筛查", "合同合规审核", "专家咨询通道"]
triggers:
  - "合规检查"
  - "进出口合规"
  - "产品认证"
  - "关税查询"
  - "制裁名单"
  - "清关"
  - "认证要求"
  - "出口管制"
  - "进口许可"
  - "compliance"
  - "禁运"
  - "HS编码"
---

# 进出口合规检查：AI驱动的贸易合规风险管控

> 外贸合规无小事。一次关税误判可能导致巨额罚款，一次制裁名单漏筛可能让整个交易血本无归。云旅AI进出口合规检查技能，帮助外贸企业在签约前、发货前、付款前全面筛查合规风险，将"被动踩坑"变为"主动避险"。

---

## 一、技能定位

**解决什么问题**：进出口合规要求太多，不知道产品出口某国需要哪些认证？不知道客户是否在制裁名单里？

**核心价值**：将合规风险从"事后发现"变为"事前预防"，一次重大合规事故的损失足够支付 **10年** 的合规服务费用。

---

## 二、能做什么

### 【核心功能】

| 功能 | 说明 |
|------|------|
| 关税税率查询 | 220+国家HS编码关税税率查询，含MFN/特惠税率 |
| 产品认证要求 | CE/FCC/RoHS/UL/INMETRO等目标市场认证清单 |
| 进口许可证筛查 | 特定产品/国家的进口许可要求 |
| 制裁名单筛查 | OFAC/欧盟/联合国等制裁名单企业筛查 |
| 出口管制筛查 | 美国EAR/欧盟dual-use管制清单筛查 |
| 禁运国家判断 | 判断目标国家是否在禁运清单 |
| 合规风险评估 | 综合以上因素，给出1-5级风险评分 |
| 合规建议清单 | 给出需要完成的认证、文件或许可清单 |

### 【支持的合规体系】

| 体系 | 覆盖内容 |
|------|----------|
| 美国 | FCC/UL/ETL、CBP关税税率、OFAC制裁、EAR出口管制 |
| 欧盟 | CE/REACH/RoHS、EU-TIR/customs tariff、CFAC制裁 |
| 中国 | CIQ检验、CCC认证、出口管制两用物项 |
| 中东 | SASO认证（沙特）、SQP（阿联酋）、伊朗禁运 |
| 拉美 | INMETRO（巴西）、COFETEL（墨西哥）、阿根廷CIV |
| 东南亚 | SIRIM（马来西亚）、SNI（印尼）、泰国TISI |

---

## 三、操作步骤

### 第1步：输入合规检查需求

**方式A - 产品出口合规检查（最常用）**
```
产品名称：Industrial PLC Controller
HS编码：8537.10
目标国家：Russia
出口国：中国
客户公司：RobotTech LLC
用途：工业自动化
```

**方式B - 客户背调合规筛查**
```
筛查对象：
- 公司名称：RobotTech LLC
- 注册地：Russia (Moscow)
- 法定代表人：Ivan Petrov
- 关联公司：RobotTech Asia Ltd (HK)

筛查目的：
- 是否在OFAC制裁名单
- 是否在欧盟出口管制清单
- 是否有高风险信号
```

**方式C - 综合合规评估**
```
产品：Lithium Battery Pack (100Wh)
HS编码：8507.60
目的地：Germany
客户公司：GreenTech GmbH
订单金额：$500,000
付款方式：30% T/T + 70% L/C at sight
```

### 第2步：AI多维度合规筛查

系统辅助执行：
1. **关税税率查询**：查询目标国HS编码税率，识别是否有特惠税率
2. **产品认证确认**：确认目标市场所需认证及豁免条件
3. **制裁名单筛查**：对客户公司/法定代表人/关联公司进行OFAC/欧盟/联合国筛查
4. **出口管制筛查**：核查是否涉及美国EAR/欧盟dual-use管制
5. **禁运判断**：判断目的地是否为禁运国家
6. **付款风险**：评估付款方式合规性（LC/T/T及银行合规要求）
7. **综合评分**：整合以上维度输出风险等级和处置建议

### 第3步：输出合规风险报告

```json
{
  "report_type": "export_compliance_check",
  "timestamp": "2025-04-25",
  "product": "Industrial PLC Controller",
  "hs_code": "8537.10",
  "destination": "Russia",
  "customer": "RobotTech LLC",
  "risk_level": 4,
  "risk_label": "高风险 - 需要特批",
  "risk_breakdown": [
    {
      "dimension": "制裁名单",
      "result": "PASS",
      "details": "RobotTech LLC不在OFAC/欧盟/联合国制裁名单"
    },
    {
      "dimension": "出口管制",
      "result": "REVIEW_REQUIRED",
      "details": "PLC控制器可能涉及EAR 3A001/3A002类别，需要查证是否低于ECCN阈值"
    },
    {
      "dimension": "禁运国家",
      "result": "WARNING",
      "details": "俄罗斯目前受欧盟/美国广泛制裁，虽然不是全面禁运，但交易需格外谨慎"
    },
    {
      "dimension": "关税税率",
      "result": "INFO",
      "details": "俄罗斯MFN税率5%，但受制裁影响，实际清关可能面临额外审查"
    },
    {
      "dimension": "付款方式",
      "result": "REVIEW_REQUIRED",
      "details": "大额T/T付款可能触发银行合规审查，建议使用信用证"
    }
  ],
  "required_actions": [
    {
      "action": "查证ECCN分类",
      "priority": "HIGH",
      "deadline": "签约前",
      "owner": "合规专员"
    },
    {
      "action": "完成最终用户声明（End-User Certificate）",
      "priority": "HIGH",
      "deadline": "发货前",
      "owner": "销售"
    },
    {
      "action": "获取中国商务部出口许可（如涉及管制物项）",
      "priority": "MEDIUM",
      "deadline": "签约后3天内",
      "owner": "合规专员"
    }
  ],
  "recommendation": "⚠️ 建议暂缓签约，待ECCN分类确认。如确需出口，建议：(1)获取商务部出口许可 (2)使用信用证付款 (3)全程留存完整文件"
}
```

---

## 四、适用场景

| 场景 | 使用方式 |
|------|----------|
| 新客户首次合作 | 签约前做完整合规筛查，规避高风险客户 |
| 新产品出口新市场 | 查询目标市场的认证要求和关税税率 |
| 订单金额较大 | 深度合规审查，避免巨额损失 |
| 涉及制裁国家 | 严查制裁名单和出口管制清单 |
| 展会后快速评估 | 展会上遇到高风险国家客户，快速评估是否继续跟进 |
| 年度合规审计 | 梳理现有客户合规状态，清理高风险账户 |

---

## 五、资源索引

- **产品认证要求清单**: 见 `references/certification_requirements.md`（何时读取：查询特定产品/国家的认证要求时）
- **制裁名单筛查指南**: 见 `references/sanctions_screening.md`（何时读取：理解制裁名单筛查逻辑时）
- **合规报告模板**: 见 `references/compliance_report_template.md`（何时读取：生成标准格式合规报告时）

---

## 六、注意事项

### ⚠️ 重要声明
- **合规建议仅供参考**：云旅AI合规检查是辅助工具，不能替代专业法律意见
- **法规实时更新**：制裁名单和关税税率随时变化，检查结果有时效性
- **最终责任在企业**：企业须对自身合规行为承担完全法律责任

### ⚠️ 高风险国家
- 俄罗斯、伊朗、朝鲜、叙利亚、苏丹等高风险国家需格外谨慎
- 即使未被全面禁运，出口也可能触发二级制裁风险

### ⚠️ 制裁名单更新
- OFAC制裁名单每日更新，重要交易需在签约/发货/付款三个节点分别筛查

---

## 七、使用示例

### 示例 1：机械产品出口德国
**用户需求**：我们出口一批机械设备到德国，客户要求CE认证和REACH合规证明，我需要知道完整要求清单

**执行结果**：
- 完整认证要求：CE（强制性）、REACH（化学品合规）、RoHS（电子部件）
- 关税税率：MFN税率4.2%，中欧地理标志产品可能享受0税率
- 清关文件清单：CE符合性声明、装箱单、商业发票、原产地证
- 合规风险：低风险，正常出口流程

### 示例 2：新客户OFAC制裁筛查
**用户需求**：迪拜新客户Al-Rashid Trading LLC，帮我筛查是否在制裁名单

**执行结果**：
- OFAC筛查：未命中
- EU制裁筛查：未命中
- 联合国制裁：未命中
- 风险评级：低风险（1级）
- 建议：可正常开展业务，但仍建议完成KYC尽调

---

## 八、Common Rationalizations

| Rationalization | Reality |
|----------------|---------|
| "大客户不会有问题" | 大客户同样可能在制裁名单，且一旦出事损失更大 |
| "查过一次就够了" | 制裁名单实时更新，需在签约/发货/付款前分别筛查 |
| "AI筛查就够用了" | AI筛查是辅助，必须结合专业法律意见处理高风险交易 |
| "出口管制只关美国的事" | 欧盟、中国等都有各自的出口管制法规 |

---

## 九、Verification

完成合规检查流程后：
- [ ] 确认HS编码准确（错误HS编码导致整个检查无效）
- [ ] 制裁名单筛查包含公司+法定代表人+关联公司
- [ ] 高风险项已标记（3级以上风险项必须人工复核）
- [ ] 建议清单具体可执行（不含模糊建议）
- [ ] 报告包含明确的时效性声明
- [ ] 高风险客户已建议寻求专业法律意见

---

## 十、Security & Privacy

### 存储根路径
```
./data/yunlv-skills/complianceCheck/
├── screening/          # 筛查记录
├── reports/            # 合规报告
├── alerts/             # 预警记录
└── logs/               # 运行日志
```

### 数据处理原则
- **筛查数据保密**：被筛查客户信息严格保密，仅用户可查看
- **数据最小化**：筛查结果仅保留必要记录，12个月后自动归档
- **独立性**：合规筛查不受商业利益影响，AI给出客观判断

### 权限边界声明
- ✅ **允许**：读取 `./skills/yunlv-skills/references/` 下的参考文件
- ✅ **允许**：调用云旅AI合规数据API进行筛查
- ✅ **允许**：写入 `./data/yunlv-skills/complianceCheck/` 报告记录
- ❌ **禁止**：将筛查结果用于非授权目的（如销售给第三方）
- ❌ **禁止**：将AI筛查结果作为法律依据（仅供参考，须结合专业意见）

---

## ⚠️ 不要在以下情况使用

- 需要法律专业意见时（请咨询律师）
- 涉及特殊行业监管时（请咨询行业专家）

---

## 交付标准

- 方案结构完整，覆盖所有章节
- 建议具体可执行，不含模糊表述
- 内容适配用户提供的行业和场景
- 输出格式清晰，便于直接使用

---

## 相关技能推荐

- **yunlv-customs-scout** — 海关情报，识别高风险交易方
- **yunlv-contract-draft** — 合同起草，确保条款合规
- **yunlv-pricing** — 定价策略，综合合规风险调整价格策略
