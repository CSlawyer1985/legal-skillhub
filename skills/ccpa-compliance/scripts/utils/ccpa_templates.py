#!/usr/bin/env python3
"""
CCPA模板引擎
提供CCPA/CPRA合规文档的模板生成功能
"""

import json
import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path


class CCPATemplateEngine:
    """CCPA模板引擎"""
    
    def __init__(self, template_dir: Optional[str] = None):
        """
        初始化模板引擎
        
        Args:
            template_dir: 模板目录路径
        """
        if template_dir:
            self.template_dir = Path(template_dir)
        else:
            self.template_dir = Path(__file__).parent.parent.parent / "assets" / "templates"
        
        # 检查模板目录是否存在，但不自动创建
        # 注意：如果目录不存在，模板保存功能可能失败
        # 这是为了遵守"不执行任何系统修改"的声明
        
        # 预定义模板
        self.templates = {
            "privacy_notice": self._get_privacy_notice_template(),
            "do_not_sell_page": self._get_do_not_sell_template(),
            "consumer_request_form": self._get_consumer_request_template(),
            "data_inventory": self._get_data_inventory_template(),
        }
    
    def _get_privacy_notice_template(self) -> str:
        """获取隐私通知模板"""
        return """# CCPA/CPRA隐私通知 (Privacy Notice)
根据加州《消费者隐私法》(CCPA/CPRA)要求

## 企业信息
**公司名称**: {company_name}
**地址**: {company_address}
**联系方式**: {contact_email}
**网站**: {website_url}

## 收集的个人信息类别
根据CCPA，我们收集以下类别的个人信息：

| 类别 | 示例 | 收集目的 |
|------|------|----------|
{pi_categories}

## 个人信息来源
我们收集个人信息的方式包括：
- 直接来自您（例如，填写表格、创建账户）
- 自动收集（例如，通过cookies和跟踪技术）
- 来自第三方（例如，数据提供商、合作伙伴）

## 个人信息使用
我们使用个人信息的目的包括：
{use_purposes}

## 个人信息共享和销售
### 个人信息共享
我们与以下类别的第三方共享个人信息：
{shared_with}

### 个人信息销售
{data_sale_info}

### "请勿销售我的个人信息"
您有权选择退出个人信息销售。要行使此权利，请访问：
**请勿销售我的个人信息**: {do_not_sell_link}

## 您的CCPA权利
根据CCPA，您拥有以下权利：

### 知情权 (Right to Know)
- 了解我们收集的个人信息类别
- 了解个人信息来源
- 了解个人信息使用和共享目的
- 了解个人信息销售情况

### 删除权 (Right to Delete)
- 要求删除我们收集的您的个人信息
- 某些例外情况适用（例如，法律要求保留）

### 选择退出权 (Right to Opt-Out)
- 选择退出个人信息销售
- 选择退出个人信息共享（仅限某些情况）

### 不受歧视权 (Right to Non-Discrimination)
- 不会因行使CCPA权利而受到歧视
- 不会因此被拒绝商品或服务
- 不会因此被收取不同价格

### 更正权 (Right to Correct) - CPRA新增
- 要求更正不准确的个人信息

### 限制权 (Right to Limit) - CPRA新增
- 限制敏感个人信息的使用

## 如何行使您的权利
### 提交请求
要行使您的CCPA权利，请：
1. 访问: {rights_portal_url}
2. 或发送电子邮件至: {rights_email}
3. 或拨打: {rights_phone}

### 验证流程
为确保安全，我们可能需要验证您的身份。

### 授权代理
您可以授权他人代表您行使权利。

## 响应时间
我们将在收到请求后45天内响应。如有需要，可延期45天并通知您。

## 13岁以下儿童
我们不会在未获得家长同意的情况下故意收集13岁以下儿童的个人信息。

## 联系方式
如有任何问题或行使您的权利，请联系：
**隐私团队**: {privacy_team}
**邮箱**: {privacy_email}
**电话**: {privacy_phone}

## 更新记录
**上次更新**: {last_updated}
**生效日期**: {effective_date}

---

**重要提示**: 本隐私通知仅适用于加州居民，解释我们的个人信息处理实践。其他州居民的权利可能不同。"""
    
    def _get_do_not_sell_template(self) -> str:
        """获取"请勿销售"页面模板"""
        return """# 请勿销售我的个人信息 (Do Not Sell My Personal Information)
CCPA/CPRA选择退出页面

## 您的CCPA选择退出权
根据加州《消费者隐私法》(CCPA)，您有权选择退出我们销售您的个人信息。

## 如何选择退出

### 选项1: 在线选择退出
请点击以下链接完成选择退出：
**选择退出链接**: {opt_out_link}

### 选项2: 电子邮件选择退出
请发送电子邮件至：{opt_out_email}
主题：CCPA选择退出请求

### 选项3: 电话选择退出
请拨打：{opt_out_phone}
请准备好提供验证信息。

### 选项4: 邮件选择退出
请邮寄至：
{mailing_address}
收件人：隐私团队 - CCPA选择退出

## 选择退出范围
当您选择退出时，我们将：
1. 停止销售您的个人信息
2. 通知所有我们已销售您信息的第三方
3. 尊重您的选择至少12个月

## 选择退出例外情况
请注意，某些个人信息共享不属于"销售"，包括：
- 与服务提供商的共享
- 履行您请求的共享
- 法律要求的共享

## 选择退出验证
为确保安全，我们可能需要验证您的身份。

## 选择退出确认
提交选择退出请求后，您将收到确认信息。

## 选择退出有效期
您的选择退出有效期为12个月。12个月后，我们将再次请求您的同意。

## 全局选择退出
我们支持全局选择退出机制。

## 选择退出恢复
如果您改变主意，可以随时选择重新加入。

## 其他权利提醒
除选择退出权外，您还拥有：
- **知情权**: 了解我们收集的个人信息
- **删除权**: 要求删除您的个人信息
- **不受歧视权**: 不会因行使权利而受到歧视

## 联系信息
如有问题，请联系：
**隐私团队**: {contact_name}
**邮箱**: {contact_email}
**电话**: {contact_phone}

**页面最后更新**: {last_updated}"""
    
    def _get_consumer_request_form(self) -> str:
        """获取消费者请求表格模板"""
        return """# CCPA消费者权利请求表格 (Consumer Request Form)
根据加州《消费者隐私法》(CCPA)要求

## 请求人信息
**姓名**: {requester_name}
**地址**: {requester_address}
**联系方式**: {requester_contact}
**加州居民证明**: {ca_resident_proof}

## 请求类型 (请选择一项)
□ **知情权请求** - 了解我们收集的个人信息
□ **删除权请求** - 要求删除个人信息
□ **选择退出请求** - 选择退出个人信息销售
□ **更正权请求** - 更正不准确的个人信息 (CPRA)
□ **限制权请求** - 限制敏感个人信息使用 (CPRA)

## 请求详细信息
**涉及的账户/服务**: {related_accounts}
**具体请求内容**: {request_details}
**相关时间范围**: {relevant_time_period}

## 授权代理信息 (如适用)
**代理姓名**: {agent_name}
**代理关系**: {agent_relationship}
**授权证明**: {authorization_proof}
**代理联系方式**: {agent_contact}

## 验证信息
**提供的验证文件**: {verification_documents}
**验证方法**: {verification_method}

## 企业响应
**收到请求日期**: {receipt_date}
**响应截止日期**: {response_deadline} (应在收到后45天内)
**响应状态**: {response_status}

## 延期信息 (如适用)
**延期原因**: {extension_reason}
**延期天数**: {extension_days}

## 请求处理记录
**处理人**: {handler_name}
**处理日期**: {handling_date}

## 投诉信息
如对响应不满意，您有权向加州总检察长投诉：
**加州总检察长办公室**: California Attorney General's Office
**联系方式**: (800) 952-5225

## 重要提醒
1. 我们不会因您行使CCPA权利而歧视您
2. 验证是为了确保个人信息安全
3. 某些信息可能因法律要求无法删除
4. 响应可能需要45天时间

## 签字
**请求人**: ___________________________
**日期**: {signature_date}

**企业代表**: ___________________________
**日期**: {acknowledgement_date}
**处理编号**: {request_id}"""
    
    def _get_data_inventory_template(self) -> str:
        """获取数据清单模板"""
        return """# CCPA数据清单 (Data Inventory)
个人信息处理记录

## 企业信息
**公司名称**: {company_name}
**编制日期**: {inventory_date}
**负责人**: {responsible_person}

## 收集的个人信息类别
| 类别 | 具体数据类型 | 收集方式 | 收集目的 | 保留期限 |
|------|-------------|----------|----------|----------|
{collected_data}

## 个人信息来源
| 来源类别 | 具体来源 | 数据类别 | 收集频率 |
|----------|----------|----------|----------|
{data_sources}

## 个人信息使用目的
| 使用目的 | 使用的数据类别 | 合法性基础 | 是否必要 |
|----------|----------------|------------|----------|
{use_purposes}

## 第三方共享
| 第三方类别 | 第三方名称 | 共享的数据 | 共享目的 | 合同类型 |
|------------|------------|------------|----------|----------|
{third_party_sharing}

## 个人信息销售
| 购买方类别 | 购买方名称 | 销售的数据 | 选择退出机制 |
|------------|------------|------------|--------------|
{data_sales}

## 敏感个人信息 (CPRA)
| 敏感信息类别 | 具体数据 | 处理目的 | 限制措施 |
|--------------|----------|----------|----------|
{sensitive_pi}

## 消费者权利响应记录
| 请求类型 | 本月数量 | 本年数量 | 平均处理时间 |
|----------|----------|----------|--------------|
{request_stats}

## 合规检查记录
| 检查项目 | 检查日期 | 检查结果 | 整改措施 |
|----------|----------|----------|----------|
{compliance_checks}

## 更新记录
| 变更日期 | 变更内容 | 变更原因 | 负责人 |
|----------|----------|----------|--------|
{inventory_changes}

---

**数据清单状态**: {inventory_status}
**下次更新**: {next_update}
**批准**: {approval_signature}"""
    
    def get_template(self, template_name: str) -> str:
        """
        获取指定模板
        
        Args:
            template_name: 模板名称
            
        Returns:
            模板内容
        """
        return self.templates.get(template_name, "")
    
    def render_template(self, template_name: str, data: Dict[str, Any]) -> str:
        """
        渲染模板
        
        Args:
            template_name: 模板名称
            data: 渲染数据
            
        Returns:
            渲染后的内容
        """
        template = self.get_template(template_name)
        if not template:
            return ""
        
        # 简单的模板渲染
        result = template
        for key, value in data.items():
            placeholder = "{" + key + "}"
            result = result.replace(placeholder, str(value))
        
        return result
    
    def save_template(self, template_name: str, data: Dict[str, Any], output_path: str) -> bool:
        """
        保存渲染后的模板
        
        Args:
            template_name: 模板名称
            data: 渲染数据
            output_path: 输出路径
            
        Returns:
            是否成功
        """
        try:
            content = self.render_template(template_name, data)
            if not content:
                return False
            
            # 确保输出目录存在
            output_dir = Path(output_path).parent
            if not output_dir.exists():
                # 不自动创建目录，遵守"不执行任何系统修改"声明
                print(f"警告: 输出目录不存在: {output_dir}")
                return False
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
        except Exception as e:
            print(f"保存模板失败: {e}")
            return False