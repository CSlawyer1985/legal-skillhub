# 法律术语中英互译 Skill

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Terms: 34,000+](https://img.shields.io/badge/Terms-34,000+-blue.svg)](references/glossary.csv)

面向中国大陆法律实务的中英双语法律术语翻译工具。基于香港律政司(DOJ)双语法律词汇表清洗整理的 ~34,000 条通用法律术语，加上 ~950 条中国大陆法律体系特色术语。

## ✨ 特色

- 📚 **34,000+ 通用法律术语** — 涵盖民法、刑法、商法、诉讼法、宪法行政法、国际法
- 🇨🇳 **320+ 大陆特色术语** — PRC 民法典、刑法、公司法等核心法律官方英译
- 🏛️ **拉丁法律术语** — ~430 条拉丁术语均附双语注释
- 🔍 **智能搜索** — 精确匹配 → 子串搜索 → 模糊匹配，自动路由
- 🏷️ **领域分类** — 六大法律领域标注，支持按领域筛选
- 📄 **多格式输出** — 文本、JSON、CSV 三种输出格式
- 🔄 **可复现清洗** — 从原始 DOJ 数据到清洗结果的完整 pipeline

## 📦 安装

### 方式一：ZCode Skill（推荐）

```bash
# 复制到 ZCode skill 目录
cp -r legal-translation/ ~/.agents/skills/legal-translation/

# 或在项目中使用
cp -r legal-translation/ your-project/.agents/skills/legal-translation/
```

ZCode 会自动发现并加载该 skill，当你询问法律术语翻译时自动触发。

### 方式二：独立脚本

也可以直接使用脚本（无需 ZCode）：

```bash
git clone https://github.com/yourusername/legal-translation.git
cd legal-translation
pip install -r requirements.txt  # 无需额外依赖，仅需 Python 3.8+
```

## 🚀 快速使用

### 基本查询

```bash
# 中文 → 英文
python scripts/lookup.py -q "不可抗力"

# 英文 → 中文
python scripts/lookup.py -q "force majeure"

# JSON 格式输出（方便程序调用）
python scripts/lookup.py -q "tort" --format json
```

### 高级查询

```bash
# 模糊搜索
python scripts/lookup.py -q "合同违约" --fuzzy -n 10

# 按领域筛选
python scripts/lookup.py -q "证据" --domain 诉讼法

# 精确匹配
python scripts/lookup.py -q "物权" --exact

# 查询大陆法律术语
python scripts/lookup.py -q "用益物权" -g references/mainland_terms.csv

# 限制返回数量
python scripts/lookup.py -q "party" -n 5
```

### 中国大陆法律特有概念

```bash
# 大陆特色术语已在 mainland_terms.csv 中
python scripts/lookup.py -q "善意取得"
python scripts/lookup.py -q "人民调解"
python scripts/lookup.py -q "审判委员会"
python scripts/lookup.py -q "指导性案例"
```

## 📊 数据规模

| 文件 | 条目数 | 内容 |
|------|--------|------|
| `glossary.csv` | 33,996 | 通用法律术语（清洗自 DOJ 双语词汇表） |
| `mainland_terms.csv` | 951 | 中国大陆法律体系特色术语 |

### 领域分布

| 领域 | 条目数 | 占比 |
|------|--------|------|
| 通用 | ~31,000 | 90% |
| 诉讼法 | ~960 | 2.8% |
| 刑法 | ~630 | 1.9% |
| 商法 | ~600 | 1.8% |
| 民法 | ~560 | 1.6% |
| 宪法行政法 | ~285 | 0.8% |
| 国际法 | ~263 | 0.8% |

> 注：大部分通用术语适用于多个领域，标记为"通用"。

## 🛠️ 数据清洗

从原始 DOJ CSV（78,912 行）清洗：

```bash
# 1. 解压原始文件
python -c "import gzip,shutil; shutil.copyfileobj(gzip.open('doj_glossary.csv.gz','rb'), open('doj_glossary.csv','wb'))"

# 2. 运行清洗
python scripts/clean_glossary.py doj_glossary.csv references/glossary.csv
```

清洗策略（温和）：
- ✅ 保留通用法律词典和大陆法律来源
- ❌ 移除香港独有机构/角色/概念
- ❌ 移除报告/咨询文件来源
- ❌ 移除模板占位符条目
- 🔄 去重：来源优先级 词典 > 条例 > 其他

## 🔗 配合 PKULaw MCP 工具

本 Skill 与北大法宝 MCP 工具配合使用效果更佳：

1. **术语查询** → 使用本 Skill 查找中英对应
2. **法条验证** → 使用 `mcp__pkulaw-law-search` 验证术语在法条中的实际用法
3. **案例参考** → 使用 `mcp__pkulaw-case-search` 查看术语在判决中的使用

## 📖 数据来源

- **香港律政司双语法律词汇表** — 英文法律词汇的主要来源（已清洗去香港专属内容）
- **中华人民共和国民法典** — 大陆民法术语
- **中华人民共和国刑法** — 大陆刑法术语
- **中华人民共和国公司法** — 大陆商法术语
- **NPC 英文版法律译本** — 官方翻译标准

详见 [references/source-guide.md](references/source-guide.md)

## ⚠️ 使用注意事项

1. **普通法 vs 大陆法**：主体术语库源自香港普通法体系，部分翻译风格偏向英式 / common law 表达
2. **大陆法律翻译**：中国大陆法律特有概念请优先使用 `mainland_terms.csv`
3. **翻译一致性**：同一中文术语在不同语境下可能有不同英文对应，本工具列出所有选项
4. **非官方翻译**：除 mainland_terms.csv 中标注为官方翻译的术语外，其他翻译仅供参考

## 🗺️ 路线图

- [x] v1.0 — 数据清洗 + 大陆术语精选 + ZCode Skill
- [ ] v1.1 — 改进领域分类算法（降低"通用"占比）
- [ ] v1.2 — 在线抓取 NPC/CLT 最新术语
- [ ] v2.0 — 接入 pkulaw MCP 做实时法条验证
- [ ] v2.1 — LLM 辅助的上下文翻译建议
- [ ] v3.0 — Web 界面、社区贡献机制

## 📄 许可

MIT License — 详见 [LICENSE](LICENSE)

术语数据的原始来源（香港 DOJ、NPC 等）各有其使用条款，请在使用时自行确认合规性。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！特别是：

- 补充大陆法律术语
- 改进领域分类
- 报告翻译错误
- 添加更多数据来源
