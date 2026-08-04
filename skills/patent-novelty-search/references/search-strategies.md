# Patent Search Strategy Reference Manual
## Google Patents Search Guide
### Basic Search URLs
```
https://patents.google.com/?q=keyword1+keyword2&hl=zh&num=50
https://patents.google.com/?q=keyword1+keyword2&hl=en&num=50
```
### Advanced Search Parameters

| Parameter                     | Purpose                  | Example                  |
| ----------------------------- | ------------------------ | -----------------------  |
| `q=`                          | Keyword search           | `q=battery+electrode`    |
| `assignee=`                   | Assignee-based search    | `assignee=huawei`        |
| `before=priority:20240101`    | Priority date restriction| Restrict to prior to the date |
| `after=priority:20140101`     | Priority date restriction| Restrict to after the date|
| `num=50`                      | Result quantity          | Max. 50 results          |

### Keyword Extraction Strategy
**Step 1: Identify Technical Subject Terms (Mandatory)**
- Extract the core technical subjects from technical means
- Example: Lithium battery cathode material → "lithium battery cathode material" / "锂电池正极"

**Step 2: Extract Technical Feature Keywords (2~3 groups)**
- Select the most discriminative technical features as keywords
- 3~5 terms per group, combined with the AND operator

**Step 3: Multi-combination Search**
- Combination 1: Technical subject + Core technical means
- Combination 2: Technical subject + Technical effect
- Combination 3: Broader hypernyms

---
## Keyword Templates for Common Technical Fields
### Mechanical/Structural Category
- Chinese: 结构、装置、机构、系统、组件、连接件
- English: structure, device, mechanism, system, component, connector

### Electrical/Electronic Category
- Chinese: 电路、控制器、传感器、驱动、信号处理
- English: circuit, controller, sensor, driver, signal processing

### Chemical/Material Category
- Chinese: 组合物、制备方法、材料、涂层、处理工艺
- English: composition, preparation method, material, coating, treatment process

### Software/Algorithm Category
- Chinese: 方法、系统、装置、处理器、存储介质
- English: method, system, apparatus, processor, computer-readable medium

### Medical Device Category
- Chinese: 医疗设备、治疗方法、诊断装置、植入物
- English: medical device, treatment method, diagnostic apparatus, implant

---
## Alternative Patent Databases
If Google Patents is unavailable, try the following databases in order:
1. **Espacenet** (European Patent Office): `https://worldwide.espacenet.com/`
2. **CNIPA Patent Search and Analysis System**: `https://pss-system.cponline.cnipa.gov.cn/`
3. **Lens.org**: `https://www.lens.org/lens/search/patent/`
4. **Web Search**: `site:patents.google.com [keywords]`
5. **Academic Search Reference**: Search relevant papers on Google Scholar to assist in determining prior art

---
## Similarity Evaluation Criteria
### Characteristics of High Similarity (>70%)
- Identical technical subjects
- Highly overlapping core technical means (more than 3 identical main features)
- Similar technical effects

### Characteristics of Medium Similarity (40%~70%)
- Identical or adjacent technical subjects
- Partially overlapping technical means (1~2 identical main features)
- Intersecting technical effects

### Characteristics of Low Similarity (<40%)
- Similar technical subjects with significantly different solutions
- Basically different technical means
- Usable to support the proof of common general knowledge

---
## Search Quality Self-Check
Upon completion of the search, verify that:
- [ ] At least 3 rounds of searches with different keyword combinations have been conducted
- [ ] Searches have been performed with both Chinese and English keywords
- [ ] At least 3 patents with high similarity have been identified (as D1/D2/D3)
- [ ] The patent list is sorted correctly by similarity
- [ ] The following information is recorded for each patent: Patent No., Title, Assignee, Filing Date, Abstract