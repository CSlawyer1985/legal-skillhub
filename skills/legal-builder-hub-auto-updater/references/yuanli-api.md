# 法律元力 API 参考（技能 + 工具包）

站点根 URL 记为 `{BASE}`（profile 默认 `https://yuanli.ailaw.cn`，[法律元力](https://yuanli.ailaw.cn/)）。

以下接口均为 **公开读**，无需鉴权 Header，供终端用户与 legal-builder-hub 智能体调用。

---

## 一、工具包（Toolkits / Skillpack）

### 1.1 目录（auto-updater / registry-sync）

```http
GET {BASE}/api/toolkits/catalog
```

响应字段：

| 字段 | 说明 |
|------|------|
| `schema_version` | 契约版本，当前 `0.1.0` |
| `generated_at` | ISO8601 生成时间 |
| `toolkits[].id` | `toolkit_id` |
| `toolkits[].name` / `version` / `published_at` | 与 `toolkits.yaml` 一致 |
| `toolkits[].package_dir` | 磁盘目录名 |
| `toolkits[].download_url` | 相对路径，拼 `{BASE}` |
| `toolkits[].sha256` | 当前 zip 的 SHA-256（十六进制） |
| `toolkits[].size_bytes` | zip 字节大小 |
| `toolkits[].etag` / `last_modified` | 与下载接口一致 |

**更新检测**：本地保存 `sha256` 或 `etag`，轮询 catalog；变化则 `GET .../download`。

```bash
curl -sS '{BASE}/api/toolkits/catalog' | jq '.toolkits[] | {id, version, sha256}'
```

### 1.2 检索（registry-browser）

```http
GET {BASE}/api/toolkits?search=&tag=&category=&page=1&page_size=12
GET {BASE}/api/toolkits/{toolkit_id}
GET {BASE}/api/toolkits/categories
```

| 参数 | 说明 |
|------|------|
| `search` | 匹配 `name`、`name_en`、`description`、`tags`（子串，不区分大小写） |
| `tag` | 标签精确匹配 |
| `category` | 分类精确匹配 |
| `page` / `page_size` | 分页，`page_size` 最大 100 |

列表响应：`{ total, page, page_size, items: [Toolkit, ...] }`。

详情含 `description`、`content`（README/INSTALL 摘要）、`author`、`author_logo`、`tags`、`version` 等。

**文件浏览（可选）**

```http
GET {BASE}/api/toolkits/{toolkit_id}/files
GET {BASE}/api/toolkits/{toolkit_id}/files/{path}
```

### 1.3 下载

```http
GET {BASE}/api/toolkits/{toolkit_id}/download
HEAD {BASE}/api/toolkits/{toolkit_id}/download
```

响应头：

- `ETag` — `"<sha256>"`，与 catalog 一致
- `Last-Modified` — GMT
- `Content-Length`
- `X-Package-Sha256` — 无引号 sha256
- `Cache-Control: public, max-age=300`

条件请求（未变化 → `304`）：

```bash
curl -sSL -o pack.zip '{BASE}/api/toolkits/legal-skillpack-cn-localized/download'

curl -sSI -H 'If-None-Match: "<本地 etag>"' \
  '{BASE}/api/toolkits/legal-skillpack-cn-localized/download'
```

---

## 二、技能（Skills）

列表与详情数据来自站点技能库；安装包在 `skills/{skill_id}/` 或 OSS。

### 2.1 检索（registry-browser）

```http
GET {BASE}/api/skills?search=&tag=&category=&page=1&page_size=12
GET {BASE}/api/skills/{skill_id}
GET {BASE}/api/skills/categories
GET {BASE}/api/skills/tags
```

| 参数 | 说明 |
|------|------|
| `search` | 匹配 `name`、`description`、`tags` |
| `tag` | 标签精确匹配 |
| `category` | 分类精确匹配 |
| `page` / `page_size` | 分页，最大 100 |

列表项主要字段：`id`、`name`、`description`、`category`、`tags`、`owner`、`version`、`updated`、`download_count`、`source`（作者结构化信息）等。

详情 `GET /api/skills/{skill_id}` 额外包含：

- `content` — SKILL.md 正文（去 frontmatter）
- `trust_info` — 安全/有效性 vetting
- `examples`、`related_articles`

**标签聚合**

```http
GET {BASE}/api/skills/tags
```

响应：`[{ "tag": "合同审查", "count": 12 }, ...]`，按 count 降序。

```bash
curl -sS '{BASE}/api/skills?search=NDA&page_size=20'
curl -sS '{BASE}/api/skills/commercial-nda-review'
```

### 2.2 下载

```http
GET {BASE}/api/skills/{skill_id}/download
```

- 将 `skills/{skill_id}/` 目录打包为 `{skill_id}.zip`
- 成功时递增 `download_count`
- 若配置 OSS：可能 **307 重定向** 到签名 URL（`expires=300`），客户端需跟随重定向

```bash
curl -sSL -o commercial-nda-review.zip \
  '{BASE}/api/skills/commercial-nda-review/download'
```

**包内文件列表**

```http
GET {BASE}/api/skills/{skill_id}/files
GET {BASE}/api/skills/{skill_id}/files/{path}
```

优先读 OSS 上已发布 zip；否则读本地目录。

**Vetting 报告（若存在）**

```http
GET {BASE}/api/skills/{skill_id}/vetting-report
```

### 2.3 更新检测（智能体）

| 来源 | 检测方式 | 拉取方式 |
|------|----------|----------|
| 法律元力 工具包 | `GET /api/toolkits/catalog` 对比 `sha256` / `etag` | `GET /api/toolkits/{id}/download` |
| 法律元力 单 skill | `GET /api/skills/{id}` 中的 `version`、`updated` 与本地记录对比 | `GET /api/skills/{id}/download` |
| GitHub registry | commit SHA（上游 skill-installer） | raw / git，非本 API |

技能侧 **暂无** 与 toolkits 相同的 `catalog` / `HEAD` / `ETag` 接口；以详情中的版本字段为准。

---

## 三、与 legal-builder-hub 技能对照

| 能力 | 推荐 API | 对应 skill |
|------|----------|------------|
| 浏览 法律元力 包 | `GET /api/toolkits`、`/catalog` | `registry-browser` |
| 安装 zip 包 | `GET /api/toolkits/{id}/download` | `skill-installer` |
| 检查包更新 | `GET /api/toolkits/catalog` | `auto-updater` |
| 浏览站内 skill | `GET /api/skills?search=` | `registry-browser` |
| 安装单 skill 包 | `GET /api/skills/{id}/download` | `skill-installer`（站内源） |
| 检查 skill 更新 | `GET /api/skills/{id}`（`version` / `updated`） | `auto-updater` |

静态兜底：`references/yuanli-toolkits.yaml`（离线或无 API 时使用）。
