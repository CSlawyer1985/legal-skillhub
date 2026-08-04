# 检索策略参考手册

## 谷歌专利检索指南

### 基本检索URL

```
https://patents.google.com/?q=关键词1+关键词2&hl=zh&num=50
https://patents.google.com/?q=keyword1+keyword2&hl=en&num=50
```

### 高级检索参数

| 参数                         | 用途         | 示例                    |
| ---------------------------- | ------------ | ----------------------- |
| `q=`                       | 关键词检索   | `q=battery+electrode` |
| `assignee=`                | 按申请人检索 | `assignee=huawei`     |
| `before=priority:20240101` | 申请日限制   | 限制在某日期前          |
| `after=priority:20140101`  | 申请日限制   | 限制在某日期后          |
| `num=50`                   | 返回数量     | 最多50条                |

### 关键词提取策略

**第一步：确定技术主题词（必选）**

- 从技术手段中提取最核心的技术主题
- 例：锂电池正极材料 → "lithium battery cathode material" / "锂电池正极"

**第二步：提取技术特征关键词（2~3组）**

- 选取最有区分度的技术特征作为关键词
- 每组3~5个词，用AND关系组合

**第三步：多组合检索**

- 组合1：技术主题 + 核心技术手段
- 组合2：技术主题 + 技术功效
- 组合3：更宽泛的上位概念词

---

## 常见技术领域检索关键词模板

### 机械/结构类

- 中文：结构、装置、机构、系统、组件、连接件
- 英文：structure, device, mechanism, system, component, connector

### 电气/电子类

- 中文：电路、控制器、传感器、驱动、信号处理
- 英文：circuit, controller, sensor, driver, signal processing

### 化学/材料类

- 中文：组合物、制备方法、材料、涂层、处理工艺
- 英文：composition, preparation method, material, coating, treatment process

### 软件/算法类

- 中文：方法、系统、装置、处理器、存储介质
- 英文：method, system, apparatus, processor, computer-readable medium

### 医疗器械类

- 中文：医疗设备、治疗方法、诊断装置、植入物
- 英文：medical device, treatment method, diagnostic apparatus, implant

---

## 专利数据库备选

当谷歌专利无法访问时，按以下顺序尝试：

1. **Espacenet**（欧洲专利局）：`https://worldwide.espacenet.com/`
2. **国家知识产权局专利检索**：`https://pss-system.cponline.cnipa.gov.cn/`
3. **Lens.org**：`https://www.lens.org/lens/search/patent/`
4. **网页检索**：`site:patents.google.com [关键词]`
5. **学术检索参考**：Google Scholar 检索相关论文，辅助判断公知技术

---

## 相似度评估标准

### 高相似度（>70%）的特征

- 技术主题完全相同
- 核心技术手段高度重合（3个以上主要特征相同）
- 技术功效相似

### 中相似度（40%~70%）的特征

- 技术主题相同或相邻领域
- 部分技术手段重合（1~2个主要特征相同）
- 技术功效有交叉

### 低相似度（<40%）的特征

- 技术主题相近但方案差异大
- 技术手段基本不同
- 可能用于佐证公知常识

---

## 检索质量自检

完成检索后，确认：

- [ ] 至少进行了3轮不同关键词的检索
- [ ] 中英文关键词都进行了检索
- [ ] 找到了相似度"高"的专利至少3篇（作为D1/D2/D3）
- [ ] 专利列表按相似度正确排序
- [ ] 每篇专利记录了：专利号、标题、申请人、申请日、摘要
