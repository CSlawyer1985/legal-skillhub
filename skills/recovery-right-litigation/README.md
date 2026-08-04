# 追偿权纠纷 Skill 平台轻量版

- Skill：`recovery-right-litigation`
- 版本：`1.0.4-platform-lite`
- 许可：`GPL-3.0-only`
- 入口：`SKILL.md`
- 平台画像：单入口、纯文本、无嵌套压缩包、少于 200 文件、小于 10 MB
- 私密空间限定：`false`

先阅读 `PLATFORM-LITE-NOTICE.md` 和 `RIGHTS-AND-RELEASE-NOTICE.md`。本包不包含真实案件数据。

本机验证：

```bash
python3 -B scripts/validate_package.py . --selftest
python3 -B scripts/smoke_test.py .
```
