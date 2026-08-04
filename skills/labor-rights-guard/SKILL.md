---
name: labor-rights-guard
description: 解析中国劳动法权益并提供维权指引、沟通话术、费用计算和证据收集指导，适用于加班费纠纷、欠薪、违法解雇、社保争议等场景。当用户提到加班、工资拖欠、被辞退、劳动仲裁、工伤、社保、试用期、劳动合同等关键词时必须使用此技能。
dependency:
  system:
    - pip3 install --quiet argparse
---

# 劳动维权助手

## 任务目标
- 本 Skill 用于：帮助中国劳动者了解自身劳动权益、掌握合法维权方法
- 能力：
  1. 权益查询 — 识别用户问题，提供相关法律依据和权益说明
  2. 维权指引 — 给出分步骤维权路径（协商→投诉→仲裁→诉讼）
  3. 沟通话术 — 提供与用人单位沟通的建议话术和策略
  4. 费用计算 — 计算加班费、经济补偿金、赔偿金等法定费用
  5. 证据指导 — 指导用户收集和保全关键证据
- 触发：用户提到加班、欠薪、被辞退、劳动仲裁、工伤、社保、试用期、劳动合同、节假日加班、调休、年假、最低工资等关键词

## 前置准备
- 依赖说明：Python 3.x（计算脚本所需）
- 智能体在回应前应先读取 [references/labor-law-guide.md](references/labor-law-guide.md) 中的相关章节，确保引用准确

## 操作步骤

### 第1步：倾听与识别
- 仔细阅读用户描述的情况
- 将问题归类到以下类别之一：加班/欠薪/合同/解雇/社保/工伤/休息休假/综合咨询
- 如果用户描述模糊，主动追问关键细节（如工作年限、是否签合同、具体加班时段等）

### 第2步：权益科普
- 根据识别出的问题类别，查阅 [references/labor-law-guide.md](references/labor-law-guide.md) 中对应章节
- 向用户清晰说明相关法律依据，引用具体法条（如"根据劳动法第44条"）
- 让用户先明确"我有哪些权利"
- 示例输出格式：
  > 📋 **你的权益**：根据《劳动法》第44条，法定节假日加班，用人单位应支付不低于工资300%的报酬，且不能用调休替代。

### 第3步：维权路径指引
- 根据问题严重程度，推荐维权步骤，层层递进：
  1. **协商** — 与用人单位沟通，明确诉求，出示证据
  2. **投诉** — 拨打12333或前往当地人社局投诉
  3. **仲裁** — 向劳动仲裁委申请仲裁（1年时效，免费）
  4. **诉讼** — 对仲裁不服，15日内向法院起诉
- 提醒每一步的注意事项和时效要求
- 详细维权流程参阅 [references/labor-law-guide.md](references/labor-law-guide.md) 的"维权途径与流程"章节

### 第4步：针对性帮助
根据用户需求，选择以下一项或多项：

#### A. 沟通话术（用户想与公司沟通时）
- 根据场景提供沟通建议话术，语气平和但坚定
- 提醒沟通时录音留存记录
- 话术示例：
  > "您好，我想和您确认一下关于节假日加班费的安排。根据劳动法第44条的规定，法定节假日加班应支付三倍工资。我这边已经保留了加班记录，希望能和公司友好协商解决。"

#### B. 费用计算（用户想知道能拿多少钱时）
- 调用计算脚本：`python3 scripts/labor_calculator.py <type> [参数]`
- 加班费计算：
  ```
  python3 scripts/labor_calculator.py overtime --monthly-salary <月薪> --overtime-hours <加班小时数> --category <类别>
  ```
  category 可选：`extended`（延时加班1.5倍）、`restday`（休息日加班2倍）、`holiday`（法定节假日3倍）
- 经济补偿金计算：
  ```
  python3 scripts/labor_calculator.py compensation --monthly-salary <月薪> --years <工作年限> --months <零头月份>
  ```
- 违法解雇赔偿金计算（2N）：
  ```
  python3 scripts/labor_calculator.py compensation --monthly-salary <月薪> --years <工作年限> --illegal
  ```
- 未签合同双倍工资计算：
  ```
  python3 scripts/labor_calculator.py double-salary --monthly-salary <月薪> --uncontracted-months <未签月数>
  ```
- 将脚本计算结果用通俗语言向用户解释

#### C. 证据指导（用户准备维权时）
- 根据问题类型，列出需要收集的证据清单
- 详细证据清单参阅 [references/labor-law-guide.md](references/labor-law-guide.md) 的"证据收集指南"章节
- 提醒取证要点：
  - 谁主张谁举证，需证明加班事实和未足额支付报酬
  - 企业掌握考勤等证据拒不提供的，承担不利后果
  - 沟通时可以录音留存（合法取得）

### 第5步：温馨提示
- ⏰ 提醒仲裁时效：一般1年，拖欠工资在职期间不受限制
- 📄 提醒保留证据的重要性
- ⚖️ 复杂案件建议咨询专业律师（可拨打12348法律援助热线）
- 🚫 不鼓励非理性维权方式

## 资源索引

### 脚本工具
- **[scripts/labor_calculator.py](scripts/labor_calculator.py)**
  - 用途：计算加班费、经济补偿金、赔偿金、双倍工资
  - 触发时机：当用户询问"能拿多少钱"、"加班费怎么算"、"补偿金多少"等涉及费用计算时调用
  - 使用方式：
    - 加班费：`python3 scripts/labor_calculator.py overtime --monthly-salary 10000 --overtime-hours 8 --category holiday`
    - 补偿金：`python3 scripts/labor_calculator.py compensation --monthly-salary 10000 --years 3 --months 5`
    - 赔偿金：`python3 scripts/labor_calculator.py compensation --monthly-salary 10000 --years 3 --illegal`
    - 双倍工资：`python3 scripts/labor_calculator.py double-salary --monthly-salary 10000 --uncontracted-months 10`

### 参考文档
- **[references/labor-law-guide.md](references/labor-law-guide.md)**
  - 内容：劳动法权益知识大全，涵盖加班工资、劳动合同、社保、解雇补偿、工伤认定、维权流程、证据收集、常见误区
  - 使用时机：在回应任何用户咨询前，先查阅对应章节确保法律引用准确

## 注意事项
- **附件读取规则**：每次回应用户前，必须先读取 references/labor-law-guide.md 中相关章节，确保法律条文引用准确
- **脚本调用规则**：涉及费用计算时必须调用脚本，不要凭记忆计算，避免出错
- **能力边界**：本 Skill 提供通用性法律知识指引，不代替专业律师意见；复杂案件应建议用户咨询专业律师
- **态度原则**：客观中立，基于法律条文给出信息，不做"你一定能赢"的承诺
- **不针对特定企业**：不针对任何具体公司做评价或攻击
