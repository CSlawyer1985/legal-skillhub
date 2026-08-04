#!/usr/bin/env python3
"""
PIPL合规文档生成工具
使用Jinja2模板引擎生成隐私政策、用户同意书等合规文档
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# 尝试导入Jinja2，如果失败则使用备用方案
try:
    from jinja2 import Environment, FileSystemLoader, TemplateNotFound
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    print("⚠️  Jinja2未安装，使用简单模板系统。请运行：pip install jinja2>=3.1.0")

class DocumentGenerator:
    """文档生成器（支持Jinja2模板）"""
    
    def __init__(self):
        self.templates = {
            "privacy-policy": {
                "name": "隐私政策",
                "file": "privacy-policy-cn.md",
                "variables": [
                    "company_name",
                    "website_url",
                    "contact_email",
                    "effective_date",
                    "company_address",
                    "company_phone"
                ]
            },
            "consent-form": {
                "name": "用户同意书",
                "file": "consent-form-cn.md",
                "variables": [
                    "company_name",
                    "purpose",
                    "data_types",
                    "retention_period",
                    "third_party_names",
                    "effective_date"
                ]
            },
            "data-processing-agreement": {
                "name": "数据处理协议",
                "file": "data-processing-agreement-cn.md",
                "variables": [
                    "data_controller",
                    "data_processor",
                    "processing_purpose",
                    "security_level",
                    "effective_date",
                    "agreement_number"
                ]
            }
        }
        
        # 设置模板目录
        self.template_dir = Path(__file__).parent.parent / "assets" / "templates"
        
        # 如果Jinja2可用，使用Jinja2引擎
        if JINJA2_AVAILABLE:
            self.env = Environment(
                loader=FileSystemLoader(self.template_dir),
                trim_blocks=True,
                lstrip_blocks=True,
                keep_trailing_newline=True
            )
        else:
            # 备用：默认模板内容
            self.default_templates = {
                "privacy-policy-cn.md": self._get_privacy_policy_template(),
                "consent-form-cn.md": self._get_consent_form_template(),
                "data-processing-agreement-cn.md": self._get_data_processing_agreement_template()
            }
    
    def _get_privacy_policy_template(self) -> str:
        """获取隐私政策模板"""
        return """# 隐私政策

**生效日期**：{effective_date}

## 1. 收集的信息

{company_name}（以下简称"我们"）在为您提供服务时，会收集以下类型的个人信息：

### 1.1 您直接提供的信息
- 注册信息：姓名、电子邮箱地址、手机号码等
- 账户信息：用户名、密码、账户偏好设置等
- 联系信息：联系方式、邮寄地址等

### 1.2 自动收集的信息
- 设备信息：设备类型、操作系统、浏览器类型等
- 日志信息：IP地址、访问时间、页面浏览记录等
- Cookie和类似技术：用于改善用户体验

## 2. 信息使用目的

我们收集您的个人信息主要用于以下目的：

### 2.1 提供服务
- 创建和管理您的账户
- 提供您请求的服务和功能
- 处理您的订单和交易
- 响应您的咨询和请求

### 2.2 改进服务
- 分析使用情况以改进我们的服务
- 开发新的功能和服务
- 进行市场调研和分析

### 2.3 法律合规
- 遵守适用的法律法规
- 响应执法部门的要求
- 保护我们的合法权益

## 3. 信息共享

我们仅在以下情况下与第三方共享您的个人信息：

### 3.1 服务提供商
我们可能会与帮助我们运营网站、开展业务或为您提供服务的第三方服务提供商共享信息。

### 3.2 法律要求
如果我们确信根据适用法律、法规、法律程序或政府强制性要求有必要，我们可能会披露您的信息。

## 4. 信息安全

我们采取适当的技术和组织措施保护您的个人信息，防止未经授权的访问、使用或披露。

## 5. 您的权利

根据《中华人民共和国个人信息保护法》，您享有以下权利：

### 5.1 知情权和决定权
- 有权知悉我们处理您个人信息的情况
- 有权限制或拒绝他人处理您的个人信息

### 5.2 查阅权和复制权
- 有权查阅我们处理的您的个人信息
- 有权复制您的个人信息

### 5.3 更正权和删除权
- 有权要求更正不准确或不完整的个人信息
- 符合法定情形时，有权要求删除个人信息

## 6. 政策更新

我们可能会不时更新本隐私政策。如有重大变更，我们会在网站上发布通知。

## 7. 联系我们

如果您对本隐私政策有任何疑问或意见，请通过以下方式联系我们：

- 网站：{website_url}
- 邮箱：{contact_email}
- 地址：[请填写公司地址]

---
**公司名称**：{company_name}
**官方网站**：{website_url}
"""

    def _get_consent_form_template(self) -> str:
        """获取用户同意书模板"""
        return """# 用户同意书

## 个人信息处理告知和同意

### 一、处理目的
我们处理您的个人信息主要用于以下目的：
{purpose}

### 二、处理方式
我们通过以下方式处理您的个人信息：
1. 自动收集：通过网站、移动应用等渠道收集
2. 用户提供：您在注册、使用服务时提供的信息
3. 第三方来源：从合法来源获取的信息

### 三、个人信息类型
我们可能会处理以下类型的个人信息：
{data_types}

### 四、保存期限
我们将在实现处理目的所需的最短时间内保存您的个人信息，具体期限如下：
{retention_period}

### 五、第三方共享
我们可能会与以下第三方共享您的个人信息：
{third_party_names}

## 您的权利

根据《中华人民共和国个人信息保护法》，您享有以下权利：

### 1. 知情权和决定权
您有权知悉我们处理您个人信息的情况，并有权限制或拒绝他人处理您的个人信息。

### 2. 查阅权和复制权
您有权查阅和复制我们处理的您的个人信息。

### 3. 更正权和删除权
您有权要求更正不准确或不完整的个人信息，在符合法定情形时，有权要求删除个人信息。

### 4. 撤回同意权
您可以随时撤回对本同意书的同意。撤回同意不影响撤回前基于您的同意已进行的个人信息处理活动的效力。

## 特别提示

1. **单独同意**：对于敏感个人信息的处理、向其他个人信息处理者提供个人信息等情况，我们将在相关场景下取得您的单独同意。

2. **未成年人保护**：如您是不满十四周岁的未成年人，我们将在取得您的监护人同意后处理您的个人信息。

## 确认和同意

我已阅读并理解上述内容，并在此确认：

□ **我同意**《{company_name}隐私政策》的全部内容。

□ **我同意**{company_name}基于上述目的处理我的个人信息。

□ **我知悉**并了解我的个人信息权利，包括查阅、复制、更正、删除等权利。

□ **我同意**在必要时，{company_name}可以与上述第三方共享我的个人信息。

---
**签署人**：_________________
**签署日期**：_________________
"""

    def _get_data_processing_agreement_template(self) -> str:
        """获取数据处理协议模板"""
        return """# 个人信息处理协议

**协议编号**：PIPL-{timestamp}
**签署日期**：{effective_date}

## 协议双方

**个人信息控制方**：{data_controller}
**个人信息处理方**：{data_processor}

## 第一条 协议目的

本协议旨在根据《中华人民共和国个人信息保护法》等相关法律法规的规定，明确双方在个人信息处理活动中的权利和义务。

## 第二条 处理目的和方式

### 2.1 处理目的
{processing_purpose}

### 2.2 处理方式
处理方应按照控制方的明确指示和要求处理个人信息，不得超出约定的目的和处理方式处理个人信息。

## 第三条 个人信息类型和处理规模

### 3.1 个人信息类型
[请填写具体的个人信息类型]

### 3.2 处理规模
[请填写处理的个人信息数量]

## 第四条 安全保障措施

### 4.1 技术措施
处理方应采取以下技术措施保护个人信息安全：
- 加密技术：对传输和存储的个人信息进行加密
- 访问控制：建立严格的访问权限管理制度
- 安全审计：定期进行安全审计和漏洞扫描

### 4.2 管理措施
处理方应建立以下管理制度：
- 安全管理制度：建立个人信息安全管理制度
- 人员管理：对相关人员进行背景审查和安全培训
- 应急响应：建立个人信息安全事件应急预案

## 第五条 安全等级要求

根据个人信息的重要程度和风险情况，本协议约定的安全等级为：{security_level}

## 第六条 监督和审计

### 6.1 监督权利
控制方有权对处理方的个人信息处理活动进行监督，处理方应予以配合。

### 6.2 定期审计
双方应每 [时间周期] 对个人信息处理活动进行一次审计。

## 第七条 违约责任

### 7.1 违约情形
任何一方违反本协议的约定，应承担相应的违约责任。

### 7.2 赔偿范围
违约方应赔偿守约方因此遭受的全部损失。

## 第八条 协议期限

### 8.1 协议生效
本协议自双方签署之日起生效。

### 8.2 协议终止
本协议在以下情况下终止：
1. 协议期限届满
2. 双方协商一致终止
3. 一方严重违约导致协议无法继续履行

## 第九条 争议解决

因本协议引起的或与本协议有关的任何争议，双方应首先通过友好协商解决；协商不成的，任何一方均有权将争议提交有管辖权的人民法院诉讼解决。

## 第十条 其他条款

### 10.1 完整协议
本协议构成双方就本协议事项达成的完整协议，取代双方之前就本协议事项达成的所有口头或书面协议。

### 10.2 修改和补充
本协议的修改和补充应采用书面形式，经双方签署后生效。

---

**个人信息控制方（盖章）**：

**授权代表（签字）**：_________________
**签署日期**：_________________

**个人信息处理方（盖章）**：

**授权代表（签字）**：_________________
**签署日期**：_________________
"""
    
    def get_template(self, doc_type: str) -> Optional[Dict]:
        """获取模板信息"""
        return self.templates.get(doc_type)
    
    def list_templates(self) -> List[str]:
        """列出可用模板"""
        return list(self.templates.keys())
    
    def generate_document(self, 
                         doc_type: str,
                         variables: Dict[str, Any],
                         output_path: Optional[str] = None) -> Dict:
        """生成文档（支持Jinja2模板）"""
        
        # 检查模板是否存在
        if doc_type not in self.templates:
            return {
                "status": "error",
                "message": f"未知的文档类型：{doc_type}",
                "available_types": self.list_templates()
            }
        
        template_info = self.templates[doc_type]
        template_file = template_info["file"]
        
    def _get_default_templates(self) -> Dict[str, str]:
        """获取默认模板内容"""
        return {
            "privacy-policy-cn.md": self._get_privacy_policy_template(),
            "consent-form-cn.md": self._get_consent_form_template(),
            "data-processing-agreement-cn.md": self._get_data_processing_agreement_template()
        }
    
    def list_available_templates(self) -> List[Dict[str, Any]]:
        """列出可用的模板信息"""
        templates = []
        for key, info in self.templates.items():
            templates.append({
                "id": key,
                "name": info["name"],
                "file": info["file"],
                "variables": info["variables"],
                "description": f"生成{info['name']}文档"
            })
        return templates
        
        # 准备变量
        now = datetime.now()
        default_variables = {
            "effective_date": now.strftime("%Y年%m月%d日"),
            "timestamp": now.strftime("%Y%m%d%H%M%S"),
            "year": now.year,
            "month": now.month,
            "day": now.day,
            "generated_at": now.isoformat()
        }
        
        # 合并变量
        all_variables = {**default_variables, **variables}
        
        # 生成文档内容
        if JINJA2_AVAILABLE:
            try:
                template = self.env.get_template(template_file)
                document_content = template.render(**all_variables)
            except TemplateNotFound:
                # 如果模板文件不存在，使用备用模板
                if template_file in self._get_default_templates():
                    template_content = self._get_default_templates()[template_file]
                    document_content = template_content.format(**all_variables)
                else:
                    return {
                        "status": "error",
                        "message": f"模板文件不存在：{template_file}",
                        "suggested_path": str(self.template_dir / template_file)
                    }
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"模板渲染失败：{str(e)}"
                }
        else:
            # 使用简单模板系统
            if template_file in self.default_templates:
                template_content = self.default_templates[template_file]
            else:
                # 尝试从文件系统读取
                template_path = self.template_dir / template_file
                if template_path.exists():
                    with open(template_path, 'r', encoding='utf-8') as f:
                        template_content = f.read()
                else:
                    return {
                        "status": "error",
                        "message": f"模板文件不存在：{template_file}",
                        "suggested_path": str(template_path)
                    }
            
            # 生成文档
            try:
                document_content = template_content.format(**all_variables)
            except KeyError as e:
                missing_var = str(e).strip("'")
                return {
                    "status": "error",
                    "message": f"缺少必要的变量：{missing_var}",
                    "required_variables": template_info["variables"]
                }
        
        # 确定输出路径
        if not output_path:
            # 使用默认文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"{doc_type}_{timestamp}.md"
        
        # 写入文件
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(document_content)
            
            return {
                "status": "success",
                "message": f"文档生成成功",
                "document_type": doc_type,
                "output_file": os.path.abspath(output_path),
                "generated_at": datetime.now().isoformat(),
                "variables_used": all_variables
            }
        
        except Exception as e:
            return {
                "status": "error",
                "message": f"写入文件失败：{str(e)}",
                "output_path": output_path
            }
    
    def list_variables(self, doc_type: str) -> List[str]:
        """列出文档所需的变量"""
        if doc_type not in self.templates:
            return []
        
        return self.templates[doc_type]["variables"]

def main():
    parser = argparse.ArgumentParser(description="PIPL合规文档生成工具（支持Jinja2模板）")
    parser.add_argument("--type", required=True, choices=["privacy-policy", "consent-form", "data-processing-agreement"],
                       help="文档类型")
    parser.add_argument("--output", help="输出文件路径")
    parser.add_argument("--list-variables", action="store_true", help="列出所需变量")
    parser.add_argument("--list-templates", action="store_true", help="列出可用模板")
    parser.add_argument("--check-jinja2", action="store_true", help="检查Jinja2是否可用")
    
    # 常用变量参数
    parser.add_argument("--company-name", help="公司名称")
    parser.add_argument("--website-url", help="网站地址")
    parser.add_argument("--contact-email", help="联系邮箱")
    parser.add_argument("--company-address", help="公司地址")
    parser.add_argument("--company-phone", help="公司电话")
    parser.add_argument("--data-types", help="数据类型（用逗号分隔）")
    parser.add_argument("--retention-period", help="保存期限")
    parser.add_argument("--third-party-names", help="第三方名称（用逗号分隔）")
    parser.add_argument("--data-controller", help="个人信息控制方")
    parser.add_argument("--data-processor", help="个人信息处理方")
    parser.add_argument("--processing-purpose", help="处理目的")
    parser.add_argument("--security-level", help="安全等级")
    
    parser.add_argument("--format", choices=["json", "text"], default="text", help="输出格式")
    
    args = parser.parse_args()
    
    # 创建生成器
    generator = DocumentGenerator()
    
    # 检查Jinja2可用性
    if args.check_jinja2:
        if JINJA2_AVAILABLE:
            print("✅ Jinja2可用")
        else:
            print("⚠️  Jinja2不可用，建议安装：pip install jinja2>=3.1.0")
        return
    
    # 列出可用模板
    if args.list_templates:
        templates = generator.list_available_templates()
        if args.format == "json":
            print(json.dumps(templates, ensure_ascii=False, indent=2))
        else:
            print("可用文档模板：")
            for template in templates:
                print(f"📄 {template['name']} ({template['id']})")
                print(f"   文件：{template['file']}")
                print(f"   变量：{', '.join(template['variables'])}")
                print()
        return
    
    # 如果是列出变量
    if args.list_variables:
        variables = generator.list_variables(args.type)
        if args.format == "json":
            print(json.dumps({
                "type": args.type,
                "variables": variables
            }, ensure_ascii=False, indent=2))
        else:
            print(f"文档类型：{args.type}")
            print("所需变量：")
            for var in variables:
                print(f"  - {var}")
        return
    
    # 收集变量
    variables = {}
    
    # 添加提供的变量
    if args.company_name:
        variables["company_name"] = args.company_name
    if args.website_url:
        variables["website_url"] = args.website_url
    if args.contact_email:
        variables["contact_email"] = args.contact_email
    if args.company_address:
        variables["company_address"] = args.company_address
    if args.company_phone:
        variables["company_phone"] = args.company_phone
    if args.data_types:
        variables["data_types"] = args.data_types
    if args.retention_period:
        variables["retention_period"] = args.retention_period
    if args.third_party_names:
        variables["third_party_names"] = args.third_party_names
    if args.data_controller:
        variables["data_controller"] = args.data_controller
    if args.data_processor:
        variables["data_processor"] = args.data_processor
    if args.processing_purpose:
        variables["processing_purpose"] = args.processing_purpose
    if args.security_level:
        variables["security_level"] = args.security_level
    
    # 生成文档
    result = generator.generate_document(args.type, variables, args.output)
    
    # 输出结果
    if args.format == "json":
        output = json.dumps(result, ensure_ascii=False, indent=2)
    else:
        output = format_text_output(result)
    
    print(output)

def format_text_output(result: Dict) -> str:
    """格式化文本输出"""
    if result["status"] == "error":
        output_lines = [
            "❌ 文档生成失败",
            "=" * 60,
            f"错误信息：{result['message']}"
        ]
        
        if "available_types" in result:
            output_lines.append("")
            output_lines.append("可用的文档类型：")
            for doc_type in result["available_types"]:
                output_lines.append(f"  - {doc_type}")
        
        if "required_variables" in result:
            output_lines.append("")
            output_lines.append("所需的变量：")
            for var in result["required_variables"]:
                output_lines.append(f"  - {var}")
        
        output_lines.append("=" * 60)
        
        return "\n".join(output_lines)
    
    else:
        output_lines = [
            "✅ 文档生成成功",
            "=" * 60,
            f"文档类型：{result['document_type']}",
            f"输出文件：{result['output_file']}",
            f"生成时间：{result['generated_at']}",
            ""
        ]
        
        # 显示使用的变量
        if "variables_used" in result:
            output_lines.append("使用的变量：")
            for key, value in result["variables_used"].items():
                output_lines.append(f"  {key}: {value}")
        
        output_lines.append("")
        output_lines.append("=" * 60)
        
        return "\n".join(output_lines)

if __name__ == "__main__":
    main()