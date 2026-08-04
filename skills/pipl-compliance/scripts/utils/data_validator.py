#!/usr/bin/env python3
"""
数据验证工具 - 验证PIPL合规相关数据
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional

class DataValidator:
    """数据验证工具类"""
    
    @staticmethod
    def validate_company_info(company_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证企业信息
        
        Args:
            company_data: 企业信息字典
        
        Returns:
            Dict: 验证结果
        """
        required_fields = ['name', 'industry', 'data_processing_scale']
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'missing_fields': []
        }
        
        # 检查必需字段
        for field in required_fields:
            if field not in company_data or not company_data[field]:
                validation_result['missing_fields'].append(field)
                validation_result['valid'] = False
        
        # 验证数据规模
        if 'data_processing_scale' in company_data:
            scale = company_data['data_processing_scale']
            valid_scales = ['small', 'medium', 'large', 'enterprise']
            if scale not in valid_scales:
                validation_result['warnings'].append(f"数据规模 '{scale}' 不在标准范围内: {valid_scales}")
        
        # 验证行业分类
        if 'industry' in company_data:
            industry = company_data['industry']
            common_industries = ['tech', 'finance', 'healthcare', 'ecommerce', 'education', 'other']
            if industry not in common_industries:
                validation_result['warnings'].append(f"行业 '{industry}' 可能不是标准分类")
        
        return validation_result
    
    @staticmethod
    def validate_personal_info(personal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证个人信息
        
        Args:
            personal_data: 个人信息字典
        
        Returns:
            Dict: 验证结果
        """
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'sensitive_fields': []
        }
        
        # 定义敏感字段
        sensitive_fields = {
            'id_card': '身份证号码',
            'phone': '手机号码',
            'email': '电子邮箱',
            'address': '住址',
            'biometric': '生物识别信息',
            'health': '健康信息',
            'financial': '金融信息'
        }
        
        # 检查敏感字段
        for field, description in sensitive_fields.items():
            if field in personal_data and personal_data[field]:
                validation_result['sensitive_fields'].append(description)
        
        # 验证身份证格式
        if 'id_card' in personal_data and personal_data['id_card']:
            if not DataValidator._validate_id_card(personal_data['id_card']):
                validation_result['errors'].append('身份证格式不正确')
                validation_result['valid'] = False
        
        # 验证手机号码格式
        if 'phone' in personal_data and personal_data['phone']:
            if not DataValidator._validate_phone(personal_data['phone']):
                validation_result['errors'].append('手机号码格式不正确')
                validation_result['valid'] = False
        
        # 验证邮箱格式
        if 'email' in personal_data and personal_data['email']:
            if not DataValidator._validate_email(personal_data['email']):
                validation_result['errors'].append('邮箱格式不正确')
                validation_result['valid'] = False
        
        return validation_result
    
    @staticmethod
    def validate_consent_data(consent_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证用户同意数据
        
        Args:
            consent_data: 同意数据字典
        
        Returns:
            Dict: 验证结果
        """
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'consent_types': []
        }
        
        required_consent_fields = ['consent_time', 'consent_type', 'purpose', 'withdrawal_available']
        
        for field in required_consent_fields:
            if field not in consent_data:
                validation_result['errors'].append(f"同意数据缺少必需字段: {field}")
                validation_result['valid'] = False
        
        # 验证同意时间
        if 'consent_time' in consent_data:
            try:
                consent_time = datetime.fromisoformat(consent_data['consent_time'].replace('Z', '+00:00'))
                if consent_time > datetime.now():
                    validation_result['errors'].append('同意时间不能晚于当前时间')
                    validation_result['valid'] = False
            except ValueError:
                validation_result['errors'].append('同意时间格式不正确')
                validation_result['valid'] = False
        
        # 验证同意类型
        if 'consent_type' in consent_data:
            consent_type = consent_data['consent_type']
            valid_types = ['explicit', 'separate', 'specific', 'general']
            if consent_type not in valid_types:
                validation_result['errors'].append(f"同意类型 '{consent_type}' 无效，有效类型: {valid_types}")
                validation_result['valid'] = False
            else:
                validation_result['consent_types'].append(consent_type)
        
        # 验证撤回选项
        if 'withdrawal_available' in consent_data:
            withdrawal = consent_data['withdrawal_available']
            if not isinstance(withdrawal, bool):
                validation_result['errors'].append('撤回选项必须是布尔值')
                validation_result['valid'] = False
        
        return validation_result
    
    @staticmethod
    def _validate_id_card(id_card: str) -> bool:
        """验证身份证号码格式"""
        # 简化验证，实际应使用更复杂的算法
        pattern = r'^[1-9]\d{5}(18|19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[1-2]\d|3[0-1])\d{3}[0-9Xx]$'
        return bool(re.match(pattern, id_card))
    
    @staticmethod
    def _validate_phone(phone: str) -> bool:
        """验证手机号码格式"""
        pattern = r'^1[3-9]\d{9}$'
        return bool(re.match(pattern, phone))
    
    @staticmethod
    def _validate_email(email: str) -> bool:
        """验证邮箱格式"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_compliance_checklist(checklist_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        验证合规检查清单数据
        
        Args:
            checklist_data: 检查清单数据列表
        
        Returns:
            Dict: 验证结果
        """
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'total_items': len(checklist_data),
            'completed_items': 0,
            'incomplete_items': 0
        }
        
        required_checklist_fields = ['id', 'category', 'requirement', 'status', 'importance']
        
        for i, item in enumerate(checklist_data):
            # 检查必需字段
            for field in required_checklist_fields:
                if field not in item:
                    validation_result['errors'].append(f"第{i+1}项检查缺少字段: {field}")
                    validation_result['valid'] = False
            
            # 验证状态
            if 'status' in item:
                status = item['status']
                valid_statuses = ['not_started', 'in_progress', 'completed', 'failed', 'exempt']
                if status not in valid_statuses:
                    validation_result['errors'].append(f"第{i+1}项检查状态 '{status}' 无效")
                    validation_result['valid'] = False
                elif status == 'completed':
                    validation_result['completed_items'] += 1
                else:
                    validation_result['incomplete_items'] += 1
            
            # 验证重要性
            if 'importance' in item:
                importance = item['importance']
                valid_importance = ['low', 'medium', 'high', 'critical']
                if importance not in valid_importance:
                    validation_result['warnings'].append(f"第{i+1}项检查重要性 '{importance}' 不在标准范围内")
        
        return validation_result

# 使用示例
if __name__ == "__main__":
    validator = DataValidator()
    
    # 测试企业信息验证
    company_data = {
        'name': '示例公司',
        'industry': 'tech',
        'data_processing_scale': 'medium'
    }
    
    result = validator.validate_company_info(company_data)
    print("企业信息验证结果:", json.dumps(result, indent=2, ensure_ascii=False))
    
    # 测试个人信息验证
    personal_data = {
        'name': '张三',
        'id_card': '110101199001011234',
        'phone': '13800138000',
        'email': 'zhangsan@example.com'
    }
    
    result = validator.validate_personal_info(personal_data)
    print("\n个人信息验证结果:", json.dumps(result, indent=2, ensure_ascii=False))
    
    # 测试同意数据验证
    consent_data = {
        'consent_time': '2024-01-01T10:00:00',
        'consent_type': 'explicit',
        'purpose': '用户注册',
        'withdrawal_available': True
    }
    
    result = validator.validate_consent_data(consent_data)
    print("\n同意数据验证结果:", json.dumps(result, indent=2, ensure_ascii=False))