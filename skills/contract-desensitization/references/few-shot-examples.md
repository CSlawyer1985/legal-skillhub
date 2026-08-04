# 脱敏示例（Few-shot）

## 示例一：中文合同

**原文：**

> "甲方深圳市云图科技有限公司向乙方北京智算信息技术有限公司采购'城市交通管理系统'，合同金额人民币 200 万元，付款至乙方账户 6222 xxxx xxxx。"

**脱敏后：**

> "甲方某公司A向乙方某公司B采购某项目，合同金额【金额已脱敏】，付款至乙方账户【账户已脱敏】。"

---

## 示例二：中英对照涉外合同（双语同步脱敏）

**原文：**

中文：
> "甲方 Yuntu Technology Co., Ltd. 与乙方 ABC Inc. 就'智能识别系统'采购达成协议，合同金额 USD 500,000，付款至账户 IBAN: DE89..."

英文：
> "Party A Yuntu Technology Co., Ltd. and Party B ABC Inc. agree on the procurement of 'Intelligent Recognition System', with a contract value of USD 500,000, payable to IBAN: DE89..."

**脱敏后：**

中文：
> "甲方某公司A与乙方某公司B就某项目采购达成协议，合同金额【金额已脱敏】，付款至账户【账户已脱敏】。"

英文：
> "Party A Company A and Party B Company B agree on the procurement of the Project, with a contract value of [Amount Redacted], payable to [Account Redacted]."

**关键注意点：** 主体中英文成对替换、金额与账户双语脱敏，而 "agree on / procurement / payable to" 的法律句法结构完整保留。

---

## 示例三：完整采购合同脱敏前后对比

### 脱敏前（敏感信息摘要）

| 要素 | 原文 |
|------|------|
| 合同编号 | CG-2026-0388 |
| 甲方 | 深圳市云图科技有限公司，91440300MA5FL2X39K |
| 乙方 | 北京智算信息技术有限公司，91110108MA01YUW72T |
| 丙方（境外） | TechVision Solutions Inc.，EIN: 47-2938475 |
| 项目 | 城市交通管理系统V3.0 |
| 技术 | DeepTraffic Engine |
| 金额 | RMB 2,580,000 + USD 150,000 |
| 账户 | 6225 8878 1234 5678 / SWIFT: BOFAUS3N / IBAN: DE89... |
| 人员 | 王建国 135-2098-1122 / 刘晓东 186-0066-4455 / James Chen |
| License | TVS-2026-TRFC-8892-LOCK |

### 脱敏后

| 要素 | 脱敏值 |
|------|--------|
| 合同编号 | 【编号已脱敏】 |
| 甲方 | 某公司A |
| 乙方 | 某公司B |
| 丙方（境外） | 某公司C |
| 项目 | 某项目 |
| 技术 | 某技术 |
| 金额 | 【金额已脱敏】 |
| 账户 | 【账户已脱敏】 |
| 人员 | 某人甲/某人乙/某人丙 |
| License | 【授权码已脱敏】 |
