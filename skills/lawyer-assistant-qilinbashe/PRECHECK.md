# PRECHECK — 法律技能包上线前自检



## 文件完整性

- [x] agents/ — 107个技能，全部含YAML frontmatter（reviewer / maturity / related_skills 齐备）

- [x] README.md / SKILL.md / manifest.yaml / QUICKSTART.md / PRECHECK.md / CHANGELOG.md / 律师助手.md / _plugin_base.json（plugin 体系公共权威源，由 scripts/generate_plugins.py 生成双平台 plugin.json）

- [x] references/ — 13 个逻辑依赖文件全部可达（含 references/样例/ 子目录）（核心法条速查索引 / MCP工具速查表 / 高频领域法条摘要 / 边界事实卡 / 中文名称 / 口语映射表 / 完整流程 / 法条时效标注速查 / 离线法条精华）；32 部离线法条摘要已合并为 references/离线法条精华.md（离线兜底）

- [x] 重资料已外置 — 离线法条全集 / 省域司法指引全集 / 案例库全集 / 使用手册全集 / 相关法规汇编 共 5 部合并全集已注入法律法规知识库供全文检索；case-library/、area-guide/、docs/、references/离线-* 已从包内移除（原始分文件备份见工作区 _removed_backup/，可随时恢复且不打包）

- [x] templates/ — 37 个文件（templates/文书模板/ 28 个 + templates/ 顶层 9 个），包内文书模板齐全

- [x] scripts/ — 12 个 .py 脚本 + 1 个 panorama_template.html 完整且可用（verify_consistency / logic_doctor / markdown_to_docx / build_matrix / render_panorama / multimodal_ingest / voice_transcribe / generate_plugins / rebuild_zip / submit_check / sync_to_installed / check_knowledge_base 等）

- [x] 源目录含 .codebuddy-plugin/plugin.json 与 .workbuddy-plugin/plugin.json（WorkBuddy/CodeBuddy 加载用；由 _plugin_base.json + scripts/generate_plugins.py 双平台生成，互为镜像）；**SkillHub 提交版按平台规则排除**——ZIP 内不含 plugin.json / _meta.json / _skillhub_meta.json 及任何 dotfile 目录（仅收 .md/.yaml，dotfile 判路径不安全），属提交规则设计而非缺失



## 版本一致

- [x] 版本统一为 4.4.1（SKILL.md / manifest / plugin.json×2 / _meta.json / _skillhub_meta.json 一致；agent 头 version 已清零——刻意设计，仅保留包级版本；如平台 schema 要求 agent 级 version 可一键回补）



## 格式规范

- [x] 无BOM；无零宽字符（U+200B/U+200C/U+FEFF 等恶意隐藏字符为零；U+200D ZWJ 仅出现在 👨U+200D👩U+200D👦 等 emoji 组合序列中，属合法 Unicode 编码，非隐藏字符，允许保留）

- [x] 全部文件为 .md / .yaml / .yml / .json / .py / .html（无其他类型）

- [x] trigger_keywords / related_skills 采用正确YAML格式

- [x] SKILL_INVENTORY 已含「成熟度(maturity)」列，与107个agent frontmatter一致



## 安全

- [x] 无个人密钥/Token/绝对路径（源文件路径统一用  占位，不泄露用户名）

- [x] Bearer占位符已标注PLACEHOLDER

- [x] logic_doctor.py 对输出做 PII 硬扫描（身份证号/手机号等），发现即 FAIL



## 数量

- [x] 提交稿 legal-skills.zip 共 192 条（源目录完整文件排除 .git/__pycache__/.codebuddy-plugin/.workbuddy-plugin 与 _icon.jpg/_meta.json/_skillhub_meta.json 后，与 zip 零差异，经解包 verify_consistency.py 实跑核验全绿）；结构：agents/107 + references/13（12 + 样例 1） + templates/37（9 + 文书模板 28） + scripts/16（15 个 .py + 1 个 panorama_template.html） + assets/1 + examples/1 + 顶层文档与配置 17 = 192（平台 plugin 元数据 .workbuddy-plugin/.codebuddy-plugin 按提交规则排除、不进 zip；.gitattributes/.DS_Store/.gitignore 等 dotfile 与 _icon.jpg/_meta.json/_skillhub_meta.json/fix2.py/fix_submit_blockers.py 均排除；legacy 历史参考 3 个与 12 个小白版技能已按“核心轻量化”移除，不影响功能）。上传 SkillHub 裁剪版排除非运行必需的节点图可视化资源 assets/律师助手节点树状图.html（1，属渲染资源非执行逻辑），实传 192 个，满足 ≤200 上限；Agent 功能零影响，.py 与技能脚本均保留；重资料已外置 法律法规知识库，原始分文件备份见工作区 _removed_backup/ 不打包）。



## 构建与校验命令

```bash

# 一致性自检（计数/版本/分类数/plugin.json）

python3 scripts/verify_consistency.py



# 输出品质十一维核验（对任一 agent 生成的 .md 交付物）

python3 scripts/logic_doctor.py <output.md>



# 导出 Word 正式文书

python3 scripts/markdown_to_docx.py <output.md> <out.docx>

```



## 完整性哈希（SHA256）

打包后用以下命令计算并核对：

```bash

# Windows

certutil -hashfile legal-skills.zip SHA256

# macOS / Linux

shasum -a 256 legal-skills.zip

```

> 本次构建参考值（近期构建）：

> 

> 注：每次重新打包后数值会变，请以重新计算的哈希为准；不要将该值硬编码进需要随包变化的文件。



## 隐私与合规

- [x] 107 个 agent 均含  字段；专业版/工具类均建议补充「隐私与数据安全提醒」三段（脱敏 / 主办律师实质审查 / 不泄露商业秘密）

- [x] 所有文书均标注「AI 生成初稿，不得直接使用，须经主办律师实质审查」

- [x] 反模式拦截：胜率预测、直接提交法院、代替出庭等话术均设拦截提示



## 依赖与降级

- [x] MCP 依赖：pkulaw（北大法宝）、yuandian（华宇元典），required=true

- [x] 离线降级：MCP 不可用时回退 references/离线法条精华.md（32 部离线法条摘要已合并为该单文件，离线兜底）

- [x] 节点图渲染：先 cp 出 .workbuddy 隐藏目录再 present_files，规避 403 拦截

