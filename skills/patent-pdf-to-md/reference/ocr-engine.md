
# MinerU OCR 引擎

仅在 MinerU 不可用或需要排查问题时阅读此节。

## 安装 MinerU

```bash
npm install -g mineru-open-api
# 验证
mineru-open-api version
```

## MinerU 两种模式

| | `flash-extract` | `extract` |
|---|---|---|
| Token | 不需要 | 需要 |
| 页数限制 | 20 页 | 无严格限制 |
| 文件大小 | 10 MB | 更大 |
| 输出格式 | 仅 Markdown | md/html/latex/docx/json |
| 本 Skill 使用 | **是**（逐页提取文字） | 否 |

本 Skill 仅使用 `flash-extract` 逐页提取文字，不使用 MinerU 的 Markdown 输出。MinerU 输出的文字会喂入 Python 结构化解析流程。

## MinerU 故障排除

| 错误 | 原因 | 解决 |
|------|------|------|
| `mineru-open-api: command not found` | 未安装 | `npm install -g mineru-open-api` |
| 退出码 4 | 文件超 10MB/20 页 | Skill 已自动逐页提取，若仍超限则降级到 Tesseract |
| 退出码 5 | 提取失败 | 检查 PDF 是否损坏，或降级到 Tesseract |
| 退出码 6 | 超时 | 增加 `--timeout` 或降级到 Tesseract |
| HTTP 429 | 速率限制 | 等待几分钟后重试 |

## MinerU Token（可选升级）

如需处理超 20 页的PDF，可注册 Token 使用 `extract` 模式：

```bash
# 注册 Token: https://mineru.net/apiManage/token
mineru-open-api auth          # 交互式配置
mineru-open-api auth --verify # 验证 Token
```
