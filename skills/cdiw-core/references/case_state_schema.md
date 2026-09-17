# case_status.md数据结构与读写规范（case_state_schema）

## 一、案件工作区目录结构（运行时由scripts/case_state_manager.py创建）

```
案件工作区/
  case_status.md        # 唯一权威状态源
  meetings/             # 会见纪要（meeting_minutes_template.md格式）
  receptions/           # 接待记录
  communications/       # 沟通留痕（communication_log.md格式）
  documents/            # 生成文书（草稿与定稿分版本）
  reports/              # 期限报告、认罪认罚分析报告、量刑测算报告等
  confirmations/        # 选择笔录提示件、阶段确认表、月度工作清单
  retrieval/            # 检索档案（检索式全版本、命中清单、类案六要素表——检索线写入）
  evidence/             # 证据线索固定清单、矛盾排查报告（取证线写入）
  logs/                 # 脚本运行日志（trace_id、参数、结果）
```

## 二、case_status.md数据结构（YAML，生成于案件工作区根目录）

```yaml
case_id: CASE-YYYYMMDD-NNN              # 创建日期及当日序号
case_name: 某某涉嫌××罪案                # 脱敏代称
created_at / updated_at: YYYY-MM-DD HH:MM
basic_info:
  client_alias: ××                       # 当事人代称，禁真实姓名
  charges: [××罪]                        # 罪名数组，罪名数即数组长度
  measure: {type: 刑事拘留|取保候审|监视居住|逮捕, start: YYYY-MM-DD}
  detention_place / authority / handler: ××（均脱敏）
  offense_date / client_age / victim_age: ××（年龄待核实时标【待核实】）
  offense_count: ×                       # 作案次数
  cross_region: true|false
  accomplices_total: ×                   # 含本人
  prior_record / arrest_manner: ××       # 到案方式为自首核实线索
  family_contact: {alias: ××, relation: ××}
  family_demand: ×××
complexity: {charge_count, fact_count, accomplice_count, level: 标准|复杂}
stage: {current: 侦查|审查起诉|一审|二审|死刑复核|执行|申诉,
        substage: 批捕前|批捕后|侦查终结前|阅卷期|正常审查期间|退查期间|审查起诉到期前|庭前|庭审期间|一审补侦期间|庭后判决前（侦查/审查起诉/一审内取值，与 current 匹配；二审单独列示不设子阶段）,
        entered_at, history: []}
emergency: {level: 红|橙|黄|蓝, assessed_at}
deadlines:                              # 期限线写入
  - {type, start, end, days_remaining, basis: 刑事诉讼法第××条〔2018年修正〕,
     legal_expiry: 法定届满日, authority_action_day: 机关实际动作日, lawyer_alert_day: 律师预警日,
     shift_notice: {kind: 前移|顺延, original_day, adjusted_day, reason}（发生前移/顺延时必填，无则 null）,
     warnings: [{date, node, action, status: 待执行|已执行}]}
meetings:                               # 会见线写入（追加型）
  - {seq: 1–21|增见, node, date, lawyer, minutes, summary,
     pending_verify: [], family_feedback: []}
receptions:                             # 接待线写入（追加型）
  - {node, date, attendees, demands: [], handled}
communications:                         # 沟通线写入（追加型）
  - {seq, target: 公安|检察|法院, date, purpose, outcome,
     evidence: 回执|通话记录|none, next_action}
documents:                              # 文书线写入（追加型）
  - {type: 意见类|申请类|备用类|报告类, name, date,
     status: 草稿|待律师确认|已签署|已提交, path}
service_progress:                       # 服务进程（核心字段）
  stage: 侦查
  checklist:                            # 按investigation_service_checklist.md载入
    - {category: 接待|会见|沟通|文书, item, baseline, completed,
       details: [{date, lawyer, minutes, summary}], status: 完成|进行中|未完成}
  monthly_worklog: [{month, items: [{date, lawyer, task, minutes}]}]
  confirmations: [{date, method: 微信回复收到|书面签署, content, archived}]
consents:                               # 强制人工复核节点留痕
  - {item: 辩护路线选择|认罪认罚方案|量刑意见授权|对外文书确认,
     date, parties: 当事人及家属, note: 选择笔录已制作|待制作}
todos: [{priority: 红|橙|黄|蓝, task, deadline, workstream}]
files: [{path, desc, created_at}]
```

## 三、读写规范

（1）**唯一写入通道**：全部修改经scripts/case_state_manager.py执行，各工作线不得直接编辑该文件。

（2）**追加不覆盖**：日志型字段只增不改，更正以新记录附corrected_from索引实现。

（3）**字段校验**：日期一律YYYY-MM-DD格式，枚举字段按既定取值，写入前经脱敏规则检查。

（4）**冲突处理**：用户口述与文件记录冲突时以文件为准，输出差异提示，律师确认后更新留痕。

（5）**断点续接加载顺序**：stage—service_progress—todos—emergency，据此恢复上下文并输出路由建议。

（6）**阶段终结**：读取checklist按service_progress_confirm.md生成确认表文本，未完成事项自动转入todos并列入“衔接事项”。
