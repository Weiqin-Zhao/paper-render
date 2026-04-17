# CoEvoSkills: Self-Evolving Agent Skills via Co-Evolutionary Verification

> **论文信息**: Hanrong Zhang, Shicheng Fan, Henry Peng Zou, Yankai Chen, Zhenting Wang, Jiayu Zhou, Chengze Li, Wei-Chieh Huang, Yifei Yao, Kening Zheng, Xue (Steve) Liu, Xiaoxiao Li, Philip S. Yu
>
> **机构**: UIC, MBZUAI, McGill, Columbia, Zhejiang, UBC
>
> **投稿**: COLM 2026 (preprint, arXiv:2604.01687v2)
>
> **项目主页**: https://zhang-henry.github.io/CoEvoSkills/
>
> **关键词**: LLM Agent, Agent Skills, Self-Evolution, Co-Evolution, Surrogate Verifier, Claude Code, Codex, SkillsBench

---

## TL;DR

**核心问题**: Anthropic 的 "agent skill" 概念把工具 (tool) 扩展为多文件结构化工作流包，但当前几乎全部依赖人工编写——既昂贵，又常因 *human–machine cognitive misalignment* 降低 agent 性能（某些领域甚至负收益）。

**核心贡献**: 提出 **CoEvoSkills**，一个由 **Skill Generator** + **Surrogate Verifier** 两个信息隔离的 LLM session 共同进化的框架。Surrogate Verifier 在看不到真值测试内容的情况下合成测试套件，向 Generator 提供结构化失败诊断；Ground-Truth Oracle 只返回 opaque pass/fail bit 以防 overfitting。

**实验结果**: 在 SkillsBench (87 tasks, 11 domains) 上，Claude Opus 4.6 + Claude-Code 条件下 CoEvoSkills 达到 **71.1% pass rate**，比 no-skill 基线 (30.6%) 高 **+40.5pp**，比 human-curated skills (53.5%) 高 **+17.6pp**。Opus 进化出的 skill 迁移到 6 个其它 LLM 全部获得 +36~+44pp 提升。

---

## 1. Motivation & Problem

### 1.1 Tool → Skill 的范式转变

LLM agent 的进展大量依赖外部工具调用（ToolLLM、Gorilla、Toolformer 系列），但真实专业任务（复杂软件修复、多步科研分析、企业数据管道编排）远不止"单次 tool 调用"：

- 决策是 long-horizon 的
- 指令/脚本耦合紧密
- 环境反馈稀疏或延迟

Anthropic 提出 **agent skills**：一个 skill 不是单一函数，而是 **多文件结构化包**，包含 workflow 说明、可执行脚本、领域参考材料。

> **[Figure 1 (Fig:tool_vs_skill_example): Tool vs. Skill 对比]**
>
> Caption: *Tool–skill difference illustration.* 单个 tool 是一个自包含函数；skill 是一捆 SKILL.md + scripts/ + 参考资料，共同指导 agent 走完一条长程工作流。

### 1.2 现有方法的两大缺陷

| 缺陷 | 相关工作 | 表现 |
|---|---|---|
| **Tool–skill gap**: 只能产出单文件函数 | Voyager, SkillCraft, Live-Learning, YunJue, SEAgent, EvoTest | 无法生成多文件结构化 skill 包 |
| **依赖 GT 监督进行失败诊断** | EvoSkill (Alzubi 2026), SEAgent | 真实场景没有 GT test content → 无法落地 |
| **仅产出 prompt-level 启发式** | AutoSkill, AutoRefine, SAGE, SkillRL | 非可执行 artifact，无法复用 |

### 1.3 Human–Machine Cognitive Misalignment（关键观察）

SkillsBench 的评估发现：**人工编写的 skill 带来的收益极不均匀，某些领域（Natural Science）甚至使 agent 性能下降**。作者假设根因在于：

> 人类专家设计的 workflow 和抽象符合人类直觉，但 **与 LLM agent 的上下文处理方式、推理方式、执行约束不匹配**。

> **[Figure 5 (Fig:domain_breakdown): Per-domain pass rates]**
>
> Caption: *Per-domain pass rates on SkillsBench.* 对比三条件（no-skill、human-curated、CoEvoSkills）在 11 个专业领域上的表现。自进化 skill 在 9/11 个领域上超越 human-curated；箭头标注 Natural Science：human-curated 使性能下降，CoEvoSkills 反而大幅提升——直接印证 human–machine misalignment。

### 1.4 本文定位

**Research Question**: 能否让 agent 在 **不访问 ground-truth test 内容** 的前提下，自主生成、迭代、验证一个 multi-file skill 包？

**方法**: 把 skill 生成拆成两个信息隔离的 LLM 角色，用 co-evolution 绕过"缺 GT 反馈"的死锁。

---

## 2. Method

### 2.1 整体架构

> **[Figure 2 (Fig:evoSkill_framework): CoEvoSkills framework]**
>
> Caption: *Overview of the CoEvoSkills co-evolutionary framework.* Skill Generator 与 Surrogate Verifier 迭代 generate–verify–refine；Verifier 提供结构化失败诊断驱动 skill 改进；GT Oracle 只返回不透明的 pass/fail 信号，触发 test escalation 并保持严格信息隔离。

三个信息隔离的角色：

1. **Skill Generator** ($\pi_\theta$)：持久 conversation context，迭代生成/改写 skill 包
2. **Surrogate Verifier** ($\pi_\theta^V$)：独立 LLM session，合成 test assertion，输出诊断（不继承 generator 的 bias）
3. **Ground-Truth Oracle**：在干净环境 $\mathcal{E}'$ 重执行，仅返回 1-bit pass/fail

### 2.2 POMDP 形式化

任务环境建模为 POMDP $\mathcal{M} = \langle \mathcal{X}, \mathcal{A}, T, \mathcal{O}, \Omega, \mathcal{R} \rangle$：

- $\mathcal{X}$: 文件系统 + 进程状态
- $\mathcal{A}$: 终端命令 + 文件编辑
- $\mathcal{O}$: 命令执行结果（部分可观测）
- $\mathcal{R}(x_T) \in [0,1]$: 对最终输出的隐藏 GT 评分

Skill 作为策略条件：
$$a_t \sim \pi_\theta(a_t \mid h_t,\, \mathcal{S})$$

优化目标：
$$\mathcal{S}^* = \arg\max_{\mathcal{S}}\; J(\mathcal{S}),\quad J(\mathcal{S}) \triangleq \mathbb{E}_{\tau}[\mathcal{R}(x_T)]$$

直接优化 $J$ 不可行——oracle 只返回 1-bit，没有梯度、没有诊断。

### 2.3 Surrogate Reward 与交替优化

引入 surrogate reward by 独立 verifier：
$$\tilde{\mathcal{R}}(x, \mathcal{V}) \triangleq \frac{1}{|\mathcal{V}|}\sum_{k=1}^{|\mathcal{V}|}\mathbf{1}[e_k(x)] \in [0,1]$$

其中 $\mathcal{V} = \{e_1,\dots,e_{|\mathcal{V}|}\}$ 是 verifier 合成的 assertion 套件。然后交替优化：

**Skill refinement**（固定 $\mathcal{V}^{(j)}$，优化 skill）：
$$\mathcal{S}^{(i+1)} \leftarrow \arg\max_{\mathcal{S}}\; \tilde{\mathcal{R}}(\Phi(\mathcal{S},\mathcal{E}),\, \mathcal{V}^{(j)})$$

**Test escalation**（仅当 surrogate 通过但 GT 失败时触发）：
$$\mathcal{V}^{(j+1)} \sim \pi_\theta^V(\cdot \mid I, x^{(i)}, \mathcal{V}^{(j)}),\ \text{if } \mathbf{1}[\tilde{\mathcal{R}}=1 \wedge \mathcal{R}<1]$$

**关键设计**：test escalation 只拿到 **oracle 的 1-bit 失败信号**，不拿到 GT 测试内容，从而 verifier 必须"独立"增强自己的 test（如加更多 assertion、提高精度阈值）。这避免 Generator 偷偷对着 held-out test 过拟合。

### 2.4 Skill Generator

持久 context $C^{(0)} = (I, \mathcal{S}_{\text{meta}})$，其中 $\mathcal{S}_{\text{meta}}$ 是 Anthropic 官方的 `skill-creator` meta-skill。

每次迭代：
$$\mathcal{S}^{(i+1)} \sim \pi_\theta(\cdot \mid \mathcal{S}^{(i)}, C^{(i+1)}),\quad C^{(i+1)} = C^{(i)} \oplus \mathcal{F}^{(i,j)}$$

$\mathcal{F}^{(i,j)}$ 是 verifier 的结构化诊断：failed tests + root-cause + 修复建议。$\oplus$ 是 context 追加。

### 2.5 Surrogate Verifier

- 独立 session，**只看 task instruction $I$ 和 output files $x^{(i)}$**
- 看不到 Generator 的 reasoning、代码、skill 内容 → 避免 confirmation bias
- 输出：deterministic assertion 套件 + 结构化诊断（per-assertion 结果 / root cause / 修复建议）

### 2.6 Co-Evolution Algorithm（Alg. 1）

关键超参：$N=5$ evolution iters、$M=15$ surrogate iters、$\beta=0.7$ context cap。

```
while n < N and r < M:
  x = Φ(S, E)                               # rollout skill
  if context_usage > β: break               # 防 OOM
  R̃ = surrogate_reward(x, V)
  if R̃ < 1:                                 # Surrogate fail
    F = verifier_diagnose(I, x, V)
    C = C ⊕ F
    S = refine(S, C);  i++; r++; continue
  # Surrogate passed → Oracle 评测
  x̂ = Φ(S, E')                              # fresh env 重执行
  R = oracle(x̂);  n++
  if R == 1: return S
  elif R > R_best: save S as S*
  C = C ⊕ 1[R<1]                            # 只追加 1-bit
  V = escalate(I, x, V)                     # verifier 升级测试
```

**对比已有 self-evolving pipeline 的关键区别**：

| 方面 | 已有方法 | CoEvoSkills |
|---|---|---|
| 产物形式 | 单 tool / prompt / 权重 | 多文件 skill 包（SKILL.md + scripts/）|
| GT 依赖 | 需 GT test content | 只要 1-bit GT 信号 |
| Verifier 来源 | self-verify 或 无 | 独立 LLM session，信息隔离 |
| Feedback 形式 | 1-bit 或 trajectory | per-assertion 诊断 + root cause + 建议 |

---

## 3. 数据：SkillsBench

- **任务数**: 87 tasks
- **领域**: ~20 professional domains（聚合成 11 大类：Finance, Cybersecurity, Natural Science, Energy, Robotics 等）
- **评测**: 每任务配 deterministic verifier，输出二值 pass (reward=1.0) / fail (reward=0.0)
- **指标**: **Pass rate** = 全通过任务比例

作者声称这是"当前唯一专为评估 agent skill 设计"的 benchmark，因此只用它。

---

## 4. 实验设计与结果

### 4.1 Shared 配置

| 组件 | 设置 |
|---|---|
| Backbones | Claude Opus 4.6, GPT-5.2 |
| Surrogate verifier model | 同 backbone |
| GT oracle agent | Claude-Code (Opus) / Codex (GPT-5.2) |
| Evolution 超参 | $K=5$ oracle rounds, $M=15$ surrogate retries |
| Evolution runtime | 5× timeout（有效 3000s/task），4 workers |
| Eval runtime | 7200s/task, 10 workers |

六条 baseline：No-Skill / Self-Generated Skills / CoT-Guided Self-Gen / Skill-Creator (Anthropic 官方) / Human-Curated Skills，加上 CoEvoSkills 本身。

### 4.2 RQ1: Skill Quality Comparison（核心结果）

> **[Figure 3 (Fig:opus_main): Main results on Claude Opus 4.6]**
>
> Caption: *Skill quality comparisons with baselines on SkillsBench (Claude Opus 4.6 + Claude-Code).* Error bars: ±1 std over 5 runs.

| 方法 | Pass rate | vs. No-Skill |
|---|---|---|
| No-Skill Baseline | 30.6% | — |
| CoT-Guided Self-Generation | 30.7% (±5.2) | +0.1pp |
| Self-Generated (SkillsBench) | 32.0% (±3.1) | +1.4pp |
| Skill-Creator (in-session) | 32.4% | +1.8pp |
| Skill-Creator (Anthropic 官方两阶段) | 34.1% | +3.5pp |
| Human-Curated Skills | 53.5% | +22.9pp |
| **CoEvoSkills** | **71.1%** | **+40.5pp** |

**核心观察**：所有一次性（无 co-evolution）的 skill 生成策略 ≈ no-skill 基线，说明收益主要来自 **iterative verification loop** 本身，不是 prompt 工程。

### 4.3 RQ3: Cross-Model Transferability

> **[Figure 4 (Fig:cross_model): Cross-model skill transferability]**
>
> Caption: *Cross-model skill transferability on SkillsBench.* 用 Claude Opus 4.6 进化出来的 skill 迁移给 6 个其它模型，每对柱分别是 no-skill 基线（红）与 with-skills（蓝），delta 标注改进幅度。所有模型 +36~+44pp。

| Model | With skills | No skill | Δ |
|---|---|---|---|
| **Self-Evolved** |  |  |  |
| Claude Opus 4.6 | 71.1 | 30.6 | +40.5 |
| GPT-5.2 | 69.8 | 29.6 | +40.2 |
| **Transfer (Opus-evolved)** |  |  |  |
| GPT-5.2 | 65.0 | 29.6 | +35.4 |
| Claude Sonnet 4.5 | 63.1 | 20.0 | +43.1 |
| Claude Haiku 4.5 | 54.5 | 10.4 | +44.1 |
| Qwen3 Coder | 50.8 | 8.4 | +42.4 |
| DeepSeek V3 | 48.8 | 13.0 | +35.8 |
| Mistral Large 3 | 43.1 | 4.9 | +38.2 |

**观察**：GPT-5.2 上，自进化 (69.8%) 比迁移 Opus 进化 (65.0%) 高 4.8pp，说明存在**轻微但一致的 model-matched advantage**，但迁移版本仍然把 no-skill 基线从 29.6% 抬到 65.0%。

**Takeaway 2**: Skill 编码的是**可复用的任务结构**，不是模型特定的 artifact。

### 4.4 RQ4: Domain-level Breakdown

见 Figure 5。9/11 领域上 CoEvoSkills > human-curated：
- 最大提升：Finance (+56.9pp over human)、Cybersecurity (+23.2pp)
- 饱和域：Energy, Robotics（human 已经很好，进化空间小）
- **Natural Science**：human-curated 甚至降低性能，CoEvoSkills 带来大幅提升——直接印证 human–machine misalignment 假设。

### 4.5 Evolution Dynamics

> **[Figure 2 重复使用 / Fig:evolution_trajectory: Evolution trajectory]**
>
> Caption: *Skill quality improvement across 5 evolution rounds.* Round 0（one-shot）≈ no-skill；round 2 达 44%；round 3 超过 human-curated (63%)；round 5 收敛到 75%。

与三条静态 baseline 对比：no-skill 30.6%、Skill-Creator 34.1%、human-curated 53.5%。

---

## 5. 消融实验

> **[Table A2 (Tab:ablation)]**

所有 ablation 在 Claude Opus 4.6 + Claude-Code 上，单次 run。

| Setting | Pass rate | Δ vs. Full |
|---|---|---|
| **CoEvoSkills (Full)** | **71.1%** | — |
| W/O surrogate verifier | 41.1% | −30.0pp |
| W/O evolution (仅 background context) | 48.6% | −22.5pp |
| No-Skill Baseline | 30.6% | −40.5pp |

**诊断**：
- **去掉 surrogate verifier** 掉 30pp → 没有结构化诊断，只有 opaque 1-bit，Generator 无法 targeted 修复
- **仅给 background context** 48.6% → 非结构化知识不等于结构化 skill 包
- 这两个数字合起来说明 **"structured packaging + iterative verification"** 两者缺一不可

### 5.1 Iteration Distribution

> **[Figure 6 (Fig:iteration_distribution)]**
>
> Caption: *Distribution of verification cycles (left) and Ground-Truth Oracle rounds (right) across 86 evolution tasks.* 验证周期包含所有 host 干预（Surrogate 失败 + Oracle 评测）；Oracle rounds 只计 surrogate 通过后触发 oracle 的子集；失败任务（红）集中在高迭代数。

统计：
- 平均 4.1 verification cycles / task
- 平均 2.4 oracle rounds / task
- **60%+ 任务 ≤ 2 oracle rounds 收敛**
- 失败的 10 个任务聚集在 ≥5 cycles → 迭代多的任务本身更难

**结论**：surrogate verifier 吸收了 ~40% 的迭代成本（4.1 - 2.4 = 1.7 cycles 由 surrogate 独立解决），证明 Oracle budget $K=5$ 对绝大多数任务绰绰有余。

### 5.2 Per-Task Heatmap

> **[Figure 7 (Fig:task_heatmap)]**
>
> Caption: *Per-task pass rate heatmap across conditions.* Tasks 按 no-skill 难度排序（top = easiest）；cell 越深越容易。Self-evolved skills 救回了许多 no-skill 和 human-curated 都失败的任务，但极少数硬任务所有条件都解不了。

---

## 6. Case Study: Exoplanet Transit Period Detection

任务：从 TESS 望远镜光变曲线（含恒星自转调制）中检测系外行星周期，精度到 5 位小数。GT 有 4 个 deterministic test。

### 6.1 演化轨迹

| Round | Exit condition | Surrogate Verifier | GT Oracle | Key event |
|---|---|---|---|---|
| 1 | Verifier fail | 0/15 (0%) | — | Initial skill has bugs |
| 2 | Checklist fail | 15/15 (100%) | — | Progress checklist incomplete |
| 3 | Verifier pass | 15/15 (100%) | 3/4 (75%) | Period precision insufficient |
| 4 | Verifier pass | 20/20 (100%) | 3/4 (75%) | Precision fixed, alias check fails |
| 5 | Verifier fail | 19/22 (86%) | — | Surrogate 抓到回归 |
| **6** | **Verifier pass** | **22/22 (100%)** | **4/4 (100%)** | **All tests pass** |

### 6.2 四次 skill 版本

| Ver. | Detrending | Algorithm | Precision strategy | Oracle |
|---|---|---|---|---|
| V1 | Biweight | BLS | None | — |
| V2 | Biweight (opt.) | BLS | None | 75% |
| V3 | Median filter | BLS | None | 75% |
| **V4** | **Savitzky-Golay** | **TLS** | **Two-stage + alias check** | **100%** |

**关键洞察**：V2/V3 在 BLS 上死磕 75%，逼出 V4 的**算法级切换**——从 BLS 换到 TLS（真正用 limb-darkened transit model）+ 两阶段周期搜索（broad 0.5–15 天 → 窄 ±2%）+ alias 检查（$P/2$, $2P$）。

### 6.3 Surrogate vs. GT 的固有 gap（极好的案例）

Round 3：surrogate 15/15 全过，GT 却 3/4。原因：
- Surrogate 用 1% tolerance 匹配周期
- GT 要求 5-decimal 精确匹配 —— Surrogate **无法从 task 描述推断出这个精度阈值**

Round 5：Surrogate 升级到 22 tests，在自己的 BLS 上算出 3.24158，而 agent 的 TLS 算出 3.24156。Surrogate 把 0.00002 天的差当失败标记——**即使 agent 的答案更准**。

**这说明了两个 surrogate 结构性局限**：
1. Surrogate 无法复刻 GT 的精度要求
2. Surrogate 无法区分"自己估计的误差"与"agent 的误差"

因此 **GT Oracle 不可被 Surrogate 取代**——必须作为权威 arbiter 存在。

### 6.4 Human-curated vs. Self-evolved（结构性对比）

| Aspect | Human (5 skills) | Self-evolved (1 skill) |
|---|---|---|
| Total size | 1,096 lines across 5 SKILL.md | 64 lines SKILL.md + 142 lines Python |
| Executable code | 无 | 9 callable functions |
| 算法推荐 | 平等列出 BLS/TLS/Lomb-Scargle | 明确处方 TLS + justification |
| Period refinement | 2 行 tip | Two-stage（broad then ±2% narrow）|
| Alias detection | "Check for aliasing"（一句）| 自动检测 $P$, $2P$, $P/2$ |
| Precision handling | 未提 | 强制 5-decimal 输出格式 |

**哲学差异**：人工 skill 是 *prose documentation* 要 agent 每次解释再实现；进化 skill 是 *tested executable functions* 直接 import。前者每次试错都有可能引入 precision bug。

装入 fresh Opus 4.6 后：evolved skill **5/5 runs 100%**；human-curated **53.5%**（agent 在三个算法间摇摆）；no-skill **~75%**（default 到 Lomb-Scargle，错误模型）。

---

## 7. Discussion & 局限性

### 7.1 为什么 surrogate verifier 这么关键？

消融显示 surrogate 贡献了 30pp。本质上 surrogate 的价值是：
1. **把 1-bit GT 信号扩展成 per-assertion 诊断** → targeted repair 成为可能
2. **吸收 ~40% 的 oracle 预算** → 节省真实评测成本
3. **信息隔离** → 避免 Generator 的 self-verification bias

### 7.2 信息隔离如何避免 overfit to held-out test？

设计上 oracle 只返回 $\mathbf{1}[\mathcal{R}<1]$，不返回失败内容；verifier 必须靠 task instruction 和 output 独立合成 test。Case study round 5 正面验证了这点——surrogate 甚至比 GT 更严格（把比 GT 更准的答案标成 fail）。

### 7.3 局限与批判

1. **Budget 选择**：$N=5$、$M=15$ 怎么选的？失败的 10 个任务集中在 budget 用光处，说明 budget 可能是性能瓶颈——没有做 budget sensitivity 分析。

2. **Surrogate overshoot 的代价**：Round 5 那种"surrogate 比 GT 还严格"的情形在多少任务上发生？论文没定量。理论上 surrogate 误报会浪费 evolution 轮次、把好 skill 改坏。

3. **只用 SkillsBench**：作者承认这是"当前唯一 skill-purpose benchmark"，但 87 tasks 对 7 个模型 × 多 baseline × 3-5 seeds 的矩阵，统计力是否足够？ablation 都是单次 run（成本原因），置信区间缺失。

4. **Cost transparency 弱**：3000s/task × 4 workers × 5 runs × 5 iters × 多模型 = 相当昂贵。论文未给 token cost 或 $ cost，对复现不友好。

5. **"Agent 比人好" 的结论边界**：人工 skill 是 *SkillsBench 提供的* 那个版本——这是一组特定人写的 skill，不一定代表"人类能做的最好"。一个经验丰富的该领域专家花同样时间写是否能赶上？作者没对比。

6. **对 Meta-skill 的依赖**：`skill-creator`（Anthropic 官方）本身是人写的 meta-skill，CoEvoSkills 依赖它 bootstrap。严格说这是 *human-in-the-loop at meta-level*。

7. **Verifier 的脆弱性**：如果 task 描述很模糊（现实常见），verifier 合成的 assertion 可能完全偏离 GT。论文挑的都是 deterministic-verifier 任务，在 open-ended 任务（如 UI 设计、创作）上 surrogate 会怎样？

### 7.4 值得深入讨论的问题

- **Test escalation 的收敛性理论**：既然 surrogate 只拿到 1-bit oracle 反馈，它怎么保证单调变"更严"？有没有可能 escalate 成不一致的 test？
- **Skill 的 composability**：如果一个任务需要多个进化过的 skill 组合，它们会不会彼此矛盾？论文只评测了 "一个任务一个 skill" 的场景。
- **Negative transfer**：Opus 进化的 skill 给 Haiku 用比 no-skill 高 44pp，但真的没有"某个 skill 让某个模型变差"的案例吗？论文只报了 domain-level aggregate。
- **"Skill 是知识还是 trace"**：进化出的 skill 本质是 *几条在 surrogate 上能过的规则* 还是 *真正的领域知识*？能不能让一个弱模型靠 skill 解决超出它能力的任务？Haiku 从 10.4% → 54.5% 大概回答了这个。

---

## 8. 技术细节速查

### Training / Evolution 参数

| 项 | 值 |
|---|---|
| $N$ (oracle rounds 上限) | 5 |
| $M$ (surrogate retries 上限) | 15 |
| $\beta$ (context usage cap) | 0.7 |
| Evolution timeout | 3000s/task (5× 基础) |
| Eval timeout | 7200s/task |
| Eval parallel workers | 10 |
| Baseline runs | 5 (mean±std) |
| Transfer runs | 3 |

### 关键数字速查

| 数字 | 含义 |
|---|---|
| **71.1%** | Opus 4.6 + Claude-Code 主结果 |
| **+40.5pp** | 对 no-skill 基线绝对提升 |
| **+17.6pp** | 对 human-curated 绝对提升 |
| **69.8%** | GPT-5.2 self-evolved |
| **65.0%** | GPT-5.2 用 Opus 迁移 skill |
| **+44.1pp** | Haiku 4.5 受益最大 |
| **4.1 / 2.4** | 平均 verification cycles / oracle rounds per task |
| **63%** | Round 3 超过 human-curated |
| **75%** | Round 5 收敛值（traj. 图） |

### 使用到的 LLM / Agent

| 模型 | Harness |
|---|---|
| Claude Opus 4.6 | Claude-Code |
| GPT-5.2 | Codex |
| Claude Sonnet 4.5 | Claude-Code |
| Claude Haiku 4.5 | Terminus-2 |
| Qwen3 Coder 480B | Terminus-2 |
| DeepSeek V3 671B | Terminus-2 |
| Mistral Large 3 675B | Terminus-2 |

### Skill Generator 系统 prompt 关键约束

- 三阶段：Evolve → Execute → Summarize
- 强制 `/root/progress.md` 清单（P1–P6），所有 phase 必须 `[x]` 才可 task_complete
- 强制：所有 task 输出必须通过 **import skill scripts/** 产生，禁止把函数代码复制到 main script
- "Write back all runtime fixes"：execute 阶段的任何修补必须写回 skill 的 scripts/，保证 skill 对 fresh agent 自包含
- Computational budget 约束：空间 >1000 组合必须用近似算法

---

## 关键公式速查

Surrogate reward:
$$\tilde{\mathcal{R}}(x, \mathcal{V}) = \frac{1}{|\mathcal{V}|}\sum_{k=1}^{|\mathcal{V}|}\mathbf{1}[e_k(x)]$$

Skill update:
$$\mathcal{S}^{(i+1)} \sim \pi_\theta(\cdot \mid \mathcal{S}^{(i)}, C^{(i+1)}),\quad C^{(i+1)} = C^{(i)} \oplus \mathcal{F}^{(i,j)}$$

Test escalation（仅当 $\tilde{\mathcal{R}}=1 \wedge \mathcal{R}<1$）：
$$\mathcal{V}^{(j+1)} \sim \pi_\theta^V(\cdot \mid I, x^{(i)}, \mathcal{V}^{(j)})$$
