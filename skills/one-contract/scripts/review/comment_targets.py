"""源文档批注的读取与定位。

用途有两个，都是 2026-09-17 实测暴露的缺口：

1. **回复源批注**（A3）：审阅件应当能对源文档里的既有批注形成**线程化回复**
   （`w15:paraIdParent` 指向父批注）。本模块提供"批注 id ↔ 锚定文本 ↔ 作者/正文"的映射，
   供 review plan 的 `responses` 定位目标。
2. **悬空批注**（B1）：`comments.xml` 里存在、但 `document.xml` 中**没有任何锚点**的批注
   （Word 修订窗格里看不到，正文也无从对应）。这类批注必须能被识别出来，
   并在处置时**原样导出**，不得静默丢弃。

底层是 OOXML 直读，不依赖 `docx_engine` 的编辑态对象，因此也能用于**只读检查**。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from defusedxml import minidom

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

#: `plan.responses[].stance` 取值 → 报告与日志里显示的处理口径。
#: 审查人只做"核对/补充/说明"，**不使用"采纳、同意、接受、认可"等当事人表态**。
RESPONSE_STANCES = {
    "already_present": "现稿已体现",
    "added_this_round": "本轮已补充",
    "declined": "未按该意见修改",
    "pending_fill": "仍需填写／待确认",
}


@dataclass(frozen=True)
class SourceComment:
    """源文档里的一条批注。"""

    comment_id: int
    author: str
    date: str
    text: str
    anchor_text: str
    anchored: bool

    def as_dict(self) -> dict:
        return {
            "comment_id": self.comment_id,
            "author": self.author,
            "date": self.date,
            "text": self.text,
            "anchor_text": self.anchor_text,
            "anchored": self.anchored,
        }


def _iter_elements(node):
    for child in getattr(node, "childNodes", []):
        if child.nodeType == child.ELEMENT_NODE:
            yield child
            yield from _iter_elements(child)


def _element_text(elem) -> str:
    """拼接元素下所有 `w:t` / `w:delText` 的文本。"""
    parts: list[str] = []
    for tag in ("w:t", "w:delText"):
        for t in elem.getElementsByTagName(tag):
            for child in t.childNodes:
                if child.nodeType == child.TEXT_NODE:
                    parts.append(child.data)
    return "".join(parts)


def _load_comment_definitions(comments_path: Path) -> dict[int, dict]:
    if not comments_path.exists():
        return {}
    dom = minidom.parse(str(comments_path))
    definitions: dict[int, dict] = {}
    for comment in dom.getElementsByTagName("w:comment"):
        raw_id = comment.getAttribute("w:id")
        if raw_id == "":
            continue
        definitions[int(raw_id)] = {
            "author": comment.getAttribute("w:author"),
            "date": comment.getAttribute("w:date"),
            "text": _element_text(comment).strip(),
        }
    return definitions


def _collect_anchor_text(document_path: Path) -> dict[int, str]:
    """按文档顺序收集每个批注锚点覆盖的正文文本。"""
    if not document_path.exists():
        return {}
    dom = minidom.parse(str(document_path))
    buffers: dict[int, list[str]] = {}
    open_ids: set[int] = set()
    for elem in _iter_elements(dom.documentElement):
        tag = elem.tagName
        if tag == "w:commentRangeStart":
            raw = elem.getAttribute("w:id")
            if raw != "":
                open_ids.add(int(raw))
                buffers.setdefault(int(raw), [])
        elif tag == "w:commentRangeEnd":
            raw = elem.getAttribute("w:id")
            if raw != "":
                open_ids.discard(int(raw))
        elif tag in ("w:t", "w:delText") and open_ids:
            text = "".join(
                child.data for child in elem.childNodes if child.nodeType == child.TEXT_NODE
            )
            for cid in open_ids:
                buffers[cid].append(text)
    return {cid: "".join(chunks) for cid, chunks in buffers.items()}


def load_source_comments(unpacked_dir: str | Path) -> list[SourceComment]:
    """读取拆包目录里的全部源批注（含悬空批注），按 id 升序返回。"""
    root = Path(unpacked_dir)
    definitions = _load_comment_definitions(root / "word" / "comments.xml")
    anchors = _collect_anchor_text(root / "word" / "document.xml")
    comments: list[SourceComment] = []
    for cid in sorted(definitions):
        info = definitions[cid]
        anchor_text = anchors.get(cid)
        comments.append(
            SourceComment(
                comment_id=cid,
                author=info["author"],
                date=info["date"],
                text=info["text"],
                anchor_text=anchor_text or "",
                anchored=anchor_text is not None,
            )
        )
    return comments


def orphan_comments(comments: Iterable[SourceComment]) -> list[SourceComment]:
    """没有任何锚点的批注（Word 修订窗格里不可见）。"""
    return [item for item in comments if not item.anchored]


def find_comment(
    comments: Iterable[SourceComment],
    *,
    comment_id: int | None = None,
    anchor_text: str | None = None,
    occurrence: int = 1,
) -> SourceComment | None:
    """按 id 或文本定位一条源批注；定位不到返回 None（调用方据此降级，**不猜**）。

    `anchor_text` 会同时匹配**批注锚定的正文**与**批注自身的内容**：
    实践中编写 review plan 时引用的是"对方那条批注说了什么"（内容），
    而锚定的正文常常只是一个句号，只匹配锚定正文会定位不到。
    """
    items = list(comments)
    if comment_id is not None:
        for item in items:
            if item.comment_id == int(comment_id):
                return item
        return None
    if anchor_text:
        matched = [
            item for item in items if anchor_text in item.anchor_text or anchor_text in item.text
        ]
        if 0 < occurrence <= len(matched):
            return matched[occurrence - 1]
    return None
