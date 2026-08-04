#!/usr/bin/env python3
"""
条款匹配引擎 v4.0
风险点 → 条款库检索 → 推荐替换文本

匹配策略（三级）：
1. 索引分类定位：风险类型映射到条款库 10 大分类，缩小候选范围
2. 关键词命中：用索引 keywords 与风险标题/描述做倒排命中，扩展候选
3. 综合打分：分类匹配 + 关键词重叠 + 适用范围 + 风险等级，取最高分
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 条款库路径
CLAUSE_LIBRARY_PATH = Path(__file__).parent.parent / 'references' / 'clause_library' / 'clauses.json'
CLAUSE_INDEX_PATH = Path(__file__).parent.parent / 'references' / 'clause_library' / 'clause_index.yaml'

# 风险类型 → 条款库分类（覆盖全部 10 个分类）
RISK_TYPE_MAPPING = {
    '主体风险': 'subject',
    '条款风险': 'clause',
    '金额风险': 'amount',
    '价款风险': 'amount',
    '履行风险': 'performance',
    '交付风险': 'performance',
    '质量风险': 'performance',
    '争议解决风险': 'dispute',
    '争议风险': 'dispute',
    '合规风险': 'compliance',
    '知识产权风险': 'ip',
    '知识产权': 'ip',
    '保密风险': 'confidentiality',
    '保密': 'confidentiality',
    '终止风险': 'termination',
    '解除风险': 'termination',
    '违约责任风险': 'liability',
    '违约风险': 'liability',
    '责任风险': 'liability',
}

# 规则引擎英文分类 → 条款库分类（专用规则/行业规则使用英文 category）
ENGLISH_CATEGORY_MAPPING = {
    'subject': 'subject', 'party': 'subject',
    'clause': 'clause', 'terms': 'clause',
    'amount': 'amount', 'payment': 'amount', 'price': 'amount',
    'performance': 'performance', 'delivery': 'performance', 'quality': 'performance',
    'dispute': 'dispute', 'arbitration': 'dispute', 'jurisdiction': 'dispute',
    'compliance': 'compliance', 'regulatory': 'compliance',
    'ip': 'ip', 'intellectual_property': 'ip',
    'confidentiality': 'confidentiality', 'nda': 'confidentiality',
    'termination': 'termination', 'exit': 'termination',
    'liability': 'liability', 'breach': 'liability', 'penalty': 'liability',
}

# 严重等级归一化：规则引擎(critical/high/...)、LLM(严重/中等/...)、条款库(高/中等/低)
SEVERITY_TO_LEVEL = {
    'critical': '高', 'high': '高', '严重': '高', '高': '高',
    'medium': '中等', '中等': '中等', '中': '中等',
    'low': '低', '一般': '中等', '提示': '低', '低': '低',
}

# 匹配分数阈值，低于此值视为未匹配
MATCH_THRESHOLD = 0.25

# 《民法典》第 470 条七项必备条款 → 条款库基础条款的确定性映射。
# 这七项是「缺失条款」类风险的固定场景，通用打分容易命中细分场景条款
# （如「缺少质量条款」匹到「隐蔽瑕疵异议期」），此处直接指定基础通用条款，
# 优先级高于打分匹配；映射的 ID 不存在时自动回退到打分流程。
ESSENTIAL_CLAUSE_PREFERRED = {
    '标的': ['CL039'],
    '数量': ['CL040'],
    '质量': ['CL105', 'CL193'],
    '价款': ['CL058', 'CL057'],
    '履行期限': ['CL101', 'CL103'],
    '违约责任': ['CL260', 'CL078'],
    '争议解决': ['CL144', 'CL146'],
}


class ClauseMatcher:
    """条款匹配器"""

    def __init__(self, library_path: Path = None, index_path: Path = None):
        self.library_path = library_path or CLAUSE_LIBRARY_PATH
        self.index_path = index_path or CLAUSE_INDEX_PATH
        self._clauses: List[Dict] = []
        self._index: Dict[str, Dict] = {}
        self._clause_by_id: Dict[str, Dict] = {}
        # 关键词倒排：keyword -> 分类代码集合
        self._keyword_index: Dict[str, List[str]] = {}
        self._loaded = False

    def load(self):
        """加载条款库和索引"""
        if self._loaded:
            return

        try:
            with open(self.library_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self._clauses = data.get('clauses', [])
            self._clause_by_id = {c['id']: c for c in self._clauses if 'id' in c}

            import yaml
            with open(self.index_path, 'r', encoding='utf-8') as f:
                self._index = yaml.safe_load(f) or {}

            # 构建关键词倒排索引
            for cat_code, entry in self._index.items():
                if not isinstance(entry, dict):
                    continue
                for kw in entry.get('keywords', []) or []:
                    self._keyword_index.setdefault(str(kw), []).append(cat_code)

            self._loaded = True
            logger.info(
                f"条款库加载完成: {len(self._clauses)} 条，"
                f"{len(self._index)} 个分类，{len(self._keyword_index)} 个关键词"
            )
        except Exception as e:
            logger.warning(f"条款库加载失败: {e}")
            self._clauses = []
            self._index = {}
            self._keyword_index = {}
            self._loaded = True  # 避免反复重试

    def get_by_id(self, clause_id: str) -> Optional[Dict]:
        """按条款编号精确获取"""
        if not self._loaded:
            self.load()
        return self._clause_by_id.get(clause_id)

    def match(self, risk: Dict, contract_type: str = "") -> Optional[Dict]:
        """
        为风险点匹配推荐条款

        Args:
            risk: 风险点字典（含 risk_type, title, description, severity 等）
            contract_type: 合同类型

        Returns:
            匹配的条款字典，或 None
        """
        if not self._loaded:
            self.load()
        if not self._clauses:
            return None

        # 七项法定必备条款走确定性映射，避免打分命中细分场景条款
        preferred = self._match_essential(risk, contract_type)
        if preferred:
            return preferred

        categories = self._resolve_categories(risk)
        candidate_ids = self._collect_candidates(categories)

        # 无候选时全库扫描（关键词打分兜底）
        pool = (
            [self._clause_by_id[i] for i in candidate_ids if i in self._clause_by_id]
            if candidate_ids else self._clauses
        )

        best_match = None
        best_score = 0.0
        for clause in pool:
            score = self._calculate_match_score(risk, clause, contract_type, categories)
            if score > best_score + 1e-9:
                best_score = score
                best_match = clause
            elif abs(score - best_score) <= 1e-9 and best_match is not None:
                # 同分时优先选更通用、编号更靠前的基础条款
                if self._is_more_general(clause, best_match):
                    best_match = clause

        if best_score < MATCH_THRESHOLD:
            return None
        return best_match

    def _match_essential(self, risk: Dict, contract_type: str) -> Optional[Dict]:
        """
        命中「可能缺少【X】相关条款」时，按确定性映射返回基础条款。
        
        多个候选时优先选适用范围覆盖当前合同类型的那条，其次取首选项。
        映射的条款 ID 在库中不存在时返回 None，交回打分流程兜底。
        """
        title = str(risk.get('title', '') or '')
        if '缺少' not in title and '缺失' not in title:
            return None
        
        for item, clause_ids in ESSENTIAL_CLAUSE_PREFERRED.items():
            if f'【{item}】' not in title and f'[{item}]' not in title:
                continue
            
            candidates = [self._clause_by_id[cid] for cid in clause_ids
                          if cid in self._clause_by_id]
            if not candidates:
                return None
            
            if contract_type:
                for c in candidates:
                    scope = c.get('applicable_scope', []) or []
                    if contract_type in scope:
                        return c
            return candidates[0]
        
        return None

    @staticmethod
    def _is_more_general(candidate: Dict, current: Dict) -> bool:
        """同分条款择优：适用范围更广者优先，其次条款编号更小者优先"""
        c_scope = len(candidate.get('applicable_scope', []) or [])
        u_scope = len(current.get('applicable_scope', []) or [])
        if c_scope != u_scope:
            return c_scope > u_scope
        return str(candidate.get('id', '')) < str(current.get('id', ''))

    def match_top_n(self, risk: Dict, contract_type: str = "", n: int = 3) -> List[Dict]:
        """返回匹配度最高的前 N 条条款（含 score 字段）"""
        if not self._loaded:
            self.load()
        if not self._clauses:
            return []

        categories = self._resolve_categories(risk)
        candidate_ids = self._collect_candidates(categories)
        pool = (
            [self._clause_by_id[i] for i in candidate_ids if i in self._clause_by_id]
            if candidate_ids else self._clauses
        )

        scored = []
        for clause in pool:
            score = self._calculate_match_score(risk, clause, contract_type, categories)
            if score >= MATCH_THRESHOLD:
                item = dict(clause)
                item['score'] = round(score, 3)
                scored.append(item)

        scored.sort(key=lambda c: c['score'], reverse=True)
        return scored[:n]

    def match_batch(self, risks: List[Dict], contract_type: str = "") -> Dict[str, Optional[Dict]]:
        """批量匹配风险点 → {risk_id: clause}"""
        results = {}
        for risk in risks:
            risk_id = risk.get('risk_id', risk.get('title', ''))
            results[risk_id] = self.match(risk, contract_type)
        return results

    def _resolve_categories(self, risk: Dict) -> List[str]:
        """
        解析风险点归属的条款库分类，按置信度降序返回

        置信度来源：风险类型精确映射（最高） > 长关键词命中 > 短关键词命中
        """
        weights: Dict[str, float] = {}

        def bump(code: str, w: float):
            if code:
                weights[code] = weights.get(code, 0.0) + w

        risk_type = str(risk.get('risk_type', '')).strip()

        # 1. 中文风险类型精确映射（强信号）
        if risk_type in RISK_TYPE_MAPPING:
            bump(RISK_TYPE_MAPPING[risk_type], 10.0)
        else:
            for cn, code in RISK_TYPE_MAPPING.items():
                if cn and cn in risk_type:
                    bump(code, 6.0)

        # 2. 英文分类映射（专用规则/行业规则使用英文 category）
        low = risk_type.lower()
        if low in ENGLISH_CATEGORY_MAPPING:
            bump(ENGLISH_CATEGORY_MAPPING[low], 10.0)

        # 3. 关键词倒排命中：关键词越长越具体，权重越高
        text = f"{risk.get('title', '')} {risk.get('description', '')}"
        for kw, codes in self._keyword_index.items():
            if kw and kw in text:
                # 长度 2 的通用词权重低，长度 >=4 的专有词权重高
                w = 0.6 if len(kw) <= 2 else (1.2 if len(kw) == 3 else 2.2)
                # 命中该词的分类越少，说明该词越专属
                w = w / max(1, len(codes))
                for code in codes:
                    bump(code, w)

        return [c for c, _ in sorted(weights.items(), key=lambda kv: kv[1], reverse=True)]

    def _collect_candidates(self, categories: List[str]) -> set:
        """按分类收集候选条款 id"""
        candidate_ids = set()
        for code in categories:
            entry = self._index.get(code)
            if isinstance(entry, dict):
                candidate_ids.update(entry.get('clause_ids', []) or [])
        return candidate_ids

    def _keyword_overlap(self, text1: str, text2: str) -> float:
        """计算两段中文文本的字符级 n-gram 重叠度（对中文分词无依赖）"""
        g1 = self._bigrams(text1)
        g2 = self._bigrams(text2)
        if not g1 or not g2:
            return 0.0
        return len(g1 & g2) / min(len(g1), len(g2))

    @staticmethod
    def _bigrams(text: str) -> set:
        """提取中文二元组，用于无分词的相似度计算"""
        chars = ''.join(re.findall(r'[\u4e00-\u9fffA-Za-z0-9]+', str(text)))
        if len(chars) < 2:
            return set(chars)
        return {chars[i:i + 2] for i in range(len(chars) - 1)}

    def _calculate_match_score(self, risk: Dict, clause: Dict,
                               contract_type: str, categories: List[str] = None) -> float:
        """
        计算风险点与条款的匹配分数 (0-1)

        权重：主题词命中 0.40 + 分类 0.25 + 文本相似 0.15 + 适用范围 0.12 + 风险等级 0.08
        主题词命中是决定性信号——风险标题与条款名称共有的领域名词
        """
        score = 0.0
        categories = categories or []
        clause_category = clause.get('category', '')
        clause_name = clause.get('name', '')
        risk_title = str(risk.get('title', ''))
        risk_desc = str(risk.get('description', ''))

        # 1. 主题词命中：条款名称中的领域名词是否出现在风险标题/描述中
        topic_score = self._topic_hit_score(risk_title, risk_desc, clause_name)
        score += topic_score * 0.40

        # 2. 分类匹配（按 _resolve_categories 的置信度排序加权）
        if clause_category and clause_category in categories:
            rank = categories.index(clause_category)
            if rank == 0:
                score += 0.25
            elif rank == 1:
                score += 0.15
            else:
                score += 0.06

        # 3. 文本相似度（标题 vs 条款名称，权重高于描述）
        score += self._keyword_overlap(risk_title, clause_name) * 0.15

        # 4. 合同类型适用范围
        applicable_scope = clause.get('applicable_scope', []) or []
        if applicable_scope:
            if contract_type and any(contract_type in s or s in contract_type
                                     for s in applicable_scope):
                score += 0.12
            elif '通用' in applicable_scope:
                score += 0.06

        # 5. 风险等级匹配（跨口径归一化后比较）
        sev = str(risk.get('severity', '')).strip()
        risk_level = SEVERITY_TO_LEVEL.get(sev.lower(), SEVERITY_TO_LEVEL.get(sev, ''))
        clause_level = str(clause.get('risk_level', '')).strip()
        if risk_level and clause_level and risk_level == clause_level:
            score += 0.08

        return min(1.0, score)

    def _topic_hit_score(self, risk_title: str, risk_desc: str, clause_name: str) -> float:
        """
        主题词命中评分：提取条款名称中的领域名词，检查是否出现在风险文本中

        条款名称形如「违约金标准条款（建议版本）」，去掉「条款/建议版本」等模板词后
        剩下的即为领域主题词（违约金、标准）

        特殊处理：缺失条款类风险标题形如「可能缺少【数量】相关条款」，
        方括号内即为精确主题词，直接与条款名称做包含判定
        """
        if not clause_name:
            return 0.0

        # 缺失条款类风险：方括号内的关键要素是唯一有效主题词
        bracket = re.findall(r'[【\[]([^】\]]+)[】\]]', risk_title)
        if bracket:
            core_name = re.sub(r'[（(].*?[）)]', '', clause_name)
            for term in bracket:
                term = term.strip()
                if term and term in core_name:
                    return 1.0
            return 0.0

        # 去除条款名称的模板后缀
        core = re.sub(r'[（(].*?[）)]', '', clause_name)
        core = re.sub(r'条款$|约定$|条$', '', core.strip())
        if not core:
            return 0.0

        risk_text = f"{risk_title}{risk_desc}"
        if not risk_text:
            return 0.0

        # 完整主题词直接命中 → 满分
        if len(core) >= 2 and core in risk_text:
            return 1.0

        # 主题词切分为 2-4 字候选词，统计命中比例（标题命中权重加倍）
        candidates = self._topic_terms(core)
        if not candidates:
            return 0.0

        hit_weight = 0.0
        total_weight = 0.0
        for term in candidates:
            w = len(term)  # 词越长越重要
            total_weight += w
            if term in risk_title:
                hit_weight += w * 1.0
            elif term in risk_desc:
                hit_weight += w * 0.6

        return min(1.0, hit_weight / total_weight) if total_weight else 0.0

    @staticmethod
    def _topic_terms(core: str) -> List[str]:
        """从条款核心名称中提取 2-4 字主题词候选"""
        # 按常见连接词切分
        parts = re.split(r'[与和及、／/\s，,]+', core)
        terms = []
        for part in parts:
            part = part.strip()
            if len(part) < 2:
                continue
            if len(part) <= 4:
                terms.append(part)
            else:
                # 长词滑窗切分为 3 字词，保留整体
                terms.append(part)
                terms.extend(part[i:i + 3] for i in range(0, len(part) - 2))
        return terms


def main():
    """命令行测试"""
    matcher = ClauseMatcher()
    matcher.load()

    test_risks = [
        {'risk_id': 'T1', 'risk_type': '条款风险', 'title': '违约责任约定不明确',
         'description': '未约定违约金计算方式', 'severity': '严重'},
        {'risk_id': 'T2', 'risk_type': '主体风险', 'title': '签约主体信息不完整',
         'description': '缺少统一社会信用代码', 'severity': 'high'},
        {'risk_id': 'T3', 'risk_type': '争议解决风险', 'title': '仲裁机构名称不准确',
         'description': '仲裁委员会表述不规范', 'severity': 'medium'},
    ]

    for risk in test_risks:
        result = matcher.match(risk, '买卖合同')
        if result:
            print(f"[{risk['risk_id']}] 匹配 {result['id']} {result.get('name')}")
            print(f"      推荐措辞: {result.get('recommended_text', '')[:60]}...")
        else:
            print(f"[{risk['risk_id']}] 未匹配到条款")


if __name__ == '__main__':
    main()
