#!/usr/bin/env python3
"""
合同审核报告生成器 - Phase 3
功能：整合解析、识别、审核结果，生成结构化报告
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional

# 导入同目录下的模块（兼容脚本直接运行和包导入两种方式）
try:
    from .parse_contract import ContractParser
    from .classify_contract import ContractClassifier, main as classify_main
    from .risk_review import RiskReviewEngine, RiskLevel
except ImportError:
    from parse_contract import ContractParser
    from classify_contract import ContractClassifier, main as classify_main
    from risk_review import RiskReviewEngine, RiskLevel


# ============================================================
# 示范条款生成器
# ============================================================

MODEL_CLAUSES = {
    '管辖约定不明': {
        'concise': '凡因本合同引起的争议，协商不成的，任何一方均有权向甲方所在地有管辖权的人民法院提起诉讼。',
        'full': '1. 凡因本合同引起的或与本合同有关的任何争议，双方应首先友好协商解决。\n'
                '2. 协商不成的，任何一方均有权向甲方所在地有管辖权的人民法院提起诉讼。\n'
                '3. 违约方应承担守约方为实现债权而支出的全部费用，包括但不限于律师费、诉讼费、保全费、担保费、公证费、差旅费、调查取证费等。'
    },
    '不可抗力范围过宽': {
        'concise': '不可抗力指不能预见、不能避免并不能克服的客观情况，包括但不限于自然灾害、战争、政府行为、法律法规重大变更。',
        'full': '1. 不可抗力指不能预见、不能避免并不能克服的客观情况，包括但不限于自然灾害（地震、洪水、台风等）、战争或武装冲突、政府行为（征收、征用、禁运等）、法律法规重大变更。\n'
                '2. 遭受不可抗力的一方应在事件发生后48小时内书面通知对方，并在15日内提供相关证明文件。\n'
                '3. 因不可抗力导致合同无法履行的，受影响方部分或全部免除责任，但应及时采取减损措施。\n'
                '4. 任何一方不得将自身经营风险（如资金周转困难、原材料涨价、市场行情变化等）列为不可抗力。'
    },
    '法律依据过时': {
        'concise': '本合同的订立、效力、解释、履行及争议解决，均适用《中华人民共和国民法典》及相关法律法规。',
        'full': '1. 本合同的订立、效力、解释、履行及争议解决，均适用《中华人民共和国民法典》及相关法律法规。\n'
                '2. 原《中华人民共和国合同法》已于2021年1月1日废止，相应内容已并入《民法典》合同编。\n'
                '3. 合同条款中引用的法律法规如被修订或废止，应自动适用届时有效的最新版本。'
    },
    '付款节奏不利': {
        'concise': '甲方应在收到乙方开具的合法有效发票后30个工作日内支付相应款项。',
        'full': '1. 付款方式：【银行转账】，收款账户信息如下：户名___、开户行___、账号___。\n'
                '2. 乙方应在【节点描述】后3个工作日内向甲方开具合法有效的增值税专用发票。\n'
                '3. 甲方应在收到发票后30个工作日内支付。逾期支付的，每逾期一日按应付未付金额的万分之五支付逾期利息。\n'
                '4. 甲方逾期支付超过60日的，乙方有权暂停履行合同义务，且不视为违约。'
    },
    '违约金过低': {
        'concise': '任何一方违约的，应向守约方支付合同总金额20%的违约金；违约金不足以弥补损失的，违约方还应赔偿实际损失。',
        'full': '1. 任何一方不履行合同义务或履行不符合约定的，应向守约方支付合同总金额【20】%的违约金。\n'
                '2. 违约金不足以弥补守约方实际损失的，违约方还应赔偿差额部分，损失包括但不限于直接损失、预期利益损失。\n'
                '3. 守约方为实现债权而支出的全部费用（包括律师费、诉讼费、保全费、差旅费等）由违约方承担。\n'
                '4. 逾期履行超过【30】日的，守约方有权单方解除合同并要求违约方承担上述全部违约金及损失赔偿。'
    },
    '知识产权不明': {
        'concise': '乙方保证对其提供的全部素材拥有合法知识产权或已取得权利人完整授权，并列举具体授权清单作为附件。',
        'full': '1. 乙方保证对其提供的全部素材（包括但不限于文字、图片、音视频、字体、软件代码）拥有合法知识产权或已取得权利人完整授权。\n'
                '2. 授权清单作为合同附件，载明各素材的权利来源、授权期限、授权范围。\n'
                '3. 因乙方提供的素材侵犯第三方知识产权导致甲方遭受损失的，乙方应承担全部赔偿责任（包括甲方的商誉损失）。\n'
                '4. 发生第三方侵权主张时，乙方应自费应诉并承担全部赔偿，甲方已支付的费用应全额退还。'
    },
    '无验收条款': {
        'concise': '乙方交付工作成果后，甲方应在15个工作日内验收。验收不合格的，乙方应在收到通知后10个工作日内无偿修改，修改次数不超过3次。',
        'full': '1. 乙方交付工作成果后，甲方应在【15】个工作日内组织验收并出具书面验收意见。\n'
                '2. 验收标准以【附件约定的技术指标/行业标准/双方确认的样品】为准。\n'
                '3. 验收不合格的，乙方应在收到书面通知后【10】个工作日内无偿修改完善并重新提交。修改次数不超过【3】次。\n'
                '4. 修改后仍不合格的，甲方有权解除合同并要求乙方退还已付款项并赔偿损失。\n'
                '5. 甲方未在验收期限内出具书面意见的，视为验收通过。但甲方擅自使用未经验收成果的，视为验收合格。'
    },
    '无违约解约权': {
        'concise': '一方逾期履行超过30日的，守约方有权书面通知解除合同，并要求违约方承担违约责任。',
        'full': '1. 一方逾期履行超过【30】日，经守约方书面催告后【10】日内仍未履行的，守约方有权单方解除合同。\n'
                '2. 守约方解除合同的，自解除通知到达对方时合同解除。\n'
                '3. 合同解除后，违约方应在【15】日内返还已收取的全部款项，并按合同总金额【20】%支付违约金。\n'
                '4. 守约方保留向违约方主张实际损失赔偿的权利。'
    },
    '保密违约金低': {
        'concise': '违反保密义务的，应向守约方支付违约金人民币【】元或合同总金额【3】倍（以高者为准）的违约金，并赔偿实际损失。',
        'full': '1. 保密义务不因合同终止、解除或期满而失效，保密期限自合同终止后继续有效【5】年。\n'
                '2. 违反保密义务的，应向守约方支付违约金人民币【】元或合同总金额【3】倍（以高者为准）。\n'
                '3. 违约金不足以弥补守约方实际损失的，违约方还应赔偿差额部分，违约金条款不构成对损失赔偿责任的限制。\n'
                '4. 守约方还有权立即解除合同并要求违约方返还因泄密获取的全部利益。'
    },
    '争议解决': {
        'concise': '因本合同引起的争议，双方协商不成的，提交甲方所在地有管辖权的人民法院诉讼解决。',
        'full': '1. 因本合同引起的或与本合同有关的任何争议，双方应首先友好协商解决。\n'
                '2. 协商不成的，任何一方均有权向甲方所在地有管辖权的人民法院提起诉讼。\n'
                '3. 违约方应承担守约方为实现债权而支出的全部费用，包括但不限于律师费、诉讼费、保全费、担保费、公证费、差旅费、调查取证费等。'
    },
    # 通用 / 缺省
    '单方决定权条款': {
        'concise': '相关事项应由双方协商一致后确定，任何一方不得单方面决定。',
        'full': '相关事项应由双方协商一致后确定，并以书面形式确认。任何一方不得单方面决定或变更。如双方无法协商一致的，按以下方式处理：【约定处理机制】。'
    },
    '权利放弃条款': {
        'concise': '删除该条款，双方各自保留法律赋予的全部权利。',
        'full': '删除该条款。双方确认，本合同任何条款均不构成对任何一方依法享有的实体权利或程序权利的放弃或限制。'
    },
    '过高违约金/滞纳金': {
        'concise': '违约金不超过合同总金额的20%。',
        'full': '违约金约定为合同总金额的【20】%。违约金不足以弥补守约方实际损失的，违约方还应赔偿差额部分。该约定系双方经充分协商后的真实意思表示，不构成显失公平。'
    },
    '限制诉权条款': {
        'concise': '删除该条款。',
        'full': '删除该条款。双方确认，任何一方均有权依法向有管辖权的人民法院提起诉讼或申请仲裁，该权利不受本合同任何条款的限制。'
    },
    '付款账号不明确': {
        'concise': '付款至以下账户：户名___、开户行___、账号___。',
        'full': '付款至以下指定账户：（1）户名：___；（2）开户行：___；（3）账号：___。收款账户如需变更，收款方应提前【15】个工作日书面通知付款方，否则付款方向原账户付款即视为已履行付款义务。'
    },
    '模糊表述条款': {
        'concise': '将"合理/若干/适当"等模糊词汇替换为具体数字或标准。',
        'full': '建议将模糊词汇替换为具体数值或计算公式，例如：合理期限 → 【30】个工作日；适当调整 → 调整幅度不超过【10】%；必要时 → 满足以下条件之一时：【列举具体触发条件】。'
    },
    '不可抗力条款不完整': {
        'concise': '受不可抗力影响的一方应在48小时内书面通知对方，并在15日内提供证明。',
        'full': '1. 遭受不可抗力的一方应在事件发生后48小时内书面通知对方，说明事件情况和预计影响期限。\n2. 受影响方应在15日内提供有权机关出具的不可抗力证明文件。\n3. 双方应根据事件影响协商延期履行或解除合同的方案。'
    },
    '通知条款不完善': {
        'concise': '双方地址/联系方式变更的，应在变更后3个工作日内书面通知对方，否则原地址视为有效送达地址。',
        'full': '1. 本合同载明的地址、电话、电子邮箱均为有效送达方式。\n2. 一方地址或联系方式变更的，应在变更后3个工作日内书面通知对方。\n3. 未及时通知的，向原地址发出的通知视为已有效送达，由此产生的法律后果由变更方自行承担。\n4. 司法文书送达亦适用本条约定的地址。'
    },
    '争议解决条款缺失': {
        'concise': '因本合同引起的争议，双方协商不成的，提交甲方所在地有管辖权的人民法院诉讼解决。',
        'full': '1. 因本合同引起的或与本合同有关的任何争议，双方应首先友好协商解决。\n2. 协商不成的，任何一方均有权向【】所在地有管辖权的人民法院提起诉讼。\n3. 违约方应承担守约方为实现债权而支出的全部费用。'
    },
    '保密条款不完整': {
        'concise': '保密期限自合同终止后继续有效3年，保密范围包括但不限于【列举】。',
        'full': '1. 保密信息包括但不限于：【列举具体范围】。\n2. 保密义务自合同终止/解除后继续有效【5】年，法律法规另有规定的除外。\n3. 以下信息不受保密条款约束：（1）接收方在披露前已合法持有的；（2）非因接收方过错而公开的；（3）接收方从有权披露的第三方合法获取的。\n4. 违反保密义务的，应承担违约责任并赔偿损失。'
    },
}


def _match_model_clause_key(risk_title: str) -> str:
    """根据风险标题匹配示范条款（三层匹配：精确→包含→关键词交叉）"""
    for key in MODEL_CLAUSES:
        if key == risk_title:
            return key
    for key in MODEL_CLAUSES:
        if key in risk_title or risk_title in key:
            return key
    keyword_pairs = [
        ('管辖', '管辖'), ('违约金', '违约金'), ('违约', '违约'),
        ('付款', '付款'), ('不可抗力', '不可抗力'), ('验收', '验收'),
        ('知识产权', '知识产权'), ('保密', '保密'), ('通知', '通知'),
        ('争议', '争议'), ('单方', '单方'), ('放弃', '权利放弃'),
        ('模糊', '模糊'), ('诉权', '限制诉权'), ('账号', '付款'),
    ]
    for kw, target_kw in keyword_pairs:
        if kw in risk_title:
            for key in MODEL_CLAUSES:
                if target_kw in key:
                    return key
    return None


def generate_model_clause(risk_title: str) -> dict:
    """为风险条目生成简洁版 + 全面版示范条款"""
    key = _match_model_clause_key(risk_title)
    if key:
        return MODEL_CLAUSES[key]

    # 默认返回
    return {
        'concise': '建议根据具体情况进行修改，确保条款清晰、对等、合法。',
        'full': '建议参照相关法律法规和行业标准，对条款进行完整修订，明确双方权利义务、违约责任和争议解决方式。'
    }


# ============================================================


class ReportGenerator:
    """审核报告生成器"""
    
    def __init__(self, text: str, contract_type: str = None, style: str = 'markdown'):
        """
        初始化报告生成器
        
        Args:
            text: 合同文本内容
            contract_type: 可选的指定合同类型
            style: 输出格式 ('markdown' | 'docx' | 'json')
        """
        self.text = text
        self.contract_type = contract_type
        self.style = style
        
        # 执行各阶段分析
        self._run_analysis()
        
    def _run_analysis(self):
        """运行各阶段分析"""
        # Phase 0: 合同解析
        parser = ContractParser(self.text)
        self.parsed = parser.parse()
        
        # Phase 1: 类型识别
        classifier = ContractClassifier(self.text)
        if self.contract_type:
            self.classified = classify_main(self.text, self.contract_type)
        else:
            self.classified = classifier.classify()
            
        # Phase 2: 风险审核（使用指定类型或识别类型）
        detected_type = self.classified.get('contract_type')
        risk_engine = RiskReviewEngine(self.text, detected_type)
        self.reviewed = risk_engine.review()
        
    def generate(self) -> str:
        """
        生成报告
        
        Returns:
            格式化的报告文本
        """
        if self.style == 'json':
            return self._generate_json()
        elif self.style == 'docx':
            return self._generate_markdown()  # 暂返回Markdown，后续可转换为DOCX
        else:
            return self._generate_markdown()
    
    def _generate_markdown(self) -> str:
        """生成 Markdown 格式报告"""
        basic = self.parsed.get('basic_info', {})
        classified = self.classified
        summary = self.reviewed.get('summary', {})
        risks = self.reviewed.get('risks', {})
        
        # 标题
        report = f"""# 合同审核报告

**生成时间**：{datetime.now().strftime('%Y年%m月%d日 %H:%M')}  
**合同类型**：{classified.get('contract_type', '未识别')}  
**风险评分**：{self.reviewed.get('risk_score', 0):.0f}/100

---

## 一、审核结论

{summary.get('overall_assessment', '无法生成结论')}

| 风险等级 | 数量 |
|---------|------|
| 🔴 高风险 | {summary.get('high_risk_count', 0)} 项 |
| 🟡 中风险 | {summary.get('medium_risk_count', 0)} 项 |
| 🟢 低风险 | {summary.get('low_risk_count', 0)} 项 |

---

## 二、合同基本信息

| 字段 | 内容 |
|-----|------|
| 合同名称 | {basic.get('contract_name', '未明确')} |
| 甲方（委托方） | {basic.get('party_a', '未明确')} |
| 乙方（受托方） | {basic.get('party_b', '未明确')} |
| 签署日期 | {basic.get('signing_date', '未明确')} |
| 合同金额 | {basic.get('contract_amount', '未明确')} |

**类型识别置信度**：{classified.get('confidence', 0):.1f}  
{f'**类型指定来源**：用户指定' if classified.get('specified') else ''}

"""
        
        # 高风险条款
        high_risks = risks.get(RiskLevel.HIGH, [])
        if high_risks:
            report += self._format_risk_section('🔴 高风险条款（必须修改）', high_risks)
        
        # 中风险条款
        medium_risks = risks.get(RiskLevel.MEDIUM, [])
        if medium_risks:
            report += self._format_risk_section('🟡 中风险条款（建议修改）', medium_risks)
        
        # 低风险条款
        low_risks = risks.get(RiskLevel.LOW, [])
        if low_risks:
            report += self._format_risk_section('🟢 低风险条款（可保留参考）', low_risks)
        
        # 关键条款清单
        key_clauses = self.parsed.get('key_clauses', {})
        if key_clauses:
            report += """---

## 三、关键条款摘要

"""
            for clause_type, items in key_clauses.items():
                if items:
                    report += f"**{clause_type}**：\n"
                    for item in items:
                        report += f"- {item.get('content', '')[:100]}...\n"
                    report += "\n"
        
        # 缺失条款
        missing = [r for r in self.reviewed.get('all_items', []) if '缺少' in r.get('title', '')]
        if missing:
            report += """---

## 四、建议补充的条款

"""
            for item in missing:
                report += f"### {item['title']}\n"
                report += f"**建议**：{item['suggestion']}\n\n"
        
        # 合同结构分析
        structure = self.parsed.get('structure', [])
        if structure:
            report += f"""---

## 五、合同结构分析

| 序号 | 条款 | 内容摘要 |
|-----|------|---------|
"""
            for i, item in enumerate(structure[:15], 1):  # 最多显示15条
                title = item.get('title', '')
                content = item.get('content', '')[:40]
                report += f"| {i} | {title} | {content}... |\n"
        
        # 页脚
        report += f"""

---

*本报告由 WorkBuddy 合同审核 Skill 自动生成*  
*仅供参考，最终意见以执业律师判断为准*
"""
        
        return report
    
    def _format_risk_section(self, title: str, items: List[Dict]) -> str:
        """格式化风险章节（含示范条款）"""
        section = f"\n---\n\n## {title}\n\n"
        for i, item in enumerate(items, 1):
            section += f"### {i}. {item['title']}\n"
            section += f"- **风险类型**：{item['type']}\n"
            section += f"- **问题描述**：{item['description']}\n"
            section += f"- **位置**：{item['location']}\n"
            if item.get('reference'):
                section += f"- **参考依据**：{item['reference']}\n"

            # 生成示范条款
            model = generate_model_clause(item['title'])
            section += f"\n📝 **简洁版示范条款**：\n> {model['concise']}\n"
            section += f"\n📋 **全面版示范条款**：\n"
            for line in model['full'].split('\n'):
                if line.strip():
                    section += f"> {line}\n"

            section += "\n"
        return section
    
    def _generate_json(self) -> str:
        """生成 JSON 格式报告"""
        result = {
            'generated_at': datetime.now().isoformat(),
            'basic_info': self.parsed.get('basic_info', {}),
            'classification': {
                'contract_type': self.classified.get('contract_type'),
                'confidence': self.classified.get('confidence'),
                'specified': self.classified.get('specified', False),
                'ranking': self.classified.get('ranking', []),
            },
            'review': self.reviewed,
            'structure': self.parsed.get('structure', []),
            'key_clauses': self.parsed.get('key_clauses', {}),
            'statistics': self.parsed.get('statistics', {}),
        }
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    def save(self, output_path: str = None) -> str:
        """
        保存报告到文件
        
        Args:
            output_path: 输出文件路径（不含扩展名）
            
        Returns:
            保存的文件路径
        """
        if not output_path:
            # 使用默认路径
            base_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'outputs'
            )
            os.makedirs(base_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = os.path.join(base_dir, f'审核报告_{timestamp}')
        
        if self.style == 'json':
            file_path = f'{output_path}.json'
            content = self._generate_json()
        else:
            file_path = f'{output_path}.md'
            content = self._generate_markdown()
            
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        return file_path


def main(text: str, contract_type: str = None, style: str = 'markdown', 
         output_path: str = None) -> str:
    """
    主入口函数
    
    Args:
        text: 合同文本内容
        contract_type: 可选的指定合同类型
        style: 输出格式 ('markdown' | 'json')
        output_path: 可选的输出文件路径
        
    Returns:
        报告内容（字符串）
    """
    generator = ReportGenerator(text, contract_type, style)
    
    if output_path:
        saved_path = generator.save(output_path)
        print(f"报告已保存至: {saved_path}")
        
    return generator.generate()


# 如果作为独立脚本运行
if __name__ == '__main__':
    sample = """
    咨询服务合同
    
    合同编号：ZX-2024-001
    委托方（甲方）：大兴安岭农村商业银行股份有限公司
    受托方（乙方）：知恒律师事务所
    
    签署日期：2024年3月15日
    
    第一条 服务内容
    乙方为甲方提供二级资本债赎回相关法律咨询服务，包括但不限于：
    1. 法律尽职调查
    2. 合同审核与修订
    3. 出具法律意见书
    
    第二条 服务费用
    咨询服务费共计人民币50万元，甲方应于本合同签署后30日内支付。
    
    第三条 违约责任
    任何一方违约应承担相应法律责任。
    
    第四条 保密条款
    双方应对本合同内容保密，未经对方同意不得向第三方披露。
    
    第五条 争议解决
    因本合同产生的争议，双方应协商解决；协商不成的，提交北京仲裁委员会仲裁。
    """
    
    report = main(sample, '委托合同', 'markdown')
    print(report)
