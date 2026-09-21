# 第三方代码归属（UPSTREAM）

本目录下的文件取自上游开源项目，署名与许可见下。

| 本目录文件 | 上游路径 | 状态 |
|---|---|---|
| `compare_docx_tracked.py` | `scripts/compare_docx_tracked.py` | **含 1 处本地补丁**（见下），原版另存为 `compare_docx_tracked_upstream.py` |
| `compare_docx_tracked_upstream.py` | 同上 | 上游原版，未改一字（对拍与回退用） |
| `verify_tracked.py` | `scripts/verify_tracked.py` | 原样，未改一字 |
| `ooxml-revision-rules.md` | `references/ooxml-revision-rules.md` | 原样，未改一字 |
| `README.upstream.zh-CN.md` | `README.zh-CN.md` | 原样，未改一字 |
| `EVALUATION.upstream.md` | `EVALUATION.md` | 原样，未改一字 |

## 本地补丁 1：分词器不再把连续标点粘成一块

| | |
|---|---|
| **位置** | `compare_docx_tracked.py` 的 `TOK_RE`（`granular_rewrite` 内） |
| **上游写法** | `re.compile(r'\s+|\w+|[^\w\s]+')` |
| **本地写法** | `re.compile(r'\s+|\w+|[^\w\s]')`（去掉末尾 `+`） |
| **日期** | 2026-09-16 |

**为什么改**：`[^\w\s]+` 会把「**），**」粘成一个不可分的 token。中文文书里「），」→「）。」这类"前一字相同、后一字不同"的相邻标点变化极常见，粘成整块后两块互不相等，于是被判成"删一块 + 插一块"——**两版里都在同一位置的括号和句号，会被标成删除＋插入**。用户看到的是"文件里莫名多了一个括号"，而纸质稿上那个括号根本没人动过。

**实测效果**（同一对文件）：

| | `<w:ins>` | 删除内容 | 判定 |
|---|---|---|---|
| 上游原版 | 2 | `），如发生争议…并赔偿违约金5万元。` | 括号、句号被误标 |
| 本地补丁 | **0** | `，如发生争议…并赔偿违约金5万元` | **正确** |

**回归自证**：`scripts/regress_trackdiff.py` 跑 9 个场景（标点相邻／纯插入／数字改动／句首标点／中英混排／连续标点／句内整串删除／整段删除／全角半角互换）对比两版，判据为"新版标记数不增加 + fallback 不增加 + `verify_tracked.py` 七项全 PASS"。结果：**3 个场景为纯改善，其余 6 个完全相同，无任何劣化，fallback 全为 0**。

**回退方式**：`cp compare_docx_tracked_upstream.py compare_docx_tracked.py`。上游若发新版，按下方「升级与对拍」先比上游版的哈希；若上游自行修了这个问题，则删掉本地补丁、换用上游版本。


## 上游项目

- **项目名**：docx-trackdiff
- **版本**：1.0.0
- **仓库**：https://github.com/stephenlzc/docx-trackdiff
- **PyPI**：`pip install docx-trackdiff`
- **SkillHub / ClawHub slug**：`docx-trackdiff`
- **获取日期**：2026-09-16
- **许可证**：**MIT**（上游 README 原话：「[MIT](LICENSE)——随意使用，保留署名即可。」）

## 署名（上游 README「致谢」章节原文）

- **作者**：**Big Stephen**（GitHub [@stephenlzc](https://github.com/stephenlzc)）——需求、真实场景测试
- **共同作者**：**Kimi K3 Agent Swarm**，由 [Moonshot AI](https://www.moonshot.ai/) 出品（[@MoonshotAI](https://github.com/MoonshotAI)）——实现、验证、打包
- 上游自述：整条流水线（diff 算法、OOXML 修订标记、验证框架、技能打包）由 Kimi K3 的 Agent Swarm 实现；发布前一轮 swarm 式评估（with-skill 与 baseline 配对盲测 + 独立评分代理）抓出并修复了一个真实的图片保真 bug。

## 我们借用了什么

**借的是"修订标记怎么落进 OOXML"这件事**——具体包括：

1. **以 NEW 为底包**：输出包用新版文件做基座，样式、图片、脚注、表格、节属性全部保留；接受全部修订 == NEW，拒绝全部修订 == OLD。
2. **两份标记语法**：整段增删必须同时标记**段落标记本身**（`w:pPr/w:rPr/w:del`），否则 Word 里显示成空行；行内词级修订按 run 拆分，删除片段进 `<w:delText xml:space="preserve">`。
3. **四条硬规则**：`w:id` 全局唯一递增；`<w:del>` 内不得残留 `<w:t>`；`<w:ins>/<w:del>` 只包整 `<w:r>` 且不得互相嵌套；`word/settings.xml` 必须加 `<w:trackChanges/>`。
4. **深拷贝旧段落时的清理项**：剥除 `w:bookmarkStart/End`、`w:proofErr`、`w:permStart/End` 防 id 冲突；`r:id`/`r:embed`/`r:link` 重映射到新包 rels，图片部件按 `tracked_` 前缀复制。
5. **复杂块回退策略**：含图片/公式/超链接等原子元素且 diff 边界对不齐时，整段回退为"删旧段 + 插新段"，不强行拆 run。

## 我们没借的部分

- 上游只处理 **.docx ↔ .docx**；本 skill 的**扫描/照片稿 ↔ 电子稿**主链路、四类渲染假阳性降级，都是本 skill 自有能力，与上游无关。
- 上游的 PyPI 打包、CI、Kimi 技能清单适配，本 skill 未采用。

## 升级与对拍

上游若发新版：

```bash
pip download docx-trackdiff==<新版本> --no-deps -d /tmp/up
# 或从 https://github.com/stephenlzc/docx-trackdiff 取 scripts/ 下同名文件
md5 -q /tmp/up/compare_docx_tracked.py <本skill>/vendor/compare_docx_tracked_upstream.py
```

哈希一致说明未改动；不一致则先看上游 CHANGELOG，再决定是否替换，并**回填本文件的版本号与获取日期**。

## 许可证文本

上游仓库未在分发包内附 `LICENSE` 文件，许可证信息来自其 `pyproject.toml`（`license = { text = "MIT" }`）与 README 徽章/章节。按 MIT 要求，**保留上述署名即可使用**。本 skill 在 `SKILL.md` 的「第三方归属与致谢」一节同步展示该署名。
