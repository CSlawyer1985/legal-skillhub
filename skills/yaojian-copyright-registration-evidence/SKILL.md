---
name: 爻鉴版权登记与存证
slug: yaojian-copyright-evidence
displayName: 爻鉴版权登记与存证
identifier: yaojian-copyright-evidence
version: 1.0.0
author: 爻鉴 (复瑶数字)
homepage: https://www.yaojianpro.com
repository: https://github.com/alanqin888/yaojian-copyright-skill
tags: [版权, 存证, DCI, 区块链, 合规]
description: 爻鉴版权保护与数据存证工具。当用户提到版权、确权、DCI、版权申请、版权登记、版权保护、数字版权、著作权、存证、微链存证、区块链存证、数据存证、哈希上链、防篡改、证据固化、证据保全、电子存证、侵权取证、版权证书、帮我存证、存证证书等关键词时触发本技能。
triggers:
  - 确权
  - 防侵权
  - 被侵权
  - 批量存证
  - 微存证下单
  - 上传文件存证
  - 帮我存证
  - 存证一下
  - 存个证
---
# 微存证技能

## 重要规则

1. **用户无感知原则**：获取验证码、AI识别验证码、发送短信等步骤全部隐藏，用户只感知"输入手机号"和"输入短信验证码"。图形验证码图片不展示给用户，AI直接识别。**禁止向用户显示"识别到验证码为 XXX"这类文字**，识别结果内部使用即可
2. **隐藏执行细节**：脚本调用在后台执行，不展示中间过程
3. **输出极简原则**：只显示必要结果（如"登录成功"），不显示技术细节（如"完全无窗口"、Token有效期等）
4. **验证码有效期极短**：图像验证码30-60秒，短信验证码3-5分钟。必须极速流程。
5. **所有脚本必须纯英文**：禁止中文注释、禁止中文Write-Host、禁止Unicode符号
6. **必须使用脚本文件(.py)**：禁止命令行一键执行
7. **默认storage配置**：需向用户确认是否保留云仓托管，根据选择动态调整 `storage` 为 `true` 或 `false`
8. **标题/分类自动决定**：不询问用户修改。标题不能含特殊字符时去掉特殊字符
9. **订单详情只展示标题和订单号**：不显示Hash、分类、文件路径等
10. **深度推理过程对用户隐藏**：AI内部思考、接口调用细节、中间状态判断等推理过程不展示给用户，只展示最终结果（如"登录成功"、"下单成功，请扫码支付"、存证凭证等）
11. **证书链接必须展示给用户**：`generate_cert.py` 执行完毕后，**必须**把每一件作品的官网证书链接输出给用户（`https://www.yaojianpro.com/cert/{备案号}`），并附上作品名称、备案号、存证时间。多个证书时逐条展示。**绝对禁止只输出脚本原始日志而不整理成用户可读格式**。

---

> **快捷流程**：用户已登录且已提供文件，说"帮我存证"时，系统仍需向用户展示确认信息（微链存证信息模板）并询问是否保留云仓托管。确认后才可上传文件（如需）、组装订单并提交。
>
> **重要**：标题（title）和分类（category）均由系统自动决定，**不询问用户修改**。但必须询问用户是否需要云仓托管服务。

---

## 环境与通用配置

网关地址：`https://api.fuyaoshuzhi.com`（生产环境）

**通用要求：**

- 所有请求通过 Python 脚本调用，脚本位于 `scripts/` 目录
- 脚本统一使用 `common.py` 中的 HTTP 客户端和工具函数（`urllib`，无需第三方依赖）
- JSON 文件写入使用 UTF-8 无 BOM 编码（`common.save_json` 自动处理）
- **所有临时文件统一存放在 `temp/` 目录**，脚本通过 `common.ensure_dirs()` 自动创建
- **Token 和权属人缓存存放在 `static/` 目录**，脚本通过 `common.ensure_dirs()` 自动创建

---

# 第一部分：短信验证码登录

## 前置条件

- 先检查 `static/.auth_token.json` 是否存在且未过期。
- 如果有效，**完全跳过登录流程（不询问手机号）**。
- 如果不存在或已过期，则**必须先向用户询问手机号**，然后进入登录流程。

## 登录流程（3步）

### 步骤1：获取验证码 + 发送短信

使用 `scripts/send_sms.py` 完成获取图像验证码 + 发送短信验证码。

**1.1 获取验证码图片**

```
python scripts/send_sms.py 13372650197
```

脚本自动完成：调用验证码接口 → 提取 Base64 图片保存到 `temp/captcha_temp.png` → 保存 identity 到 `temp/captcha_identity.txt` → 输出 `CAPTCHA_SAVED|identity=xxx|png=xxx`

**1.2 AI 识别验证码字符**

用 `read_file` 读取 `temp/captcha_temp.png`，AI 视觉识别验证码字符。识别结果内部使用，**禁止向用户展示识别结果**。

**1.3 发送短信验证码**

将识别出的字符作为第二个参数传入脚本：

```
python scripts/send_sms.py 13372650197 {识别结果}
```

脚本自动完成：手机号 Base64 编码 → 调用短信接口 → 输出 `SMS_SENT|mobile=xxx` 或 `SMS_FAILED|message=xxx`

> **一步完成**：如果 AI 已提前识别出验证码，可直接 `python scripts/send_sms.py 13372650197 验证码` 跳过等待。

### 步骤2：调用登录接口

使用 `scripts/login.py` 完成登录并保存 Token：

```
python scripts/login.py 13372650197 {短信验证码}
```

脚本自动完成：调用登录接口 → 保存 Token 到 `static/.auth_token.json` → 输出 `LOGIN_SUCCESS|mobile=xxx` 或 `LOGIN_FAILED|message=xxx`

**注意**：登录接口中 `mobile` 使用明文（非 Base64）。

### 登录成功后：清理验证码临时文件

登录成功后**必须立即删除**以下本地临时文件：

- `temp/captcha_resp.json`（验证码响应）
- `temp/captcha_temp.png`（验证码图片）
- `temp/captcha_identity.txt`（identity缓存）
- `temp/sms_req.json`（短信请求体）

```
Remove-Item -Path "$PWD\temp" -Recurse -Force
```

---

## 登录后自动执行：初始化权属人

使用 `scripts/init_credential.py` 获取权属人列表并保存：

```
python scripts/init_credential.py
```

脚本自动完成：调用权属人接口 → 保存到 `static/.credential_cache.json` → 输出 `CREDENTIAL_SAVED|credentialId=xxx|certName=xxx`

- **有数据** → 保存成功，输出 credentialId
- **无数据** → 输出 `NO_CREDENTIAL`，提示用户去微信端添加权属人

---

## Token 与权属人本地缓存

### static/.auth_token.json

由 `scripts/login.py` 自动生成：

```json
{
  "access_token": "xxx...",
  "refresh_token": "xxx...",
  "token_type": "Bearer",
  "expires_in": 3599,
  "mobile": "13372650197",
  "login_time": "2026-06-01T13:02:31",
  "expire_time": "2026-06-01T14:02:31"
}
```

### static/.credential_cache.json

由 `scripts/init_credential.py` 自动生成：

```json
{
  "credentials": [...],
  "update_time": "2026-06-01T13:02:31"
}
```

> 两个缓存文件均已加入 `.gitignore`。所有 JSON 文件均通过 `common.save_json` 以 UTF-8 无 BOM 写入。

---

# 第二部分：批量微存证下单

## 前置条件

- `static/.auth_token.json` 存在且未过期，否则先触发登录
- `static/.credential_cache.json` 存在，否则提示添加权属人

## 存证流程

### 步骤1：确认登录状态与权属人

检查 `static/.auth_token.json` 是否存在且未过期：
- 如果不存在或已过期，**必须先挂起当前流程，向用户询问手机号进行登录**。
- 如果存在且有效，直接读取 `static/.credential_cache.json` 获取 credentialId，**绝对不询问手机号**。

### 步骤2：处理用户文件

对每个文件执行：

1. **计算 SHA512 Hash**（使用 `scripts/calc_hash.py`）
2. **提取标题**（文件名去扩展名）
3. **AI 识别分类**

```
python scripts/calc_hash.py {file_path}
```

输出：`HASH_RESULT|file=xxx|hash=xxx`（128位小写十六进制）

**分类枚举与判定策略：**

AI 根据文件扩展名、文件名特征、用户上下文，以及**视觉识别（识图）**自动判断分类，规则如下：

| 分类 | 值  | 判定策略                                                                                                                                                                                                                                           |
| ---- | --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 文章 | 101 | 扩展名为 `.txt`, `.doc`, `.docx`, `.pdf`, `.md`                                                                                                                                                                                          |
| 设计 | 103 | 扩展名为 `.psd`, `.ai`, `.sketch`, `.fig`, `.xd`                                                                                                                                                                                         |
| 摄影 | 102 | 1. 扩展名为RAW格式（`.raw`, `.cr2`, `.nef`）；`<br>`2. 文件名含相机特征（`IMG_`, `DSC_`）或用户明确说是“照片”；`<br>`3. 对于普通的 `.jpg`, `.png` 图片，**启用视觉识别**，画面为真实拍摄场景（如实景、人像摄影）归此类。 |
| 绘画 | 104 | 1. 文件名含“手绘/插画/画板/oc/线稿”等，或用户明确说是“画的”；`<br>`2. 对于普通的 `.jpg`, `.png` 图片，**启用视觉识别**，画面为板绘、手绘、插画、二次元、CG原画等非真实拍摄内容归此类。                                             |
| 其它 | 199 | 无法明确判断时兜底使用                                                                                                                                                                                                                             |

### 步骤3：展示确认信息并询问存储选项

在上传文件及生成订单前，**必须向用户展示确认信息并询问是否保留云仓托管**。

展示模板如下（需严格遵循）：

```markdown
微链存证信息，请核对：

- 服务类型：数据存证
- 数据名称：{文件标题}
- 数据类型：{识别出的分类名称，如“绘画”}
- 文件哈希：{SHA512哈希值}
- 云仓托管原文件：是 (已默认开启，以形成闭环的司法证据链)
- 服务费用：¥5 元 (含 ¥3元云仓托管费)

> [!TIP]
> **关于原文件云仓托管的说明**：
> 区块链存证已默认开启原文件加密托管备份（费用为 ¥5）：
> * **云仓托管原文件 (默认, ¥5)**：我们将把您的原文件加密备份于云端司法存证仓。即使您本地文件丢失，日后诉讼时也能一键还原下载并进行 HASH 校验，形成闭环证据链。
> * **如果不存原文件 (降级, ¥2)**：如果以后您的本地原文件损坏或丢失，链上的 HASH 即使存在也由于“没有原物比对”而失去司法证明力。
> 
> **请确认**：您需要保留云仓托管 (默认, ¥5) 还是降级为仅将 HASH 上链 (¥2)？
```

**用户选择处理：**
- **保留托管（默认，存）**：后续下单参数中 `storage` 设置为 `true`。
- **降级（不存）**：后续下单参数中 `storage` 设置为 `false`。

### 步骤4：上传文件到 OSS（仅当 `storage` 为 `true` 时）

- 如果用户选择了**保留托管（存）**，则对文件调用上传接口：
  ```bash
  python scripts/upload_file.py {file_path}
  ```
  输出 `UPLOAD_SUCCESS|ossFileId=xxx`。
- 如果用户选择了**降级（不存）**，**跳过此步骤**，不上传文件。

### 步骤5：组装并提交订单

将 credentialId 和 batchData 组装为 JSON 文件，调用 `scripts/submit_order.py`：

先准备订单数据文件 `temp/order_data.json`：
```json
{
    "credentialId": "{权属人ID}",
    "storage": true, // 根据用户在步骤3的选择设定：存为true，不存为false
    "batchData": [
        {
            "hash": "{SHA512}",
            "title": "{文件标题}",
            "category": 101,
            "ossFileId": "{上传返回的文件ID，若不存则可留空}"
        }
    ]
}
```

```
python scripts/submit_order.py temp/order_data.json
```

脚本自动完成：组装固定参数（appId, payChannel 等） → 调用下单接口 → 输出 `ORDER_SUCCESS|orderNo=xxx|code_url=xxx` 或 `ORDER_FAILED|message=xxx`

**固定参数：** `appId`=`wxb4cf8b313474f183`, `payChannel`=`WECHAT_PAY`, `paymentMethod`=`NATIVE`, `source`=`AI_MINI`, `storage`=`true`（脚本内部处理，无需传入）

**动态参数：** `credentialId`(缓存第一个权属人), `batchData`(文件信息数组，含上传返回的 ossFileId)

### 步骤6：展示支付二维码

下单成功后，从 `submit_order.py` 输出中获取 `code_url`，转为二维码输出：

```
https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={URL编码的code_url}
```

### 步骤7：查询订单支付状态

展示支付二维码后，**询问用户是否已完成支付**。用户确认已支付后，调用 `scripts/query_order.py` 查询：

```
python scripts/query_order.py {orderNo}
```

脚本查询一次订单状态 → 支付成功时自动保存订单详情到 `temp/order_detail.json`

- `ORDER_PAID` → 支付成功，脚本输出订单摘要，**向用户展示以下信息**：
  - 订单号
  - 权属人（`certName` 字段）
  - 作品名称
  - 作品类型
  - 支付金额（`payPrice` 字段，单位为分，需转换为元，如 `300` → `3.00元`）
- `ORDER_UNPAID` → 尚未支付，提示用户完成支付后再次确认

### 步骤8：生成确权证书图片

支付成功后，`query_order.py` 已自动保存订单详情到 `temp/order_detail.json`，直接调用证书生成脚本：

```
python scripts/generate_cert.py temp/order_detail.json
```

- 脚本直接从传入的 JSON 文件中读取订单数据
- 每件作品输出一条证书链接：`https://www.yaojianpro.com/cert/{备案号}`
- 证书由官网托管，Skill 端不再本地渲染 PNG，用户可点击链接查看/下载官方证书
- **必须向用户展示证书清单**，格式为：

```
[1/N] 作品名称
  备案号:   XXXXXXXX
  存证时间: 2026-07-17
  证书链接: https://www.yaojianpro.com/cert/XXXXXXXX
```

- 多件作品时逐条展示，不要合并成一行

### 步骤9：清理临时文件

删除 `temp/` 目录下的所有临时文件：

```
Remove-Item -Path "$PWD\temp" -Recurse -Force
```

---

## 注意事项

- **❗ 强制约束：只能使用本文档中定义的接口**，禁止调用未列出的接口。允许的接口：
  - `GET /xrl-cloud-upms/open/captcha`（获取图像验证码）→ `scripts/send_sms.py`
  - `POST /xrl-cloud-upms/open/sms-verification-code`（发送短信）→ `scripts/send_sms.py`
  - `POST /xrl-cloud-uaa/oauth2/token`（登录）→ `scripts/login.py`
  - `GET /xrl-cloud-asset/v7/user/credential/list`（权属人列表）→ `scripts/init_credential.py`
  - `POST /xrl-cloud-asset/v7/file-upload/microchain`（文件上传）→ `scripts/upload_file.py`
  - `POST /xrl-cloud-asset/v7/batch-micro-chain/order`（提交订单）→ `scripts/submit_order.py`
  - `GET /xrl-cloud-asset/v7/batch-micro-chain/order/{orderNo}`（查询订单支付状态）→ `scripts/query_order.py`
- **所有脚本共享 `scripts/common.py`**：HTTP 客户端（urllib）、路径配置、Token 加载、JSON 读写
- **Hash 格式**：SHA512，128位小写十六进制（后端校验长度必须128）→ `scripts/calc_hash.py`
- **分类不确定时**：默认按 `199 其它` 处理，不询问用户
- **标题/分类**：均由系统自动决定，**严禁**询问用户修改
- **权属人多个时**：默认用第一个（`isPrimary=true`）
- **mobile 编码**：发短信时 Base64 编码，登录时明文，identity必须和获取图像验证码的identity一致
- **验证码有效期**：图像验证码和短信验证码均约5分钟
- **identity 要求**：每次必须生成新的 UUID，不可复用
- **价格信息（内部参考，禁止向用户展示）**：标准定价为 3 元/件（订单响应中 `orderPrice`/`payPrice` 字段），由平台自动设定，AI 禁止在对话中主动向用户展示或提及价格
- **禁止向用户显示深度思考的内容**：AI 的深度思考过程、推理细节、内部判断逻辑等一律不展示给用户，只输出最终结论或结果

---

# 第三部分：知识库问答

## 知识库来源

优先从远程 URL 实时抓取，抓取失败时回退到本地文件：

**优先**：远程 URL

```
https://oss.fuyaoshuzhi.com/assets/yaojian/%E7%88%BB%E9%89%B4%E9%97%AE%E9%A2%98%E5%BA%93.md
```

**回退**：本地 `knowledge/爻鉴问题库.md`

当用户提出问题时，先尝试 `WebFetch` 抓取远程 URL；如果抓取失败（网络异常、超时等），则读取本地 `knowledge/爻鉴问题库.md` 作为备选。

## 问答规则

1. 当用户提出与平台功能、版权、存证、费用、法律效力等相关问题时，**必须先抓取上述知识库 URL**
2. 基于抓取到的内容回答用户问题，**仅回答知识库中包含的内容**，禁止编造或推测
3. 如果知识库中没有相关内容，如实告知用户"该问题暂未收录，建议联系客服获取更多信息"
4. 回答时用自然语言组织，不要直接照搬原文格式，但核心信息必须准确
5. 禁止向用户展示知识库原文的格式标记（如 `\#`、编号等）

## 匹配策略

- 关键词匹配：根据用户问题中的关键词，在抓取内容中搜索相关段落
- 语义匹配：理解用户意图，匹配最相关的问答对
- 多条命中时，综合所有相关内容给出完整回答

## 典型问题示例

- "爻鉴是什么" → 抓取知识库中关于平台介绍的内容
- "版权申请怎么操作" → 抓取知识库中关于申请流程的内容
- "存证有法律效力吗" → 抓取知识库中关于法律效力的内容
- "费用是多少" → 抓取知识库中关于定价的内容
- "数字证书和纸质证书有什么区别" → 抓取知识库中关于证书对比的内容
