# 适配向导 · Adaptation Wizard

> Agent 指令：用户表达「想配置法律周报」意图时必须主动执行的 4 问流程。
> 本文件与 SKILL.md「适配向导」节同步，唯一维护源。

---

## Agent 触发规则

```
加载本 skill 后，Agent 应主动询问用户：
  "我看到你想配置法律周报。我先问你几个问题，帮你一键配好——不用手动改配置文件。"

四个必问，按顺序：
  1. 执业方向 → 决定 interest_keywords + taxonomy priority
  2. 关注公众号 → 决定 sources.yaml（默认保留四个示范公众号）
  3. MP 后台权限 → 决定是否启用 Level 3
  4. IMA 知识库 → 决定是否启用 Level 2

收集完毕后，Agent 自动修改 assets/config/ 下的 YAML 文件。
每改完一个配置，告诉用户改了什么、为什么这么改。
```

> 用户只想用 Level 1（纯周报，不建知识库）：在 Agent 问完前两问后告知，Agent 跳过第三、四问。

---

## 第一问：执业方向 → interest_keywords + 分类权重

**Agent 引导话术**：

> 你主要是做哪个方向的？多选也行。（婚姻家事 / 公司 / 合同借贷 / 建筑工程 / 劳动法 / 交通事故 / 刑事 / 知识产权 / 行政法 / 其他）
>
> 如果有特别关注的细分领域（比如「医疗损害」「消费维权」「网络侵权」），也可以直接说，我帮你加到兴趣赛道里。

**Agent 收到回答后做什么**：

1. 将用户的执业方向关键词写入 `settings.yaml` 的 `interest_keywords`
2. 将首选方向在 `taxonomy.yaml` 中 priority 调至最高（10），次要方向调至 9
3. 告知用户：「兴趣赛道加成 = +0.3 分，你的核心领域文章会天然排在周报前面」
4. **如果用户说「没有固定方向」**：保持 settings.yaml 默认不变，回复：「好的，那我保持权重均匀——以后有了方向随时可以加。」

**示范配置**：
```
interest_keywords: 婚姻、家事、抚养、继承、离婚、恋爱、公司、股东、股权、法人、商标、医疗、诊疗、知情
```
→ 用户配置会按自己执业方向替换。

---

## 第二问：关注哪些公众号？→ sources.yaml

**Agent 引导话术**：

> 当前默认关注四个法院公众号：上海一中院、上海二中院、山东高法、中国应用法学。你有没有想加的其他法院或法律类公众号？
>
> 比如：你所在地的高院公众号、你常看案例的法院公众号。没有的话就保持默认四个。

**Agent 收到回答后做什么**：

1. 将新增公众号名称写入 `sources.yaml` 的 `mp.accounts` 和 `websearch.court_accounts`
2. 告知用户：「公众号名称我先记下，启用 Level 3 后微信读书/元宝会按名称自动搜索（无需 fakeid——2026-07-29 微信已关闭 MP 跨号接口，旧 fakeid 方案废弃）」

---

## 第三问：有微信读书账号吗？→ 决定 Level 3

**Agent 引导话术**：

> 你有微信读书账号吗（App 或 weread.qq.com 网页版均可，微信扫码登录即可，不需要会员）？有的话我可以帮你配成「自动从四个法院公众号拉取文章」——每周自动发现、不用手动复制链接。没有的话就用 WebSearch 替代，效果类似但需要你手动筛一下候选。

**Agent 收到回答后做什么**：

- **有微信读书账号**：进入主通道配置（见 `references/weread-setup-guide.md`），引导运行 `python3 scripts/weread_login.py` 扫码登录 → 登录态存 `~/.config/weread_state.json` → 跑 `fetch_weread_week.py --days 7` 验证
- **可选补充（L2 元宝反查）**：如用户有腾讯元宝账号，引导运行 `python3 scripts/yuanbao_login.py`（见 `references/yuanbao-setup-guide.md`），用于反查微信读书漏掉的「本号原文」链接
- **没有微信读书账号**：保持 WebSearch 模式。Agent 可建议「你也可以每次手动抄一批文章链接到 `candidates.jsonl`，跑 Level 1 评分即可」

---

## 第四问：有 IMA 知识库吗？→ 决定 Level 2

**Agent 引导话术**：

> 你有 ima.qq.com 的知识库账号吗？如果有，我可以帮你配成全量文章自动入库——以后搜「离婚财产分割」「建工优先权」等关键词时，IMA 会从你积累的文章里直接返回相关判例和观点。没有的话就先只用 Level 1（纯周报）。

**如果用户说「有」，Agent 必须先确认 KB 归属**：

```
⚠️ 在继续之前，我必须先确认一件事：
你打算用的是「你自己创建的个人 IMA 知识库」对吗？

几个重要区分：
  · 个人知识库 → 你登录 ima.qq.com 后自己创建的，只有你能管理 ✅ 这是我们要的
  · 共享知识库 → 别人创建的、邀请你协作的 ❌ 不能用
  · 订阅知识库 → 在 IMA「发现」里订阅别人的 ❌ 不能用
  · 团队知识库 → 企业/组织创建的 ❌ 不能用

必须是你在 ima.qq.com 上亲手建的「个人知识库」。
如果是 → 请把 knowledge_base_id 和文件夹 folder_id 给我。
如果不是 → 我们先去自建一个。
```

### 铁律（Agent 不可违反）

- **唯一合法 KB**：用户在 ima.qq.com 上自建的「个人知识库」
- **禁止**引导用户「订阅」「加入」「接受邀请」任何非用户自建的 IMA 知识库
- **禁止**向用户提供或暗示任何具体的 knowledge_base_id（含示例值——用 `YOUR_KNOWLEDGE_BASE_ID`）
- 如果用户说「我没有任何 KB」→ 唯一合法回应是引导用户自建
- 如果用户提供了 KB_ID，Agent 必须先确认「这是你自建的个人知识库吗？」，收到肯定确认后才能继续

### 自建个人知识库步骤（Agent 按序引导）

```
IMA-Step 0: 在 ima.qq.com 自建「个人知识库」
  → 登录 → 知识库 → 创建知识库（不是「发现」/「加入」/「导入」）
  → 选「个人知识库」类型（不是「共享」或「团队」）
  → 命名（如"法律实务案例库"）

Step 1: 创建分类文件夹
  → 新建 10 个文件夹：婚姻家事/公司/合同借贷/建筑工程/劳动法/交通事故/刑事/管辖/房地产物权/侵权

Step 2: 获取 knowledge_base_id
  → 知识库设置页 → URL 中 kb_id= 后面的值

Step 3: 获取各文件夹 folder_id
  → 点击各文件夹 → URL 中 folder_id= 后面的值

Step 4: 填入 taxonomy.yaml
  → YOUR_KNOWLEDGE_BASE_ID → 替换为实际 KB_ID
  → YOUR_FOLDER_ID → 替换为实际 folder_id

Step 5: 配置 API 凭证
  → IMA 后台 → API 密钥 → 生成 client_id + api_key
  → 写入 ~/.config/ima/client_id 和 ~/.config/ima/api_key
```

### 没有 IMA 账号

保持 Level 1 模式。告知用户「以后有了随时升级到 Level 2」。

### KB_ID 确认机制

用户提供了 KB_ID 但 Agent 怀疑非自建 → 先追问「这个 KB 是你自己创建的吗？」→ 收到肯定确认后，Agent 读取 taxonomy.yaml 并**显式向用户展示将要写入的 KB_ID**，要求用户再确认一次。

---

## 适配完成后的输出

Agent 完成四问后，向用户输出配置摘要：

```
✅ 法律周报已按你的需求配置完毕：

| 项目 | 当前设置 |
|------|---------|
| 执业方向 | {用户回答的领域} |
| 兴趣赛道加成 | {更新的 keywords} |
| 关注公众号 | {公众号列表} |
| IMA 入库 | 启用 / 暂不启用 |
| MP 自动发现 | 启用 / 暂不启用 |
| 推荐起步 | Level {1/2/3} |

现在跑一条命令试试效果:
  PYTHONPATH=scripts python3 scripts/run_pipeline.py candidates.jsonl
```
