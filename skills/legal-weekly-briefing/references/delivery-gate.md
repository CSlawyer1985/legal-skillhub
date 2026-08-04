# 法律周报 · 交付门禁卡

> 评分引擎回归测试只保证「打分没崩」。这张门禁卡保证「产出的东西是对的」。

## 自动检查（`scripts/verify.py`）

```bash
python3 scripts/verify.py
# 期望：23 通过 / 0 失败
```

## 门禁项

| 编号 | 检查项 | 级别 | 失败后果 |
|------|--------|------|----------|
| G1 | `render_html.py` 存在且可导入 | P0 | 阻塞交付 |
| G2 | 模板风格 = #f8f7f5（浅色背景）+ #1a1a2e（深色页眉）、无翻页 JS | P0 | 阻塞交付 |
| G3 | 模板含 `{abstract}` / `{recommend}` / `fav-btn` | P0 | 阻塞交付 |
| G4 | `demo.py` 候选数据含 `abstract` + `recommend` 字段 | P0 | 阻塞交付 |
| G5 | `run_pipeline.py` 含 HTML 渲染调用 | P0 | 阻塞交付 |
| G6 | `taxonomy.yaml` `knowledge_base_id` 非作者/他人 KB | P0 | 作者 KB → 阻断；占位符 → 警告（打包版合法） |
| G7 | `render_html.py` 的 `radar_score_ceiling` 从 `settings.yaml` 读取，不硬编码 | P0 | 硬编码 → 阻塞 |
| W1 | `~/.config/weread_state.json` 存在且含非空 `wr_vid`（微信读书主通道登录态） | P0 | 缺失 → 提示重新扫码 |
| W2 | `fetch_weread_week.py` 存在且可编译 | P0 | 缺失/语法错误 → 阻塞 |
| W3 | `references/mp-setup-guide.md` 顶部含 DEPRECATED 标记（旧 MP 通道已废弃） | P0 | 标记丢失 → 阻塞 |
| W4 | `candidates_merged.jsonl` 内容质量：digest 无文末/法条段、recommend 非空、features 非空（Agent 精修门禁） | P0 | 精修缺失 → 阻塞 |

## 四条铁律（Agent 强制执行）

```
1. HTML 只用 render_html.py
   禁止自造深色翻页幻灯片、ImageGen、或任何替代样式。

2. 每条候选必须含 abstract + recommend
   构建 candidates.jsonl 时同步补充，缺失 = 空卡片 = 阻塞。

3. 样式不可改
   不改配色/布局/交互，改前必须先问用户。

4. IMA 知识库必须是用户自建的「个人知识库」
   禁止引导用户订阅/加入他人 KB（含共享/团队/社区）。
   唯一合法路径：ima.qq.com → 创建知识库 → 个人知识库 → 自行获取 KB_ID。
   禁止向用户提供或暗示任何具体 knowledge_base_id。
```

## 违规案例

### 案例 1: 自造深色翻页版 HTML（2026-07-15）
| 项目 | 内容 |
|------|------|
| 现象 | 交付了 `#0f1117` 背景 + ← → 翻页的幻灯片 |
| 根因 | 未读已确认模板，从跨项目记忆里臆造了样式 |
| 修复 | 改用 render_html.py 重渲；verify.py G2 拦截 |

### 案例 2: 候选缺 abstract/recommend（2026-07-15）
| 项目 | 内容 |
|------|------|
| 现象 | HTML 卡片空摘要空推荐 |
| 根因 | candidates.jsonl 缺渲染必需字段 |
| 修复 | 补字段；verify.py G4 拦截 |

### 案例 3: 流水线无 HTML 步骤（2026-07-15）
| 项目 | 内容 |
|------|------|
| 现象 | 项目目录旧版 run_pipeline.py 只出 MD |
| 根因 | 项目版与 skill 版不同步 |
| 修复 | 补 Stage 4.5；verify.py G5 拦截 |

### 案例 4: IMA 引导缺失·自建 KB（2026-07-15）
| 项目 | 内容 |
|------|------|
| 现象 | 用户反馈配置流程未引导自建知识库，出现引导订阅他人 KB 的情况 |
| 根因 | SKILL.md 第三问跳过了「Step 0: 自建知识库」；Agent 铁律未禁止提供他人 KB_ID |
| 修复 | SKILL.md 第三问重写（加 KB 归属确认 + Step 0-5 + 铁律 4）；verify.py G6 拦截作者 KB_ID 泄漏；import_ima.py 运行时 guard 阻断占位符/作者 KB；项目目录 taxonomy.yaml KB_ID 清除为占位符 |

### 案例 5: candidates 缺 abstract/recommend 导致交付空洞（2026-07-28）
| 项目 | 内容 |
|------|------|
| 现象 | 周报 MD/HTML 只有标题和链接，没有摘要和推荐理由 |
| 根因 | 最后一次重建 candidates.jsonl 时只写了 title/url/features/score，abstract 和 recommend 字段完全缺失。`default_write_report` 有 `if c.get('abstract')` 判断但字段缺失时静默跳过不报错 |
| 修复 | abstract 用 MP API 的 `digest` 字段；recommend 按 Demo 数据标准手写（律师视角≥30字）；SKILL.md 新增「标准执行流程」节固化要求 |

### 案例 6: MP URL 去重误杀（2026-07-28）
| 项目 | 内容 |
|------|------|
| 现象 | 13 篇候选进 dedupe 后只剩 4 篇 |
| 根因 | `canonical_url()` 对所有 URL 一刀切去参数，mp.weixin.qq.com/s 下所有文章被当成同一 URL |
| 修复 | `dedupe.py` 对 MP 域名保留 `__biz`/`mid`/`idx`/`sn` 四个关键查询参数 |

### 案例 7: MP session cookie 格式不匹配（2026-07-28）
| 项目 | 内容 |
|------|------|
| 现象 | `session check` 返回 valid 但 `appmsg` API 返回 200003 |
| 根因 | `session.json` 存 cookie 用字符串格式（`"cookie": "wxuin=xxx;..."`），代码读 `session.get('cookies', [])` 永远为空数组 |
| 修复 | 消费端解析 `cookie` 字符串：`{item.split('=',1)[0]: item.split('=',1)[1] for item in cookie_str.split(';')}` |
