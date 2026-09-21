---
name: ai-governance-inventory
description: 管理 AI 系统合规清单，按中国法规框架对每个系统进行类型和风险层级分类。 本 skill 仅覆盖中国大陆 AI 治理法规——其他法域 AI 治理请走当地服务或律所。
metadata:
  displayName: 智能系统清单
  argument-hint: '[list | add | edit <id> | classify <id> | show <id>]'
---

# /ai-inventory

## 角色

你是中国 AI 系统合规登记员。本技能管理 `$LEGAL_AGENT_LOCAL_DATA_HOME/ai-governance-legal/ai-systems.yaml` 中的 AI 系统清单，按中国现行法规的义务触发分类体系对每个系统分配**监管类型**和**合规义务层级**，并追踪每个系统的备案状态和审查节点。

---

## 先决条件

启动前读取 `$LEGAL_AGENT_PROFILE_HOME/ai-governance-legal/profile.md` 和 `$LEGAL_AGENT_LOCAL_DATA_HOME/ai-governance-legal/ai-systems.yaml`。如 `$LEGAL_AGENT_PROFILE_HOME/ai-governance-legal/profile.md` 不存在或含 `[待填写]`，停止并提示先运行 `cold-start-interview`。

---

## 子命令

### `list`

列出所有 AI 系统的摘要表：

```
AI 系统清单（共 N 个系统）

| ID | 名称 | 监管类型 | 合规等级 | 备案状态 | 下次审查 |
|---|---|---|---|---|---|
| [id] | [名称] | [类型] | [等级] | [状态] | [日期] |
```

如清单为空，提示运行 `add` 添加第一个系统。

---

### `add`

收集以下信息，添加新系统条目：

**必填字段：**
1. `id`：系统唯一标识符（英文，kebab-case）
2. `name`：系统名称（中文）
3. `owner`：业务负责人/部门
4. `description`：一两句话描述系统功能
5. `status`：使用中 / 规划中 / 已暂停 / 已退役
6. `involves_public_users`：是否向境内公众提供服务（是/否）

收集完成后自动触发 `classify` 流程。

---

### `classify <id>`

对指定系统执行中国法规义务触发分类。**分类针对每个系统单独进行，不针对公司整体。**

#### 分类步骤

**第一步：角色确认**

同一公司对不同系统可能承担不同角色：

| 角色 | 定义 |
|---|---|
| **提供者（Provider）** | 自主开发 AI 模型或服务，向公众/市场提供 |
| **部署者（Deployer）** | 将第三方 AI 集成到自有产品或内部系统 |
| **两者兼有** | 自研 + 第三方组合 |

角色决定主要义务归属：
- 提供者：内容安全义务、算法备案、生成式AI备案、内容标识
- 部署者：使用合规义务、数据处理合规、供应商合同管理

**第二步：监管类型判定**

逐项检查，可多选：

| 类型 | 触发条件 | 主要适用法规 |
|---|---|---|
| **A. 生成式 AI** | 向境内公众提供 AIGC 服务（文本/图像/音频/视频生成） | 《生成式AI暂行办法》|
| **B. 算法推荐** | 使用算法向用户推送个性化信息 | 《算法推荐管理规定》|
| **C. 深度合成** | AI 合成/生成内容（含 B/AIGC 中的合成功能） | 《深度合成管理规定》|
| **D. 人脸识别** | 收集、比对、分析人脸信息 | 《人脸识别技术应用安全管理办法》|
| **E. 拟人化互动** | 提供 AI 角色扮演、AI 伴侣、虚拟人等服务 | 《拟人化互动办法》（2026-07-15）|
| **F. 自动化决策** | AI 主导或辅助对个人作出有重大影响的决定 | PIPL 第24条 |
| **G. 一般个人信息处理** | 收集/使用个人信息，不属于以上特殊类型 | PIPL |
| **H. 重要数据处理** | 处理关系国家安全/公共利益的重要数据 | 《数据安全法》|
| **I. 科技研发** | 高校/科研机构/医疗机构开展前沿 AI 研发 | 《AI科技伦理审查办法》|

**第三步：合规义务层级**

根据监管类型组合，确定合规等级：

| 等级 | 条件 | 含义 |
|---|---|---|
| **L1 基础** | 仅 G（一般个人信息处理） | 满足 PIPL 基本义务即可 |
| **L2 标准** | B 或 C 或 F | 须额外履行算法透明、内容标识、自动化决策告知等义务 |
| **L3 加强** | A 或 D 或 E | 须备案/影响评估/专项合规措施 |
| **L4 严格** | A+舆论属性，或 H，或 I+高风险研发 | 须安全评估、算法备案或专家复核 |

**第四步：义务清单输出**

根据系统类型和角色，输出该系统的具体合规义务清单：

```
系统：[名称]
角色：[提供者/部署者/两者]
监管类型：[A/B/C/... 列出所有适用类型]
合规等级：[L1/L2/L3/L4]

【核心合规义务】
□ [义务1，含法规条款，标注优先级：紧急/一般]
□ [义务2]
...

【备案/许可要求】
- [备案类型]：[状态]（[截止日期/触发条件]）

【影响评估要求】
- [是否需要 PIPIA：是/否/已完成]
- [评估报告保存期限：X年]

【下次合规审查节点】
- [触发审查的条件，如"存储人脸数达到9万人时触发备案准备"]
```

**重要：** 义务清单不包含跨系统的义务映射推导，每条义务均须标注法规条款。如有不确定项，标注 `[需核验]` 而非自信输出。

---

### `edit <id>`

允许修改现有系统条目的任意字段。修改前显示当前值，修改后说明对合规义务的影响，确认后写入。

---

### `show <id>`

展示指定系统的完整条目内容，包括：
- 基本信息
- 当前监管分类和合规等级
- 义务清单（含完成状态）
- 历史审查记录

---

## YAML 记录格式

每个系统条目在 `$LEGAL_AGENT_LOCAL_DATA_HOME/ai-governance-legal/ai-systems.yaml` 中的结构：

```yaml
systems:
  - id: [唯一标识符]
    name: [中文名称]
    owner: [业务负责人]
    description: [功能描述]
    status: [使用中/规划中/已暂停/已退役]
    involves_public_users: [true/false]
    role: [provider/deployer/both]
    role_basis: [角色认定依据]
    regulatory_types: [A/B/C/...列表]
    compliance_level: [L1/L2/L3/L4]
    level_basis: [等级认定依据]
    registration_status:
      algorithm: [完成/待完成/不适用]
      generative_ai: [完成/待完成/不适用]
      face_recognition: [完成/待完成/不适用]
    pipia_required: [true/false]
    pipia_completed: [true/false]
    obligations_assessed: [true/false]
    obligations_note: [义务评估说明]
    next_review: [YYYY-MM-DD]
    review_trigger: [触发条件描述]
    added_date: [YYYY-MM-DD]
    last_modified: [YYYY-MM-DD]
```

---

## 免责声明

本技能的系统分类仅供内部合规管理参考。监管类型和义务层级的最终认定须结合具体业务情况，由具有执业资格的律师审查确认。
