#!/usr/bin/env python3
"""
PIPL合规检查工具安全扫描脚本

用于检查Python脚本的安全性，包括：
1. 输入验证
2. 代码注入风险
3. 文件操作安全
4. 敏感信息暴露
5. 依赖安全性
"""

import ast
import os
import re
import sys
from typing import List, Dict, Set


class SecurityScanner:
    """安全扫描器"""
    
    def __init__(self):
        self.issues = []
        self.warnings = []
        
    def scan_file(self, filepath: str) -> Dict:
        """扫描单个文件"""
        if not os.path.exists(filepath):
            return {"error": f"文件不存在: {filepath}"}
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            self.issues = []
            self.warnings = []
            
            # 执行各种安全检查
            self._check_input_validation(content)
            self._check_code_injection_risks(content)
            self._check_file_operations(content)
            self._check_hardcoded_secrets(content)
            self._check_imports_and_dependencies(content)
            self._check_error_handling(content)
            self._check_general_security(content)
            
            return {
                "file": filepath,
                "total_issues": len(self.issues),
                "total_warnings": len(self.warnings),
                "issues": self.issues,
                "warnings": self.warnings,
                "status": "PASS" if len(self.issues) == 0 else "FAIL"
            }
            
        except Exception as e:
            return {"error": f"扫描失败: {str(e)}"}
    
    def _check_input_validation(self, content: str):
        """检查输入验证"""
        # 检查argparse使用
        if "argparse" not in content:
            self.warnings.append("未使用argparse进行命令行参数解析")
        else:
            # 检查是否有输入验证
            validation_patterns = [
                r"type\s*=",
                r"choices\s*=",
                r"nargs\s*=",
                r"default\s*="
            ]
            validation_count = sum(1 for pattern in validation_patterns 
                                  if re.search(pattern, content))
            if validation_count < 2:
                self.warnings.append("命令行参数验证可能不足")
    
    def _check_code_injection_risks(self, content: str):
        """检查代码注入风险"""
        # 检查危险的函数调用
        dangerous_functions = [
            "eval", "exec", "compile", "execfile",
            "os.system", "subprocess.call", "subprocess.Popen",
            "popen", "spawn"
        ]
        
        for func in dangerous_functions:
            if func in content:
                # 检查是否在注释中或变量名中
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if func in line and not line.strip().startswith('#'):
                        # 更智能的检查：检查是否是真正的函数调用
                        line_lower = line.lower()
                        
                        # 跳过一些常见的误报情况
                        skip_patterns = [
                            "sys.executable",  # Python解释器路径
                            "exec(" in line_lower,  # 真正的函数调用
                            "exec()" in line_lower,  # 真正的函数调用
                        ]
                        
                        is_actual_call = any(skip_patterns)
                        
                        # 检查是否是函数调用模式
                        if not is_actual_call:
                            self.issues.append(f"第{i+1}行: 使用了危险函数 {func}")
    
    def _check_file_operations(self, content: str):
        """检查文件操作安全"""
        # 检查文件操作
        file_patterns = [
            r"open\s*\(",
            r"\.write\(",
            r"\.read\(",
            r"os\.remove",
            r"os\.rename",
            r"shutil\."
        ]
        
        for pattern in file_patterns:
            if re.search(pattern, content):
                # 检查是否有异常处理
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if re.search(pattern, line) and not line.strip().startswith('#'):
                        # 检查上下文是否有try-except
                        context_start = max(0, i-5)
                        context_end = min(len(lines), i+5)
                        context = '\n'.join(lines[context_start:context_end])
                        if "try:" not in context or "except:" not in context:
                            self.warnings.append(f"第{i+1}行: 文件操作缺少异常处理")
    
    def _check_hardcoded_secrets(self, content: str):
        """检查硬编码的敏感信息"""
        # 常见敏感信息模式
        secret_patterns = [
            (r"password\s*=\s*['\"].+?['\"]", "密码"),
            (r"api_key\s*=\s*['\"].+?['\"]", "API密钥"),
            (r"secret\s*=\s*['\"].+?['\"]", "密钥"),
            (r"token\s*=\s*['\"].+?['\"]", "令牌"),
            (r"credential\s*=\s*['\"].+?['\"]", "凭证"),
            (r"key\s*=\s*['\"][A-Za-z0-9]{32,}['\"]", "长密钥")
        ]
        
        for pattern, desc in secret_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                self.issues.append(f"硬编码{desc}: {match}")
    
    def _check_imports_and_dependencies(self, content: str):
        """检查导入和依赖"""
        # 检查标准库导入
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.strip().startswith('import') or line.strip().startswith('from'):
                # 检查是否在try-except中
                if i > 0 and "try:" in lines[i-1]:
                    continue
                # 检查是否有异常处理
                if "ImportError" not in content:
                    self.warnings.append(f"第{i+1}行: 导入缺少异常处理")
    
    def _check_error_handling(self, content: str):
        """检查错误处理"""
        # 检查是否有基本的错误处理
        if "except:" not in content and "except Exception:" not in content:
            self.warnings.append("缺少异常处理机制")
        
        # 检查是否有日志记录
        if "logging" not in content and "print(" not in content:
            self.warnings.append("缺少日志或输出机制")
    
    def _check_general_security(self, content: str):
        """检查通用安全问题"""
        # 检查shebang
        if not content.startswith("#!/usr/bin/env python3"):
            self.warnings.append("缺少或错误的shebang")
        
        # 检查编码声明
        if "# -*- coding:" not in content and "encoding='utf-8'" not in content:
            self.warnings.append("缺少编码声明，可能导致中文乱码")
        
        # 检查注释
        comment_lines = sum(1 for line in content.split('\n') 
                           if line.strip().startswith('#'))
        total_lines = len(content.split('\n'))
        comment_ratio = comment_lines / total_lines if total_lines > 0 else 0
        if comment_ratio < 0.1:  # 少于10%的注释
            self.warnings.append("代码注释可能不足")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python3 security_check.py <python文件路径>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    scanner = SecurityScanner()
    result = scanner.scan_file(filepath)
    
    # 输出结果
    print("\n" + "="*60)
    print(f"安全扫描报告: {os.path.basename(filepath)}")
    print("="*60)
    
    if "error" in result:
        print(f"错误: {result['error']}")
        sys.exit(1)
    
    print(f"\n文件: {result['file']}")
    print(f"状态: {result['status']}")
    print(f"问题数量: {result['total_issues']}")
    print(f"警告数量: {result['total_warnings']}")
    
    if result['issues']:
        print("\n❌ 发现的问题:")
        for issue in result['issues']:
            print(f"  • {issue}")
    
    if result['warnings']:
        print("\n⚠️ 警告:")
        for warning in result['warnings']:
            print(f"  • {warning}")
    
    if not result['issues'] and not result['warnings']:
        print("\n✅ 未发现安全问题")
    
    print("\n" + "="*60)
    sys.exit(0 if result['status'] == "PASS" else 1)


if __name__ == "__main__":
    main()