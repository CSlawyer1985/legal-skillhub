> 公共复用模块，被模块A和模块C引用。
> 数据源：flk.npc.gov.cn 官方 API（`/law-search/` 端点系）。调用入口：`scripts/flk_npc_client.py`

## A7. 混合法条检索引擎

本Skill采用 **API 优先 + AI 知识库兜底** 的双通道法条检索策略。

### 7.1 架构总览

```
用户输入关键词
  → 调用 scripts/flk_npc_client.py（封装 flk.npc.gov.cn /law-search/ API）
  → 返回结果 → 格式化输出：📜法律条文 + ⚖️参考案例（如有）
  → API 不可用/超时 → 降级到 AI 训练知识库 + 标注来源 + 建议手动核验
```

### 7.2 官方 API 调用入口

**当前状态（2026年7月，已验证可用）：**
- ✅ `/law-search/search/list` — 按标题/关键词搜索法律法规
- ✅ `/law-search/search/detail` — 获取法条详情（标题、机关、日期等）
- ✅ `/law-search/search/download/url` — 获取法条原文下载链接（Word/PDF）
- ✅ `/law-search/search/enumData` — 获取法规分类树 + 制定机关分类树
- ✅ `/law-search/search/vague` — 搜索联想建议（自动补全）

**调用方式：**
```python
from scripts.flk_npc_client import FlkNpcClient

client = FlkNpcClient(timeout=10)
# 关键词搜索
result = client.search_by_title("民法典", page_size=10)
# 获取详情
detail = client.get_detail(bbbs="...")
# 下载链接
url = client.get_download_url(bbbs="...", file_type="docx")
# 枚举数据
enum = client.get_enum_data()
client.close()
```

### 7.3 双通道策略

| 通道 | 数据源 | 优先级 | 触发条件 |
|:---|:---|:---:|:---|
| **实时通道** | `scripts/flk_npc_client.py` → flk.npc.gov.cn API | 最高 | 默认使用 |
| **知识库通道** | AI 训练知识库 | 兜底 | API 超时/不可用/返回空 |

### 7.4 API 降级处理

当实时 API 不可用时（网络超时、返回空、限流），自动降级：

1. 使用 AI 训练知识库中的法律条文（适用于《民法典》《刑法》《劳动合同法》等常见法律）
2. 所有引用必须标注来源："据《XXX》第X条"
3. 附加免责声明："以上内容仅供参考，具体适用请以官方最新文本及司法实践为准"
4. 在输出末尾标注：`[数据来源：AI知识库]`，区别于实时 API 的 `[数据来源：flk.npc.gov.cn]`

**不使用非官方数据源：**
- ❌ 不调用任何第三方非官方 API
- ❌ 不依赖可能过时的本地缓存
- ✅ 仅使用 flk.npc.gov.cn 官方 API + AI 训练知识兜底

### 7.5 统一引用格式

所有法条引用均按统一格式输出，并标注数据来源：
- 📜 **实时 API 结果**：`[数据来源：flk.npc.gov.cn]`《**法律全称**》"**第XXX条** 法条原文内容"
- 📚 **AI 知识库兜底**：`[数据来源：AI知识库]`《**法律全称**》"**第XXX条** 法条原文内容"
- ⚠️ 法条引用末尾附带说明："以上内容仅供参考，具体适用请以官方最新文本及司法实践为准"

### 7.6 查询示例

```
用户："劳动法对试用期怎么规定的？"

AI 调用 flk_npc_client.search_by_title("劳动合同法") → 获取实时法条

响应：
📜 [数据来源：flk.npc.gov.cn] 据《中华人民共和国劳动合同法》第十九条：
   劳动合同期限三个月以上不满一年的，试用期不得超过一个月；
   劳动合同期限一年以上不满三年的，试用期不得超过二个月；
   三年以上固定期限和无固定期限的劳动合同，试用期不得超过六个月。

⚠️ 以上内容仅供参考，具体适用请以官方最新文本及司法实践为准。
```

### 7.7 局限性说明

| 场景 | 限制 | 应对 |
|:---|:---|:---|
| API 限流 | 连续高频请求可能触发限流 | 建议请求间隔 ≥0.5 秒；触发后自动切换到知识库通道 |
| 新近修订 | API 更新可能存在延迟 | 标注"截至 API 最后可用时间" |
| 地方性法规 | 全国人大数据库侧重国家层面 | 补充说明"地方性法规请查询各地人大官网" |
| 知识库时效 | AI 训练截止日期后的法律修订可能未包含 | 优先走实时 API；API 不可用时明确标注数据来源 |
