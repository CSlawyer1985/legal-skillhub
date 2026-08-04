# legal-cn-api - 中国法律条文检索付费API

> 给AI Agents提供准确、结构化、可直接调用的中国法律条文检索，按次付费，不需要自己建库。

## 🎯 产品定位

- **目标用户**：AI Agents、AI应用开发者、法律AI产品
- **核心价值**：解决agents没法直接获得结构化准确中国法律数据的痛点
- **支付协议**：支持 x402 (USDC on Base) / L402 (Lightning)
- **定价**：
  - 单次查询：10 sats ≈ 0.01 USD
  - 包月100次：500 sats ≈ 0.5 USD

## 🚀 快速开始

### 1. clone数据
```bash
git clone https://github.com/pengxiao1997/china_law.git data
```

### 2. 启动服务
```bash
docker-compose up -d
```

这会启动 Meilisearch 搜索引擎。

### 3. 导入数据
```bash
pip install -r requirements.txt
python utils/import_data.py --data-dir data --host http://localhost:7700 --master-key masterKey
```

### 4. 配置支付
```bash
cp config.py.example config.py
# 编辑 config.py，填入你的钱包地址和密钥
```

### 5. 启动API
```bash
# 开发
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 生产
pm2 start uvicorn --name legal-cn-api -- main:app --host 0.0.0.0 --port 8000
```

## 📚 API文档

启动后访问 `http://your-server:8000/docs` 查看交互式API文档。

### 端点

#### `GET /api/v1/search`
- 参数：
  - `q`: 搜索关键词
  - `limit`: 返回数量，默认 10
- 返回：
```json
{
  "success": true,
  "results": [
    {
      "law_title": "中华人民共和国民法典",
      "article_no": "第五条",
      "article_title": "自愿原则",
      "content": "民事主体从事民事活动，应当遵循自愿原则...",
      "effective_date": "2021-01-01",
      "category": "民法",
      "score": 0.98
    }
  ],
  "total": 12
}
```

## 💰 付费模式

基于 x402 协议（USDC on Base）微支付，三层定价：

1. **Tier 1 Discovery** - ✅ **免费** 获取分类和统计信息
2. **Tier 2 Micro-access** - **0.001 USDC** / 次搜索 ≈ 0.007 CNY
3. **Tier 3 Bulk/Subscription** - 即将支持包月套餐（优惠价）

**为什么这么定价：**
- 极低试用门槛，任何人都敢用
- 仍然覆盖微支付链上成本
- 就算一天搜 1000 次，也才 7 毛钱

## 📊 数据来源

初始数据来自：https://github.com/pengxiao1997/china_law

后续每月从中国人大网更新新增/修改法律。

## 📄 许可证

MIT
