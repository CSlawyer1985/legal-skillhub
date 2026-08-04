# 🛡️ gdpr-guard — GDPR 合规护栏

在 AI 应用输入/输出链路中实时检测 GDPR 语境下的个人数据：IBAN、UK NI、EU 电话、信用卡（Luhn）等模式，以及 Art.9 特殊类别数据（种族/基因/生物识别/健康等）和 Art.10 刑事定罪数据。按风险分级脱敏或阻断，供 Agent 主动调用。

纯本地运行，零网络请求，零动态执行。

## 安装

```bash
openclaw skill install gdpr-guard
```

## 用法

```bash
# 检测并脱敏（默认 gdpr 规则）
python3 scripts/guard.py --text "IBAN DE89370400440532013000, NI AB123456C"

# 特殊类别数据检测
python3 scripts/guard.py --text "The patient has a genetic test and a criminal record"

# 高危阻断
python3 scripts/guard.py --text "credit card 4532015112830366" --action block

# 列出规则包
python3 scripts/guard.py --list-profiles
```

## 动作

| 动作 | 行为 |
|------|------|
| `detect` | 仅检测并报告，不改动文本 |
| `mask` | 脱敏后放行（默认） |
| `block` | 命中达阈值则阻断，否则脱敏 |

## 检测范围（gdpr v1.0.0）

**结构性模式**：IBAN、UK NI、EU 电话（E.164）、信用卡（Luhn）、IPv4、MAC、邮箱。

**关键词线索**：Art.9 特殊类别（种族/政治/宗教/工会/基因/生物识别/健康/性取向）、Art.10 刑事定罪。

## 架构

```
scripts/
  guard.py          检测内核
  rules/
    gdpr.py         GDPR 规则包（自包含）
```

## 系列规划

- `pipl-guard`（通用版）— PIPL 护栏
- `pipl-guard-finance`（金融版）— PIPL 护栏（金融版）
- `gdpr-guard`（GDPR版）— 本项目

## 许可证与声明

MIT 许可证。本工具仅为防护辅助手段，不构成法律建议或合规证明，检测不保证 100% 完整。
