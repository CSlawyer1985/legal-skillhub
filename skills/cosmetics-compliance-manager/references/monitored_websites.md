# 化妆品合规法规监控网站列表

本目录包含需要定期监控的化妆品法规网站信息。

## 国内官方机构

| 网站名称 | URL | 说明 |
|---------|-----|------|
| 国家药监局化妆品法规 | https://www.nmpa.gov.cn/hzhp/hzhpfgwj/index.html | 国家药品监督管理局化妆品法规文件 |
| 中检院通知公告 | https://www.nifdc.org.cn/nifdc/bshff/hzhpjssp/hzpsptzgg/index.html | 中国食品药品检定研究院化妆品通知 |
| 化妆品法规中心 | https://law.cosmmate.com/rule/ | 化妆品法规汇总，含国家/地方法规 |

## 行业数据库

| 网站名称 | URL | 说明 |
|---------|-----|------|
| 妆合规-瑞旭集团 | https://zhg.cirs-group.com/product-and-service/china-cosmetic-regulation | 化妆品一站式数字化合规服务平台 |
| 食药法规网 | https://law.pharmnet.com.cn/laws/index_c_2.html | 食品药品化妆品法规数据库 |
| 化妆品违禁词网 | http://www.hzpwjc.cn/hao/hao123.html | 化妆品行业法规资源导航站 |

## 检测规则

1. **检测频率**：每天凌晨4:00自动执行
2. **检测方式**：获取页面内容并计算哈希值
3. **变化判断**：哈希值与上次记录不同时视为有更新
4. **更新处理**：有更新时自动抓取最新内容并更新技能文档

## 监控指标

- 法规文件发布数量变化
- 新公告/通知出现
- 政策解读更新
- 地方法规新增
- 国际法规变化