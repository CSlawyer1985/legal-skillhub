"""测试 Word 批注功能"""

import sys
from pathlib import Path

# 添加服务目录到路径
sys.path.insert(0, str(Path(__file__).parent / "services"))

from contract_auditor import audit_with_word_annotation


def test_word_annotation():
    """测试 Word 批注功能"""
    # 检查测试文件
    test_dir = Path(__file__).parent / "tests" / "test_contracts"
    
    # 查找测试用的 Word 文件
    word_files = list(test_dir.glob("*.docx")) + list(test_dir.glob("*.doc"))
    
    if not word_files:
        print("未找到测试用的 Word 文件")
        print(f"请在 {test_dir} 目录下放置 .docx 或 .doc 文件进行测试")
        return
    
    for word_file in word_files:
        print(f"\n{'='*60}")
        print(f"测试文件: {word_file.name}")
        print(f"{'='*60}")
        
        try:
            # 执行审计并添加 Word 批注
            audit_report, output_path = audit_with_word_annotation(
                input_path=str(word_file),
                output_path=str(test_dir / f"{word_file.stem}_annotated{word_file.suffix}")
            )
            
            # 打印审计报告
            print("\n【审计报告】")
            print(audit_report[:500] + "..." if len(audit_report) > 500 else audit_report)
            
            # 检查结果
            if output_path:
                print(f"\n✅ Word 批注文档已生成: {output_path}")
            else:
                print("\n❌ Word 批注生成失败")
                
        except Exception as e:
            print(f"\n❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    test_word_annotation()
