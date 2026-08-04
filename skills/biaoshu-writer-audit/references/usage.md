# 执行细节（操作手册）

本文件是**执行任务时的完整操作指引**——做解读/制作/合规、生成报告、处理边界情形时按需查阅。接口契约与返回字段见 [api.md](api.md)。

## ⚠️ 输出约定（必须遵守，除非用户明确说不要）

运行 `zcm.py` 时**老老实实把脚本输出原样给用户看**，不得为了「省事/抽字段」把它藏起来：

1. **实时进度照常显示**：解读/抽包/生成/合规都会把百分比+阶段（如 `[20%] 智能解读中`）打到 **stderr**。**不要 `2>` 重定向、不要吞掉**——用户要看到进度推进。需要后台实时播报时用 `progress-stream` + Monitor，而非把进度倒进文件。
2. **完整打印结果文件的绝对全路径**：每次产出后，必须把以下文件的**绝对路径**明确告知用户：
   - 智能解读结果/报告（`*_智能解读.html` 等）
   - 成品标书 `*_投标文件.docx`
   - 合规审查结果/报告（`*_合规审查.html` 等）

   脚本本身已打印这些路径（`generate`/`result` 成功后打 `已下载成品标书：<全路径>` 到 stderr，并把路径打到 stdout）；**别用 `>`/`2>` 把它们重定向掉**。若用 `--no-wait`，完成后须主动补取结果/出报告并打印全部全路径。

   此外，解读/生成/合规完成后脚本会打印一行 `💰 当前剩余积分：X`——**照常转述给用户**，让其对余额与「够不够下一次」有数；查询失败时不打印，属正常，不必追问。

> 反例（禁止）：`python3 scripts/zcm.py generate <pid> > out.json 2> log` —— 这会同时藏掉进度和成品全路径。

3. **凭证/注册/绑定/积分类交互是例外，不要把命令与 exit 码原样抛给用户**：这类脚本报错（如 `register` 缺参的 exit 2、`非交互环境请传参…`）是给你（助手）看的提示，**不是给用户的**。你应当把它翻译成一句「用户下一步该提供什么」，并由你代跑命令——绝不要让用户自己去敲 `python3 scripts/zcm.py register`。详见「第 1 步：凭证」末尾的绑定/积分流程。

## 用法速查（完整流程）

```bash
python3 scripts/zcm.py login --app-key bk_live_xxx   # 1. 配凭证（自动生成 config.json；或 trial / 环境变量）
python3 scripts/zcm.py me                            #    连通 + 余额自检
python3 scripts/zcm.py interpret 招标文件.pdf --report html   # 2. 解读 → project_id（+解读报告）
python3 scripts/zcm.py packages <project_id>         # 3. 抽包（多包才需选包）
python3 scripts/zcm.py generate <project_id>         # 4. 生成成品标书（扣积分）
python3 scripts/zcm.py compliance <project_id> 投标文件.docx --report html --name 招标文件.pdf   # 5. 可选：合规审查
```
招标文件支持 `.pdf/.doc/.docx`；投标文件 `.doc/.docx`。全部自动轮询、实时播报后端进度。各步详解见下。

## 目录
- [第 1 步：凭证](#第-1-步凭证)
- [第 2 步：智能解读](#第-2-步智能解读)
- [第 3 步：抽取分包](#第-3-步抽取分包)
- [第 4 步：生成成品标书](#第-4-步生成成品标书)
- [第 5 步：合规审查](#第-5-步合规审查)
- [报告生成与命名](#报告生成与命名)
- [关键约定](#关键约定)

---

## 第 1 步：凭证

凭证默认存在 **skill 内 `config.json`**。读取优先级：环境变量 > `config.json`（回退旧 `~/.zcm/credentials.json`）。

**只需 App Key 一项**：

**配置方式（任选其一）**：
1. 直接创建 `config.json`（skill 根目录，按下面模板写入即可，`base`/`output_dir` 可选留空）：
   ```json
   {"app_key":"bk_live_xxxxx","base":"","output_dir":""}
   ```
   建好后 `chmod 600 config.json`（含真实 Key）。通常不用手写——方式 2~5 任一命令都会自动生成该文件。
2. 用户把 Key 发你后，**由你代跑** `login --app-key bk_live_xxx` 保存（自动建/更新 config.json，权限 600）——别把这条命令丢给用户自己敲。
3. 临时用环境变量：`export ZCM_APP_KEY=bk_live_xxx`（首次会自动落盘到 config.json）。
4. 没 Key 想直接注册：向用户要手机号，由你代跑 `register --phone`（skill 内手机号+短信验证码换取 App Key，自动保存）——见本节末尾「绑定手机号 / 积分不足」流程，别让用户自己敲命令。
5. 免费试用：`python3 scripts/zcm.py trial`（自动采集设备特征开通试用账号，送 200 积分；同设备重复执行幂等返回原 Key，不重复赠分）。

- **保存后转述位置**：凭证保存成功后（login / trial / register / 环境变量落盘任一方式），把脚本打印的**凭证文件（config.json）完整路径**转述给用户。
- 🔒 **发布安全**：`config.json` 含真实 Key——**绝不上传发布包/提交仓库**；发布包不含任何配置文件，模板结构见上方方式 1。`ZCM_CONFIG` 可改 config.json 路径。
- **用户完全没有任何 Key**（首次用）：三选一，均由你代跑——① 试用零输入自动开通（送 200，绑手机号再送 200）；② 向用户要手机号，你代跑 `register --phone` 在 skill 内注册；③ 用户已在官网有 Key——获取全路径：打开官网 https://biaoshu.zhiliaobiaoxun.com/ 注册登录后，点**左侧菜单『Skill 接入 → 获取 APP Key』**在弹出面板中查看/复制 Key（首次打开自动生成）；让他把 Key 粘贴到对话里（如「我的 App Key 是 bk_live_xxxxx，帮我保存一下」），由你代为保存（**别把 `login --app-key` 命令甩给用户**）。缺凭证时脚本会打印这些指引并退出（码 2）。
  - 注意：③ 仅限**从没有过 Key** 的场景。若用户**已有 Key** 只是积分不够，走上面「绑定手机号 / 积分不足」的 `bind_key` 链接，别让他另开新账号。
- 先 `python3 scripts/zcm.py me` 确认连通与积分余额（生成会扣分）。

### 绑定手机号 / 积分不足（由你代跑，别把命令丢给用户）

积分不足或想绑手机号领 200 积分时，**你（助手）驱动整个流程，用户只需提供手机号与验证码**，App Key 全程不变：

1. 先向用户要**手机号**（例：「请提供你的手机号，我来发送验证码」）。**不要**打印 `python3 scripts/zcm.py register` 让用户自己敲。
2. 你运行 `python3 scripts/zcm.py register --phone <手机号>` 触发发码，然后告诉用户「验证码已发送，请把收到的验证码发我」。
3. 拿到验证码后你运行 `python3 scripts/zcm.py register --phone <手机号> --code <验证码>` 完成绑定/注册（App Key 不变、+200 积分）。
4. **绝不运行无参 `register`**（非交互会 exit 2）；也**别把 exit 码 / `非交互环境请传参…` 这类内部报错贴给用户**——只说下一步要什么。

- **用户不想在 skill 内注册 / 想自助上网页**（已有 App Key，比如积分烧穿时）：给这条「注册即绑定」网页链接——`<当前 App Key>` 用 `me` 或 config.json 里那枚**真实 Key** 替换后再发给用户：
  ```
  https://biaoshu.zhiliaobiaoxun.com/register?bind_key=<当前 App Key>
  ```
  用户在网页注册手机号即把新账号绑定到**这枚现有 Key**，+200 积分、Key 不变，回到对话直接继续，**无需再 login**。
  - ⛔ **禁止**：已有 Key 的用户，别引导他去官网首页「另注册新账号 / 另生成新 Key 再 `login` 切换」——那会把积分留在一个**孤立的新账号**上、还得换 Key，正是这次要修的坑。官网首页 `https://biaoshu.zhiliaobiaoxun.com/`（不带 `bind_key`）只给**完全没有任何 Key** 的新用户。
  - **别凭空写站点首页当充值/绑定入口**；充值用脚本输出的 `recharge_url`，绑定用上面带 `bind_key` 的链接。
- 手机号已被注册过：返回老账号 Key 并切换，试用账号数据不迁移。

## 第 2 步：智能解读

唯一招标文件入口；只在这步传一次，后续全程复用 `project_id`。

```bash
python3 scripts/zcm.py interpret /path/招标文件.pdf      # 本地路径，或 http(s) URL
```
- 支持 `.pdf/.doc/.docx`，**≤ 50 MB**（超限脚本提前报错）。自动轮询，结束打印 `project_id`（**记下它**）+ **完整解读结果**。
- **云端文件先下载到本地再处理**：传入 URL 时，脚本会先把文件下载到 `biaoshu-bailian-files/_downloads/`（拿到真实文件名、绕开后端远程下载的 https/内网/大小限制），再按本地文件上传。文件名也据此自动命名报告。
- **直接把解读结果展示给用户**——含 8 维度 + 控标洞察：项目基本信息 / 合标项 / 废标项 / 评审项 / 关键要求 / 商务条款 / 报价要求 / 采购背景分析 / 控标洞察（`decision_analysis`）。挑重点讲（控标建议、废标红线、评分结构），别只丢 `project_id`。字段口径见 [api.md 附录 A](api.md)。
- 展示后**主动问是否生成解读报告**（见[报告生成与命名](#报告生成与命名)）。

## 第 3 步：抽取分包

```bash
python3 scripts/zcm.py packages <project_id>
```
- 把返回的 `packages` 呈现给用户挑选，收集选中的 `package_ids`。
- `is_multi_package=false` → 跳过选包，第 4 步不带 `--package-ids`。

## 第 4 步：生成成品标书

**唯一扣积分的步骤**，耗时较长。生成前**先问用户存哪**：
- 给了路径 → `-o <路径>`；想长期固定 → `login --output-dir <目录>`。
- 不指定 → 默认 skill 包同级 `biaoshu-bailian-files/`，文件名 `招标文件名_投标文件.docx`（招标文件名从本地缓存取，取不到退化 `bid_<job_id>.docx`）。

```bash
python3 scripts/zcm.py generate <project_id> --package-ids 11,12 --total-pages 80 -o 投标文件.docx
# 非多包：python3 scripts/zcm.py generate <project_id>
```
- 存放目录优先级：`-o` > `ZCM_OUTPUT_DIR` > `login` 存的 `output_dir` > 默认 `biaoshu-bailian-files/`。
- 自动轮询（默认超时 3600s，`--timeout` 可调）。完成后打印**成品完整路径**+所在目录，**两项都告诉用户**。
- ⏱ **生成可能耗时 >10 分钟**（实测 30 页约 15 分钟）。脚本本身轮询不会超时，但**前端/工具调用常有 ~10 分钟上限**会把命令杀掉——**注意：后端任务不受影响、仍在跑，切勿重新提交（会重复扣费）**。长任务推荐：`generate <pid> --no-wait` 拿 `job_id`，再用 `progress-stream <job_id>`（配合 Monitor 后台实时播报）续查到终态，最后 `result <job_id> -o <路径>` 下载并打印全路径。万一命令被杀，用同一 `job_id` 续查即可，不要重发 generate。

## 第 5 步：合规审查

要**两样输入，都要让用户提供**：
1. **招标文件**（`.pdf/.doc/.docx`）→ 经第 2 步解读产出 `project_id`；已解读则复用，不重传。
2. **投标文件**：**一份或多份** `.doc/.docx`，被审查对象（本地路径或 http(s) URL），**每份 ≤ 1024 MB**。

```bash
python3 scripts/zcm.py compliance <project_id> /path/投标A.docx /path/投标B.docx
# 暗标/电子标：加 --blind / --electronic
```
- 投标文件传 URL 时，**同样先逐个下载到本地再上传**（落 `biaoshu-bailian-files/_downloads/`）。
- **直接把合规结果展示给用户**——含 `summary`（风险计数 + 一句话结论）、`issues[]`（风险等级/招标依据/投标证据/修改建议）、`similarity_issues[]`（多文件雷同）、`manual_items[]`（人工核查清单）。优先讲高风险与结论。字段见 [api.md 附录 B](api.md)。
- `risk_level` 实测为 `high`/`review`/`tip`，脚本输出与报告**已自动转中文**（高风险/待复核/提示），直接用中文呈现。
- 未解读就调 → 409；投标文件缺失/类型不对 → 422（两份输入缺一不可）。
- 展示后**主动问是否生成合规报告**（见下）。

## 报告生成与命名

解读/合规结果可渲染成报告（HTML / Word），零依赖：

```bash
# 随命令一步出（默认 html；要 Word：--report both）
python3 scripts/zcm.py interpret 招标文件.pdf --report html
python3 scripts/zcm.py compliance <pid> 投标.docx --report html --name 招标文件.doc
# 按 job_id 补出
python3 scripts/zcm.py report --job <JOB_ID> --name 招标文件.pdf            # html
python3 scripts/zcm.py report --job <JOB_ID> --name 招标文件.pdf --format both  # +Word
```
- **默认只出 HTML**；用户明确要 Word 才 `docx`/`both`。
- 命名：`招标文件名_智能解读` / `招标文件名_合规审查`。取名优先级：`--name` > 结果自动识别（`original_filename` / `project_info.项目名称` / 本地缓存）> `标签_时间戳`。
  - `interpret` 自动用上传文件名；`generate` 自动用缓存名；**`compliance`/`report --job` 拿不到招标文件名时务必带 `--name`**，否则退化时间戳。
- 报告内容依赖后端按 [api.md 附录 A/B](api.md) 返回完整结果；`/result` 只回句柄或字段空时，报告注明「无明细」而不报错。

## 经验沉淀与问题上报（后台命令，勿展示给用户）

经验沉淀（用户两问都同意后执行；长文本先写入临时文件走 --content-file）：

```bash
python3 scripts/zcm.py experience --type preference --stage write \
  --title "落款格式" --content "落款统一用公司全称"
# type: material=素材 preference=偏好 correction=纠错；stage: interpret/write/compliance
# 长文本：--content-file /tmp/exp.txt；可选 --project-id 关联项目
```

成功输出「已沉淀，累计 N 条」——向用户转述 N；`daily_quota_exceeded` → 转述「今日沉淀已达上限（每天最多 20 条）」。

问题上报（内容先展示给用户、同意后执行；自动附带 skill 版本与渠道码）：

```bash
python3 scripts/zcm.py feedback --category error --scene "生成标书" \
  --phenomenon "轮询中断报超时" --expectation "自动续轮询"
# category: misguide=跑偏 correction=用户纠正 error=报错 suggestion=建议
```

两条命令上报失败（网络/配额/Key 失效）时不阻断主流程：如实告知「本次未回传，稍后可再试」。

## 关键约定

- **必须输出完整路径**：解读报告 / 成品标书 / 合规报告生成后，把**每个文件的完整绝对路径**逐行告诉用户（脚本已用「已生成…/已下载…」打印绝对路径，照搬即可）——**不要只说落在某目录**。
- **进度播报（两阶段，必须这样做才能实时）**：Bash 工具不流式传输 stderr，`--no-wait` + `progress-stream` + Monitor 是唯一能让用户看到实时进度的方式。长任务（interpret / generate / compliance）统一走以下三步：
  1. **提交**（同步，快）：加 `--no-wait`，Bash 运行后立即拿到 `job_id`。
  2. **实时监听**：`Bash(run_in_background=True)` 运行 `python3 scripts/zcm.py progress-stream <job_id>`，再用 Monitor 订阅该进程 stdout——每行状态变更即时通知 Claude，Claude 实时转达给用户（如「5% 准备文档」→「20% 解读中」→「完成」）。Monitor 的 description 用正常任务名，**不带「重试」等临时标签**——即使是 worker_lost 后重新提交的 job，新 job 已正常运行，描述应反映当前状态而非历史原因。
  3. **取结果 + 生成报告 + 输出路径**：Monitor 收到 `[完成]` 后必须主动补齐后处理，三类任务各有对应步骤：
     - `interpret`：`result <job_id>`（提取 project_id）→ `report --job <job_id> --format html`（生成解读报告）→ 输出报告全路径
     - `generate`：`result <job_id> -o <路径>.docx`（下载标书）→ 输出 docx 全路径
     - `compliance`：`result <job_id>`（打合规摘要）→ `report --job <job_id> --format html`（生成合规报告）→ 输出报告全路径
     
     > `--no-wait` 跳过了同步模式的后处理，**AI 必须手动补**，否则报告文件不会生成，用户看不到路径。
  > 仅在用户不需要看进度或调试时才用单命令前台运行（无 `--no-wait`）。`packages` / `me` 等快速命令无需两阶段。
- **断点续查**：`job <job_id>` 查状态、`result <job_id> [-o file]` 取结果、`cancel <job_id>` 取消。
- **幂等**：网络重试给提交命令加 `--idempotency-key <UUID>`，避免重复建任务/重复扣费。
- **续接已有 project**：用户解读后直接说「帮我生成」，沿用 `project_id` 从第 3 步继续，不重传。
- **错误处理**：脚本已把 401/402/404/422/429 转中文。常见——402 余额不足让用户充值；整层 404 多为开放 API 总开关未开，让管理员开启；429 退避重试。完整对照见 [api.md](api.md)。
- **积分不足（402）**：错误体带 `phone_bound` / `bind_url`（未绑手机号时）——脚本会先引导「绑定手机号再领 200 积分」（`register`，App Key 不变），已绑则直接给充值链接（`recharge_url`，携带 `bind_key`）。
