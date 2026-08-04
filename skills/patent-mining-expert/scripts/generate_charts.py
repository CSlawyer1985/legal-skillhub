#!/usr/bin/env python3
"""
专利数据可视化脚本
用于生成专业的专利分析图表
"""

import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from typing import List, Dict, Tuple
import json

# 设置中文字体
matplotlib.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'PingFang SC']
matplotlib.rcParams['axes.unicode_minus'] = False

# 专利文档配色方案(专业简洁风格)
PATENT_COLORS = {
    'primary': '#2E5090',      # 深蓝
    'secondary': '#5B9BD5',    # 浅蓝
    'accent': '#ED7D31',       # 橙色
    'comparison': '#70AD47',   # 绿色
    'background': '#F2F2F2',   # 浅灰
    'text': '#404040'          # 深灰
}


def create_performance_comparison(
    methods: List[str],
    metrics: Dict[str, List[float]],
    title: str = "性能对比图",
    output_file: str = "performance_comparison.png",
    figsize: Tuple[int, int] = (12, 6)
):
    """
    创建性能对比柱状图
    
    Args:
        methods: 方法名称列表
        metrics: 指标字典 {指标名: [各方法的值]}
        title: 图表标题
        output_file: 输出文件名
        figsize: 图表尺寸
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    x = np.arange(len(methods))
    width = 0.15
    multiplier = 0
    
    colors = [PATENT_COLORS['primary'], PATENT_COLORS['secondary'], 
              PATENT_COLORS['accent'], PATENT_COLORS['comparison']]
    
    for idx, (metric, values) in enumerate(metrics.items()):
        offset = width * multiplier
        bars = ax.bar(x + offset, values, width, label=metric, 
                     color=colors[idx % len(colors)], alpha=0.8)
        
        # 添加数值标签
        ax.bar_label(bars, padding=3, fontsize=9, fmt='%.1f')
        multiplier += 1
    
    ax.set_xlabel('技术方案', fontsize=11, color=PATENT_COLORS['text'])
    ax.set_ylabel('性能指标', fontsize=11, color=PATENT_COLORS['text'])
    ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
    ax.set_xticks(x + width * (len(metrics) - 1) / 2)
    ax.set_xticklabels(methods)
    ax.legend(loc='upper right', framealpha=0.9)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_facecolor(PATENT_COLORS['background'])
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"图表已保存: {output_file}")


def create_trend_line(
    years: List[int],
    patent_counts: List[int],
    title: str = "专利申请趋势图",
    output_file: str = "trend_line.png",
    figsize: Tuple[int, int] = (10, 6)
):
    """
    创建专利申请趋势折线图
    
    Args:
        years: 年份列表
        patent_counts: 专利数量列表
        title: 图表标题
        output_file: 输出文件名
        figsize: 图表尺寸
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    ax.plot(years, patent_counts, marker='o', linewidth=2.5, 
           color=PATENT_COLORS['primary'], markersize=8,
           markerfacecolor=PATENT_COLORS['accent'],
           markeredgecolor=PATENT_COLORS['primary'],
           markeredgewidth=2)
    
    # 填充区域
    ax.fill_between(years, patent_counts, alpha=0.2, color=PATENT_COLORS['secondary'])
    
    # 标注关键点
    for x, y in zip(years, patent_counts):
        ax.annotate(f'{y}', xy=(x, y), xytext=(0, 10),
                   textcoords='offset points', ha='center', fontsize=9)
    
    ax.set_xlabel('年份', fontsize=11, color=PATENT_COLORS['text'])
    ax.set_ylabel('专利申请数量', fontsize=11, color=PATENT_COLORS['text'])
    ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_facecolor(PATENT_COLORS['background'])
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"图表已保存: {output_file}")


def create_radar_chart(
    categories: List[str],
    values_list: List[List[float]],
    labels: List[str],
    title: str = "技术效果雷达图",
    output_file: str = "radar_chart.png",
    figsize: Tuple[int, int] = (8, 8)
):
    """
    创建技术效果雷达图
    
    Args:
        categories: 维度类别
        values_list: 多组数值(用于对比)
        labels: 各组数据的标签
        title: 图表标题
        output_file: 输出文件名
        figsize: 图表尺寸
    """
    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    
    fig, ax = plt.subplots(figsize=figsize, subplot_kw=dict(projection='polar'))
    
    colors = [PATENT_COLORS['primary'], PATENT_COLORS['accent'], 
              PATENT_COLORS['comparison']]
    
    for idx, (values, label) in enumerate(zip(values_list, labels)):
        values_plot = values + [values[0]]  # 闭合
        angles_plot = angles + [angles[0]]
        
        ax.plot(angles_plot, values_plot, 'o-', linewidth=2.5,
               label=label, color=colors[idx % len(colors)])
        ax.fill(angles_plot, values_plot, alpha=0.15, color=colors[idx % len(colors)])
    
    ax.set_xticks(angles)
    ax.set_xticklabels(categories, fontsize=10)
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"图表已保存: {output_file}")


def create_comparison_table_chart(
    data: Dict[str, List],
    title: str = "技术方案对比表",
    output_file: str = "comparison_table.png",
    figsize: Tuple[int, int] = (12, 6)
):
    """
    创建对比表格图
    
    Args:
        data: 表格数据字典
        title: 图表标题
        output_file: 输出文件名
        figsize: 图表尺寸
    """
    fig, ax = plt.subplots(figsize=figsize)
    ax.axis('tight')
    ax.axis('off')
    
    # 准备表格数据
    columns = ['对比项'] + data['headers']
    cell_data = []
    
    for row_name in data['rows']:
        row = [row_name]
        for header in data['headers']:
            row.append(data['content'].get(f"{row_name}_{header}", '-'))
        cell_data.append(row)
    
    # 创建表格
    table = ax.table(cellText=cell_data,
                     colLabels=columns,
                     cellLoc='center',
                     loc='center',
                     colWidths=[0.3] + [0.35] * len(data['headers']))
    
    # 设置表格样式
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)
    
    # 表头样式
    for i in range(len(columns)):
        table[(0, i)].set_facecolor(PATENT_COLORS['primary'])
        table[(0, i)].set_text_props(color='white', fontweight='bold')
    
    # 数据行样式
    for i in range(1, len(cell_data) + 1):
        for j in range(len(columns)):
            if i % 2 == 0:
                table[(i, j)].set_facecolor(PATENT_COLORS['background'])
    
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"图表已保存: {output_file}")


def create_flow_chart(
    steps: List[str],
    title: str = "技术流程图",
    output_file: str = "flow_chart.png",
    figsize: Tuple[int, int] = (10, 8)
):
    """
    创建技术流程图
    
    Args:
        steps: 流程步骤列表
        title: 图表标题
        output_file: 输出文件名
        figsize: 图表尺寸
    """
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # 绘制流程框
    n_steps = len(steps)
    box_height = 8 / n_steps
    y_start = 9
    
    for idx, step in enumerate(steps):
        y_pos = y_start - idx * box_height
        
        # 绘制矩形框
        rect = plt.Rectangle((1.5, y_pos - box_height/2), 7, box_height * 0.7,
                            fill=True, facecolor=PATENT_COLORS['secondary'],
                            edgecolor=PATENT_COLORS['primary'], linewidth=2,
                            alpha=0.8)
        ax.add_patch(rect)
        
        # 添加文字
        ax.text(5, y_pos - box_height * 0.15, step,
               ha='center', va='center', fontsize=11,
               fontweight='bold', color=PATENT_COLORS['text'])
        
        # 添加箭头
        if idx < n_steps - 1:
            ax.annotate('', xy=(5, y_pos - box_height * 0.5),
                       xytext=(5, y_pos - box_height * 0.7),
                       arrowprops=dict(arrowstyle='->', 
                                      color=PATENT_COLORS['accent'],
                                      lw=2))
    
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"图表已保存: {output_file}")


if __name__ == "__main__":
    print("专利数据可视化工具")
    print("=" * 50)
    
    # 示例: 性能对比图
    methods = ["现有方案A", "现有方案B", "本申请方案"]
    metrics = {
        "准确率(%)": [85.2, 87.3, 94.6],
        "处理速度(ms)": [120, 95, 45],
        "资源占用(MB)": [256, 312, 178]
    }
    create_performance_comparison(methods, metrics, 
                                 title="图像识别性能对比",
                                 output_file="performance_comparison.png")
    
    # 示例: 趋势图
    years = [2018, 2019, 2020, 2021, 2022, 2023, 2024]
    counts = [45, 78, 120, 186, 245, 312, 398]
    create_trend_line(years, counts, 
                     title="人工智能图像识别专利申请趋势",
                     output_file="trend_line.png")
    
    # 示例: 雷达图
    categories = ["准确性", "效率", "鲁棒性", "可扩展性", "成本"]
    values_list = [
        [75, 70, 65, 80, 60],  # 现有方案A
        [80, 75, 70, 75, 70],  # 现有方案B
        [95, 92, 88, 90, 85]   # 本申请方案
    ]
    labels = ["现有方案A", "现有方案B", "本申请方案"]
    create_radar_chart(categories, values_list, labels,
                      title="技术效果综合对比",
                      output_file="radar_chart.png")
    
    print("\n所有示例图表已生成完成!")
