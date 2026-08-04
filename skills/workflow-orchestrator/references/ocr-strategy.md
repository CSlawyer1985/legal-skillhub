## OCR 预处理策略

几乎所有用户提供的材料都需要 OCR 预处理。本文件定义材料识别→OCR引擎选择→兜底的全链路逻辑。

### 材料类型识别

拿到材料后，先按扩展名分类：

| 类型 | 扩展名 | 首选引擎 | 原因 |
|------|--------|----------|------|
| 图片 | .jpg .jpeg .png .bmp .tif .tiff .webp | 百度 OCR | 速度快，中文识别精准 |
| 文档 | .pdf .docx .pptx | MinerU | 保留文档结构、表格、排版，输出 Markdown |
| 混合文件夹 | 多种扩展名混排 | 按文件逐一分发 | 图片→百度，文档→MinerU |
| 微信图片/截图 | 无扩展名或 .dat | 百度 OCR | 先尝试识别，失败则提示律师提供原图 |

### OCR 调用链路

```
材料进入
  ↓
识别类型
  ↓
┌─ 图片 ─────────→ 百度 OCR (ocr_image)
│                    ↓ 失败
│                  MinerU 图片模式  (convert_document)
│                    ↓ 失败
│                  PaddleOCR (本地兜底)
│
└─ 文档 ─────────→ MinerU (convert_document)
                     ↓ 失败
                   百度 OCR PDF 模式 (ocr_image, 逐页转图片)
                     ↓ 失败
                   PaddleOCR (本地兜底)
```

### 批量处理规则

- 文件夹内文件按扩展名自动分发到对应引擎
- 百度 OCR 自身支持文件夹批量（`ocr_image(folder_path)`）
- MinerU 需逐个文件调用

### OCR 输出处理

- 百度 OCR 输出为纯文本 → 直接作为材料内容
- MinerU 输出为 Markdown → 保留结构，表格/层级完整
- PaddleOCR 输出为纯文本 → 同百度 OCR

### 失败处理

- 单文件识别失败 → 标记该文件，继续处理其余
- 全部引擎失败 → 告知用户"以下文件无法识别：[列表]"，请用户提供可读版本
- 网络不可用 → 自动跳过云引擎，直接走 PaddleOCR 本地兜底

### 环境依赖

| 引擎 | 依赖 | 配置 |
|------|------|------|
| 百度 OCR | 网络 + API Key/Secret | `config.toml` 中注册 MCP 服务 |
| MinerU | 网络（Token 可选） | `config.toml` 中注册 MCP 服务，Token 在环境变量 `MINERU_API_TOKEN` |
| PaddleOCR | 本地 Python 环境 | `${OCR_TOOL_PATH}/batch_ocr.py`，环境变量 `PADDLE_PDX_CACHE_HOME` 已配置 |