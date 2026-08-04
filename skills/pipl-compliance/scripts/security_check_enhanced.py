#!/usr/bin/env python3
"""
PIPL Compliance - 增强版安全检查脚本
用于验证技能的安全性和纯本地运行特性
"""

import os
import sys
import re
import subprocess
from pathlib import Path

class SecurityChecker:
    """安全检查器"""
    
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.project_root = self.script_dir.parent
        
        # 网络调用关键词
        self.network_keywords = [
            'import requests', 'import urllib', 'import http', 'import socket',
            'import ftplib', 'import aiohttp', 'import paramiko',
            'requests.get', 'requests.post', 'urllib.request',
            'http.client', 'socket.socket', 'subprocess.run.*curl',
            'subprocess.run.*wget', 'subprocess.Popen.*curl',
            'subprocess.Popen.*wget'
        ]
        
        # 自动更新/上报关键词
        self.update_keywords = [
            'check_for_updates', 'auto_update', 'telemetry',
            'upload.*data', 'post.*data', 'send.*report',
            'external.*api', 'api.*endpoint', 'webhook',
            'callback.*url', 'report.*server'
        ]
        
        # 外部URL模式
        self.url_patterns = [
            r'http://[^\s"\']+',
            r'https://[^\s"\']+',
            r'ftp://[^\s"\']+',
            r'ws://[^\s"\']+',
            r'wss://[^\s"\']+'
        ]
        
        self.findings = []
    
    def check_python_files(self):
        """检查所有Python文件"""
        print("🔍 检查Python文件...")
        
        python_files = list(self.script_dir.rglob("*.py"))
        print(f"  发现 {len(python_files)} 个Python文件")
        
        for file_path in python_files:
            relative_path = file_path.relative_to(self.project_root)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 检查网络调用
                for keyword in self.network_keywords:
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
                        
            except Exception as e:
                print(f"  警告: 无法检查文件 {relative_path}: {e}")
        
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
        
        print(f"  完成依赖文件检查")
    
    def check_package_json(self):
        """检查package.json"""
        print("🔍 检查package.json...")
        
        pkg_file = self.project_root / 'package.json'
        if pkg_file.exists():
            with open(pkg_file, 'r') as f:
                content = f.read()
            
            # 检查外部URL
            for pattern in self.url_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    self.findings.append({
                        'file': 'package.json',
                        'type': 'metadata_url',
                        'url': match,
                        'severity': 'low',
                        'note': '这是元数据URL，通常可以接受'
                    })
        
        print(f"  完成package.json检查")
    
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
        
        print(f"  完成SKILL.md检查")
    
    def run_quick_test(self):
        """运行快速测试"""
        print("🔍 运行快速测试...")
        
        test_commands = [
            ['python', str(self.script_dir / 'pipl-check.py'), '--help'],
            ['python', str(self.script_dir / 'risk-assessment.py'), '--help'],
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
        
        print(f"  完成快速测试")
    
    def generate_report(self):
        """生成检查报告"""
        print("\n" + "="*60)
        print("📋 安全检查报告")
        print("="*60)
        
        if not self.findings:
            print("✅ 所有检查通过！")
            print("\n🎉 技能看起来是安全的，符合纯本地运行的要求")
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
    
    def print_installation_advice(self):
        """打印安装建议"""
        print("\n" + "="*60)
        print("🚀 安装和使用建议")
        print("="*60)
        
        print("""
1. 📋 安装前检查
   - 在隔离环境中安装和测试
   - 使用网络监控工具观察外向流量
   - 先用样本数据测试，再使用真实数据

2. 🛡️ 安全使用建议
   - 始终在受控环境下运行
   - 定期进行安全检查
   - 关注安全更新和漏洞报告

3. 🔧 环境要求
   - Python 3.8+
   - 依赖包: pandas>=2.0.0, jinja2>=3.1.0
   - 本地运行，无需网络连接

4. ⚠️ 重要提醒
   - 本工具仅供辅助参考，不构成法律建议
   - 重大决策请咨询专业律师
   - 用户对使用后果负全责
""")

def main():
    """主函数"""
    print("🔐 PIPL Compliance - 增强版安全检查")
    print("="*60)
    
    checker = SecurityChecker()
    
    # 运行所有检查
    checker.check_python_files()
    checker.check_requirements()
    checker.check_package_json()
    checker.check_skill_md()
    checker.run_quick_test()
    
    # 生成报告
    is_safe = checker.generate_report()
    
    # 打印建议
    checker.print_installation_advice()
    
    # 返回退出码
    return 0 if is_safe else 1

if __name__ == "__main__":
    sys.exit(main())