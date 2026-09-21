"""源文档批注的卫生处置：**悬空批注**。

问题（2026-09-17 实测暴露）：源合同里可能带着**没有任何锚点**的批注——
它存在于 `word/comments.xml`，但 `word/document.xml` 里既没有 `commentRangeStart`
也没有 `commentRangeEnd`。Word 修订窗格里看不到它，正文也无从对应，
而质量门会因此报 `批注 N 锚点不闭合` 直接把交付卡住（**检出是对的，但没有处置出口**）。

三种策略：

| 策略 | 行为 |
|---|---|
| `reject` | 不动源文件，让质量门按原样报错（需要人工介入时用） |
| **`quarantine`（默认）** | 把悬空批注**原样导出**到 `orphan-comments.json`，再从工作副本移除 |
| `strip` | 直接移除；内容只留执行日志 |

无论哪种策略，**批注内容都必须留痕**——悬空批注往往承载着尚未落实的编辑意见
（实测案例：一条"增加：长期展示样机为合作投放，不收取租赁费"的意见正是如此）。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from defusedxml import minidom

try:  # 包内导入
    from .comment_targets import SourceComment, load_source_comments, orphan_comments
except ImportError:  # 直接以脚本方式运行（无包上下文）时的扁平导入
    from comment_targets import SourceComment, load_source_comments, orphan_comments

ORPHAN_POLICIES = ("reject", "quarantine", "strip")


def _remove_comments(unpacked_dir: Path, comment_ids: list[int]) -> list[int]:
    """从 comments.xml / commentsExtended.xml 中移除指定批注；返回实际移除的 id。"""
    if not comment_ids:
        return []
    targets = {int(cid) for cid in comment_ids}
    removed: list[int] = []
    para_ids: set[str] = set()

    comments_path = unpacked_dir / "word" / "comments.xml"
    if comments_path.exists():
        dom = minidom.parse(str(comments_path))
        for comment in list(dom.getElementsByTagName("w:comment")):
            raw_id = comment.getAttribute("w:id")
            if raw_id == "" or int(raw_id) not in targets:
                continue
            for paragraph in comment.getElementsByTagName("w:p"):
                para_id = paragraph.getAttribute("w14:paraId")
                if para_id:
                    para_ids.add(para_id)
                    break
            comment.parentNode.removeChild(comment)
            removed.append(int(raw_id))
        comments_path.write_bytes(dom.toxml(encoding="utf-8"))

    extended_path = unpacked_dir / "word" / "commentsExtended.xml"
    if para_ids and extended_path.exists():
        dom = minidom.parse(str(extended_path))
        for entry in list(dom.getElementsByTagName("w15:commentEx")):
            if entry.getAttribute("w15:paraId") in para_ids:
                entry.parentNode.removeChild(entry)
        extended_path.write_bytes(dom.toxml(encoding="utf-8"))

    ids_path = unpacked_dir / "word" / "commentsIds.xml"
    if para_ids and ids_path.exists():
        dom = minidom.parse(str(ids_path))
        for entry in list(dom.getElementsByTagName("w16cid:commentId")):
            if entry.getAttribute("w16cid:paraId") in para_ids:
                entry.parentNode.removeChild(entry)
        ids_path.write_bytes(dom.toxml(encoding="utf-8"))

    return removed


def resolve_orphan_comments(
    unpacked_dir: str | Path,
    *,
    policy: str = "quarantine",
    export_path: Path | None = None,
) -> dict[str, Any]:
    """按策略处置悬空批注。返回可写入执行日志的结果对象。"""
    root = Path(unpacked_dir)
    if policy not in ORPHAN_POLICIES:
        raise ValueError(f"未知的悬空批注策略：{policy!r}（允许：{'/'.join(ORPHAN_POLICIES)}）")

    comments = load_source_comments(root)
    orphans: list[SourceComment] = orphan_comments(comments)
    result: dict[str, Any] = {
        "policy": policy,
        "count": len(orphans),
        "orphans": [item.as_dict() for item in orphans],
        "removed_ids": [],
        "status": "none",
    }
    if not orphans:
        return result

    if policy == "reject":
        result["status"] = "rejected"
        result["message"] = (
            "源文档存在悬空批注；按 --orphan-comments reject 保留原样，交由质量门报错"
        )
        return result

    if policy == "quarantine" and export_path is not None:
        export_path.parent.mkdir(parents=True, exist_ok=True)
        export_path.write_text(
            json.dumps(
                {
                    "description": (
                        "源文档中没有任何锚点的批注（Word 修订窗格不可见）。"
                        "已从工作副本移除，内容在此原样留存。"
                    ),
                    "count": len(orphans),
                    "orphans": [item.as_dict() for item in orphans],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        result["export_path"] = str(export_path)

    result["removed_ids"] = _remove_comments(root, [item.comment_id for item in orphans])
    result["status"] = "quarantined" if policy == "quarantine" else "stripped"
    result["message"] = "悬空批注已从工作副本移除，内容已留存"
    return result
