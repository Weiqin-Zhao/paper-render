# SkillsBench: Benchmarking How Well Agent Skills Work Across Diverse Tasks

> **论文信息**: Xiangyi Li, Yimin Liu, Wenbo Chen, Shenghan Zheng 等（23 家机构，105 贡献者）
>
> **机构映射（从 tex 源）**: BenchFlow（lead）/ Amazon / OSU / Dartmouth / Stanford / UC Davis / CMU / UC Berkeley / Princeton / Foxconn / BU / Zenity / UC Santa Cruz / USC / ByteDance / UT Dallas / MSU / UT Austin / Duke / Oxford / UC San Diego / Columbia / Independent（联系作者 Xiangyi Li, xiangyi@benchflow.ai）
>
> **发表时间**: 2026-03-16（Preprint, ICML 2026 投稿格式）
>
> **关键词**: Agent Skills, Benchmark, LLM Agent, Procedural Knowledge, Claude Code, Gemini CLI, Codex CLI
>
> **代码 & 网站**: [skillsbench.ai](https://skillsbench.ai)；基于 Harbor 框架构建
>
> **arxiv ID**: 2602.12670v3
>
> **一句话总结**: SkillsBench 是第一个**把 Agent Skill 作为一等评测对象**的基准：在 84 个任务 × 3 种条件（无 Skill / 人工策划 Skill / 模型自生成 Skill）× 7 个 agent-model 配置上跑了 7,308 条轨迹，发现人工策划的 Skill 平均能带来 +16.2pp 提升，而模型自生成的 Skill 几乎无效或反向有害（–1.3pp）。
>
> **📌 笔记数据源**: 本笔记直接从 arxiv LaTeX 源码（`main.tex` + `sections/*.tex` + `figs/*.pdf`）生成，figure 为矢量原件渲染，不是 PDF OCR 截图。tex 源里**注释保留的草稿内容**为本笔记提供了 PDF 看不到的附加信号（见 §11）。

---

## 0. 预备知识：Prompt / Skill / Harness（读懂本文的三层同心结构）

读这篇论文前，先对齐三个经常被混淆的概念。它们**不是并列关系**，而是一层套一层的**嵌套**。

### 0.1 一张图理解

> **CPU / OS / 应用 类比**：原始 LLM 像一颗没 RAM、没硬盘、没 I/O 的 CPU。上下文窗口是 RAM（快但小），外部数据库是硬盘（大但慢），工具集成是设备驱动，**harness 就是操作系统**。
>
> 围绕模型有三层同心的工程：**Prompt engineering**（起草给模型的指令）⊂ **Context engineering**（管理模型看到什么、何时看到）⊂ **Harness engineering**（前两者 + 工具编排、状态持久化、错误恢复、验证循环、安全执行、生命周期管理）。

**一句话概括**：
- **Prompt**：你这一次对话里写给模型的话
- **Skill**：打包好的、模型按需自动调用的"专家手册"
- **Harness**：整个包裹模型的运行时系统，让它能真正"做事"

### 0.2 速记卡

| 概念 | 回答的问题 | 生命周期 | 典型载体 |
|---|---|---|---|
| **Prompt** | 这一次我要模型做什么？ | 一次对话 | 你打的字 |
| **Skill** | 这类任务我要它怎么做？ | 跨会话复用 | `SKILL.md` 文件夹 |
| **Harness** | 整个系统如何让 agent 真正动起来？ | 持久基础设施 | Claude Code / Claude Agent SDK / LangGraph |

### 0.3 Prompt（提示词）

- 对话里**一次性的自然语言指令**。
- **灵活、快速，但不跨会话保留**，重复劳动多。
- 适用场景：临时任务、头脑风暴、原型探索、一次性细腻调整。

### 0.4 Skill（技能）

- Anthropic 2025-10 推出的概念，解决"同一个 prompt 反反复复写"的痛点。
- 一个**可复用指令集**：`SKILL.md` + 元数据 + 可选资源（脚本、模板、参考文档），丢到 `.claude/skills/` 目录即可。
- **关键机制：渐进式披露 (progressive disclosure)** ——
  > Claude 运行在带文件系统访问的 VM 里，skill 作为目录存在，按需分阶段加载，而不是一次性塞满 context 窗口。
  >
  > 启动时只看到 skill 的**名字和描述**，真正需要时才加载完整内容。**这一点是 skill 和"把 prompt 存文本文件里"最大的区别——它不占 context 预算。**

**Skill vs Prompt 决策原则**（Anthropic 官方）：

> 如果你发现自己在多个对话里一遍遍敲同一段 prompt，那就该做一个 skill 了。

**MCP vs Skill 的区别**（经常被搞混）：

| | 给 agent 的是 | 例子：接 GitHub MCP |
|---|---|---|
| **MCP** | **能力**（"能做什么"） | 让 agent 能创建 PR、列 issue、搜仓库 |
| **Skill** | **专业度**（"怎么做"） | 告诉 agent 你们团队怎么组织 PR / 必含测试章节 / 按变更类型打 tag / 标题里引用 Linear ticket |

两者互补，不替代。

### 0.5 Harness（脚手架 / 载具）

- 2026 年初才被"正式命名"，但概念早就存在。
- 包裹 LLM 的**完整软件基础设施**：编排循环、工具、记忆、上下文管理、状态持久化、错误处理、护栏。
- Anthropic 官方："Claude Code SDK **就是**驱动 Claude Code 的 agent harness。"
- LangChain 的经典公式：**"如果你不是那个模型，那你就是 harness。"**

**为什么需要 harness？** 因为 LLM 本质**无状态**：每个新会话都从零开始，什么都不记得。Harness 负责上下文压缩 (compaction)、工具调用分发、会话持久化、进度追踪、验证循环、错误恢复、安全执行。

**反直觉但重要的洞察：Harness 是会被"削薄"的**

> 建筑脚手架是临时设施，它让工人能够搭建他们本来够不到的楼层，但它自己不是楼。楼建完就拆。随着模型变强，**harness 的复杂度应该下降**。Manus 在 6 个月里被重写了 5 次，每次都在**移除**复杂度——复杂的工具定义变成了通用的 shell 执行。

### 0.6 本论文在这个三层框架中的位置

作者在 Figure 1 提出了对应的类比：**CPUs（模型）+ OS（agent harness）+ Applications（Skills）**。

- **研究对象** = "applications" 层的 **Skill**
- **必须跨 harness 评测** ：同一个 Skill 在 Claude Code / Gemini CLI / Codex CLI 下表现不同（§4.1.2 Harness-Specific Reliability）——**"With Skill" 不能被当成单一条件**。
- **Prompt 级替代不行**：Self-generated Skill condition（让 model 先自写 Skill 再解题）本质是 prompt 级 elicitation，失败（–1.3pp）——说明 **procedural knowledge 不能从 parametric memory 里 elicit 出来，需要人工 curation**。
- **Harness 变薄的预测对应论文观察**：Claude Code 有原生 Skill 集成 → 效果最好；Codex "acknowledge but ignore" → Skill 被浪费。Harness 的 Skill-aware 程度直接影响 Skill 效用。

---

## 1. Motivation & Problem

### 1.1 背景：Skill 生态在爆炸，但没人系统量化它

- LLM 已经从"文本生成器"走向"能在真实环境下多步执行任务的 autonomous agent"，代表是 Claude Code、Gemini CLI、Codex CLI 等终端类 agent-CLI。
- 但基础模型**有通用能力、缺少特定领域的 procedural knowledge**，而 fine-tuning 代价高、牺牲通用性。
- **Agent Skill** 是近期的折中方案：一个结构化的 package（`SKILL.md` + 脚本 + 模板 + 参考资料 + 验证逻辑），在推理时挂载进来，**不改模型权重**。
- 生态发展非常快：作者收集到 3 个来源 12,847 / 28,412 / 5,891 条，经去重后有 **47,150 条独立 Skill**（另一统计口径下 136 天共 84,192 条，峰值日增 18,904）。

### 1.2 现有方法的局限：benchmark 不量化增强

现有 agent benchmark（AgentBench, SWE-bench, OSWorld, WebArena, τ-bench 等）问的是"模型 X 在任务 T 上能做到多好"，但**从不问**"给 agent 加一个 Skill Y，能带来多少增益？什么情况下 Skill 会反而拖累？"。

> **作者的原问**: "How much do Skills help compared to baseline augmentation? Which Skills components contribute most? When do Skills fail despite being present?"

### 1.3 本文定位

SkillsBench 把 Skill 作为**一等评测对象**，核心贡献两点：

1. **Skill-centric 评测框架**: 84 任务 × 11 领域，每个任务在 3 条件（No Skill / With Skill / Self-Generated Skill）下跑，配以**确定性**验证器（pytest，不用 LLM-as-judge）。
2. **大规模实证**: 7 agent-model 配置 × 7,308 条 valid trajectory，首次给出 Skill 效果、方差、失败模式的系统性证据。

> **[Figure 1: Agent 架构栈 + 7 配置分辨率]** (`fig01_architecture.png`，tex label `fig:architecture`)
> 把整个 agent 系统类比为"CPU（模型）+ OS（Agent Harness）+ Applications（Skills）"。柱状图展示 7 个 agent-model 配置在 3 种条件下的通过率：curated Skill 普遍提升（米色），self-generated 几乎无效甚至下降（琥珀色）。

---

## 2. Method: SkillsBench 基准构造

### 2.1 Skill 的四条形式化标准

一个合格的 Skill 必须满足：

| # | 标准 | 含义 |
|---|------|------|
| 1 | **Procedural content** | "How-to" 型（流程 / SOP / workflow），不是事实检索 |
| 2 | **Task-class applicability** | 适用于一类问题，不是单一实例 |
| 3 | **Structured components** | `SKILL.md` + 可选脚本 / 模板 / 示例 |
| 4 | **Portability** | 纯文件系统组织，可跨 agent-harness 移植 |

显式**排除**：system prompt（无结构）、few-shot 示例（描述性非过程性）、RAG 召回（事实性）、tool documentation（能力描述非操作流程）。

> **[Table 1: 四种 runtime augmentation 对比]** (tex label `tab:comparison`)
> Skills 是唯一同时拥有 "模块化 + procedural guidance + 可执行资源 + 跨模型可移植" 的范式。

### 2.2 任务的四个组件

每个任务是一个自包含 module：

- **Instruction** (`instruction.md`): 人类写的自然语言任务描述；规定"**不能写明该用哪个 Skill**"，必须让 agent 自己去发现和调用 Skill。
- **Environment**: Docker 容器 + 任务数据 + `skills/` 子目录（只在 with-Skills 条件挂载）。
- **Solution**: 参考 oracle 解法，必须 100% 通过测试。
- **Verifier**: 确定性 pytest，带数值 tolerance；不使用 LLM-as-judge 以保证可复现。

### 2.3 数据来源与规模

- 105 贡献者（学术 + 工业）提交了 **322 候选任务**；最终过关 **86**（26.7% 接受率），实际评测 **84**（剔除 `mhc-layer-impl` 要 GPU、`fix-visual-stability` verifier 超时）。
- 难度按"中位领域专家手工完成时间"分层（Table 2）：

| Difficulty | 任务数 | 人类耗时 |
|------------|--------|----------|
| Core       | 17 (19.8%) | <60 min |
| Extended   | 43 (50.0%) | 1–4 h |
| Extreme    | 26 (30.2%) | >4 h |

### 2.4 质量管控：防止"答案泄漏"是重中之重

作者特别注意**防止 Skill 把具体答案编码进去**，否则就变成 cheating：

- Skill **不得包含**：任务特定文件名/路径/标识符、精确解题命令序列、任务数据里的常数 / magic number、对特定测试用例或期望输出的引用。
- 使用 **Claude Code Agent SDK 的 validation agent** 在 CI 里跑 **leakage audit**，失败即拒。
- 人工 reviewer 按 5 criteria 审：data validity / task realism / oracle quality / Skill quality / anti-cheating。
- Instruction 必须是**人类写**的（GPTZero + 人工判别），防 LLM 自生成的低质量指令污染评测。

> **[Figure 2: 三阶段 pipeline]** (`fig02_pipeline.png`，tex label `fig:pipeline`)
> - Phase 1 Benchmark Construction：聚合 3 来源的 Skill（12,847 / 28,412 / 5,891）→ 47,150 去重；同时收 322 任务。
> - Phase 2 Quality Filtering：结构校验 + AI 检测 + leakage audit + 5 项人工审；得 84 任务 / 11 领域。
> - Phase 3 Evaluation：3 条件 × 3 agent-harness，跑 7,308 trajectory。
>
> 🔍 **tex 源发现**：pipeline.pdf 的 caption 在 tex 里写的是 "+12.66pp average improvement"，但正文与 abstract 都说 "+16.2pp"。这是草稿残留的数字不一致，PDF 里能看到但不能反查源头。

### 2.5 11 个领域的任务分布

> **[Figure 3: 11 domain 任务数分布]** (`fig03_category_distribution.png`，tex label `fig:category_distribuion`)
> Software Engineering (16), Office & White Collar (14), Natural Science (12), Media & Content (11), Cybersecurity (8), Finance (8), Robotics (5), Manufacturing (3), Energy (3), Mathematics (2), Healthcare (2)。

---

## 3. Experimental Setup

### 3.1 Agent-harness × model 配置（7 套）

| Harness       | Model                     | Runs  |
|---------------|---------------------------|-------|
| Claude Code   | Opus 4.5 / 4.6 / Sonnet 4.5 / Haiku 4.5 | 4×~1100 |
| Gemini CLI    | Gemini 3 Pro / Flash      | 2×840 |
| Codex CLI     | GPT-5.2                   | 1092  |

- Temperature=0；Claude 模型在 Agent Skills spec 上被训练过，理论上有优势。
- **Self-Generated 条件不评测 Gemini CLI**（Gemini CLI 的 skill 激活是 explicit tool call，不支持"凭空生成"模式）。

### 3.2 三种 Skill 条件

| 条件 | 说明 |
|------|------|
| **No Skills**           | 只给 `instruction.md` |
| **With Skills**         | 完整 `environment/skills/` 挂载 |
| **Self-Generated**      | 无 Skill，但 prompt 要求 agent **先自己写 1–5 个 Skill 到 `environment/skills/`**，然后再解题 |

### 3.3 评测协议细节

- 每条件每任务 **5 次试验**（self-gen 是 3 次），取平均 → 任务级分数 → 固定分母 84 求 mean，遵循 Terminal-Bench 的 Method D 打分法。
- Skill 作为 **system-level context** 注入；每个 Docker 把 skills 复制到 harness 特定路径（`/root/.claude/skills`、`/root/.codex/skills`、`/root/.gemini/skills`）。
- **Context budget 8K token** 滑动窗口，最大 round 数按难度分 10/30/50。
- Per-task timeout 600–1200s；bootstrap 1,000 次算 95% CI。

### 3.4 两个关键 metric

- **Pass Rate**: 5 次 binary reward 平均，任务级平均，固定分母=84。
- **Normalized Gain** (Hake 1998)：

$$g = \frac{\text{pass}_\text{skill} - \text{pass}_\text{vanilla}}{1 - \text{pass}_\text{vanilla}}$$

解释：$g$ 衡量"距离 100% 走了百分之多少"。但 $g$ 有 ceiling effect（90→95% 和 10→55% 都是 $g=0.5$），所以作者**同时报 $\Delta_\text{abs}$ 和 $g$**。

---

## 4. Results

### 4.1 主结果：7 个配置下 Skill 的影响

> **[Table 3: 3 条件的 pass rate / g，按 with-Skill 表现排序]**

| Harness | Model | No Skill | With Skill | g (%) | Self-Gen | $\Delta_G$ (pp) |
|---|---|---|---|---|---|---|
| Gemini CLI | Gemini 3 Flash | 31.3 | **48.7** | 25.3 | – | – |
| Claude Code | Opus 4.5 | 22.0 | 45.3 | **29.9** | 21.6 | –0.5 |
| Codex | GPT-5.2 | 30.6 | 44.7 | 20.3 | 25.0 | –8.1 |
| Claude Code | Opus 4.6 | 30.6 | 44.5 | 20.0 | 32.0 | +2.0 |
| Gemini CLI | Gemini 3 Pro | 27.6 | 41.2 | 18.8 | – | – |
| Claude Code | Sonnet 4.5 | 17.3 | 31.8 | 17.5 | 15.2 | –2.5 |
| Claude Code | Haiku 4.5 | 11.0 | 27.7 | 18.8 | 11.0 | 0.0 |
| **Mean** | | **24.3** | **40.6** | **21.5** | **21.0** | **–1.8** |

> 🔍 **tex 源发现**：Table 3 Mean 行 `$\Delta_G$` 的**最终版是 –1.8**（tex 源显式这么写），但正文 Finding 3 和 abstract 都说 "self-generated Skills yield –1.3pp on average"。这是内部数字不一致。注释掉的草稿版本里，Mean 行就是 –1.3，推测是在表格数据修订（Codex –5.6 → –8.1、Opus 4.5 –0.4 → –0.5 等）后忘了更新 Mean 行与正文。

**7 条关键发现**（作者自己总结 + 笔记扩展）：

1. **Finding 1：Skill 有显著但方差很大的增益**。平均 +16.2pp，区间 +13.6 到 +23.3pp。
2. **Finding 2：最高绝对分 ≠ 最高增益**。Gemini 3 Flash + Gemini CLI 拿最高绝对分 48.7%，但 Claude Code + Opus 4.5 拿最高相对增益 +23.3pp，体现 Claude Code 的原生 Skill 集成优势。
3. **Finding 3：Self-Generated 几乎无效（–1.3pp 均值）**。只有 Opus 4.6 +2.0pp，GPT-5.2 甚至 –8.1pp。失败模式两种：(a) 识别到要用领域知识但写得不具体（"use pandas for data processing"），(b) 高领域知识任务上根本识别不出要 Skill。**→ 有效的 Skill 需要人类 curation，模型无法可靠自生成**。
4. **Finding 4：Skill 收益在 domain 上高度异质**（下一小节展开）。
5. **Finding 5：2–3 个 Skill 最优**。4+ Skill 反而 +5.9pp（vs +18.6 for 2–3），非单调。
6. **Finding 6：Detailed/Compact > Comprehensive**。过于详尽的 Skill（Comprehensive）反而 **–2.9pp**，暗示"context budget 被吃掉 + 信息噪声"。
7. **Finding 7：小模型 + Skill 能追平大模型 naked**。Haiku 4.5 + Skill (27.7%) > Opus 4.5 naked (22.0%)。

### 4.2 Domain-Level: 收益差 10 倍以上

> **[Table 4: 11 个 domain 的 With/No Skill 对比]**

| Domain | With | No | $\Delta_\text{abs}$ |
|---|---|---|---|
| Healthcare | 86.1% | 34.2% | **+51.9** |
| Manufacturing | 42.9% | 1.0% | +41.9 |
| Cybersecurity | 44.0% | 20.8% | +23.2 |
| Natural Science | 44.9% | 23.1% | +21.9 |
| Energy | 47.5% | 29.5% | +17.9 |
| Office & WC | 42.5% | 24.7% | +17.8 |
| Finance | 27.6% | 12.5% | +15.1 |
| Media | 37.6% | 23.8% | +13.9 |
| Robotics | 27.0% | 20.0% | +7.0 |
| Mathematics | 47.3% | 41.3% | +6.0 |
| Software Eng. | 38.9% | 34.4% | **+4.5** |

**规律**：**pretraining 覆盖少的领域（医疗、制造）Skill 增益最大；pretraining 强的领域（数学、SWE）Skill 增益很小**。这是一个很自然的、但从未被量化过的直觉。

### 4.3 Task-Level: 有 16 个任务 Skill 反而有害

- **Top Skill 受益**：`mario-coin-counting` (+85.7pp)、`sales-pivot-analysis` (+85.7pp)、`flood-risk-analysis` (+77.1pp)、`sec-financial-report` (+75.0pp)、`protein-expression-analysis` (17.1% → 91.4%, +74.3pp)。
- **Skill 有害**：`taxonomy-tree-merge` (**–39.3pp**)、`energy-ac-optimal-power-flow` (–14.3pp)、`trend-anomaly-causal-inference` (–12.9pp)、`exoplanet-detection-period` (–11.4pp)。
- **16/84 任务**（19%）在 all model × all condition 下都是 **0% pass**，指向当前 agent 能力前沿（作者分类为：计算受限 / 复杂多步 pipeline / 严苛 spec）。

### 4.4 Cost-Performance Pareto

> **[Figure 4: Pareto frontier of pass rate vs cost]** (`fig04_pareto_cost.png`，tex label `fig:pareto`)
>
> Skill 整体把 frontier 向上推。Gemini 3 Flash 在 with-Skill 下占据帕累托前沿：
> - Flash 消耗 2.3× Pro 的 input token（1.08M vs 0.47M），但 token 单价 4× 便宜，**per-task 成本反而低 47%（$0.57 vs $1.06）**。
> - **启示**：小模型通过"多探索多采样"补足推理深度，是一种可观的性价比策略。
>
> 🔍 **tex 源发现**：tex 里 `\includegraphics` 后面有一行注释 `% TODO: Regenerate Pareto figure with updated data` —— 作者自己标记这图还没用最新数据重新生成，说明图的具体坐标可能是旧快照（PDF 完全看不到这种 TODO）。

---

## 5. Skills 设计因素

### 5.1 数量：2–3 是 sweet spot

> **[Table 5: Skill 数量 vs 增益]**

| Count | With | No | $\Delta$ |
|---|---|---|---|
| 1 skill | 42.2 | 24.4 | +17.8 |
| 2–3 skills | **42.0** | 23.4 | **+18.6** |
| 4+ skills | 32.7 | 26.9 | +5.9 |

- **单调上升到 2–3 之后**骤然下降。可能解释：（a）Skill 之间冲突指引；（b）认知负担；（c）上下文预算被挤占。

### 5.2 复杂度：Detailed / Compact 优于 Comprehensive

> **[Table 6: 4 种复杂度档位]**

| Complexity | Pass | $\Delta$ | n |
|---|---|---|---|
| Detailed | **42.7** | +18.8 | 1165 |
| Compact | 37.6 | +17.1 | 845 |
| Standard | 37.1 | +10.1 | 773 |
| Comprehensive | 39.9 | **–2.9** | 140 |

- **Comprehensive Skill 是唯一负向增益的档位**。对 Skill 作者的现实指导：**不要写得"面面俱到"**，要**写得"聚焦且配一个可执行示例"**。

### 5.3 模型规模 vs Skill

- Claude 家族实验：**Haiku + Skill (27.7%) > Opus naked (22.0%)**。
- **Skill 能部分替代模型 scale**，对部署经济性有意义：可以考虑"小模型 + 高质量 Skill"组合。

---

## 6. 失败模式的深度剖析（Appendix I）

### 6.1 失败分类学（Terminal Agent Taxonomy 改编）

作者把 **5,171 次失败** 按程序化判定归到 5 大类：

| Category | 失败模式 | 计数 | % |
|---|---|---|---|
| **Verification** | Quality Below Threshold | 2,577 | **49.8** |
| **Timeout** | Agent Timeout | 922 | 17.8 |
| **Coherence** | Incomplete Solution | 527 | 10.2 |
| **Execution** | No Output Produced | 411 | 7.9 |
| Execution | Domain Knowledge Gap | 251 | 4.9 |
| Execution | Specification Violation | 171 | 3.3 |
| Execution | Incorrect Implementation | 68 | 1.3 |
| Execution | Tool/Env Failure | 16 | 0.3 |
| Unknown | Unclassified | 228 | 4.4 |

**一条最大启示**：**49.8% 失败是"结构对了但数值精度/tolerance 挂了"**，说明 agent 能理解任务结构，但在 domain-specific 数值层面容易出错。这也正是 Skill 最能撬动的地方。

### 6.2 Skill 怎么改变失败分布（Table 17）

| Condition | Fail Rate | Timeout | Execution | Coherence | Verification |
|---|---|---|---|---|---|
| No Skills | **78.4%** | 16.1 | 17.1 | 10.7 | 52.1 |
| With Skills | **61.1%** | 18.6 | 21.1 | 8.9 | 46.6 |
| Self-Gen | 80.9 | 19.9 | 13.9 | 11.2 | 50.4 |

- **Skill 主要减少 Verification 失败**（1184 → 819，–30.8%），即提升数值精度/输出质量。
- **Skill 相对放大 Timeout 比例**，因为简单错误被先消除、剩下的是难任务，agent 会花更多时间追求更优解。
- **Self-Gen fail rate 比 no-skill 还高**（+2.5pp），生成 Skill 的过程本身消耗时间、引入噪声。

### 6.3 模型间的差异（Table 16）

- **Haiku 4.5** Execution 失败率 **21%**（最高），fail rate 85.2%，低能力 → 基础错误多。
- **Opus 4.6** Timeout 比例 **29%**（最高），表明它更倾向"慢而野心大"策略。
- **Gemini 3 Flash/Pro** timeout 最低（9–10%）但 execution 最高（23–25%）：**快但粗糙**。
- **Verification 是所有模型的统治性失败（48–53%）**——质量而非结构，是当前 agent 的真正瓶颈。

### 6.4 代表性成功案例（Skill 把 0% → 85%）

| Task | No Skill | With Skill | $\Delta$ | 关键机制 |
|---|---|---|---|---|
| `sales-pivot-analysis` | 0% | 85.7% | +85.7 | Skill 提供 openpyxl pivot table API 精确用法 |
| `flood-risk-analysis` | 2.9 | 80.0 | +77.1 | 指定 USGS 标准 Log-Pearson Type III 分布 |
| `sec-financial-report` | 0 | 75.0 | +75.0 | 给出 SEC EDGAR API + 13F filing 结构 |
| `mfg-fjsp-optimization` | 0 | 68.6 | +68.6 | 给出 OR-Tools 约束传播方案 |

这 4 个例子都指向一个共同模式：**"domain-specific API / regulatory knowledge / 标准方法论"是 Skill 最能撬动的缺口**。

### 6.5 13 张热力图（全 84 任务 × 7 模型）

> **[Figure 11/12/13]** (`fig11_heatmap_with_skills.png` / `fig12_heatmap_no_skills.png` / `fig13_heatmap_uplift.png`，tex label `fig:heatmap-with/-no/-uplift`)
>
> - Fig 11: With Skill pass rate 网格，顶部易任务蓝一片，底部难任务红一片。
> - Fig 12: No Skill baseline，蓝色区域明显收缩，证明 Skill 把相当比例任务从"不可解"推到"可解"。
> - Fig 13: Uplift 差值图，蓝=Skill 有益，红=Skill 有害，大多数格子蓝色但 16 个任务红。
>
> 这 3 张图每张都是 2136×4733 px 的超高长图（因为有 84 个任务行 × 7 模型列），tex 源渲染能保留全部细节。

---

## 7. Discussion

作者给出四条高层论点：

1. **Skill 填的是 procedural 而非 conceptual 鸿沟**。模型有概念知识（懂 flood risk 是什么），但不知道"具体该调哪个 scipy 函数 + 哪组参数"，Skill 正好填这一层。
2. **Harness 对 Skill 效用有中介作用**。Claude Code 会可靠调用 Skill；Codex "acknowledge 但不 invoke"；Gemini CLI 需要 explicit tool。**"With Skill"不应被当成单一条件**。
3. **Skill authoring 的三条工程建议**：
    - Concise stepwise + 至少一个可运行示例 > 长文档；
    - Modular Skill 在多步任务上组合更好；
    - 要显式 match harness constraints（比如 JSON-only protocol 要在 Skill 里重复格式提醒）。
4. **Skill ≠ 一定变好**。16/84 任务 Skill 反而有害，说明 "添加相关 context 不总是正向的"。这挑战了"给 agent 更多信息就一定更好"的朴素假设。

### 7.1 局限性（作者自陈）

| 局限 | 作者 mitigation | 我的补充思考 |
|------|-------------|------------|
| 只评 terminal / containerized，不覆盖 GUI / 多 agent / 超长 horizon | 承认，并把"多模态 Skill + VLM"列为 future work | 现实落地中 GUI agent 比例很高，这个缺口值得警惕 |
| Skill 注入 = 更多 context，增益可能来自"长度"而非"结构" | Self-Gen 失败作为间接证据，但未做 length-matched baseline | **确实是实验设计的关键空白**：需要 random/irrelevant text 对照 |
| Docker 不能 100% 消除 training-set contamination | 多轮 + leakage audit + paired 比较 | LLM 训练数据对某些 USGS/SEC 工作流的 coverage 会偏置结果 |
| Benchmark Skill 质量均值 10.1/12，远高于生态 6.2/12 | 承认是 optimistic scenario | 真实部署下 Skill 质量更差，增益肯定 < +16.2pp |
| Skill 组合效果不可加和 | 未研究 | 未来可以建"composite Skill calculus" |

---

## 8. 个人思考与组会讨论点

### 8.1 这篇论文的真正贡献

- **第一个把 Skill 当成变量**而非背景设置的 benchmark。过去的 agent benchmark 是 "model × task"，这篇变成 "model × skill × task"，带来新的实验维度。
- **提供了定量、可复现、多模型的证据**，而不是 case study 级别的 anecdote。
- **"Self-gen Skill ≈ 无效"**是很有穿透力的发现：它说明 procedural knowledge 不能从 parametric memory 里自己 elicit 出来，**human curation 在可预见未来是必需品**。

### 8.2 强 / 弱点评估

**强点**：
1. 规模大（7,308 trajectory）、评测设计严谨（确定性 verifier、leakage audit、paired 比较、双 metric）。
2. Failure mode 的程序化分类学（而非 LLM-as-judge）提高复现性。
3. Ecosystem analysis（47,150 Skill 去重）罕见、有参考价值。
4. 11 个 domain 的异质性结果给 Skill 生态的资源配置提供了数据：**healthcare / manufacturing 这些大涨的领域值得优先投入人工 Skill 编写**。

**可疑 / 可讨论的点**：
1. **Length-matched baseline 缺失**：Skill 注入带来了 +1–13% 的 input token，增益是否部分来自"更长 context"而非"结构化 procedural knowledge"？作者承认但未实验。
2. **Skill 质量 rubric 太粗（0–12 分）**，难以做 fine-grained 消融；"Detailed/Compact/Standard/Comprehensive" 的分类边界依赖作者主观判断。
3. **多次 retry 策略不一致**：self-gen 有 retry、main 无 retry，可能轻度偏置 self-gen 结果向乐观方向。
4. **16/84 任务 0% pass**，其中 Skill 反向有害的 4 个任务，作者对原因只给定性解释（"conflicting guidance"），**没有实验对照**（比如 Skill 改写后是否变正向？）。
5. **只有 3 个 commercial harness**，agent-agnostic harness（Harbor）结果没进主表，harness-level 分析其实只在 3 点上做：样本量不够强。
6. **"Skill can compensate for model scale"** 的结论基于 Claude 家族，但 Claude 模型被训练过 Agent Skills spec，**这一点会放大 Skill 增益**——跨 family 验证不充分。
7. **论文内部数字不一致**（见 §11）：Table 3 Mean 行的 Self-Gen Δ_G 是 –1.8，但正文说 –1.3pp；Codex Self-Gen Δ_G Table 写 –8.1 正文写 –5.6；pipeline.pdf caption 用 +12.66pp 正文用 +16.2pp。这反映论文过了多轮修订但终稿未对齐。审稿人应该捕到。

### 8.3 值得延展的问题

1. **Skill synthesis**：能不能用"trajectory → Skill"的蒸馏方式自动生成高质量 Skill？self-gen 失败是因为 model 没有过程记忆，但 trajectory 里是有过程信息的。
2. **Skill composition**：2 个好 Skill 合用 = 1+1 吗？作者 Finding 5 暗示 **1+1<2（到 4+ 反而降）**，这本身是一个有趣的 "procedural interference" 现象，值得形式化建模。
3. **Long-term skill drift**：论文是 snapshot 评测。Skill 的生态特性意味着 "昨天的最佳 Skill 明天可能过时"（比如 openpyxl API 变化），**benchmark 的时间维度**值得专门设计。
4. **Skill 和 RL 的关系**：RL 训练出的 policy ≈ implicit procedural knowledge；Skill ≈ explicit procedural knowledge。两者能否互相转换？这篇文章其实是 Sutton 的 options 框架在 LLM agent 时代的重现。
5. **Adversarial Skill**：如果 malicious user 提供一个"看起来合理、实际有 backdoor"的 Skill，会怎么样？Agent 的 Skill 接受策略几乎是 default trust，这是个安全 gap。
6. **Anti-pattern：Skill hurt 的 16 个任务**，能不能训一个 "Skill skepticism" meta-policy？"在什么情况下该忽略 Skill"也是一种重要的 procedural knowledge。

---

## 9. 技术细节速查

### 9.1 架构 / 资源

| 项目 | 取值 |
|------|------|
| 容器基础镜像 | `ubuntu:24.04` |
| CPU / RAM / Storage | 1–4 cores / 2–10 GB / 10 GB |
| GPU | 无（唯一 GPU 任务被排除）|
| Context budget | 8K token sliding window |
| Temperature | 0（deterministic）|
| Max rounds (Core/Ext/Extreme) | 10 / 30 / 50 |
| Per-task timeout | 600–1200s |
| Verifier | pytest + CTRF，reward 0/1 |
| Bootstrap CI | 1,000 resamples，95% |

### 9.2 模型版本

| 显示名 | API ID |
|---|---|
| Claude Opus 4.5 | `claude-opus-4-5@20251101` |
| Claude Opus 4.6 | `claude-opus-4-6` |
| Claude Sonnet 4.5 | `claude-sonnet-4-5@20250929` |
| Claude Haiku 4.5 | `claude-haiku-4-5@20251001` |
| GPT-5.2 | `openai/gpt-5.2-codex` |
| Gemini 3 Pro | `gemini/gemini-3-pro-preview` |
| Gemini 3 Flash | `gemini/gemini-3-flash-preview` |

### 9.3 API pricing（2026-02，standard 非 cache）

| Model | Input $/MTok | Output $/MTok |
|---|---|---|
| Haiku 4.5 | 1.00 | 5.00 |
| Sonnet 4.5 | 3.00 | 15.00 |
| Opus 4.5 / 4.6 | 5.00 | 25.00 |
| GPT-5.2 | 1.75 | 14.00 |
| Gemini 3 Pro | 2.00 | 12.00 |
| Gemini 3 Flash | 0.50 | 3.00 |

- Flash 缓存命中 63–67%，Gemini Pro 75–76%，GPT-5.2 91–92%，**Claude Code >99%**。实际成本因 cache 再降 50–90%。

### 9.4 Skill 生态统计

| 指标 | 值 |
|------|-----|
| 去重后 Skill 总数 | 47,150 |
| 136 天累计（另一口径）| 84,192 |
| 峰值日增 | 18,904（2026-01）|
| `SKILL.md` token 中位数 | 1,569 |
| 总 Skill 体积中位数 | 2,296 token (≈ 9 KB) |
| 文件数中位数 / Skill | 1（绝大多数 ≤ 5）|
| 主导扩展名 | `.md`（92,760 文件）|
| 生态平均质量分 | 6.2/12（基准选用 ≥9 的 top quartile）|

### 9.5 Skill 结构约定

```
skill-name/
  SKILL.md         # YAML frontmatter (name + one-line description) + procedural body
  scripts/         # 可选，executable code
  references/      # 可选，reference doc
```

Claude Code 和 Codex 通过读取 SKILL.md 的 frontmatter 决定相关性；Gemini CLI 要求 agent 显式调用 `activate_skill(name)`。

### 9.6 Self-Generated Prompt（Appendix C.6）

```
Important: Generate Skills First
Before attempting to solve this task:
1. Analyze task and identify required domain knowledge/APIs/techniques.
2. Write 1–5 modular skill documents.
3. Save each as markdown in environment/skills/.
4. Then solve the task using the skills you created.
```

---

## 10. 关键数字回顾（一页卡片）

- **86 tasks / 84 evaluated, 11 domains, 7 configs, 3 conditions, 7,308 trajectories**
- **Curated Skill: +16.2pp** 均值（+13.6 到 +23.3pp）
- **Self-Generated Skill: –1.3pp** 均值（基本无效；*注：Table 3 Mean 行写的是 –1.8，内部不一致*）
- **Domain extreme**: Healthcare +51.9pp / SWE +4.5pp
- **16/84 任务 Skill 反而变差；16/84 任务 0% pass**
- **最佳绝对性能**: Gemini CLI + Gemini 3 Flash，48.7%
- **最佳相对增益**: Claude Code + Opus 4.5，+23.3pp
- **最佳性价比**: Gemini 3 Flash（$0.57/task）
- **最优 Skill 数量**: 2–3；超过 4 个反而下降
- **最优 Skill 复杂度**: Detailed / Compact > Comprehensive（后者 –2.9pp）
- **小模型 + Skill ≈ 大模型 no-Skill**: Haiku+Skill 27.7% > Opus naked 22.0%
- **49.8% 失败** 类型是 "Quality Below Threshold"——结构对、数值差
- **Skill 最擅长解决**: 领域 API 规范、监管知识、标准工作流

---

## 11. tex 源专属发现（PDF 看不到的信号）

**本节是 tex-based 笔记流程独有的价值**：tex 源里保留了大量 `%` 注释掉的草稿、开发者 TODO、未最终采纳的表格/图/案例。这些提供了：(a) 评审修改痕迹，(b) 作者真正想表达但被删减的细节，(c) 论文内部的数字不一致证据。

### 11.1 数字修订痕迹

| 地方 | 草稿值 | 最终值 | 备注 |
|------|--------|--------|------|
| 任务数 | 85 | 86（84 evaluated） | Abstract 早期 "85 curated tasks" 改为 86 |
| Difficulty Core/Ext/Extreme | 6 / 52 / 27 | 17 / 43 / 26 | 整个难度分布被重新校准 |
| Self-Gen Mean Δ_G | –1.3（草稿） | –1.8（Table 3 最终）| 正文仍用 –1.3，**未对齐** |
| Codex Self-Gen Δ_G | –5.6（草稿 + 正文） | –8.1（Table 3 最终）| **不一致** |
| Claude Opus 4.5 Self-Gen Δ_G | –0.4 | –0.5 | |
| 10-Run Validation 描述 | "10 runs instead of 3" | "10 runs instead of 5" | 原来 main 是 3 runs 改成 5 runs |
| Pipeline caption 增益 | "+12.66pp average improvement" | 正文用 "+16.2pp" | **pipeline.pdf caption 未更新** |
| Skills paired count | 221（2.6 per task） | *正文未出现此数字* | 早期 pairing 描述被完全删除 |

### 11.2 被完全删除的内容（草稿里有，终稿没有）

1. **Table `tab:positioning`: SkillsBench vs 8 个 agent benchmark 的 feature matrix** —— 比较 Container / Verifier / Multi-Dom / Paired / Skills / Leakage / Ablation 7 个维度。被删可能因版面或 reviewer 建议。
2. **Table `tab:leakage`: N-gram Jaccard / Semantic cosine / Command overlap 三项 leakage audit 指标**（mean/max/excluded），展示具体数值。终稿只剩下定性描述。
3. **Context Usage Table `tab:context_full`**：L0/L1/L2/L3/BYOS 五档的 mean tokens / std dev / truncation rate。说明作者**原本设计过 5 档 Skill 分级**（L0-L3 + BYOS = Bring Your Own Skill），终稿简化为 3 档（No/With/Self-Gen）。
4. **3 个 Qualitative Case Studies**：
    - Case 1: CI debugging 成功（47 min 超时 → 12 min 完成）
    - Case 2: OAuth Skill 被识别但被忽略（Haiku 4.5 "acknowledges but ignores"）
    - Case 3: Skill quality impact（Skill A score 11/12 → 87.5%，Skill B score 5/12 → 54.2% 比 vanilla 还差）
5. **Reproducibility Checklist**（6 项），终稿未放出。
6. **Intrinsic difficulty indicators**：dependency depth / tool invocations / state complexity 三个替代难度指标（人类时间的 proxy），与人类耗时 $r=0.73$，被删除。
7. **Per-Skill efficacy 分布**：+8.2pp 到 +31.4pp range，median +17.1pp；3 个 Skill（6%）显示负向 —— 比终稿 "16/84 任务负向" 更细粒度。

### 11.3 作者留在 tex 里的 TODO / 反思

- `% TODO: Regenerate Pareto figure with updated data`（Figure 4 源码旁）—— Pareto 图数据可能不是最新
- `\sh{...}` 命令定义：`\newcommand{\sh}[1]{\textcolor{orange}{[shenghan: #1]}}` —— 作者 Shenghan 的橙色 inline 注释宏（虽然 tex 里没实际使用，但定义存在说明曾有 back-and-forth）

### 11.4 这些发现对读者的价值

- **对 reviewers**：可以指出数字不一致，要求作者 final camera-ready 时对齐
- **对后续工作**：被删除的 L0-L3/BYOS 5 档设计、3 个 case studies 对理解作者的**原始设计意图**很有价值，后续工作可以 revive
- **对 benchmark 用户**：知道 pipeline.pdf caption 数字是草稿、Pareto 图可能旧 —— 不要把细节当 ground truth

---

**笔记数据源**: arxiv tex source (2602.12670v3) + main.tex + sections/*.tex + figs/*.pdf（高 DPI 渲染）

**笔记完成日期**: 2026-04-16

**笔记工具**: paper-read skill L1 (tex-based) 流程，首次 end-to-end 实测
