---
name: patent-scout
description: "通过百度或Google Patents在线检索中国专利信息，支持关键词和专利号查询，输出结构化专利摘要和申请人等数据。"
---

# Patent Scout - 中国专利搜索 Skill

真实的中国专利搜索工具，通过百度搜索或 Google Patents 在线检索中国专利信息。

## 触发条件

当用户提到以下内容时使用此 Skill：
- "搜索专利"、"查专利"、"专利检索"
- "patent search"、"find patents"
- "技术专利"、"发明专利"、"实用新型"
- 提到具体的中国专利号（如 CN116789012A）
- 需要查看专利摘要、申请人等信息

## 功能特性

### 数据源
- **百度搜索**（默认）— 国内直连，无需代理，适合中国网络环境
- **Google Patents** — 全球专利数据库，需代理访问

### 搜索能力
- 关键词搜索（中文）
- 专利号精确查询（CN 开头）
- 自动过滤广告和无关结果
- 自动提取专利号

### 输出格式
- Markdown（默认）— 结构化展示专利信息
- JSON — 方便程序处理

## 使用方法

### 关键词搜索
```bash
# 默认百度搜索
node scripts/patent-scout.js --query "工业防火墙"

# 限制结果数量
node scripts/patent-scout.js --query "深度学习" --limit 5

# 导出到文件
node scripts/patent-scout.js --query "固态电池" --output results.md

# JSON 格式输出
node scripts/patent-scout.js --query "5G" --format json
```

### 专利号查询
```bash
node scripts/patent-scout.js --patent-id CN116789012A
```

### 使用 Google Patents（需代理）
```bash
node scripts/patent-scout.js --query "芯片" -s google --proxy http://127.0.0.1:7890
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-q, --query` | 搜索关键词 | - |
| `-p, --patent-id` | 专利号（如 CN116789012A） | - |
| `-l, --limit` | 结果数量 | 10 |
| `-s, --source` | 数据源 (baidu/google) | baidu |
| `-o, --output` | 输出文件路径 | - |
| `-f, --format` | 输出格式 (markdown/json) | markdown |
| `--proxy` | 代理地址（Google Patents 需要） | - |

## 技术栈

- **Node.js** — 运行环境
- **axios** — HTTP 请求
- **cheerio** — HTML 解析
- **commander** — 命令行参数解析

## 安装

```bash
cd internal/java/patent-scout
npm install
```

## 示例场景

### 场景 1: 技术调研
```
用户: "帮我搜索关于工业防火墙的专利"
→ node scripts/patent-scout.js --query "工业防火墙" --limit 5
```

### 场景 2: 专利号查询
```
用户: "查一下专利 CN121567465A"
→ node scripts/patent-scout.js --patent-id CN121567465A
```

### 场景 3: 导出分析
```
用户: "搜索固态电池专利并导出"
→ node scripts/patent-scout.js --query "固态电池" --output results.md
```

## 注意事项

- 百度搜索为默认数据源，国内可直连
- Google Patents 在中国大陆需要配合代理使用
- 请控制请求频率，避免被限流
- 部分百度结果可能无法提取完整专利号

## 许可证

MIT License

## 作者

闫老师团队

## 更新日志

### v2.0.0
- 重写为真实网络搜索（移除演示数据）
- 支持百度搜索（国内直连）
- 支持 Google Patents（需代理）
- 自动过滤广告
- 自动提取中国专利号

### v1.0.0
- 初始版本（演示数据）
