#!/usr/bin/env python3
"""
CCPA Compliance - 安全检查脚本
用于验证技能的安全性和纯本地运行特性
"""

import os
import sys
import re
import subprocess
from pathlib import Path

class SecurityCheckerCCPA:
    """CCPA安全检查器"""
    
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.project_root = self.script_dir.parent
        
        # 网络调用关键词（CCPA特定）
        self.network_keywords = [
            'import requests', 'import urllib', 'import http', 'import socket',
            'import ftplib', 'import aiohttp', 'import paramiko',
            'requests.get', 'requests.post', 'urllib.request',
            'http.client', 'socket.socket', 'subprocess.run.*curl',
            'subprocess.run.*wget', 'subprocess.Popen.*curl',
            'subprocess.Popen.*wget',
            # CCPA特定可能的外部调用
            'california.*privacy', 'doj.*california', 'ag.*ca.gov',
            'data.*sale', 'opt.*out.*api'
        ]
        
        # 自动更新/上报关键词
        self.update_keywords = [
            'check_for_updates', 'auto_update', 'telemetry',
            'upload.*data', 'post.*data', 'send.*report',
            'external.*api', 'api.*endpoint', 'webhook',
            'callback.*url', 'report.*server',
            'consumer.*data.*api', 'privacy.*rights.*api'
        ]
        
        # 外部URL模式
        self.url_patterns = [
            r'http://[^\s"\']+',
            r'https://[^\s"\']+',
            r'ftp://[^\s"\']+',
            r'ws://[^\s"\']+',
            r'wss://[^\s"\']+'
        ]
        
        # CCPA特定关键词（应当存在的）
        self.ccpa_keywords = [
            'ccpa', 'cpra', 'california.*consumer.*privacy',
            'consumer.*rights', 'right.*to.*know', 'right.*to.*delete',
            'right.*to.*opt.*out', 'right.*to.*non.*discrimination',
            'personal.*information', 'sensitive.*personal.*information',
            'data.*sale', 'data.*sharing', 'do.*not.*sell',
            'opt.*out', 'opt.*in', 'privacy.*notice',
            'verifiable.*consumer.*request', 'service.*provider',
            'business.*purpose', 'commercial.*purpose'
        ]
        
        self.findings = []
        self.ccpa_compliance_score = 0
        self.max_ccpa_score = 0
    
    def check_python_files(self):
        """检查所有Python文件"""
        print("🔍 检查Python文件...")
        
        python_files = list(self.script_dir.rglob("*.py"))
        
        # 排除安全检查脚本本身
        python_files = [f for f in python_files if f.name != 'security_check_ccpa.py']
        
        print(f"  发现 {len(python_files)} 个Python文件")
        
        for file_path in python_files:
            relative_path = file_path.relative_to(self.project_root)
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 检查网络调用
                for keyword in self.network_keywords:
                    # 跳过CCPA术语关键词（不是实际网络调用）
                    ccpa_terms = ['california.*privacy', 'doj.*california', 'ag.*ca.gov', 'data.*sale', 'opt.*out.*api']
                    if any(ccpa_term in keyword for ccpa_term in ccpa_terms):
                        continue
                    
                    if re.search(keyword, content, re.IGNORECASE):
                        self.findings.append({
                            'file': str(relative_path),
                            'type': 'network_call',
                            'keyword': keyword,
                            'severity': 'high'
                        })
                
                # 检查自动更新逻辑
                for keyword in self.update_keywords:
                    if re.search(keyword, content, re.IGNORECASE):
                        self.findings.append({
                            'file': str(relative_path),
                            'type': 'auto_update',
                            'keyword': keyword,
                            'severity': 'medium'
                        })
                
                # 检查外部URL
                for pattern in self.url_patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        # 跳过package.json中的已知URL
                        if 'clawhub.ai' in match and 'package.json' in str(relative_path):
                            continue
                        self.findings.append({
                            'file': str(relative_path),
                            'type': 'external_url',
                            'url': match,
                            'severity': 'medium'
                        })
                
                # 检查CCPA特定关键词
                ccpa_found = 0
                for keyword in self.ccpa_keywords:
                    if re.search(keyword, content, re.IGNORECASE):
                        ccpa_found += 1
                
                if ccpa_found > 0:
                    self.ccpa_compliance_score += min(ccpa_found, 5)  # 最多加5分
                        
            except Exception as e:
                print(f"  警告: 无法检查文件 {relative_path}: {e}")
        
        self.max_ccpa_score = len(self.ccpa_keywords) * 0.5  # 每个最多0.5分
        print(f"  完成Python文件检查")
    
    def check_requirements(self):
        """检查依赖文件"""
        print("🔍 检查依赖文件...")
        
        req_file = self.project_root / 'requirements.txt'
        if req_file.exists():
            with open(req_file, 'r') as f:
                content = f.read()
            
            # 检查依赖数量
            lines = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]
            print(f"  发现 {len(lines)} 个依赖包")
            
            for line in lines:
                if 'requests' in line.lower() or 'urllib' in line.lower() or 'http' in line.lower():
                    self.findings.append({
                        'file': 'requirements.txt',
                        'type': 'network_dependency',
                        'dependency': line,
                        'severity': 'high'
                    })
                
                # CCPA合规包检查
                if 'pandas' in line.lower():
                    self.ccpa_compliance_score += 2
                if 'jinja2' in line.lower():
                    self.ccpa_compliance_score += 2
        else:
            print("  ⚠️  未找到requirements.txt文件")
            print("  ℹ️  请确保安装前创建requirements.txt文件")
            # 不自动创建，避免文件系统修改
            # self._create_default_requirements()
        
        print(f"  完成依赖文件检查")
    
    def _create_default_requirements(self):
        """创建默认的requirements.txt（已禁用）"""
        # 注意：已禁用自动创建，以遵守"不执行任何系统修改"的声明
        print("  ℹ️  已禁用自动创建，避免文件系统修改")
        print("  ℹ️  请手动创建requirements.txt文件")
    
    def check_skill_md(self):
        """检查SKILL.md中的声明"""
        print("🔍 检查SKILL.md声明...")
        
        skill_file = self.project_root / 'SKILL.md'
        if skill_file.exists():
            with open(skill_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查纯本地声明
            local_keywords = ['纯本地运行', '无网络调用', '本地运行', '无需网络']
            found_local_declaration = False
            
            for keyword in local_keywords:
                if keyword in content:
                    found_local_declaration = True
                    break
            
            if not found_local_declaration:
                self.findings.append({
                    'file': 'SKILL.md',
                    'type': 'missing_local_declaration',
                    'severity': 'medium',
                    'note': '建议添加纯本地运行的明确声明'
                })
            else:
                print(f"  ✅ SKILL.md中包含纯本地运行声明")
                self.ccpa_compliance_score += 5
            
            # 检查CCPA免责条款
            disclaimer_keywords = ['免责条款', '非法律建议', '专业咨询', '责任限制']
            found_disclaimer = 0
            for keyword in disclaimer_keywords:
                if keyword in content:
                    found_disclaimer += 1
            
            if found_disclaimer >= 3:
                print(f"  ✅ SKILL.md中包含完整的免责条款")
                self.ccpa_compliance_score += 10
            elif found_disclaimer > 0:
                print(f"  ⚠️ SKILL.md中包含部分免责条款")
                self.ccpa_compliance_score += 5
            else:
                self.findings.append({
                    'file': 'SKILL.md',
                    'type': 'missing_disclaimer',
                    'severity': 'high',
                    'note': '强烈建议添加完整的法律免责条款'
                })
            
            # 检查CCPA特定关键词
            ccpa_found = 0
            for keyword in self.ccpa_keywords[:10]:  # 只检查前10个关键词
                if re.search(keyword, content, re.IGNORECASE):
                    ccpa_found += 1
            
            if ccpa_found >= 5:
                print(f"  ✅ SKILL.md中包含完整的CCPA相关信息")
                self.ccpa_compliance_score += 10
        
        print(f"  完成SKILL.md检查")
    
    def check_ccpa_references(self):
        """检查CCPA参考文档"""
        print("🔍 检查CCPA参考文档...")
        
        ref_dir = self.project_root / 'references'
        if ref_dir.exists():
            ref_files = list(ref_dir.rglob("*.md"))
            print(f"  发现 {len(ref_files)} 个参考文档")
            
            for file_path in ref_files:
                if 'ccpa' in file_path.name.lower() or 'cpa' in file_path.name.lower():
                    self.ccpa_compliance_score += 10
                    print(f"  ✅ 找到CCPA法规参考文档: {file_path.name}")
        else:
            print("  未找到references目录")
        
        print(f"  完成CCPA参考文档检查")
    
    def run_ccpa_functional_tests(self):
        """运行CCPA功能测试"""
        print("🔍 运行CCPA功能测试...")
        
        # 检查是否有ccpa-check.py
        ccpa_check_script = self.script_dir / 'ccpa-check.py'
        if ccpa_check_script.exists():
            test_commands = [
                ['python3', str(ccpa_check_script), '--help'],
            ]
            
            for cmd in test_commands:
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    if result.returncode == 0:
                        print(f"  ✅ 命令 {' '.join(cmd)} 执行成功")
                        self.ccpa_compliance_score += 20
                    else:
                        self.findings.append({
                            'type': 'test_failure',
                            'command': ' '.join(cmd),
                            'error': result.stderr[:100],
                            'severity': 'medium'
                        })
                        
                except subprocess.TimeoutExpired:
                    self.findings.append({
                        'type': 'test_timeout',
                        'command': ' '.join(cmd),
                        'severity': 'medium',
                        'note': '命令执行超时，可能有问题'
                    })
                except Exception as e:
                    self.findings.append({
                        'type': 'test_exception',
                        'command': ' '.join(cmd),
                        'error': str(e),
                        'severity': 'medium'
                    })
        else:
            print("  ⚠️ 未找到ccpa-check.py脚本")
        
        print(f"  完成CCPA功能测试")
    
    def generate_report(self):
        """生成检查报告"""
        print("\n" + "="*60)
        print("📋 CCPA安全检查报告")
        print("="*60)
        
        # 计算CCPA合规评分
        total_score = self.ccpa_compliance_score
        max_score = 100
        
        print(f"\n🔐 CCPA合规评分: {total_score}/{max_score}")
        
        if total_score >= 80:
            print("  🥇 优秀 - CCPA合规性良好")
        elif total_score >= 60:
            print("  🥈 良好 - CCPA合规性较好")
        elif total_score >= 40:
            print("  🥉 中等 - CCPA合规性一般")
        else:
            print("  ⚠️  需要改进 - CCPA合规性不足")
        
        if not self.findings:
            print("\n✅ 所有安全检查通过！")
            print("\n🎉 CCPA Compliance技能看起来是安全的，符合纯本地运行的要求")
            return True
        
        # 按严重程度分类
        high_findings = [f for f in self.findings if f['severity'] == 'high']
        medium_findings = [f for f in self.findings if f['severity'] == 'medium']
        low_findings = [f for f in self.findings if f['severity'] == 'low']
        
        print(f"\n发现的问题:")
        print(f"  🔴 高风险: {len(high_findings)} 个")
        print(f"  🟡 中风险: {len(medium_findings)} 个")
        print(f"  🟢 低风险: {len(low_findings)} 个")
        
        if high_findings:
            print("\n🔴 高风险问题:")
            for finding in high_findings:
                print(f"  • {finding.get('file', '未知文件')}")
                print(f"    类型: {finding['type']}")
                if 'keyword' in finding:
                    print(f"    关键词: {finding['keyword']}")
                if 'note' in finding:
                    print(f"    说明: {finding['note']}")
                print()
        
        if medium_findings:
            print("\n🟡 中风险问题:")
            for finding in medium_findings:
                print(f"  • {finding.get('file', '未知文件')}")
                print(f"    类型: {finding['type']}")
                if 'keyword' in finding:
                    print(f"    关键词: {finding['keyword']}")
                if 'note' in finding:
                    print(f"    说明: {finding['note']}")
                print()
        
        if low_findings:
            print("\n🟢 低风险问题:")
            for finding in low_findings:
                print(f"  • {finding.get('file', '未知文件')}")
                print(f"    类型: {finding['type']}")
                if 'note' in finding:
                    print(f"    说明: {finding['note']}")
                print()
        
        # 提供建议
        print("\n💡 建议:")
        if high_findings:
            print("  ❗ 存在高风险问题，建议在安装前修复")
            return False
        elif medium_findings:
            print("  ⚠️  存在中风险问题，建议审查后再使用")
            return True
        else:
            print("  ✅ 只有低风险或无风险问题，可以安全使用")
            return True
    
    def print_ccpa_specific_advice(self):
        """打印CCPA特定的建议"""
        print("\n" + "="*60)
        print("🚀 CCPA合规安装和使用建议")
        print("="*60)
        
        print("""
1. 📋 CCPA特定检查
   - 确认工具包含完整的CCPA/CPRA法规参考
   - 验证消费者权利检查功能
   - 检查数据销售选择退出机制
   - 确认包含敏感个人信息处理检查

2. 🛡️ CCPA安全使用建议
   - 始终在受控环境下运行CCPA检查
   - 确保不包含敏感消费者数据的测试
   - 验证所有CCPA合规逻辑
   - 关注加州隐私法规更新

3. 🔧 CCPA环境要求
   - 了解加州消费者隐私要求
   - 准备律师联系方式
   - 了解其他州隐私法规差异
   - 准备数据销售选择退出机制

4. ⚖️ CCPA法律注意事项
   - 本工具仅供CCPA合规辅助参考
   - 重大CCPA合规决策必须咨询律师
   - 数据销售需提供清晰选择退出机制
   - 消费者权利请求需在规定时间内响应
""")


def main():
    """主函数"""
    print("🔐 CCPA Compliance - 安全检查")
    print("="*60)
    
    checker = SecurityCheckerCCPA()
    
    # 运行所有检查
    checker.check_python_files()
    checker.check_requirements()
    checker.check_skill_md()
    checker.check_ccpa_references()
    checker.run_ccpa_functional_tests()
    
    # 生成报告
    is_safe = checker.generate_report()
    
    # 打印建议
    checker.print_ccpa_specific_advice()
    
    # 返回退出码
    return 0 if is_safe else 1


if __name__ == "__main__":
    sys.exit(main())