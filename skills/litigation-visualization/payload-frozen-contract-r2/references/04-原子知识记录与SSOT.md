# 原子知识记录与 SSOT

## 原子化标准

一条 Atomic Knowledge Record（AKR）只表达：

- 一个可验证法律/事实命题；或
- 一个有明确触发条件和输出的实务动作。

若一句话包含多个独立条件、多个动作或不同法域规则，应拆分并用关系边连接。

## 必填语义

| 字段 | 用途 |
|---|---|
| `id` | 稳定、无个人信息的记录号 |
| `source_type` | case、statute、decision、book、course、interview、practice-note |
| `source_locator` | 可回溯但脱敏的相对定位 |
| `source_hash` | 来源版本指纹 |
| `cutoff` | 事实或知识截止点 |
| `claim` | 单一命题或动作 |
| `conditions` | 适用条件和排除条件 |
| `steps` | 可观察执行步骤 |
| `evidence` | 事实或方法的支持材料 |
| `legal_authority` | 法域、层级、有效性和核验日期 |
| `confidence` | 置信度及理由，不替代门禁 |
| `privacy_class` | private、restricted、internal、public |
| `rights_status` | 权利状态 |
| `failure_modes` | 反例、误用和升级点 |
| `status` | 候选生命周期状态 |
| `public_projection` | 可公开字段的允许清单 |

机器约束见 `templates/atomic-knowledge-record.schema.json`。

## SSOT 规则

1. AKR 集合是验证知识层的唯一事实源。
2. Skill、文书、图谱、FAQ 和 GEO 页面都由 AKR 派生。
3. 派生物发现错误时，先修改或新建 AKR，再重新生成下游产物。
4. 不覆盖已冻结记录；用 `supersedes` 建立版本关系。
5. 引用只指向固定版本与哈希，动态网页另记获取时间。

## 知识链接

允许的核心关系：

- `supports`：证据或规则支持命题；
- `contradicts`：来源或规则存在冲突；
- `requires`：动作执行需要前置记录；
- `precedes`：流程先后关系；
- `exception_to`：例外限制一般规则；
- `conflicts_with`：两个 Skill 的触发或动作冲突；
- `supersedes`：新版本替代旧版本；
- `public_projection_of`：公开记录来源于内部验证记录。

链接不能替代内容验证。图上可达不代表法律上成立。

## 版本与变更

任何影响法律结论、触发条件、输出契约或公开范围的变更都应：

1. 生成新版本或变更记录；
2. 重跑相关正例、反例和边界测试；
3. 更新法源核验日期；
4. 重新做隐私和 GEO 忠实度检查；
5. 重新冻结哈希。

