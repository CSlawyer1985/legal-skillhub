# Skill 埋点说明

本文描述 **cha88-base** 中 Skill 调用埋点的上报时机、请求内容与失败策略，便于对接网关统计与二次开发对齐行为。

## 1. 作用概述

埋点用于在 **Skill 网关**侧统计 Skill 被调用的次数与基础元信息（名称、版本、渠道、场景）。实现集中在 `scripts/_tracker.py` 的 `report_skill_usage()`，由统一 CLI 入口 `cli.py` 在命令生命周期末尾触发。

## 2. 上报时机

| 场景 | 是否上报 | 说明 |
|------|----------|------|
| 已识别子命令（如 `cha88_search`、`cha88_detail`、`configure`），且子命令 `main()` **正常执行完毕** | **是** | 无论业务 JSON 中 `success` 为 `true` 或 `false`，均在子命令返回后上报一次。 |
| 未传入子命令、子命令名不在注册表、或展示用法后 `sys.exit(1)` | **否** | `cli.py` 在调用子模块前即退出，不会执行埋点逻辑。 |
| 子命令内 `argparse` 报错并 `sys.exit`（如必填参数缺失） | **否** | 进程在 `module.main()` 内退出，**不会**回到 `cli.py` 的埋点代码。 |
| 子命令 `main()` 抛出**未捕获**异常 | **否** | 异常向上传播，埋点代码未执行。 |

**小结**：埋点表示「一次 CLI 子命令入口已跑完主流程」，偏 **会话级 / 调用次数** 统计。

## 3. 上报接口与传输

| 项 | 值 |
|----|-----|
| 方法 | `POST` |
| 路径 | `/api/reportSkillsUsage/1.0.0` |
| 完整 URL | 与业务 API 相同网关：`https://skills-gateway.1688.com` + 路径 |
| 请求体 | JSON，`Content-Type: application/json; charset=utf-8` |
| 鉴权 | 与能力调用一致：通过 `get_auth_headers()` 注入签名 |

## 4. 请求体字段

| 字段 | 类型 | 取值说明 |
|------|------|----------|
| `apiName` | `null` | 固定为 JSON `null` |
| `skillsName` | string | Skill 名称，来自环境变量 `SKILL_NAME`，缺省为 `cha88-base` |
| `version` | string | Skill 版本，来自 `SKILL_VERSION`，缺省为 `1.0.0` |
| `scene` | string | 固定为 `"CLI"` |
| `channel` | string | 发布渠道，来自 `SKILL_CHANNEL`，缺省为 `clawhub` |

## 5. 失败与日志策略

- `report_skill_usage()` 整体包裹在 `try/except` 中：**任意异常均不向外抛出**
- 失败时通过 logger `cha88_tracker` 输出 **DEBUG** 级别日志
- `cli.py` 在调用 `report_skill_usage()` 外层还有一次 `try/except`

## 6. 与模板扩展的关系

新增 `capabilities/<name>/cmd.py` 并注册命令后，只要仍由根目录 `cli.py` 统一调度且在子命令 `main()` 正常返回后回到 `cli.py`，**会自动沿用同一套埋点**。

## 7. 相关文件索引

| 文件 | 职责 |
|------|------|
| `scripts/_tracker.py` | 读取 `.env`、组装请求体、调用 `api_post` 上报 |
| `cli.py` | 命令分发结束后调用 `report_skill_usage()` |
| `scripts/_http.py` | `api_post`：网关地址、签名、重试与错误映射 |
| `SKILL.md` | 面向使用方的环境变量与埋点摘要 |
