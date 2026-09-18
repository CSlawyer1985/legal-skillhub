# 法律类质量门禁

门禁状态只有 `pass`、`warn`、`block`：

- `pass`：证据存在且满足要求；
- `warn`：可以继续，但必须在交接中展示风险；
- `block`：不得声称已经达到对应成熟度或可发布状态。

级别约定：以下各门禁项未单独标注级别的均为 `block`；标注 `（warn）` 的项未满足时记为警告，不阻断对应成熟度，但必须写入交接。

## 分层门禁

### 草案级（`scaffold`）

- `SKILL.md` frontmatter 准确，description 有触发与排除边界；
- 有 should-trigger、should-not-trigger、near-neighbor；
- 有输入、输出、权限和不做事项。
- 只要求法律元技能生成包具有 manifest 和三类触发用例；审计外部最小 Skill 时，可只确认官方 `SKILL.md` 结构，但必须警告其法律成熟度未知（warn）。
- 法律元技能生成包宜声明场景原型（`scenario_archetype`）或记录未选定理由（warn）。

### 专业复用级（`production`）

- `agents/interface.yaml` 与 `SKILL.md` 一致；
- 有触发评测与法律输出契约；
- 有至少一个脱敏/合成输出 case 或明确的 `missing evidence`；
- 根目录只有一个精确命名的 `SKILL.md`；
- 示例和测试入口不得精确命名为 `SKILL.md`，可使用 `SKILL.example.md` 或 `SKILL.fixture.md`；
- 新建 Skill 包含 `CSlawyer`、`https://chenshi.ai` 和 `legal-meta-skill` 来源标识；改造 Skill 保留原作者与许可证；
- 新建包声明标准许可证并保留对应 LICENSE/NOTICE；用户明确要求白标时，必须同时记录白标授权，不得仅删除署名文件绕过许可证条件；
- 可执行结构检查、触发检查和本地安装检查。
- 通用法律能力十二模块全部有状态；`active` 有最低输出，`not_applicable` 有任务特定理由，不得以空泛占位词替代适用性判断。
- 每个 `active` 模块必须使用固定中文标签、具体任务理由，并完整覆盖通用模型规定的最低输出字段；任意字段 `x` 或仅一个占位输出不得通过。
- `manifest.skill_contract` 的重复任务、决定、用户、输入、输出、排除、工作流、决策点和失败模式均为非空目标任务内容。
- 已按 [法律场景原型](legal-scenario-archetypes.md) 选定场景原型，并把对应检查清单写入目标包 `references/`；选择 `other` 时须在交接中说明任务特征与自行确定的专项检查。

### 基础设施级（`library`）

- 有 Skill IR、prior-art 取舍、信任边界和复核周期；
- Skill IR 采用 `legal-skill-ir/v0.3`，并至少有一个覆盖十二模块状态的脱敏或合成能力配置 case；
- 说明目标平台、降级路径、写文件和网络权限；
- 对包内法律规则、知识来源、现行法核验、证据转换和用户提供的项目约束有明确契约。
- 至少七个合成或脱敏输出用例；成熟度证据路径必须是包内安全相对路径、真实存在、内容非空且不含占位标记（JSON 证据须可解析）。
- 至少四个覆盖授权、法源/日期、文件证据和外部写入风险的 `blocked` 停机用例；每个受阻模块须记录缺口、降级、人工责任人和恢复条件。

### 高风险治理级（`governed`）

- 涉及真实案卷、外部服务、自动写回、发布或高权限工具时，增加 `file-backed fixture`、owner、review cadence、rollback boundary、trust report 和 permission policy；
- 输出质量或完整性有人审/真实运行证据；
- secret scan、安装模拟、版本一致性和公开 claim guard 通过；
- 未取得的 provider、人审、遥测或跨平台原生权限证据保持 `missing evidence`。
- 涉及发布时，发布行为获得单独授权，并按包内发布规则执行，不依赖独立 publisher Skill。
- 每个 `blocked` 模块同时记录输入或依据缺口、停止/降级路径、人工责任人和重新核验或更新触发点。
- 文件型夹具索引必须指向包内真实文件；人工复核记录至少包含 reviewer、日期、case、结果、信心和理由。只有计划、空模板或 `missing evidence` 台账时不得声明高风险治理级。

## 法律专属阻断项

以下任一项缺失，不能把法律 Skill 标为可靠生产能力（均为 `block`）：

1. 具体法条、司法解释、诉讼时效或案例可独立核验的规则；
2. 关键依据缺失时的停止路径；
3. 来源溯源标签或等价来源记录；
4. 材料/事实/法律评价/程序状态四层分离；
5. 事实或证据不足时不输出确定性结论；
6. PDF 处理没有遵守包内归档、转换和 evidence JSON 契约（无 PDF 工作流的 Skill 豁免，但须在输出契约或交接中声明豁免理由）；
7. 用户提供的项目约束被用来放宽本 Skill 的法律真实性或安全底线；
8. 引用会议纪要、指导性案例、理解与适用等准法源时未区分裁判依据、应当参照、仅能说理、须举证查明的引用姿态。

## 运行后交接

报告至少写明：命令、日期、输入范围、结果、失败项、人工复核项、未覆盖法域/时点、`missing evidence` 和下一步修复位置。不要只写“通过”或把上游仓库的测试数字搬过来。
