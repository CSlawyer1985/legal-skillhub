# 国外专利附图/全文获取通道（v1.0.6 新增 · G6 落地）

> 适用：本技能 G6「检索数据源」条款中，**针对国外专利（非 CN）的全文 PDF 与原始附图获取通道**。
> 配套脚本：`scripts/foreign_patent_fetch.py`（Google Patents 抓附图 / Espacenet 抓 PDF / 元数据查询 / 批量）
> 关联脚本：`scripts/figure_compare.py`（G7 同色标注特征对照图）
> 关联脚本：`scripts/cnipa_epub.py`（**针对中国专利**的官方通道，已在 v1.0.5 落地）

---

## 1. 为什么需要这套通道

无效分析做 G7 同色标注比对时，需要涉案专利与对比文件的**原始附图**；G2「证据具体出处」需要附图号 + 段落号。PatSeek 的 `patent` 详情接口仅稳定返回 CN 文本，**国外文献既无全文 PDF，也无附图**——必须启用其他途径。

本节介绍 6 大官方/半官方来源 + 1 套自动化脚本，覆盖**全球主流专利局**。

---

## 2. 全球通道总览

| 来源 | URL 模式 | 覆盖 | 优点 | 缺点 | 推荐度 |
|------|---------|------|------|------|-------|
| **Google Patents** | `patents.google.com/patent/{id}/en` | US/EP/JP/KR/WO/DE/FR/GB/CA/AU 等 | **无验证码**、附图单独可下载、HTML 友好 | 附图与文字分离、无完整 PDF 端点 | ⭐⭐⭐⭐⭐ |
| **Espacenet** | `worldwide.espacenet.com/patent/search?q={id}` | EP/WO 全球 | 完整 PDF（说明书+附图）、权威 | 反爬较强、偶发重定向 | ⭐⭐⭐⭐ |
| **WIPO PatentScope** | `patentscope.wipo.int/...` | WO 国际申请 | 原文 PDF、含检索报告 | 加载较慢 | ⭐⭐⭐⭐ |
| **USPTO PubWest/PAIR** | `ppubs.uspto.gov/pubwebapp/` | US 授权 | PDF 含全部历史 | UI 较老 | ⭐⭐⭐ |
| **J-PlatPat (JPO)** | `www.j-platpat.inpit.go.jp/` | JP | 原文 PDF + 机器翻译 | 日文 UI | ⭐⭐⭐ |
| **KIPRIS (KIPO)** | `www.kipris.or.kr/` | KR | 原文 PDF | 韩文 UI | ⭐⭐⭐ |

**首选方案**：Google Patents（HTML 抓附图）—— 无验证码、稳定、覆盖最广。
**完整存档**：Espacenet（PDF 含说明书 + 附图）—— 适合做证据留存。

---

## 3. Google Patents 抓附图（主方案）

### 3.1 原理
1. 访问 `https://patents.google.com/patent/{公开号}/en`
2. 解析 HTML 中所有 `<img>` 标签
3. 过滤 `src` 含 `patentimages.storage.googleapis.com` 的图（附图 URL）
4. 逐张下载为 PNG

### 3.2 一键使用

```bash
# 单个专利
python scripts/foreign_patent_fetch.py figures US10234567B2 --out ./figs

# 批量
python scripts/foreign_patent_fetch.py batch compare_list.txt --cmd figures --out ./figs
```

`compare_list.txt` 格式（每行一个公开号，# 开头为注释）：
```
# 发明专利
US10234567B2
EP1234567A1
JP2021-123456A
# WO
WO2021/123456A1
```

### 3.3 输出结构
```
figs/
└── US10234567B2/
    ├── fig-001.png
    ├── fig-002.png
    ├── fig-003.png
    └── ...
```

每张附图单独存为 PNG，可直接用于：
- `figure_compare.py compare` 同色标注比对
- 人工目视核查
- 插入请求书"特征对照图"位置

### 3.4 公开号归一化

脚本自动识别以下格式（无需手动加国家代码前缀）：

| 原始 | 归一化 | 备注 |
|------|-------|------|
| `US10234567B2` | `US10234567B2` | 标准 |
| `10234567B2` | `US10234567B2` | 默认 US |
| `US10234567` | `US10234567A1` | 补 A1 |
| `10234567` | `US10234567A1` | 默认 US + A1 |
| `EP1234567A1` | `EP1234567A1` | 标准 |
| `JP2021-123456A` | `JP2021123456A` | 去 `-` |
| `KR10-2021-0012345` | `KR1020210012345` | 去 `-` |
| `WO2021/123456A1` | `WO2021123456A1` | 去 `/` |
| `DE102020123456A1` | `DE102020123456A1` | 通用 |
| `FR3056789A1` | `FR3056789A1` | 通用 |

### 3.5 与 G7 同色标注的衔接

附图下载后，**直接**用 `figure_compare.py` 同色叠加：

```bash
# 1. 准备 JSON 配置（见 figure_compare.py docstring）
cat > compare.json <<EOF
{
  "target": "./figs/CN118658342A/fig-002.png",
  "compare": "./figs/US10234567B2/fig-002.png",
  "out": "./figs/feature_compare_2.png",
  "target_label": "涉案专利 CN118658342A",
  "compare_label": "对比文件 US10234567B2",
  "title": "特征对照图 — 附图 2",
  "features": [
    {"name": "散热器", "color": "红-散热器",
     "target_xy": [[120, 80]], "compare_xy": [[100, 90]]},
    {"name": "压缩机", "color": "蓝-压缩机",
     "target_xy": [[200, 150]], "compare_xy": [[180, 160]]}
  ]
}
EOF

# 2. 一键生成
python scripts/figure_compare.py from-json compare.json
```

输出为 PNG（含左右并排 + 同色叠加 + 标题 + 色板图例），可直接插入请求书或口审 PPT。

---

## 4. Espacenet 抓 PDF（备选完整存档）

### 4.1 适用场景
- 需要包含**说明书全文 + 附图**的 PDF 单文件
- 准备"证据完整存档"提交合议组时
- 需附 PDF 复印件到请求书附件

### 4.2 一键使用

```bash
python scripts/foreign_patent_fetch.py pdf US10234567B2 --out ./pdfs
python scripts/foreign_patent_fetch.py pdf EP1234567A1 --out ./pdfs
python scripts/foreign_patent_fetch.py pdf US10234567B2 --out ./pdfs --extract-figures
```

`--extract-figures` 选项：PDF 下载后用 PyMuPDF 拆出每页为 PNG（与 Google Patents 附图合并使用）。

### 4.3 失败回退策略

Espacenet 反爬较严，自动化下载**经常失败**。脚本会明确打印人工指引：

```
[error] Espacenet 详情页未找到 PDF 链接（反爬或页面改版）
[manual] 请手工访问: https://worldwide.espacenet.com/patent/family/...
```

**手工 fallback 路径**（按推荐度排序）：
1. **Google Patents**（同源，附图 + 文字 + 引用 + 法律状态）
2. **WIPO PatentScope**（WO 专利原文 PDF，最权威）
3. **各国家局**（USPTO/JPO/KIPO/DPMA/INPI 等原文）
4. **PatSeek `semantic`**（已含国外文献入口，可作为定位起点）

---

## 5. 元数据查询

`info` 子命令抓取标题/申请人/日期/摘要（不下载附图/PDF）：

```bash
python scripts/foreign_patent_fetch.py info US10234567B2
```

输出示例：
```
[Foreign Patent] 公开号: US10234567B2
  URL:       https://patents.google.com/patent/US10234567B2/en
  title      : Method and apparatus for ...
  applicant  : Apple Inc.
  dates      : 2018-09-12; 2019-03-14
  abstract   : The invention provides ...
```

可用于：
- 特征映射前确认目标专利技术领域
- 权利要求解构前快速看摘要
- 跨语言专利对比时翻译辅助

---

## 6. 批量任务

```bash
# 准备清单
cat > compare_list.txt <<EOF
# 重要对比文件清单
US10234567B2
EP1234567A1
JP2021-123456A
WO2021/123456A1
EOF

# 批量抓附图
python scripts/foreign_patent_fetch.py batch compare_list.txt --cmd figures --out ./figs

# 批量抓元数据（仅元数据，体积小）
python scripts/foreign_patent_fetch.py batch compare_list.txt --cmd info
```

---

## 7. 与其他途径的关系（G6 总览 v1.0.6）

| 文献类型 | 首选通道 | 备选 | 备注 |
|----------|---------|------|------|
| **中国专利** 文本/检索 | PatSeek `bool` / `patent` | — | 快速画像、检索式 |
| **中国专利** 全文 PDF / 附图 | **CNIPA 公布公告系统**（`cnipa_epub.py`） | — | PatSeek 无附图，故 CN 走官方 |
| **国外专利** 附图 | **Google Patents**（`foreign_patent_fetch.py figures`） | Espacenet 各国家局 | 无验证码、覆盖广 |
| **国外专利** 完整 PDF | **Espacenet**（`foreign_patent_fetch.py pdf`） | Google Patents / WIPO | 完整存档 |
| **非专利文献**（论文/标准/手册） | 知网/万方/IEEE Xplore/Google Scholar | — | 走机构订阅 |
| **使用公开**（销售/展会/产品） | `use_evidence_builder.py`（v1.1 规划） | 公证/固定 | 走证据链流程 |
| **涉案自认引用国外文献** | 直接采用涉案说明书背景技术 | — | 自认效力，无需另行检索 |

---

## 8. 证据清单中的标注规范

经本通道取得的文献，在证据清单与比对表中应注明来源与日期：

> **证据 X**：US10234567B2《Method and apparatus for ...》，Google Patents
> （patents.google.com/patent/US10234567B2/en）附图页，公开日 2019-03-14，
> 下载日期 2026-07-30。
>
> **证据 Y**：EP1234567A1《...》，Espacenet
> （worldwide.espacenet.com/patent/family/...）专利单行本 PDF，公开日 2020-05-22，
> 下载日期 2026-07-30。

附图页可直接用于 G7 同色标注比对；PDF 作为完整存档附于请求书证据清单。

---

## 9. 常见问题

### Q1：Google Patents 抓不到某些专利的附图？
- 部分文献（外观设计、临时申请）无附图
- 部分早期文献（1980 前）附图可能为 TIFF（脚本只取 PNG/JPG）
- 极少数情况下 Google Patents 改版导致 src 模式变化

**回退**：用 Espacenet / WIPO / 各国家局，或人工截图。

### Q2：Espacenet 频繁失败怎么办？
- 常态。Espacenet 有较强的反爬（IP 频率限制、JS 验证等）
- 失败时直接用人工浏览下载；或改用 Google Patents
- 不要用 VPN 高频切换（会触发更严的反爬）

### Q3：日本/韩国专利怎么抓？
- `foreign_patent_fetch.py` 已支持 JP/KR 公开号归一化
- JP 推荐 Google Patents 或 J-PlatPat
- KR 推荐 Google Patents 或 KIPRIS

### Q4：能抓到 WO 专利吗？
- 能。WO 公开号归一化已支持（`WO2021/123456A1` → `WO2021123456A1`）
- Google Patents 覆盖 WO；Espacenet 覆盖 WO；WIPO PatentScope 原文 PDF 最权威

### Q5：附图下载后还需要做什么？
- 至少做一次人工目视核查（确认自动下载的图与文献实际附图一致）
- 用 `figure_compare.py` 做 G7 同色标注
- 在证据清单中记录"附图来源 + 下载日期 + 公开日"

---

## 10. 脚本依赖

```bash
pip install requests beautifulsoup4 PyMuPDF Pillow
```

- `requests`：HTTP 抓取（必需）
- `beautifulsoup4`：HTML 解析（仅 `info` 子命令用，无 BS4 时用纯 regex 兜底）
- `PyMuPDF`（`fitz`）：PDF 拆附图（仅 `pdf --extract-figures` 用）
- `Pillow`：本 reference 关联的 `figure_compare.py` 用

无 `beautifulsoup4` 时 `info` 子命令仍可用（仅返回 title），但元数据不全。
无 `PyMuPDF` 时 `pdf --extract-figures` 选项无效，其他子命令不受影响。
