# 信息提取 —— 扩展说明（数据截至 2026 年 7 月）

> 规范数据集的切片。完整跨垂直数据 + 更新指南：仓库 `data/scorecard-2026-07.md`。
> 数字是时点先验，而非定论——高风险路由请重新核查实时来源。

## 2. 信息提取

**来源：** legalbenchmarks.ai ——“信息提取”（29 项任务）。文档以**原生、未转换形式**发送，因此文件读取（包括扫描文档）也是被测试的一部分。与起草相同的双轴评分标准。

| 排名 | 模型            | 提供者  | 可靠性 | 实用性 | 每任务成本 |
|-----:|------------------|-----------|------------:|-----------:|----------:|
| 1    | GPT 5.6 Sol      | OpenAI    | 89.7%       | 2.78       | ~$0.19    |
| 2    | Claude Opus 4.8  | Anthropic | 86.2%       | 2.54       | ~$0.29    |
| 2    | Claude Fable 5   | Anthropic | 86.2%       | 2.51       | ~$0.63    |
| 4    | GPT-5.5          | OpenAI    | 82.8%       | 2.62       | $0.15     |
| 5    | Grok 4.5         | xAI       | 79.3%       | 2.70       | ~$0.19    |
| 6    | Claude Sonnet 4.6| Anthropic | 72.4%       | 2.47       | $0.13     |
| 7    | Gemini 3.1 Pro   | Google    | 65.5%       | 2.51       | $0.07     |
| 7    | Gemini 3.5 Flash | Google    | 65.5%       | 2.76       | ~$0.08    |
| 9    | DeepSeek V4 Pro  | DeepSeek  | 62.1%       | 2.37       | ~$0.03    |
| 10   | GPT-5.4-mini     | OpenAI    | 58.6%       | 2.75       | ~$0.01    |
| 11   | Qwen 3.7 Max     | Alibaba   | 55.2%       | 2.55       | ~$0.03    |

**事实与要点**
- **GPT 5.6 Sol** —— 在*穷尽性条款检索*和*跨文档比较*方面最佳。盲点：**扫描文档**，以及**将条件性答案扁平化为绝对表述**（“如 X 则 Y”→ “Y”）。须核验条件性内容。
- **Opus 4.8 / Fable 5** —— 最可靠的一对（并列第 2），但**回答最为冗长**；你为输出 token 和后处理付费。
- **Grok 4.5** —— **所有模型中处理扫描文档最佳**，但在完整性上回报不足（“几乎所有”而非全部）。图像密集/接近 OCR 的提取路由到此，然后复查覆盖率。
- **廉价档（Qwen 3.7 Max、GPT-5.4-mini、DeepSeek V4 Pro）** —— 可靠性垫底（55–62%）。适合低风险分流，不适合你将依赖的提取。

**相关学术锚点（Wei Chen / Atticus Project）：** **CUAD**（条款提取，510 份合同，41 种条款类型）、**MAUD**（并购阅读理解，92 种问题类型）、**ACORD**（条款检索，1–5 相关性）。这些是该领域需要可复现的提取/检索评估时使用的开放数据集。

---

## 跨领域告诫（融入每一个路由决策）

1. **能力 ≠ 可控性**（Wei Chen，Atticus Project）。高基准分数不意味着模型保持在范围内、真实引用，或可安全无人监督部署。治理是与原始性能分离的独立轴线。
2. **全捕获现实**（Harvey）。能发现 10 个风险中 8 个的审查不是 80% 有用——它在实质上不完整。高风险工作路由应追求可靠性，而非平均质量。
3. **评分并不完美。** legalbenchmarks.ai 的可靠性由*单一* LLM 裁判（Claude Sonnet 4.6）评分；实用性由 2 人裁判小组评分（约 82% 一致）。他们自己的偏差检查：Sonnet 在两个榜单上均不居首，且 Anthropic 模型在篇幅长度上排名最低——这证明不存在自我评分偏袒，但 LLM 评判的分数仍非基准真相。
4. **覆盖面狭窄。** legalbenchmarks.ai 仅限英语、偏重美国/英国、单轮对话、每任务一次运行（无漂移/一致性测试），且任务集为私有。Vals LegalBench 是选择题推理，而非起草。**非美国、非英语、多轮和长周期工作测量不足。**
5. **基准漂移与路由坍缩。** 这里的数字每月都会过时；而总是选择单一主导模型的路由器已停止路由。当新的前沿模型发布时须重新验证。
6. **静默质量退化。** 成本节省立即体现在账单上；质量损失几天后才体现在工作产品中。任何成本驱动的降级都应以抽查为门禁。

---

## 实时来源 —— 高风险路由前重新核查

- 合同起草与信息提取：https://www.legalbenchmarks.ai/leaderboard（+ /research/phase-2-research）
- 法律推理（LegalBench，124 个模型，实时）：https://www.vals.ai/benchmarks/legal_bench
- 代理式法律任务设计：https://www.harvey.ai/blog/introducing-harveys-legal-agent-benchmark
- “通往更好的法律 AI 之路：基准”（Wei Chen）：https://www.linkedin.com/pulse/path-better-legal-ai-benchmarks-wei-chen-jpksc
- Atticus 开放数据集（CUAD/MAUD/ACORD）：https://www.atticusprojectai.org/
- 通用型交叉核查：https://artificialanalysis.ai/leaderboards/models · https://lmarena.ai · https://www.swebench.com
- 长上下文效率（Mamba 与 transformer 在长法律文档上的对比）：https://arxiv.org/abs/2509.00141

**快照日期：2026-07。** 如今天晚于 2 个月以上，将排名视为可疑并重新拉取实时榜单。
