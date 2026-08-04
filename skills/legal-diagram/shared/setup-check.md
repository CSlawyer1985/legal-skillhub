# 设置检查（共享）

会话缓存的依赖检查。由 `tutorial.md`、`direct.md`、`extract.md` 调用。

## 流程

1. **先查缓存。** 若本会话已设置 `_setup_ok = true` → 跳过脚本。返回 ok。
2. **运行脚本。** `python scripts/check_setup.py`。解析 JSON：`{ok, python_version, installed[], missing[], optional{}}`。`optional` 键列出可选包及其 `installed`、`pip_name` 和 `purpose`；它们的缺失不影响 `ok`。
3. **`ok=true` 时。** 记录已安装包。设置 `_setup_ok = true`。返回 ok。
4. **`missing` 非空时。** 打印精确缺失列表加一行安装命令：
   `pip install -r requirements.txt -c constraints.txt`
   - 教程模式：停止。“安装后重新运行。”
   - 直接模式：一行消息。提供粘贴文本回退（`.md`/文本提取无需第三方依赖）。
5. **崩溃时（非零退出、无 JSON）。** Python 不在 PATH 中。打印：“Python not found. Ensure Python 3.9+ installed and on PATH.”（未找到 Python。请确保已安装 Python 3.9+ 且在 PATH 中。）不尝试变通方案。
6. **退化情形 `ok=true, installed=[]` 时。** 警告：“依赖列表为空但无错误。”谨慎继续。

## 说明

- 仅 `.docx`/`.pdf`/`.pptx`/`.xlsx` 解析和 HTML 导出需要第三方库。`.md`、`.txt`、粘贴文本和对话上下文仅靠标准库运行；缺失依赖绝不阻塞这些路径。
- 缓存键按会话而非按调用。干净通过后绝不重新运行脚本。
