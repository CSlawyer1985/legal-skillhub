---
name: "skill-pour-interroger-judilibre-allison-fiorentino"
description: >-
  >本技能提供对 judilibre API 的访问。您以法语提出请求，它查询 Judilibre 数据库并返回回答。
  
  注意：本技能仅在使用了附加域名且用户输入了自己的 Judilibre 密钥时才能运行。
  
  本技能及其作者与最高法院或 Judilibre 无任何关联。
metadata:
  author: "Allison Fiorentino"
  license: "agpl-3.0"
  version: "2026-06-25"
---

# Judilibre——司法判例

本技能查询 Judilibre API（最高法院）以检索和阅读司法序列的法院判决。工作通过脚本 `scripts/judilibre_client.py` 完成，该脚本处理身份验证并返回 JSON。

## 范围——如有需要告知用户

- ✅ 涵盖：最高法院（全部分庭），以及越来越多的上诉法院和一审法院（逐步扩容）。
- ❌ 不涵盖：文本（法典、法律、法令）和行政判例（最高行政法院、行政上诉法院、行政法院）。对此，引导至 OpenLegi / Légifrance 或其他来源。

## 配置（仅一次）

脚本需要一把 PISTE 密钥和经授权的网络访问。

1. **API 密钥（KeyId 模式——推荐）。** 一把简单的 API 密钥即可：即 KeyId 模式，密钥在 HTTP 请求头中发送。脚本按此顺序读取密钥：`--key` 参数、环境变量 `JUDILIBRE_KEY_ID`，然后是 `scripts/config.json`。如果未找到密钥，脚本返回明确错误。在这种情况下，向用户索取密钥，然后从 `scripts/config.example.json` 创建 `scripts/config.json`，将密钥粘贴到 `key_id` 字段并将 `env` 设为 `prod`（或 `sandbox`）。OAuth 客户端（`client_id` / `client_secret`）在 KeyId 模式下**不**需要：将这些字段留空。

   *OAuth2 模式（高级，回退）。* 如果用户没有 KeyId 但有 `client_id` / `client_secret` 对，填写这两个字段并将 `key_id` 留空；脚本将自动获取并缓存 Bearer 令牌。

   ⚠️ `scripts/config.json` 以明文包含密钥：绝不要显示或分享它。

2. **网络。** 出站调用发往 `*.piste.gouv.fr`。如果脚本返回「无法连接到 piste.gouv.fr」或「网络域名未授权」错误，告知用户必须在 Claude 代码执行的网络设置中授权该域名：
   - `api.piste.gouv.fr`——**必需**（生产环境，KeyId 模式）；
   - `sandbox-api.piste.gouv.fr`——仅用于沙箱；
   - `oauth.piste.gouv.fr` 和 `sandbox-oauth.piste.gouv.fr`——仅用于 OAuth2 模式。

验证一切正常：`python3 scripts/judilibre_client.py test`。
此命令执行一次真实的认证检索（而非简单的健康检查），因此成功即确认密钥被接受。

## 用法

必要时安装依赖：`pip install requests`（已存在则静默）。

### 检索

```bash
python3 scripts/judilibre_client.py search "période d'essai rupture abusive" \
  --chamber soc --page-size 10
```

可用过滤器（全部可选）。类别过滤器接受多个值（用空格分隔）：
`--chamber`（soc、civ1、civ2、civ3、comm、crim……）、`--jurisdiction`（cc、ca、tj）、
`--type`、`--theme`、`--publication`、`--solution`、`--field`、
`--operator`（and|or|exact）、`--date-start AAAA-MM-JJ`、`--date-end AAAA-MM-JJ`、
`--page`、`--page-size`（最大 50）、`--sort`（score|date）、`--order`（asc|desc）。

多值示例：`--chamber soc comm` 在两个分庭中检索。

输出为 JSON。每个结果的有用字段：`id`、`number`/`numbers`、
`jurisdiction`、`chamber`、`formation`、`decision_date`、`solution`、`ecli`、
`publication`、`summary`、`themes`、`score`，以及 `url`（courdecassation.fr 上决定的直接公开链接，由脚本添加）。

### 阅读完整决定

取用搜索结果中的 `id`：

```bash
python3 scripts/judilibre_client.py decision <id>
```

返回全文（`text`）、公开链接（`url`）和分区（`zones`：引言、案情陈述、理由、论证、判项、附件）。

### 了解某过滤器的取值

```bash
python3 scripts/judilibre_client.py taxonomy chamber
```

## 向用户呈现结果——始终如此

检索后，不要原样输出原始 JSON。呈现一份按相关性排序的清晰清单，每项决定注明：司法机构和分庭、**上诉编号**、日期、裁判结果（撤销、驳回……）、公布级别（P、B……）、可用时的简短摘要，以及指向文本的**公开链接**（`url`）。保留 `id` 以便按请求打开全文。提议显示完整判决或细化检索（分庭、时期）。

始终提醒这些仅是司法序列的决定。

## 出现错误时

脚本返回明确的 JSON 消息（`error` + `fix`）。将其简单转达给用户：
- 密钥缺失 → 索取密钥并保存在 `scripts/config.json` 中；
- 401 → 密钥错误或环境错误（sandbox 与 prod）；
- 403 → Judilibre CGU 未接受或 API 未挂靠到 PISTE 应用程序；
- 429 / 5xx → 达到配额或 API 不可用；脚本自动重试，否则稍候再运行；
- 无法连接 / 域名未授权 → 在网络设置中授权 `api.piste.gouv.fr`。
