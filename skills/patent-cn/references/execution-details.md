# 执行细节文档

下文是专利生成各步骤的完整命令、参数和注意事项。

> `$DIR` 指本技能所在目录。

---

## 第 0 步：首次自举（仅一次）

### 写出 assemble.js

若 `$DIR/assemble.js` 不存在，读取 `SKILL.md` 附录 A 写出。此脚本已预置在根目录。

### npm install（导出 DOCX 时必需）

仅在用户后续同意导出 DOCX 且 `$DIR/node_modules` 不存在时才需要：

```powershell
cd "$DIR"
npm install
```

`package.json` 已在根目录，`@resvg/resvg-js` 和 `docx` 会自动安装。

> ⚠️ `@resvg/resvg-js` 是 native addon，Windows 上需 Visual Studio Build Tools（含 C++ 工具链）。若 `npm install` 报 node-gyp 错误，先安装 [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)。

---

## 第 1 步：确认输入格式 & DOCX 自动转 PDF

上传接口**只接受 PDF**。若用户上传 DOCX/DOC，**自动静默转换**，无需提示。

**转换方法（按优先级尝试）：**

1. **LibreOffice**（推荐）：
   ```powershell
   soffice --headless --convert-to pdf --outdir "$DIR" "C:\绝对路径\交底材料.docx"
   ```

2. **PowerShell COM**（仅 Windows + Word 已安装）：
   ```powershell
   $word = New-Object -ComObject Word.Application
   $doc = $word.Documents.Open("C:\绝对路径\交底材料.docx")
   $doc.SaveAs([ref]"$DIR\temp_交底材料.pdf", [ref]17)
   $doc.Close(); $word.Quit()
   ```

3. **Python docx2pdf**：
   ```powershell
   pip install docx2pdf
   docx2pdf "C:\绝对路径\交底材料.docx" --output "$DIR\temp_交底材料.pdf"
   ```

> ⚠️ **不要在用户原始路径下产生临时文件**，PDF 输出到 `$DIR/` 目录下。
> 成功后用 PDF 继续，失败时才告知用户。

---

## 第 2 步：上传，取 documentId

```powershell
curl.exe -s -X POST "https://www.cndeeptest.com/patent_draft/api/files/upload-document" `
  -F "file=@C:\绝对路径\交底材料.pdf"
```

> ⚠️ PowerShell 中 `curl` 是 `Invoke-WebRequest` 别名，**必须用 `curl.exe`**。

从返回 JSON 的 `data` 取 `documentId`。`code != "200"` 时反馈 `message` 并停止。

---

## 第 3 步：生成并落盘（SSE 流式）

`assemble.js` 内部 spawn `curl.exe` 请求 SSE，实时解析流，绕开 PowerShell 管道编码问题。

**后台启动 + 轮询进度：**

```powershell
# 后台启动，timeout 900 秒
# 第三个参数传 "stdout" 让内容输出到标准输出
node "$DIR/assemble.js" "<documentId>" "-" "stdout"
```

**轮询方式**：启动后用 `process poll` 轮询 stdout。每当 poll 到新的 `[进度]` 行时，**立即向用户发送一条简短进度消息**（参考 `references/progress-mapping.md` 的话术模板）。

**捕获结果**：
- 进程完成後用 `process log` 获取完整输出
- 从输出中提取 `===PATENT_CONTENT_START===` 和 `===PATENT_CONTENT_END===` 之间的 JSON
- 解析 JSON 获取 `content`（全文）和 `charCount`

---

## 第 4 步：呈现结果

**不展示全文**，只汇报统计：

```
✅ 100% 专利申请文件生成完成
共 X,XXX 字，包含 X 张附图

是否需要导出为 .docx 格式（内嵌高清PNG附图）？
```

**统计方式**：
- 字数：`charCount`（JSON 字段）
- 附图数：统计 `content` 中 `<svg` 出现次数

> 期间若收到 `error` 事件，仅转述 `message`，不做原因猜测或建议。

---

## 第 5 步：征求同意 → 导出 DOCX

**用户同意后**执行：

```powershell
# 1. 写入临时 md 文件
$content | Out-File -FilePath "$DIR/临时专利文件.md" -Encoding UTF8

# 2. 转换为 docx（高清 PNG 内嵌 + 表格原生转换）
node "$DIR/svg-to-docx.js" "$DIR/临时专利文件.md" "专利申请文件.docx"

# 3. 删除临时 md 文件
Remove-Item "$DIR/临时专利文件.md" -Force
```

**用户不同意**：仅保留聊天文本，不生成文件。

转换器功能：
- 每个 `<svg>` → 按 3 倍率渲染高清 PNG，原位置居中内嵌
- Markdown 表格 → docx 原生表格（带边框、表头加粗）
- `权利要求书` / `说明书` 等标题 → 居中加粗
- `技术领域` / `背景技术` 等子标题 → 左对齐加粗
