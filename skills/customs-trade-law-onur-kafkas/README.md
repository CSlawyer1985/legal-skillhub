# customs-trade-law

一个用于美国海关归类与贸易法研究的 Claude Code Agent Skill。

它帮助准备可供律师审核的草稿工作成果，涵盖 HTSUS 归类、CROSS 裁决研究、CIT/CAFC 判决简报、关税汇编、原产地分析、第 99 章筛查、AD/CVD 问题识别、PGA 审查以及 UFLPA 强迫劳动核查。

> 仅为草稿工作成果。不构成法律意见。在进口交易中使用前，输出必须经美国执业律师或持证报关行审核。

## 安装

```text
/plugin marketplace add onurkafk/customs-trade-law
/plugin install customs-trade-law@onurkafk
```

安装后重启 Claude Code 或开始新会话。

本地安装的替代方案：

```sh
git clone https://github.com/onurkafk/customs-trade-law.git ~/.claude/skills/customs-trade-law
```

## 使用

无需斜杠命令。自然提问即可：

```text
Classify a Bluetooth keyboard from China.
Find CROSS rulings for ceramic mugs under heading 6912.
Calculate duty for HTS 8471.30.0100 from Taiwan.
Check whether Section 301 applies to this product.
Run an import compliance review for medical devices from Vietnam.
```

## 它处理什么

- 使用 GRI 1-6 和美国附加规则进行 HTSUS 归类
- 带 HQ/NY 权威加权的 CROSS 裁决研究
- 从检索到的意见书文本进行 CIT 和 CAFC 判决分析
- 关税汇编：普通、特别、第 99 章、AD/CVD、MPF、HMF
- 原产地、标记、FTA 资格和 TAA 审查
- PGA 和 UFLPA 进口合规风险筛查

## 工作原理

该技能强制执行美国海关权威层级：

```text
HTSUS legal text > CAFC > CIT > CBP HQ > CBP NY > agency guidance > secondary sources
```

它还要求：

- 在进行层级敏感分析前，通过 Data.gov 发现现行 HTS JSON
- 来源标注：`Verified`、`Retrieved`、`Identified`、`Unverified`
- 重大法律结论的证据台账
- 对缺失事实、冲突、过时来源和高风险歧义的明确人工审查标记

核心操作规程见 [`SKILL.md`](./SKILL.md)。完整示例见 [`examples/output.md`](./examples/output.md)。

## 权限

该技能检索实时政府来源。在 `~/.claude/settings.local.json` 或项目设置中添加这些 `WebFetch` 权限：

```json
{
  "permissions": {
    "allow": [
      "WebFetch(hts.usitc.gov/*)",
      "WebFetch(www.usitc.gov/*)",
      "WebFetch(catalog.data.gov/*)",
      "WebFetch(search.uscourts.gov/*)",
      "WebFetch(www.cit.uscourts.gov/*)",
      "WebFetch(law.justia.com/*)",
      "WebFetch(www.federalregister.gov/*)",
      "WebFetch(rulings.cbp.gov/*)",
      "WebFetch(ustr.gov/*)",
      "WebFetch(www.trade.gov/*)",
      "WebFetch(www.cbp.gov/*)"
    ]
  }
}
```

## 仓库

```text
customs-trade-law/
├── SKILL.md            # skill manifest and workflow router
├── references/         # methodology, doctrine, source maps, disclaimers
├── templates/          # output templates
├── scripts/            # HTS, CIT, and hierarchy helpers
├── examples/           # worked examples
├── evals/              # evaluation scenarios
├── CHANGELOG.md
└── LICENSE
```

## 版本

当前技能版本：`1.0.2`

发布说明见 [`CHANGELOG.md`](./CHANGELOG.md)。

## 许可证

AGPL-3.0。见 [`LICENSE`](./LICENSE)。
