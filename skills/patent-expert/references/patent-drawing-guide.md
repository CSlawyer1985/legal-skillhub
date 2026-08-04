# 专利交底书配图绘制指南

本指南基于 Graphviz (Python graphviz 库) 绘制专利交底书配图，适用于系统架构图、流程图、模块结构图、示意图等常见专利图类型。

## 环境要求

- **Python**: 3.x（当前环境 C:\Python314\python.exe，含 graphviz 包）
- **Graphviz**: 二进制安装于 C:\Program Files\Graphviz\bin（含 dot.exe）
- **字体**: Microsoft YaHei（中文渲染）

> ⚠️ AutoClaw 自带的 python (C:\Program Files\AutoClaw\resources\python\python.exe) 无 pip，不可用。绘图时必须用 C:\Python314\python.exe。

## 统一视觉规范

所有配图必须遵循以下风格，保证交底书视觉一致性：

### 全局属性
`python
g.attr(
    rankdir='TB',          # 布局方向: TB(上到下) / LR(左到右) / BT / RL
    dpi='200',             # 高清输出
    bgcolor='white',
    fontname='Microsoft YaHei',
    fontsize='11',
    nodesep='0.4',         # 节点间距
    ranksep='0.6',         # 层级间距
)
`

### 节点属性
`python
g.attr('node',
    fontname='Microsoft YaHei',
    fontsize='10',
    shape='box',           # 默认矩形
    style='rounded,filled',# 圆角 + 填充（黑白线框）
    fillcolor='white',
    color='black',
    fontcolor='black',
    penwidth='1.2',
)
`

### 边属性
`python
g.attr('edge',
    fontname='Microsoft YaHei',
    fontsize='9',
    color='black',
    fontcolor='black',
    penwidth='1.0',
    arrowsize='0.8',
)
`

### 配色方案（黑白线框图）

> ⚠️ **专利交底书要求黑白线框图**，不使用彩色填充。所有节点统一黑白灰配色。

| 用途 | fillcolor | 说明 |
|------|-----------|------|
| 核心节点 | #E8E8E8 (浅灰) | 系统核心/中枢模块 |
| 子节点/组件 | #F0F0F0 (更浅灰) | 子模块/插件/子单元 |
| 默认节点 | white (白) | 普通节点 |
| 边框区分 | penwidth='1.5' 加粗 / penwidth='1.0' 常规 | 重要节点用粗边框强调 |
| 判断/决策 | 无特殊颜色，用 diamond 形状区分 | 通过形状区分语义 |
| 虚线分组 | subgraph style='dashed' | 模块分组边界 |

**禁止使用**：`#D4EDDA`(绿)、`#F8D7DA`(红)、`#FFF3CD`(黄) 等彩色填充。

### 常用节点形状
| shape | 用途 |
|-------|------|
| ox | 模块、组件、系统 |
| ellipse / oval | 起点、终点、状态 |
| diamond | 判断、决策 |
| cylinder | 数据库、存储 |
| parallelogram | 输入/输出 |
| older | 文件/资源 |
| 
ote | 说明/注释 |
| ecord | 数据结构定义 |

## 六种常见图类型

### 类型1：系统架构图
**适用场景**：展示系统各模块之间的关系和层级
**布局**：TB（自上而下）或 LR（自左而右，适用于分层架构）
**要点**：
- 用 subgraph 做模块分组，style='dashed' 划分组边界
- 核心层/中间层/外围层用不同 fillcolor 区分层级
- 用 cluster_ 前缀命名 subgraph 使 Graphviz 自动加边框

`python
# 示例：三层架构
g = graphviz.Digraph('arch', format='png', engine='dot')
# ... 全局属性设置 ...

with g.subgraph(name='cluster_input') as c:
    c.attr(label='输入层', style='dashed')
    c.node('mic', '麦克风阵列')
    c.node('cam', '摄像头')

with g.subgraph(name='cluster_core') as c:
    c.attr(label='核心处理层', style='dashed')
    c.node('model', '端侧AI模型', fillcolor='#E8E8E8')
    c.node('plan', '任务规划器', fillcolor='#E8E8E8')

with g.subgraph(name='cluster_exec') as c:
    c.attr(label='执行层', style='dashed')
    c.node('engine', '执行引擎', fillcolor='#F0F0F0')

g.edge('mic', 'model')
g.edge('cam', 'model')
g.edge('model', 'plan')
g.edge('plan', 'engine')
g.render(outpath, cleanup=True)
`

### 类型2：流程图
**适用场景**：展示处理流程、执行步骤、判断分支
**布局**：TB
**要点**：
- 起点/终点用 shape='ellipse'
- 判断节点用 shape='diamond'
- 用边标签标注条件（如"是"/"否"）
- 异常分支用粗边框(penwidth='1.5')或不同填充灰度区分，不用彩色

`python
g.node('start', '开始', shape='ellipse')
g.node('check', '是否超时?', shape='diamond')
g.node('retry', '指数退避重试')
g.node('skip', '跳过并记录日志')
g.node('end', '结束', shape='ellipse')
g.edge('start', 'check')
g.edge('check', 'retry', label='是')
g.edge('check', 'skip', label='否')
g.edge('retry', 'check', label='重试次数<N')
g.edge('retry', 'end', label='重试次数>=N')
`

### 类型3：模块内部结构图
**适用场景**：展示一个模块的内部子结构和数据流
**布局**：LR 或 TB
**要点**：
- 用 subgraph 将子模块分组
- 箭头标注数据流方向和内容
- 子模块用统一配色（#E8E8E8）

### 类型4：DAG/依赖关系图
**适用场景**：展示任务之间的依赖、并行执行关系
**布局**：TB
**要点**：
- 节点代表原子任务
- 有向边代表依赖关系
- 可用批次分组（同一 rank 的节点可并行）

### 类型5：时间/时序示意图
**适用场景**：展示时间窗口、时序关系
**布局**：TB
**要点**：
- 用 shape='box' 表示时间段
- 用隐藏边（style='invis'）控制对齐
- 时间轴可用 ankdir='LR' + 隐藏链实现

### 类型6：多设备/分布式示意图
**适用场景**：展示多设备协作、跨设备通信
**布局**：TB（中心辐射）或 LR（总线型）
**要点**：
- 中心节点用深色（#F0F0F0），外围设备用浅色（#E8E8E8）
- 边标注通信协议或数据类型

## 绘图工作流

### 步骤1：分析需求
从交底书「七、附图说明」中提取每张图的：
- 图号与图名
- 要表达的核心关系
- 数据流/控制流方向

### 步骤2：选择图类型
根据附图说明匹配上述六种类型，选择合适的布局方向和节点形状。

### 步骤3：编写脚本
1. 使用统一视觉规范的模板头
2. 定义节点（注意中文标签用 \n 换行）
3. 定义边（标注关系）
4. 按需添加 subgraph 分组
5. ender() 输出到对应专利目录

### 步骤4：执行与验证
`ash
C:\Program Files\AutoClaw\resources\python;C:\Python314\Scripts\;C:\Python314\;C:\Program Files\K12\GCCommon\GCCommon_V1.0.11.20230311;C:\Program Files (x86)\Common Files\Oracle\Java\javapath;C:\windows\system32;C:\windows;C:\windows\System32\Wbem;C:\windows\System32\WindowsPowerShell\v1.0\;C:\windows\System32\OpenSSH\;C:\windows\SysWOW64\5097;C:\windows\SysWOW64;C:\Program Files\Git\cmd;C:\Program Files\TortoiseSVN\bin;C:\Users\hp\AppData\Local\Android\Sdk\platform-tools;c:\Program Files (x86)\Microsoft SQL Server\100\Tools\Binn\;c:\Program Files\Microsoft SQL Server\100\Tools\Binn\;c:\Program Files\Microsoft SQL Server\100\DTS\Binn\;C:\Users\hp\AppData\Local\Programs\Python\Launcher\;C:\Users\hp\AppData\Local\Programs\Python\Python313;C:\Users\hp\AppData\Local\Programs\Python\Python313\Scripts;c:\Users\hp\AppData\Local\Programs\cursor\resources\app\bin;C:\Program Files (x86)\NetSarang\Xshell 8\;C:\Program Files\nodejs\;C:\ProgramData\chocolatey\bin;C:\Users\hp\AppData\Local\Microsoft\WindowsApps;C:\Users\hp\AppData\Local\Programs\Microsoft VS Code\bin;C:\Users\hp\AppData\Roaming\Programs\Zero Install;C:\Users\hp\AppData\Local\Programs\cursor\resources\app\bin;C:\Users\hp\AppData\Roaming\npm;C:\Program Files\WorkBuddy\bin = "C:\Program Files\Graphviz\bin;" + C:\Program Files\AutoClaw\resources\python;C:\Python314\Scripts\;C:\Python314\;C:\Program Files\K12\GCCommon\GCCommon_V1.0.11.20230311;C:\Program Files (x86)\Common Files\Oracle\Java\javapath;C:\windows\system32;C:\windows;C:\windows\System32\Wbem;C:\windows\System32\WindowsPowerShell\v1.0\;C:\windows\System32\OpenSSH\;C:\windows\SysWOW64\5097;C:\windows\SysWOW64;C:\Program Files\Git\cmd;C:\Program Files\TortoiseSVN\bin;C:\Users\hp\AppData\Local\Android\Sdk\platform-tools;c:\Program Files (x86)\Microsoft SQL Server\100\Tools\Binn\;c:\Program Files\Microsoft SQL Server\100\Tools\Binn\;c:\Program Files\Microsoft SQL Server\100\DTS\Binn\;C:\Users\hp\AppData\Local\Programs\Python\Launcher\;C:\Users\hp\AppData\Local\Programs\Python\Python313;C:\Users\hp\AppData\Local\Programs\Python\Python313\Scripts;c:\Users\hp\AppData\Local\Programs\cursor\resources\app\bin;C:\Program Files (x86)\NetSarang\Xshell 8\;C:\Program Files\nodejs\;C:\ProgramData\chocolatey\bin;C:\Users\hp\AppData\Local\Microsoft\WindowsApps;C:\Users\hp\AppData\Local\Programs\Microsoft VS Code\bin;C:\Users\hp\AppData\Roaming\Programs\Zero Install;C:\Users\hp\AppData\Local\Programs\cursor\resources\app\bin;C:\Users\hp\AppData\Roaming\npm;C:\Program Files\WorkBuddy\bin
& "C:\Python314\python.exe" script.py
`
输出 OK: 图X 即成功。检查生成的 PNG 确认内容正确。

### 步骤5：文件命名
`
图{N}_{图名}.png
`
如：图2_标准化协议适配层插件架构图.png

## 完整脚本模板

`python
# -*- coding: utf-8 -*-
import os, graphviz

# 环境配置
os.environ['PATH'] = r'C:\Program Files\Graphviz\bin;' + os.environ.get('PATH', '')
DIR = r'交底书目录路径'

# 公共样式函数
# 灰度: #E8E8E8=核心/重要, #F0F0F0=子模块, white=默认
def new_graph(name, rankdir='TB'):
    g = graphviz.Digraph(name, format='png', engine='dot')
    g.attr(rankdir=rankdir, dpi='200', bgcolor='white',
           fontname='Microsoft YaHei', fontsize='11',
           nodesep='0.4', ranksep='0.6')
    g.attr('node', fontname='Microsoft YaHei', fontsize='10',
           shape='box', style='rounded,filled',
           fillcolor='white', color='black', fontcolor='black', penwidth='1.2')
    g.attr('edge', fontname='Microsoft YaHei', fontsize='9',
           color='black', fontcolor='black', penwidth='1.0', arrowsize='0.8')
    return g

# === 图N: {图名} ===
g = new_graph('pn_n')
# ... 定义节点和边 ...
out = os.path.join(DIR, '图N_{图名}')
g.render(out, cleanup=True)
print(f'OK: 图N')
`

## 历史图索引

| 专利 | 图号 | 图名 | 类型 |
|------|------|------|------|
| P1 | 图1 | 免唤醒词流式语音交互实时指令修正系统架构图 | 系统架构图 |
| P1 | 图2 | 声学前端处理模块内部结构图 | 模块内部结构图 |
| P1 | 图3 | 实时指令修正检测与动态更新流程图 | 流程图 |
| P1 | 图4 | 系统部署示意图 | 示意图 |
| P2 | 图1 | 多模态融合意图识别与任务规划系统架构图 | 系统架构图 |
| P2 | 图2 | 多模态数据融合模块结构图 | 模块内部结构图 |
| P2 | 图3 | 原子化任务规划流程图 | 流程图 |
| P2 | 图4 | 多模态蒸馏模型结构图 | 模块内部结构图 |
| P3 | 图1 | 端侧智能体自主执行系统架构图 | 系统架构图 |
| P3 | 图2 | 能力注册与发现流程图 | 流程图 |
| P3 | 图3 | 异步并发执行调度流程图 | 流程图 |
| P3 | 图4 | 异常回滚流程图 | 流程图 |
| P14 | 图1 | 多模态确认语音指令执行方法整体流程图 | 流程图 |
| P14 | 图2 | 确认时间窗口示意图 | 时间示意图 |
| P14 | 图3 | 综合置信度计算模块示意图 | 模块内部结构图 |
| P14 | 图4 | 声源定位与空间过滤示意图 | 示意图 |
| P14 | 图5 | 多用户场景下干扰过滤示意图 | 示意图 |
| P15 | 图1 | 端侧设备自主执行系统整体架构图 | 系统架构图 |
| P15 | 图2 | 标准化协议适配层插件架构图 | 模块内部结构图 |
| P15 | 图3 | 设备能力抽象层的JSON Schema定义示例 | 数据结构图 |
| P15 | 图4 | 指令DAG构建与调度流程图 | DAG图 |
| P15 | 图5 | 异常回滚机制流程图 | 流程图 |
| P15 | 图6 | 跨设备协同执行示意图 | 多设备示意图 |
| S1 | 图1 | 端云协同AI原生数字标牌系统整体架构图 | 系统架构图 |
| S1 | 图2 | 云端AI决策中枢三层架构图 | 模块内部结构图 |
| S1 | 图3 | 三级审核与发布流程图 | 流程图 |
| S1 | 图4 | 终端任务队列调度流程图 | 流程图 |
| S1 | 图5 | 全链路AI闭环示意图 | 多设备示意图 |
| S3 | 图1 | AI PQ自适应画质优化系统架构图 | 系统架构图 |
| S3 | 图2 | 五种内容类型画质策略对照图 | 模块内部结构图 |
| S3 | 图3 | 多维因素综合决策流程图 | 流程图 |
| S3 | 图4 | 端侧NPU算力调度示意图 | 示意图 |
| S5 | 图1 | 端侧语音自助服务系统架构图 | 系统架构图 |
| S5 | 图2 | 免唤醒检测与声源方向判断流程图 | 流程图 |
| S5 | 图3 | 封闭域NLU意图分类与拒识流程图 | 流程图 |
| S5 | 图4 | 端云知识库增量更新流程图 | 流程图 |
| S6 | 图1 | AI内容审核与品牌合规管控系统架构图 | 系统架构图 |
| S6 | 图2 | 三级审批自动判定流程图 | 流程图 |
| S6 | 图3 | 强制人工审核锁定机制示意图 | 流程图 |
| S6 | 图4 | 全链路审计日志记录流程图 | 时间示意图 |