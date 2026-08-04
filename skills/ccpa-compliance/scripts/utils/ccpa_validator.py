#!/usr/bin/env python3
"""
CCPA数据验证工具
提供CCPA/CPRA合规性检查的验证函数
"""

import json
import datetime
from typing import Dict, List, Any, Optional, Tuple


class CCPAValidator:
    """CCPA数据验证器"""
    
    @staticmethod
    def check_business_applicability(business_info: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        检查企业是否适用CCPA
        
        Args:
            business_info: 企业信息
            
        Returns:
            Tuple[是否适用CCPA, 适用原因列表]
        """
        applicable = False
        reasons = []
        
        # CCPA适用条件 (根据AB-375)
        # 1. 年收入超过$2500万
        if business_info.get('annual_revenue', 0) > 25000000:
            applicable = True
            reasons.append("年收入超过$2500万")
        
        # 2. 每年购买、接收、销售或共享超过50,000名消费者的个人信息
        if business_info.get('consumer_data_volume', 0) > 50000:
            applicable = True
            reasons.append("处理超过50,000名消费者数据")
        
        # 3. 年收入的50%以上来自销售消费者个人信息
        if business_info.get('revenue_from_data_sales', 0) > 0.5 * business_info.get('annual_revenue', 0):
            applicable = True
            reasons.append("年收入50%以上来自数据销售")
        
        # CPRA新增条件 (2023年生效)
        # 4. 处理超过100,000名消费者的个人信息
        if business_info.get('consumer_data_volume', 0) > 100000:
            applicable = True
            reasons.append("处理超过100,000名消费者数据 (CPRA要求)")
        
        # 5. 处理敏感个人信息
        if business_info.get('processes_sensitive_pi', False):
            applicable = True
            reasons.append("处理敏感个人信息")
        
        return applicable, reasons
    
    @staticmethod
    def validate_consumer_rights(rights_implementation: Dict[str, Any]) -> Tuple[bool, Dict[str, List[str]]]:
        """
        验证消费者权利实现情况
        
        Args:
            rights_implementation: 权利实现信息
            
        Returns:
            Tuple[是否完整实现, {权利类型: 缺失项列表}]
        """
        required_rights = {
            'right_to_know': [
                'privacy_notice',  # 隐私通知
                'data_collection_disclosure',  # 数据收集披露
                'data_use_disclosure',  # 数据使用披露
                'data_sharing_disclosure',  # 数据共享披露
                'verifiable_request_mechanism',  # 可验证请求机制
                'response_timeline_45_days'  # 45天响应时间
            ],
            'right_to_delete': [
                'deletion_request_mechanism',  # 删除请求机制
                'verification_process',  # 验证流程
                'exceptions_handling',  # 例外情况处理
                'confirmation_of_deletion'  # 删除确认
            ],
            'right_to_opt_out': [
                'do_not_sell_link',  # "请勿销售"链接
                'clear_opt_out_mechanism',  # 清晰的选择退出机制
                'no_requirement_for_account',  # 不要求创建账户
                'global_opt_out_support'  # 支持全局选择退出
            ],
            'right_to_non_discrimination': [
                'equal_service_policy',  # 平等服务政策
                'no_penalty_for_exercising_rights',  # 不因行使权利而惩罚
                'financial_incentive_disclosure'  # 财务激励披露
            ],
            'right_to_correct': [  # CPRA新增权利
                'correction_request_mechanism',  # 更正请求机制
                'verification_process',  # 验证流程
                'reasonable_effort_requirement'  # 合理努力要求
            ],
            'right_to_limit': [  # CPRA新增权利
                'sensitive_pi_use_limitation',  # 敏感个人信息使用限制
                'opt_out_mechanism_for_sensitive_pi'  # 敏感个人信息选择退出机制
            ]
        }
        
        missing_items = {}
        all_implemented = True
        
        for right_type, requirements in required_rights.items():
            missing = []
            for requirement in requirements:
                if not rights_implementation.get(requirement, False):
                    missing.append(requirement)
            
            if missing:
                missing_items[right_type] = missing
                all_implemented = False
        
        return all_implemented, missing_items
    
    @staticmethod
    def validate_personal_information_categories(categories: List[str]) -> Tuple[bool, List[str], List[str]]:
        """
        验证个人信息类别
        
        Args:
            categories: 处理的个人信息类别列表
            
        Returns:
            Tuple[是否完整识别, 缺失的类别, 敏感个人信息类别]
        """
        # CCPA定义的个人信息类别
        pi_categories = [
            'identifiers',  # 标识符
            'contact_information',  # 联系信息
            'financial_information',  # 财务信息
            'commercial_information',  # 商业信息
            'biometric_information',  # 生物识别信息
            'internet_activity',  # 互联网活动
            'geolocation_data',  # 地理位置数据
            'sensory_data',  # 感官数据
            'professional_information',  # 专业信息
            'education_information',  # 教育信息
            'inferences'  # 推断信息
        ]
        
        # CPRA新增的敏感个人信息类别
        sensitive_pi_categories = [
            'social_security_number',  # 社会安全号码
            'driver_license_number',  # 驾照号码
            'state_id_number',  # 州身份证号码
            'passport_number',  # 护照号码
            'account_login',  # 账户登录信息
            'financial_account_number',  # 金融账户号码
            'credit_card_number',  # 信用卡号码
            'debit_card_number',  # 借记卡号码
            'security_code',  # 安全码
            'password',  # 密码
            'precise_geolocation',  # 精确地理位置
            'racial_ethnic_origin',  # 种族或民族出身
            'religious_beliefs',  # 宗教信仰
            'union_membership',  # 工会会员身份
            'genetic_data',  # 基因数据
            'biometric_data_for_id',  # 身份识别用生物识别数据
            'health_information',  # 健康信息
            'sex_life_sexual_orientation'  # 性生活或性取向
        ]
        
        # 检查缺失的类别
        missing_categories = []
        for category in pi_categories:
            if category not in categories:
                missing_categories.append(category)
        
        # 识别敏感个人信息
        found_sensitive_pi = []
        for category in categories:
            if category in sensitive_pi_categories:
                found_sensitive_pi.append(category)
        
        is_complete = len(missing_categories) == 0
        return is_complete, missing_categories, found_sensitive_pi
    
    @staticmethod
    def check_data_sale_requirements(data_sale_info: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        检查数据销售要求
        
        Args:
            data_sale_info: 数据销售信息
            
        Returns:
            Tuple[是否合规, 不合规项列表]
        """
        compliant = True
        violations = []
        
        # 1. "请勿销售"链接要求
        if not data_sale_info.get('has_do_not_sell_link', False):
            compliant = False
            violations.append("缺少'请勿销售我的个人信息'链接")
        
        # 2. 选择退出机制要求
        if not data_sale_info.get('has_clear_opt_out_mechanism', False):
            compliant = False
            violations.append("缺少清晰的选择退出机制")
        
        # 3. 不要求创建账户
        if data_sale_info.get('requires_account_for_opt_out', False):
            compliant = False
            violations.append("选择退出要求创建账户（违反CCPA）")
        
        # 4. 全局选择退出支持
        if not data_sale_info.get('supports_global_opt_out', False):
            compliant = False
            violations.append("不支持全局选择退出")
        
        # 5. 13岁以下儿童特殊要求
        if data_sale_info.get('sells_children_data', False):
            if not data_sale_info.get('has_parental_consent_mechanism', False):
                compliant = False
                violations.append("销售13岁以下儿童数据但缺少家长同意机制")
        
        # 6. 16-17岁青少年要求 (CPRA)
        if data_sale_info.get('sells_teen_data', False):
            if not data_sale_info.get('has_teen_opt_in_mechanism', False):
                compliant = False
                violations.append("销售16-17岁青少年数据但缺少选择加入机制")
        
        # 7. 第三方披露要求
        if not data_sale_info.get('discloses_third_parties', False):
            compliant = False
            violations.append("未向消费者披露第三方接收方")
        
        return compliant, violations
    
    @staticmethod
    def validate_service_provider_agreements(agreements: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """
        验证服务提供商协议
        
        Args:
            agreements: 服务提供商协议列表
            
        Returns:
            Tuple[是否合规, 不合规项列表]
        """
        compliant = True
        violations = []
        
        for agreement in agreements:
            # 1. 书面合同要求
            if not agreement.get('is_written_contract', False):
                compliant = False
                violations.append(f"与 {agreement.get('provider_name', '未知提供商')} 的协议不是书面合同")
            
            # 2. 禁止销售数据
            if agreement.get('allows_data_resale', False):
                compliant = False
                violations.append(f"与 {agreement.get('provider_name', '未知提供商')} 的协议允许数据转售")
            
            # 3. 使用限制
            if not agreement.get('limits_use_to_contract_purpose', False):
                compliant = False
                violations.append(f"与 {agreement.get('provider_name', '未知提供商')} 的协议未限制使用目的")
            
            # 4. 安全要求
            if not agreement.get('requires_reasonable_security', False):
                compliant = False
                violations.append(f"与 {agreement.get('provider_name', '未知提供商')} 的协议缺少合理安全要求")
            
            # 5. 删除要求
            if not agreement.get('requires_deletion_upon_request', False):
                compliant = False
                violations.append(f"与 {agreement.get('provider_name', '未知提供商')} 的协议缺少删除要求")
        
        return compliant, violations
    
    @staticmethod
    def check_verifiable_consumer_requests(process_info: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        检查可验证消费者请求流程
        
        Args:
            process_info: 请求流程信息
            
        Returns:
            Tuple[是否合规, 不合规项列表]
        """
        compliant = True
        violations = []
        
        # 1. 验证机制
        if not process_info.get('has_verification_process', False):
            compliant = False
            violations.append("缺少可验证消费者请求的验证机制")
        
        # 2. 响应时间
        if process_info.get('response_time_days', 0) > 45:
            compliant = False
            violations.append(f"响应时间 {process_info.get('response_time_days', 0)} 天超过45天限制")
        
        # 3. 延期通知
        if process_info.get('allows_extension', False):
            if not process_info.get('notifies_consumer_of_extension', False):
                compliant = False
                violations.append("允许延期但未通知消费者")
        
        # 4. 免费提供服务
        if process_info.get('charges_for_request', False):
            compliant = False
            violations.append("对消费者权利请求收费（违反CCPA）")
        
        # 5. 多个请求处理
        if not process_info.get('handles_multiple_requests', False):
            compliant = False
            violations.append("无法处理多个请求")
        
        return compliant, violations


def main():
    """测试函数"""
    validator = CCPAValidator()
    
    # 测试企业适用性检查
    print("1. 测试企业适用性检查:")
    business_info = {
        'annual_revenue': 30000000,
        'consumer_data_volume': 60000,
        'revenue_from_data_sales': 10000000,
        'processes_sensitive_pi': True
    }
    applicable, reasons = validator.check_business_applicability(business_info)
    print(f"   企业信息: {business_info}")
    print(f"   是否适用CCPA: {applicable}")
    print(f"   适用原因: {reasons}")
    
    # 测试消费者权利验证
    print("\n2. 测试消费者权利验证:")
    rights_info = {
        'privacy_notice': True,
        'data_collection_disclosure': True,
        'do_not_sell_link': True,
        'deletion_request_mechanism': True,
        'correction_request_mechanism': False  # 缺少更正请求机制
    }
    implemented, missing = validator.validate_consumer_rights(rights_info)
    print(f"   权利实现: {rights_info}")
    print(f"   是否完整实现: {implemented}")
    print(f"   缺失项: {missing}")
    
    # 测试个人信息类别验证
    print("\n3. 测试个人信息类别验证:")
    categories = ['identifiers', 'contact_information', 'financial_information', 'social_security_number']
    complete, missing_cats, sensitive = validator.validate_personal_information_categories(categories)
    print(f"   处理的数据类别: {categories}")
    print(f"   是否完整识别: {complete}")
    print(f"   缺失的类别: {missing_cats}")
    print(f"   敏感个人信息: {sensitive}")


if __name__ == "__main__":
    main()