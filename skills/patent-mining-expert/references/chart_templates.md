# 图表模板参考

## 一、图表设计原则

### 1.1 专业性原则
- 配色简洁,建议使用蓝灰色系
- 字体规范,中文使用宋体或微软雅黑
- 标注清晰,数据来源明确
- 格式统一,符合专利文档风格

### 1.2 可读性原则
- 图表大小适中,便于阅读
- 文字清晰可辨,避免过小
- 对比鲜明,差异明显
- 布局合理,重点突出

### 1.3 准确性原则
- 数据准确无误
- 坐标轴标注规范
- 单位标识清楚
- 图例说明完整

## 二、常用图表类型模板

### 2.1 性能对比柱状图

**适用场景:**
对比本发明与现有技术的性能指标

**设计要点:**
- 使用分组柱状图
- 不同方案使用不同颜色
- 标注具体数值
- 突出本发明优势

**Python代码模板:**
```python
import matplotlib.pyplot as plt
import numpy as np

# 数据准备
methods = ['现有方案A', '现有方案B', '本申请方案']
metrics = {
    '准确率(%)': [85.2, 87.3, 94.6],
    '速度(ms)': [120, 95, 45],
    '资源(MB)': [256, 312, 178]
}

# 配色方案
colors = ['#5B9BD5', '#ED7D31', '#70AD47']

# 绘图
fig, ax = plt.subplots(figsize=(12, 6))
x = np.arange(len(methods))
width = 0.25

for i, (metric, values) in enumerate(metrics.items()):
    offset = width * i
    bars = ax.bar(x + offset, values, width, label=metric, color=colors[i])
    ax.bar_label(bars, padding=3, fontsize=10)

ax.set_xlabel('技术方案', fontsize=12)
ax.set_ylabel('性能指标', fontsize=12)
ax.set_title('性能对比图', fontsize=14, fontweight='bold')
ax.set_xticks(x + width)
ax.set_xticklabels(methods)
ax.legend()
ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('performance_comparison.png', dpi=300)
```

### 2.2 技术趋势折线图

**适用场景:**
展示技术发展趋势、专利申请量变化

**设计要点:**
- 使用平滑折线
- 标注关键数据点
- 添加趋势线(可选)
- 时间轴清晰

**Python代码模板:**
```python
import matplotlib.pyplot as plt

# 数据准备
years = [2018, 2019, 2020, 2021, 2022, 2023, 2024]
patent_counts = [45, 78, 120, 186, 245, 312, 398]

# 绘图
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(years, patent_counts, marker='o', linewidth=2.5, 
       color='#2E5090', markersize=8, markerfacecolor='#ED7D31')

# 填充区域
ax.fill_between(years, patent_counts, alpha=0.2, color='#5B9BD5')

# 标注
for x, y in zip(years, patent_counts):
    ax.annotate(f'{y}', xy=(x, y), xytext=(0, 10),
               textcoords='offset points', ha='center')

ax.set_xlabel('年份', fontsize=12)
ax.set_ylabel('专利申请数量', fontsize=12)
ax.set_title('专利申请趋势图', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('trend_line.png', dpi=300)
```

### 2.3 技术效果雷达图

**适用场景:**
多维度技术效果对比

**设计要点:**
- 维度数量适中(5-8个)
- 使用填充区域增强对比
- 标注清晰
- 多方案叠加对比

**Python代码模板:**
```python
import matplotlib.pyplot as plt
import numpy as np

# 数据准备
categories = ['准确性', '效率', '鲁棒性', '可扩展性', '成本效益']
values_list = [
    [75, 70, 65, 80, 60],  # 现有方案A
    [80, 75, 70, 75, 70],  # 现有方案B
    [95, 92, 88, 90, 85]   # 本申请方案
]
labels = ['现有方案A', '现有方案B', '本申请方案']

# 绘图
angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))

colors = ['#5B9BD5', '#ED7D31', '#70AD47']

for i, (values, label) in enumerate(zip(values_list, labels)):
    values_plot = values + [values[0]]
    angles_plot = angles + [angles[0]]
    ax.plot(angles_plot, values_plot, 'o-', linewidth=2.5,
           label=label, color=colors[i])
    ax.fill(angles_plot, values_plot, alpha=0.15, color=colors[i])

ax.set_xticks(angles)
ax.set_xticklabels(categories, fontsize=11)
ax.set_title('技术效果雷达图', fontsize=14, fontweight='bold', pad=20)
ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))

plt.tight_layout()
plt.savefig('radar_chart.png', dpi=300)
```

### 2.4 技术流程图

**适用场景:**
展示技术方案的流程步骤

**设计要点:**
- 流程清晰完整
- 使用箭头指示方向
- 步骤标注详细
- 分支逻辑明确

**Python代码模板:**
```python
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# 数据准备
steps = [
    '输入待识别图像',
    '图像预处理\n(缩放、归一化)',
    '特征提取\n(轻量级CNN)',
    '特征融合\n(注意力机制)',
    '分类识别',
    '输出结果'
]

# 绘图
fig, ax = plt.subplots(figsize=(10, 10))
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.axis('off')

n_steps = len(steps)
box_height = 8 / n_steps
y_start = 9

for idx, step in enumerate(steps):
    y_pos = y_start - idx * box_height
    
    # 绘制矩形框
    rect = mpatches.FancyBboxPatch(
        (1.5, y_pos - box_height/2), 7, box_height * 0.7,
        boxstyle="round,pad=0.1",
        facecolor='#5B9BD5',
        edgecolor='#2E5090',
        linewidth=2,
        alpha=0.8
    )
    ax.add_patch(rect)
    
    # 添加文字
    ax.text(5, y_pos - box_height * 0.15, step,
           ha='center', va='center', fontsize=11,
           fontweight='bold', color='white')
    
    # 添加箭头
    if idx < n_steps - 1:
        ax.annotate('', xy=(5, y_pos - box_height * 0.5),
                   xytext=(5, y_pos - box_height * 0.65),
                   arrowprops=dict(arrowstyle='->', 
                                  color='#ED7D31',
                                  lw=2))

ax.set_title('技术流程图', fontsize=14, fontweight='bold', pad=20)

plt.tight_layout()
plt.savefig('flow_chart.png', dpi=300)
```

### 2.5 系统架构图

**适用场景:**
展示系统整体架构和模块关系

**设计要点:**
- 层次分明
- 模块清晰
- 连接关系明确
- 标注详细

**Python代码模板:**
```python
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# 绘图
fig, ax = plt.subplots(figsize=(12, 8))
ax.set_xlim(0, 12)
ax.set_ylim(0, 8)
ax.axis('off')

# 定义模块
modules = [
    {'name': '输入层', 'x': 1, 'y': 4, 'w': 2, 'h': 1.5, 'color': '#5B9BD5'},
    {'name': '预处理层', 'x': 4, 'y': 4, 'w': 2, 'h': 1.5, 'color': '#ED7D31'},
    {'name': '特征提取层', 'x': 7, 'y': 4, 'w': 2, 'h': 1.5, 'color': '#70AD47'},
    {'name': '分类层', 'x': 10, 'y': 4, 'w': 2, 'h': 1.5, 'color': '#FFC000'},
]

# 绘制模块
for module in modules:
    rect = mpatches.FancyBboxPatch(
        (module['x'] - module['w']/2, module['y'] - module['h']/2),
        module['w'], module['h'],
        boxstyle="round,pad=0.1",
        facecolor=module['color'],
        edgecolor='#404040',
        linewidth=2,
        alpha=0.8
    )
    ax.add_patch(rect)
    ax.text(module['x'], module['y'], module['name'],
           ha='center', va='center', fontsize=12, fontweight='bold')

# 绘制连接线
for i in range(len(modules) - 1):
    ax.annotate('',
               xy=(modules[i+1]['x'] - modules[i+1]['w']/2, modules[i+1]['y']),
               xytext=(modules[i]['x'] + modules[i]['w']/2, modules[i]['y']),
               arrowprops=dict(arrowstyle='->', lw=2, color='#404040'))

ax.set_title('系统架构图', fontsize=14, fontweight='bold', pad=20)

plt.tight_layout()
plt.savefig('architecture.png', dpi=300)
```

### 2.6 对比表格图

**适用场景:**
多维度技术方案对比

**设计要点:**
- 表格清晰
- 重点突出
- 对比明确
- 一目了然

**Python代码模板:**
```python
import matplotlib.pyplot as plt

# 数据准备
data = {
    'headers': ['现有方案A', '现有方案B', '本申请方案'],
    'rows': ['准确率', '处理速度', '资源占用', '适用范围', '实现复杂度'],
    'content': {
        '准确率_现有方案A': '85.2%',
        '准确率_现有方案B': '87.3%',
        '准确率_本申请方案': '94.6%',
        '处理速度_现有方案A': '120ms',
        '处理速度_现有方案B': '95ms',
        '处理速度_本申请方案': '45ms',
        '资源占用_现有方案A': '256MB',
        '资源占用_现有方案B': '312MB',
        '资源占用_本申请方案': '178MB',
        '适用范围_现有方案A': '有限',
        '适用范围_现有方案B': '一般',
        '适用范围_本申请方案': '广泛',
        '实现复杂度_现有方案A': '复杂',
        '实现复杂度_现有方案B': '中等',
        '实现复杂度_本申请方案': '简单',
    }
}

# 绘图
fig, ax = plt.subplots(figsize=(10, 6))
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
                 colWidths=[0.25, 0.25, 0.25, 0.25])

# 设置表格样式
table.auto_set_font_size(False)
table.set_fontsize(11)
table.scale(1, 2)

# 表头样式
for i in range(len(columns)):
    table[(0, i)].set_facecolor('#2E5090')
    table[(0, i)].set_text_props(color='white', fontweight='bold')

# 数据行样式
for i in range(1, len(cell_data) + 1):
    for j in range(len(columns)):
        if i % 2 == 0:
            table[(i, j)].set_facecolor('#F2F2F2')
        # 突出本申请方案
        if j == 3:
            table[(i, j)].set_text_props(fontweight='bold', color='#2E5090')

ax.set_title('技术方案对比表', fontsize=14, fontweight='bold', pad=20)

plt.tight_layout()
plt.savefig('comparison_table.png', dpi=300)
```

## 三、配色方案参考

### 3.1 专利文档推荐配色

**主色调:**
- 深蓝: `#2E5090` - 用于标题、重点标注
- 浅蓝: `#5B9BD5` - 用于数据展示、填充
- 橙色: `#ED7D31` - 用于对比、强调
- 绿色: `#70AD47` - 用于优势展示
- 黄色: `#FFC000` - 用于警示、标记

**辅助色:**
- 浅灰: `#F2F2F2` - 用于背景、分隔
- 深灰: `#404040` - 用于文字、边框
- 白色: `#FFFFFF` - 用于背景

### 3.2 配色原则

1. **对比鲜明**: 不同数据使用对比色
2. **重点突出**: 关键数据使用强调色
3. **整体协调**: 颜色不超过5种
4. **专业简洁**: 避免花哨配色

## 四、图表质量检查清单

- [ ] 图表大小适中(建议宽度10-12英寸)
- [ ] 分辨率足够(建议300dpi)
- [ ] 字体大小合适(建议10-12pt)
- [ ] 坐标轴标注完整
- [ ] 图例说明清晰
- [ ] 数据来源标注
- [ ] 配色专业协调
- [ ] 文件命名规范
