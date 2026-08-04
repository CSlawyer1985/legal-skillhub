# Changelog

## 1.0.0-rc.4-candidate - 2026-07-23

- 新增 `professional_service.litigation_visualization` 按需扩展，不增加顶层产物类别。
- 固化 `L2-05` 九锚点、anchor-map、handoff、source ledger、隐私和 fail-closed 五门。
- 保持诉讼可视化 renderer 独立；母 Skill 不新增渲染依赖，不允许下游反写 L2、SSOT 或法院件。
- 新增 HOLD 示例、漂移拒绝集和独立 handoff validator。
- 本版本仅为 workspace candidate；未写正式 Skill、未安装、未晋升、未上传、未外传或发布。

## 1.0.0-rc.3 - 2026-07-21

- 将领域 donor 门禁改为 inventory 与逐 gate 决策集合严格相等，漏项或重复即 HOLD。
- 新增法院提交件与专业服务件的结构化输出契约；派生物固定为只读，治理 sidecar 物理分离。
- 新增法院可见文本零治理词、固定字体双遍逐页渲染和完整案/HOLD 案双 E2E 门。
- 将物理安装观察、安装授权收据与生产晋升授权分开记录，不追认历史 RC1 的授权状态。
- 按用户范围锁定，本 RC 不新增产物类别，也不吸收其他派生产物 donor。
- 扩展静态验证和单元测试至 20 项；RC3 真实 E2E 与独立验收仍待完成。

## 1.0.0-rc.2 - 2026-07-18

- 统一入口索引与运行时规则为十二阶段（阶段 0-11）。
- 将流水线和 manifest 的单元测试计数统一为 13/13 PASS。
- 为桌面交付重新生成完整 checksums 和 UTF-8 路径 ZIP。
- 按用户最终需求重申，将 GEO donor 明确登记为姚金刚（`yaojingang/GEORank`）。
- 不改变蒸馏、验证、隐私或 GEO 能力；外部发布仍需单独授权。

## 1.0.0-rc.1 - 2026-07-18

- 建立律师专用案件、法律书籍、课程和实务经验统一蒸馏流水线。
- 以原创案由诉讼方法论为基底，完成仓颉与 GEORank 的 Sublation 比较。
- 新增法律四重验证、答案键隔离、三层隐私架构和十一类 HOLD。
- 新增 GEO 公开投影、引用忠实度、查询集和重复测量协议。
- 新增原子知识记录 schema、本地验证器和回归测试。
- 保持本地候选状态，未安装、未晋升、未对外发布。
