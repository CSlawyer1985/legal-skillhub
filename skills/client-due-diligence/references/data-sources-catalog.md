# 数据源目录（Data Sources Catalog）

> 每个数据模块对应 MCP connector（优先）与权威公开网站（fallback）。生成报告前必读。

---

## MCP Connector 映射（优先通道）

| 模块 | 首选 MCP | 备选 MCP | 说明 |
|---|---|---|---|
| B1 工商基础 | `qcc-company`（企查查） | `tyc-mcp`（天眼查） | 企业登记、注册资本、法人、地址 |
| B2 股东/实控人/投资 | `qcc-company` | `qixinhuiyan-mcp`（启信慧眼） | 前十大股东、实控人、对外投资 |
| B3 董监高 | `qcc-company` | `tyc-mcp` | 主要人员名单、任职 |
| B4 经营异常 | `qcc-company` | `shuidi-credit`（水滴信用·企业尽调） | 经营异常、严重违法 |
| B5 司法风险 | `jufa-mcp-server`（聚法） | `qcc-legal`（企查查·法律数据）、`pkulaw`（北大法宝） | 裁判文书、涉诉 |
| B6 执行/失信/限高 | `qcc-legal` | `qcc-company` | 被执行人、失信、限高 |
| B7 知识产权 | `mzl-trademark`（摩知轮商标） | `patsnap-search`（智慧芽） | 商标、专利 |
| B8 行政处罚 | `qcc-company` | `shuidi-credit` | 行政处罚、信用中国 |
| B9 上市专项 | `westock-data` | `neodata-financial-search` | 行情、财务、股东、质押 |
| B10 重整/立案/监管 | `qcc-legal` | `fazhi-law`（同花顺法律） | 立案、处分、重整 |
| B11 舆情 | 无稳定 MCP | — | 用权威媒体网站 |

## 权威网站白名单（fallback + URL 校验）

### 市场监管
- 国家企业信用信息公示系统 `gsxt.gov.cn`
- 信用中国 `creditchina.gov.cn`
- 国家市场监督管理总局 `samr.gov.cn`

### 司法
- 中国裁判文书网 `wenshu.court.gov.cn`
- 中国执行信息公开网 `zxgk.court.gov.cn`
- 最高人民法院 `court.gov.cn`
- 全国企业破产重整案件信息网 `pccz.court.gov.cn`
- 司法部 `moj.gov.cn`

### 知识产权
- 国家知识产权局商标局 `sbj.cnipa.gov.cn`
- 专利检索系统 `pss-system.cnipa.gov.cn`
- 国家版权局 `ncac.gov.cn`
- 国家知识产权局 `cnipa.gov.cn`

### 证券监管
- 中国证监会 `csrc.gov.cn`
- 深交所 `szse.cn` / 上交所 `sse.com.cn` / 北交所 `bse.cn`

### 信息披露
- 巨潮资讯网 `cninfo.com.cn`

### 中央级权威媒体
- 新华网 `xinhuanet.com` / 人民网 `people.com.cn`
- 央视网 `cctv.com` / `cctv.cn`
- 经济日报 `jrj.com.cn` / 光明网 `gmw.cn`
- 中国法院网 `chinacourt.org`

## 屏蔽清单（禁止作为来源）

`baike.baidu.com` `baike.sogou.com` `baike.so.com` `sohu.com` `163.com` `sina.com.cn` `qq.com` `ifeng.com` `toutiao.com` `mp.weixin.qq.com` `baidu.com` `google.com` `bing.com` `sogou.com` `zhihu.com`

## 字段映射（关键字段 → 权威源）

| 字段 | 权威源 | 说明 |
|---|---|---|
| 统一社会信用代码 | gsxt.gov.cn | 18 位，唯一 |
| 法定代表人 | gsxt.gov.cn | 注意变更时点 |
| 成立日期 | gsxt.gov.cn | |
| 注册资本/实缴 | gsxt.gov.cn | |
| 股东/实控人 | gsxt.gov.cn + cninfo（上市公司） | 上市公司以定期报告为准 |
| 财务数据 | cninfo / szse / sse | 以定期报告"主要会计数据"章节为准 |
| 涉诉/执行 | wenshu / zxgk | 动态数据，注意时效 |
| 立案/处分 | csrc / szse / sse | 以交易所纪律处分决定书为准 |
| 预重整/重整 | pccz.court.gov.cn + 公司公告 | 以法院决定书为准 |

## 使用时点规范

- 工商信息：标注"数据截至 YYYY-MM-DD"
- 财务信息：标注报告期（如"2025 年度 / 2026 年半年度"）
- 司法信息：标注检索基准日
- 监管信息：标注处分决定书文号