---
name: stock-k-line-analysis-visualization-plus
description: 面向研究者的A股K线技术分析工作流。
metadata:
  display_name: 股票分析涨跌勿迷Plus
  agent_created: true
  author: 龚家勇&小民（此信息不对外）
---

# 股票分析涨跌勿迷Plus (Stock K-line Analysis & Visualization)

面向研究者的 A 股 K 线技术分析工作流。输入任意 A 股代码（如 300308）或证券名称，自动完成：
**数据获取 → 指标计算 → 统计摘要 → 静态图(PNG) → 交互式HTML(辅助) → 合并为一份完整DOCX报告** 全流程，便于研究者对个股技术形态做结构化记录与复核。

**最终产出逻辑（关键）**：所有分析内容（指标速览、技术形态分析、文字摘要、风险提示、图表）必须合并为**一份完整的 DOCX 报告**，而非分散在多份文件中。HTML 仅作为可选的交互式补充，不作为主交付物。

**日内分时图（可选增强项）**：除日K线外，工作流可额外拉取并渲染最新交易日的**日内分时图**（现价线 / 均价线 / 昨收基准线 + 分时成交量），覆盖静态 PNG、ECharts 交互图与 DOCX 内嵌图三处，作为盘口即时走势的辅助观察维度。

## 适用场景
- 研究者需要对某只 A 股标的做 K 线技术形态分析并以图表呈现结论（如："分析 XXX 的 K 线图""观察 XX 的走势""将分析结果可视化"）。
- 需要对中国 A 股（沪深京）做技术面分析并形成可归档、可复核的可视化交付物。

## 核心约定
- **颜色习惯**：红涨绿跌（中国股市惯例，与欧美相反）。
- **复权**：默认使用前复权（fqt=1）数据。
- **默认周期**：日K线（klt=101），样本250个交易日。
- **技术评分模型（模型测算）**：基于 7 个技术因子（均线排列、MACD、RSI、布林位置、区间百分位、量能配合、中期趋势）加权求和得综合技术评分 T∈[-1,1]，再经 softmax 映射为「偏多/中性/偏空」三类概率（和为100%）。圆点语义：偏多=红●、中性=黄●、偏空=绿●（与红涨绿跌一致）。**重要：该模块为历史技术指标的数学映射示意，非投资建议，所有展示位均须标注"模型测算、非投资建议"。** 因子权重与映射在 `scripts/signal_score.py` 中显式定义、可调、可复核。
- **交付物（最终）**：**一份完整的 DOCX 报告**（默认路径 `~/Desktop/<名称>（<代码>）日K线AI技术分析报告.docx`），内容含：封面标题、核心指标速览表、8 节技术形态分析（含"日内分时"小节）、逐段文字分析摘要、风险提示、三张 matplotlib 静态图（K线主图 / RSI / 日内分时图）、底部居中页码。该 DOCX 为唯一主交付物。
- **交付物（辅助）**：ECharts 交互式 HTML 报告（内嵌 PNG，可离线查看静态图）作为可选的交互补充，仍会生成，但不作为最终归档件。HTML 中包含"日内分时图"交互区块。
- **工作区中间产物**：分析过程中的 `kline.json`、`*_kline.json`、`*_intraday.json`、`*_analysis.png`、`*_rsi.png`、`*_intraday.png`、HTML 等中间产物存于当前工作区；最终 DOCX 生成至目标路径（默认桌面）。
- **免责声明**：所有输出须标注"仅基于历史价格与技术指标，不构成任何偏多/中性/偏空的操作建议"。

## 工作流程

### Step 1 — 解析标的与获取代码
- 若输入为证券名称（如"中际旭创"），需先解析为 A 股代码。可用东方财富搜索接口：
  `https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=5&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23&fields=f12,f14&key=<名称>`
  返回中 `f12`=代码，`f14`=名称。沪深市场 secid 前缀：深圳=0，上海=1。
- 若输入已为代码则直接进入 Step 2。

### Step 2 — 拉取日K线（东方财富，无需登录）
```bash
curl -s "https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=<市场>.<代码>&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&klt=101&fqt=1&end=20500101&lmt=250" -H "User-Agent: Mozilla/5.0" -o kline.json
```
字段顺序（klines 每行逗号分隔）：
`日期,开盘,收盘,最高,最低,成交量(手),成交额,振幅%,涨跌幅%,涨跌额,换手率%`
即索引：p[0]=日期, p[1]=开, p[2]=收, p[3]=高, p[4]=低, p[5]=量。

### Step 2.5 — 拉取日内分时数据（东方财富，无需登录）
```bash
curl -s "https://push2his.eastmoney.com/api/qt/stock/trends2/get?secid=<市场>.<代码>&fields1=f1,f2,f3,f7&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&iscr=0&ndays=1&forcect=1" -H "User-Agent: Mozilla/5.0" -o intraday.json
```
字段顺序（trends 每行逗号分隔）：
`时间, 开, 收(当前价), 高, 低, 成交量(手), 成交额, 均价, 手数, 涨跌幅%, 成交量(累计)`
即索引：p[0]=时间(如 "2026-07-24 09:30"), p[2]=当前价, p[7]=均价, p[5]=成交量。
- `data.preClose` 为昨收基准价；若缺失则用首条收盘价兜底。
- secid 前缀：深圳=0，上海=1（与 Step 2 一致）。
- 该步骤已由共享模块 `scripts/intraday.py` 封装（`fetch_intraday` / `load_intraday` / `secid_of`），三个脚本统一调用，避免重复实现。

### Step 3 — 指标计算（Python，managed runtime）
使用隔离 Python：`/Users/gongjiayong/.workbuddy/binaries/python/envs/default/bin/python`
首次需建 venv 并装包：
```bash
/Users/gongjiayong/.workbuddy/binaries/python/versions/3.13.12/bin/python3 -m venv /Users/gongjiayong/.workbuddy/binaries/python/envs/default
/Users/gongjiayong/.workbuddy/binaries/python/envs/default/bin/pip install matplotlib numpy
```
关键算法（注意数组对齐，均线用 convolve mode='valid' 会缩短，绘图时 dates 要切对应尾部）：
- **MA**：`np.convolve(closes, np.ones(w)/w, mode='valid')`，MA5/10/20/60。
- **EMA**：递推 `out[i]=arr[i]*k+out[i-1]*(1-k)`, `k=2/(span+1)`。
- **MACD**：DIF=EMA12-EMA26；DEA=EMA(DIF,9)；MACD=(DIF-DEA)*2。
- **RSI(14)**：涨跌幅分正负，up/down 分别求14日均值，`RS=up_avg/down_avg`, `RSI=100-100/(1+RS)`。前14位填 NaN。
- **布林带(20,2)**：中轨=MA20；上/下轨=中轨±2*std(rolling 20)。`std` 用 `np.array([np.std(closes[i-20:i]) for i in range(20, n+1)])`（注意 range 到 n+1 以对齐长度）。

### Step 4 — 生成 matplotlib 静态图
- K线蜡烛图：每根画影线(高-低) + 实体(开-收)，红涨绿跌。叠加 MA5/10/20/60 线 + 布林上下轨(虚线)。
- 成交量副图：红绿柱。
- MACD 副图：DIF/DEA 线 + 红绿柱。
- 单独 RSI 图。
- **日内分时图**：现价线（红涨绿跌）+ 均价线（蓝）+ 昨收基准虚线，下方叠分时成交量副图；涨区红填充、跌区绿填充。保存为 `zjxc_intraday.png`。
- 保存为 `zjxc_analysis.png` / `zjxc_rsi.png` / `zjxc_intraday.png`（文件名按需替换）。
- 字体：`plt.rcParams["font.sans-serif"]=["Arial Unicode MS","PingFang SC","SimHei"]`，`axes.unicode_minus=False`。

### Step 5 — 生成 ECharts 交互式 HTML（辅助交付物）
- 把 PNG 用 base64 内嵌（离线也能看静态图），K线/量/MACD/RSI 用 ECharts 画交互图。
- **日内分时图**：用 ECharts 画现价/均价折线 + 昨收 markLine，标题含交易日与收盘涨跌幅。
- 顶部放指标卡片（最新价、区间涨跌幅、较高点回撤、最高/最低、近20日振幅、量比、RSI）。
- ECharts CDN：`https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js`。
- 报告底部附文字结论 + 风险提示。
- 输出 `zjxc_report.html`（文件名按需替换），存于工作区。
- **说明**：HTML 仅为交互式辅助材料，最终归档以 Step 5.5 的 DOCX 为准。

### Step 5.5 — 生成完整 DOCX 报告（最终交付物，必须执行）
- 由 `scripts/build_docx.py` 完成：将**全部分析内容**——核心指标速览表、8 节技术形态分析（含日内分时小节）、逐段文字分析摘要、风险提示、三张 matplotlib 静态 PNG——合并为**一份完整的 DOCX 报告**。
- **触发方式**：`build_report.py` 在生成 HTML 后会**自动调用** `build_docx.py` 并将报告导出至目标路径（默认桌面）；也可单独运行：
  ```bash
  /Users/gongjiayong/.workbuddy/binaries/python/envs/default/bin/python \
    scripts/build_docx.py --workspace <工作区绝对路径> --code <代码> --name <名称> [--desktop <桌面绝对路径>]
  ```
- **DOCX 内容结构（单一文件）**：
  1. 封面标题：`<名称>（<代码>）日K线AI技术分析报告`
  2. 核心指标速览表（最新收盘、区间涨跌幅、较高点回撤、区间最高/最低、近20日振幅、量比、RSI，含红涨绿跌着色）
  2.5. 技术评分章节（三色圆点+百分比概览：● 偏多概率x% / ● 中性概率y% / ● 偏空概率z% + 综合技术评分 T + 因子加权明细表，标注"模型测算、非投资建议"）
  3. 技术形态分析（趋势 / 均线 / MACD / 布林 / RSI / 量能 / 日内分时 / 支撑阻力 / 综合判断，共 8 节 + 日内分时小节，结论与指标联动）
  4. 文字分析摘要（逐段综合结论，与 Step 6 口径一致）
  5. 风险提示段落（灰色小字，含免责声明）
  6. 分析图表（内嵌 `zjxc_analysis.png`、`zjxc_rsi.png`、`zjxc_intraday.png` 三张静态图，分别为图1/图2/图3）
  7. **页码**：文档底部居中插入 PAGE 域，自动编号
- **输出文件（默认路径）**：`~/Desktop/<名称>（<代码>）日K线AI技术分析报告.docx`。
- 依赖：`python-docx`（已装在 managed venv）。字体：标题黑体、正文宋体（已设置 eastAsia 确保中文不降级）。

### Step 6 — 文字分析摘要（输出结论时 + 写入 DOCX）
必须包含：走势分段、均线排列状态、MACD 状态、布林位置、RSI 强弱、量能、关键支撑/阻力、综合判断、风险提示。
该摘要须同步写入 DOCX 的"文字分析摘要"节，保证报告自包含、可独立阅读与复核。
统计口径示例：`区间涨跌幅=(最新/首日-1)*100`；`较高点回撤=(最新/区间最高-1)*100`；`量比=近5日均量/全样本均量`。

### Step 7 — 展示
用 `present_files` 展示**完整的 DOCX 报告**（主交付物）；HTML 与两张 PNG 作为辅助材料可一并列出，但须明确 DOCX 为最终归档件。

## 已验证的坑（必看）
1. RSI 用 convolve 求均值时，up_ma/down_ma 长度 = len-13，写回 out 从 index 14 起（out[period:]）。
2. 布林 std 列表长度要比 ma20 多1，用 `range(20, n+1)`。
3. matplotlib 绘图时布林上下轨要用 `dates[19:]` 对齐（MA用 dates[w-1:]）。
4. 沙箱可能拦截 curl 到 eastmoney，必要时加 `dangerouslyDisableSandbox: true` 并说明。
5. DOCX 中文字体须同时设置 `run.font.name`（西文）与 `w:eastAsia`（中文），否则中文回落默认字体。
6. `build_report.py` / `build_docx.py` 已参数化（--workspace/--code/--name），运行时务必传入当前工作区，避免写入旧路径。
7. 日内分时接口（`push2his.eastmoney.com/.../trends2`）在沙箱中可能偶发连接重置（Remote end closed connection）。`intraday.py` 的 `fetch_intraday` 失败时不影响主流程：`load_intraday` 会读取已落盘的 `<CODE>_intraday.json`，且三处渲染（PNG/HTML/DOCX）均对 `idata is None` 做了空值兜底（显示"当日分时数据暂未获取"），不会抛异常。
8. 分时数据非交易日或盘前盘后可能为空数组，此时 `load_intraday` 返回 None，所有展示位自动降级，无需特殊分支处理。

## 参考文件
- 完整可运行脚本见 `scripts/analyze.py`（matplotlib 版，含分时图）、`scripts/build_report.py`（HTML + 自动生成 DOCX，含分时图）、`scripts/build_docx.py`（DOCX 整合版，含分时图）、`scripts/intraday.py`（日内分时数据拉取/解析共享模块，供三个脚本统一调用），可复制后改文件名/代码复用。
