# legal-cn-api - 中国法律条文检索付费 API

给 AI Agents 提供准确、结构化、可直接调用的中国法律条文检索，按次付费，不需要自己建库。

## 🎯 解决什么问题

AI Agents 在处理涉及中国法律的问题时，经常需要查阅最新的法律法规。自己搭建法律数据库成本高、维护麻烦，使用本服务可以：

- ✅ **即拿即用**：直接调用 API 获取结构化法律条文
- ✅ **按次付费**：用多少付多少，成本极低（每次搜索约 0.000007 人民币）
- ✅ **去中心化**：付费直接到开发者钱包，没有中间商抽成
- ✅ **自动更新**：每季度同步最新法律法规

## 📊 数据规模

- **2,416** 部现行有效法律
- **81,529** 条具体条文
- 更新到 **2026 年 7 月**
- 分类完善：民法、刑法、行政法、经济法、社会法、诉讼法等

## 💰 付费模式

基于 **x402 协议**（USDC on Base）实现微支付，三层定价：

- **获取分类信息**：✅ 免费
- **单次查询**：**0.001 USDC** ≈ **0.007 人民币**
- **包月套餐**：即将推出（优惠价）

**为什么这么定价：**
- 极低试用门槛，任何人都敢尝试
- 价格覆盖微支付链上成本，可持续运营
- 就算一天搜索 1000 次，也才 7 毛钱，用户完全不心疼
- **去中心化**：付费直接到开发者钱包，不需要托管
- **自动验证**：协议自动验证支付，无需人工干预

## 🚀 快速部署

### 1. 克隆项目

```bash
git clone https://github.com/fengsu82/legal-cn-api
cd legal-cn-api
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 启动 Meilisearch

```bash
docker-compose up -d
```

### 4. 导入数据

数据来自公开项目 [pengxiao1997/china_law](https://github.com/pengxiao1997/china_law)，自动导入。

```bash
bash update_database.sh
```

### 5. 配置支付

```bash
cp config.py.example config.py
# 编辑 config.py，填入你的钱包地址和私钥
```

### 6. 启动服务

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 📚 API 使用

### `GET /api/v1/search`

参数：
- `q`: 搜索关键词
- `limit`: 返回数量（默认 10，最大 50）

返回示例：

```json
{
  "success": true,
  "results": [
    {
      "law_title": "中华人民共和国民法典",
      "article_no": "第五条",
      "article_title": "自愿原则",
      "content": "民事主体从事民事活动，应当遵循自愿原则，按照自己的意思设立、变更、终止民事法律关系。",
      "effective_date": "2021-01-01",
      "category": "民法",
      "score": 0.98
    }
  ],
  "total": 12
}
```

### `GET /categories`

**免费接口**，获取所有法律分类及条文数量。

### `GET /health`

健康检查。

## 🛠 技术栈

- **FastAPI** - 高性能 Web 框架
- **Meilisearch** - 全文搜索引擎，毫秒级响应
- **x402** - 去中心化微支付协议
- **USDC on Base** - 稳定币支付网络

## 📄 许可证

MIT License —— 可以自由使用、修改、分发。

## 👨‍💼 作者

Felix Feng <fengsu82@qq.com>

- 广东广和律师事务所 执业律师
- 关键词教育 国际部 CEO
