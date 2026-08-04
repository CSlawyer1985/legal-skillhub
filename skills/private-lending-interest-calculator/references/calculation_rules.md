# 详细计算规则与算法说明

## 一、法律适用判定

```
if 借款日期 < "2015-09-01":
    适用规则 = "旧民间借贷意见（银行同期4倍）"
elif "2015-09-01" <= 借款日期 < "2020-08-20":
    适用规则 = "2015年《民间借贷规定》（24%/36%两线三区）"
elif "2020-08-20" <= 借款日期:
    适用规则 = "2020修订版（4倍LPR）"
```

## 二、LPR 查找算法

查找合同成立时对应的1年期LPR：
1. 在LPR数据表中，找到**报价日期 ≤ 合同成立日期**的最近一条记录
2. 取该记录的1年期LPR值
3. 利率上限 = LPR × 4

示例：合同成立于2024年6月15日，对应最近LPR报价日期为2024-05-20（3.45%），上限 = 3.45% × 4 = 13.80%

## 三、分段计算规则

### 强制分段点：2020-08-20

无论借贷是否跨期，只要计算区间跨越 2020-08-20，必须拆分为两段：

**前段（~2020-08-19）**：
- 适用利率 = min(约定利率, 24%)

**后段（2020-08-20~）**：
- 适用利率 = min(约定利率, 合同成立时LPR × 4)
- 注意：使用**合同成立时**的LPR，不是计算时的LPR

### 动态本金
- 后段计息本金 = 前段本金 - 前段已冲抵本金
- 每次还款后重新计算剩余本金

## 四、利息类型判定

### 1. 借期内利息

| 情形 | 处理方式 |
|------|---------|
| 有约定利率 | 按约定（不超上限） |
| 无约定利率 | 视为无息（《民法典》第680条） |
| 自然人间约定不明 | 视为无息 |
| 非自然人间约定不明 | 结合交易习惯、LPR等确定 |

### 2. 逾期利息

```
1. 约定逾期利率：min(约定逾期利率, 利率上限)
2. 仅约定借期内利率：min(借期内利率, 利率上限)
3. 均未约定：
   - 2020-08-20前：年利率 6%
   - 2020-08-20后：当时1年期LPR
```

### 3. 违约金 + 逾期利息合并审查

**双重上限控制**：
1. **利率上限**：逾期利率本身不得超过 LPR 四倍
2. **合并上限**：逾期利率 + 违约金 + 其他费用**总计不得超过** LPR 四倍

```python
# 伪代码
legal_cap = get_legal_cap(loan_date)

if has_agreed_overdue_rate:
    applicable_rate = min(agreed_overdue_rate, legal_cap)
else:
    applicable_rate = min(loan_rate, legal_cap) if has_loan_rate else LPR

total_charge_rate = applicable_rate + penalty_rate
if total_charge_rate > legal_cap:
    adjusted_penalty_rate = max(0, legal_cap - applicable_rate)
    warning = "违约金已调整至与逾期利率合计不超过法定上限"
```

## 五、还款冲抵算法

根据《民法典》第561条，按以下顺序冲抵：

```
1. 实现债权的有关费用
2. 利息（含逾期利息）
3. 本金
```

### 冲抵逻辑（伪代码）

```python
def apply_repayment(payment, principal, accrued_interest, fees):
    remaining = payment
    # 第一步：冲抵费用
    if remaining > fees:
        remaining -= fees
        fees = 0
    else:
        fees -= remaining
        return principal, accrued_interest, fees

    # 第二步：冲抵利息
    if remaining > accrued_interest:
        remaining -= accrued_interest
        accrued_interest = 0
    else:
        accrued_interest -= remaining
        return principal, accrued_interest, fees

    # 第三步：冲抵本金
    principal -= remaining
    return max(principal, 0), accrued_interest, fees
```

### 边界处理
- **利息不足**：还款 < 应付利息时，差额结转为下期"积欠利息"
- **本金清零**：剩余本金 ≤ 0 时，终止后续利息计算
- **超额识别**：自动检测已付利息中超过36%（旧规）或LPR四倍（新规）的部分

## 六、复利计算规则

### 合规条件
1. **前期利率限制**：计入本金的利息，其利率不得超过合同成立时LPR四倍
2. **本息和上限**：最终本息和不得超过 原始本金 + 原始本金 × LPR四倍 × 总期限
3. **跨期分段**：合同成立于2020-08-20前的，2020-08-19前按24%，之后按LPR四倍分段

### 计算逻辑

```python
def calculate_compound(principal, rate, start, end, loan_date):
    _, cap = determine_rule(loan_date)

    # 合规验证
    if rate > cap:
        return error("利率超过上限，复利被拒绝")

    # 限制滚利次数（通常限制为1次）
    current = principal
    interest = current * (min(rate, cap) / 100)
    current += interest

    # 检查本息和上限
    total_years = (end - start).days / 365.0
    max_allowed = principal * (1 + cap / 100 * total_years)
    if current > max_allowed:
        return error("突破法定本息和上限")

    return current
```

## 七、砍头息处理

- 本金按**实际到账金额**计算（《民间借贷规定》第27条）
- 合同载明金额与实际到账金额的差额为预扣利息
- 该预扣利息不得计入本金，也不得单独主张

## 八、特殊场景

### 职业放贷人
- 若出借人被认定为职业放贷人，借贷合同可能被认定无效
- 合同无效后，借款人仅需返还本金及按LPR计算的占用费
- 此场景需提示用户合同效力风险，但计算时仍按有效合同计算

### 展期
- 展期视为新的借款期间
- 展期利率约定与原约定不同时，分段计算
- 展期后的法律适用按原合同成立时间确定

### 部分还款
- 每笔还款按冲抵顺序处理后，以剩余本金为基数继续计息
- 计息天数精确到日

## 九、计算方式

### 按日计息（默认）
```
利息 = 本金 × (年利率 / 100) × 天数 / 365
```

### 按月计息
- 通常按30天/月或实际月天数
- 需用户明确约定

### 利随本清
- 到期一次性还本付息
- 按实际借款天数计算

### 等额本息/等额本金
- 按揭式还款计算
- 需用户明确约定
