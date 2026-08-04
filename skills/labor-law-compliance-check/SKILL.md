---
name: 劳动法合规速查
id: z-labor-law-check
description: 列常见用工合规风险点（合同/工时/解除/女职工），给自查 checklist。明确非律师，重大找专业。
version: "1.0.0"
agent_created: true
platforms: [workbuddy, claude, cursor, codex, windsurf, gemini, copilot, openclaw]
category: 人事
slug: z-labor-law-check
displayName: 劳动法合规速查
summary: 常见用工风险点checklist（引导专业审核）
license: MIT
disable: false
---

# 劳动法合规速查（z-labor-law-check）

常见用工风险点checklist（引导专业审核）

## 触发词
「常见用工风险点checklist（引导专业审核）」相关提问；如「帮我整理会议纪要」「写个放假通知」「用印怎么登记」「办公用品盘点」「安排出差」「接待客户流程」「团建怎么策划」「档案怎么归档」「制度版本管理」「写招聘JD」「入离转调清单」「面试评估」「排班考勤」「劳动合同提醒」「社保公积金」「绩效面谈」「员工关怀」「离职面谈」「劳动法自查」「培训规划」「人才盘点」「花名册」

## 流程
1. 明确用户场景与目标（会议/通知/用印/招聘/合同等）。
2. 调用本技能 `scripts/run.py` 读取 `data/checklist.json` 生成框架或清单。
3. 输出结构化建议，并附适用边界与免责说明。
4. 数据写入技能目录相对路径 `data/`，纯本地、不云传。

## 注意
- 本技能为行政/人事工作**框架与清单辅助工具**，不替代专业判断与官方流程。
- 涉及劳动法、合同、薪酬、人事隐私等，以最新法律法规与公司制度为准。
- 用户数据（纪要、花名册、合同节点等）均存本地，不上云、不对外传。

## 红线（P0）
- 不模拟审批/不代操作印章证照等高风险动作。
- 不替代律师、不编具体法律/社保数字，重大争议引导专业审核。
- 人事敏感信息最小化收集、本地存储、不云传。
- 公文/通知仅出模板，发布前需用户按规范审核。

## 适用边界
- 适用于企业行政与人事日常工作的框架梳理、清单生成、提醒辅助。
- 不适用于法律代理、专业审计、系统人事软件替代。

## 红蓝对抗记录
蓝军指出法律专业性强→非律师不替代；以最新劳动法为准；风险点标注严重级。

## 跨平台安装
本技能通用，可装于以下客户端（技能目录相对路径，无平台独占依赖）：
- WorkBuddy: `~/.workbuddy/skills/z-labor-law-check/`
- Claude: `~/.claude/skills/z-labor-law-check/`
- Cursor: `~/.cursor/skills/z-labor-law-check/`
- 其他兼容客户端同理，整目录复制即可。
