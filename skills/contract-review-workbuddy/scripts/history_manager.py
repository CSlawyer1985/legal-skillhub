#!/usr/bin/env python3
"""
历史审查记录管理模块 v3.0
支持：审查记录保存、版本查询、diff 对比（只高亮新增风险点）
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 历史记录存储路径
HISTORY_DIR = Path.home() / '.contract-review' / 'history'


class HistoryManager:
    """历史审查记录管理器"""
    
    def __init__(self, history_dir: Optional[Path] = None):
        self.history_dir = history_dir or HISTORY_DIR
        self.history_dir.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def compute_contract_hash(contract_text: str) -> str:
        """
        计算合同文本的 SHA256 指纹（用于判断是否为同一份合同）
        
        Returns:
            16 位十六进制字符串
        """
        # 去除空白字符后计算哈希（避免格式差异导致同一份合同被识别为不同）
        normalized = ''.join(contract_text.split())
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()[:16]
    
    def save_review(self, contract_text: str, review_result: Dict[str, Any]) -> str:
        """
        保存审查记录
        
        Args:
            contract_text: 合同原文（用于计算哈希）
            review_result: 审查结果（包含 risks, score, contract_info 等）
            
        Returns:
            记录ID
        """
        contract_hash = self.compute_contract_hash(contract_text)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        record_id = f"{contract_hash}_{timestamp}"
        
        history_file = self.history_dir / f"{contract_hash}.json"
        
        # 读取已有记录
        history = self._load_history(history_file)
        
        # 提取本次审查的风险指纹（用于 diff）
        risks = review_result.get('risks', [])
        risk_signatures = []
        for risk in risks:
            sig = self._compute_risk_signature(risk)
            risk_signatures.append(sig)
        
        # 创建新版本记录
        version_record = {
            'record_id': record_id,
            'timestamp': timestamp,
            'score': review_result.get('score', 0),
            'summary': {
                'total_risks': len(risks),
                'critical': sum(1 for r in risks if r.get('severity') == '严重'),
                'medium': sum(1 for r in risks if r.get('severity') == '中等'),
                'low': sum(1 for r in risks if r.get('severity') == '一般'),
                'info': sum(1 for r in risks if r.get('severity') == '提示'),
            },
            'risk_signatures': set(risk_signatures),  # 存储为集合
            'contract_info': review_result.get('contract_info', {}),
            'report_summary': review_result.get('report_summary', ''),
        }
        
        history['versions'].append(version_record)
        
        # 保存回文件
        self._save_history(history_file, history)
        
        logger.info(f"审查记录已保存: {record_id}")
        return record_id
    
    def get_history(self, contract_text: str) -> Optional[Dict[str, Any]]:
        """获取合同的历史审查记录"""
        contract_hash = self.compute_contract_hash(contract_text)
        history_file = self.history_dir / f"{contract_hash}.json"
        return self._load_history(history_file)
    
    def get_latest_version(self, contract_text: str) -> Optional[Dict[str, Any]]:
        """获取最新版本的审查记录"""
        history = self.get_history(contract_text)
        if not history or not history.get('versions'):
            return None
        return history['versions'][-1]
    
    def diff_reviews(self, old_review: Dict[str, Any], new_review: Dict[str, Any]) -> Dict[str, Any]:
        """
        对比两个审查结果，只保留新增风险点
        
        Args:
            old_review: 旧版本审查结果
            new_review: 新版本审查结果
            
        Returns:
            {
                'new_risks': List[Dict],      # 新增的风险点
                'resolved_risks': List[Dict],  # 已解决的风险点（旧有新无）
                'changed_risks': List[Dict],   # 严重等级变化的风险点
                'summary': str,               # 对比摘要
            }
        """
        old_risks = old_review.get('risks', [])
        new_risks = new_review.get('risks', [])
        
        # 计算风险签名集合
        old_sigs = {self._compute_risk_signature(r) for r in old_risks}
        new_sigs = {self._compute_risk_signature(r) for r in new_risks}
        
        # 新增风险：在新结果中但不在旧结果中
        added_sigs = new_sigs - old_sigs
        new_only = [r for r in new_risks if self._compute_risk_signature(r) in added_sigs]
        
        # 已解决风险：在旧结果中但不在新结果中
        resolved_sigs = old_sigs - new_sigs
        resolved_only = [r for r in old_risks if self._compute_risk_signature(r) in resolved_sigs]
        
        # 严重等级变化（可选：通过标题匹配检查同一风险点的等级变化）
        changed = self._detect_severity_changes(old_risks, new_risks)
        
        # 生成摘要
        summary = self._generate_diff_summary(new_only, resolved_only, changed)
        
        return {
            'new_risks': new_only,
            'resolved_risks': resolved_only,
            'changed_risks': changed,
            'summary': summary,
        }
    
    def list_all_contracts(self) -> List[Dict[str, Any]]:
        """列出所有审查过的合同"""
        contracts = []
        for f in sorted(self.history_dir.glob('*.json'), reverse=True):
            try:
                with open(f, 'r', encoding='utf-8') as fh:
                    data = json.load(fh)
                
                versions = data.get('versions', [])
                contract_info = versions[-1].get('contract_info', {}) if versions else {}
                
                contracts.append({
                    'contract_hash': data.get('contract_hash', ''),
                    'title': contract_info.get('title', '未知合同'),
                    'contract_type': contract_info.get('contract_type', '未知'),
                    'last_reviewed': versions[-1].get('timestamp', '') if versions else '',
                    'total_versions': len(versions),
                    'file_path': str(f),
                })
            except Exception as e:
                logger.warning(f"读取历史记录失败 {f}: {e}")
        
        return contracts
    
    def _compute_risk_signature(self, risk: Dict[str, Any]) -> str:
        """
        计算风险点的稳定签名（用于判断是否为同一个风险点）
        
        使用 title + risk_type + clause_ref 组合，比单独比较更稳定
        """
        parts = [
            risk.get('title', ''),
            risk.get('risk_type', ''),
            risk.get('clause_ref', ''),
            # 使用前 30 字符的原文片段（避免微小差异导致签名不同）
            risk.get('text_snippet', '')[:30],
        ]
        combined = '|'.join(parts)
        return hashlib.md5(combined.encode('utf-8')).hexdigest()[:12]
    
    def _detect_severity_changes(self, old_risks: List[Dict], new_risks: List[Dict]) -> List[Dict]:
        """检测风险点严重等级的变化"""
        # 建立标题到风险点的映射
        old_map = {(r.get('title', ''), r.get('clause_ref', '')): r for r in old_risks}
        
        changed = []
        for new_risk in new_risks:
            key = (new_risk.get('title', ''), new_risk.get('clause_ref', ''))
            if key in old_map:
                old_risk = old_map[key]
                if old_risk.get('severity') != new_risk.get('severity'):
                    changed.append({
                        'title': new_risk.get('title', ''),
                        'clause_ref': new_risk.get('clause_ref', ''),
                        'old_severity': old_risk.get('severity'),
                        'new_severity': new_risk.get('severity'),
                    })
        
        return changed
    
    def _generate_diff_summary(self, new_risks: List, resolved: List, changed: List) -> str:
        """生成对比摘要"""
        parts = []
        if new_risks:
            parts.append(f"🆕 **新增** {len(new_risks)} 个风险点")
        if resolved:
            parts.append(f"✅ **已解决** {len(resolved)} 个风险点")
        if changed:
            parts.append(f"⚠️ **等级变化** {len(changed)} 个风险点")
        
        if not parts:
            return "📋 新旧版本无明显变化"
        
        return " | ".join(parts)
    
    def _load_history(self, path: Path) -> Dict[str, Any]:
        """加载历史记录文件"""
        if not path.exists():
            return {
                'contract_hash': path.stem,
                'created_at': datetime.now().strftime('%Y%m%d_%H%M%S'),
                'versions': [],
            }
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # 确保 risk_signatures 字段存在
            for v in data.get('versions', []):
                if 'risk_signatures' not in v:
                    v['risk_signatures'] = []
            return data
        except Exception as e:
            logger.warning(f"读取历史记录失败 {path}: {e}")
            return {
                'contract_hash': path.stem,
                'created_at': datetime.now().strftime('%Y%m%d_%H%M%S'),
                'versions': [],
            }
    
    def _save_history(self, path: Path, data: Dict[str, Any]):
        """保存历史记录文件"""
        try:
            # 将 set 转换为 list 以便 JSON 序列化
            save_data = json.loads(json.dumps(data, default=list))
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存历史记录失败 {path}: {e}")


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='合同审查历史记录管理 v3.0')
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # list 子命令
    subparsers.add_parser('list', help='列出所有审查过的合同')
    
    # diff 子命令
    diff_parser = subparsers.add_parser('diff', help='对比两个审查结果文件')
    diff_parser.add_argument('old_report', help='旧版报告 JSON 路径')
    diff_parser.add_argument('new_report', help='新版报告 JSON 路径')
    
    args = parser.parse_args()
    
    manager = HistoryManager()
    
    if args.command == 'list':
        contracts = manager.list_all_contracts()
        if not contracts:
            print("暂无历史审查记录")
            return
        
        print(f"{'=' * 60}")
        print(f"📋 历史审查记录 ({len(contracts)} 份合同)")
        print(f"{'=' * 60}")
        for c in contracts:
            print(f"\n  📄 {c['title']}")
            print(f"     类型: {c['contract_type']}")
            print(f"     审查次数: {c['total_versions']}")
            print(f"     最近审查: {c['last_reviewed']}")
    elif args.command == 'diff':
        # 从 JSON 文件读取并对比
        with open(args.old_report, 'r', encoding='utf-8') as f:
            old = json.load(f)
        with open(args.new_report, 'r', encoding='utf-8') as f:
            new = json.load(f)
        
        result = manager.diff_reviews(old, new)
        print(f"\n{'=' * 60}")
        print("📊 版本对比结果")
        print(f"{'=' * 60}")
        print(f"\n{result['summary']}\n")
        
        if result['new_risks']:
            print("🆕 新增风险点:")
            for r in result['new_risks']:
                print(f"  - [{r.get('severity', '?')}] {r.get('title', '')}")
        
        if result['resolved_risks']:
            print("\n✅ 已解决风险点:")
            for r in result['resolved_risks']:
                print(f"  - {r.get('title', '')}")
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
