# GMP 合规基线（示例：化学药固体制剂企业）

> 这是 gmp-compliance-check 脚本的内置示例基线。脚本严格按下列格式解析：
> - `## 域名  weight=N` 定义一个合规域（权重用于覆盖度加权）
> - `- 检查项：xxx  risk=高|中|低` 定义一个检查项
> - 紧接两行 `keywords: ...`（用 `、` `,` 分隔）和 `advice: ...`（单行整改建议）
>
> 您可按客户品种/剂型新建专属基线目录（如 `data/<客户>/`），在 `review.py` 用 `--client` 指向。

## 数据完整性 (Data Integrity)  weight=18
- 检查项：ALCOA+ 原则落地  risk=高
  keywords: ALCOA、数据完整性、可归因、清晰、同步、原始、准确
  advice: 在数据治理 SOP 中明确 ALCOA+ 9 项原则，并落地于记录管理与系统能力。
- 检查项：防篡改与原始数据  risk=高
  keywords: 防篡改、不可篡改、原始数据、元数据
  advice: 关键系统启用不可关闭的审计追踪，关键字段不得覆盖写，保留原始痕迹。
- 检查项：数据可读性与留痕  risk=高
  keywords: 可读、可读性、留痕、原始痕迹、前后对比
  advice: 修改/删除须保留前后值与操作人、操作时间、操作原因。

## 计算机化系统验证 (CSV)  weight=14
- 检查项：URS 与验证生命周期  risk=高
  keywords: 计算机化系统验证、CSV、URS、用户需求、用户需求说明
  advice: 建立 URS，按 GAMP 5 风险分级实施 IQ/OQ/PQ 与定期复核。
- 检查项：IQ/OQ/PQ 三阶段  risk=高
  keywords: IQ、OQ、PQ、安装确认、运行确认、性能确认
  advice: 至少完成安装、运行、性能三个阶段的确认并形成报告。
- 检查项：风险评估与供应商审计  risk=中
  keywords: 风险评估、供应商审计、供应商评估、GAMP
  advice: 关键系统按 GAMP 分类做风险评估，并对供应商进行资质审计。

## 审计追踪 (Audit Trail)  weight=12
- 检查项：关键操作审计追踪  risk=高
  keywords: 审计追踪、审计跟踪、操作日志
  advice: 关键操作（登录、创建、修改、删除、签发、审批）启用审计追踪，不可由普通用户关闭。
- 检查项：定期审计审核  risk=中
  keywords: 审计报告、定期审核、审计审核
  advice: 质量部门定期审核审计日志，留存审核记录。

## 电子签名与权限 (E-Signature & Access)  weight=12
- 检查项：唯一身份与密码策略  risk=高
  keywords: 电子签名、签名、唯一账号、密码策略、复杂度、有效期
  advice: 每个员工有唯一账号，密码符合复杂度、有效期、错误锁定策略。
- 检查项：角色权限矩阵  risk=高
  keywords: 权限、角色、分级授权、防共享
  advice: 建立角色与权限矩阵，按岗位职责授权，禁止账号共享。

## 批次与物料追溯 (Traceability)  weight=10
- 检查项：批次主数据与谱系  risk=高
  keywords: 批次、批记录、物料平衡
  advice: 每批有唯一批号，全程贯穿；记录投入产出，建立物料平衡。
- 检查项：正反向追溯  risk=中
  keywords: 追溯、正向追溯、反向追溯
  advice: 支持从批号到原料的正向追溯和从原料到下游成品的反向追溯。

## 变更控制 (Change Control)  weight=8
- 检查项：变更闭环  risk=中
  keywords: 变更控制、变更管理、变更申请、变更评估
  advice: 变更按申请→评估→批准→实施→确认→关闭的闭环管理。
- 检查项：变更对验证与培训的影响  risk=中
  keywords: 变更验证、变更再验证、影响评估
  advice: 关键变更须评估对验证、培训、文件的影响并执行相应动作。

## 偏差与CAPA (Deviation & CAPA)  weight=8
- 检查项：偏差识别与调查  risk=中
  keywords: 偏差、偏差调查、根本原因
  advice: 偏差及时识别，按 5Why/FTA/FMEA 调查根本原因。
- 检查项：CAPA 闭环  risk=中
  keywords: CAPA、纠正预防措施、有效性确认
  advice: 制定纠正预防措施并验证有效性后关闭。

## 备份与容灾 (Backup & DR)  weight=8
- 检查项：备份策略与可恢复性  risk=中
  keywords: 备份、归档、恢复
  advice: 制定备份策略（频率/保留期/介质/异地），定期验证可恢复性。
- 检查项：容灾与业务连续性  risk=中
  keywords: 灾备、容灾、业务连续性、RTO、RPO
  advice: 明确 RTO/RPO，定期演练，保留演练记录。

## 时间同步 (Time Sync)  weight=5
- 检查项：NTP 统一时钟  risk=中
  keywords: 时间同步、NTP、时钟、时区
  advice: 关键系统接入 NTP 统一时钟，时区一致，关键记录时间不可篡改。

## 培训与资质 (Training)  weight=5
- 检查项：培训矩阵与上岗资格  risk=低
  keywords: 培训、资质、上岗资格
  advice: 按岗位建立年度培训矩阵，关键岗位通过理论与实操考核取得上岗资格。
- 检查项：复训与再认证  risk=低
  keywords: 复训、再认证、再确认
  advice: 定期复训，资质到期再认证。
