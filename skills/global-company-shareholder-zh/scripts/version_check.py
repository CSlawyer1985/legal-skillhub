"""
SKILL 版本检测模块
用于检测服务端是否有新版本的 skill 可供升级
"""
import os
import json
import re
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import httpx

# 配置路径
UPKUAJING_DIR = Path.home() / '.upkuajing'
VERSION_CACHE_FILE = UPKUAJING_DIR / 'version_cache.json'

# 技能目录配置
SKILL_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 已检测标记（进程内缓存，避免重复检测）
_CHECKED_FLAG = False


def get_version_cache_file() -> Path:
    """获取版本缓存文件路径"""
    UPKUAJING_DIR.mkdir(parents=True, exist_ok=True)
    return VERSION_CACHE_FILE


def load_version_cache() -> Dict[str, Any]:
    """加载版本缓存"""
    cache_file = get_version_cache_file()
    if cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_version_cache(cache: Dict[str, Any]) -> None:
    """保存版本缓存"""
    cache_file = get_version_cache_file()
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except IOError:
        pass


def get_skill_name() -> str:
    """获取当前 skill 的名称（从目录名）"""
    return os.path.basename(SKILL_BASE_DIR)


def get_skill_version() -> str:
    """从 SKILL.md front matter 提取版本号"""
    skill_md = os.path.join(SKILL_BASE_DIR, 'SKILL.md')
    try:
        with open(skill_md, 'r', encoding='utf-8') as f:
            content = f.read()
        # 提取 metadata: {"version":"1.0.5",...}
        match = re.search(r'"version"\s*:\s*"([^"]+)"', content)
        return match.group(1) if match else "unknown"
    except (IOError, FileNotFoundError):
        return "unknown"


def is_check_needed(skill_name: str) -> bool:
    """判断是否需要检查版本（每天第一次 API 调用时触发）"""
    cache = load_version_cache()
    today = datetime.now().strftime('%Y-%m-%d')

    if skill_name not in cache:
        return True

    skill_cache = cache[skill_name]
    return skill_cache.get("last_check_date") != today


def mark_checked(skill_name: str, latest_version: str) -> None:
    """标记已检查"""
    cache = load_version_cache()
    today = datetime.now().strftime('%Y-%m-%d')

    cache[skill_name] = {
        "last_check_date": today,
        "latest_version": latest_version
    }
    save_version_cache(cache)


def check_skill_version(skill_name: str, api_base_url: str) -> Optional[str]:
    """调用 API 检查最新版本"""
    try:
        url = f"{api_base_url}/agent/api/skills/version"
        headers = {"Content-Type": "application/json"}

        with httpx.Client(timeout=10.0) as client:
            response = client.post(url, json={"name": skill_name}, headers=headers)
            response.raise_for_status()

            data = response.json()
            if data.get("code") == 0:
                return data.get("data")
    except Exception as e:
        print(f"Error checking skill version:{e}", file=sys.stderr)
        pass
    return None


def notify_upgrade(skill_name: str, current_version: str, latest_version: str):
    """生成升级提示信息"""
    notice = f"""📢 Skill 升级提示
技能: {skill_name}
当前版本: {current_version}
最新版本: {latest_version}
升级命令: clawhub update {skill_name}"""

    """打印升级提示到 stderr"""
    print("\n" + notice + "\n", file=sys.stderr)


def check_and_notify(api_base_url: str) -> bool:
    """
    执行版本检测并打印升级提示（如果有新版本）
    每天第一次 API 调用时触发，非阻塞
    Returns:
        True if an update is available, False otherwise
    """
    global _CHECKED_FLAG

    # 进程内检查，避免重复检测
    if _CHECKED_FLAG:
        return False
    _CHECKED_FLAG = True

    skill_name = get_skill_name()

    # 检查是否需要检测
    if not is_check_needed(skill_name):
        return False

    current_version = get_skill_version()
    latest_version = check_skill_version(skill_name, api_base_url)
    if latest_version and latest_version != current_version:
        # 标记已检查并打印升级提示
        mark_checked(skill_name, latest_version)
        notify_upgrade(skill_name, current_version, latest_version)
        return True

    # 即使没有新版本也标记已检查，避免重复检测
    if latest_version:
        mark_checked(skill_name, latest_version)
    return False


def get_cached_latest_version(skill_name: str) -> Optional[str]:
    """获取缓存中的最新版本（如果有）"""
    cache = load_version_cache()
    if skill_name in cache:
        return cache[skill_name].get("latest_version")
    return None
