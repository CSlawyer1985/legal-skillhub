# IMA 接入踩坑卡

> 从「配好 KB_ID」到「文章真正入库」之间最容易踩的坑，都在这。

## 接入链路总览

```
用户自建个人知识库(ima.qq.com)
    ↓
手动创建分类文件夹(10个)
    ↓
获取 KB_ID + folder_id → 填入 taxonomy.yaml
    ↓
获取 API 凭证 → 写入 ~/.config/ima/{client_id,api_key}
    ↓
【选方式】WorkBuddy → ima-skills(import_urls)
         或  CLI → import_ima.py(OpenAPI)
    ↓
文章入库 ✅
```

## 7 个高频坑

| # | 症状 | 根因 | 解决 |
|---|------|------|------|
| 1 | `folder_id 非法 (222000)` | 文件夹**只能在网页端手动创建**，API 不能自动建 | 去 ima.qq.com 手动建文件夹 → 填 folder_id |
| 2 | Agent 说「只有只读工具」 | ima-mcp connector 暴露的是 search/get，不是 import_urls | 确保 ima-skills 已加载（对话中说「导入网页到知识库」验证） |
| 3 | `401 Unauthorized` | 凭证未配或格式错 | ima.qq.com → 设置 → API 密钥 → 生成 → 写入无空格无换行 |
| 4 | 导入后页面在根目录 | taxonomy 关键词没命中 → folder_id 为空 | 检查 taxonomy.yaml，补「债权人撤销权」「董监高」等冷门词 |
| 5 | 相同 URL 重复入库 | IMA `import_urls` **不自动去重** | 用 `imported_cache.jsonl` 记录已导入 URL |
| 6 | 一次传 >10 个 URL | IMA 限 10 个/次 | 分批；`import_ima.py` 自动处理 |
| 7 | 中文 URL 报 400 | URL 编码问题 | `urllib.parse.quote(url, safe=':/?&=#')` |

## 凭证获取路径

```
ima.qq.com → 登录 → 右上角头像 → 设置 → API 密钥 → 生成密钥
→ 复制 Client ID → echo "xxx" > ~/.config/ima/client_id
→ 复制 API Key  → echo "xxx" > ~/.config/ima/api_key
```

## 检测是否就绪

在 WorkBuddy 对话中执行：
```
Agent，帮我把 https://example.com 导入我的 IMA 知识库
```
→ 成功说明链路通。失败则看对应症状查上表。
