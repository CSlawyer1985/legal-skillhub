#!/usr/bin/env python3
"""公共资产指纹与 public snapshot 描述符。

契约来源：architecture-contract.md §8.5。

指纹覆盖（五项，缺一不可）：
1. references/review-doctrine.md
2. references/redline-comment-policy.md
3. references/common-clause-doctrine.md
4. assets/knowledge_v2 下全部正式普通文件
5. resolver_semantics_version

算法：文件按 POSIX 相对路径排序，各自算原始字节 SHA-256；
对包含 path、sha256、size 与 resolver 语义版本的 JCS 数组取总 SHA-256。
不得纳入本机绝对路径、mtime、缓存或遍历顺序。

MVP 不复制公共文件到另一快照目录：审查开始时一次性读取并校验，
形成内存不可变投影；public_snapshot_id 即 public_sha256_<聚合哈希>。
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple

from . import models, paths

__all__ = [
    "GLOBAL_DOCUMENT_PATHS",
    "KNOWLEDGE_ASSET_DIR",
    "RESOLVER_SEMANTICS_VERSION",
    "FingerprintError",
    "PublicAssetFingerprint",
    "fingerprint_public_assets",
]

#: 第一层三份全局规则文档（相对 skill 根）
GLOBAL_DOCUMENT_PATHS: Tuple[str, ...] = (
    "references/review-doctrine.md",
    "references/redline-comment-policy.md",
    "references/common-clause-doctrine.md",
)

#: 公共知识资产目录（相对 skill 根）
KNOWLEDGE_ASSET_DIR = "assets/knowledge_v2"

#: 解析语义版本。它进入指纹：任何解析语义变化都必须体现在 public_snapshot_id 上，
#: 从而使绑定旧指纹的客户快照被显式暂停而非静默套用（ADR-022）。
#: 公共资产本身未携带该版本号（asset_manifest 仅有 schema_version/taxonomy_version），
#: 因此由本模块显式持有，并与三份文档、knowledge_v2 一并纳入聚合哈希。
RESOLVER_SEMANTICS_VERSION = "0.1.0"


class FingerprintError(Exception):
    """指纹无法生成。调用方不得降级为使用过期指纹。"""


@dataclass(frozen=True)
class _FileEntry:
    relative_path: str
    source_kind: str
    size_bytes: int
    sha256: str

    def to_schema_dict(self) -> Dict[str, Any]:
        return {
            "relative_path": self.relative_path,
            "source_kind": self.source_kind,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
        }


@dataclass(frozen=True)
class PublicAssetFingerprint:
    """一次加载形成的不可变公共投影指纹。"""

    public_asset_fingerprint: str
    public_snapshot_id: str
    resolver_semantics_version: str
    files: Tuple[_FileEntry, ...]
    projection_hash: str

    def to_snapshot_descriptor(
        self,
        *,
        source_release_version: str,
        loaded_at: str,
    ) -> Dict[str, Any]:
        """构造 public-snapshot-v1 描述符。

        projection_hash 按 §8.5 的「loaded projection」口径生成：对已加载的
        内存投影（文件清单 + resolver 语义版本）取 JCS 哈希。本函数不读取
        资产正文以外的内容，因此该值与文件清单一一对应且可复现。
        """
        return {
            "schema_version": "1.0",
            "snapshot_mode": "fingerprint_and_loaded_projection",
            "public_snapshot_id": self.public_snapshot_id,
            "public_asset_fingerprint": self.public_asset_fingerprint,
            "resolver_semantics_version": self.resolver_semantics_version,
            "source_release_version": source_release_version,
            "loaded_at": loaded_at,
            "files": [entry.to_schema_dict() for entry in self.files],
            "projection_hash": self.projection_hash,
        }


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _collect_files(skill_root: Path) -> List[_FileEntry]:
    """收集被覆盖的文件。只收普通文件，跳过符号链接与 __pycache__。"""
    entries: List[_FileEntry] = []
    for relative in GLOBAL_DOCUMENT_PATHS:
        target = skill_root / relative
        if not target.is_file():
            raise FingerprintError(f"第一层文档缺失，指纹不可信: {relative}")
        entries.append(
            _FileEntry(relative, "global_document", target.stat().st_size, _hash_file(target))
        )

    asset_root = skill_root / KNOWLEDGE_ASSET_DIR
    if not asset_root.is_dir():
        raise FingerprintError(f"公共知识资产目录缺失: {KNOWLEDGE_ASSET_DIR}")
    for item in sorted(asset_root.rglob("*")):
        if not item.is_file() or item.is_symlink():
            continue
        if "__pycache__" in item.parts:
            continue
        relative = item.relative_to(skill_root).as_posix()
        entries.append(
            _FileEntry(relative, "knowledge_asset", item.stat().st_size, _hash_file(item))
        )
    return entries


def fingerprint_public_assets(*, skill_root: Optional[Path] = None) -> PublicAssetFingerprint:
    """生成公共资产指纹。纯读操作，不写盘、不联网。"""
    root = Path(skill_root) if skill_root is not None else paths.skill_root()
    if not root.is_dir():
        raise FingerprintError("skill root 不存在，无法生成公共指纹。")

    entries = _collect_files(root)
    # 排序键为 POSIX 相对路径，确保与遍历顺序无关
    entries.sort(key=lambda e: e.relative_path)

    payload = {
        "resolver_semantics_version": RESOLVER_SEMANTICS_VERSION,
        "files": [
            {
                "path": e.relative_path,
                "sha256": e.sha256,
                "size": e.size_bytes,
            }
            for e in entries
        ],
    }
    aggregate = models.content_hash(payload, exclude=()).removeprefix("sha256:")
    return PublicAssetFingerprint(
        public_asset_fingerprint=f"sha256:{aggregate}",
        public_snapshot_id=f"public_sha256_{aggregate}",
        resolver_semantics_version=RESOLVER_SEMANTICS_VERSION,
        files=tuple(entries),
        projection_hash=f"sha256:{aggregate}",
    )
