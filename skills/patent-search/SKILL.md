---
name: patent-search
description: Patent search and analytics via 9235 API (search, detail, claims, company portrait, Excel export).
version: 1.0.10
metadata:
  openclaw:
    emoji: "📜"
    homepage: https://www.9235.net/api/open
    primaryEnv: PATENT_API_TOKEN
    requires:
      env:
        - PATENT_API_TOKEN
      bins:
        - python3
    envVars:
      - name: PATENT_API_TOKEN
        required: true
        description: 9235 patent search API token from https://www.9235.net/api/open
      - name: PATENT_API_BASE_URL
        required: false
        description: Optional API base URL (default https://www.9235.net/api)
    install:
      - kind: uv
        package: requests
---

# 专利检索 · Patent Search

## 概述 | Overview

| | |
|---|---|
| **中文** | 对接 [9235](https://www.9235.net/api) 专利 API：检索、详情、权利要求、说明书、法律信息、引用/相似专利、**企业画像**（工商全称）、统计与 Excel 导出；数据范围 `cn` / `all` / `us` / `jp` / `kr` / `tw` / `wo` / `ep`。 |
| **English** | [9235](https://www.9235.net/api) patent API client: search, detail, claims, description, legal events, citations, similar patents, **company portrait**, analytics, Excel export; scopes `cn`, `all`, `us`, `jp`, `kr`, `tw`, `wo`, `ep`. |

**凭证 Credentials**: `PATENT_API_TOKEN` 或 OpenClaw `skills.entries.patent-search.apiKey` · 申请 <https://www.9235.net/api/open>

用户可说：「检索大疆无人机专利」「全球检索锂电池」「华为技术有限公司企业画像」「导出当前检索 Excel」。

---

## 功能概述

- **专利搜索**: 根据关键词、申请人、发明人、IPC分类等条件搜索专利
- **专利详情**: 查看专利的完整信息，包括摘要、申请人、发明人、法律状态等
- **权利要求**: 查看专利的权利要求书
- **说明书**: 查看专利的说明书全文
- **法律信息**: 查看专利的法律事务信息
- **引用分析**: 查看专利的引用和被引用情况
- **相似专利**: 查找相似专利
- **企业画像**: 分析企业的专利布局和竞争力
- **文件下载**: 下载专利PDF全文和摘要附图
- **统计分析**: 专利维度统计分析
- **导出 Excel**: `export` 导出检索列表；`export_analysis` 导出统计分布（需 dimension）
- **著作权搜索**: 软件著作权和作品著作权搜索
- **商标搜索**: 商标信息搜索

## 安装

### 自动安装
```bash
# 进入技能目录（本仓库 patents/patent-search）
cd /path/to/patents/patent-search

# 运行安装脚本
python3 setup.py
```

### 手动安装
```bash
# 1. 安装依赖
pip3 install requests --break-system-packages

# 2. 设置文件权限
chmod +x patent_api.py main.py setup.py

# 3. 创建配置文件
cp config.example.json config.json
# 编辑config.json，设置您的API token
```

## 配置

### 配置文件
在技能目录下创建 `config.json` 文件（或复制 `config.example.json`）：

```json
{
  "api_base_url": "https://www.9235.net/api",
  "token": "YOUR_API_TOKEN_HERE",
  "default_data_scope": "cn",
  "default_page_size": 10,
  "max_records": 1000,
  "timeout_seconds": 30,
  "download_dir": "./downloads",
  "enable_cache": false,
  "cache_ttl_seconds": 3600,
  "retry_times": 3,
  "retry_delay_seconds": 1
}
```

### 环境变量配置
```bash
export PATENT_API_TOKEN="your_token_here"
export PATENT_API_BASE_URL="https://www.9235.net/api"
export PATENT_DEFAULT_SCOPE="cn"
export PATENT_DOWNLOAD_DIR="./downloads"
```

### 获取API Token
1. 访问 https://www.9235.net/api/open
2. 申请API访问权限
3. 获取token后填入配置文件

## 使用方法

### 运行模式

**交互模式:**
```bash
python3 main.py
# 然后输入命令，如: search 无人机
```

**命令行模式:**
```bash
python3 main.py <命令> <参数>
```

### 1. 搜索专利

**基本搜索:**
```bash
/search 无人机
/search 石墨烯
/search "新能源汽车"
```

**高级搜索:**
```bash
/search agency:北京博思佳知识产权代理有限公司
/search documentYear:[2020 TO 2024] AND 锂电池
/search applicant:"清华大学" AND 人工智能
/search 无人机 AND type:发明授权 AND legalStatus:有效专利
```

**带选项搜索:**
```bash
/search 无人机 --page 2 --page-size 20
/search 无人机 --sort applicationDate
/search 无人机 --sort !documentDate  # 降序
/search 无人机 --scope all  # 全球搜索
/search 无人机 --details  # 显示详细信息
```

### 2. 查看专利详情

```bash
/patent CN110382353B
```

### 3. 查看权利要求

```bash
/claims CN110382353B
```

### 4. 查看说明书

```bash
/desc CN110382353B
```

### 5. 查看法律信息

```bash
/law CN110382353B
```

### 6. 查看引用分析

```bash
/citing CN110382353B
```

### 7. 查看相似专利

```bash
/similar CN110382353B
```

### 8. 企业画像分析

```bash
/company 深圳市大疆创新科技有限公司
/company 华为技术有限公司
```

### 9. 著作权搜索

**软件著作权:**
```bash
/copyright 档案管理系统 --type software
/copyright owner:阿里巴巴 --type software --field owner
```

**作品著作权:**
```bash
/copyright 美术作品 --type works
/copyright author:张三 --type works --field author
```

### 10. 商标搜索

**商标列表:**
```bash
/trademark 华为
/trademark 阿里巴巴 --page 2 --page-size 20
```

**商标详情:**
```bash
/trademark --detail --trademark-id "2020163926c8006d56dba63557fbefe8213a3aaa"
```

### 11. 统计分析

```bash
/analysis 人工智能 --dimension ipc
/analysis 锂电池 --dimension applicant --scope all
/analysis documentYear:[2020 TO 2024] AND 5G --dimension province
```

### 12. 下载文件

```bash
/download CN110382353B --type pdf
/download CN110382353B --type image
/download CN110382353B --type all --output ./my_downloads/
```

### 13. 帮助信息

```bash
/help
```

## 检索式语法参考

### 字段限定
- `title:无人机` - 标题包含无人机
- `applicant:"清华大学"` - 申请人为清华大学
- `inventor:王勇` - 发明人包含王勇
- `agency:北京博思佳知识产权代理有限公司` - 代理机构
- `ipc:G01C` - IPC分类号
- `mainIpc:H04N` - 主分类号
- `province:广东省` - 省份
- `city:深圳市` - 城市

### 时间范围
- `applicationYear:[2020 TO 2024]` - 申请年份范围
- `documentYear:[2019 TO 2023]` - 公开年份范围
- `applicationDate:[2020-01-01 TO 2024-12-31]` - 申请日期范围

### 逻辑运算
- `AND` - 与关系 (默认，空格表示AND)
- `OR` - 或关系
- `NOT` - 非关系
- `()` - 括号分组

### 专利类型
- `type:发明公开`
- `type:发明授权`
- `type:实用新型`
- `type:外观设计`
- `type:PCT发明专利`
- `type:PCT实用新型`

### 法律状态
- `legalStatus:有效专利`
- `legalStatus:失效专利`
- `legalStatus:实质审查`
- `legalStatus:公开`

### 国家/地区
- `countryCode:CN` - 中国
- `countryCode:US` - 美国
- `countryCode:JP` - 日本
- `countryCode:EP` - 欧洲

### 精确匹配
- 使用双引号: `"无人机控制系统"`
- 避免分词: `"新能源汽车电池"`

### 通配符
- `*`: 多个字符通配符
- `?`: 单个字符通配符
- 示例: `comput*` 匹配 computer, computing 等

## 完整示例

### 1. 技术领域搜索
```bash
# 搜索无人机相关专利
/search 无人机

# 搜索大疆公司的无人机专利
/search 无人机 AND applicant:"深圳市大疆创新科技有限公司"

# 搜索2020-2024年的锂电池专利，按申请时间降序
/search documentYear:[2020 TO 2024] AND 锂电池 --sort !applicationDate

# 搜索清华大学的AI专利，显示详细信息
/search applicant:"清华大学" AND 人工智能 --details
```

### 2. 企业分析
```bash
# 华为公司专利分析
/company 华为技术有限公司

# 阿里巴巴集团专利布局
/company 阿里巴巴集团控股有限公司

# 分析大疆公司的技术领域
/analysis applicant:"深圳市大疆创新科技有限公司" --dimension ipc
```

### 3. 专利分析
```bash
# 查看专利详情
/patent CN110382353B

# 查看专利权利要求
/claims CN110382353B

# 查看专利法律状态变化
/law CN110382353B

# 查找相似专利
/similar CN110382353B

# 分析专利引用关系
/citing CN110382353B
```

### 4. 统计分析
```bash
# 分析人工智能技术的IPC分类分布
/analysis 人工智能 --dimension ipc

# 分析锂电池技术的申请人分布
/analysis 锂电池 --dimension applicant

# 分析5G技术的省份分布
/analysis 5G --dimension province

# 分析新能源汽车的申请趋势
/analysis 新能源汽车 --dimension applicationYear
```

### 5. 文件操作
```bash
# 下载专利PDF
/download CN110382353B --type pdf

# 下载专利图片
/download CN110382353B --type image

# 下载所有文件到指定目录
/download CN110382353B --type all --output ./patent_files/
```

### 6. 著作权和商标
```bash
# 搜索软件著作权
/copyright 管理系统 --type software

# 搜索作品著作权
/copyright 美术作品 --type works

# 搜索商标
/trademark 华为

# 查看商标详情
/trademark --detail --trademark-id "商标ID"
```

### 7. 复杂检索式
```bash
# 组合条件搜索
/search (无人机 OR 无人车) AND (雷达 OR 传感器) AND applicationYear:[2020 TO 2024]

# 排除特定分类
/search 石墨烯 AND NOT mainIpc:H

# 多条件筛选
/search 电池 AND type:发明授权 AND legalStatus:有效专利 AND province:广东省
```

## 重要注意事项

### API限制
1. **记录限制**: 每次搜索最多返回1000条记录
2. **分页限制**: 最大100页，每页最多50条
3. **ID有效期**: 专利ID有效期为60分钟
4. **访问限制**: 直接访问详情接口每天前200个免费
5. **频率限制**: 注意API调用频率，避免被封禁

### 使用建议
1. **合理分页**: 使用--page和--page-size参数控制数据量
2. **精确检索**: 使用字段限定提高检索精度
3. **时间范围**: 使用时间范围缩小检索结果
4. **保存ID**: 及时使用搜索得到的专利ID
5. **错误处理**: 注意错误代码，合理重试

### 排序选项
- `relation`: 相关度排序 (默认)
- `applicationDate`: 申请时间排序
- `!applicationDate`: 申请时间降序
- `documentDate`: 公开时间排序  
- `!documentDate`: 公开时间降序
- `rank`: 专利评级排序

### 常见问题
1. **Q: 为什么搜索不到结果？**
   A: 检查检索式语法，尝试简化关键词

2. **Q: 为什么无法查看专利详情？**
   A: 专利ID可能已过期，重新搜索获取新ID

3. **Q: 为什么下载失败？**
   A: 检查网络连接，确认专利有PDF文件

4. **Q: 如何提高搜索精度？**
   A: 使用字段限定、时间范围、逻辑运算

5. **Q: 如何获取API token？**
   A: 访问 https://www.9235.net/api/open 申请

## 错误代码处理

### 常见错误代码
- `200`: 响应成功
- `201`: token为空 - 检查配置文件或环境变量
- `202`: 非法token - token无效或过期，重新申请
- `203`: 响应异常 - API服务器错误，稍后重试
- `204`: ip被拒绝访问 - 检查IP白名单
- `205`: 参数值为空 - 检查请求参数
- `206`: 没有找到对应数据 - 调整检索条件
- `207`: 该接口当天访问次数已经用尽 - 次日再试或升级套餐
- `208`: 没有访问权限 - 检查API权限
- `209`: 版本号为空 - 内部错误，联系技术支持
- `210`: 参数错误 - 检查参数格式
- `211`: 该等级接口当年专利总数量已经用尽 - 升级套餐或次年使用
- `212`: 分析维度为空 - 指定分析维度
- `213`: 分析维度不存在 - 检查维度名称
- `214`: TOKEN类型错误 - 检查token类型
- `215`: 异常访问，被终止 - 遵守API规范，通过搜索接口获取ID

### 错误处理建议
1. **检查配置**: 确认token和API地址正确
2. **验证网络**: 检查网络连接是否正常
3. **简化请求**: 减少请求数据量，使用分页
4. **查看日志**: 查看详细错误信息
5. **联系支持**: 访问 https://www.9235.net 获取技术支持

## 高级功能

### 批量处理
```
/search 锂电池 --save-to-file patents.json
```

### 统计分析
```
/search 新能源汽车 --stats
```

### 导出结果
```
/search 5G通信 --export csv
```

## 更新日志

- **v1.0.10**: 精简核心（移除 trend/analysis/test 等 8 个开发脚本）；Excel 导出（`excel_export.py`）；完善凭证说明与文档。
- v1.0.0: 初始版本，支持基本搜索和详情查看

详见 [CHANGELOG.md](CHANGELOG.md)。

## 技术支持

如有问题，请参考：
- API文档: https://www.9235.net/api/interface.html
- 检索帮助: https://www.9235.net/help/index.html
- 申请token: https://www.9235.net/api/open