#!/usr/bin/env python3
"""
Skill 更新检测模块 v3.0
异步检查 GitHub 新版本，每 7 天提醒一次
"""

import json
import re
import time
import urllib.request
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 更新检查配置
UPDATE_CHECK_PATH = Path.home() / '.contract-review' / 'update_check.json'
CHECK_INTERVAL_SECONDS = 7 * 24 * 3600  # 7 天
GITHUB_RAW_URL = 'https://raw.githubusercontent.com/fyniujin/devskill/main/contract-review/SKILL.md'
REQUEST_TIMEOUT = 10  # 秒


class UpdateChecker:
    """更新检测器"""
    
    def __init__(self, github_url: str = GITHUB_RAW_URL):
        self.github_url = github_url
        self._check_data: Optional[Dict[str, Any]] = None
    
    def check(self, force: bool = False) -> Optional[Dict[str, Any]]:
        """
        检查是否有新版本
        
        Returns:
            None: 无新版本或检查失败
            Dict: 有新版本，返回版本信息
        """
        # 读取检查记录
        check_data = self._load_check_data()
        
        # 检查是否需要跳过（7 天内已检查过）
        if not force:
            last_check = check_data.get('last_check_time', 0)
            if time.time() - last_check < CHECK_INTERVAL_SECONDS:
                logger.debug("跳过更新检查（7 天内已检查）")
                return None
        
        # 获取远程版本
        remote_version = self._fetch_remote_version()
        if remote_version is None:
            return None
        
        # 获取本地版本
        local_version = self._get_local_version()
        
        # 更新检查记录
        check_data['last_check_time'] = time.time()
        check_data['last_remote_version'] = remote_version
        check_data['last_local_version'] = local_version
        self._save_check_data(check_data)
        
        # 比较版本
        if self._compare_versions(remote_version, local_version) > 0:
            return {
                'local_version': local_version,
                'remote_version': remote_version,
                'should_notify': self._should_notify(check_data, remote_version),
            }
        
        return None
    
    def get_update_message(self, update_info: Dict[str, Any]) -> str:
        """生成更新提示消息"""
        local = update_info.get('local_version', '?')
        remote = update_info.get('remote_version', '?')
        
        return (
            f"\n{'=' * 50}\n"
            f"📢 发现新版本 v{remote} (当前 v{local})\n"
            f"{'=' * 50}\n"
            f"更新内容：新增 Word 报告生成、历史版本对比、硬件自适应调度、安全风险拦截等功能。\n"
            f"更新方法：运行 skillhub install contract-review\n"
            f"{'=' * 50}\n"
        )
    
    def _fetch_remote_version(self) -> Optional[str]:
        """从 GitHub 获取远程版本号"""
        try:
            req = urllib.request.Request(
                self.github_url,
                headers={'User-Agent': 'contract-review-updater/3.0'}
            )
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
                content = response.read().decode('utf-8')
            
            # 从 SKILL.md 中提取版本号
            # 匹配 version: x.y.z 或 version: "x.y.z"
            match = re.search(r'version:\s*["\']?(\d+\.\d+\.\d+)["\']?', content)
            if match:
                return match.group(1)
            
            logger.warning("无法从远程 SKILL.md 解析版本号")
            return None
        except Exception as e:
            logger.debug(f"获取远程版本失败: {e}")
            return None
    
    def _get_local_version(self) -> str:
        """获取本地版本号"""
        # 从 SKILL.md 读取
        skill_md = Path(__file__).parent.parent / 'SKILL.md'
        try:
            with open(skill_md, 'r', encoding='utf-8') as f:
                content = f.read()
            match = re.search(r'version:\s*["\']?(\d+\.\d+\.\d+)["\']?', content)
            if match:
                return match.group(1)
        except Exception:
            pass
        return '2.5.0'  # 默认值
    
    def _compare_versions(self, v1: str, v2: str) -> int:
        """
        比较两个版本号
        
        Returns:
            1: v1 > v2
            0: v1 == v2
            -1: v1 < v2
        """
        def parse_version(v):
            return tuple(int(x) for x in v.split('.'))
        
        try:
            v1_parts = parse_version(v1)
            v2_parts = parse_version(v2)
            
            if v1_parts > v2_parts:
                return 1
            elif v1_parts < v2_parts:
                return -1
            return 0
        except Exception:
            return 0
    
    def _should_notify(self, check_data: Dict, remote_version: str) -> bool:
        """判断是否需要提醒（同一版本 7 天内只提醒一次）"""
        last_notified_version = check_data.get('last_notified_version', '')
        last_notified_time = check_data.get('last_notified_time', 0)
        
        # 如果是新版本，或者同一版本超过 7 天，需要提醒
        if remote_version != last_notified_version:
            return True
        
        if time.time() - last_notified_time >= CHECK_INTERVAL_SECONDS:
            return True
        
        return False
    
    def record_notified(self, version: str):
        """记录已提醒的版本"""
        check_data = self._load_check_data()
        check_data['last_notified_version'] = version
        check_data['last_notified_time'] = time.time()
        self._save_check_data(check_data)
    
    def _load_check_data(self) -> Dict[str, Any]:
        """加载检查记录"""
        if self._check_data is not None:
            return self._check_data
        
        try:
            if UPDATE_CHECK_PATH.exists():
                with open(UPDATE_CHECK_PATH, 'r', encoding='utf-8') as f:
                    self._check_data = json.load(f)
                return self._check_data
        except Exception as e:
            logger.debug(f"读取更新检查记录失败: {e}")
        
        return {}
    
    def _save_check_data(self, data: Dict[str, Any]):
        """保存检查记录"""
        try:
            UPDATE_CHECK_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(UPDATE_CHECK_PATH, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self._check_data = data
        except Exception as e:
            logger.debug(f"保存更新检查记录失败: {e}")


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Skill 更新检测 v3.0')
    parser.add_argument('--force', '-f', action='store_true', help='强制检查（忽略 7 天间隔）')
    parser.add_argument('--quiet', '-q', action='store_true', help='静默模式（只输出 JSON）')
    args = parser.parse_args()
    
    checker = UpdateChecker()
    update_info = checker.check(force=args.force)
    
    if update_info:
        if args.quiet:
            print(json.dumps(update_info, ensure_ascii=False))
        else:
            print(checker.get_update_message(update_info))
    else:
        if args.quiet:
            print('{}')
        else:
            print("✅ 当前已是最新版本")


if __name__ == '__main__':
    main()
