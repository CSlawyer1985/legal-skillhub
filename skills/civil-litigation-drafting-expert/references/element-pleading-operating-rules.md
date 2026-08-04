# 要素式诉辩运行规则

## 1. 数据层级

1. `element-pleading-knowledge.json`：11类纠纷的全局知识、证据、审查和风险。
2. `element-pleading-claim-matrix.json`：63个逐诉请模块，包含要件、阻断事实、证据组、答辩路径、法院审查、计算和救济冲突。
3. `legal-source-index.json`：现行法律来源和版本路由；正式提交时仍按案件时点复核条号。

## 2. 起诉端

1. 识别纠纷并选择具体诉请，不默认勾选全部诉请。
2. 对每项诉请依次检查要件、阻断事实和证据组。
3. 存在“待核实”“不知道”或缺失阻断事实时，只能输出待补正草稿。
4. 同时选择继续履行与解除、经济补偿与违法解除赔偿金、全部租金与解除返还等冲突救济时，改为主位／备位或要求当事人选择。
5. 金额请求必须展示基数、标准、期间、抵扣和合计。

## 3. 答辩端

每项原告诉请均使用下列回应状态之一：

- `admit`：承认请求基础事实和法律后果。
- `deny`：否认并说明否认的要件、事实、证据或法律理由。
- `partial`：明确承认范围、否认范围和可复算金额。
- `unknown`：说明因何无法确认，以及需要对方举证或法院调查的事项。

答辩不得只写“原告诉请无事实和法律依据”。应优先审查：

1. 请求权要件欠缺。
2. 权利消灭、阻却或延期事实。
3. 原告证据真实性、合法性、关联性和证明力。
4. 计算基数、期间、抵扣和重复受偿。
5. 管辖、主体、前置程序、时效或期间。
6. 抵销、反诉、追加主体和调查取证需要。

## 4. 命令

```bash
python3 scripts/element_pleading_tool.py list
python3 scripts/element_pleading_tool.py intake \
  --dispute 民间借贷 --role plaintiff --claim 偿还本金
python3 scripts/element_pleading_tool.py intake \
  --dispute 劳动争议 --role defendant --claim 加班费
python3 scripts/element_pleading_tool.py example \
  --dispute 买卖合同 --role plaintiff
python3 scripts/element_pleading_tool.py audit \
  --case-json /absolute/path/to/case.json
```

## 5. 输出状态

- `blocked`：存在阻断事实、救济冲突或答辩未回应，不得生成可提交候选。
- `needs_evidence`：事实结构已齐，但证据组存在缺口；输出补证方案。
- `structure_ready`：请求结构、事实答案和证据组齐备；继续进行现行法条、管辖、期限、法院格式和真实性复核。

`structure_ready`不等于法律和事实已经最终成立，也不代替律师审阅。
