#!/usr/bin/env python3
"""法律元力 Skill 管理脚本（对齐 law-portal/backend 真实 API）。"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import shutil
import sys
import tempfile
import time
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


@dataclass
class Config:
    api_base_url: str
    timeout_seconds: int
    api_token: str
    state_file: Path
    package_dir: Path
    workbuddy_skills_dir: Path


def _read_config() -> Config:
    base_url = os.getenv("YUANLI_API_BASE_URL", "https://yuanli.ailaw.cn").strip().rstrip("/")
    timeout_raw = os.getenv("YUANLI_TIMEOUT_SECONDS", "30").strip()
    token = os.getenv("YUANLI_API_TOKEN", "").strip()
    state_path = os.getenv("YUANLI_AGENT_SKILL_STATE_PATH", "~/.yuanli/agent_skills.json").strip()
    package_dir = os.getenv("YUANLI_AGENT_SKILL_PACKAGE_DIR", "~/.yuanli/packages").strip()
    workbuddy_dir = os.getenv(
        "YUANLI_AGENT_SKILLS_DIR",
        os.getenv("YUANLI_WORKBUDDY_SKILLS_DIR", "~/.workbuddy/skills"),
    ).strip()

    if not base_url:
        raise ValueError("YUANLI_API_BASE_URL 不能为空")
    try:
        timeout_seconds = int(timeout_raw)
    except ValueError as exc:
        raise ValueError("YUANLI_TIMEOUT_SECONDS 必须为整数") from exc
    if timeout_seconds <= 0:
        raise ValueError("YUANLI_TIMEOUT_SECONDS 必须大于 0")

    return Config(
        api_base_url=base_url,
        timeout_seconds=timeout_seconds,
        api_token=token,
        state_file=Path(state_path).expanduser(),
        package_dir=Path(package_dir).expanduser(),
        workbuddy_skills_dir=Path(workbuddy_dir).expanduser(),
    )


def _headers(config: Config) -> dict[str, str]:
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if config.api_token:
        headers["Authorization"] = f"Bearer {config.api_token}"
    return headers


def _http_json(
    config: Config,
    method: str,
    path: str,
    payload: Optional[dict[str, Any]] = None,
    query: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    url = f"{config.api_base_url}{path}"
    if query:
        compact = {k: v for k, v in query.items() if v is not None and v != ""}
        if compact:
            url = f"{url}?{urlencode(compact)}"
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = Request(url=url, data=body, headers=_headers(config), method=method)
    try:
        with urlopen(req, timeout=config.timeout_seconds) as resp:
            raw = resp.read().decode("utf-8") or "{}"
            return json.loads(raw)
    except HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8")
        except Exception:
            detail = ""
        raise RuntimeError(f"HTTP {exc.code} {exc.reason}. Response: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"网络错误: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"响应不是合法 JSON: {exc}") from exc


def _http_bytes(config: Config, method: str, path: str) -> bytes:
    req = Request(
        url=f"{config.api_base_url}{path}",
        data=None,
        headers=_headers(config),
        method=method,
    )
    try:
        with urlopen(req, timeout=config.timeout_seconds) as resp:
            return resp.read()
    except HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8")
        except Exception:
            detail = ""
        raise RuntimeError(f"HTTP {exc.code} {exc.reason}. Response: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"网络错误: {exc.reason}") from exc


def _load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"skills": {}, "auto_update_configured": False}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if "skills" not in data:
            data["skills"] = {}
        if "auto_update_configured" not in data:
            data["auto_update_configured"] = False
        return data
    except Exception:
        return {"skills": {}, "auto_update_configured": False}


def _save_state(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _version_key(ver: str) -> tuple[int, ...]:
    nums = re.findall(r"\d+", str(ver or ""))
    if not nums:
        return (0,)
    return tuple(int(x) for x in nums)


def _extract_license(detail: dict[str, Any]) -> dict[str, Any]:
    """从 GET /api/skills/{id} 响应提取 license 信息，优先使用 license 字段。"""
    info = {
        "license_name": "",
        "license_spdx": "",
        "license_url": "",
        "copyright_notice": "",
        "display": "",
        "raw": detail.get("license"),
    }
    raw = detail.get("license")
    if isinstance(raw, str) and raw.strip():
        info["license_name"] = raw.strip()
    elif isinstance(raw, dict):
        info["license_name"] = str(
            raw.get("name") or raw.get("license_name") or ""
        ).strip()
        info["license_spdx"] = str(
            raw.get("spdx") or raw.get("license_spdx") or raw.get("spdx_id") or ""
        ).strip()
        info["license_url"] = str(
            raw.get("url") or raw.get("license_url") or ""
        ).strip()
        info["copyright_notice"] = str(raw.get("copyright_notice") or "").strip()

    if not info["license_name"] and not info["license_spdx"]:
        trust = detail.get("trust_info")
        lm = trust.get("legal_metadata") if isinstance(trust, dict) else {}
        if isinstance(lm, dict):
            info["license_name"] = str(lm.get("license_name") or "").strip()
            info["license_spdx"] = str(lm.get("license_spdx") or "").strip()
            info["license_url"] = str(lm.get("license_url") or "").strip()
            info["copyright_notice"] = str(lm.get("copyright_notice") or "").strip()

    if info["license_name"]:
        info["display"] = info["license_name"]
    elif info["license_spdx"]:
        info["display"] = info["license_spdx"]
    else:
        info["display"] = "未提供许可证信息"

    return info


def _license_fingerprint(license_info: dict[str, Any]) -> str:
    parts = [
        str(license_info.get("license_name") or ""),
        str(license_info.get("license_spdx") or ""),
        str(license_info.get("license_url") or ""),
        str(license_info.get("copyright_notice") or ""),
    ]
    return "|".join(parts)


def _format_license_text(skill_id: str, name: str, license_info: dict[str, Any]) -> str:
    lines = [
        "=" * 60,
        "  法律元力 Skill 许可证信息",
        "=" * 60,
        f"  Skill ID : {skill_id}",
        f"  名称     : {name}",
        f"  许可证   : {license_info.get('display') or '未提供'}",
    ]
    if license_info.get("license_spdx"):
        lines.append(f"  SPDX     : {license_info['license_spdx']}")
    if license_info.get("license_url"):
        lines.append(f"  链接     : {license_info['license_url']}")
    if license_info.get("copyright_notice"):
        lines.append(f"  版权说明 : {license_info['copyright_notice']}")
    lines.extend(
        [
            "-" * 60,
            "  下载或落地安装前，请向安装者明确上述 license 并获得确认。",
            "  确认后执行 install/update 时附加参数：--accept-license",
            "=" * 60,
        ]
    )
    return "\n".join(lines)


def _fetch_remote_skill_meta(config: Config, skill_id: str) -> dict[str, str]:
    try:
        detail = _http_json(config, "GET", f"/api/skills/{skill_id}")
        return {
            "name": str(detail.get("name") or ""),
            "version": str(detail.get("version") or ""),
        }
    except Exception:
        return {"name": "", "version": ""}


def _resolve_scan_register_meta(
    config: Config,
    skill_id: str,
    item: dict[str, Any],
) -> tuple[str, str]:
    """注册 scan 发现的 Skill 时解析版本与名称，避免本地 version 为空导致误报可更新。"""
    version = str(item.get("remote_version") or "").strip()
    name = str(item.get("remote_name") or item.get("name") or "").strip()

    skill_md_path = Path(str(item.get("skill_md_path") or ""))
    if not version and skill_md_path.is_file():
        frontmatter, _ = _parse_skill_frontmatter(skill_md_path)
        version = str(frontmatter.get("version") or "").strip()

    if not version or not name:
        remote = _fetch_remote_skill_meta(config, skill_id)
        if not version:
            version = str(remote.get("version") or "").strip()
        if not name:
            name = str(remote.get("name") or "").strip()

    return version, name or skill_id


def get_skill_license(config: Config, skill_id: str) -> dict[str, Any]:
    detail = _http_json(config, "GET", f"/api/skills/{skill_id}")
    license_info = _extract_license(detail)
    return {
        "skillId": skill_id,
        "name": detail.get("name") or skill_id,
        "version": detail.get("version") or "",
        "license": license_info,
        "display": _format_license_text(
            skill_id,
            str(detail.get("name") or skill_id),
            license_info,
        ),
    }


def _license_download_gate(
    *,
    skill_id: str,
    name: str,
    license_info: dict[str, Any],
    accept_license: bool,
    need_download: bool,
    prior_fingerprint: str = "",
) -> Optional[dict[str, Any]]:
    if not need_download:
        return None
    current_fp = _license_fingerprint(license_info)
    if accept_license:
        return None
    if prior_fingerprint and prior_fingerprint == current_fp:
        return None
    return {
        "blocked": True,
        "requiresLicenseAcceptance": True,
        "skillId": skill_id,
        "name": name,
        "license": license_info,
        "message": "下载前需向安装者明确 license 并获得确认；确认后请附加 --accept-license",
        "display": _format_license_text(skill_id, name, license_info),
    }


def _format_installed_at(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        except (OSError, ValueError):
            return str(value)
    text = str(value).strip()
    if not text:
        return "-"
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return text


def _find_skill_md(skill_dir: Path) -> Optional[Path]:
    direct = skill_dir / "SKILL.md"
    if direct.is_file():
        return direct
    matches = sorted(skill_dir.rglob("SKILL.md"))
    return matches[0] if matches else None


def _read_yuanli_skill_id(skill_md_path: Path) -> Optional[str]:
    try:
        content = skill_md_path.read_text(encoding="utf-8")
    except OSError:
        return None
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return None
    fm = match.group(1)
    id_match = re.search(r"^yuanli_skill_id:\s*(.+)$", fm, re.MULTILINE)
    if not id_match:
        return None
    return id_match.group(1).strip().strip('"').strip("'")


def _parse_skill_frontmatter(skill_md_path: Path) -> tuple[dict[str, str], str]:
    try:
        content = skill_md_path.read_text(encoding="utf-8")
    except OSError:
        return {}, ""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
    if not match:
        return {}, content
    frontmatter: dict[str, str] = {}
    for line in match.group(1).splitlines():
        item = re.match(r"^([A-Za-z0-9_-]+):\s*(.+)$", line.strip())
        if item:
            frontmatter[item.group(1)] = item.group(2).strip().strip('"').strip("'")
    return frontmatter, match.group(2)


def _extract_local_skill_name(frontmatter: dict[str, str], body: str, folder_name: str) -> str:
    for key in ("name", "title"):
        value = str(frontmatter.get(key) or "").strip()
        if value:
            return value
    title_match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
    if title_match:
        return title_match.group(1).strip()
    return folder_name


def _normalize_match_text(text: str) -> str:
    return re.sub(r"[\s_\-]+", "", str(text or "").strip().lower())


def _score_yuanli_match(local_name: str, folder_name: str, remote_item: dict[str, Any]) -> float:
    remote_id = str(remote_item.get("id") or "").strip().lower()
    remote_name = str(remote_item.get("name") or "").strip()
    remote_name_en = str(remote_item.get("name_en") or "").strip()

    local_norm = _normalize_match_text(local_name)
    folder_norm = _normalize_match_text(folder_name)
    remote_name_norm = _normalize_match_text(remote_name)
    remote_name_en_norm = _normalize_match_text(remote_name_en)
    remote_id_norm = _normalize_match_text(remote_id)

    if remote_id and remote_id == folder_name.strip().lower():
        return 1.0
    if folder_norm and folder_norm == remote_id_norm:
        return 1.0
    if local_norm and local_norm == remote_name_norm:
        return 0.95
    if local_norm and local_norm == remote_name_en_norm:
        return 0.9
    if folder_norm and folder_norm == remote_name_norm:
        return 0.92
    if local_norm and remote_name_norm and (local_norm in remote_name_norm or remote_name_norm in local_norm):
        return 0.75
    return 0.0


def _match_yuanli_skill_by_search(
    config: Config,
    local_name: str,
    folder_name: str,
) -> dict[str, Any]:
    queries: list[str] = []
    for candidate in (local_name, folder_name):
        text = str(candidate or "").strip()
        if text and text not in queries:
            queries.append(text)

    best: Optional[dict[str, Any]] = None
    best_score = 0.0
    candidates: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for query in queries:
        search_result = search_skills(config, query, "", limit=20)
        for item in search_result.get("items", []) or []:
            if not isinstance(item, dict):
                continue
            skill_id = str(item.get("id") or "").strip()
            if not skill_id or skill_id in seen_ids:
                continue
            seen_ids.add(skill_id)
            score = _score_yuanli_match(local_name, folder_name, item)
            candidate = {
                **item,
                "match_score": score,
                "match_query": query,
            }
            candidates.append(candidate)
            if score > best_score:
                best_score = score
                best = candidate

    candidates.sort(key=lambda x: float(x.get("match_score") or 0), reverse=True)
    confident_threshold = 0.9

    if best and best_score >= confident_threshold:
        close_matches = [
            c for c in candidates
            if float(c.get("match_score") or 0) >= best_score - 0.05
            and float(c.get("match_score") or 0) >= confident_threshold
        ]
        if len(close_matches) > 1:
            return {
                "matched": False,
                "ambiguous": True,
                "local_name": local_name,
                "folder_name": folder_name,
                "candidates": close_matches[:5],
                "message": "名称检索到多个高置信度候选，需人工确认",
            }
        return {
            "matched": True,
            "ambiguous": False,
            "skill_id": str(best.get("id") or ""),
            "match_score": best_score,
            "remote_name": best.get("name") or "",
            "remote_version": best.get("version") or "",
            "identification_method": "name_search",
            "match_query": best.get("match_query") or "",
            "candidates": candidates[:3],
        }

    probable = [c for c in candidates if float(c.get("match_score") or 0) >= 0.75]
    if len(probable) == 1:
        only = probable[0]
        return {
            "matched": True,
            "ambiguous": False,
            "skill_id": str(only.get("id") or ""),
            "match_score": float(only.get("match_score") or 0),
            "remote_name": only.get("name") or "",
            "remote_version": only.get("version") or "",
            "identification_method": "name_search",
            "match_query": only.get("match_query") or "",
            "candidates": candidates[:3],
            "message": "基于名称检索的单候选匹配（中等置信度）",
        }

    return {
        "matched": False,
        "ambiguous": len(probable) > 1,
        "local_name": local_name,
        "folder_name": folder_name,
        "candidates": candidates[:5],
        "message": "未能在元力平台确认该技能来源" if not probable else "名称检索到多个候选，需人工确认",
    }


def _build_scan_record(
    *,
    entry: Path,
    skill_md: Path,
    yuanli_id: str,
    display_name: str,
    identification_method: str,
    match_meta: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "path": str(entry),
        "skill_md_path": str(skill_md),
        "yuanli_skill_id": yuanli_id,
        "name": display_name,
        "identification_method": identification_method,
    }
    if match_meta:
        record["match_score"] = match_meta.get("match_score")
        record["match_query"] = match_meta.get("match_query")
        record["remote_name"] = match_meta.get("remote_name")
        record["remote_version"] = match_meta.get("remote_version")
    return record


def _inject_yuanli_skill_id(skill_md_path: Path, skill_id: str) -> None:
    content = skill_md_path.read_text(encoding="utf-8")
    if re.match(r"^---\s*\n", content):
        if re.search(r"^yuanli_skill_id:\s*.+$", content, re.MULTILINE):
            content = re.sub(
                r"^yuanli_skill_id:\s*.+$",
                f"yuanli_skill_id: {skill_id}",
                content,
                count=1,
                flags=re.MULTILINE,
            )
        else:
            content = re.sub(
                r"^(---\s*\n)",
                rf"\1yuanli_skill_id: {skill_id}\n",
                content,
                count=1,
            )
    else:
        content = f"---\nyuanli_skill_id: {skill_id}\n---\n\n{content}"
    skill_md_path.write_text(content, encoding="utf-8")


def _extract_skill_zip(zip_bytes: bytes, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            zf.extractall(tmp_path)
        entries = [p for p in tmp_path.iterdir() if not p.name.startswith(".")]
        source = entries[0] if len(entries) == 1 and entries[0].is_dir() else tmp_path
        for item in source.iterdir():
            if item.name.startswith("."):
                continue
            target = dest / item.name
            if item.is_dir():
                if target.exists():
                    shutil.rmtree(target)
                shutil.copytree(item, target)
            else:
                shutil.copy2(item, target)


def _workbuddy_registered(record: dict[str, Any]) -> bool:
    path_raw = str(record.get("workbuddy_path") or "").strip()
    if not path_raw:
        return False
    return Path(path_raw).expanduser().exists()


def _register_to_workbuddy(
    config: Config,
    skill_id: str,
    package_bytes: bytes,
) -> str:
    dest = config.workbuddy_skills_dir / skill_id
    if dest.exists():
        shutil.rmtree(dest)
    _extract_skill_zip(package_bytes, dest)
    skill_md = _find_skill_md(dest)
    if skill_md:
        _inject_yuanli_skill_id(skill_md, skill_id)
    return str(dest)


def search_skills(config: Config, query: str, category: str, limit: int) -> dict[str, Any]:
    page_size = min(max(limit, 1), 100)
    payload = _http_json(
        config=config,
        method="GET",
        path="/api/skills",
        query={
            "search": query,
            "category": category,
            "page": 1,
            "page_size": page_size,
            "sort": "default",
        },
    )
    items = payload.get("items") if isinstance(payload, dict) else []
    normalized = []
    for item in items or []:
        normalized.append(
            {
                "id": item.get("id"),
                "name": item.get("name"),
                "description": item.get("description"),
                "category": item.get("category"),
                "version": item.get("version"),
                "owner": item.get("owner"),
            }
        )
    return {
        "total": payload.get("total", len(normalized)),
        "items": normalized,
    }


def list_skills(config: Config, detail: bool) -> dict[str, Any]:
    state = _load_state(config.state_file)
    skills = state.get("skills") or {}
    if not skills:
        return {
            "total": 0,
            "items": [],
            "message": "尚未安装任何法律元力 Skill",
            "hint": "可先执行 search 查找技能，或 scan 盘点本地技能目录中已有技能",
            "display": "尚未安装任何法律元力 Skill",
        }

    items: list[dict[str, Any]] = []
    for idx, (skill_id, record) in enumerate(sorted(skills.items()), start=1):
        if not isinstance(record, dict):
            continue
        registered = _workbuddy_registered(record)
        item: dict[str, Any] = {
            "index": idx,
            "id": skill_id,
            "name": record.get("name") or skill_id,
            "version": record.get("version") or "",
            "installed_at": record.get("installed_at"),
            "from": record.get("from") or "yuanli",
            "workbuddy_registered": registered,
            "registration_method": record.get("registration_method") or "",
        }
        if detail:
            try:
                remote = _http_json(config, "GET", f"/api/skills/{skill_id}")
                item["category"] = remote.get("category") or record.get("category", "")
                item["owner"] = remote.get("owner") or ""
                item["download_count"] = remote.get("download_count") or 0
            except Exception as exc:
                item["category"] = record.get("category", "")
                item["detail_error"] = str(exc)
        items.append(item)

    lines = [
        "=" * 60,
        f"  本地已管理的法律元力 Skill（共 {len(items)} 个）",
        "=" * 60,
    ]
    for item in items:
        wb = "✓ 已落地" if item["workbuddy_registered"] else "✗ 未落地（可执行 scan --register-all）"
        lines.extend(
            [
                f"  [{item['index']}] {item['name']}",
                f"      ID       : {item['id']}",
                f"      版本     : {item['version']}",
                f"      安装时间 : {_format_installed_at(item['installed_at'])}",
                f"      本地目录 : {wb}",
            ]
        )
        if detail and item.get("category"):
            lines.append(f"      分类     : {item.get('category')}")
        if detail and item.get("owner"):
            lines.append(f"      作者     : {item.get('owner')}")
    lines.append("=" * 60)

    return {
        "total": len(items),
        "items": items,
        "auto_update_configured": bool(state.get("auto_update_configured")),
        "display": "\n".join(lines),
    }


def scan_skills(config: Config, register: bool, register_all: bool) -> dict[str, Any]:
    workbuddy_dir = config.workbuddy_skills_dir
    state = _load_state(config.state_file)
    skills_state = state.setdefault("skills", {})

    managed: list[dict[str, Any]] = []
    unregistered: list[dict[str, Any]] = []
    unknown: list[dict[str, Any]] = []
    ambiguous: list[dict[str, Any]] = []

    if workbuddy_dir.is_dir():
        for entry in sorted(workbuddy_dir.iterdir()):
            if not entry.is_dir() or entry.name.startswith("."):
                continue
            skill_md = _find_skill_md(entry)
            if not skill_md:
                unknown.append({"path": str(entry), "reason": "未找到 SKILL.md"})
                continue

            frontmatter, body = _parse_skill_frontmatter(skill_md)
            local_name = _extract_local_skill_name(frontmatter, body, entry.name)
            yuanli_id = _read_yuanli_skill_id(skill_md)
            identification_method = "yuanli_skill_id"
            match_meta: Optional[dict[str, Any]] = None

            if not yuanli_id:
                match_result = _match_yuanli_skill_by_search(config, local_name, entry.name)
                if match_result.get("matched"):
                    yuanli_id = str(match_result.get("skill_id") or "")
                    identification_method = str(match_result.get("identification_method") or "name_search")
                    match_meta = match_result
                elif match_result.get("ambiguous"):
                    ambiguous.append(
                        {
                            "path": str(entry),
                            "local_name": local_name,
                            "reason": match_result.get("message") or "名称检索存在多个候选",
                            "candidates": match_result.get("candidates") or [],
                        }
                    )
                    continue
                else:
                    unknown.append(
                        {
                            "path": str(entry),
                            "local_name": local_name,
                            "reason": match_result.get("message") or "无 yuanli_skill_id 且名称检索未匹配",
                            "candidates": match_result.get("candidates") or [],
                        }
                    )
                    continue

            if not yuanli_id:
                unknown.append(
                    {
                        "path": str(entry),
                        "local_name": local_name,
                        "reason": "无法识别元力 Skill ID",
                    }
                )
                continue

            record = _build_scan_record(
                entry=entry,
                skill_md=skill_md,
                yuanli_id=yuanli_id,
                display_name=local_name or entry.name,
                identification_method=identification_method,
                match_meta=match_meta,
            )
            if yuanli_id in skills_state:
                managed.append(record)
            else:
                unregistered.append(record)

    registered_now: list[str] = []
    if register or register_all:
        for item in unregistered:
            skill_id = item["yuanli_skill_id"]
            remote_version, remote_name = _resolve_scan_register_meta(config, skill_id, item)
            skills_state[skill_id] = {
                "skill_id": skill_id,
                "name": remote_name,
                "version": remote_version,
                "from": "yuanli",
                "installed_at": datetime.now(timezone.utc).isoformat(),
                "workbuddy_path": item["path"],
                "registration_method": "scan",
                "identification_method": item.get("identification_method") or "yuanli_skill_id",
            }
            if item.get("identification_method") == "name_search":
                skill_md_path = Path(str(item.get("skill_md_path") or ""))
                if skill_md_path.is_file():
                    _inject_yuanli_skill_id(skill_md_path, skill_id)
            registered_now.append(skill_id)
        if registered_now:
            _save_state(config.state_file, state)

    return {
        "workbuddy_dir": str(workbuddy_dir),
        "managed": managed,
        "unregistered": unregistered,
        "ambiguous": ambiguous,
        "unknown": unknown,
        "registered_now": registered_now,
        "summary": {
            "managed_count": len(managed),
            "unregistered_count": len(unregistered),
            "ambiguous_count": len(ambiguous),
            "unknown_count": len(unknown),
            "registered_now_count": len(registered_now),
            "name_search_identified_count": sum(
                1 for group in (managed, unregistered)
                for item in group
                if item.get("identification_method") == "name_search"
            ),
        },
    }


def install_skill(
    config: Config,
    skill_id: str,
    download_package: bool,
    register_to_workbuddy: bool,
    accept_license: bool,
) -> dict[str, Any]:
    detail = _http_json(config, "GET", f"/api/skills/{skill_id}")
    version = str(detail.get("version") or "")
    name = str(detail.get("name") or skill_id)
    license_info = _extract_license(detail)
    state = _load_state(config.state_file)
    skills = state.setdefault("skills", {})
    old_record = skills.get(skill_id) if isinstance(skills.get(skill_id), dict) else {}

    need_package = download_package or register_to_workbuddy
    gate = _license_download_gate(
        skill_id=skill_id,
        name=name,
        license_info=license_info,
        accept_license=accept_license,
        need_download=need_package,
        prior_fingerprint=str(old_record.get("license_fingerprint") or ""),
    )
    if gate:
        return gate

    package_path: Optional[Path] = None
    workbuddy_path = ""
    package_bytes: Optional[bytes] = None

    if need_package:
        package_bytes = _http_bytes(config, "GET", f"/api/skills/{skill_id}/download")
        if download_package:
            config.package_dir.mkdir(parents=True, exist_ok=True)
            package_path = config.package_dir / f"{skill_id}-{version or 'latest'}.zip"
            package_path.write_bytes(package_bytes)

    if register_to_workbuddy:
        if not package_bytes:
            package_bytes = _http_bytes(config, "GET", f"/api/skills/{skill_id}/download")
        workbuddy_path = _register_to_workbuddy(config, skill_id, package_bytes)

    if not workbuddy_path:
        workbuddy_path = str(old_record.get("workbuddy_path") or "")

    license_fp = _license_fingerprint(license_info)
    skills[skill_id] = {
        "skill_id": skill_id,
        "name": name,
        "version": version,
        "category": detail.get("category", ""),
        "updated": detail.get("updated", ""),
        "from": "yuanli",
        "installed_at": datetime.now(timezone.utc).isoformat(),
        "content": detail.get("content", ""),
        "workbuddy_path": workbuddy_path,
        "registration_method": "cli" if register_to_workbuddy else str(old_record.get("registration_method") or ""),
        "license": license_info,
        "license_fingerprint": license_fp,
        "license_accepted_at": datetime.now(timezone.utc).isoformat() if need_package and accept_license else old_record.get("license_accepted_at"),
    }

    _save_state(config.state_file, state)
    return {
        "skillId": skill_id,
        "name": name,
        "version": version,
        "installed": True,
        "license": license_info,
        "workbuddyPath": workbuddy_path,
        "workbuddyRegistered": bool(workbuddy_path),
        "stateFile": str(config.state_file),
        "packagePath": str(package_path) if package_path else "",
        "content": detail.get("content", ""),
    }


def remove_skill(config: Config, skill_id: str) -> dict[str, Any]:
    state = _load_state(config.state_file)
    skills = state.setdefault("skills", {})
    if skill_id not in skills:
        return {
            "skillId": skill_id,
            "removed": False,
            "message": "本地安装记录不存在",
            "stateFile": str(config.state_file),
        }
    removed = skills.pop(skill_id)
    _save_state(config.state_file, state)
    return {
        "skillId": skill_id,
        "removed": True,
        "previousVersion": removed.get("version", ""),
        "stateFile": str(config.state_file),
    }


def update_skill(
    config: Config,
    skill_id: str,
    download_package: bool,
    force: bool,
    accept_license: bool,
) -> dict[str, Any]:
    state = _load_state(config.state_file)
    skills = state.setdefault("skills", {})
    if skill_id not in skills:
        raise ValueError("该 skill 尚未安装，请先执行 install")
    local = skills[skill_id]
    local_version = str(local.get("version") or "")
    remote = _http_json(config, "GET", f"/api/skills/{skill_id}")
    remote_version = str(remote.get("version") or "")
    name = str(remote.get("name") or skill_id)
    license_info = _extract_license(remote)
    should_update = force or (_version_key(remote_version) > _version_key(local_version))
    if not should_update:
        return {
            "skillId": skill_id,
            "updated": False,
            "localVersion": local_version,
            "remoteVersion": remote_version,
            "license": license_info,
            "message": "当前已是最新版本",
        }

    gate = _license_download_gate(
        skill_id=skill_id,
        name=name,
        license_info=license_info,
        accept_license=accept_license,
        need_download=download_package,
        prior_fingerprint=str(local.get("license_fingerprint") or ""),
    )
    if gate:
        return gate

    local.update(
        {
            "name": name,
            "version": remote_version,
            "category": remote.get("category", ""),
            "updated": remote.get("updated", ""),
            "content": remote.get("content", ""),
            "installed_at": datetime.now(timezone.utc).isoformat(),
            "license": license_info,
            "license_fingerprint": _license_fingerprint(license_info),
        }
    )
    if accept_license and download_package:
        local["license_accepted_at"] = datetime.now(timezone.utc).isoformat()

    package_path = None
    if download_package:
        config.package_dir.mkdir(parents=True, exist_ok=True)
        package_bytes = _http_bytes(config, "GET", f"/api/skills/{skill_id}/download")
        package_path = config.package_dir / f"{skill_id}-{remote_version or 'latest'}.zip"
        package_path.write_bytes(package_bytes)
        if local.get("workbuddy_path"):
            _register_to_workbuddy(config, skill_id, package_bytes)
    _save_state(config.state_file, state)
    return {
        "skillId": skill_id,
        "updated": True,
        "fromVersion": local_version,
        "toVersion": remote_version,
        "license": license_info,
        "packagePath": str(package_path) if package_path else "",
        "stateFile": str(config.state_file),
    }


def _check_single_update(config: Config, skill_id: str, record: dict[str, Any]) -> dict[str, Any]:
    local_version = str(record.get("version") or "")
    try:
        remote = _http_json(config, "GET", f"/api/skills/{skill_id}")
        remote_version = str(remote.get("version") or "")
    except Exception as exc:
        return {
            "id": skill_id,
            "name": record.get("name") or skill_id,
            "local_version": local_version,
            "remote_version": "",
            "status": "check_failed",
            "error": str(exc),
        }
    if _version_key(remote_version) > _version_key(local_version):
        status = "update_available"
    else:
        status = "up_to_date"
    return {
        "id": skill_id,
        "name": remote.get("name") or record.get("name") or skill_id,
        "local_version": local_version,
        "remote_version": remote_version,
        "status": status,
    }


def check_updates(
    config: Config,
    auto_update: bool,
    output_format: str,
    download_package: bool,
    accept_license: bool,
) -> dict[str, Any]:
    state = _load_state(config.state_file)
    skills = state.get("skills") or {}
    results: list[dict[str, Any]] = []
    auto_updated: list[dict[str, Any]] = []

    for skill_id, record in skills.items():
        if not isinstance(record, dict):
            continue
        item = _check_single_update(config, skill_id, record)
        results.append(item)
        if auto_update and item.get("status") == "update_available":
            try:
                updated = update_skill(
                    config,
                    skill_id,
                    download_package,
                    force=False,
                    accept_license=accept_license,
                )
                auto_updated.append(updated)
            except Exception as exc:
                auto_updated.append({"skillId": skill_id, "updated": False, "error": str(exc)})

    updatable = [r for r in results if r.get("status") == "update_available"]
    report = {
        "checked_at": int(time.time()),
        "total": len(results),
        "updatable": len(updatable),
        "results": results,
        "auto_updated": auto_updated,
    }

    if output_format == "text":
        lines = [
            "=" * 60,
            f"  元力 Skill 更新检查（共 {len(results)} 个，{len(updatable)} 个可更新）",
            "=" * 60,
        ]
        for item in results:
            status_label = {
                "update_available": "可更新",
                "up_to_date": "已最新",
                "check_failed": "检查失败",
            }.get(str(item.get("status")), str(item.get("status")))
            lines.extend(
                [
                    f"  - {item.get('name')} ({item.get('id')})",
                    f"    本地: {item.get('local_version')}  远端: {item.get('remote_version')}  [{status_label}]",
                ]
            )
        lines.append("=" * 60)
        report["display"] = "\n".join(lines)

    return report


def status_overview(config: Config) -> dict[str, Any]:
    state = _load_state(config.state_file)
    skills = state.get("skills") or {}
    remote_total = 0
    try:
        payload = _http_json(
            config,
            "GET",
            "/api/skills",
            query={"page": 1, "page_size": 1},
        )
        remote_total = int(payload.get("total") or 0)
    except Exception:
        remote_total = -1

    managed_count = len(skills)
    workbuddy_registered = sum(
        1 for record in skills.values() if isinstance(record, dict) and _workbuddy_registered(record)
    )
    check = check_updates(
        config,
        auto_update=False,
        output_format="json",
        download_package=False,
        accept_license=False,
    )
    updatable = [r for r in check.get("results", []) if r.get("status") == "update_available"]

    return {
        "remote_total_skills": remote_total,
        "local_managed_count": managed_count,
        "workbuddy_registered_count": workbuddy_registered,
        "updatable_count": len(updatable),
        "updatable_skills": updatable,
        "auto_update_configured": bool(state.get("auto_update_configured")),
        "state_file": str(config.state_file),
        "workbuddy_skills_dir": str(config.workbuddy_skills_dir),
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="管理法律元力技能（通用智能体）")
    subparsers = parser.add_subparsers(dest="command", required=True)

    search_parser = subparsers.add_parser("search", help="搜索技能")
    search_parser.add_argument("--query", default="", help="搜索关键词")
    search_parser.add_argument("--category", default="", help="分类过滤（可选）")
    search_parser.add_argument("--limit", type=int, default=20, help="返回数量，默认 20")

    list_parser = subparsers.add_parser("list", help="查看本地已管理 Skill")
    list_parser.add_argument("--detail", action="store_true", help="补充 API 详情")
    list_parser.add_argument("--format", choices=["json", "text"], default="json", help="输出格式")

    scan_parser = subparsers.add_parser("scan", help="盘点本地技能目录中的元力 Skill")
    scan_parser.add_argument("--register", action="store_true", help="注册未纳入管理的元力 Skill")
    scan_parser.add_argument("--register-all", action="store_true", help="批量注册所有未管理 Skill")

    status_parser = subparsers.add_parser("status", help="全局健康检查")

    check_parser = subparsers.add_parser("check-updates", help="批量检查更新")
    check_parser.add_argument("--auto-update", action="store_true", help="自动更新可更新 Skill")
    check_parser.add_argument("--download-package", action="store_true", help="自动更新时下载 zip")
    check_parser.add_argument("--format", choices=["json", "text"], default="json", help="输出格式")

    check_parser.add_argument("--accept-license", action="store_true", help="自动下载更新前确认接受许可证")

    license_parser = subparsers.add_parser("license", help="查看 Skill 许可证信息")
    license_parser.add_argument("--skill-id", required=True, help="技能 ID")
    license_parser.add_argument("--format", choices=["json", "text"], default="json", help="输出格式")

    install_parser = subparsers.add_parser("install", help="安装技能")
    install_parser.add_argument("--skill-id", required=True, help="技能 ID")
    install_parser.add_argument(
        "--download-package",
        action="store_true",
        help="下载 zip 安装包（默认仅同步提示词内容）",
    )
    install_parser.add_argument(
        "--register-to-workbuddy",
        action="store_true",
        help="解压并落地到本地技能目录（兼容参数名）",
    )
    install_parser.add_argument(
        "--accept-license",
        action="store_true",
        help="安装者已确认许可证；下载/落地前必填",
    )

    remove_parser = subparsers.add_parser("remove", help="删除已安装技能")
    remove_parser.add_argument("--skill-id", required=True, help="技能 ID")

    update_parser = subparsers.add_parser("update", help="更新技能")
    update_parser.add_argument("--skill-id", required=True, help="技能 ID")
    update_parser.add_argument("--download-package", action="store_true", help="更新时同步下载 zip")
    update_parser.add_argument("--force", action="store_true", help="强制更新")
    update_parser.add_argument(
        "--accept-license",
        action="store_true",
        help="安装者已确认许可证；下载更新包前必填（许可证变更时需重新确认）",
    )

    return parser


def _emit_result(command: str, result: dict[str, Any], *, text_key: str = "display") -> int:
    if result.get("requiresLicenseAcceptance"):
        print(json.dumps({"ok": False, "command": command, "result": result}, ensure_ascii=False))
        return 1
    print(json.dumps({"ok": True, "command": command, "result": result}, ensure_ascii=False))
    return 0


def main() -> int:
    # Windows 默认使用 GBK/CP936 编码，无法输出 ✓/✗ 等 Unicode 字符
    # 统一 reconfigure stdout/stderr 为 UTF-8
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

    parser = _build_parser()
    args = parser.parse_args()
    try:
        config = _read_config()
        result: dict[str, Any]
        if args.command == "search":
            if args.limit <= 0:
                raise ValueError("--limit 必须大于 0")
            result = search_skills(config, args.query, args.category, args.limit)
        elif args.command == "list":
            result = list_skills(config, args.detail)
            if args.format == "text" and result.get("display"):
                print(result["display"])
                return 0
        elif args.command == "scan":
            result = scan_skills(config, args.register, args.register_all)
        elif args.command == "status":
            result = status_overview(config)
        elif args.command == "check-updates":
            result = check_updates(
                config,
                args.auto_update,
                args.format,
                args.download_package,
                args.accept_license,
            )
            if args.format == "text" and result.get("display"):
                print(result["display"])
                return 0
            if args.auto_update and args.download_package:
                blocked = [
                    x for x in result.get("auto_updated", [])
                    if isinstance(x, dict) and x.get("requiresLicenseAcceptance")
                ]
                if blocked:
                    print(json.dumps({"ok": False, "command": "check-updates", "result": result}, ensure_ascii=False))
                    return 1
        elif args.command == "license":
            result = get_skill_license(config, args.skill_id)
            if args.format == "text" and result.get("display"):
                print(result["display"])
                return 0
        elif args.command == "install":
            result = install_skill(
                config,
                args.skill_id,
                args.download_package,
                args.register_to_workbuddy,
                args.accept_license,
            )
            return _emit_result("install", result)
        elif args.command == "remove":
            result = remove_skill(config, args.skill_id)
        elif args.command == "update":
            result = update_skill(
                config,
                args.skill_id,
                args.download_package,
                args.force,
                args.accept_license,
            )
            return _emit_result("update", result)
        else:
            raise ValueError(f"不支持的命令: {args.command}")
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps({"ok": True, "command": args.command, "result": result}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
