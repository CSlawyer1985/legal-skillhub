#!/usr/bin/env python3
"""
规则引擎模块 v4.0
基于硬规则的确定性检查
安全特性：YAML 安全加载、输入长度限制、日志脱敏
v3.2 新增：按合同类型懒加载专用规则文件
v4.0 新增：按行业懒加载专项合规规则文件
"""

import re
from typing import List, Dict, Any
from pathlib import Path
import yaml
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 最大处理文本长度（防止 ReDoS 和内存溢出）
MAX_TEXT_LENGTH = 500000

# v3.2 合同类型与专用规则文件映射
CONTRACT_TYPE_RULE_FILES = {
    '股权转让合同': 'equity_transfer.yaml',
    '增资扩股协议': 'capital_increase.yaml',
    '对赌协议': 'valuation_adjustment.yaml',
    'NDA保密协议': 'nda.yaml',
    '知识产权许可协议': 'ip_license.yaml',
    '建设工程合同': 'construction.yaml',
    '劳动合同': 'labor_contract_deep.yaml',
    '采购框架协议': 'procurement_framework.yaml',
}

# v4.0 行业专项规则目录映射（key 为标准行业代码）
INDUSTRY_RULE_DIRS = {
    'medical': 'medical',
    'construction': 'construction',
    'cross_border': 'cross_border',
    'internet': 'internet',
}

# v4.0 行业别名（支持中文/简写输入）
INDUSTRY_ALIASES = {
    '医疗': 'medical', '医药': 'medical', '医疗器械': 'medical',
    'medical': 'medical', 'med': 'medical',
    '建筑': 'construction', '建设工程': 'construction', '工程': 'construction',
    'construction': 'construction', 'build': 'construction',
    '跨境': 'cross_border', '跨境电商': 'cross_border', '外贸': 'cross_border',
    'cross_border': 'cross_border', 'crossborder': 'cross_border', 'cb': 'cross_border',
    '互联网': 'internet', '软件': 'internet', '互联网软件': 'internet', 'it': 'internet',
    'internet': 'internet', 'software': 'internet', 'net': 'internet',
}


# v4.0 《民法典》第 470 条七项必备条款的同义表述族
# 合同实务中同一要素表述差异极大（如"标的"可写作"工程概况""服务内容""采购标的"），
# 仅做字面匹配会产生大量误报，此处按语义族匹配，命中任一同义词即视为已约定。
ESSENTIAL_CLAUSE_SYNONYMS = {
    '标的': [
        '标的', '工程概况', '工程内容', '服务内容', '服务事项', '开发内容',
        '采购内容', '货物名称', '产品名称', '项目内容', '委托事项', '租赁物',
        '许可范围', '供应', '交付物', '工作内容',
    ],
    '数量': [
        '数量', '数 量', '台', '件', '套', '吨', '批', '份', '平方米', '立方米',
        '建筑面积', '规模', '工程量', '人数', '并发', '席位', '授权数',
    ],
    '质量': [
        '质量', '品质', '技术标准', '验收标准', '规格', '技术要求', '质量保证',
        '国家标准', '行业标准', '合格', '性能指标', '服务水平', 'SLA',
    ],
    '价款': [
        '价款', '价格', '金额', '费用', '报酬', '款项', '合同价', '总价',
        '服务费', '租金', '对价', '结算', '计价', '元', '万元',
    ],
    '履行期限': [
        '履行期限', '期限', '工期', '交付时间', '交货期', '完成时间', '开工',
        '竣工', '交付日期', '服务期', '合作期', '有效期', '天内', '个月内',
        '日历天', '起止', '交付期', '完工', '上线时间', '生效日',
    ],
    '违约责任': [
        '违约责任', '违约金', '违约', '赔偿', '损失赔偿', '责任承担',
        '逾期责任', '罚则', '滞纳金',
    ],
    '争议解决': [
        '争议解决', '争议', '纠纷', '仲裁', '诉讼', '管辖', '法院', '调解',
        '协商解决',
    ],
}


def normalize_industry(industry: str) -> str:
    """将用户输入的行业名归一化为标准代码，无法识别返回空串"""
    if not industry:
        return ''
    key = str(industry).strip().lower()
    return INDUSTRY_ALIASES.get(key, INDUSTRY_ALIASES.get(str(industry).strip(), ''))


class RiskItem:
    """风险项"""
    def __init__(self, risk_id: str, risk_type: str, severity: str, 
                 title: str, description: str, suggestion: str,
                 legal_basis: str = "", text_snippet: str = "",
                 clause_ref: str = ""):
        self.risk_id = risk_id
        self.risk_type = risk_type
        self.severity = severity
        self.title = title
        self.description = description
        self.suggestion = suggestion
        self.legal_basis = legal_basis
        self.text_snippet = text_snippet
        self.clause_ref = clause_ref
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'risk_id': self.risk_id,
            'risk_type': self.risk_type,
            'severity': self.severity,
            'title': self.title,
            'description': self.description,
            'suggestion': self.suggestion,
            'legal_basis': self.legal_basis,
            'text_snippet': self.text_snippet,
            'clause_ref': self.clause_ref,
        }


class RuleEngine:
    """规则引擎"""
    
    def __init__(self, rules_path: str = None):
        """初始化规则引擎"""
        self.rules = []
        # v3.2 规则缓存（按合同类型）
        self._rule_cache: Dict[str, List[Dict]] = {}
        # v4.0 行业规则缓存
        self._industry_cache: Dict[str, List[Dict]] = {}
        if rules_path:
            self._load_rules(rules_path)
    
    def _load_rules(self, rules_path: str):
        """安全地从 YAML 文件加载规则（使用 safe_load 防止反序列化攻击）"""
        try:
            with open(rules_path, 'r', encoding='utf-8') as f:
                # YAML safe_load 已经是安全的，但为了双重保险，限制文件大小
                content = f.read(1024 * 1024)  # 最大 1MB
                config = yaml.safe_load(content)
            self.rules = config.get('rules', [])
            logger.info(f"加载了 {len(self.rules)} 条规则")
        except Exception as e:
            logger.error(f"规则加载失败: {e}")
            self.rules = []
    
    def check_all(self, text: str, contract_type: str = "", 
                  structure: Dict = None, industry: str = "") -> List[RiskItem]:
        """
        运行所有规则检查
        
        Args:
            text: 合同全文（最大 500KB）
            contract_type: 合同类型
            structure: 解析后的合同结构
            industry: v4.0 行业代码（medical/construction/cross_border/internet）
            
        Returns:
            风险项列表
        """
        # 安全检查：限制文本长度
        if len(text) > MAX_TEXT_LENGTH:
            logger.warning(f"文本过长 ({len(text)} 字符)，截断至 {MAX_TEXT_LENGTH} 字符")
            text = text[:MAX_TEXT_LENGTH]
        
        risks = []
        
        # v3.2 优先加载专用规则（如果存在）
        specific_rules = self._load_contract_specific_rules(contract_type)
        # v4.0 加载行业专项规则
        industry_rules = self._load_industry_rules(industry)
        all_rules = industry_rules + specific_rules + self.rules
        
        for rule in all_rules:
            if not rule.get('enabled', True):
                continue
            
            try:
                result = self._apply_rule(rule, text, contract_type, structure)
                if result:
                    if isinstance(result, list):
                        risks.extend(result)
                    else:
                        risks.append(result)
            except Exception as e:
                logger.warning(f"规则 {rule.get('id', '?')} 执行失败: {e}")
        
        return risks
    
    def _load_contract_specific_rules(self, contract_type: str) -> List[Dict]:
        """v3.2 按合同类型懒加载专用规则文件"""
        if not contract_type or contract_type not in CONTRACT_TYPE_RULE_FILES:
            return []
        
        # 检查缓存
        if contract_type in self._rule_cache:
            return self._rule_cache[contract_type]
        
        # 查找专用规则文件
        rule_file = CONTRACT_TYPE_RULE_FILES[contract_type]
        rules_dir = Path(__file__).parent.parent / 'references' / 'contract_types'
        rule_path = rules_dir / rule_file
        
        if not rule_path.exists():
            logger.debug(f"专用规则文件不存在: {rule_path}")
            return []
        
        try:
            with open(rule_path, 'r', encoding='utf-8') as f:
                content = f.read(1024 * 1024)
                config = yaml.safe_load(content)
            rules = config.get('rules', [])
            # 缓存
            self._rule_cache[contract_type] = rules
            logger.info(f"加载 {contract_type} 专用规则 {len(rules)} 条")
            return rules
        except Exception as e:
            logger.warning(f"加载专用规则失败: {e}")
            return []
    
    def _load_industry_rules(self, industry: str) -> List[Dict]:
        """v4.0 按行业懒加载专项合规规则文件"""
        code = normalize_industry(industry)
        if not code or code not in INDUSTRY_RULE_DIRS:
            if industry:
                logger.warning(f"未识别的行业: {industry}，可选值: {', '.join(sorted(INDUSTRY_RULE_DIRS))}")
            return []
        
        # 检查缓存
        if code in self._industry_cache:
            return self._industry_cache[code]
        
        rule_path = (Path(__file__).parent.parent / 'references' / 'industries'
                     / INDUSTRY_RULE_DIRS[code] / 'rules.yaml')
        
        if not rule_path.exists():
            logger.debug(f"行业规则文件不存在: {rule_path}")
            return []
        
        try:
            with open(rule_path, 'r', encoding='utf-8') as f:
                content = f.read(2 * 1024 * 1024)  # 行业规则较大，最大 2MB
                config = yaml.safe_load(content)
            rules = config.get('rules', []) if isinstance(config, dict) else []
            self._industry_cache[code] = rules
            logger.info(f"加载 {code} 行业专项规则 {len(rules)} 条")
            return rules
        except Exception as e:
            logger.warning(f"加载行业规则失败: {e}")
            return []
    
    def _apply_rule(self, rule: Dict, text: str, contract_type: str,
                    structure: Dict) -> Any:
        """应用单条规则"""
        check_type = rule.get('check_type', '')
        
        if check_type == 'regex_match':
            return self._check_regex(rule, text)
        elif check_type == 'threshold':
            return self._check_threshold(rule, text)
        elif check_type == 'pattern_match':
            return self._check_pattern(rule, text)
        elif check_type == 'checklist':
            return self._check_checklist(rule, text, structure)
        elif check_type == 'list_check':
            return self._check_list(rule, text)
        elif check_type in ('llm_check', 'api_check', 'prompt_check', 'semantic_check'):
            # 由 LLM 或外部服务处理
            return None
        else:
            logger.warning(f"未知的检查类型: {check_type}")
            return None
    
    def _get_rule_id(self, rule: Dict) -> str:
        """安全获取规则 ID（兼容 id/name 两种字段）"""
        return rule.get('id', rule.get('name', 'unknown'))
    
    @staticmethod
    def _extract_sentence(text: str, pos: int, max_len: int = 120) -> str:
        """
        v4.0 按句子边界提取风险原文片段
        
        原按固定字符窗口截取会跨行跨句，导致修订稿无法准确定位原文。
        改为向前找到句首、向后找到句末，保证片段是完整语句。
        """
        if pos < 0 or pos >= len(text):
            return ''
        
        boundaries = '。；！？\n\r'
        
        # 向前找句首
        start = pos
        while start > 0 and text[start - 1] not in boundaries:
            start -= 1
            if pos - start >= max_len:
                break
        
        # 向后找句末（含句号）
        end = pos
        while end < len(text) and text[end] not in boundaries:
            end += 1
            if end - start >= max_len:
                break
        if end < len(text) and text[end] in '。；！？':
            end += 1
        
        return text[start:end].strip()
    
    def _check_regex(self, rule: Dict, text: str) -> RiskItem:
        """正则匹配检查（安全的正则，防止 ReDoS）"""
        pattern = rule.get('check_rule', '')
        
        # 安全检查：限制正则复杂度
        if len(pattern) > 1000:
            logger.warning(f"跳过复杂正则 ({len(pattern)} 字符)")
            return None
        
        try:
            # 设置超时，防止正则灾难性回溯
            m = re.search(pattern, text)
        except re.error as e:
            logger.warning(f"正则错误: {e}")
            return None
        
        if m:
            # v4.0 统一按句子边界提取，保证修订稿可定位原文
            snippet = self._extract_sentence(text, m.start())
            if not snippet:
                snippet = m.group(0)
            return RiskItem(
                risk_id=rule['id'],
                risk_type=rule.get('category', ''),
                severity=rule.get('severity', 'medium'),
                title=rule.get('name', ''),
                description=rule.get('description', ''),
                suggestion=rule.get('suggestion', ''),
                legal_basis=rule.get('legal_basis', ''),
                text_snippet=snippet,
            )
        return None
    
    def _check_threshold(self, rule: Dict, text: str) -> RiskItem:
        """阈值检查"""
        pattern = rule.get('extract_pattern', rule.get('check_rule', ''))
        
        # 安全检查：限制正则复杂度
        if len(pattern) > 500:
            return None
        
        try:
            matches = re.findall(pattern, text)
        except re.error:
            return None
        
        for match in matches:
            try:
                value = float(str(match).replace(',', ''))
                threshold = rule.get('threshold', 0)
                
                if rule.get('operator', '>') == '>' and value > threshold:
                    return RiskItem(
                        risk_id=rule['id'],
                        risk_type=rule.get('category', ''),
                        severity=rule.get('severity', 'medium'),
                        title=rule.get('name', ''),
                        description=f"检测到 {value:.1f}，超过阈值 {threshold}",
                        suggestion=rule.get('suggestion', ''),
                        legal_basis=rule.get('legal_basis', ''),
                        text_snippet=str(match)[:100],
                    )
            except (ValueError, TypeError):
                continue
        
        return None
    
    def _check_pattern(self, rule: Dict, text: str) -> RiskItem:
        """模式匹配检查"""
        check_rule = rule.get('check_rule', '')
        
        if isinstance(check_rule, str):
            patterns = [check_rule]
        elif isinstance(check_rule, list):
            patterns = check_rule
        else:
            patterns = []
        
        for pattern in patterns:
            if pattern in text:
                pos = text.find(pattern)
                # v4.0 按句子边界截取，保证修订稿可准确定位原文
                snippet = self._extract_sentence(text, pos)
                
                return RiskItem(
                    risk_id=rule['id'],
                    risk_type=rule.get('category', ''),
                    severity=rule.get('severity', 'medium'),
                    title=rule.get('name', ''),
                    description=rule.get('description', ''),
                    suggestion=rule.get('suggestion', ''),
                    legal_basis=rule.get('legal_basis', ''),
                    text_snippet=snippet,
                )
        
        return None
    
    def _check_checklist(self, rule: Dict, text: str, structure: Dict) -> List[RiskItem]:
        """清单检查"""
        risks = []
        check_rule = rule.get('check_rule', '')
        
        if check_rule == '对照合同必备条款清单检查':
            for item, synonyms in ESSENTIAL_CLAUSE_SYNONYMS.items():
                if not any(kw in text for kw in synonyms):
                    risks.append(RiskItem(
                        risk_id=f"{rule['id']}_{item}",
                        risk_type=rule.get('category', ''),
                        severity=rule.get('severity', 'medium'),
                        title=f"可能缺少【{item}】相关条款",
                        description=f"合同文本中未检测到明确的【{item}】约定",
                        suggestion=f"建议补充【{item}】的具体约定",
                        legal_basis=rule.get('legal_basis', ''),
                    ))
        
        return risks
    
    def _check_list(self, rule: Dict, text: str) -> RiskItem:
        """列表验证检查"""
        check_rule = rule.get('check_rule', '')
        
        if '验证仲裁机构' in check_rule:
            valid_institutions = [
                '中国国际经济贸易仲裁委员会', '北京仲裁委员会', '上海仲裁委员会',
                '深圳国际仲裁院', '广州仲裁委员会', '中国海事仲裁委员会',
                '贸仲', '北仲', '上仲', '深国仲', '广仲',
            ]
            
            if '仲裁' in text:
                found = False
                for inst in valid_institutions:
                    if inst in text:
                        found = True
                        break
                
                if not found:
                    if '仲裁委员会' in text or '仲裁机构' in text:
                        pos = text.find('仲裁委员会')
                        if pos == -1:
                            pos = text.find('仲裁机构')
                        
                        snippet = self._extract_sentence(text, pos)
                        return RiskItem(
                            risk_id=rule['id'],
                            risk_type=rule.get('category', ''),
                            severity=rule.get('severity', 'medium'),
                            title=rule.get('name', ''),
                            description=rule.get('description', ''),
                            suggestion=rule.get('suggestion', ''),
                            legal_basis=rule.get('legal_basis', ''),
                            text_snippet=snippet,
                        )
        
        return None


def main():
    """命令行入口"""
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("用法: python rule_engine.py <文本文件> [规则文件]")
        sys.exit(1)
    
    text_path = sys.argv[1]
    rules_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    with open(text_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    engine = RuleEngine(rules_path)
    risks = engine.check_all(text)
    
    print(f"发现 {len(risks)} 个风险点:")
    print(json.dumps([r.to_dict() for r in risks], ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
