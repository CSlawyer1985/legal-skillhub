#!/usr/bin/env python3
"""Contract Modify Scripts - 合同修订文档操作工具

提供合同「修订模式」的文档操作功能（基于 scripts/docx/ 的 XML 级修订引擎）。

导入方式（两种均可）：
    # 方式一：直接导入子模块（apply_modify_plan.py 采用此方式，最稳妥）
    # 前提：已将 scripts/ 目录本身加入 sys.path
    #   import sys
    #   sys.path.insert(0, "/path/to/contract-modify/scripts")
    from docx.reviewer import ContractReviewer

    # 方式二：经本包导入
    # 前提：已将 scripts/ 的【父目录】(即 contract-modify/) 加入 sys.path
    #   import sys
    #   sys.path.insert(0, "/path/to/contract-modify")
    from scripts import ContractReviewer

    reviewer = ContractReviewer("workspace/unpacked")
    node = reviewer.find_text("甲方")
    reviewer.add_comment(node, "建议明确甲方的具体法律主体")
    reviewer.save()
"""

from .docx.reviewer import ContractReviewer

__all__ = ["ContractReviewer"]
