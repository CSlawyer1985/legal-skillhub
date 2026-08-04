#!/usr/bin/env python3
"""
专利文档整理脚本
用于创建项目目录结构和整理文件
"""

import os
import shutil
from pathlib import Path
from typing import List
import json


def create_patent_project_structure(base_path: str, patent_title: str) -> dict:
    """
    创建专利项目目录结构
    
    Args:
        base_path: 基础路径(如 /opt/www/pattern/docs)
        patent_title: 专利标题
    
    Returns:
        创建的目录路径字典
    """
    # 清理标题,用作目录名
    safe_title = "".join(c for c in patent_title if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_title = safe_title.replace(' ', '_')
    
    project_root = Path(base_path) / safe_title
    
    # 定义目录结构
    directories = {
        'root': project_root,
        'search_report': project_root / '检索报告',
        'tech_solution': project_root / '技术方案',
        'charts': project_root / '技术方案' / '对比图表',
        'references': project_root / '参考资料',
        'patents': project_root / '参考资料' / '相关专利全文',
        'literature': project_root / '参考资料' / '技术文献'
    }
    
    # 创建所有目录
    for name, path in directories.items():
        path.mkdir(parents=True, exist_ok=True)
        print(f"✓ 创建目录: {path}")
    
    return {k: str(v) for k, v in directories.items()}


def generate_readme(patent_title: str, output_path: str):
    """
    生成项目README文件
    
    Args:
        patent_title: 专利标题
        output_path: 输出路径
    """
    readme_content = f"""# {patent_title}

## 项目概述

本目录包含专利挖掘和交底书撰写的完整资料。

## 目录结构

```
{patent_title}/
├── 专利交底书.md              # 主文档
├── 专利交底书.docx            # Word格式(可选)
├── 检索报告/
│   ├── 检索结果汇总.xlsx      # 专利列表
│   ├── 重点专利分析.pdf       # 对比分析
│   └── 技术趋势报告.pdf       # 趋势分析
├── 技术方案/
│   ├── 系统架构图.png
│   ├── 流程图.png
│   └── 对比图表/
│       ├── 性能对比.png
│       └── 效果分析.png
├── 参考资料/
│   ├── 相关专利全文/
│   └── 技术文献/
└── README.md                  # 本文件
```

## 文档说明

### 专利交底书.md
专利申请技术交底书主文档,包含:
- 背景技术
- 发明内容
- 具体实施方式
- 权利要求建议

### 检索报告/
专利检索和分析相关文档:
- 检索结果汇总: 包含所有相关专利的基本信息
- 重点专利分析: 核心专利的详细对比分析
- 技术趋势报告: 技术发展趋势和市场分析

### 技术方案/
技术方案相关图表:
- 系统架构图: 技术方案整体架构
- 流程图: 关键技术流程
- 对比图表: 性能和效果对比可视化

### 参考资料/
支撑材料:
- 相关专利全文: 重点参考专利原文
- 技术文献: 相关技术文档和论文

## 更新日志

- {__import__('datetime').datetime.now().strftime('%Y-%m-%d')}: 项目初始化

## 备注

如有问题,请联系专利挖掘智能体专家。
"""
    
    readme_path = Path(output_path) / "README.md"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"✓ 生成README: {readme_path}")


def copy_template_file(template_path: str, dest_path: str, new_name: str = None):
    """
    复制模版文件到目标目录
    
    Args:
        template_path: 模版文件路径
        dest_path: 目标目录
        new_name: 新文件名(可选)
    """
    template = Path(template_path)
    dest = Path(dest_path)
    
    if not template.exists():
        print(f"⚠ 模版文件不存在: {template_path}")
        return False
    
    if new_name:
        dest_file = dest / new_name
    else:
        dest_file = dest / template.name
    
    shutil.copy2(template, dest_file)
    print(f"✓ 复制文件: {template} -> {dest_file}")
    return True


def save_search_results(results: List[dict], output_path: str, filename: str = "检索结果汇总.json"):
    """
    保存检索结果到JSON文件
    
    Args:
        results: 检索结果列表
        output_path: 输出目录
        filename: 文件名
    """
    output_file = Path(output_path) / filename
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 保存检索结果: {output_file}")


def generate_patent_summary(patent_data: dict, output_path: str):
    """
    生成专利摘要卡片
    
    Args:
        patent_data: 专利数据字典
        output_path: 输出路径
    """
    summary = f"""# 专利摘要卡片

## 基本信息

- **专利号**: {patent_data.get('patent_number', '未知')}
- **标题**: {patent_data.get('title', '未知')}
- **申请人**: {patent_data.get('applicant', '未知')}
- **发明人**: {patent_data.get('inventor', '未知')}
- **申请日**: {patent_data.get('application_date', '未知')}
- **公开日**: {patent_data.get('publication_date', '未知')}
- **IPC分类号**: {patent_data.get('ipc', '未知')}

## 技术摘要

{patent_data.get('abstract', '暂无摘要')}

## 权利要求

{patent_data.get('claims', '暂无权利要求信息')}

## 技术要点

{patent_data.get('key_points', '待分析')}

## 与本申请的关联

{patent_data.get('relevance', '待分析')}
"""
    
    output_file = Path(output_path) / f"{patent_data.get('patent_number', 'unknown')}_摘要.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(summary)
    
    print(f"✓ 生成摘要卡片: {output_file}")


if __name__ == "__main__":
    print("专利文档整理工具")
    print("=" * 50)
    
    # 示例用法
    base_path = "/opt/www/pattern/docs"
    patent_title = "基于深度学习的图像识别方法"
    
    # 创建目录结构
    directories = create_patent_project_structure(base_path, patent_title)
    print(f"\n项目目录已创建: {directories['root']}")
    
    # 生成README
    generate_readme(patent_title, directories['root'])
    
    # 保存示例检索结果
    sample_results = [
        {
            "patent_number": "CN12345678A",
            "title": "一种图像识别方法",
            "applicant": "某某科技有限公司",
            "application_date": "2023-01-15"
        },
        {
            "patent_number": "CN87654321A",
            "title": "深度学习图像处理系统",
            "applicant": "某某研究院",
            "application_date": "2023-03-20"
        }
    ]
    save_search_results(sample_results, directories['search_report'])
    
    print("\n项目初始化完成!")
