#!/usr/bin/env python3
"""
专利撰写辅助脚本
Patent Draft Helper

功能：根据技术交底书自动生成专利申请文件初稿
- 权利要求书
- 说明书框架
- 摘要

使用方法：
    python patent-draft-helper.py

作者：OPC知识产权助手
版本：v1.0
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional

# ============================================================
# 配置区域
# ============================================================

OUTPUT_DIR = "./output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================
# 模板定义
# ============================================================

CLAIM_TEMPLATE = """# 权利要求书

## 技术领域
本专利涉及{tech_field}领域，具体涉及{topic}。

## 背景技术
{background}

现有技术存在的问题：
{problem}

## 发明内容
本发明的目的是提供一种{topic}，以解决上述技术问题。

为实现上述目的，本发明采用以下技术方案：

{claims_content}

本发明具有以下有益效果：
{effects}

## 附图说明
本发明包含以下附图：
{figures}

## 具体实施方式
实施例1：
{implementation}

---

*本权利要求书由AI辅助生成，建议在专业代理人指导下修改完善。*
"""

CLAIM_ITEM_TEMPLATE = """
### 权利要求 {num}
{claim_text}
"""

INDEPENDENT_CLAIM_TEMPLATE = """
#### 独立权利要求 {num}
一种{topic}，其特征在于：
{features}
"""

DEPENDENT_CLAIM_TEMPLATE = """
#### 从属权利要求 {num}
根据权利要求{referenced}所述的{topic}，其特征在于：
{features}
"""

# ============================================================
# 核心功能
# ============================================================

class PatentDraftGenerator:
    """专利文稿生成器"""
    
    def __init__(self):
        self.data = {}
    
    def load_technical_brief(self, brief_data: Dict) -> None:
        """
        加载技术交底书
        
        Args:
            brief_data: 技术交底书数据字典
        """
        self.data = brief_data
        print(f"✓ 已加载技术交底书：{brief_data.get('title', '未命名')}")
    
    def load_from_file(self, filepath: str) -> bool:
        """
        从文件加载技术交底书
        
        Args:
            filepath: 文件路径
            
        Returns:
            bool: 是否加载成功
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            print(f"✓ 已从文件加载：{filepath}")
            return True
        except Exception as e:
            print(f"✗ 加载失败：{e}")
            return False
    
    def generate_claims(self) -> str:
        """
        生成权利要求书
        
        Returns:
            str: 权利要求书文本
        """
        title = self.data.get('title', '未命名')
        tech_field = self.data.get('tech_field', '相关技术')
        background = self.data.get('background', '暂无')
        problem = self.data.get('problem', '暂无')
        key_features = self.data.get('key_features', [])
        effects = self.data.get('effects', [])
        figures = self.data.get('figures', [])
        implementation = self.data.get('implementation', '暂无')
        
        # 生成独立权利要求
        claims = []
        claim_num = 1
        
        # 独立权利要求1
        if key_features:
            features_text = '\n'.join([f"- {f}" for f in key_features[:5]])
            independent = INDEPENDENT_CLAIM_TEMPLATE.format(
                num=claim_num,
                topic=title,
                features=features_text
            )
            claims.append(independent)
            claim_num += 1
        
        # 生成从属权利要求
        for i, feature in enumerate(key_features[5:10], start=2):
            dependent = DEPENDENT_CLAIM_TEMPLATE.format(
                num=claim_num,
                referenced=1,
                topic=title,
                features=f"- {feature}"
            )
            claims.append(dependent)
            claim_num += 1
        
        claims_content = '\n'.join(claims)
        
        # 生成有益效果
        effects_text = '\n'.join([f"{i+1}. {e}" for i, e in enumerate(effects)]) if effects else "待补充"
        
        # 生成附图说明
        figures_text = '\n'.join([f"- 图{i+1}：{f}" for i, f in enumerate(figures)]) if figures else "待补充"
        
        # 格式化输出
        claims_output = CLAIM_TEMPLATE.format(
            tech_field=tech_field,
            topic=title,
            background=background,
            problem=problem,
            claims_content=claims_content,
            effects=effects_text,
            figures=figures_text,
            implementation=implementation if implementation else "详见本领域技术人员根据上述技术方案的具体实施方式。"
        )
        
        return claims_output
    
    def generate_specification(self) -> str:
        """
        生成说明书框架
        
        Returns:
            str: 说明书文本
        """
        title = self.data.get('title', '未命名')
        tech_field = self.data.get('tech_field', '相关技术')
        background = self.data.get('background', '暂无')
        problem = self.data.get('problem', '暂无')
        key_features = self.data.get('key_features', [])
        effects = self.data.get('effects', [])
        implementation = self.data.get('implementation', '暂无')
        
        spec = f"""# 说明书

## 技术领域
本发明涉及{tech_field}领域，具体涉及一种{title}。

## 背景技术
{background}

然而，现有的{tech_field}技术存在以下问题：
{problem}

本发明的设计旨在解决上述技术问题。

## 发明内容
本发明的目的是提供一种{title}，以解决上述问题。

### 技术方案
"""
        # 添加技术方案
        if key_features:
            spec += "\n本发明采用以下技术方案：\n"
            for i, feature in enumerate(key_features, 1):
                spec += f"{i}. {feature}\n"
        
        spec += "\n### 有益效果\n"
        if effects:
            for i, effect in enumerate(effects, 1):
                spec += f"{i}. {effect}\n"
        else:
            spec += "待补充本发明的有益效果。\n"
        
        spec += "\n## 附图说明\n"
        spec += "图1为本发明的整体结构示意图；\n"
        spec += "图2为本发明的工作流程图；\n"
        spec += "图3为本发明的关键部件放大图。\n"
        
        spec += "\n## 具体实施方式\n"
        if implementation:
            spec += f"{implementation}\n"
        else:
            spec += """以下结合附图对本发明的具体实施方式进行详细说明。

实施例1：
如图1所示，一种{title}，包括[部件A]、[部件B]、[部件C]...
[具体描述技术方案的实现方式]

使用时，[描述使用过程]
与现有技术相比，本实施例具有以下优点：
1. [优点1]
2. [优点2]
3. [优点3]
""".format(title=title)
        
        spec += "\n---\n*本说明书由AI辅助生成，建议在专业代理人指导下修改完善。*\n"
        
        return spec
    
    def generate_abstract(self) -> str:
        """
        生成摘要
        
        Returns:
            str: 摘要文本
        """
        title = self.data.get('title', '未命名')
        tech_field = self.data.get('tech_field', '相关技术')
        key_features = self.data.get('key_features', [])
        effects = self.data.get('effects', [])
        
        # 提取关键技术特征（摘要通常300字以内）
        features_text = '；'.join(key_features[:3]) if key_features else '待补充关键技术特征'
        effects_text = '；'.join(effects[:2]) if effects else '待补充有益效果'
        
        abstract = f"""# 摘要

本发明公开了一种{title}，属于{tech_field}领域。该{title}包括关键技术特征：{features_text}。与现有技术相比，本发明具有以下有益效果：{effects_text}。本发明可用于{tech_field}领域的实际应用。

*本摘要由AI辅助生成，建议根据最终权利要求书调整。*
"""
        
        return abstract
    
    def generate_full_draft(self) -> Dict[str, str]:
        """
        生成完整的专利申请文件初稿
        
        Returns:
            Dict: 包含各部分文稿的字典
        """
        return {
            '权利要求书': self.generate_claims(),
            '说明书': self.generate_specification(),
            '摘要': self.generate_abstract()
        }
    
    def save_draft(self, output_dir: str = None) -> Dict[str, str]:
        """
        保存生成的文稿
        
        Args:
            output_dir: 输出目录
            
        Returns:
            Dict: 保存的文件路径
        """
        if output_dir is None:
            output_dir = OUTPUT_DIR
        
        os.makedirs(output_dir, exist_ok=True)
        
        draft = self.generate_full_draft()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        saved_files = {}
        
        for name, content in draft.items():
            filename = f"{self.data.get('title', 'patent')}_{name}_{timestamp}.md"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            saved_files[name] = filepath
            print(f"✓ 已保存：{filepath}")
        
        return saved_files


def interactive_input() -> Dict:
    """
    交互式输入技术交底书
    
    Returns:
        Dict: 技术交底书数据
    """
    print("\n" + "="*60)
    print("专利申请辅助工具 - 技术交底书输入")
    print("="*60)
    
    brief = {}
    
    print("\n【基本信息】")
    brief['title'] = input("1. 发明名称：").strip() or "未命名"
    brief['tech_field'] = input("2. 技术领域：").strip() or "相关技术领域"
    
    print("\n【背景技术】")
    brief['background'] = input("3. 背景技术描述（现有技术现状）：\n").strip() or "暂无"
    brief['problem'] = input("4. 现有技术存在的问题：\n").strip() or "暂无"
    
    print("\n【技术方案】")
    print("5. 关键技术特征（输入完成后按回车）：")
    key_features = []
    while True:
        feature = input("   - ").strip()
        if not feature:
            break
        key_features.append(feature)
    brief['key_features'] = key_features if key_features else []
    
    print("\n【有益效果】")
    print("6. 有益效果（输入完成后按回车）：")
    effects = []
    while True:
        effect = input("   - ").strip()
        if not effect:
            break
        effects.append(effect)
    brief['effects'] = effects if effects else []
    
    print("\n【其他信息】")
    print("7. 附图说明（如有）：")
    figures = []
    while True:
        fig = input("   - ").strip()
        if not fig:
            break
        figures.append(fig)
    brief['figures'] = figures if figures else []
    
    brief['implementation'] = input("8. 最佳实施方式（可选）：\n").strip()
    
    return brief


def demo_example() -> Dict:
    """
    提供示例数据
    
    Returns:
        Dict: 示例技术交底书
    """
    return {
        "title": "智能水杯",
        "tech_field": "智能家居",
        "background": "现有的水杯只能盛装液体，无法实时监测饮水量和水温，用户难以养成良好的饮水习惯。",
        "problem": "1. 无法提醒用户及时饮水\n2. 无法监测饮水量\n3. 无法显示水温，存在烫伤风险",
        "key_features": [
            "杯体内置温度传感器，实时监测水温",
            "杯体设置液位传感器，监测饮水量",
            "配合APP记录饮水数据，分析饮水习惯",
            "设置饮水提醒功能，定时提醒用户饮水",
            "显示屏实时显示水温和剩余容量",
            "杯体采用食品级不锈钢材质",
            "支持无线充电，续航可达30天"
        ],
        "effects": [
            "帮助用户养成良好的饮水习惯",
            "避免饮水温度过高导致烫伤",
            "通过数据追踪提升饮水健康"
        ],
        "figures": [
            "图1-整体结构示意图",
            "图2-传感器布局图",
            "图3-APP界面示意图"
        ],
        "implementation": "实施例1：\n智能水杯包括杯体1、杯盖2、控制器3、温度传感器4、液位传感器5、显示屏6和锂电池7。\n温度传感器4设置在杯体1底部，液位传感器5设置在杯体1内壁。\n控制器3与各传感器和显示屏6电连接，接收传感器数据并控制显示屏显示。\n用户通过APP设置饮水目标，控制器根据液位传感器数据计算已饮用量。\n当达到饮水时间但饮用量不足时，控制器触发提醒功能。"
    }


# ============================================================
# 主程序
# ============================================================

def main():
    """主函数"""
    print("\n" + "="*60)
    print("🔧 专利申请辅助工具 v1.0")
    print("="*60)
    
    generator = PatentDraftGenerator()
    
    print("\n请选择输入方式：")
    print("1. 使用示例数据演示")
    print("2. 交互式输入技术交底书")
    print("3. 从JSON文件加载")
    
    choice = input("\n请输入选项 (1/2/3)：").strip()
    
    if choice == '1':
        print("\n正在加载示例数据...")
        brief = demo_example()
        generator.load_technical_brief(brief)
        
    elif choice == '2':
        brief = interactive_input()
        generator.load_technical_brief(brief)
        
    elif choice == '3':
        filepath = input("请输入JSON文件路径：").strip()
        if not generator.load_from_file(filepath):
            print("加载失败，将使用示例数据。")
            brief = demo_example()
            generator.load_technical_brief(brief)
    else:
        print("无效选项，将使用示例数据。")
        brief = demo_example()
        generator.load_technical_brief(brief)
    
    print("\n" + "-"*60)
    print("正在生成专利申请文件...")
    print("-"*60)
    
    # 生成并显示各部分
    draft = generator.generate_full_draft()
    
    for name, content in draft.items():
        print(f"\n{'='*60}")
        print(f"【{name}】")
        print('='*60)
        print(content)
    
    # 保存文件
    print("\n" + "-"*60)
    save = input("是否保存文件？(y/n)：").strip().lower()
    if save == 'y':
        saved = generator.save_draft()
        print(f"\n✓ 已保存 {len(saved)} 个文件到 {OUTPUT_DIR} 目录")
    
    print("\n" + "="*60)
    print("⚠️  提示：本工具生成的仅为初稿，建议：")
    print("   1. 仔细核对技术方案的准确性")
    print("   2. 在专业代理人的指导下修改完善")
    print("   3. 申请前进行专利查新检索")
    print("="*60)


if __name__ == "__main__":
    main()
