# 欧盟《数据法案》实务技能——部署指南

> 📄 **[查看交互式技能页面 →](https://oliverschmidtprietz.github.io/EU-Data-Act/)**

版本历史见 [CHANGELOG.md](CHANGELOG.md)。

## 概述

面向执业律师的《欧盟法规 (EU) 2023/2854》（《数据法案》）分析与起草技能。为在面向客户或企业内部的场景中使用《数据法案》的资深法律顾问、合规官和产品法务量身校准。

本技能的结构锚点是**角色 × 章节 × 阶段**。每项事务通过识别以下要素定位：

- 各方扮演哪些《数据法案》角色（用户、数据持有者、数据接收者、第三方、客户、提供者、公共部门机构，以及任何并存的 GDPR 角色）；
- 法规的哪些章节适用（第二至八章）；
- 该章节流程处于哪个阶段。

该锚点决定加载哪些参考资料以及技能应用哪张场景卡。

## 覆盖范围

| 章节 | 条文 | 操作深度 |
|------|------|----------|
| 第二章 | 3–7 | 完整——物联网产品及相关服务数据；B2C 和 B2B 共享 |
| 第三章 | 8–12 | 完整——依据欧盟其他法律进行的强制性 B2B 共享（FRAND、补偿） |
| 第四章 | 13 | 完整——B2B 数据合同中单方强加的不公平合同条款 |
| 第五章 | 14–22 | 完整——公共部门特殊需要访问 |
| 第六章 | 23–31 | 完整——数据处理服务之间的切换 |
| 第七章 | 32 | 完整——第三国政府访问 |
| 第八章 | 33–36 | 仅门禁，但第 34–35 条服务于第六章时除外 |

### 跨制度门禁

| 门禁 | 参考文件 | 姿态 |
|------|----------|------|
| GDPR + ePrivacy | `references/gates/gdpr-overlay.md` | 涉及个人数据或终端设备访问时生效 |
| 《商业秘密指令》(EU) 2016/943 | `references/gates/trade-secrets-directive.md` | 主张或援引商业秘密保护时生效 |
| DMA 守门人排除 | `references/gates/dma-gatekeeper.md` | 适用于第 5 条第三方请求和第 6(2)(d) 条的继续共享 |
| 行业特别法 | `references/gates/sectoral-lex-specialis.md` | 仅警示（车辆、医疗器械、DORA、NIS2、CRA、AI 法案、eIDAS、能源、农业、电信） |
| 成员国实施法律 | `references/gates/member-state.md` | 仅警示（主管机关、争议解决、处罚） |

## 文件结构

```
eu-data-act/
├── SKILL.md                              # 入口和路由器
├── CHANGELOG.md                          # 版本历史
├── references/
│   ├── method/
│   │   ├── analysis-method.md            # 七步认知流程
│   │   └── house-style.md                # 语气、篇幅、引用、结构
│   ├── gates/
│   │   ├── gdpr-overlay.md               # 第 1(5) 条桥梁、情形 A/B、ePrivacy
│   │   ├── trade-secrets-directive.md    # TSD 阶梯、严重且不可恢复
│   │   ├── dma-gatekeeper.md             # 第 5(3) 条排除、第 6(2)(d) 条
│   │   ├── sectoral-lex-specialis.md     # 仅警示的行业目录
│   │   └── member-state.md               # 仅警示的成员国实施法律
│   ├── gotchas.md                        # 20 条编号的失败模式条目
│   └── scenarios/                        # 预先演练的角色 × 章节 × 阶段卡片
├── sources/
│   ├── regulation-2023-2854.md           # 《数据法案》逐字文本（119 条序言 + 50 个条文）
│   ├── faq-v1-4.md                       # 欧盟委员会 FAQ v1.4（2026 年 1 月 22 日，CC BY 4.0）
│   ├── digital-omnibus-amendments-tracker.md
│   ├── mcts-sccs-recommendation-pointer.md
│   ├── vehicle-data-guidance-pointer.md
│   ├── _versions.json                    # 来源溯源
│   └── _manifest.sha256                  # 来源校验和
├── scripts/
│   └── validate_sources.py               # 来源层验证器（20/20 项检查）
├── templates/                            # 起草模板
└── evals/                                # 评估夹具 + 评分
```

## 部署

### Claude Code（推荐）

将技能文件夹符号链接到 `~/.claude/skills/`：

```bash
ln -s ~/CLAUDE_PROJECTS/SKILLS/claude-skills/skills/eu-data-act ~/.claude/skills/eu-data-act
```

### Claude.ai（用户技能）

在 设置 → 个人资料 → 自定义技能 下上传整个 `eu-data-act/` 文件夹结构。

## 触发短语

- “Data Act” / “Datengesetz” / “Regulation (EU) 2023/2854”
- “Art. 4(1) request” / “Art. 5(1) third-party request” / “trade-secret handbrake”
- “cloud switching obligations” / “Chapter VI” / “Art. 25 mandatory terms”
- “Chapter V exceptional need” / “Art. 17 public-sector request”
- “Art. 13 unfair contract terms” / “Art. 32 third-country access”
- 对《数据法案》具体条文或序言段落的引用。

## 来源层验证器

在任何发布或下游符号链接之前运行：

```bash
python3 scripts/validate_sources.py --verbose
```

检查标题分类（每一段预期的序言、条文和 FAQ 问题）、指针文件存在性、清单校验和以及 `_versions.json` 结构。退出码 0 表示所有检查通过。当前状态：20/20。

## 监管依据

| 文件 | 引用 |
|------|------|
| 欧盟《数据法案》 | 法规 (EU) 2023/2854 |
| 欧盟委员会《数据法案》FAQ | v1.4（2026 年 1 月 22 日），CC BY 4.0 |
| 数字综合（Digital Omnibus）提案 | COM(2025) 833 final，2025 年 11 月 19 日（联合立法者谈判中，未通过） |
| 《商业秘密指令》 | 指令 (EU) 2016/943 |
| GDPR | 法规 (EU) 2016/679 |
| 《电子隐私指令》 | 指令 2002/58/EC |
| 《数字市场法案》 | 法规 (EU) 2022/1925 |

## 许可与免责声明

根据 **AGPL-3.0** 许可。

本技能基于欧盟《数据法案》、欧盟委员会 FAQ 及相关欧盟法律提供结构化指引。不构成法律意见。使用本技能产生的实质性交付物应由具备《数据法案》专长的合格法律顾问审阅。

> **质量保证：** 本技能随附 `evals/` 文件夹中的评估测试，我运行这些测试以核对其输出是否与预期结果一致。

---

*作者：Oliver Schmidt-Prietz — [OneZero Legal](https://onezero.legal)*
