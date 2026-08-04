# 木瓜法律咨询

## 简介
对接木瓜法律API，提供专业的法律咨询、案件要素提取和案件完整分析能力。

## 功能
- **法律咨询**：针对用户法律问题提供专业解答
- **案件要素提取**：从文本或文件中自动提取案件关键要素
- **案件完整分析**：基于当事人信息、案由、事实和诉求生成完整案件分析报告

## HTTP 端点（必须严格一致）
`base_url` 末尾带 `/`（默认 `https://api.test.mugua.muguafabao.com/`）。本 Skill 在服务端按下列路径请求，**不得**改用其它路径或自行 `curl` 猜测地址。

| 能力 | 方法 | 完整 URL（拼接规则） |
|------|------|----------------------|
| 法律咨询 | POST | `{base_url}v1/legal-chat/completions` |
| 案件分析 | POST | `{base_url}v1/case-analysis/generate` |

**错误示例（不存在，会导致 404）**：`/v1/legal/chat`、`/api/v1/legal/chat` 等任何与上表不一致的路径。

**正确调用方式**：通过本 Skill 的 `action` 与 JSON 参数调用（见下），由运行时注入 `base_url` 与 `api_key`；**不要**把 `legal/chat` 当作接口路径。

## 调用示例
### 法律咨询
```json
{
  "action": "legal_chat",
  "prompt": "员工被口头辞退，我该如何维权？",
  "stream": false,
  "enable_network": false
}
```

### 案件要素提取
```json
{
  "action": "case_analysis",
  "analysis_mode": "element_extract",
  "input_text": "张三于2024年1月入职A公司，未签订劳动合同，2024年6月被口头辞退。"
}
```

## 配置说明
- `base_url`: 木瓜 API 根地址（与 `metadata.json` 中 `required_configs` 一致）。运行时按顺序读取 `context.credentials.base_url`、`context.config.base_url`、`event.config.base_url`；均未提供时使用代码内默认 `https://api.test.mugua.muguafabao.com/`。法律咨询实际请求为 `{base_url}v1/legal-chat/completions`。
- `api_key`: 木瓜 API 鉴权 Token（Bearer），对应 `context.credentials.api_key`。
- `requirements.txt` 仅声明 `requests`；勿将标准库 `typing` 写入 pip 依赖（与注册元数据一致）。

## 许可证
MIT-0

## 数据安全与隐私提示
- 本Skill会将用户提供的案件文本、上传文件及配置的`api_key`发送至您指定的`base_url`服务端，请务必确认该服务是您信任的官方服务。
- 请勿在未阅读并同意木瓜法律API隐私政策前，发送包含敏感个人信息的案件数据。
- 建议仅在隔离环境中测试，使用模拟数据验证功能后再处理真实案件。

## 安装前必看
1.  确认`base_url`为官方可信端点（当前默认是测试环境）。
2.  必须配置`api_key`（Bearer Token）才能正常调用API。
3.  妥善保管`api_key`，避免泄露。