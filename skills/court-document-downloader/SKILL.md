---
name: court-document-downloader
description: 从人民法院电子送达平台(zxfw.court.gov.cn)下载传票/判决书等文书PDF，自动归档到本地案件文件夹，解析文书内容告知用户，设置开庭提醒（含日历集成），自动计算上诉期限
category: legal
tags:
  - court
  - download
  - document
  - legal
  - chinese
  - pdf
---

# 法院文书下载与归档

## 何时使用

当收到来自人民法院电子送达平台（zxfw.court.gov.cn）的文书送达时使用。支持两种触发方式：

**方式一：粘贴短信原文**

```
收到法院短信，内容如下：
【xx市人民法院】某某，您好！您有（2025）苏0981民初1234号案件文书送达，请点击链接查收：https://zxfw.court.gov.cn/zxfw/#/pagesAjkj/app/wssd/index?qdbh=DEMO1&sdbh=DEMO2&sdsin=DEMO3
```

**方式二：直接发送送达链接**

用户直接发送以 `https://zxfw.court.gov.cn/zxfw/#/pagesAjkj/app/wssd/index?qdbh=...` 开头的链接。此时跳过短信文本解析，直接从 URL 提取参数进入下载流程。

**自动触发规则（无需手动加载）：** 当用户发送包含以下关键词时，自动加载本 skill：
- `zxfw.court.gov.cn`
- 人民法院电子送达
- 法院 + 传票/文书/送达/判决书/开庭提醒 等
- 传票链接 + 帮我下载/归档/存档/存起来 等

## 工作流程

### 前置步骤：确认工作目录（⚠️ 必须，每次执行前检查）

> 此步骤在**每次执行前**都必须检查。配置保存在用户本地 `~/.config/court-document-downloader/config.json`，不随 skill 文件分发。

**执行检查：**

```bash
CONFIG_FILE="$HOME/.config/court-document-downloader/config.json"
python3 -c "
import json, os, sys
config_path = os.path.expanduser('~/.config/court-document-downloader/config.json')

# 情况一：配置文件不存在
if not os.path.exists(config_path):
    print('NOT_CONFIGURED')
    sys.exit(0)

# 情况二：配置文件存在但解析失败
try:
    with open(config_path) as f:
        cfg = json.load(f)
except Exception:
    print('CONFIG_BROKEN')
    sys.exit(0)

# 情况三：缺少必需字段（旧版残留的不完整配置）
required_fields = ['work_directory', 'archive_mode', 'calendar_name', 'default_reminders']
missing = [f for f in required_fields if f not in cfg]
if missing:
    print('CONFIG_INCOMPLETE')
    print('缺失字段: ' + ', '.join(missing))
    sys.exit(0)

# 情况四：配置完整，输出工作目录
print(os.path.expanduser(cfg['work_directory']))
" 2>/dev/null
```

**输出含义：**
- `NOT_CONFIGURED` — 配置文件不存在，进入首次配置引导
- `CONFIG_BROKEN` — 配置文件存在但损坏（JSON 解析失败），提示用户后进入配置引导
- `CONFIG_INCOMPLETE` — 配置文件存在但不完整（旧版残留），提示用户后进入配置引导
- 其他输出（路径）— 配置完整，使用该路径继续执行

**如果输出 `NOT_CONFIGURED`、`CONFIG_BROKEN` 或 `CONFIG_INCOMPLETE`：必须立即停止后续流程，进入首次配置引导。**

> ⚠️ 对于 `CONFIG_BROKEN` 和 `CONFIG_INCOMPLETE`，先告知用户"检测到旧版不完整配置，需要重新配置"，然后执行 `rm "$HOME/.config/court-document-downloader/config.json"` 删除旧文件，再进入下方配置引导。

**⚠️ 关键：不要替用户做决定。每一轮交互都必须等待用户明确回复后才能继续。绝对不能自动选择默认值跳过交互。**

---

#### 第一轮交互：询问保存路径

向用户展示以下内容，然后**停止，等待用户回复**：

> ⚠️ 执行到此步骤时必须停下来，把下面的内容展示给用户，然后等待用户的实际回复。不允许自行假设用户的选择，不允许自动填入默认值。

```
⚠️ 首次使用，需要设置诉讼文书的保存位置。

文书将保存到这个文件夹中，建议选择一个方便查找的持久化位置。

请选择保存路径：
  1. 保存到桌面（默认）— ~/Desktop/诉讼案件/
  2. 自定义路径 — 回复一个本地文件夹路径

示例：
  回复 "1" 或 "默认"       → 保存到 ~/Desktop/诉讼案件/
  回复 "~/Documents/诉讼案件" → 保存到文稿目录
  回复 "/Volumes/移动硬盘/诉讼案件" → 保存到外接硬盘

同时请选择归档方式：
  A. 按年份分层（默认）— 自动创建 2026/、2027/ 等年份子文件夹
  B. 不分年份 — 所有案件文件夹直接放在工作目录下

回复格式：路径选择 + 归档方式，如 "1 A" 或 "~/Documents/诉讼案件 B"
仅回复路径则默认使用按年份分层（A）。
```

**在用户回复之前，不得执行任何后续步骤。**

#### 第二轮交互：确认配置

收到用户回复后，解析出路径和归档方式。**先不要保存**，向用户展示确认信息，然后**停止，等待用户确认**：

```
📋 请确认你的配置：

  📁 保存路径：{解析出的完整路径}
  📂 归档方式：{按年份分层 / 不分年份}

  📅 日历提醒：Apple Calendar「个人」日历
  ⏰ 提醒时间：开庭前 7 天 + 开庭前 2 天

  📂 文件夹结构预览：
  {路径}/
  ├── 2026/                         ← 按年份分层时才有此层
  │   └── {原告}诉{被告}{案由}/
  │       └── {文书名}_20260711收.pdf
  └── .archive/                     ← 归档记录
      └── 20260711_143025_1234.json

确认无误请回复「确认」或「Y」
如需修改路径请直接回复新路径
如需修改日历名称或提醒设置请回复「高级配置」
```

**在用户确认之前，不得保存配置。**

#### 高级配置（仅当用户回复"高级配置"时触发）

向用户展示：

```
⚙️ 高级配置（可直接回复修改项，格式：设置名=值，多项用逗号分隔）：

  日历名称    当前：个人        例：日历名称=工作
  提醒1       当前：提前7天     例：提醒1=10（天）
  提醒2       当前：提前2天     例：提醒2=1（天）

  回复示例：日历名称=工作,提醒1=10,提醒2=3
  回复「确认」则使用当前设置完成配置
```

收到用户的高级配置修改后，更新对应值，重新展示第二轮确认信息。

#### 保存配置（仅在用户明确确认后执行）

```bash
mkdir -p ~/.config/court-document-downloader

# 以下变量已从前述交互中解析获得：
# WORK_DIR_INPUT   — 用户确认的路径（如 ~/Desktop/诉讼案件）
# ARCHIVE_MODE     — "by_year" 或 "flat"
# CALENDAR_NAME    — 日历名称（默认 "个人"）
# REMINDER_1_DAYS  — 第一个提醒提前天数（默认 7）
# REMINDER_2_DAYS  — 第二个提醒提前天数（默认 2）

# 展开路径中的 ~ 为 $HOME
WORK_DIR_EXPANDED=$(python3 -c "import os; print(os.path.expanduser('$WORK_DIR_INPUT'))")

# 创建工作目录（包括 .archive 子目录）
mkdir -p "$WORK_DIR_EXPANDED/.archive"

# 写入完整配置
cat > ~/.config/court-document-downloader/config.json << EOF
{
  "work_directory": "$WORK_DIR_INPUT",
  "archive_mode": "$ARCHIVE_MODE",
  "archive_subdirectory": ".archive",
  "calendar_name": "$CALENDAR_NAME",
  "default_reminders": [
    {"days_before": $REMINDER_1_DAYS, "description": "提前${REMINDER_1_DAYS}天"},
    {"days_before": $REMINDER_2_DAYS, "description": "提前${REMINDER_2_DAYS}天"}
  ]
}
EOF

echo "✅ 配置已保存"
echo "✅ 工作目录已创建: $WORK_DIR_EXPANDED"
```

#### 展示配置摘要并继续

```
✅ 配置完成！

  📁 保存路径：{完整路径}
  📂 归档方式：{按年份分层 / 不分年份}
  📅 日历名称：{日历名}
  ⏰ 开庭提醒：提前 {N} 天 + 提前 {M} 天

  📝 配置文件：~/.config/court-document-downloader/config.json
  如日后需要修改配置，可直接编辑该文件，或删除它重新触发配置引导。
```

**配置完成后，重新读取配置并继续执行下方 Step 1-12。**

```bash
CONFIG_FILE="$HOME/.config/court-document-downloader/config.json"
WORK_DIR=$(python3 -c "
import json, os
with open('$CONFIG_FILE') as f:
    path = json.load(f)['work_directory']
print(os.path.expanduser(path))
")
echo "✅ 工作目录: $WORK_DIR"
```

---

### Step 1：判断输入类型

**完整短信文本**：包含法院签名（如 `【xx法院】`）+ 正文 + 链接 → 进入 Step 2 短信解析

**纯链接**：用户直接发送送达 URL → 跳过 Step 2 的短信解析部分，直接从 URL 提取 `qdbh`、`sdbh`、`sdsin` 参数，进入 Step 3 下载。案号、当事人等信息在下载文书后从文书内容中提取。

### Step 2：短信原文解析（仅短信输入时触发）

**a) 短信类型分类**：根据关键词判断

| 类型 | 特征 | 含下载链接 | 处理方式 |
| --- | --- | --- | --- |
| 文书送达 | 含送达平台链接 + 案号 | 是 | 下载文书并归档到案件目录 |
| 立案通知 | 含"已立案"等关键词 | 可能有 | 展示解析结果 |
| 信息通知 | 无链接，纯信息 | 否 | 展示解析结果 |

**b) 案号提取**：使用正则 `[（(〔[]\d{4}[）)〕]]` 匹配标准案号格式

标准案号格式示例：
- `（2025）苏0981民初1234号`
- `(2024)粤0604执保5678号`
- `〔2025〕京0105民初901号`

**c) 当事人提取**：从短信文本初步识别，最终以文书内容为准
- **注意**：短信中的称呼（如"某某，您好"）仅为短信接收人，不作为案件当事人
- 公司名称：`xx有限责任公司`、`xx有限公司`、`xx股份有限公司`
- 诉讼对峙：`A与B`、`A诉B`、`原告A 被告B`
- 角色前缀：`原告：xxx`、`被告：xxx` 等
- 排除关键词：法院、人民法院、书记员、法官、审判员、执行员、系统、平台、服务、通知、短信等

**d) 下载链接提取**：从短信中提取 zxfw.court.gov.cn 链接，提取 `qdbh`、`sdbh`、`sdsin` 三个参数

**e) 发送时间提取**：优先从后续 API 响应的 `dt_cjsj` 字段提取；其次从短信网关时间匹配（`发送：YYYY-MM-DD HH:mm` 格式）

**输出格式**（向用户展示）：

```
📋 短信解析结果：
- 类型：文书送达
- 案号：（2025）苏0981民初1234号
- 当事人：某某、xx有限公司
- 法院：xx市人民法院
- 下载链接：已提取（zxfw.court.gov.cn）
```

### Step 3：获取文书列表并下载

> 优先使用方案一（API 直连），失败后降级到方案二（浏览器）。严格串行，当前方案成功即停止，不并行尝试。

**API 失败判断条件（满足任一即视为失败，降级到方案二）：**
- curl 返回非 0 退出码（网络错误）
- HTTP 状态码非 200
- 响应体无法解析为 JSON
- 响应 JSON 中 `data` 字段为 `null` 或空数组 `[]`
- 响应 JSON 中 `data` 字段不存在

#### 方案一：API 直连（推荐，无需浏览器）

直接调用 zxfw 后端 API 获取文书列表和 OSS 下载链接，再用 curl 批量下载 PDF。

**API 信息**：
- 端点：`POST https://zxfw.court.gov.cn/yzw/yzw-zxfw-sdfw/api/v1/sdfw/getWsListBySdbhNew`
- Content-Type：`application/json`
- 请求体：`{ "qdbh": "xxx", "sdbh": "xxx", "sdsin": "xxx" }`（从短信 URL 提取）
- 响应字段：`data[].c_wsmc`（文书名称）、`data[].wjlj`（OSS 签名下载链接）、`data[].c_fymc`（法院名称）、`data[].c_wsbh`（文书编号）、`data[].dt_cjsj`（送达时间）
- 无需认证、无需浏览器

```bash
# 0. WORK_DIR 已在前置步骤读取，直接使用
# 确认变量存在
[ -z "$WORK_DIR" ] && { echo "错误：WORK_DIR 未设置"; exit 1; }

# 1. 从短信 URL 提取参数
qdbh="DEMO_qdbh_value"
sdbh="DEMO_sdbh_value"
sdsin="DEMO_sdsin_value"

# 2. 调用 API 获取文书列表
mkdir -p /tmp/court-sms-staging/
resp=$(curl -s -X POST "https://zxfw.court.gov.cn/yzw/yzw-zxfw-sdfw/api/v1/sdfw/getWsListBySdbhNew" \
  -H "Content-Type: application/json" \
  -d "{\"qdbh\":\"$qdbh\",\"sdbh\":\"$sdbh\",\"sdsin\":\"$sdsin\"}")

# 3. 解析文书列表，逐个下载 PDF
echo "$resp" | python3 -c "
import json, sys, urllib.parse, subprocess
data = json.load(sys.stdin)
for doc in data.get('data', []):
    name = doc.get('c_wsmc', '未知文书')
    url = doc.get('wjlj', '')
    if url:
        # URL 解码文件名
        safe_name = name.replace('/', '_').replace(':', '_')
        subprocess.run(['curl', '-sL', '-o', f'/tmp/court-sms-staging/{safe_name}.pdf', url,
            '-H', 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            '-H', 'Referer: https://zxfw.court.gov.cn/'])
"

# 4. 验证下载结果
ls -lh /tmp/court-sms-staging/*.pdf

# 5. 记录 API 响应（用于后续归档）
echo "$resp" > /tmp/court-sms-staging/_api_response.json
```

> **注意**：OSS 签名 URL 有过期时间（约 1 小时），获取后应尽快下载。`dt_cjsj` 字段为送达记录创建时间，可用于后续上诉期限计算。

#### 方案二：浏览器提取 OSS 直链（降级方案）

当方案一 API 不可用时，使用浏览器自动化。

> ⚠️ 浏览器操作需先加载 `agent-browser` skill。以下为操作步骤描述，具体工具调用方式以 agent-browser skill 的接口为准。

**操作流程：**

1. **导航到送达链接** — 用浏览器打开法院送达 URL，等待页面完全加载
2. **截取页面快照** — 查看完整页面结构，确认文书列表

**页面有两个区域：**
1. **左侧/上方侧边栏** — 列出本次送达的全部文书（可点击切换）
2. **右侧 PDF.js 阅读器** — 显示当前选中文书的 PDF 内容（内含"下载"按钮）

⚠️ **一个送达链接通常包含多份文书！** 务必先扫描侧边栏，确认本次送达共有多少份文书。

**依次点击侧边栏每份文书，获取其 OSS URL：**

对侧边栏中每个文书元素，执行：
1. 点击该文书元素 — 切换到该文书
2. 执行 JavaScript `document.querySelector('iframe')?.src` — 获取 iframe 的 src

iframe 的 src 结构：
```
https://zxfw.court.gov.cn/zxfw/static/pdfjs/web/viewer.html?file=https%3A%2F%2Fzxfy2-oss.oss-cn-north-2-gov-1.aliyuncs.com%2Fwssdclxz%2F{date}%2F{time}%2F{sdbh}%2F{file_hash}%2F{filename}%3FExpires%3D...%26Signature%3D...
```

其中 `file=` 后的内容（URL 解码 1 次）就是可直接下载的 OSS PDF 地址。

**用 curl 批量下载到 /tmp/court-sms-staging/：**

```bash
curl -L -o "/tmp/court-sms-staging/{文件名}.pdf" \
  "实际PDF下载URL" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
  -H "Referer: https://zxfw.court.gov.cn/"
```

> **为什么优先用 API？** API 方案完全无头、不需要浏览器、速度快，一次性获取所有文书列表和下载链接，避免逐个点击侧边栏提取 iframe src。

### Step 4：确定目标路径

先读取归档模式配置：

```bash
ARCHIVE_MODE=$(python3 -c "
import json
with open('$HOME/.config/court-document-downloader/config.json') as f:
    print(json.load(f).get('archive_mode', 'by_year'))
")
```

**模式一：`archive_mode = "by_year"`（默认，按年份分层）**

年份按下载日期（当前日期）确定，不从案号解析。

- 基础路径：`${WORK_DIR}/`
- 搜索/创建路径：`${WORK_DIR}/{年份}/{案件文件夹}/`
- 例：2026 年下载 → `${WORK_DIR}/2026/`

⚠️ ⚠️ ⚠️ **即使案号为 `（2025）苏1002民初XX号`，只要在 2026 年下载，就归入 2026 文件夹**

**模式二：`archive_mode = "flat"`（不分年份）**

- 基础路径：`${WORK_DIR}/`
- 搜索/创建路径：`${WORK_DIR}/{案件文件夹}/`
- 不创建年份层级，所有案件文件夹直接放在工作目录下

### Step 5：查找匹配的案件文件夹

> ⚠️ **核心原则：先搜后建。必须先在目标目录下搜索是否已有包含原被告名的文件夹，有则直接复用，无则才新建。绝不允许跳过搜索直接创建新文件夹。**

#### 5.1 确定搜索目录

```bash
if [ "$ARCHIVE_MODE" = "flat" ]; then
    SEARCH_DIR="${WORK_DIR}"
else
    SEARCH_DIR="${WORK_DIR}/$(date +%Y)"
fi
```

#### 5.2 提取原被告名

**来源一（优先）：从 API 返回或 PDF 文件名提取**

如果 PDF 文件名包含当事人公司名（如 `民事传票（某某建设工程有限公司）.pdf`），或 API 返回的法院信息中包含当事人信息，直接使用。

**来源二（回退）：从 PDF 文件内容解码提取**

当文件名仅含案号时，解码 PDF 正文提取原告和被告信息。（详见 Step 7 的 CID 字体解码章节）

#### 5.3 执行搜索（⚠️ 必须，不可跳过）

提取到原被告名后，**必须执行以下搜索代码**，在目标目录下查找匹配的已有文件夹：

```bash
# PLAINTIFF 和 DEFENDANT 已从 5.2 提取获得
# SEARCH_DIR 已从 5.1 确定

MATCHED_DIR=$(python3 -c "
import os, sys, re

search_dir = '$SEARCH_DIR'
plaintiff = '''$PLAINTIFF'''   # 原告名
defendant = '''$DEFENDANT'''   # 被告名

if not os.path.exists(search_dir):
    print('')
    sys.exit(0)

# 列出所有案件文件夹（排除 .archive 等隐藏目录）
existing_folders = [d for d in os.listdir(search_dir)
                    if os.path.isdir(os.path.join(search_dir, d)) and not d.startswith('.')]

if not existing_folders:
    print('')
    sys.exit(0)

print('现有文件夹:', existing_folders, file=sys.stderr)

# 去掉公司后缀，提取核心关键词
def strip_suffix(name):
    if not name:
        return ''
    for suffix in ['股份有限公司', '有限责任公司', '有限公司', '集团']:
        if name.endswith(suffix):
            return name[:-len(suffix)]
    return name

# 去掉地域前缀（省份、城市等），生成变体
# 例如：「江苏天下无敌公司」→「天下无敌公司」
#       「南京市某某建设工程」→「某某建设工程」
def strip_geo_prefix(name):
    if not name:
        return ''
    variants = [name]
    # 省份前缀
    provinces = ['江苏', '浙江', '广东', '北京', '上海', '天津', '重庆',
                 '山东', '河南', '河北', '湖北', '湖南', '四川', '福建',
                 '安徽', '江西', '辽宁', '吉林', '黑龙江', '山西', '陕西',
                 '云南', '贵州', '甘肃', '青海', '海南', '内蒙古', '新疆',
                 '西藏', '广西', '宁夏', '香港', '澳门', '台湾']
    for prov in provinces:
        if name.startswith(prov):
            variants.append(name[len(prov):])
            break
    # 「XX市」前缀
    m = re.match(r'([\u4e00-\u9fa5]{2,4}市)', name)
    if m:
        variants.append(name[len(m.group(1)):])
    # 「XX省XX市」组合前缀
    m = re.match(r'([\u4e00-\u9fa5]{2,4}省[\u4e00-\u9fa5]{2,4}市)', name)
    if m:
        variants.append(name[len(m.group(1)):])
    # 「XX市XX区」组合前缀
    m = re.match(r'([\u4e00-\u9fa5]{2,4}市[\u4e00-\u9fa5]{2,4}区)', name)
    if m:
        variants.append(name[len(m.group(1)):])
    return variants

# 生成一个当事人名的所有匹配变体
def get_variants(full_name):
    if not full_name:
        return []
    variants = set()
    # 全名本身
    variants.add(full_name)
    # 去公司后缀
    core = strip_suffix(full_name)
    if core:
        variants.add(core)
        # 去地域前缀（从 core）
        for v in strip_geo_prefix(core):
            if len(v) >= 2:
                variants.add(v)
    # 去地域前缀（从 full_name）
    for v in strip_geo_prefix(full_name):
        if len(v) >= 2:
            stripped = strip_suffix(v)
            variants.add(v)
            if stripped:
                variants.add(stripped)
    return variants

def name_matches(folder, full_name):
    \"\"\"判断文件夹名是否包含当事人名的任意变体\"\"\"
    if not full_name:
        return False
    for variant in get_variants(full_name):
        # 变体长度 >= 3 才用于匹配，避免过短导致误匹配
        if len(variant) >= 3 and variant in folder:
            return True
    return False

# 匹配规则：原被告名必须都出现在文件夹名中（全称/简称/去地域前缀均可）
# 只命中一方不算匹配
best_match = ''
best_score = 0

for folder in existing_folders:
    p_hit = name_matches(folder, plaintiff)
    d_hit = name_matches(folder, defendant)

    # 必须原被告都命中才算匹配
    if not (p_hit and d_hit):
        continue

    # 评分用于多个匹配时选最优（全名命中优于简称命中）
    score = 0
    if plaintiff and plaintiff in folder:
        score += 2
    elif plaintiff and strip_suffix(plaintiff) in folder:
        score += 1
    if defendant and defendant in folder:
        score += 2
    elif defendant and strip_suffix(defendant) in folder:
        score += 1

    if score > best_score:
        best_score = score
        best_match = folder

if best_match:
    print(os.path.join(search_dir, best_match))
else:
    print('')
" 2>&1)
# 注意：stderr 会打印现有文件夹列表，用于调试

if [ -n "$MATCHED_DIR" ] && [ -d "$MATCHED_DIR" ]; then
    echo "✅ 找到匹配的案件文件夹: $MATCHED_DIR"
    TARGET_DIR="$MATCHED_DIR"
else
    echo "⚠️ 未找到匹配的案件文件夹，将创建新文件夹"
    # 进入 5.4 新建文件夹
fi
```

**匹配规则（原被告必须同时命中）：**

对每个当事人名，skill 会生成以下变体用于匹配：
1. **全名**：原始名称（如 `江苏天下无敌建设工程有限公司`）
2. **去公司后缀**：去掉"有限公司""有限责任公司""股份有限公司""集团"等后缀（如 `江苏天下无敌建设工程`）
3. **去地域前缀**：去掉省份（江苏/浙江/广东/北京...）、"XX市"、"XX省XX市"、"XX市XX区"等地域前缀（如 `天下无敌建设工程有限公司`、`天下无敌建设工程`）

只要文件夹名包含任意一个变体（变体长度 ≥ 3 字符），即视为该方命中。

| 条件 | 说明 |
|------|------|
| 原告命中 | 文件夹名包含原告的任意变体（全名 / 去后缀 / 去地域前缀） |
| 被告命中 | 同上，文件夹名包含被告的任意变体 |
| **匹配成功** | 原告命中 **且** 被告命中 → 复用该文件夹 |
| **匹配失败** | 只命中一方、或都未命中 → 新建文件夹 |

> ⚠️ 只有原被告名都出现在文件夹名中才算匹配。只命中原告或只命中被告不算。

**示例：**
- 已有文件夹 `天下无敌建设工程诉某某科技合同纠纷`
- 新文书原告=`江苏天下无敌建设工程有限公司`，被告=`某某科技有限公司`
- 原告变体含"天下无敌建设工程" → 文件夹命中 ✓ + 被告变体含"某某科技" → 文件夹命中 ✓ → **匹配成功**，复用

- 已有文件夹 `某某建设工程诉某某科技合同纠纷`
- 新文书原告=`某某建设工程有限公司`，被告=`张某`
- 原告命中 ✓ 但被告"张某"未命中 ✗ → **匹配失败**，新建文件夹

#### 5.4 新建文件夹（仅当 5.3 搜索无匹配时执行）

只有当 `MATCHED_DIR` 为空时，才根据已提取的原告名、被告名和案由创建新文件夹。

```bash
# 仅在未匹配到已有文件夹时执行
if [ -z "$MATCHED_DIR" ] || [ ! -d "$MATCHED_DIR" ]; then
    CASE_FOLDER="{原告名}诉{被告名}{案由}"
    TARGET_DIR="${SEARCH_DIR}/${CASE_FOLDER}"
    mkdir -p "$TARGET_DIR"
    echo "✅ 已创建新案件文件夹: $TARGET_DIR"
fi
```

**文件夹命名格式：** `{原告名}诉{被告名}{案由}`

示例：
- `某某餐饮服务有限公司诉某某合同纠纷`
- `某某诉某某房屋租赁合同纠纷`
- `某某建设工程有限公司诉某某建设施工合同纠纷`

**案由提取优先级：**
1. 优先从 PDF 正文提取（如传票中"案由：×××"）
2. 其次从 PDF 文件名推断（如"合同纠纷""侵权纠纷"）
3. 最后退化为通用案由如"民事纠纷"

### Step 6：移动 PDF 到案件文件夹

> `TARGET_DIR` 已在 Step 5 中确定（要么匹配到已有文件夹，要么新建）。此处直接使用，不再重新计算。

```bash
# TARGET_DIR 已在 Step 5 确定（匹配已有文件夹 或 新建文件夹）
# 确保目标目录存在（Step 5.4 新建时已 mkdir，匹配到时可能已存在）
mkdir -p "$TARGET_DIR"

# 使用 mv 移动文件（而非 cp 复制），避免临时文件残留
mv "/tmp/court-sms-staging/{文件名}.pdf" \
   "${TARGET_DIR}/{文书标题}（{当事人+案由}）_{YYYYMMDD}收.pdf"
```

**文件命名格式：** `{文书标题}（{当事人+案由}）_{YYYYMMDD}收.pdf`

示例：
- `传票（某某建设工程有限公司诉某某建设施工合同纠纷）_20260610收.pdf`
- `民事判决书（某某与某某合同纠纷）_20260610收.pdf`

**命名规则：**
- `文书标题`：优先使用 API 返回的 `c_wsmc`，其次从 PDF 内容提取，最后回退为原始文件名
- `当事人+案由`：从文书内容提取，取原告+被告+案由的核心信息
- `YYYYMMDD`：下载日期
- 清理非法字符：`< > : " | ? * \ /`
- 同名文件已存在时追加 `_2` 后缀
- 日期后缀统一加"收"表示收到日期，区别于文书本身日期

### Step 7：解析文书内容并告知用户

下载并归档后，使用 pymupdf 提取 PDF 文字内容：

```bash
# 使用 pymupdf 提取 PDF 文字（如未安装则安装到用户级，不污染全局环境）
python3 -c "import pymupdf" 2>/dev/null || python3 -m pip install --user pymupdf -q
python3 -c "
import pymupdf
doc = pymupdf.open('/path/to/file.pdf')
for page in doc:
    print(page.get_text())
"
```

**如果是传票，重点提取以下信息：**
- 案号、案由
- 被传唤人
- **开庭时间**（关键！用于后续提醒设置）
- **开庭地点**（关键！用于日历事件）
- 承办法官/书记员及联系方式

**如果是判决书/裁定书，重点提取：**
- 案号、案由
- 当事人信息
- 判决/裁定日期
- 文书类型（一审/二审）

**CID 字体编码 PDF 的文字提取方法：**

如果 pymupdf 输出为空或乱码，说明是 CID 字体编码的复杂 PDF（WPS 生成），需手动解码 ToUnicode CMap：

```python
import re, zlib

# 1. 读取 PDF 文件
with open('/tmp/文书.pdf', 'rb') as f:
    data = f.read()

# 2. 提取指定编号的 PDF 对象（FlateDecode 解压）
def extract_object(data, obj_num):
    """提取 PDF 中指定编号的对象（FlateDecode 解压）"""
    pattern = rb'%d\s+0\s+obj\s*(.*?)\s*endobj' % obj_num
    match = re.search(pattern, data, re.S)
    if not match:
        return None
    stream = match.group(1).split(b'stream')[1].split(b'endstream')[0].strip()
    return zlib.decompress(stream)

def find_tounicode_refs(data):
    """找到 PDF 中所有 ToUnicode CMap 的引用对象编号"""
    refs = []
    for m in re.finditer(rb'/ToUnicode\s+(\d+)\s+0\s+R', data):
        refs.append(int(m.group(1)))
    return refs

def extract_page_content_streams(data):
    """提取所有页面的 Content Stream 并解压"""
    # 找到所有页面对象编号
    page_refs = [int(m.group(1)) for m in re.finditer(rb'(\d+)\s+0\s+obj\s*.*?/Type\s*/Page\b', data, re.S)]
    streams = []
    for page_num in page_refs:
        obj_data = extract_object(data, page_num)
        if obj_data is None:
            # 页面对象本身不含 stream，查找 /Contents 引用
            pattern = rb'%d\s+0\s+obj\s*(.*?)\s*endobj' % page_num
            match = re.search(pattern, data, re.S)
            if match:
                contents_match = re.search(rb'/Contents\s+(\d+)\s+0\s+R', match.group(1))
                if contents_match:
                    obj_data = extract_object(data, int(contents_match.group(1)))
        if obj_data:
            streams.append(obj_data)
    return streams

# 3. 构建 CID→Unicode 映射字典
cmap = {}
for ref in find_tounicode_refs(data):
    cmap_data = extract_object(data, ref)
    if cmap_data:
        for m in re.finditer(r'<([0-9A-F]+)>\s+<([0-9A-F]+)>', cmap_data.decode()):
            cmap[int(m.group(1), 16)] = chr(int(m.group(2), 16))

# 4. 解压各页 Content Stream 并解码 CID 引用
decoded_text = ''
for page in extract_page_content_streams(data):
    text = page.decode('latin-1')
    segments = []
    for cid_hex in re.findall(r'<([0-9A-F]+)>Tj', text):
        cid = int(cid_hex, 16)
        if cid in cmap:
            segments.append(cmap[cid])
        else:
            # 数字 0-9 特殊处理（常见于页码、日期）
            if 0x13 <= cid <= 0x1c:
                segments.append(chr(0x30 + cid - 0x13))
    decoded_text += ''.join(segments)

# 5. 搜索"原告："和"被告："后的名称
plaintiff_match = re.search(r'原告[：:]\s*(.+?)(?:\n|$)', decoded_text)
defendant_match = re.search(r'被告[：:]\s*(.+?)(?:\n|$)', decoded_text)

plaintiff = plaintiff_match.group(1).strip() if plaintiff_match else None
defendant = defendant_match.group(1).strip() if defendant_match else None
```

### Step 8：设置开庭提醒（仅传票自动触发）

**判断逻辑：** 从文书正文中提取关键词判断文书类型。

- 如果正文包含 `传票` → **自动设置开庭提醒**（无需询问用户）
- 如果正文是判决书、裁定书等其他文书 → **仅归档，不设置提醒**

**提醒方式：仅 Apple Calendar（macOS）**

Apple Calendar 在 macOS 上可直接用 AppleScript 操作，将开庭事件添加至 iCloud 日历，自动设置地点、备注和多重提醒。

**从配置读取日历名称和提醒设置：**

```bash
# 读取配置中的日历名称和提醒设置
CONFIG_FILE="$HOME/.config/court-document-downloader/config.json"
CALENDAR_NAME=$(python3 -c "
import json
with open('$CONFIG_FILE') as f:
    print(json.load(f).get('calendar_name', '个人'))
")
REMINDERS_JSON=$(python3 -c "
import json
with open('$CONFIG_FILE') as f:
    reminders = json.load(f).get('default_reminders', [{'days_before': 7}, {'days_before': 2}])
    print(json.dumps([r['days_before'] for r in reminders]))
")
echo "日历: $CALENDAR_NAME, 提醒天数: $REMINDERS_JSON"
```

**典型事件参数：**
- 标题：`开庭 - {案号} {案由}`
- 开始时间：开庭日期 + 时间
- 结束时间：开始后约 2 小时（庭审通常 1-2 小时）
- 地点：法院全称 + 法庭 + 地址
- 备注：案号、案由、当事人、承办法官、联系方式等完整信息
- 提醒方式：从配置的 `default_reminders` 读取（默认提前 7 天 + 提前 2 天）

**AppleScript 实现：**

> ⚠️ **关键坑**：Apple Calendar 的 `trigger interval` 单位是**分钟**，不是秒！

```applescript
tell application "Calendar"
    -- 日历名称从配置读取，默认 "个人"
    set theCalendar to calendar "个人"

    set eventTitle to "开庭 - （2026）苏1002民初31号 合同纠纷"
    set eventLocation to "某某市某某区人民法院 · 第四法庭（地址）"
    set eventDescription to "案号：...
案由：...
当事人：...
承办法官：..."

    set startDate to date "2026-05-18 14:30:00"
    set endDate to date "2026-05-18 16:30:00"

    tell theCalendar
        set newEvent to make new event at end with properties {¬
            summary:eventTitle, start date:startDate, end date:endDate, ¬
            location:eventLocation, description:eventDescription}

        -- 注意：trigger interval 单位是分钟！
        -- 提醒天数从配置的 default_reminders 数组动态生成
        -- 提前7天 = -10080 分钟（7 × 24 × 60）
        make new display alarm at end of newEvent with properties {trigger interval:-7 * 24 * 60}
        -- 提前2天 = -2880 分钟（2 × 24 × 60）
        make new display alarm at end of newEvent with properties {trigger interval:-2 * 24 * 60}
    end tell
end tell
```

### Step 9：写入归档记录

每次处理完成后，在用户工作目录下的归档子目录中创建一条 JSON 记录，用于追溯。归档子目录名称从配置的 `archive_subdirectory` 字段读取（默认 `.archive`）。

```bash
# 读取归档子目录名称
ARCHIVE_SUBDIR=$(python3 -c "
import json
with open('$HOME/.config/court-document-downloader/config.json') as f:
    print(json.load(f).get('archive_subdirectory', '.archive'))
")
ARCHIVE_DIR="${WORK_DIR}/${ARCHIVE_SUBDIR}"
mkdir -p "$ARCHIVE_DIR"
```

**文件路径：** `${ARCHIVE_DIR}/YYYYMMDD_HHMMSS_{案号后4位}.json`

> `${WORK_DIR}` 从前置步骤的配置中读取，归档记录与案件文件保存在同一根目录下，便于备份和迁移。

**JSON 结构：**

```json
{
  "id": "20260610_143025_1234",
  "timestamp": "2026-06-10T14:30:25+08:00",
  "sms_raw": "【xx市人民法院】某某，您好！...",
  "parsed": {
    "type": "document_delivery",
    "case_number": "（2025）苏0981民初1234号",
    "parties": ["xx有限公司", "某某"],
    "court": "xx市人民法院",
    "case_reason": "合同纠纷"
  },
  "download": {
    "source_url": "https://zxfw.court.gov.cn/zxfw/#/...",
    "params": { "qdbh": "XX", "sdbh": "XX", "sdsin": "XX" },
    "method": "api",
    "status": "success",
    "api_response": {
      "c_fymc": "xx市人民法院",
      "dt_cjsj": "2026-03-18T07:44:00.000+00:00",
      "documents": [
        { "c_wsmc": "传票", "c_wsbh": "ecb8fe64...", "dt_cjsj": "..." }
      ]
    }
  },
  "document": {
    "type": "传票",
    "sent_at": "2026-03-18T15:44:00+08:00",
    "appeal_deadline": null,
    "appeal_days_remaining": null
  },
  "archive": {
    "matched_case": "某某建设工程有限公司诉某某建设施工合同纠纷",
    "target_path": "{WORK_DIR}/2026/某某建设工程有限公司诉某某建设施工合同纠纷/",
    "files": [
      "传票（某某建设工程有限公司诉某某建设施工合同纠纷）_20260610收.pdf"
    ]
  },
  "reminder": {
    "calendar_event": "开庭 - （2025）苏0981民初1234号 合同纠纷",
    "court_date": "2026-04-15T14:30:00+08:00",
    "location": "xx市人民法院 第3法庭",
    "alarms": ["-7天", "-2天"]
  }
}
```

### Step 10：上诉期限计算（判决书/裁定书自动触发）

当识别到判决书或裁定书时，自动计算上诉截止日期。

**上诉期限规则：**

| 案件类型 | 上诉期限 |
|---------|---------|
| 民事一审判决 | 送达后 15 天 |
| 民事裁定 | 送达后 10 天 |
| 行政判决 | 送达后 15 天 |
| 刑事判决 | 送达后 10 天 |
| 刑事裁定 | 送达后 5 天 |

**计算公式：** `上诉截止日期 = 送达日期 + 上诉期限天数`

**送达日期来源：**
- 优先使用 API 响应中的 `dt_cjsj` 字段（送达记录创建时间）
- 其次使用短信接收时间
- 无法确定时展示"送达时间待确认"，不阻塞后续流程

### Step 11：向用户汇报（结构化模板）

使用以下四段式模板汇报处理结果：

```
✅ 文书归档完成：
- 案号：（2025）苏0981民初1234号
- 法院：xx市人民法院
- 当事人：原告 xx有限公司 / 被告 某某
- 案由：合同纠纷
- 文件数：N 份
- 归档位置：{案件目录}/

📄 文书清单：
  1. 传票                                传票
  2. 应诉通知书                           通知书
  3. 起诉状（要素式）                      起诉状
  4. 举证通知书                           通知书
  ...

⚠️ 已收到传票，请注意：
  - 开庭时间：2026年4月15日（周三）14:30
  - 开庭地点：xx市人民法院 第3法庭
  - 审理程序：简易程序
  - 日历提醒：已设置（提前7天 + 提前2天）

⏰ 上诉期限提醒：
  - 文书类型：一审判决书
  - 送达时间：2026年3月18日
  - 上诉截止：2026年4月2日（周四）
  - 剩余天数：xx 天
```

**各部分触发条件：**
- "📄 文书清单"：始终展示
- "⚠️ 传票提醒"：仅当文书清单中包含传票时展示
- "⏰ 上诉期限"：仅当文书清单中包含判决书/裁定书且能提取到送达时间时展示

**归档失败时的汇报：**

```
⚠️ 文书归档部分完成：
- 案号：（2025）苏0981民初1234号
- 法院：xx市人民法院
- 成功：N 份
- 失败：N 份

失败的文书：
  - xxx.pdf（原因：下载超时）

请手动访问以下链接下载失败文书：
{原始链接}
```

#### Step 11.5：同步发送到对话框（必做）

无论归档成功还是部分成功，**必须**在汇报的同时，把本次送达的每一份文书 PDF 通过 `present_files` 工具发送到当前对话框中，使用户能在对话内直接预览和下载。这一步与桌面归档相互独立、互不影响。

- 传入路径：归档后的完整文件路径（即 Step 6 `mv` 之后的最终路径），例如
  `${TARGET_DIR}/传票（某某诉某某合同纠纷）_20260711收.pdf`
- 多份文书：一次性把所有成功归档的 PDF 路径作为数组传入 `present_files`，按重要性排序（传票/判决书优先）
- 重复送达（SHA256 与已归档文件一致）：直接 present 已有的归档文件，不再生成新副本

> 注意：本步骤在 Step 12 清理临时目录**之前**执行，确保发送的是已归档到案件文件夹的正式文件，而非 /tmp 临时文件。

### Step 12：清理临时文件

汇报完成后，清理临时下载目录：

```bash
rm -rf /tmp/court-sms-staging/
```

## 常见法院文书类型（同一送达链接可能包含多份）

- 民事传票 / 开庭传票
- (合)起诉状（素）
- 民事一审应诉通知书
- 民事一审举证通知书
- 小额诉讼程序告知书（告知当事人小额诉讼程序用）
- 原告举证材料
- 民事判决书
- 民事裁定书
- 合议庭组成人员通知书
- 受理案件通知书
- 诉讼费用交费通知书
- 廉政监督卡

## 注意事项

1. **一次送达可能含多份文书**：浏览器方案用页面快照扫描侧边栏确认文档总数，API 方案可直接从响应 `data` 数组确认
2. **优先使用 API 方案**：完全无头、无需浏览器、一次性获取所有文书，速度和可靠性远优于浏览器方案
3. **每份文书的 OSS URL 中的 file_hash 不同**：即使在同一送达批次中，每份文书有独立的 hash 子目录
4. **PDF 是临时签名 URL**：阿里云 OSS 的 URL 带有 `Expires` 过期参数，如果下载失败可能已过期，需要重新调用 API 获取新的 URL
5. **iframe 的 src 可能带有 URL 编码**：需要先 URL 解码 `file=` 参数值才能得到真实的 OSS 地址
6. **法院链接中的 qdbh/sdbh 参数是一次性/有时效的**：如果页面无法打开，让用户重新获取链接
7. **案件文件夹匹配（先搜后建）**：Step 5 必须先搜索已有文件夹，原被告名**同时命中**才算匹配（支持全名、去公司后缀简称、去地域前缀变体），匹配到则复用，无匹配才新建。新建文件夹统一按 `{原告名}诉{被告名}{案由}` 格式命名
8. **文件名中包含当事人名称的编码**：OSS 上的文件名是 URL 编码的中文，下载时可以重命名为中文明文
9. **文件命名规范**：`{文书标题}（{当事人+案由}）_{YYYYMMDD}收.pdf`，同名文件追加 `_2` 后缀
10. **CID 字体编码**：WPS 生成的 PDF 使用 CID 字体，文字不能直接提取，需解码 ToUnicode CMap
11. **OSS 链接有时效**：需及时下载，不要拖延
12. **API 响应保留**：将 API 响应保存到 `/tmp/court-sms-staging/_api_response.json`，供后续归档使用
13. **归档记录**：每次处理完成后写入 `${WORK_DIR}/${ARCHIVE_SUBDIR}/`（默认 `.archive`），便于追溯。`${WORK_DIR}` 为用户配置的工作目录
14. **上诉期限**：判决书/裁定书自动计算，使用 API 的 `dt_cjsj` 作为送达日期
15. **工作目录配置**：首次使用时需配置工作目录，保存在 `~/.config/court-document-downloader/config.json`，可随时修改或删除重新触发配置引导
16. **临时文件清理**：Step 6 使用 `mv` 移动文件后，Step 11 汇报完成后应执行 `rm -rf /tmp/court-sms-staging/` 清理临时目录

## 关键经验教训

**Apple Calendar display alarm 的 `trigger interval` 单位是分钟，不是秒！**

这是一个非常容易踩坑的点：

| 如果写成（秒） | 实际上会被解释为 | 日历显示 |
|:------------:|:---------------:|:--------:|
| `-604800` (7×86400) | -604800 分钟 = 420 天 | 提前420天 |
| `-259200` (3×86400) | -259200 分钟 = 180 天 | 提前180天 |
| `-172800` (2×86400) | -172800 分钟 = 120 天 | 提前120天 |

**正确的写法（用分钟计算）：**

| 想要的效果 | 正确值（分钟） | 公式 |
|:---------:|:-------------:|:----:|
| 提前7天 | `-10080` | `-(7 × 24 × 60)` |
| 提前3天 | `-4320` | `-(3 × 24 × 60)` |
| 提前2天 | `-2880` | `-(2 × 24 × 60)` |
| 提前1天 | `-1440` | `-(1 × 24 × 60)` |

> **最佳实践**：直接在 AppleScript 中写 `-7 * 24 * 60` 这样的表达式，让系统去计算，避免手动算错。

```applescript
-- 正确写法（分钟）
make new display alarm at end of newEvent with properties {trigger interval:-7 * 24 * 60}  -- 提前7天
make new display alarm at end of newEvent with properties {trigger interval:-2 * 24 * 60}  -- 提前2天
```

## 验证步骤

1. 送达的全部文书已成功下载（每份文件大小 > 0）
2. 在正确的年份文件夹中（按下载日期，非案号年份）
3. 在正确的案件文件夹中（Step 5 先搜后建：评分≥2 则复用已有文件夹，无匹配才新建）
4. 文件命名符合 `{文书标题}（{当事人+案由}）_{YYYYMMDD}收.pdf` 格式
5. 文书内容已解析并以结构化模板告知用户
6. 如为传票 → 已自动设置 Apple Calendar 开庭提醒（提醒天数从配置的 `default_reminders` 读取）
7. 如为判决书/裁定书 → 已自动计算上诉期限并提醒
8. 归档记录已写入 `${WORK_DIR}/${ARCHIVE_SUBDIR}/`（默认 `.archive`）
9. `/tmp/court-sms-staging/` 临时文件已清理（Step 12）
10. 已通过 `present_files` 将每份文书 PDF 同步发送到对话框（Step 11.5）
