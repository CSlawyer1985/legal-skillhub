---
name: legal-verify
description: 校验文本内容中的法律引用是否正确：自动抽取文中引用的法规/法条和案例/案号，与权威来源比对语义一致性，核验法规时效性，输出"一致/不一致/未命中"判定及权威原文。当用户要求复核、校验、核查法律引用准确性，询问法律文本是否存在幻觉，或请求AI帮助撰写包含法律引用的法律文书时，视为必须启用本skill
metadata:
  author: legal-verify 项目
  version: 1.0.0
---

# 法律文本抽取/核验 Skill

在生成或核验正式法律文本时，调用 `hall_detect` 抽取引用并按权威来源核验，避免法规、法条、案例和案号幻觉。

普通法律概念解释、非正式讨论、没有明确引用核验需求的问答，不必自动调用本 Skill。

## 触发场景

- 用户要求“复核、核查、核验、法律幻觉检测、verify legal citation、fact-check legal”。
- 即将输出正式法律意见、诉讼文书、合规审查结论，且文本包含法规/法条/案号引用。
- 用户提供 `doc` / `docx` 时，先提取纯文本，再调用接口；接口只接收 `text`。

## API Key

- 每次调用前检查 `YUANDIAN_API_KEY` 是否存在：`python -c "import os; print('已配置' if os.environ.get('YUANDIAN_API_KEY') else '未配置')"`。
- 若未配置，引导用户在本机自行配置，不要要求用户在对话中粘贴完整 Key。
- 可写入与本 `SKILL.md` 同目录的 `.env`，但调用前必须显式加载；仅写入文件不会自动生效。
- `.env` 不得提交进 git。

## 接口调用

接口：`POST https://open.chineselaw.com/open/hall_detect`

请求要求：

- Header: `Content-Type: application/json; charset=utf-8`
- Header: `Accept: application/json`
- Header: `X-API-Key: ${YUANDIAN_API_KEY}`
- Body: `{ "text": "待核验/抽取的法律文本" }`

调用约定：

1. 始终把请求体写入 `body.json`，避免长中文文本在命令行中转义失败。
2. 请求结果保存为 `response.json`，同时记录 `HTTP_STATUS`。
3. 若使用 `.env`，先加载 `YUANDIAN_API_KEY` 再请求。
4. 已验证接口使用 `X-API-Key` 鉴权；若改用 `Authorization: Bearer ...`，服务端会返回 `401 API Key 缺失`。
5. 若 `HTTP_STATUS` 非 2xx 或 `response.json` 不可解析，不编造法规内容；说明失败并建议检查网络、Key 或配额。

## 响应字段

成功响应可能没有顶层 `success`。只要 `HTTP_STATUS` 为 2xx 且未出现 `success === false`，并返回 `regulations` / `cases` / `highlighted_text` / `request_id` 等业务字段，即按成功体处理。

重点字段：

- 顶层：`request_id`、`highlighted_text`、`chat_model`、`semantic_compare_error`
- `regulations[]`：`name`、`clause`、`content`、`extract_reg_id`、`think_tank_content`、`url`、`validity_status`、`publish_date`、`implement_date`、`document_number`、`semantic_compare.结论`、`semantic_compare.语义相似度`、`semantic_compare.说明`、`semantic_compare.要点`
- `cases[]`：`case_number` / `案号`、`content`、`name`、`court`、`judgment_date`、`basic_facts`、`judgment_key_points`、`judgment_result`、`think_tank_content`、`url`

若某次响应未出现 `law_exists`、`source_no_specific_clause`、`think_tank_clause_missing` 等可选字段，跳过对应分支，不据此反推。

## 数据示例

```json
{
  "regulations": [
    {
      "name": "《中华人民共和国民法典》",
      "clause": "第九百七十九条",
      "content": "无因管理费用可依据《中华人民共和国民法典》第九百七十九条请求偿还。",
      "extract_reg_id": "f6e139eb-61d4-4c78-8f98-6eb6b184bed9",
      "think_tank_content": "管理人没有法定的或者约定的义务，为避免他人利益受损失而管理他人事务的，可以请求受益人偿还必要费用……",
      "validity_status": "现行有效",
      "semantic_compare": {
        "结论": "不一致",
        "语义相似度": 40.0,
        "说明": "用户表述遗漏核心构成要件。",
        "要点": ["遗漏无义务", "遗漏为避免他人利益受损失"]
      }
    },
    {
      "name": "《中华人民共和国合同法》",
      "clause": "第五十二条",
      "validity_status": "失效",
      "semantic_compare": { "结论": "不一致", "语义相似度": 30.0 }
    }
  ],
  "cases": [
    {
      "case_number": "（2021）沪0115民初888888号",
      "content": "参考（2021）沪0115民初888888号判决。",
      "name": "",
      "court": "",
      "judgment_date": ""
    }
  ],
  "highlighted_text": "参考<span class=\"missing-ref\">（2021）沪0115民初888888号</span>判决。",
  "chat_model": "glm-5",
  "request_id": "req_1778564620129_96d6df29"
}
```

## 判定规则

1. 全局失败：若 JSON 含 `success === false`，立即中止生成/改写，向用户返回 `request_id`、`error_code`、`message`。
2. 法规时效：`validity_status` 为“失效”“已被修改”等时，优先标为“时效风险”，不得当作现行有效依据；若同时语义不一致，写为“时效风险 + 语义不一致”。
3. 法规语义：`semantic_compare.结论 === "不一致"` 时，以 `think_tank_content` 为准，展示 `说明` / `要点` / `语义相似度`，并给出建议修订句；`think_tank_content` 为空时不得臆造条文。
4. 案例核验：若案例缺少 `think_tank_content` / `url`，且法院、日期、案情、裁判要点等字段为空，判为“案号未命中或高度可疑”。
5. 高亮文本：`highlighted_text` 是 HTML，只用于辅助定位；遇到 `missing-ref` 时转述“该引用未命中”，不要粘贴原始 HTML 当依据。
6. `chat_model` 仅在用户询问“用什么模型核验”时回答，不参与准确性判定。

## 输出格式

用户要求复核时，优先用表格：

`类型` | `用户原文摘录` | `判定` | `依据` | `权威依据` | `链接` | `request_id` | `extract_reg_id`

输出要求：

- `判定` 使用：准确 / 时效风险 / 语义不一致 / 时效风险 + 语义不一致 / 未命中。
- `权威依据` 只来自 `think_tank_content` 或权威案情字段；无则写“无”。
- 表格后补充本次 `request_id`；默认不主动展开 `chat_model`。
- 错误响应只输出 `error_code`、`message`、`request_id`，不得臆测法规表格内容。

## 自检模式

当模型即将输出含法律引用的正式文本：

- 可用 `think_tank_content` 替换或收紧表述。
- 对失效法规标注“已失效/已被修改”，并建议替换为现行依据。
- 删除或改写无法在权威库验证的案号。
- 禁止在无权威正文时编造法条全文，禁止把空权威案例当真实案例引用。
