#!/usr/bin/env python3
"""
合同类型识别脚本 - Phase 1
功能：根据合同内容自动识别《民法典》19种合同类型
"""

import os
import re
from typing import Dict, List, Optional, Tuple

# 《民法典》合同类型定义
CONTRACT_TYPES = {
    '买卖合同': {
        'keywords': ['买卖', '购买', '销售', '出售', '买受', '标的物', '交付', '所有权转移', '货款'],
        'template_dir': '买卖合同',
    },
    '供用电、水、气、热力合同': {
        'keywords': ['供电', '供水', '供气', '供热', '电费', '水费', '燃气', '热力', '用量'],
        'template_dir': '供用水电气热力合同',
    },
    '赠与合同': {
        'keywords': ['赠与', '捐赠', '无偿转让', '受赠', '赠与人', '受赠人'],
        'template_dir': '赠与合同',
    },
    '借款合同': {
        'keywords': ['借款', '贷款', '本金', '利息', '利率', '借款人', '贷款人', '偿还', '还款'],
        'template_dir': '借款合同',
    },
    '保证合同': {
        'keywords': ['保证', '担保', '保证人', '债权人', '债务人', '连带责任', '一般保证'],
        'template_dir': '保证合同',
    },
    '租赁合同': {
        'keywords': ['租赁', '出租', '承租', '租金', '租赁物', '使用权', '租用'],
        'template_dir': '租赁合同',
    },
    '融资租赁合同': {
        'keywords': ['融资租赁', '出租人', '承租人', '出卖人', '租赁物', '融资', '租金'],
        'template_dir': '融资租赁合同',
    },
    '保理合同': {
        'keywords': ['保理', '应收账款', '债权人转让', '应收账款融资', '买方', '卖方'],
        'template_dir': '保理合同',
    },
    '委托合同': {
        'keywords': ['委托', '受托', '委托方', '受托方', '代理', '委托人', '受托人', '处理'],
        'template_dir': '委托合同',
    },
    '物业服务合同': {
        'keywords': ['物业', '物业管理', '业主', '物业费', '服务费', '维修', '保洁', '保安'],
        'template_dir': '物业服务合同',
    },
    '行纪合同': {
        'keywords': ['行纪', '行纪人', '委托人', '第三人', '代购', '代销', '信托'],
        'template_dir': '行纪合同',
    },
    '中介合同': {
        'keywords': ['中介', '居间', '介绍', '促成', '报酬', '佣金', '居间人', '委托人'],
        'template_dir': '中介合同',
    },
    '保管合同': {
        'keywords': ['保管', '寄存', '保管人', '寄存人', '保管费', '物品', '丢失', '损毁'],
        'template_dir': '保管合同',
    },
    '仓储合同': {
        'keywords': ['仓储', '保管', '存货', '仓储费', '仓库', '入库', '出库', '保管人'],
        'template_dir': '仓储合同',
    },
    '建设工程合同': {
        'keywords': ['建设', '工程', '施工', '承包', '分包', '勘察', '设计', '监理', '工期', '竣工'],
        'template_dir': '建设工程合同',
    },
    '运输合同': {
        'keywords': ['运输', '承运', '旅客', '货物', '托运', '运费', '客运', '货运'],
        'template_dir': '运输合同',
    },
    '技术合同': {
        'keywords': ['技术', '开发', '转让', '许可', '咨询', '服务', '知识产权', '成果'],
        'template_dir': '技术合同',
    },
    '知识产权合同': {
        'keywords': ['知识产权', '专利', '商标', '著作权', '版权', '许可使用', '转让', '授权'],
        'template_dir': '知识产权合同',
    },
    '肖像许可使用合同': {
        'keywords': ['肖像', '肖像权', '使用', '授权', '形象', '姓名权', '明星'],
        'template_dir': '肖像许可使用合同',
    },
    '土地承包经营合同': {
        'keywords': ['土地', '承包', '经营权', '农村', '集体', '农户', '农业', '耕地'],
        'template_dir': '土地承包经营合同',
    },
    '合伙合同': {
        'keywords': ['合伙', '合伙人', '出资', '利润分配', '亏损分担', '入伙', '退伙'],
        'template_dir': '合伙合同',
    },
    # v1.6 新增：新媒体/营销推广类合同
    '新媒体推广合同': {
        'keywords': ['新媒体', '推广', '营销', '公众号', '短视频', '直播', '达人', '种草', '品宣'],
        'template_dir': '买卖合同',  # 暂用买卖合同的模板目录结构
    },
    'KOL合作合同': {
        'keywords': ['KOL', '博主', '达人', '网红', '种草', '带货', '佣金', '坑位费', '推广'],
        'template_dir': '买卖合同',
    },
    '媒体投放合同': {
        'keywords': ['媒体投放', '广告投放', '投放', '曝光', '展示', 'CPM', 'CPC', 'CPA', '流量'],
        'template_dir': '买卖合同',
    },
}


class ContractClassifier:
    """合同类型识别器"""
    
    def __init__(self, text: str, template_base: str = None):
        """
        初始化识别器
        
        Args:
            text: 合同文本内容
            template_base: 合同库根目录路径
        """
        self.text = text
        self.text_lower = text.lower()
        self.template_base = template_base or self._get_default_template_base()
        
    def _get_default_template_base(self) -> str:
        """获取默认模板库路径"""
        skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(skill_dir, 'references', 'template-library')
    
    def classify(self) -> Dict:
        """
        执行类型识别
        
        Returns:
            包含识别结果和详细分析的字典
        """
        # 计算每个类型的匹配度
        scores = self._calculate_scores()
        
        # 获取排名
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # 最佳匹配
        best_match = ranked[0] if ranked else (None, 0)
        
        return {
            'contract_type': best_match[0],
            'confidence': best_match[1],
            'ranking': ranked[:5],  # 前5个候选
            'analysis': self._analyze_features(),
        }
    
    def _calculate_scores(self) -> Dict[str, float]:
        """计算每个合同类型的匹配度"""
        scores = {}
        
        for contract_type, config in CONTRACT_TYPES.items():
            score = 0
            keywords = config['keywords']
            
            for keyword in keywords:
                # 关键词出现次数
                count = self.text_lower.count(keyword.lower())
                if count > 0:
                    # 基础分 + 次数加成
                    score += 1 + (count - 1) * 0.5
                    
            # 检查是否有对应模板
            template_path = os.path.join(
                self.template_base, 
                config['template_dir']
            )
            if os.path.exists(template_path):
                score += 2  # 有模板加分
                
            scores[contract_type] = score
            
        return scores
    
    def _analyze_features(self) -> Dict:
        """分析合同特征"""
        return {
            'length': len(self.text),
            'has_money': bool(re.search(r'[¥￥]\s*[\d,]+', self.text)),
            'has_date': bool(re.search(r'\d{4}年\d{1,2}月\d{1,2}日', self.text)),
            'has_parties': len(re.findall(r'[甲乙丙丁戊己庚辛壬癸][^方:：]', self.text)),
            'possible_subtypes': self._detect_subtypes(),
        }
    
    def _detect_subtypes(self) -> List[str]:
        """检测可能的子类型"""
        subtypes = []
        
        if '银行' in self.text or '金融' in self.text:
            subtypes.append('金融类')
        if '跨境' in self.text or '境外' in self.text:
            subtypes.append('跨境')
        if any(x in self.text for x in ['有限公司', '股份公司', '上市公司']):
            subtypes.append('企业主体')
        if any(x in self.text for x in ['个人', '自然人']):
            subtypes.append('个人主体')
            
        return subtypes
    
    def get_template_path(self, contract_type: str = None) -> Optional[str]:
        """
        获取指定合同类型的模板路径
        
        Args:
            contract_type: 合同类型（为空时使用识别结果）
            
        Returns:
            标准模板文件路径
        """
        if not contract_type:
            result = self.classify()
            contract_type = result['contract_type']
            
        config = CONTRACT_TYPES.get(contract_type, {})
        template_dir = config.get('template_dir', contract_type)
        
        template_path = os.path.join(
            self.template_base,
            template_dir,
            '_标准模板.md'
        )
        
        if os.path.exists(template_path):
            return template_path
        return None


def main(text: str, contract_type: str = None) -> Dict:
    """
    主入口函数
    
    Args:
        text: 合同文本内容
        contract_type: 可选，指定合同类型（跳过识别步骤）
        
    Returns:
        识别结果字典
    """
    classifier = ContractClassifier(text)
    
    if contract_type and contract_type in CONTRACT_TYPES:
        return {
            'contract_type': contract_type,
            'confidence': 1.0,
            'specified': True,
            'template_path': classifier.get_template_path(contract_type),
        }
    
    result = classifier.classify()
    result['template_path'] = classifier.get_template_path()
    return result


if __name__ == '__main__':
    # 测试
    sample = """
    咨询服务合同
    
    甲方（委托方）：大兴安岭农村商业银行
    乙方（受托方）：知恒律师事务所
    
    一、服务内容
    乙方为甲方提供金融法律咨询服务。
    
    二、服务费用
    咨询服务费共计人民币100万元。
    
    三、违约责任
    双方应严格履行合同义务。
    """
    
    result = main(sample)
    import json
    print(json.dumps(result, ensure_ascii=False, indent=2))
