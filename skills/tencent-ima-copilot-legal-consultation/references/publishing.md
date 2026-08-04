# 发布流程与 JSON 配置手册

> 本文档供 AI 和运维者参考，说明本技能从修改到发布上线的完整流程，以及沿途涉及的每一个 JSON 文件。

---

## 发布总览

```
skill/tencent-ima-copilot-legal-consultation/   ← 唯一真相源
    │  修改 SKILL.md / skill.yaml / references/ / scripts/config.json
    │
    ├─ 同步 → skills-mapping.json 版本号（若变更）
    │
    ├─ sync_skills.py --sync → workbuddy/.../skills/ 副本
    │
    ├─ Git push → SkillHub / GitHub 可直接引用
    │
    └─ 打包 ──→ D:\github\zip\（可选归档）
```

---

## JSON 配置体系（7 个文件完整说明）

### 1. skill.yaml — 技能元数据

**位置**：`skill/tencent-ima-copilot-legal-consultation/skill.yaml`

**角色**：技能的「身份证」，定义触发词、知识库列表、引用的辅助文件、兼容平台。

**关键字段**：

| 字段 | 示例 | 作用 |
|------|------|------|
| `version` | `"1.1.1"` | **版本号**，与 skills-mapping.json 必须一致 |
| `triggers` | `["怎么办","合同纠纷",...]` | 触发词列表，模型据此激活技能 |
| `knowledge_bases` | 5 个库的 name/role/required | 可选知识库清单 |
| `references` | 4 个 .md 文件 | 指向 `references/` 下的辅助文档 |
| `compatibility` | `[ima.copilot, Claude.ai, ...]` | 兼容平台列表 |

**版本号变更时**：必须同步更新 `skills-mapping.json` 中对应 skill 的 `version` 字段。

---

### 2. config.json — 运行时配置

**位置**：`skill/tencent-ima-copilot-legal-consultation/scripts/config.json`
**副本**：`workbuddy/workbuddy-ima-copilot-legal-consultation/skills/tencent-ima-copilot-legal-consultation/scripts/config.json`

**角色**：运行时参数，控制搜索行为、模式切换、笔记归档。

```json
{
  "brand": "律锥",
  "save_to_notes_enabled": true,      // 是否自动存笔记
  "notes_notebook": "法律咨询",         // 笔记本名称
  "search_intensity": 1.0,            // 检索强度 0.5~2.0
  "default_mode": "expert",           // 默认模式 expert/quick
  "quick_mode": {
    "enabled": true,
    "max_search_rounds": 1,           // 快速模式搜索轮次
    "max_law_articles": 3,
    "max_cases": 2,
    "no_internet_search": true,       // 快速模式禁用联网
    "use_rag_only": true,
    "skip_tiered_reading": true,
    "output_template": "brief"
  }
}
```

**调优建议**：
- `search_intensity`：日常 1.0，用户反馈覆盖面不足时调至 1.5，特殊深度需求调至 2.0
- `quick_mode.enabled`：设为 `false` 强制所有用户走专家模式
- 修改后需运行 `sync_skills.py --sync` 同步到副本

---

### 3. skills-mapping.json — 技能→Agent 映射中枢

**位置**：`D:\github\skills-mapping.json`

**角色**：`sync_skills.py` 的**唯一数据源**，定义每个 WorkBuddy Agent 绑定哪些技能、源路径和目标路径。

```json
{
  "agents": {
    "workbuddy-ima-copilot-legal-consultation": {
      "displayName": "IMA法律咨询专家",
      "skills": [{
        "name": "tencent-ima-copilot-legal-consultation",
        "source": "legalskill/skill/tencent-ima-copilot-legal-consultation",
        "target": "legalskill/workbuddy/workbuddy-ima-copilot-legal-consultation/skills/tencent-ima-copilot-legal-consultation",
        "version": "1.1.1"
      }]
    }
  }
}
```

**使用规则**：
- `source` / `target` 路径相对于 `D:\github\`
- `version` 必须与 `skill.yaml` 的 version 保持同步
- 新增 Agent 时：先在此文件加 agent 记录，再在 `workbuddy/` 下建目录
- `sync_skills.py` 只读此文件，不写回

---

### 4. plugin.json — WorkBuddy 插件清单

**位置**：`workbuddy/workbuddy-ima-copilot-legal-consultation/.codebuddy-plugin/plugin.json`

**角色**：WorkBuddy 专属的插件定义，控制专家在市场中的展示信息。

**关键字段**：

| 字段 | 说明 |
|------|------|
| `displayName` | 中英文显示名 |
| `displayDescription` | 中英文功能描述 |
| `tags` | 市场分类标签 |
| `quickPrompts` | WorkBuddy 界面预置的 3 条推荐提问 |
| `categoryId` | `"11-SecurityCompliance"` |
| `agents` | 指向 Agent 描述文件路径 |
| `skills` | 指向技能目录路径 |

**修改场景**：
- 改显示名称/描述 → 更新 `displayName` / `displayDescription`
- 换推荐提问 → 更新 `quickPrompts` 数组
- 换头像 → 更新 `avatar` 路径，替换 `avatars/expert.png`

---

### 5. _meta.json — SkillHub 发布元数据

**位置**：`workbuddy/workbuddy-ima-copilot-legal-consultation/skills/tencent-ima-copilot-legal-consultation/_meta.json`

**角色**：SkillHub 平台自动写入的发布记录。记录发布者、发布时间、slug。

```json
{
  "ownerId": "445771",
  "publishedAt": 1779436929348,
  "slug": "tencent-ima-copilot-legal-consultation",
  "version": "1.1.1"
}
```

**⚠️ 保留文件**：
- 此文件由 SkillHub 自动生成，**不在源目录中**
- `sync_skills.py` 的 `PRESERVED_FILES` 白名单包含此文件，同步时不会被删除
- **严禁手动编辑**

---

### 6. _skillhub_meta.json — 本地安装元数据

**位置**：`workbuddy/workbuddy-ima-copilot-legal-consultation/skills/tencent-ima-copilot-legal-consultation/_skillhub_meta.json`

**角色**：IDE 自动写入的本地安装记录。

```json
{
  "slug": "tencent-ima-copilot-legal-consultation",
  "name": "tencent-ima-copilot-legal-consultation",
  "version": "1.1.1",
  "installedAt": 1779956585998,
  "source": "skillhub"
}
```

**⚠️ 保留文件**：与 `_meta.json` 一样，同步时不会被删除。严禁手动编辑。

---

### 7. vercel.json — 短链重定向

**位置**：`D:\github\lawskill\vercel.json`

**角色**：部署在 lawskill.cn，将短路径重定向到实际资源。

```json
{
  "redirects": [
    { "source": "/ima",    "destination": "https://skillhub.cn/skills/tencent-ima-copilot-legal-consultation", "permanent": true },
    { "source": "/claw",   "destination": "https://skillhub.cn/skills/claw-agent-workspace", "permanent": true },
    { "source": "/qclaw",  "destination": "https://skillhub.cn/skills/claw-agent-workspace", "permanent": true },
    { "source": "/workbuddy", "destination": "https://github.com/legalskill/legalskill/tree/main/workbuddy/workbuddy-ima-copilot-legal-consultation", "permanent": true },
    { "source": "/buddy",  "destination": "https://github.com/legalskill/legalskill/tree/main/workbuddy/workbuddy-ima-copilot-legal-consultation", "permanent": true }
  ]
}
```

**修改场景**：新增短链 → 加一条 redirect → `vercel --prod` 部署。

---

## 标准发布步骤

### 日常修改 → 上线

```bash
# 1. 修改技能源文件（skill/ 下）
#    - SKILL.md、skill.yaml、references/、scripts/config.json

# 2. 如果有版本号变更 → 同步两处
#    - 编辑 skill.yaml 的 version 字段
#    - 编辑 D:\github\skills-mapping.json 对应 skill 的 version 字段

# 3. 运行同步检查
cd D:\legalskill\repo-domain-publish-manager
python scripts/sync_skills.py           # 先看差异
python scripts/sync_skills.py --sync    # 确认后同步

# 4. 提交到 Git
cd D:\github\legalskill
git add -A
git commit -m "skill: vX.X.X - 更新说明"
git push

# 5. （可选）打包归档
compress-archive -Path D:\github\legalskill\workbuddy\workbuddy-ima-copilot-legal-consultation -DestinationPath D:\github\zip\workbuddy-ima-copilot-legal-consultation.zip

# 6. （如需要）更新展示页
cd D:\github\lawskill
# 编辑 skills.js 中的版本号或链接
vercel --prod
```

### 版本号规则

- **skill.yaml 的 `version`**：每次功能变更必须递增
- **skills-mapping.json 的 `version`**：与 skill.yaml 保持同步
- **SKILL.md 尾部签名**：`*技能版本：x.y.z*`
- **skills.js 中的 `version`**：手动同步（展示页用）
- 版本号格式：`major.minor.patch`（如 `1.1.1`）

### 新增 Agent 时

1. 在 `skills-mapping.json` 新增 `agents.<agent-dir-name>` 项
2. 在 `workbuddy/` 下建完整目录结构（含 `.codebuddy-plugin/plugin.json`）
3. 在 `lawskill/skills.js` 加新卡片
4. 在 `lawskill/vercel.json` 加短链（如需要）
5. 更新 `D:\github\README.md` 映射表

---

## sync_skills.py 工作原理

- **归属**：`repo-domain-publish-manager/scripts/sync_skills.py`（发布工具，不随 WorkBuddy 产品分发）
- **数据源**：只读 `D:\github\skills-mapping.json`
- **对比方式**：MD5 哈希（不依赖文件时间戳）
- **保留文件白名单**：`_meta.json`、`_skillhub_meta.json`
- **空目录清理**：同步后自动删除副本中残留的空目录
- **`--json` 输出**：供其他脚本消费的标准 JSON 差异报告

```bash
cd D:\legalskill\repo-domain-publish-manager
python scripts/sync_skills.py          # 检查差异（人类可读）
python scripts/sync_skills.py --json   # 检查差异（JSON 格式）
python scripts/sync_skills.py --sync   # 自动同步
```

---

## 目录结构完整图

```
D:\github\
├── README.md                         # 人机共读备忘录
├── skills-mapping.json               # [JSON#1] 映射中枢
├── legalskill/                       # 主仓库
│   ├── .gitignore                    # 排除 rules
│   ├── skill/
│   │   └── tencent-ima-copilot-legal-consultation/
│   │       ├── SKILL.md              # 技能核心指令
│   │       ├── skill.yaml            # [JSON#2] 技能元数据
│   │       ├── README.md             # 技能说明（含发布章节）
│   │       ├── scripts/
│   │       │   └── config.json       # [JSON#3] 运行时配置
│   │       └── references/
│   │           ├── kb-profiles.md
│   │           ├── colloquial-mapping.md
│   │           ├── legal-scenarios.md
│   │           ├── output-templates.md
│   │           └── publishing.md     # 本文档
│   └── workbuddy/
│       └── workbuddy-ima-copilot-legal-consultation/
│           ├── .codebuddy-plugin/
│           │   └── plugin.json       # [JSON#4] 插件清单
│           ├── agents/
│           ├── avatars/
│           ├── install.bat
│           ├── install.ps1
│           ├── install.sh
│           └── skills/
│               └── tencent-ima-copilot-legal-consultation/  # 副本
│                   ├── _meta.json          # [JSON#5] SkillHub 元数据
│                   └── _skillhub_meta.json # [JSON#6] 本地安装元数据
├── lawskill/                         # 展示页
│   ├── skills.js                     # 技能卡片数据
│   └── vercel.json                   # [JSON#7] 短链重定向
├── tools/                            # 本地工具（不入 Git）
└── zip/                              # 发布产物归档
```
