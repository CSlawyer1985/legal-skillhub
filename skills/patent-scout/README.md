# Patent Scout - 中国专利搜索 Skill

## 概述

真实的中国专利搜索工具，通过百度搜索或 Google Patents 检索中国专利信息。

## 特性

- 真实网络搜索，非演示数据
- 默认百度搜索（国内直连，无需代理）
- 可选 Google Patents（需代理）
- 支持关键词搜索和专利号查询
- 输出 Markdown 或 JSON 格式
- 自动过滤广告和无关结果

## 快速开始

```bash
cd internal/java/patent-scout
npm install

# 搜索专利（默认百度）
node scripts/patent-scout.js --query "工业防火墙"

# 限制数量
node scripts/patent-scout.js --query "深度学习" --limit 5

# 查询专利号
node scripts/patent-scout.js --patent-id CN116789012A

# JSON 输出
node scripts/patent-scout.js --query "5G" --format json

# 导出文件
node scripts/patent-scout.js --query "固态电池" --output results.md

# 使用 Google Patents（需代理）
node scripts/patent-scout.js --query "芯片" -s google --proxy http://127.0.0.1:7890
```

## 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-q, --query` | 搜索关键词 | - |
| `-p, --patent-id` | 专利号 | - |
| `-l, --limit` | 结果数量 | 10 |
| `-s, --source` | 数据源 (baidu/google) | baidu |
| `-o, --output` | 输出文件 | - |
| `-f, --format` | 输出格式 (markdown/json) | markdown |
| `--proxy` | 代理地址 | - |

## 许可证

MIT License
