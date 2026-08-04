# Element-based｜要素式起诉状

将旧诉状、合同、聊天记录等案件材料填写为 67 类要素式诉状 Word 草案，供律师核对后使用。

## 内容

- 67 类诉状、申请书模板及案由索引
- 当事人主体行筛选、地址同步、勾选与要素填充
- Word/WPS 表格版式处理：清除缩进、保留字号、标题居中、落款分行

## 安装

将本仓库目录安装到 Codex 或 WorkBuddy 的 skills 目录，保留 `assets`、`references` 和 `scripts` 目录结构。

运行依赖：Python 3.8+、`python-docx`。

## 使用

1. 在 `assets/template_index.json` 中选择案由并读取该模板的字段。
2. 整理值表 JSON，拆分主体的模板需填写 `party_types`。
3. 执行：

```bash
python scripts/fill_complaint.py \
  --template "assets/templates/<模板文件>.docx" \
  --values "<值表>.json" \
  --out "<结果>.docx"
```

完整的生成规则见 [SKILL.md](SKILL.md)。

## 注意

生成结果为草案。提交前请核对当事人信息、诉讼请求、事实依据、调解意愿、日期及 Word/WPS 版式。
