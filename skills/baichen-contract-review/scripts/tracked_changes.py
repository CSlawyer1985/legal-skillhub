# Track Changes 生成脚本
"""
本脚本用于在Word文档中生成带修改痕迹（Track Changes）的合同修改版。

## 用法

由 Agent 在执行合同审查时调用，传入原合同路径和修改指令列表，输出带Track Changes的修改版合同。

```python
from tracked_changes import generate_modified_contract

modifications = [
    {
        "old_text": "原文片段",
        "new_text": "新文片段",
        "description": "修改说明"
    },
    ...
]

generate_modified_contract(
    input_path="原始合同.docx",
    output_path="修改版合同.docx",
    modifications=modifications
)
```

Agent 需要先读取原始合同的段落文本，确定准确的 old_text，然后构建 modifications 列表传入。
"""


def generate_modified_contract(input_path: str, output_path: str, modifications: list) -> None:
    """生成带 Track Changes 的修改版合同。"""
    raise NotImplementedError("Track Changes 生成功能待实现")
