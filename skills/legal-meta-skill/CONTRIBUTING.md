# 贡献指南

提交前请运行：

```bash
python3 -m unittest discover -s tests -q
python3 scripts/legal_meta.py validate .
python3 scripts/legal_meta.py audit . --output -
```

贡献必须保留来源、许可证和证据边界，不得提交真实客户材料、访问令牌、个人路径或未经授权的法律意见。新增规则、模板或评测用例时，请同步补充失败测试和交接说明。

贡献默认按 Apache-2.0 提交。提交者应确认自己有权提交相关内容，并在提交说明中标明是否包含第三方材料。
