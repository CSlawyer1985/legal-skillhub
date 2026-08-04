# 合同起草——扩展笔记（数据截至 2026-07）

> 规范数据集的切片。完整跨垂直领域数据 + 更新指南：仓库 `data/scorecard-2026-07.md`。
> 数字是时点先验，而非定论——高风险路由请重新核实实时来源。

## 1. 合同起草

**来源：** legalbenchmarks.ai——“合同起草”（34 项任务，第 3 期，每月更新）。
**指标：** `Reliability`（可靠性）= 在律师编写的检查清单上*完全*正确的任务占比（二元计分；一项遗漏即整项任务失败）。`Usefulness`（有用性）= 1-3 均值（清晰度 / 长度 / 结构）。成本 = $/任务。

| 排名 | 模型            | 提供者  | 可靠性 | 有用性 | 成本/任务 |
|-----:|------------------|-----------|------------:|-----------:|----------:|
| 1    | Claude Opus 4.8  | Anthropic | 67.6%       | 2.67       | ~$0.29    |
| 2    | Claude Fable 5   | Anthropic | 61.8%       | 2.66       | ~$0.63    |
| 3    | Grok 4.5         | xAI       | 58.8%       | 2.61       | ~$0.19    |
| 4    | Gemini 3.5 Flash | Google    | 55.9%       | 2.60       | ~$0.08    |
| 5    | Claude Sonnet 4.6| Anthropic | 50.0%       | 2.63       | $0.13     |
| 5    | Gemini 3.1 Pro   | Google    | 50.0%       | 2.69       | $0.07     |
| 7    | GPT 5.6 Sol      | OpenAI    | 44.1%       | 2.75       | ~$0.19    |
| 7    | Qwen 3.7 Max     | Alibaba   | 44.1%       | 2.67       | ~$0.03    |
| 9    | GPT-5.5          | OpenAI    | 41.2%       | 2.77       | $0.15     |
| 10   | DeepSeek V4 Pro  | DeepSeek  | 26.5%       | 2.68       | ~$0.03    |
| 10   | GPT-5.4-mini     | OpenAI    | 26.5%       | 2.55       | ~$0.01    |

**事实 / 注意事项**
- **Opus 4.8**——最佳全能起草者；独特地愿意*标记相互矛盾的指示*而非直接绕过起草。事实：最高可靠性。注意：不是最便宜的。
- **Fable 5**——质量与 Opus 持平，但每任务成本约 2.2 倍且未超越它。注意：起草而言定价过高。
- **Grok 4.5**——最佳非 Anthropic 起草者，前四名中最便宜；独特擅长*保留已经稳健的语言不动*（更少的无谓重写）。高价值之选。
- **GPT 5.6 Sol**——**最高有用性（2.75）是一个陷阱：**“比准确更光鲜”。其草稿中 >50% 遗漏隐藏在流畅文笔后的 ≥1 项指示。不要因其可读性而将起草路由至此。
- **所有模型**——在冲突检测方面薄弱；GPT 5.6 Sol 在静默绕过矛盾方面最差。

---

## 跨领域注意事项（融入每个路由决策）

1. **能力 ≠ 可控性**（Wei Chen，Atticus 项目）。高分不意味着模型能保持在范围内、真实引用或可安全无人监督部署。治理是与原始性能不同的独立轴线。
2. **全通过现实**（Harvey）。捕捉 10 项风险中 8 项的审查不是 80% 有用——它在实质上不完整。高风险工作按可靠性路由，而非平均质量。
3. **评分不完善。** legalbenchmarks.ai 的可靠性由*单一* LLM 评委（Claude Sonnet 4.6）评分；有用性由 2 人评委组（约 82% 一致性）评分。其自身偏见检查：Sonnet 在两个榜单上均未居首，且 Anthropic 模型在长度上排名最低——证明不存在自评分偏袒，但 LLM 评分数值仍非基准真值。
4. **覆盖面窄。** legalbenchmarks.ai 仅限英文、偏向美/英、单轮、每任务一次运行（无漂移/一致性测试），且任务集不公开。Vals LegalBench 是选择题推理，而非起草。**非美国、非英语、多轮和长期工作未被充分测量。**
5. **基准漂移与路由坍缩。** 这里的数字每月过时；而且总是选择单一主导模型的路由器已经停止路由。新前沿模型发布时重新验证。
6. **静默质量倒退。** 成本节省立即显示在账单上；质量损失数日后才出现在工作产品中。任何成本驱动的降级都必须以抽查作为门禁。

---

## 实时来源——高风险路由前重新核实

- 合同起草与信息提取：https://www.legalbenchmarks.ai/leaderboard（+ /research/phase-2-research）
- 法律推理（LegalBench，124 个模型，实时）：https://www.vals.ai/benchmarks/legal_bench
- 代理式法律任务设计：https://www.harvey.ai/blog/introducing-harveys-legal-agent-benchmark
- “通往更好法律 AI 之路：基准”（Wei Chen）：https://www.linkedin.com/pulse/path-better-legal-ai-benchmarks-wei-chen-jpksc
- Atticus 开放数据集（CUAD/MAUD/ACORD）：https://www.atticusprojectai.org/
- 通用交叉检查：https://artificialanalysis.ai/leaderboards/models · https://lmarena.ai · https://www.swebench.com
- 长上下文效率（Mamba 与 transformer 处理长法律文档）：https://arxiv.org/abs/2509.00141

**快照日期：2026-07。** 如今天晚于 2 个月以上，将排名视为可疑并重新拉取实时榜单。
