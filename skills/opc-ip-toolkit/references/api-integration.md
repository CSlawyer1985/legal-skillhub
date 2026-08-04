# 外部API集成指南

## 一、智慧芽开放平台

### 平台简介

**官网**：https://open.zhihuiya.com/

**优势**：
- 2.1亿+全球专利数据
- 140+REST API接口
- 支持MCP协议（Model Context Protocol）
- 数据覆盖中、美、欧、日、韩等主要国家和地区

### 注册与认证

#### 注册流程
1. 访问 https://open.zhihuiya.com/
2. 点击"立即注册"
3. 填写邮箱、密码等信息
4. 邮箱验证
5. 完成注册

#### 实名认证
1. 登录后进入控制台
2. 点击"实名认证"
3. 选择认证类型（企业/个人）
4. 上传营业执照或身份证
5. 等待审核（1-2个工作日）

#### 创建应用获取API Key
1. 进入"应用管理"
2. 点击"创建应用"
3. 选择服务类型（专利检索/数据分析等）
4. 获取 App ID 和 App Key

### API Key配置

```python
# 方式1：环境变量（推荐）
import os
os.environ['ZHIYUYA_APP_ID'] = 'your_app_id'
os.environ['ZHIYUYA_APP_KEY'] = 'your_app_key'

# 方式2：配置文件
# 在项目根目录创建 config.json
{
    "zhiyuya_app_id": "your_app_id",
    "zhiyuya_app_key": "your_app_key"
}
```

### 常用API接口

#### 1. 专利检索 API
**接口**：`POST /v1/patent/search`

```python
import requests

def search_patents(query, app_id, app_key):
    """
    搜索专利
    
    参数:
        query: 搜索关键词
        app_id: 应用ID
        app_key: 应用Key
    
    返回:
        专利列表
    """
    url = "https://open.zhihuiya.com/v1/patent/search"
    
    headers = {
        "Content-Type": "application/json",
        "X-App-Id": app_id,
        "X-App-Key": app_key
    }
    
    payload = {
        "query": query,
        "page_size": 10,
        "page_num": 1,
        "search_type": "simple"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        return None

# 使用示例
result = search_patents(
    query="人工智能 语音识别",
    app_id=os.environ.get('ZHIYUYA_APP_ID'),
    app_key=os.environ.get('ZHIYUYA_APP_KEY')
)
```

#### 2. 专利详情 API
**接口**：`GET /v1/patent/detail/{patent_number}`

```python
def get_patent_detail(patent_number, app_id, app_key):
    """
    获取专利详情
    
    参数:
        patent_number: 专利号（如 CN101234567A）
        app_id: 应用ID
        app_key: 应用Key
    
    返回:
        专利详细信息
    """
    url = f"https://open.zhihuiya.com/v1/patent/detail/{patent_number}"
    
    headers = {
        "X-App-Id": app_id,
        "X-App-Key": app_key
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        return None

# 使用示例
patent_info = get_patent_detail(
    patent_number="CN101234567A",
    app_id=os.environ.get('ZHIYUYA_APP_ID'),
    app_key=os.environ.get('ZHIYUYA_APP_KEY')
)
```

#### 3. 专利全文 API
**接口**：`GET /v1/patent/fulltext/{patent_number}`

```python
def get_patent_fulltext(patent_number, app_id, app_key):
    """
    获取专利全文（权利要求书、说明书等）
    """
    url = f"https://open.zhihuiya.com/v1/patent/fulltext/{patent_number}"
    
    headers = {
        "X-App-Id": app_id,
        "X-App-Key": app_key
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        return None
```

#### 4. 批量查询 API
**接口**：`POST /v1/patent/batch`

```python
def batch_search_patents(patent_numbers, app_id, app_key):
    """
    批量查询专利详情
    
    参数:
        patent_numbers: 专利号列表（最多50个）
    """
    url = "https://open.zhihuiya.com/v1/patent/batch"
    
    headers = {
        "Content-Type": "application/json",
        "X-App-Id": app_id,
        "X-App-Key": app_key
    }
    
    payload = {
        "patent_numbers": patent_numbers
    }
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        return None
```

### MCP协议集成（高级）

智慧芽支持MCP协议，可与AI助手深度集成：

```json
{
  "mcpServers": {
    "zhiyuya": {
      "command": "npx",
      "args": ["-y", "@zhiyuya/mcp-server"],
      "env": {
        "ZHIYUYA_APP_ID": "your_app_id",
        "ZHIYUYA_APP_KEY": "your_app_key"
      }
    }
  }
}
```

### 错误代码处理

| 错误码 | 说明 | 处理建议 |
|-------|------|---------|
| 400 | 请求参数错误 | 检查参数格式 |
| 401 | 认证失败 | 检查API Key |
| 403 | 权限不足 | 检查应用权限 |
| 429 | 请求过于频繁 | 降低请求频率 |
| 500 | 服务器错误 | 稍后重试 |

### 费用说明

| 服务类型 | 免费额度 | 超出计费 |
|---------|---------|---------|
| 基础检索 | 100次/天 | 按调用量计费 |
| 专利详情 | 50次/天 | 按调用量计费 |
| 数据分析 | 需申请 | 企业版 |

---

## 二、CNIPA.AI 使用指南

### 平台简介

**官网**：https://cnipa.ai/

**优势**：
- 完全免费使用
- 支持中国、美国、PCT、欧洲、日本、韩国专利格式
- 一键生成专利五书（权利要求书、说明书、摘要等）
- AI智能理解技术方案

### 功能列表

| 功能 | 说明 |
|-----|------|
| 专利五书生成 | 一键生成权利要求书、说明书、摘要等 |
| 格式转换 | 支持多国专利格式转换 |
| 智能解读 | 解读专利文件内容 |
| 技术对比 | 对比多个专利的技术方案 |

### 使用方法

#### 方法1：网页直接使用
1. 访问 https://cnipa.ai/
2. 注册/登录账号
3. 选择"专利申请辅助"
4. 输入技术方案描述
5. 选择目标国家/地区
6. 生成申请文件

#### 方法2：API调用（如果有）

```python
def generate_patent_documents(technical_description, country="CN"):
    """
    使用CNIPA.AI生成专利申请文件
    
    参数:
        technical_description: 技术方案描述
        country: 目标国家（CN/US/EP PCT/JP/KR）
    
    返回:
        包含权利要求书、说明书、摘要的文件对象
    """
    # 注意：CNIPA.AI主要通过网页交互
    # 如有API需求，请访问官网获取API文档
    
    print("请访问 https://cnipa.ai/ 使用网页版服务")
    print(f"技术方案: {technical_description}")
    print(f"目标国家: {country}")
```

### 使用技巧

#### 输入高质量技术描述

**推荐格式**：
```
## 技术领域
[技术领域描述]

## 背景技术
[现有技术及存在的问题]

## 技术方案
[本发明的技术方案]

## 有益效果
[相对于现有技术的优势]
```

#### 选择正确的专利类型
- 发明专利：选择"发明"
- 实用新型：选择"实用新型"
- 两者都：可先生成发明，根据需求调整

#### 审查和修改
1. 查看生成的文件
2. 检查技术描述是否准确
3. 调整保护范围
4. 导出最终版本

---

## 三、免费工具汇总

### 专利检索工具

| 工具名称 | 网址 | 特点 |
|---------|------|------|
| 国家知识产权局 | ps sbj.cnipa.gov.cn | 官方数据，最权威 |
| SooPAT | soopat.com | 界面友好 |
| 佰腾网 | baitiangroup.com | 检索功能强 |
| 智慧芽 | zhihuiya.com | 数据全面（部分免费） |
| 专利之星 | patexplorer.com | 国产检索工具 |

### 商标检索工具

| 工具名称 | 网址 | 特点 |
|---------|------|------|
| 中国商标网 | sbj.cnipa.gov.cn | 官方数据 |
| 权查查 | quancha.cn | 免费检索 |
| 知果果 | zhiguoguo.com | 服务全面 |

### 软著登记

| 工具名称 | 网址 | 特点 |
|---------|------|------|
| 中国版权保护中心 | ccopyright.com.cn | 官方登记平台 |
| 版权家 | banquanjia.net | 在线代办 |

---

## 四、API Key安全管理

### 安全最佳实践

#### 1. 环境变量存储
```bash
# Linux/Mac
export ZHIYUYA_APP_ID="your_app_id"
export ZHIYUYA_APP_KEY="your_app_key"

# Windows
set ZHIYUYA_APP_ID=your_app_id
set ZHIYUYA_APP_KEY=your_app_key
```

#### 2. 配置文件管理
```json
// config.json（不提交到版本控制）
{
  "zhiyuya_app_id": "your_app_id",
  "zhiyuya_app_key": "your_app_key"
}
```

```python
# 在 .gitignore 中添加
config.json
.env
*.key
```

#### 3. 代码中使用
```python
import os
import json

def load_config():
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    
    # 先尝试从环境变量获取
    app_id = os.environ.get('ZHIYUYA_APP_ID')
    app_key = os.environ.get('ZHIYUYA_APP_KEY')
    
    if not app_id or not app_key:
        # 再尝试从配置文件获取
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                app_id = config.get('zhiyuya_app_id')
                app_key = config.get('zhiyuya_app_key')
    
    return app_id, app_key
```

#### 4. 日志脱敏
```python
import logging

class SensitiveFilter(logging.Filter):
    """日志脱敏过滤器"""
    
    SENSITIVE_KEYS = ['app_key', 'api_key', 'password', 'token']
    
    def filter(self, record):
        message = record.getMessage()
        for key in self.SENSITIVE_KEYS:
            if key in message.lower():
                record.msg = "[REDACTED]"
                record.args = ()
        return True

# 使用
logger = logging.getLogger(__name__)
logger.addFilter(SensitiveFilter())
```

### 密钥轮换

- 定期更换API Key（建议每3个月）
- 旧Key过期前创建新Key
- 验证新Key后再删除旧Key
