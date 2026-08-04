# 靶点提取规则

## 设计原则

1. **使用 `\b` 词边界**：避免 MET≠method, ER≠derivative, AR≠aryl 等误匹配
2. **具体模式优先**：如 `KRAS G12C` 优先于 `KRAS`
3. **全称识别**：如 "Bruton's tyrosine kinase" → BTK, "Cyclin-dependent kinase" → CDK
4. **模态分离**：PROTAC/Degrader/ADC/RNAi 独立标注，不与靶点混在一起

## 当前覆盖的靶点类别

### 激酶（Kinases）
KRAS, EGFR, ALK, BTK, JAK, TYK2, CDK, CDK12, MEK, ERK, AKT, PI3K, PI3Kα, mTOR, SHP2, FGFR, c-Met, RET, ROS1, NTRK, SOS1, FLT3, KIT, PLK1, RIP2, DYRK1, CLK, RAF/BRAF, SRC

### 表观遗传（Epigenetic）
HDAC, LSD1, EZH2, IDH, PRMT5, DNMT1, SIRT, BET

### GPCR & 受体（Receptors）
GLP-1R, GIPR, GCGR, CGRP, S1P, LPA, TSHR, THR-β, FXR, ROR, CCR, CXCR, Adenosine (A2A/A2B), GABA-A, mGluR, D1, 5-HT, CB1, EP4, KininR, AHR, GR, AR, GPI

### 免疫/炎症（Immune/Inflammation）
PD-1, PD-L1, Immune Checkpoint, TLR, STING/cGAS, TSLP, SGLT2

### DNA 损伤/修复（DNA Damage/Repair）
PARP, BCL-2, BFL-1, PARG, USP48

### 其他酶与靶点
PTPN, NRF2, DHODH, SOCE, CRBN, GlyT2, Kallikrein, DNM1L, MK2, TNKS, CFTR, Sigma1, PBP4, GDF8, EGLN1, AGT, PCSK9, FTO, RUNX1, CENP-M, CYP11B2, β-Catenin, Heparanase, Microtubule, Kv3, Hepcidin, MTARC1, AZD5004

### 模态标签（Modalities）
PROTAC, Degrader, ADC/Conjugate, RNAi/ASO

## 误匹配防护

| 误匹配来源 | 防护规则 |
|-----------|---------|
| method → MET | `\bMET\b` 但排除 `\bMET` + (HOD/ALLO/HYL/ABOL) |
| derivative → ER | `\bER\b` 不用，改为 `\bANDROGEN\s+RECEPTOR\b` |
| aryl → AR | `\bAR\b` 排除 (YL/EA/TI/GU/IN/CH/ED/OU/SE/DI/AD) |
| preparation → PR | `\bPR\b` 不用，改为 `\bPROGESTERONE\s+RECEPTOR\b` |

## 扩展

新增靶点时，在 `scripts/wipo_generate_report.py` 的 `TARGET_PATTERNS` 列表中添加 `(pattern, name)` 元组即可。
注意：具体模式（如 `KRAS\s+G12C`）必须放在通用模式（如 `KRAS`）之前。