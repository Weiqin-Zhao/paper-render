# Meta-Harness: End-to-End Optimization of Model Harnesses

> **论文信息**: Yoonho Lee, Roshen Nair, Qizheng Zhang (Stanford); Kangwook Lee (KRAFTON); Omar Khattab (MIT); Chelsea Finn (Stanford) — COLM 2026 / arXiv:2603.28052v1
>
> **关键词**: harness engineering, text optimization, coding agent, filesystem feedback, LLM system search, context engineering
>
> **项目主页**: https://yoonholee.com/meta-harness/
>
> **代码**: https://github.com/stanford-iris-lab/meta-harness-tbench2-artifact

---

## TL;DR

**核心问题**：LLM 应用的性能在很大程度上取决于 **harness**（围绕模型的代码：决定"存什么、取什么、喂什么"），但 harness 至今几乎全靠手工设计。已有的 text optimizer（ProTeGi / TextGrad / OPRO / GEPA / AlphaEvolve）都把反馈压得太狠——只条件于分数、摘要或短模板——无法支持 harness 优化所需的长程诊断。

**核心方法**：Meta-Harness 是一个 *外层* 搜索系统。它把一个 coding agent（Claude Code + Opus-4.6）作为 proposer，把**所有历史候选的源码、执行轨迹、评分**原原本本写到一个文件系统里，让 proposer 通过 `grep` / `cat` 等终端工具**自主选择读什么**。每次迭代前中位 **82 个文件** 被读，总反馈预算可达 **10 MTok/step**（比 prior text optimizer 大 3 个数量级）。

**关键结果**：
1. 在线文本分类：比 SOTA（ACE）高 **+7.7 pp**，context 仅 1/4；比 OpenEvolve/TTT-Discover 用 **1/10 的评估次数** 即匹配，最终再高 10 pp。
2. 数学检索推理：单个发现的 harness 在 5 个未见过的模型上平均提升 **+4.7 pp**（IMO 级题）。
3. TerminalBench-2：Opus-4.6 上 76.4%（超过手工 Terminus-KIRA），Haiku-4.5 上排 **#1**。

---

## 1. Motivation & Problem

### 1.1 Harness 的重要性

> **[Figure 1: Meta-Harness 学习曲线 & TerminalBench-2 leaderboard]**
> **(Left)** 在文本分类上，Meta-Harness 仅用 4 次评估就匹配次优方法的最终精度，并最终高出 10 pp。**(Right)** 在 TerminalBench-2 上，Meta-Harness 超过所有已公布的 Claude Haiku 4.5 harness。

一项最新工作 [Tian 2026 SWEBench-MC] 显示：**在同一个 benchmark 上，只换 harness 不换模型，性能能差 6×**。"harness engineering" 正在成为一个独立研究方向——手动检查 failure、调启发式、迭代设计。论文要问的是：**这个过程本身能不能自动化？**

### 1.2 现有 Text Optimizer 为什么不够用

一眼看过去，harness optimization 和文本优化很像——都是"根据过去尝试的反馈，迭代改进文本/代码 artifact"。但已有方法有一个共同问题：**反馈被压缩得太狠**。

| 类别 | 代表 | 反馈特点 |
|------|------|---------|
| 当前候选本身 | Self-Refine / TextGrad / OPRO | 只看 current candidate |
| 标量分数为主 | AlphaEvolve / AdaEvolve | 只传分数 + 少量 summary |
| 短模板/LLM 摘要 | GEPA / Feedback Descent | 有轨迹但被压成 template |

表 1（见下）估算：已有 text optimizer 每步可见 context 仅 **100–30k tokens**，远不够 harness search 所需的诊断量级。

> **[Table 1: tab:task_comparison — Text optimization 方法对比]**
> Meta-Harness 每次迭代的反馈预算约为 **10 MTok**，是 TTT-Discover（0.026 MTok）的 **~400×**，是 GEPA（0.008 MTok）的 **~1250×**。这种"数量级的膨胀"是 harness 任务的实际需求，不是过度设计。

**核心直觉**：harness 是**长程、有状态**的程序——某个"什么时候存什么"的决策可能几十步之后才体现影响。把反馈压成 summary 往往会把"追溯失败到早期 harness 决策"所需的线索扔掉。类比 retrieval/memory-augmented LM：context 应该被 agent **自适应检索**，而不是一次性打包进 prompt。

### 1.3 本文定位

Meta-Harness 在三条 research thread 的交叉点：
- **外部 memory + 自适应 access**（RAG / IRCoT / MemGPT / Recursive LM）
- **可执行代码搜索**（AlphaEvolve / OpenEvolve / AFLow / MemEvolve）
- **文本优化**（ProTeGi / TextGrad / GEPA / Feedback Descent）

与它们的关键差异：**把"看什么、怎么诊断"完全 delegated 给 coding agent**，外层循环只做极简维护（提议 → 评估 → 落盘），不硬编码任何 mutation/crossover 规则。

---

## 2. Method

### 2.1 总体架构

> **[Figure 2: fig:method — Meta-Harness 搜索循环]**
> **(1)** Agent 读取一个 filesystem $\mathcal{D}$，里面含有所有先前候选的源码、执行轨迹、分数；据此提议新 harness。**(2)** 在评估任务上运行新 harness。**(3)** 所有日志（代码、reasoning trace、评估分数）落入新目录，循环继续。

### 2.2 Formulation

固定一个模型 $M$，一个任务分布 $\mathcal{X}$。harness $H$ 是一个 stateful 程序，接受任务 $x \sim \mathcal{X}$，执行轨迹 $\tau \sim p_M(H, x)$，得分 $r(\tau, x)$。目标：

$$
H^* = \arg\max_{H} \; \mathbb{E}_{x \sim \mathcal{X},\; \tau \sim p_M(H, x)} \; r(\tau, x)
$$

多目标（accuracy + context cost）时走 Pareto dominance，不强行 scalarize。

### 2.3 关键设计 1：Filesystem 作为反馈通道

**不把历史写进 prompt，而是写进一个 proposer 能自己查询的文件系统**。每个候选 harness 有自己的目录：

```
filesystem/
├── harness_001/
│   ├── source.py
│   ├── scores.json
│   └── traces/
│       ├── task_0001.log
│       ├── task_0002.log
│       └── ...
├── harness_002/
│   └── ...
```

Proposer（Claude Code）通过 `grep`、`cat`、`ls` 等标准终端工具检索——**永远不把整个 filesystem 塞进 context**。

**为什么重要**：
- 在 TerminalBench-2 run 里，proposer **每次迭代中位读 82 个文件**，来自 **20+ 个先前候选**。单次评估可产生 10M tokens 诊断信息，远超任何能塞进 prompt 的量级。
- 这种访问模式是 **non-Markovian**：proposer 不是只看最近一个 parent，而是主动跨 20+ 候选做比较。

### 2.4 关键设计 2：Coding agent 而非 raw LLM

Proposer 必须是能**执行工具调用 + 修改代码**的 agent，理由：

1. 历史规模远超 context → 必须主动决定 *what to inspect*。
2. harness 是可执行代码 → 需要 `python` / 写入 / 语法验证等真实交互。
3. 这种 read-write-execute 工作流恰好是 frontier coding agent 被重度训练的场景。

文中实现：**proposer = Claude Code + Opus-4.6**。只给一个极简 skill 文档说明目录布局和哪些文件可/不可改，其他全部交给 agent 自由发挥。

### 2.5 搜索循环（Algorithm 1）

```
Input: tasks X, LLM M, proposer P, iterations N
Initialize: population H (一组有效 harness)
Initialize: filesystem D ← ∅

for H in H:                          # 先评估种子
    E_H ← Evaluate(H, M, X)
    D ← D ∪ {(H, E_H)}

for t = 1 … N:
    P 查询 filesystem D              # 读代码、分数、trace
    P 提出 k 个新 harness {H_1 … H_k}
    for H in {H_1 … H_k}:
        if H 通过接口校验:
            D ← D ∪ {(H, Evaluate(H, M, X))}

return Pareto frontier of D
```

**关键简洁性**：
- **没有** parent-selection 规则（proposer 可以自己挑任何 parent）
- **没有** mutation / crossover 算子
- **没有** persistent memory / 固定 scaffold
- 维护一个 Pareto frontier 但不影响 proposer 的读写自由

作者在 §2 里明确说这是 *deliberate simplicity*：把诊断和编辑决策交给 proposer，系统会随 coding agent 变强而自然变强（a la bitter lesson）。

### 2.6 代码空间搜索的好处

1. **因果诊断**：通过 trace，proposer 能推断 *why* 一个 harness 失败，而不是只知道 *that* 它失败（第 3 节实验会看到这点）。
2. **算法级修改空间**：从换 retrieval 策略到全程序重写，比模板填空/mutation operator 更灵活。
3. **自然正则**：coding model 倾向生成 *连贯的算法* 而不是脆弱硬编码的解 → 搜索 bias 在 reusable context-management 上。

### 2.7 实现细节

- Harness = 单文件 Python 程序，修改 task 特定的 prompt、retrieval、memory、orchestration。
- 典型 run：**20 iterations × ~3 candidates/iter ≈ 60 harness evaluations**。
- Proposer = Claude Code + Opus-4.6（max reasoning）。
- Base model $M$ 固定，按 domain 不同（GPT-OSS-120B / 20B / Claude Opus 4.6 / Haiku 4.5 等）。

---

## 3. 实验设计与结果

三个 domain：**在线文本分类**、**数学检索推理**、**智能体编程**。所有 domain 都与 (a) 手工 SOTA harness + (b) program-search 方法对比。

### 3.1 在线文本分类（§3.1）

**设置**（沿用 ACE [Zhang 2025]）：
- LLM：`GPT-OSS-120B`
- 数据集（3 个，难度与领域多样性）：
  - **LawBench**（法律，215 类）：从案情描述预测刑事指控
  - **Symptom2Disease / S2D**（医疗，22 类）：从症状预测疾病
  - **USPTO-50k**（化学，180 类）：从产物分子预测前体反应物
- 初始化种群：zero-shot + few-shot + ACE + MCE
- 20 iterations × 2 candidates = 40 candidates

#### 3.1.1 vs. 手工 SOTA harness — Table 2 (`tab:main_results`)

| Harness | USPTO | S2D | Law | Avg Acc | Ctx (K) ↓ |
|---|---|---|---|---|---|
| Zero-Shot | 12.0 | 63.2 | 7.0 | 27.4 | 0 |
| Few-Shot (8) | 14.0 | 67.9 | 21.0 | 34.3 | 2.0 |
| Few-Shot (32) | 13.0 | 72.2 | 21.0 | 35.4 | 7.9 |
| Few-Shot (all) | 15.0 | 78.3 | 29.0 | 40.8 | 12.3 |
| MCE | 14.0 | 83.0 | 23.0 | 40.0 | 28.5 |
| ACE | **16.0** | 77.8 | 29.0 | 40.9 | 50.8 |
| **Meta-Harness** | 14.0 | **86.8** | **45.0** | **48.6** | 11.4 |

**亮点**：
- 准确率超 ACE **+7.7 pp**（48.6 vs 40.9）
- Context 仅 **11.4k**（ACE 50.8k，MCE 28.5k）→ **同时精度高 + context 省 4×**
- LawBench 提升尤其明显（45 vs 29，+16 pp）

#### 3.1.2 vs. text optimizer — Table 3 (`tab:text_classification_optimizer_comparison`)

相同 proposer（Opus-4.6）+ 相同 evaluation 预算：

| Method | Median | Best |
|---|---|---|
| GEPA | 32.6 | 40.2 |
| Best-of-N | 34.0 | 44.2 |
| OpenEvolve | 39.1 | 43.3 |
| TTT-Discover | 34.1 | 45.6 |
| **Meta-Harness** | **50.0** | **56.7** |

> **Takeaway**：Meta-Harness 在 **1/10 评估次数** 内匹配 OpenEvolve/TTT-Discover 的最终精度，然后继续超出 10+ pp。

#### 3.1.3 Ablation — Table 4 (`tab:text_classification_history_ablation`)

| Interface | Scores | Code | Summary | Traces | Median | Best | #Runs > ZS |
|---|:-:|:-:|:-:|:-:|---|---|---|
| Scores Only | ✓ | ✓ | ✗ | ✗ | 34.6 | 41.3 | 26 |
| Scores + Summary | ✓ | ✓ | ✓ | ✗ | 34.9 | 38.7 | 23 |
| **Meta-Harness (full)** | ✓ | ✓ | — | ✓ | **50.0** | **56.7** | **39** |

**结论**：**raw execution traces 是最关键的成分**。
- Summary 几乎没提升（34.6 → 34.9 中位），甚至在 Best 上下降（41.3 → 38.7）。
- 加入 traces 后才跳到 50.0 / 56.7——即便是 median candidate 都超过 ablation 的 best。
- **解读**：summary 会把"能定位失败模式的诊断细节"压掉；raw trace 不可替代。

#### 3.1.4 Pareto frontier — Figure 3 (`tab:classification_pareto`)

> **[Figure 3: fig:pareto — Accuracy vs context tokens Pareto]**
> Meta-Harness 的 accuracy-context 前沿严格优于所有对比方法。

搜索过程中自然 emerge 出 8 个 Pareto 最优变体，accuracy 40–48.6%、context 5.4k–45.5k：

| 变体 | USPTO | S2D | Law | Avg | Ctx |
|---|---|---|---|---|---|
| Draft Verification | **18.0** | 85.4 | 17.0 | 40.1 | 5.4 |
| Error-Annotated | 9.0 | 87.7 | 24.0 | 40.2 | 22.3 |
| CoT Replay | 13.0 | 88.2 | 25.0 | 42.1 | 23.3 |
| Cluster Coverage | 12.0 | 86.8 | 33.0 | 43.9 | 31.2 |
| Cascade Retrieval | 12.0 | 86.8 | 36.0 | 44.9 | 39.2 |
| RRF + Contrastive | **18.0** | 89.6 | 35.0 | 47.5 | 41.4 |
| Relevance + Contrastive | **18.0** | **90.6** | 36.0 | 48.2 | 43.9 |
| **Label-Primed Query** | 14.0 | 86.8 | **45.0** | **48.6** | 45.5 |

主文选的是 Label-Primed Query（后续 OOD 也用这个）。

#### 3.1.5 OOD 泛化 — Table 5 (`tab:ood_results`)

9 个新数据集（SciCite / FiNER / Amazon5 / FPB / GoEmo / Bank77 / AGNews / SciTail / TwHate），搜索期间从未见过：

| Harness | Avg Acc | Ctx (K) ↓ |
|---|---|---|
| Zero-shot | 67.0 | — |
| Few-shot (8) | 68.9 | 2.2 |
| Few-shot (32) | 69.6 | 5.2 |
| Few-shot (all) | 68.2 | 7.4 |
| ACE | 70.2 | 11.7 |
| **Meta-Harness** | **73.1** | **7.3** |

- 平均高 ACE **+2.9 pp**，context 还更省。
- 9 个数据集里有 6 个刷新最佳。
- 反直觉观察：**few-shot 加到 32 以上在 7/9 任务上反而掉点**（过多示例反而干扰）。

### 3.2 数学检索推理（§3.2）

**动机**：数学解题共享可复用的 proof pattern → 检索在原则上应该有帮助；但以往结果显示 retrieval 在 reasoning-heavy math 上远不如 fact-grounded domain 有效。作者认为**难点不是"要不要检索"，而是"检索策略到底怎么设计"** —— 正好适合搜索。

**设置**：
- 检索语料：**535k 道题**（OpenMathReasoning / DeepMath / NuminaMath / PolyMath / Omni-MATH / FineProofs / AIME / Putnam-AXIOM），精心去重 + 去污染（Jaccard 0.8）
- Search set：250 道 Olympiad 难题（OlympiadBench + Omni-MATH hard）
- 搜索期间 base model：GPT-OSS-20B
- **40 iterations × ~2.7 candidates = 109 个候选 retrieval harness**
- 测试：**200 道 IMO 级从未见过的题**（IMO-AnswerBench 100 + IMO-ProofBench 60 + ArXivMath Dec 2025 (17) + ArXivMath Jan 2026 (23)）
- 测试模型（5 个都没在搜索中见过）：GPT-5.4-nano / GPT-5.4-mini / Gemini-3.1-Flash-Lite / Gemini-3-Flash / GPT-OSS-20B

**结果** — Table 6 (`tab:math_results`)：

| Method | GPT-5.4n | GPT-5.4m | Gem-3.1FL | Gem-3F | GPT-20B | **Avg** |
|---|---|---|---|---|---|---|
| No Retriever | 23.0 | 28.8 | 28.6 | 42.6 | 47.6 | 34.1 |
| Dense (k=1) | 27.1 (+4.1) | 24.5 (-4.3) | 31.3 (+2.7) | 42.3 (-0.3) | 46.9 (-0.7) | 34.4 (+0.3) |
| Dense (k=5) | 31.1 (+8.1) | 28.3 (-0.5) | 37.1 (+8.5) | 47.2 (+4.6) | 46.7 (-0.9) | 38.1 (+4.0) |
| Random Few-shot | 23.1 (+0.1) | 24.5 (-4.3) | 31.0 (+2.4) | 40.4 (-2.2) | 41.8 (-5.8) | 32.2 (-1.9) |
| BM25 | 30.2 (+7.2) | 29.2 (+0.4) | 32.8 (+4.2) | 46.6 (+4.0) | 48.9 (+1.3) | 37.5 (+3.4) |
| **Meta-Harness** | 31.7 (+8.7) | 30.4 (+1.6) | 34.9 (+6.3) | 46.3 (+3.7) | 50.6 (+3.0) | **38.8 (+4.7)** |

**亮点**：
- 相比 no-retrieval 平均 +4.7 pp；**5 个模型全部提升**（其他方法大多至少在一个模型上退化）
- 超 BM25 +1.3 pp 平均，但避免了 Dense/Random 在某些模型上的 negative transfer
- **跨模型迁移**：搜索只见过 GPT-OSS-20B，却在 4 个未见模型上都涨——说明 harness 学到的是通用 retrieval 策略

**发现的 harness（§A.6）**：4-route BM25 程序：
1. **组合**：BM25@20 → dedup to 8 → rerank（词频 + 难度）→ keep 3
2. **几何**：1 hard NuminaMath ref + 2 raw BM25 neighbors（不 rerank）
3. **数论**：BM25@12 → rerank（词频 + 难度 + "解法早期明示技术"bonus）→ keep 3
4. **代数/其他**：BM25@10 → rerank → **adaptive K**（按 top 分数集中度决定取几个）

路由用**轻量词法 predicate**（关键词 + 小量正则）。论文特别强调：**所有阈值、per-route 数量、rerank 项，都是 40 轮搜索中涌现出来的，不是事后 hand-tune**。最终程序甚至是两条成功搜索谱系的 merge（一条贡献几何，一条贡献组合），由 proposer 自主完成。

### 3.3 TerminalBench-2（§3.3）

**设置**：
- 89 任务，需要长程自主执行、复杂依赖、领域知识
- Base models：Claude Opus 4.6 / Claude Haiku 4.5
- 种子 harness：Terminus 2、Terminus-KIRA
- 搜索集 = 测试集（discovery problem 定位，公开实践也是如此）；用正则审计检查 task-specific string 泄露

**结果** — Table 7 (`tab:terminalbench_results`)：

**Claude Opus 4.6**:
| Harness | Auto | Pass % |
|---|:-:|---|
| Claude Code | ✗ | 58.0 |
| Terminus 2 | ✗ | 62.9 |
| Mux | ✗ | 66.5 |
| Droid | ✗ | 69.9 |
| TongAgents | ✗ | 71.9 |
| MAYA-V2 | ✗ | 72.1 |
| Terminus-KIRA | ✗ | 74.7 |
| Capy | ✗ | 75.3 |
| ForgeCode | ✗ | 81.8 |
| **Meta-Harness** | ✓ | **76.4** |

**Claude Haiku 4.5**:
| Harness | Auto | Pass % |
|---|:-:|---|
| OpenHands | ✗ | 13.9 |
| Claude Code | ✗ | 27.5 |
| Terminus 2 | ✗ | 28.3 |
| Mini-SWE-Agent | ✗ | 29.8 |
| Terminus-KIRA | ✗ | 33.7 |
| Goose | ✗ | 35.5 |
| **Meta-Harness** | ✓ | **37.6** |

**亮点**：
- Opus 4.6：76.4% 超 Terminus-KIRA (74.7%)，leaderboard 第 2
  - ForgeCode 81.8% 但作者无法从公开代码复现 → 其成绩依赖未公开组件
- Haiku 4.5：37.6% 排 **#1**，比次好 Goose (35.5%) 高 2.1 pp
- "自动发现" 能在被 *多个团队直接手调* 的活跃 benchmark 上刷新记录，说明 long-horizon text optimization 已能触达工业前沿

**发现的 harness（§A.7）**：在 Terminus-KIRA 基础上加 **environment bootstrap**：
- 开第一轮 LLM 调用前，跑一个 compound shell 命令收集 sandbox 快照：
  - `pwd` + `/app` 目录列表（≤20 entries）
  - 可用语言：Python / GCC / G++ / Node / Java / Rust / Go 及版本
  - 包管理器：pip / apt-get
  - 可用内存
- 作为 `[Environment Snapshot]` 注入初始 prompt
- 15s timeout + 静默失败（不破坏陌生环境下的 agent）
- 仅约 +80 行代码

**Per-task 分析**：相对 Terminus-KIRA 在 89 任务中的 7 个上提升，最大增益在 `protein-assembly`、`path-tracing` 这类**需要领域特定工具但环境不明确**的任务——恰好对应 "bootstrap 消掉 2-4 轮环境摸索" 的价值。

### 3.4 Proposer 的定性行为（§A.1、A.2）

#### 3.4.1 文件访问统计（TerminalBench-2 run, 10 iter, Opus 4.6）

| 指标 | 值 |
|---|---|
| 每迭代读文件数 中位 | **82** |
| 每迭代读文件数 范围 | 69–99 |
| Harness 源码 | 41% |
| 执行 trace | 40% |
| 分数/summary | 6% |
| 其他 | 13% |

→ 源码和 trace 平均被关注，**proposer 的访问模式是非 Markov 的**。

#### 3.4.2 因果推理的搜索轨迹（TerminalBench-2 trace 摘录）

这是论文最 compelling 的 qualitative evidence——**proposer 不是在做随机 mutation，而是在做因果诊断**：

- **Iter 1–2**：两个看似合理的 bugfix 都从 64.4% baseline 大幅退步（58.9%、57.8%）。两者都捎带了"cleanup 导向的 prompt 模板"。
- **Iter 3（关键）**：proposer 明确指出 "**regression 的真正 root cause 是 prompt 变更导致 agent 在完成前删除必要状态，而不是 structural bugfix 本身**"。它 *隔离* 了 confound——只保留 marker stripping，回滚 prompt——掉 1.1 pp 而不是 6.7 pp，验证了假设。
- **Iter 4–6**：继续探测完成流程 bug，全部 regress。Proposer 学到一个经验教训：**修改 prompt / completion flow 是高风险的，即便 local 假设听起来合理**。
- **Iter 7（胜出）**：从"修控制流"转向"在循环开始前添加信息"——纯 additive 的 env bootstrap，一举成为最好候选。Proposer 自己清楚说明 *why* 它应该更安全：不触碰已证明脆弱的 completion 机制，只在难任务上补信息。
- **Iter 8**：尝试组合 env bootstrap + marker stripping。
- **Iter 10**：**跨 run 迁移**——引用另一条搜索链的经验 ("don't cleanup service artifacts" 值 +18 pp)。

这个轨迹是全论文最重要的存在性论证：**只有 filesystem 完整历史才能支持这种"识别 confound → 隔离变量 → pivot 到更安全的修改空间"的诊断推理**。

---

## 4. Discussion

### 4.1 主要贡献总结

1. **方法**：Meta-Harness 把 harness optimization 重新框定为 "coding agent 在 filesystem 历史上做长程诊断 + 代码空间搜索"，用极简外层循环替代手工 search 结构。
2. **经验发现**：raw execution traces 不可压缩（ablation 证明）；filesystem-size 反馈 (10 MTok/iter) 比 prior text optimizer 大 3 个数量级且确实被用上。
3. **跨任务泛化**：单个搜索出的 harness 能跨数据集（OOD 分类）+ 跨模型（数学检索 5 个模型全涨）。
4. **可解释性副产物**：在代码空间 overfit 是可肉眼检查的（brittle if-chain、hard-coded mapping），这在权重空间不成立。

### 4.2 作者自述的 limitation

- 只测了 3 个 domain，没横扫。
- 只用了 **一个** proposer（Claude Code + Opus-4.6）；作者说怀疑这个 workflow 是 "2026 年初 coding agent 才刚够强"。
- TerminalBench-2 里 search set = test set（discovery problem 定位）——作者做了正则审计但还是有过拟合隐忧。

### 4.3 作者展望

- **Co-evolve harness + model weights**：让策略塑造模型所学、模型所学反塑策略。
- 横扫不同 proposer agent 看方法如何 scale。

---

## 5. 个人思考与组会讨论点

### 值得肯定的设计

1. **"把反馈做大"本身是非平凡贡献**。很多 text optimizer 把"feedback size 小"当成 feature（"我们只需要 scalar score"），Meta-Harness 反其道把反馈做到 10M token，然后证明 raw trace 不可压缩。这个方向在 coding agent 足够强之前甚至不可执行——工程和科学同时成立。
2. **Bitter lesson 对齐**：刻意不加 mutation 算子、不加 parent-selection。作者明确写 "as coding agents become more capable, this method improves automatically"。这种"留给 capability growth"的系统设计在 2026 年看越发正确。
3. **Ablation 设计干净**：scores-only / scores+summary / full-trace 三组把"summary 是否足够"这个自然反驳打得很实。summary 反而在 Best 上掉点（41.3 → 38.7），暗示压缩本身是 negative information carrier。
4. **Qualitative trace 作为论据**（§A.2）比纯 benchmark 更说服人——proposer 能主动识别 "prompt intervention 是 confound" 并 pivot 到 additive modification，这是 "filesystem 给了真诊断能力" 最硬的存在性证据。

### 可深入讨论的问题

1. **Cost 讨论完全缺失**：没有列出单次搜索 run 的成本（LLM API $ / wall clock / Claude Code 调用次数）。60 个 candidate × 每个 10M token 的 proposer 上下文 + 每个评估的 base model cost，在 Opus-4.6 上估计数千到上万美元一次 run。没有 $/accuracy 的曲线，难以判断"比手工贵多少"。
2. **Test set = Search set（TerminalBench-2）的严重性没被充分处理**。Discovery problem 这个 framing 是公开实践没错，但 "发现的 harness 过拟合到具体 89 任务的哪些 regex pattern" 这个问题靠手动 + 正则审计真能挡住吗？作者自己承认"resulting harness is specialized to TerminalBench-2 regime"——应该有一个独立的 held-out 测试。
3. **对 proposer 本身的依赖没有消融**。如果 proposer 换成 GPT-5 或者更弱的 Sonnet 4.6，整个 pipeline 还 work 吗？论文只说"依赖特定强 coding agent"，但没有给出"proposer capability 到什么阈值这个 workflow 就破产"的曲线。
4. **反馈的 marginal value 递减曲线**。从 scores 到 traces 有大跳（34.6 → 50.0），但从 5M tokens 到 10M tokens 呢？论文 claim "3 个数量级以上"，但没有 scaling 实验证明"越多越好"——只证了"比 100k 多得多"。
5. **Harness 是 stateful program 但评估是跨 task 取平均**。对于 online classification 这种真正 stateful 的 setting（memory 在 task 间累积），Pareto 结果是否对 task 顺序敏感？论文没提。
6. **安全和对齐问题**：一个 coding agent 自由读写 filesystem、跑任意 shell 命令（env bootstrap 本身就是例子）——在生产级 pipeline 里这是个很大的 attack surface / 稳定性风险。文中只字未提。
7. **方法命名的递归**：Meta-Harness 本身也是 harness（决定 proposer 看什么）——那能不能用 Meta-Harness 优化 Meta-Harness？作者在脚注里暗示这是更高阶的问题但没做实验。

### 与相关工作的对比

| 系统 | 搜索空间 | 反馈形式 | 反馈规模 | 核心创新 |
|---|---|---|---|---|
| GEPA | prompt | rollout summary | 2–8k tok/step | per-candidate reflection |
| OpenEvolve / AlphaEvolve | code (单函数) | program database + score | 4–22k tok/step | fixed mutation + tournament |
| TextGrad | text artifact | textual feedback on current | 15k tok/step | "text as differentiable" |
| TTT-Discover | solution fragments | prev fragment | 26k tok/step | PUCT search over text |
| **Meta-Harness** | **完整可执行 harness** | **filesystem (code + trace + score)** | **10M tok/step** | **coding agent 自选读什么** |

---

## 6. 技术细节速查

| 项目 | 值 |
|---|---|
| Proposer | Claude Code + Opus-4.6 (max reasoning) |
| 每 run iterations | 20（分类/TerminalBench）/ 40（math） |
| 每 iter candidates | ~2–3 |
| 单 run candidate 总数 | 40（分类）/ 109（math）/ ~60（TerminalBench） |
| 每 iter proposer 读文件中位 | 82（69–99 范围） |
| 每 iter 反馈 tokens | ~10 M |
| Harness 单文件规模 | 100–1000 行 Python |
| 分类 base model | GPT-OSS-120B (冻结) |
| Math 搜索 base model | GPT-OSS-20B |
| Math 测试 base models | GPT-5.4-nano / GPT-5.4-mini / Gemini-3.1-Flash-Lite / Gemini-3-Flash / GPT-OSS-20B |
| TerminalBench base models | Claude Opus 4.6 / Claude Haiku 4.5 |
| Math 检索语料规模 | 535,356 problems |
| Math 测试集 | 200 IMO 级（IMO-AnswerBench 100 + IMO-ProofBench 60 + ArXivMath 40） |
| OOD 分类 | 9 datasets（SciCite/FiNER/Amz5/FPB/GoEmo/Bank77/AGNews/SciTail/TwHate） |
| Final 发现的 math harness 路由 | combinatorics / geometry / number theory / default |
| Final 发现的 TerminalBench harness 新增 | env bootstrap（~80 lines） |
| Final 发现的分类 harness (best) | Label-Primed Query（primer + coverage block + contrastive pairs） |

---

## 7. 实用 takeaways（§A.8）

作者总结的应用 tips（非科学 claim，但对复现很有用）：

1. **写好 skill 文档**：比调 iteration 数更重要。约束输出格式、安全行为，**不** 约束诊断流程。准备 3–5 次 3–5 iteration 的调试 run 专门打磨 skill。
2. **起点要低、search set 要硬**：对 baseline "易" 的任务搜索无物可优化。50–100 例 search set 就够。
3. **Log 要机器可查询**：JSON、层级、可读文件名、regex-friendly。
4. **给 proposer 一个小 CLI**（可选）：`list_pareto` / `top_k` / `diff_runs` 等。
5. **轻量 validation 先行**：candidate 过简单 import + instantiate test 再跑完整 eval，能挡掉大多数 malformed 候选。
6. **Eval 别让 proposer 做**：独立 harness 跑 eval 写回 filesystem。
