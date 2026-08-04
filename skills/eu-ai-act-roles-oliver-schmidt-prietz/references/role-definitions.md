# 《人工智能法》角色定义——第3条第(3)-(7)款

## 提供者（Anbieter）——第3条第(3)款

**法律定义：**

> '提供者'指开发人工智能系统或通用人工智能模型，或委托他人开发人工智能系统或通用人工智能模型，并以自己的名义或商标将其投放市场或投入使用的人工智能系统的自然人或法人、公共机关、机构或其他主体，无论有偿还是无偿。

*德文：'Anbieter' bezeichnet eine natürliche oder juristische Person, Behörde, Einrichtung oder sonstige Stelle, die ein KI-System oder ein KI-Modell mit allgemeiner Zweckbestimmung entwickelt oder entwickeln lässt und es unter ihrem eigenen Namen oder ihrer eigenen Marke in Verkehr bringt oder das KI-System unter ihrem eigenen Namen oder ihrer eigenen Marke in Betrieb nimmt, sei es entgeltlich oder unentgeltlich.*

**关键要素：**
1. **开发或委托开发**——包括内部开发 AND 委托第三方开发
2. **投放市场 OR 投入使用**——要么使其可供使用（市场），要么首次真实世界使用（投入使用）
3. **以自己名义或商标**——关键的归属要素
4. **不要求有偿**——免费系统也算

**谁是提供者：**
- 构建并销售 AI 系统的公司
- 委托开发并以自有品牌营销的公司
- 发布 AI 系统的开源开发者（义务有限）
- 为内部使用开发 AI 并以自己名义投入使用的公司

**序言：** 83-85

---

## 部署者（Betreiber）——第3条第(4)款

**法律定义：**

> '部署者'指在其权限下使用人工智能系统的自然人或法人、公共机关、机构或其他主体，但在个人非专业活动中使用人工智能系统者除外。

*德文：'Betreiber' bezeichnet eine natürliche oder juristische Person, Behörde, Einrichtung oder sonstige Stelle, die ein KI-System in eigener Verantwortung verwendet, es sei denn, das KI-System wird im Rahmen einer persönlichen und nicht beruflichen Tätigkeit verwendet.*

**关键要素：**
1. **使用**——AI 系统的实际部署和运行
2. **在其权限下**——部署者对系统的使用方式拥有控制权
3. **专业语境**——排除纯个人/家庭使用
4. **不要求开发**——部署者通常从提供者处获得系统

**谁是部署者：**
- 从供应商处购买 AI 招聘工具并使用它的公司
- 部署医疗 AI 诊断工具的医院
- 使用第三方信用评分 AI 系统的银行
- 使用 AI 系统处理福利金的政府机关
- 使用 AI 监控员工的雇主

**序言：** 86-87

---

## 授权代表（Bevollmächtigter）——第3条第(5)款

**法律定义：**

> '授权代表'指位于或设立于欧盟的自然人或法人，其已收到并接受人工智能系统或通用人工智能模型的提供者的书面委托，代表提供者开展和履行本条例规定的义务和程序。

**关键要素：**
- 必须设立于欧盟
- 代表非欧盟提供者行事
- 要求书面委托
- 在欧盟内履行提供者义务

**何时需要：** 向欧盟市场投放 AI 系统的非欧盟提供者必须指定授权代表（第22条）。

---

## 进口商（Einführer）——第3条第(6)款

**法律定义：**

> '进口商'指位于或设立于欧盟、将带有第三国设立的自然人或法人名称或商标的人工智能系统投放市场的自然人或法人。

*德文：'Einführer' bezeichnet eine in der Union ansässige oder niedergelassene natürliche oder juristische Person, die ein KI-System in Verkehr bringt, das den Namen oder die Marke einer in einem Drittland niedergelassenen natürlichen oder juristischen Person trägt.*

**关键要素：**
1. **位于/设立于欧盟**——进口商必须在欧盟
2. **投放市场**——使系统在欧盟市场上可供使用
3. **带有第三国主体的名称**——系统带有原始（非欧盟）提供者的品牌
4. **不是开发者**——进口商未开发该系统

**谁是进口商：**
- 以美国公司品牌在欧洲分销美国制造的 AI 系统的欧盟公司
- 将中国 AI 硬件带入欧盟市场的欧盟分销商

**义务：** 第23条——进口商必须核实 CE 标志、文档和提供者合规性。

**序言：** 88

---

## 分销商（Händler）——第3条第(7)款

**法律定义：**

> '分销商'指供应链中除提供者或进口商之外的、在欧盟市场上提供人工智能系统的自然人或法人。

*德文：'Händler' bezeichnet eine natürliche oder juristische Person in der Lieferkette, die weder Anbieter noch Einführer ist und ein KI-System auf dem Unionsmarkt bereitstellt.*

**关键要素：**
1. **在供应链中**——提供者/进口商与部署者之间的中介
2. **不是提供者或进口商**——剩余类别
3. **在欧盟市场上提供**——供应、转售或分销

**谁是分销商：**
- 提供来自提供者的 AI 软件的 IT 转售商
- 托管第三方 AI 系统的技术市场平台
- 分销（但不修改）AI 系统的系统集成商

**义务：** 第24条——分销商必须核实符合性标志，且不得供应不合规系统。

**序言：** 89

---

## 角色确定逻辑

### 决策树

```
开始：评估组织与 AI 系统的关系

1. 组织是否开发了 AI 系统（或委托开发）？
   且是否以自己名义投放市场/投入使用？
   ├─ 是 → 提供者（第3条第(3)款）
   └─ 否 → 继续

2. 组织是否以专业身份在其权限下使用 AI 系统？
   ├─ 是 → 部署者（第3条第(4)款）
   │         （但检查第25条准提供者风险——第3阶段）
   └─ 否 → 继续

3. 组织是否从第三国进口 AI 系统
   以投放欧盟市场（带有第三国提供者的名称）？
   ├─ 是 → 进口商（第3条第(6)款）
   └─ 否 → 继续

4. 组织是否在欧盟市场上提供 AI 系统
   （不是作为提供者或进口商）？
   ├─ 是 → 分销商（第3条第(7)款）
   └─ 否 → 继续

5. 组织是否作为产品制造商将 AI 系统
   集成到其产品中？
   ├─ 是 → 产品制造商——见第25条第(3)款
   │         （可能被视为提供者）
   └─ 否 → 角色不明——寻求法律顾问
```

### 多重角色

组织可以同时是：
- 系统A的**提供者** AND 系统B的**部署者**
- **提供者**（自行开发系统）AND **部署者**（购买供应商系统）
- **分销商** AND **部署者**（既分销又使用该系统）
- **进口商** AND **部署者**（既进口又使用该系统）

每个角色都带有自己的义务集。按系统评估。

---

## 委员会价值链指南

委员会强调了价值链责任的以下原则：

1. **提供者承担高风险系统合规的首要责任**
2. **部署者必须确保在提供者的预期目的内正确使用**
3. **链条中的每个主体对其控制范围内的行为负责**
4. **第25条防止责任空白**——影响合规性的修改转移提供者义务
5. **合作义务**——所有主体必须与市场监督机关合作（第21条）
