# 常见问题

| 现象 | 原因 / 处理 |
|------|------------|
| 上传返回 `FORMAT_ERROR` | 只支持 PDF，先转格式 |
| 收到 `error` 事件 | 按其 `message` 告知用户并停止 |
| `documentId` 失效 | 重新上传交底 PDF |
| 流提前断开 | 重跑生成；确保未设置短的 curl/客户端超时 |
| DOCX 转换报缺模块 | 在 `$DIR` 下 `npm install` |
| PowerShell `curl` 报错 | 必须用 `curl.exe`（PowerShell 的 `curl` 是 `Invoke-WebRequest` 别名） |
| SSE 管道中文乱码 | `assemble.js` 内部直接 spawn `curl.exe`，无需 PowerShell 管道 |
| npm install 报 node-gyp 错误 | 缺少 C++ 工具链，安装 Visual Studio Build Tools |
| 用户上传了非 PDF/DOCX 格式 | 告知用户只支持 PDF 或 DOCX |
| 生成结果内容不完整 | 检查网络连接，重试生成 |
