#!/usr/bin/env python3
"""初始化合同模板文件夹"""

import os
from pathlib import Path

base = str(Path(__file__).resolve().parent.parent / "references" / "template-library")

dirs = [
    "供用水电气热力合同", "赠与合同", "保证合同", "租赁合同",
    "融资租赁合同", "保理合同", "物业服务合同", "行纪合同",
    "中介合同", "保管合同", "仓储合同", "建设工程合同",
    "运输合同", "技术合同", "知识产权合同", "肖像许可使用合同",
    "土地承包经营合同", "合伙合同"
]

for d in dirs:
    path = os.path.join(base, d)
    os.makedirs(path, exist_ok=True)
    template_file = os.path.join(path, "_标准模板.md")
    if not os.path.exists(template_file):
        with open(template_file, "w", encoding="utf-8") as f:
            content = f"""# {d}

> 请导入您的标准模板

本文件夹用于存放{d}类型的合同模板。

## 导入方式

1. 将您的合同模板文件命名为`_标准模板.md`
2. 或告诉AI："帮我导入XX合同模板"
"""
            f.write(content)

print("合同模板文件夹初始化完成")
