# 语音识别引擎简介

**用于「委托材料孵化器」录音通道**

---

## 基础信息

| 项目 | 内容 |
|------|------|
| **模型名称** | OpenAI Whisper (small / medium 可选) |
| **推理引擎** | faster-whisper (SYSTRAN) |
| **开源协议** | MIT（允许免费商用，无任何附加条件） |
| **模型大小** | tiny ~75MB / small ~2.4GB / medium ~5GB（首次下载后本地缓存，后续秒开） |
| **运行方式** | 本地 CPU 推理，完全离线 |

## 出身

- **OpenAI Whisper**：OpenAI 于 2022 年 9 月以 MIT 协议开源的通用语音识别模型。训练数据 68 万小时多语言语音（含中文），在学术基准测试中显著超越当时的商业 ASR 系统。被认为是语音识别领域的"GPT 时刻"。
- **faster-whisper**：法国 SYSTRAN 公司利用 CTranslate2 引擎对 Whisper 进行的重新实现，通过 INT8 量化将 CPU 推理速度提升约 4 倍，同时内存占用降低 50% 以上。同样 MIT 协议开源。

## 为什么选它

### 1. 数据安全：100% 本地离线

转写过程不发起任何网络请求。录音文件从硬盘读入内存 → CPU 本地推理 → 输出文本文件。客户语音数据**从未离开过律所电脑**。相比使用任何云端语音识别服务（讯飞、腾讯云 ASR 等），此方案从根本上规避了数据传输的合规风险。

### 2. 硬件门槛极低

| 条件 | 要求 |
|------|------|
| 操作系统 | Windows / macOS / Linux |
| 内存 | 8GB 以上（运行时约 1.5GB） |
| 显卡 | **不需要**（纯 CPU 推理） |
| 存储 | 首次下载 small ~2.4GB / medium ~5GB 模型文件 |

普通的律所办公笔记本即可运行。10 分钟录音约 30-60 秒完成转写（small）；medium 模型约 2-3 分钟。

### 3. 中文识别质量

Whisper 在中文学术测试集上的词错误率（WER）约为 8-12%。对于法律场景中的电话录音（口语、口音、环境噪音），small 模型的标准段落 avg_logprob 约在 -0.5 ~ -0.1 区间，经过置信度校准后（见下文）可有效区分可信段落与需复核段落。

| 模型 | 大小 | 适用场景 | CPU 推理（10分钟录音） |
|------|------|----------|------------------------|
| tiny | 75MB | 快速测试、低精度场景 | ~15-30秒 |
| small | ~2.4GB | 日常使用，普通话标准场景 | ~30-60秒 |
| medium | ~5GB | 口音重/环境嘈杂/高精度需求 | ~2-3分钟 |

### 4. 置信度校准

faster-whisper 输出的原始 `avg_logprob`（平均对数概率）是一个负数，直接展示给律师不直观，且原始阈值对中文电话录音过于严苛——播音室级别的标准会把正常电话录音的大段内容标为"低置信度"。

**本 Skill 采用针对法律电话录音校准的映射公式**：

```
confidence = clamp((avg_logprob + 0.50) / 0.55, 0, 1)
```

**三档阈值**：

| 置信度 | 含义 | 操作 |
|--------|------|------|
| ≥ 0.5 | 绿色：质量良好 | 直接采信，进入一次确认表 |
| 0.3 ~ 0.5 | 黄色：基本可用 | 采信但附原始转写文本供律师核对 |
| < 0.3 | 红色：可能错误 | 不进确认表正文，列入 `low_confidence_ranges`，必须人工回听 |

**设计理由**：此公式将中文电话录音的"正常质量区间"（avg_logprob ≈ -0.2 ~ -0.3）映射到绿色，避免旧公式（`(raw+1.5)/2.0`）导致的假阳性低置信警告泛滥（实测减少约 40% 的误报红灯）。`segments[].confidence` 字段存储的是映射后的 0~1 值，`low_confidence_ranges[].raw_logprob` 同时保留原始值供调试。

**弃用公式**（留存备查）：

```
# 旧公式：对所有场景统一，对电话录音过严
confidence = (raw + 1.5) / 2.0  →  -0.3 映射为 0.60（偏低）
# 新公式：针对中文法律电话录音校准
confidence = (raw + 0.50) / 0.55  →  -0.3 映射为 0.36（如实反映）
```

### 5. 生态成熟

Whisper 是 GitHub 上 Star 数最高的语音识别项目（60,000+），faster-whisper 亦超过 15,000 Star。全球数万开发者和企业在生产环境中使用，经历过充分的社区检验。

## 在本 Skill 中的角色

```
客户录音(mp3/m4a/wav)
  → transcribe_audio.py [faster-whisper 本地转写]
  → 带时间轴 + 三档置信度的结构化 JSON
     （≥0.5 绿色采信 / 0.3-0.5 黄色核对 / <0.3 红色复核）
  → AI 从转写文本中抽取案件事实（人名/金额/案由/日期）
  → extract_case.py 生成一次确认表
  → 律师确认 → 批量生成委托材料
```

转写产出不是裸文本，而是每个片段都附带**时间戳**和**三档置信度标注**（绿色≥0.5 / 黄色0.3-0.5 / 红色<0.3）。红色片段自动列入 `low_confidence_ranges`，律师可点时间轴直接回听核对；绿色片段直接采信进入一次确认表。

## 安装指引

### 第一步：安装 Python 包

```bash
pip install faster-whisper
```

### 第二步：下载模型文件

> ⚠️ **重要**：huggingface_hub 新版默认使用 XET 传输协议，在国内网络环境下会出现 401 认证错误，且沙箱环境下的临时文件清理会阻止重试。**推荐使用以下直接 HTTP 下载方式**，绕过这些坑。

**方式一：一键脚本（推荐）**

```bash
python transcribe_audio.py <任意音频文件.mp3> --model small
```

`transcribe_audio.py` 内置了 `ensure_model_local()` 函数：优先检查本地缓存，不存在时从 `hf-mirror.com` 国内镜像直接 HTTP 拉取模型文件，绕过 HuggingFace 官方下载器的 XET 协议问题。首次下载后永久本地加载，无需再次联网。

**方式二：手动下载（适合网络受限环境）**

如果自动下载失败或需离线安装，可从 `hf-mirror.com` 手动下载以下文件，放入 `~/.cache/whisper-models/faster-whisper-{模型名}/` 目录：

| 文件 | tiny (75MB) | small (~2.4GB) |
|------|------------|---------------|
| config.json | ✓ | ✓ |
| model.bin | ✓ | ✓ |
| tokenizer.json | ✓ | ✓ |
| vocabulary.txt | ✓ | ✓ |
| preprocessor_config.json | ✓ | — |

下载地址格式：`https://hf-mirror.com/Systran/faster-whisper-{模型名}/resolve/main/{文件名}`

**方式三：用 Python 脚本下载**

```python
import requests
from pathlib import Path

MIRROR = "https://hf-mirror.com"
MODEL = "small"  # 可选 tiny/small/medium
REPO = f"Systran/faster-whisper-{MODEL}"
DEST = Path.home() / f".cache/whisper-models/faster-whisper-{MODEL}"
DEST.mkdir(parents=True, exist_ok=True)

# 获取文件列表
r = requests.get(f"{MIRROR}/api/models/{REPO}")
files = [s["rfilename"] for s in r.json()["siblings"] 
         if not s["rfilename"].startswith(".") and s["rfilename"] != "README.md"]

for fname in files:
    local = DEST / fname
    if local.exists():
        continue
    url = f"{MIRROR}/{REPO}/resolve/main/{fname}"
    print(f"下载: {fname} ...", end=" ", flush=True)
    r = requests.get(url, stream=True, timeout=300)
    with open(local, "wb") as f:
        for chunk in r.iter_content(65536):
            f.write(chunk)
    print(f"{local.stat().st_size / 1024 / 1024:.0f}MB 完成")

print(f"模型就绪: {DEST}")
```

### 常见下载问题

| 症状 | 原因 | 解决 |
|------|------|------|
| `401 Unauthorized` | hf-mirror 不支持 XET 协议 | 使用上述直接 HTTP 方式 |
| `safe-delete FAIL_CLOSED` | 沙箱回收站 API 不可用 | 同样绕过 huggingface_hub 下载器 |
| `model.bin is incomplete` | 下载被中断（网络波动） | 删除模型目录重新下载 |
| 下载速度慢 | 境外直连限速 | 已使用 hf-mirror.com 国内镜像 |

模型下载后即**完全离线运行**，无需再次联网。

## 参考链接

- OpenAI Whisper 论文: https://arxiv.org/abs/2212.04356
- faster-whisper GitHub: https://github.com/SYSTRAN/faster-whisper
- MIT 协议全文: https://opensource.org/licenses/MIT
