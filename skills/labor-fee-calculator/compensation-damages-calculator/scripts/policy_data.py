#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = BASE_DIR / "config.json"
POLICY_CACHE_DIR = BASE_DIR / ".policy_cache"
CACHE_DATE_IF_MISSING = "latest"
CACHE_YEAR_IF_MISSING = "latest"
RESOURCE_TYPE = "compensation-damages-calculator"
DEFAULT_POLICY_API_URL = "https://platform.delilegal.com/api/v1/skill/calculator/resource"
PLACEHOLDER_VALS = {"YOUR_API_KEY", "YOUR_APP_KEY", "Bearer YOUR_API_KEY", "Bearer YOUR_APP_KEY", "", None}
REGION_KEYS = ("region", "province", "city")
INLINE_POLICY_FIELDS = ("min_wage", "social_avg_wage", "law_basis", "law_articles_text", "notes")
POLICY_ACTIONS = {"api_snapshot", "fetch_api_snapshot", "policy_data"}
REGION_NORMALIZATION_TERMS = ("特别行政区", "自治区", "壮族", "回族", "维吾尔", "省", "市")
WHITESPACE_RE = re.compile(r"\s+")
CACHE_SAFE_RE = re.compile(r"[^0-9A-Za-z\u4e00-\u9fff._-]+")
REQUIRED_POLICY_FIELDS = ("min_wage", "social_avg_wage", "law_basis", "law_articles_text", "notes")
REQUIRED_POLICY_FIELD_SET = set(REQUIRED_POLICY_FIELDS)
WAGE_CALIBER_ALIASES = {
    "": "urban_non_private",
    "default": "urban_non_private",
    "urban_non_private": "urban_non_private",
    "城镇非私营单位": "urban_non_private",
    "城镇非私营单位就业人员平均工资": "urban_non_private",
    "all_urban": "all_urban",
    "全口径": "all_urban",
    "全口径城镇单位": "all_urban",
    "全口径城镇单位就业人员平均工资": "all_urban",
    "urban_private": "urban_private",
    "城镇私营单位": "urban_private",
    "城镇私营单位就业人员平均工资": "urban_private",
}


class PolicyDataError(Exception):
    """Raised when policy data cannot be fetched from the policy API."""


class SkillRequestContext:
    def __init__(self, root_dir=None, filename=".session", skill_file=None):
        self.session_id = self._load_session(Path(root_dir or os.getcwd()) / filename)
        self.skill_id, self.skill_version = self._load_skill_meta(
            Path(skill_file or Path(__file__).resolve().parents[1] / "SKILL.md")
        )
        self.headers = {
            "Session-Id": self.session_id,
            "Skill-Id": self.skill_id,
            "Skill-Version": self.skill_version,
        }

    @staticmethod
    def _load_session(path: Path) -> str:
        session_id = path.read_text(encoding="utf-8").strip() if path.exists() else ""
        if session_id:
            return session_id
        session_id = str(uuid.uuid4())
        path.write_text(session_id, encoding="utf-8")
        return session_id

    @staticmethod
    def _load_skill_meta(path: Path) -> tuple[str, str]:
        frontmatter = path.read_text(encoding="utf-8").split("---", 2)[1]
        name = re.search(r"^name:\s*[\"']?([^\"'\n]+)", frontmatter, re.MULTILINE)
        version = re.search(r"^\s*version:\s*[\"']?([^\"'\n]+)", frontmatter, re.MULTILINE)
        return name.group(1).strip(), version.group(1).strip()


REQUEST_CONTEXT = SkillRequestContext()


def policy_api_url() -> str:
    return os.getenv("COMPENSATION_DAMAGES_POLICY_API_URL", DEFAULT_POLICY_API_URL).strip()


def first_payload_value(payload: dict[str, Any], keys: tuple[str, ...]) -> Any:
    return next((payload[key] for key in keys if payload.get(key)), "")


def load_api_key() -> str:
    if not CONFIG_FILE.exists():
        raise PolicyDataError(
            f"配置文件不存在：{CONFIG_FILE}\n"
            f"请在技能根目录创建 config.json，格式如下：\n"
            f'{{"apikey": "YOUR_API_KEY"}}'
        )
    try:
        config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PolicyDataError(f"config.json 不是有效 JSON：{exc}") from exc
    if not isinstance(config, dict):
        raise PolicyDataError("config.json 顶层必须是对象")

    apikey = str(config.get("apikey", "")).strip()
    if apikey in PLACEHOLDER_VALS:
        raise PolicyDataError(
            "config.json 中的 apikey 尚未配置或为占位符，请：\n"
            "1. 前往 https://open.delilegal.com/personal/keys 注册/登录\n"
            "2. 在控制台生成 API Key\n"
            "3. 将 API Key 填入 config.json 的 \"apikey\" 字段"
        )
    return apikey


def authorization_header(apikey: str) -> str:
    return f"Bearer {apikey}"


def normalize_wage_caliber(raw: Any) -> str:
    key = str(raw or "").strip()
    if key not in WAGE_CALIBER_ALIASES:
        raise PolicyDataError("wage_caliber 仅支持 urban_non_private、all_urban、urban_private")
    return WAGE_CALIBER_ALIASES[key]


def request_payload_from_input(payload: dict[str, Any]) -> dict[str, Any]:
    region = str(first_payload_value(payload, REGION_KEYS)).strip()
    if not region:
        raise PolicyDataError("缺少 region，无法请求补偿金及赔偿金政策数据 API")

    request_payload: dict[str, Any] = {
        "region": region,
        "wage_caliber": normalize_wage_caliber(payload.get("wage_caliber") or payload.get("caliber") or "urban_non_private"),
    }
    query_date = payload.get("date")
    if query_date:
        request_payload["date"] = query_date
    social_avg_year = payload.get("social_avg_year") or payload.get("year")
    if social_avg_year:
        request_payload["social_avg_year"] = social_avg_year
    return request_payload


def normalized_region_for_cache(region: Any) -> str:
    text = WHITESPACE_RE.sub("", str(region or ""))
    if not text:
        return "unknown"
    if "深圳" in text:
        return "深圳"
    normalized = text
    for item in REGION_NORMALIZATION_TERMS:
        normalized = normalized.replace(item, "")
    return normalized or text


def safe_cache_part(value: Any) -> str:
    text = WHITESPACE_RE.sub("", str(value or ""))
    text = CACHE_SAFE_RE.sub("_", text)
    return text.strip("._-") or "unknown"


def cache_path_for_request(request_payload: dict[str, Any]) -> Path:
    region = safe_cache_part(normalized_region_for_cache(request_payload.get("region")))
    query_date = safe_cache_part(request_payload.get("date") or CACHE_DATE_IF_MISSING)
    social_avg_year = safe_cache_part(request_payload.get("social_avg_year") or CACHE_YEAR_IF_MISSING)
    wage_caliber = safe_cache_part(normalize_wage_caliber(request_payload.get("wage_caliber") or "urban_non_private"))
    return POLICY_CACHE_DIR / f"{region}__{query_date}__{social_avg_year}__{wage_caliber}.json"


def order_policy_body(data: dict[str, Any], *, require_all: bool, include_extra: bool) -> dict[str, Any]:
    if require_all:
        missing = REQUIRED_POLICY_FIELD_SET - set(data)
        if missing:
            raise PolicyDataError(f"政策数据 API 响应缺少字段：{', '.join(sorted(missing))}")

    ordered = {key: data[key] for key in REQUIRED_POLICY_FIELDS if key in data}
    if include_extra:
        ordered.update((key, value) for key, value in data.items() if key not in ordered)
    return ordered


def validate_policy_body(data: dict[str, Any]) -> dict[str, Any]:
    return order_policy_body(data, require_all=True, include_extra=False)


def validate_policy_data(data: dict[str, Any]) -> dict[str, Any]:
    if "success" not in data or "body" not in data:
        raise PolicyDataError("政策数据 API 响应缺少统一外层字段：success/msg/body")
    body = data.get("body")
    if not isinstance(body, dict):
        raise PolicyDataError("政策数据 API 响应 body 必须是对象")
    if data.get("success") is False or body.get("found") is False:
        raise PolicyDataError(str(body.get("message") or body.get("error") or "政策数据 API 未返回可用数据"))
    return validate_policy_body(body)


def read_policy_cache(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise PolicyDataError(f"政策数据缓存读取失败：{path}") from exc
    except json.JSONDecodeError as exc:
        raise PolicyDataError(f"政策数据缓存不是有效 JSON：{path}") from exc
    if not isinstance(data, dict):
        raise PolicyDataError(f"政策数据缓存顶层必须是对象：{path}")
    ordered = validate_policy_body(data)
    if list(data.keys()) != list(ordered.keys()):
        try:
            write_policy_cache(path, ordered)
        except OSError:
            pass
    return ordered


def write_policy_cache(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(f"{path.suffix}.tmp")
    tmp_path.write_text(json.dumps(validate_policy_body(data), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp_path.replace(path)


def build_api_request(payload: dict[str, Any], apikey: str) -> urllib.request.Request:
    request_payload = request_payload_from_input(payload)
    request_body = {"resource_type": RESOURCE_TYPE, "payload": request_payload}
    return urllib.request.Request(
        policy_api_url(),
        data=json.dumps(request_body, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": authorization_header(apikey),
            **REQUEST_CONTEXT.headers,
        },
        method="POST",
    )


def read_api_response(request: urllib.request.Request) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        try:
            error_data = json.loads(body_text)
            if isinstance(error_data, dict):
                validate_policy_data(error_data)
        except PolicyDataError as policy_exc:
            raise policy_exc from exc
        except json.JSONDecodeError:
            pass
        raise PolicyDataError(f"政策数据 API 返回错误：HTTP {exc.code} {body_text}") from exc
    except urllib.error.URLError as exc:
        raise PolicyDataError(f"政策数据 API 请求失败：{exc}") from exc
    except json.JSONDecodeError as exc:
        raise PolicyDataError("政策数据 API 返回的不是有效 JSON") from exc

    if not isinstance(data, dict):
        raise PolicyDataError("政策数据 API 返回的顶层 JSON 必须是对象")
    return data


def fetch_policy_data_from_api(payload: dict[str, Any]) -> dict[str, Any]:
    request = build_api_request(payload, load_api_key())
    data = read_api_response(request)
    return validate_policy_data(data)


def get_policy_data(payload: dict[str, Any]) -> dict[str, Any]:
    raw = payload.get("policy_data") or payload.get("policy")
    if isinstance(raw, dict):
        return order_policy_body(raw, require_all=False, include_extra=True)
    if any(key in payload for key in INLINE_POLICY_FIELDS):
        return order_policy_body(payload, require_all=False, include_extra=True)
    if first_payload_value(payload, REGION_KEYS):
        request_payload = request_payload_from_input(payload)
        cache_path = cache_path_for_request(request_payload)
        if cache_path.exists():
            return read_policy_cache(cache_path)
        fetched = fetch_policy_data_from_api(payload)
        write_policy_cache(cache_path, fetched)
        return fetched
    return {}


def envelope(success: bool, body: dict[str, Any]) -> dict[str, Any]:
    return {"success": success, "msg": "", "body": body}


def fail(action: str, message: str) -> dict[str, Any]:
    return envelope(
        False,
        {
            "action": action,
            "found": False,
            "needs_web_search": True,
            "message": message,
            "source": policy_api_url(),
            "fallback": "最多两轮联网检索仍失败时，提示用户咨询当地人社局12333。",
        },
    )


def dispatch(payload: dict[str, Any]) -> dict[str, Any]:
    action = str(payload.get("action") or "api_snapshot").strip()
    if action not in POLICY_ACTIONS:
        return fail(action, f"不支持的 action：{action}")
    raw = payload.get("policy_data") or payload.get("policy")
    has_direct_policy_data = isinstance(raw, dict) or any(key in payload for key in INLINE_POLICY_FIELDS)
    if not has_direct_policy_data and not first_payload_value(payload, REGION_KEYS):
        return fail(action, "缺少 region，无法请求补偿金及赔偿金政策数据 API")

    try:
        data = get_policy_data(payload)
    except PolicyDataError as exc:
        return fail(action, str(exc))
    return envelope(True, {"action": action, "found": True, "needs_web_search": False, **data})


def load_payload(argv: list[str]) -> dict[str, Any]:
    if len(argv) >= 2:
        raw = argv[1]
        if raw.startswith("@"):
            raw = Path(raw[1:]).read_text(encoding="utf-8")
    else:
        raw = sys.stdin.read()
    if not raw.strip():
        raise PolicyDataError("请通过命令行参数或 stdin 传入 JSON")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PolicyDataError(f"JSON 解析失败：{exc}") from exc
    if not isinstance(payload, dict):
        raise PolicyDataError("顶层 JSON 必须是对象")
    return payload


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv
    try:
        payload = load_payload(argv)
        result = dispatch(payload)
    except PolicyDataError as exc:
        print(json.dumps(envelope(False, {"error": str(exc)}), ensure_ascii=False, indent=2), file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("success", False) else 1


if __name__ == "__main__":
    raise SystemExit(main())
