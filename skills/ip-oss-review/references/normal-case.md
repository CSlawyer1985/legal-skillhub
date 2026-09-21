# 正常样例：SaaS项目依赖清单审查

## 输入

用户提交一个Node.js项目的package.json，项目为SaaS部署模式（用户通过浏览器访问，不分发二进制）。

依赖清单包含：
- express (MIT)
- lodash (MIT)
- mongoose (MIT)
- passport (MIT)
- mongodb-driver (Apache-2.0)
- node-forge (BSD-3-Clause 或 GPL-2.0 双许可)

## 期望行为

1. 加载团队实务配置文件，确认实务画像和OSS策略
2. 识别审查范围为"依赖清单"，部署模式为"SaaS"
3. 逐包分类许可证：
   - express → 宽松型 (MIT)
   - lodash → 宽松型 (MIT)
   - mongoose → 宽松型 (MIT)
   - passport → 宽松型 (MIT)
   - mongodb-driver → 宽松型 (Apache-2.0)
   - node-forge → 双许可（BSD-3-Clause 或 GPL-2.0），需确认选择
4. 映射义务到SaaS部署模式：
   - 大部分MIT/Apache-2.0包：仅署名义务
   - node-forge若选择GPL-2.0：SaaS模式下不触发（中国法"发行权"未触发，无"信息网络传播权"问题——GPL不包含AGPL的网络条款）
   - node-forge若选择BSD-3-Clause：仅署名义务
5. 标记风险级别：
   - 大部分包为低风险
   - node-forge为中等风险（双许可需确认选择）
6. 输出备忘录，包含：
   - 底线结论：可以发布，但需确认node-forge使用的许可证
   - 中国法域注释：SaaS模式在中国法下不构成"发行"，GPL-2.0不触发
   - 署名义务清单
   - 审批路由

## 期望输出要点

- 底线结论：项目可发布，但需：(1)确认node-forge使用的许可证分支，(2)在应用中包含所有MIT/Apache署名
- 分类统计：5宽松型 + 1双许可
- 中国法域注释明确：SaaS不构成"发行"，GPL-2.0在中国法下不触发
- 监管合规章节：若项目不涉及关键信息基础设施或重要数据，标注"未触发"

## 应触发的人工gate或来源标签

- node-forge双许可选择需人工确认
- 中国法域注释中关于"GPL-2.0在SaaS下不触发"的分析标记为`[模型知识 — 需核验]`（因该结论虽为通说，但中国尚无直接判例）
- 署名义务清单标注来源`[用户提供]`（从实际LICENSE文件读取）
