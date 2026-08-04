#!/usr/bin/env python3
"""
模板引擎工具 - 用于生成合规文档模板
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

class TemplateEngine:
    """模板引擎工具类"""
    
    def __init__(self, templates_dir: str = None):
        """
        初始化模板引擎
        
        Args:
            templates_dir: 模板目录路径
        """
        if templates_dir:
            self.templates_dir = Path(templates_dir)
        else:
            # 默认模板目录
            self.templates_dir = Path(__file__).parent.parent.parent / 'assets' / 'templates'
        
        # 确保模板目录存在
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        # 预定义模板
        self._init_default_templates()
    
    def _init_default_templates(self):
        """初始化默认模板"""
        default_templates = {
            'privacy_policy_cn': self._get_privacy_policy_template(),
            'user_agreement_cn': self._get_user_agreement_template(),
            'data_processing_agreement_cn': self._get_dpa_template(),
            'consent_form_cn': self._get_consent_form_template(),
            'compliance_report': self._get_compliance_report_template()
        }
        
        # 保存默认模板到文件
        for name, content in default_templates.items():
            template_file = self.templates_dir / f"{name}.md"
            if not template_file.exists():
                template_file.write_text(content, encoding='utf-8')
    
    def _get_privacy_policy_template(self) -> str:
        """获取隐私政策模板"""
        return """# 隐私政策

## 一、总则

### 1.1 引言
{company_name}（以下简称"我们"）深知个人信息对您的重要性，并会尽全力保护您的个人信息安全可靠。我们致力于维持您对我们的信任，恪守以下原则，保护您的个人信息：权责一致原则、目的明确原则、选择同意原则、最少够用原则、确保安全原则、主体参与原则、公开透明原则。

### 1.2 适用范围
本隐私政策适用于我们通过网站、应用程序、小程序等提供的产品和服务。

## 二、我们如何收集和使用您的个人信息

### 2.1 收集的信息类型
我们仅会出于本政策所述的以下目的，收集和使用您的个人信息：

1. **注册信息**：当您注册账户时，我们会收集您的{user_info_fields}等信息。
2. **服务信息**：当您使用我们的服务时，我们会收集您的{service_info_fields}等信息。
3. **设备信息**：我们会收集您使用的设备信息，包括{device_info_fields}等。
4. **日志信息**：当您使用我们的服务时，我们会自动收集您的{log_info_fields}等信息。

### 2.2 信息使用目的
我们可能将收集的信息用于以下目的：

1. 提供、维护和改进我们的服务；
2. 开发新服务；
3. 提供个性化服务；
4. 向您发送重要通知；
5. 进行内部审计、数据分析和研究；
6. 防范欺诈和保障账户安全。

## 三、我们如何共享、转让、公开披露您的个人信息

### 3.1 共享
我们不会与任何公司、组织和个人分享您的个人信息，但以下情况除外：

1. 在获取明确同意的情况下共享；
2. 根据法律法规规定或政府部门的强制性要求；
3. 与授权合作伙伴共享：仅为实现本政策中声明的目的，我们的某些服务将由授权合作伙伴提供。

### 3.2 转让
我们不会将您的个人信息转让给任何公司、组织和个人，但以下情况除外：

1. 在获取明确同意的情况下转让；
2. 在涉及合并、收购或破产清算时，如涉及到个人信息转让，我们会要求新的持有您个人信息的公司、组织继续受此隐私政策的约束。

### 3.3 公开披露
我们仅会在以下情况下，公开披露您的个人信息：

1. 获得您明确同意后；
2. 基于法律的披露：在法律、法律程序、诉讼或政府主管部门强制性要求的情况下。

## 四、我们如何保护您的个人信息

### 4.1 安全措施
我们已使用符合业界标准的安全防护措施保护您提供的个人信息，防止数据遭到未经授权访问、公开披露、使用、修改、损坏或丢失。

### 4.2 安全体系
我们建立了专门的管理制度、流程和组织确保信息安全。

### 4.3 信息安全事件
在不幸发生个人信息安全事件后，我们将按照法律法规的要求，及时向您告知：安全事件的基本情况和可能的影响、我们已采取或将要采取的处置措施、您可自主防范和降低风险的建议、对您的补救措施等。

## 五、您的权利

按照中国相关的法律、法规、标准，以及其他国家、地区的通行做法，我们保障您对自己的个人信息行使以下权利：

### 5.1 访问您的个人信息
您有权访问您的个人信息，法律法规规定的例外情况除外。

### 5.2 更正您的个人信息
当您发现我们处理的关于您的个人信息有错误时，您有权要求我们作出更正。

### 5.3 删除您的个人信息
在以下情形中，您可以向我们提出删除个人信息的请求。

### 5.4 改变您授权同意的范围
每个业务功能需要一些基本的个人信息才能得以完成。对于额外收集的个人信息的收集和使用，您可以随时给予或收回您的授权同意。

### 5.5 个人信息主体注销账户
您随时可注销此前注册的账户。

### 5.6 约束信息系统自动决策
在某些业务功能中，我们可能仅依据信息系统、算法等在内的非人工自动决策机制做出决定。

### 5.7 响应您的上述请求
为保障安全，您可能需要提供书面请求，或以其他方式证明您的身份。

## 六、我们如何处理儿童的个人信息

我们的产品、网站和服务主要面向成人。如果没有父母或监护人的同意，儿童不得创建自己的用户账户。

## 七、您的个人信息如何在全球范围转移

我们在中华人民共和国境内运营中收集和产生的个人信息，存储在中国境内，以下情形除外：

1. 法律法规有明确规定；
2. 获得您的明确授权；
3. 您通过互联网进行跨境交易等个人主动行为。

## 八、本隐私政策如何更新

我们的隐私政策可能变更。

## 九、如何联系我们

如果您对本隐私政策有任何疑问、意见或建议，通过以下方式与我们联系：{contact_info}。

**生效日期**：{effective_date}
**更新日期**：{update_date}
"""
    
    def _get_user_agreement_template(self) -> str:
        """获取用户协议模板"""
        return """# 用户协议

## 一、协议的范围

### 1.1 协议适用主体范围
本协议是您与{company_name}之间关于您使用{product_name}产品及相关服务所订立的协议。

### 1.2 协议关系及冲突条款
本协议内容同时包括我们可能不断发布的关于本服务的相关协议、业务规则等内容。

## 二、关于本服务

### 2.1 本服务的内容
本服务内容是指我们向用户提供的{service_description}。

### 2.2 本服务的形式
您使用本服务需要下载{product_name}客户端软件。

### 2.3 本服务许可的范围
我们给予您一项个人的、不可转让及非排他性的许可，以使用本服务。

## 三、账号的注册与使用

### 3.1 用户资格
您确认，在您开始注册程序使用本服务前，您应当具备中华人民共和国法律规定的与您行为相适应的民事行为能力。

### 3.2 账号说明
您完成注册程序后，依据法律规定，您应保管好您的账号及密码。

### 3.3 注册信息
您在注册账号时承诺遵守法律法规、社会主义制度、国家利益、公民合法权益、公共秩序、社会道德风尚和信息真实性等七条底线。

## 四、个人隐私信息保护

### 4.1 保护用户个人信息是我们的一项基本原则
我们将按照本协议及《隐私政策》的规定收集、使用、储存和分享您的个人信息。

### 4.2 您应对通过本服务了解、接收或可接触到的包括但不限于其他用户在内的任何人的个人信息予以充分尊重。

## 五、使用本服务的方式

### 5.1 使用方式
除非您与我们另有约定，您同意本服务仅为您个人非商业性质的使用。

### 5.2 行为规范
您在使用本服务时须遵守法律法规，不得利用本服务从事违法违规行为。

## 六、按现状提供服务

您理解并同意，我们的服务是按照现有技术和条件所能达到的现状提供的。

## 七、免责声明

### 7.1 我们不担保以下事项：
1. 本服务将完全符合您的要求；
2. 本服务将不受干扰、及时提供、安全可靠或不会出错。

### 7.2 在任何情况下，我们均不对任何间接性、后果性、惩罚性、偶然性、特殊性或刑罚性的损害承担责任。

## 八、协议变更

我们有权在必要时修改本协议条款。

## 九、通知送达

本协议项下我们对于您所有的通知均可通过网页公告、电子邮件、手机短信或常规的信件传送等方式进行。

## 十、法律管辖

本协议的订立、执行和解释及争议的解决均应适用中华人民共和国大陆地区法律。

## 十一、其他规定

本协议构成双方对本协议之约定事项及其他有关事宜的完整协议。

**生效日期**：{effective_date}
"""
    
    def _get_dpa_template(self) -> str:
        """获取数据处理协议模板"""
        return """# 数据处理协议

## 一、定义

### 1.1 个人信息
指以电子或者其他方式记录的能够单独或者与其他信息结合识别特定自然人身份或者反映特定自然人活动情况的各种信息。

### 1.2 数据处理
指对个人信息进行的任何操作或者一系列操作。

### 1.3 数据控制者
指决定个人信息处理目的和方式的组织或个人。

### 1.4 数据处理者
指代表数据控制者处理个人信息的组织或个人。

## 二、协议目的

本协议旨在明确数据控制者（以下简称"甲方"）与数据处理者（以下简称"乙方"）之间关于个人信息处理的权责关系。

## 三、数据处理范围

### 3.1 处理目的
乙方仅可为以下目的处理甲方委托的个人信息：{processing_purposes}。

### 3.2 处理类型
乙方可进行的处理类型包括：{processing_types}。

### 3.3 数据类别
本协议涵盖的个人信息类别包括：{data_categories}。

## 四、双方义务

### 4.1 甲方义务
1. 确保个人信息的合法性来源；
2. 明确处理目的和方式；
3. 取得个人信息主体的同意；
4. 对乙方进行必要监督。

### 4.2 乙方义务
1. 按照甲方指示处理个人信息；
2. 采取适当安全措施；
3. 协助甲方履行法定义务；
4. 处理结束后删除或返还个人信息。

## 五、安全保障

### 5.1 安全措施
乙方应采取与处理风险相适应的技术和管理措施，确保个人信息安全。

### 5.2 安全事件
发生安全事件时，乙方应立即通知甲方并采取补救措施。

## 六、监督审计

### 6.1 监督权利
甲方有权对乙方的处理活动进行监督。

### 6.2 审计权利
甲方有权委托第三方对乙方进行审计。

## 七、违约责任

任何一方违反本协议约定，应承担相应的法律责任。

## 八、协议期限

本协议有效期自{effective_date}起至{expiry_date}止。

## 九、法律适用

本协议适用中华人民共和国法律。

**甲方（数据控制者）**：{controller_name}
**乙方（数据处理者）**：{processor_name}
**签署日期**：{sign_date}
"""
    
    def _get_consent_form_template(self) -> str:
        """获取同意书模板"""
        return """# 个人信息处理同意书

## 致：{company_name}

本人（以下简称"本人"）已仔细阅读并充分理解{company_name}的《隐私政策》和本同意书内容，现就{company_name}处理本人个人信息事宜作出如下同意：

## 一、同意内容

### 1.1 同意范围
本人同意{company_name}基于以下目的处理本人的个人信息：{processing_purposes}。

### 1.2 处理方式
本人同意{company_name}通过以下方式处理本人的个人信息：{processing_methods}。

### 1.3 信息类别
本人同意{company_name}处理的个人信息类别包括：{personal_info_categories}。

## 二、特别同意

### 2.1 敏感信息
本人{consent_for_sensitive_info}同意{company_name}处理本人的敏感个人信息。

### 2.2 跨境传输
本人{consent_for_cross_border}同意{company_name}将本人的个人信息传输至境外。

### 2.3 自动化决策
本人{consent_for_automation}同意{company_name}基于自动化决策机制处理本人的个人信息。

## 三、权利告知

本人知晓并理解，根据《中华人民共和国个人信息保护法》的规定，本人享有以下权利：

1. 知情权和决定权；
2. 限制或者拒绝他人对其个人信息进行处理；
3. 查阅、复制其个人信息；
4. 请求更正、补充其个人信息；
5. 请求删除其个人信息；
6. 请求解释个人信息处理规则。

## 四、撤回同意

本人知晓并理解，本人有权随时撤回本同意。撤回同意不影响撤回前基于本人同意已进行的个人信息处理活动的效力。

## 五、其他

本同意书自本人签署之日起生效。

**个人信息主体**：{user_name}
**身份证号码**：{id_card}
**联系方式**：{contact_info}
**签署日期**：{sign_date}
"""
    
    def _get_compliance_report_template(self) -> str:
        """获取合规报告模板"""
        return """# PIPL合规自查报告

## 报告信息

**报告编号**：{report_id}
**企业名称**：{company_name}
**检查日期**：{check_date}
**报告生成日期**：{report_date}
**检查人员**：{auditor}

## 一、执行摘要

### 1.1 总体合规情况
本次合规检查总体得分：{overall_score}/100分
合规等级：{compliance_level}

### 1.2 关键发现
{key_findings}

### 1.3 改进建议
{improvement_suggestions}

## 二、详细检查结果

### 2.1 合规要求检查
| 检查项 | 要求描述 | 检查结果 | 得分 | 备注 |
|--------|----------|----------|------|------|
{table_content}

### 2.2 风险评估
**总体风险等级**：{overall_risk_level}
**高风险项数量**：{high_risk_count}
**中风险项数量**：{medium_risk_count}
**低风险项数量**：{low_risk_count}

## 三、改进计划

### 3.1 优先级排序
{priority_plan}

### 3.2 实施时间表
{implementation_timeline}

## 四、结论

本次合规检查表明，{company_name}在PIPL合规方面{conclusion_summary}。

建议按照本报告提出的改进计划，持续完善个人信息保护体系。

**报告审核人**：{reviewer}
**报告批准人**：{approver}
"""
    
    def generate_document(self, template_name: str, variables: Dict[str, Any]) -> str:
        """
        生成文档
        
        Args:
            template_name: 模板名称
            variables: 模板变量
        
        Returns:
            str: 生成的文档内容
        """
        # 加载模板
        template_content = self.load_template(template_name)
        if not template_content:
            raise ValueError(f"模板 '{template_name}' 不存在")
        
        # 添加默认变量
        default_variables = {
            'effective_date': datetime.now().strftime('%Y年%m月%d日'),
            'update_date': datetime.now().strftime('%Y年%m月%d日'),
            'report_date': datetime.now().strftime('%Y年%m月%d日'),
            'check_date': datetime.now().strftime('%Y年%m月%d日'),
            'sign_date': datetime.now().strftime('%Y年%m月%d日')
        }
        
        # 合并变量
        all_variables = {**default_variables, **variables}
        
        # 替换模板变量
        result = template_content
        for key, value in all_variables.items():
            placeholder = '{' + key + '}'
            result = result.replace(placeholder, str(value))
        
        return result
    
    def load_template(self, template_name: str) -> Optional[str]:
        """
        加载模板
        
        Args:
            template_name: 模板名称
        
        Returns:
            Optional[str]: 模板内容，如果不存在则返回None
        """
        # 首先检查文件
        template_file = self.templates_dir / f"{template_name}.md"
        if template_file.exists():
            return template_file.read_text(encoding='utf-8')
        
        # 检查内置模板
        builtin_templates = {
            'privacy_policy_cn': self._get_privacy_policy_template(),
            'user_agreement_cn': self._get_user_agreement_template(),
            'data_processing_agreement_cn': self._get_dpa_template(),
            'consent_form_cn': self._get_consent_form_template(),
            'compliance_report': self._get_compliance_report_template()
        }
        
        return builtin_templates.get(template_name)
    
    def save_document(self, content: str, output_path: str, filename: str = None):
        """
        保存文档
        
        Args:
            content: 文档内容
            output_path: 输出路径
            filename: 文件名（可选）
        """
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if not filename:
            filename = f"document_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        output_file = output_dir / filename
        output_file.write_text(content, encoding='utf-8')
        
        return str(output_file)

# 使用示例
if __name__ == "__main__":
    engine = TemplateEngine()
    
    # 生成隐私政策
    variables = {
        'company_name': '示例科技有限公司',
        'user_info_fields': '姓名、手机号码、电子邮箱',
        'service_info_fields': '服务使用记录、交易信息',
        'device_info_fields': '设备型号、操作系统版本',
        'log_info_fields': 'IP地址、浏览器类型',
        'contact_info': 'service@example.com',
        'update_date': '2024年1月1日'
    }
    
    privacy_policy = engine.generate_document('privacy_policy_cn', variables)
    print("生成的隐私政策前500字符:")
    print(privacy_policy[:500])
    print("...")
    
    # 保存文档
    saved_path = engine.save_document(privacy_policy, './output', 'privacy_policy.md')
    print(f"\n文档已保存到: {saved_path}")
