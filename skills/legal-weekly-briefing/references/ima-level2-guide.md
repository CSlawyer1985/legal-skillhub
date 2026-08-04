# IMA Level 2 · 知识库入库完整指南

> 本文与 SKILL.md Level 2 节同步，唯一维护源。

---

## 前置条件

- Level 1 已通过验证（`python3 scripts/verify.py` 全部通过）
- IMA 知识库账号（ima.qq.com）
- `~/.config/ima/client_id` 和 `~/.config/ima/api_key` 已配置

---

## 文件说明

| 文件 | 用途 |
|------|------|
| `scripts/ima_importer.py` | IMA 分类器 + 导入队列 + OpenAPI 调用 |
| `assets/config/taxonomy.yaml` | 文章标题关键词 → IMA folder_id 映射 |

---

## 工作原理

```
run_pipeline.py 产出 ima_import_queue.jsonl
    ↓
按 taxonomy.yaml 的 keywords 匹配文章 → 分配 folder_id
    ↓
按 folder_id 分组 → 调用 IMA OpenAPI import_urls
    ↓
文章进入 IMA 知识库对应文件夹
```

---

## 分类规则

内置 10 个分类：

| 分类 | priority | 代表性关键词 |
|------|----------|-------------|
| 婚姻家事 | 10 | 婚姻、继承、夫妻、离婚、遗嘱、彩礼 |
| 公司 | 8 | 公司法、股东、股权、决议、章程 |
| 合同借贷 | 8 | 合同、借贷、债务、定金、买卖 |
| 建筑工程 | 9 | 建设工程、施工、包工头、以房抵债 |
| 劳动法 | 9 | 劳动、工伤、调岗、解雇、社保 |
| 交通事故 | 9 | 道交、保险、代驾、肇事、准驾 |
| 房地产/物权 | 8 | 物业、业主、交房、拆迁、漏水 |
| 侵权 | 8 | 侵权、受伤、游乐场、高空抛物 |
| 刑事 | 7 | 刑事、罪名、命案、诈骗 |
| 管辖 | 6 | 管辖、仲裁、主管 |

**优先级设计**：专业领域（建筑工程/劳动法/交通事故）priority=9，高于通用兜底（合同借贷）priority=8——避免"劳动合同"被"合同"关键词捕获。公司 priority=8，避免"保险公司""代驾公司"被误捕获。

**关键词设计**：精确子串匹配（`keyword in title`）。多字关键词需补充单字别名（如"保险理赔"+"保险"）。

---

## 导入 IMA

`run_pipeline.py` 自动将 `score ≥ 6.5` 且来源为法院公众号的条目写入 `ima_import_queue.jsonl`。

周报精选和 IMA 入库是**两条独立管道**：
- **周报**：diversity-aware 选 10 条精品，受 `max_per_source` 限制同源≤2
- **IMA**：分数 ≥ 6.5 的法院源条目**全部**入库，不限条数、不受同源限制

6.5 = 雷达区显示线 = IMA 入库线。调整阈值：修改 `settings.yaml` 中的 `ima_import_threshold`。

IMA OpenAPI 端点: `POST https://ima.qq.com/openapi/wiki/v1/import_urls`
认证头: `ima-openapi-clientid` + `ima-openapi-apikey`
参数: `{"knowledge_base_id": "...", "folder_id": "...", "urls": [...]}`

**注意**：根目录导入时**不传 `folder_id` 字段**（传了会报 222000）。
**限制**：单次最多 ~10 个 URL。

---

## IMA 接入链路

从配好 KB_ID 到文章实际入库，有两种方式：

### 方式 A：WorkBuddy 环境（Agent 直接调 ima-skill · 推荐）

WorkBuddy 内置 `ima-skills` 套件，Agent 可直接调 `import_urls` 接口。

**前提条件**：
1. `ima-skills` 已安装（对话中说「导入网页到知识库」能触发即已安装）
2. API 凭证已配置（`~/.config/ima/client_id` + `api_key`）

**配置 API 凭证**：
```
1. ima.qq.com → 登录 → 右上角头像 → 设置 → API 密钥
2. 点击「生成密钥」→ 复制 Client ID 和 API Key
3. 终端执行：
   mkdir -p ~/.config/ima
   echo "你的client_id" > ~/.config/ima/client_id
   echo "你的api_key" > ~/.config/ima/api_key
4. 验证：cat ~/.config/ima/client_id（应输出你的 ID）
```

⚠️ echo 命令会被记录到终端历史（~/.zsh_history）。可先运行 `set +o history` 关闭记录，或用文本编辑器直接粘贴。

### 方式 B：非 WorkBuddy 环境（CLI 直调 OpenAPI）

```bash
curl -X POST https://ima.qq.com/openapi/wiki/v1/import_urls \
  -H "ima-openapi-clientid: $IMA_CLIENT_ID" \
  -H "ima-openapi-apikey: $IMA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"knowledge_base_id":"YOUR_KB_ID","folder_id":"YOUR_FOLDER_ID","urls":["https://..."]}'
```

项目目录下的 `import_ima.py` 封装了此流程。

---

## 踩坑速查表

| # | 症状 | 根因 | 解决 |
|---|------|------|------|
| 1 | `folder_id 非法 (222000)` | 文件夹只能网页端手动创建 | 去 ima.qq.com 手动建文件夹 → 填 folder_id |
| 2 | Agent 说「只有只读工具」 | ima-mcp 仅暴露 search/get | 用 ima-skills 的 import_urls 或 CLI 直调 OpenAPI |
| 3 | `401 Unauthorized` | 凭证未配或格式错 | 重新生成 → 写入无空格无换行 |
| 4 | 导入后页面在根目录 | taxonomy 关键词没命中 | 检查 taxonomy.yaml，补冷门关键词 |
| 5 | 相同 URL 重复入库 | IMA 不自动去重 | 维护 `imported_cache.jsonl` |
| 6 | 一次传 >10 个 URL | IMA 限 10 个/次 | 分批；`import_ima.py` 自动处理 |
| 7 | 中文 URL 报 400 | URL 编码问题 | `urllib.parse.quote(url, safe=':/?&=#')` |

---

## 完整导入流程（Agent 执行参考）

```
1. 读取 config/taxonomy.yaml → 加载 KB_ID（非占位符，用户已替换）
2. 读取 ima_import_queue.jsonl → 逐条 classify() 分配 folder_id
3. 按 folder_id 分组，每组 URL 按 ≤10 分批
4. 每批调用 import_urls(knowledge_base_id, folder_id, urls)
5. 成功 → imported_cache.jsonl；失败 → failed_import.jsonl
6. 输出汇总：总数 / 成功 / 失败 / 按文件夹分布
```

---

## 初始化步骤

> ⚠️ **P0 安全红线**：必须使用用户**自己创建的** IMA 知识库。不允许订阅/加入他人 KB。如果 `knowledge_base_id` 为 `YOUR_KNOWLEDGE_BASE_ID`，导入自动阻断。

1. 访问 [ima.qq.com](https://ima.qq.com) **自建知识库**（点击「创建知识库」，不是「加入」）
2. 在知识库中创建 10 个对应文件夹
3. 从 IMA 后台 URL 获取各文件夹 `folder_id`，替换 `taxonomy.yaml` 占位符
4. 替换 `knowledge_base_id`
5. 将凭证写入 `~/.config/ima/client_id` 和 `~/.config/ima/api_key`
