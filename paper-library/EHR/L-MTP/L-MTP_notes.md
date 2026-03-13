# L-MTP: Leap Multi-Token Prediction Beyond Adjacent Context for Large Language Models

> **论文信息**: Xiaohao Liu, Xiaobo Xia, Weixiang Zhao, Manyi Zhang, Xianzhi Yu, Xiu Su, Shuo Yang, See-Kiong Ng, Tat-Seng Chua (NUS, HIT, THU, CAS, CSU)
>
> **发表**: NeurIPS 2025
>
> **关键词**: Multi-Token Prediction, Speculative Decoding, LLM Inference Acceleration, Leap Mechanism
>
> **代码**: https://github.com/Xiaohao-Liu/L-MTP

---

## 1. Motivation & Problem

### 1.1 问题背景

Next-Token Prediction (NTP) 是 LLM 训练和推理的主流策略，但存在两个核心瓶颈：
- **上下文覆盖有限**：每步仅基于前文预测单个 token，短视地聚焦于相邻上下文
- **推理效率低下**：严格的自回归串行生成，每个 token 需要一次 forward pass

### 1.2 现有方法的局限

Multi-Token Prediction (MTP) 是 NTP 的自然扩展（如 DeepSeek-V3、Gloeckle et al. 2024），通过多个输出头并行预测相邻的 $n$ 个 token。但 MTP 的预测范围仍局限于**相邻位置** $[t+1, t+2, ..., t+n]$，没有突破局部上下文的限制。

### 1.3 本文定位

提出 **Leap Multi-Token Prediction (L-MTP)**，核心思路：不预测相邻 token，而是**跳跃式**预测非连续位置的 token。例如，4 个头预测 $[t+1, t+3, t+5, t+7]$ 而非 $[t+1, t+2, t+3, t+4]$。

**核心优势**：
1. 更宽的训练信号——捕获长程依赖
2. 更快的推理——通过 "looking backward" 解码策略复用重叠上下文

---

## 2. Method

### 2.1 Background: NTP → MTP

**NTP 目标**：

$$\mathcal{L}_{\text{NTP}} = -\sum_T \log p(x_{t+1} | x_{\leq t}; \theta)$$

**MTP 目标**（多头并行预测相邻 token）：

$$\mathcal{L}_{\text{MTP}} = -\sum_T \log p(x_{[t+n,...,t+1]} | x_{\leq t}; \bar{\theta})$$

MTP 将 LLM 分解为 backbone（生成 hidden states $z$）+ 多个输出头：

$$p(x_{t+n,...,t+1} | x_{\leq t}) = \prod_{i=1}^n p(x_{t+i} | z_{\leq t}; \theta_i) \cdot p(z_{\leq t} | x_{\leq t}; \theta')$$

> **[Figure 1: Architecture Comparison]** NTP 单头串行 → MTP 多头相邻 → L-MTP 多头跳跃

### 2.2 L-MTP 核心设计

给定输入 $x_{\leq t}$，L-MTP 预测跳跃间隔为 $k$ 的 token 序列：

$$x_{[t+k(n-1)+1, ..., t+k+1, t+1]}$$

例如 $k=2, n=4$：预测位置 $[t+1, t+3, t+5, t+7]$，跳过中间 token。

### 2.3 两阶段训练

**Stage 1: Head Warm-up**（冻结 backbone，仅训练新头）
- 用自蒸馏数据（backbone 自己生成的输出）
- 新头按跳跃模式 $x_{t+k(i-1)+1}$ 分配不同的监督信号

$$\mathcal{L}^{(1)}_{\text{L-MTP}} = -\sum_T \log p(x_{[t+k(n-1)+1,...,t+k+1]} | z_{\leq t}; \{\theta_i\}_{i>1})$$

**Stage 2: Full Model Tuning**（LoRA 微调全模型）

$$\mathcal{L}^{(2)}_{\text{L-MTP}} = -\sum_T \log p(x_{t+1} | x_{\leq t}; \theta', \theta_1) + \beta \cdot \log p(x_{[t+k(n-1)+1,...,t+k+1]} | x_{\leq t}; \theta', \{\theta_i\}_{i>1})$$

其中 $\beta$ 控制额外头的贡献权重。

> **[Figure 3+4: Training Recipe & Tree Attention]** 左：L-MTP 训练流程，先 warm-up 再 full tuning。右：与 tree-attention 的结合用于推理加速。

### 2.4 推理策略：Looking Backward

L-MTP 每步只预测不连续的 token（有间隙）。关键洞察：**间隙中的 token 已被前一步预测过**。

例如，当前步预测 $\{x_{t+1}, x_{t+3}, x_{t+5}, x_{t+7}\}$，而前一步（条件 $x_{\leq t-1}$）已预测了 $\{x_t, x_{t+2}, x_{t+4}, x_{t+6}\}$。通过"回看"前一步的结果，可以填补间隙：

$$\{p(x_{t+i} | x_{\leq t - (i-1) \bmod k}) \mid i \in \{1, 2, ..., k(n-1)+1\}\}$$

连续序列通过回看 $k-1$ 步获得，无需额外推理，只需检索已有预测。

### 2.5 结合 Tree Attention

L-MTP 与 speculative decoding 无缝集成：
- 构建层次化 token tree，第 $i$ 层代表第 $i$ 个头的候选 token
- 探索 tree 中的路径找到被接受的序列
- 使用 tree attention mask 限制每个 hidden state 只关注其祖先节点

> **[Figure 2: MTP Self-Speculative Decoding]** 三步流程：Prediction → Verification → Acceptance

---

## 3. 理论分析

### 3.1 两个核心性质

**Definition 1 (Attenuation)**：预测越远的 token，边际概率越低：

$$p(x_{t+1}|x_{\leq t}) > p(x_{t+2}|x_{\leq t}) > \cdots > p(x_{t+n}|x_{\leq t})$$

**Assumption 2 (Consistency)**：期望边际概率关于预测距离 $i$ 稳定且可预测：

$$\mathbb{E}_{x_{\leq t} \sim \mathcal{D}}[p(x_{t+i}|x_{\leq t})] = f(i)$$

### 3.2 Theorem 3: Less Attenuation, More Speed-up

设衰减函数 $f(i) = \exp[-\gamma \cdot (i-1)]$，则当 $\gamma = O(1/n^2)$ 时，L-MTP 的期望接受长度渐近优于 vanilla MTP：

$$E[L]_l > E[L]_s$$

**直觉**：L-MTP 用更长的预测范围 $k(n-1)+1$ 补偿跳跃位置的置信度损失。当衰减系数 $\gamma$ 较小（模型预测较自信），L-MTP 的加速效果越显著。

> **[Figure 5: Theoretical Curves]** 不同 $\gamma$ 下的边际概率、联合概率、期望接受长度对比。$k=2$（L-MTP）一致优于 $k=1$（MTP）。

---

## 4. 数据

### 训练数据
- **Math** [Hendrycks et al.]: 7.5K 数学问题
- **Evol-Instruct-Code** [WizardCoder]: 80K 代码生成指令
- **Alpaca-GPT4**: 52K 通用指令

Stage 1（head warm-up）: 全量自蒸馏数据
Stage 2（full model tuning）: 随机采样 10K 样本（math:code:general = 4:4:2）

### 评测基准
| 类别 | 基准 | 指标 |
|------|------|------|
| 数学 | Math500 (4-shot), GSM8K (4-shot) | Accuracy |
| 代码 | MBPP/MBPP+, HumanEval/HumanEval+ | Pass@1 |
| 通用 | MMLU, IFEval | Accuracy |

---

## 5. 实验结果

### 5.1 性能对比 (RQ1)

6 个 base model × 3 种预测范式 (NTP/MTP/L-MTP) 的全面对比（Table 1）：

**关键发现**：
- L-MTP 在大多数任务上优于 MTP，尤其是 Llama/Gemma 系列的数学任务和 Qwen 系列的代码任务
- Gemma3-12B: L-MTP (49.58 avg) 显著优于 MTP (45.17) 和 NTP (46.87)
- 所有模型在 IFEval（指令遵循）上均有提升

### 5.2 推理加速 (RQ2)

> **[Figure 6: Speedup]** 3D 柱状图展示不同模型/任务的 speedup ratio

- L-MTP 的 "looking backward" 解码**无需任何架构修改**
- 与 MTP 相比，L-MTP 在 GSM8K 上实现更高加速
- 扩展到 Medusa 模型（Table 2）：直接切换到 L-MTP 解码策略带来 **22% 相对加速**（最高 2.43×）

### 5.3 预测精度分析 (RQ3)

> **[Figures 7-9: Prediction Accuracy]**

- 验证了 Attenuation 和 Consistency 性质
- L-MTP 在远距离位置保持了更好的精度
- **Myopia 现象**：更大的模型反而在远距离预测上更差（NTP 预训练的固有近视）
- 数据量增加可提升精度，但增长非线性

### 5.4 与 MTP n=7 的对比

直接增加 MTP 头数到 n=7 不能改善整体性能（Avg 51.82 < MTP n=4 的 52.79）。而 L-MTP k=3, n=3 仅用 3 个头就达到 52.35，接近 MTP n=4 的效果。说明**跳跃策略比堆叠更多头更有效**。

---

## 6. Discussion & 局限性

### 局限性
- 实验限于 ≤12B 模型（计算资源限制）
- $n$ 和 $k$ 的选择目前是固定的（$k=2, n=4$），未自适应
- 数据质量对结果影响大（部分情况下 NTP 微调也会降低 base 性能）

### 未来方向
- 自适应 $n$ 和 $k$：基于局部 uncertainty/entropy 动态调整
- 从头预训练（而非后训练）使用 L-MTP 目标
- 与 reinforcement fine-tuning 结合

---

## 7. 个人思考与讨论点

### 值得肯定的设计
1. **简洁有效的思路**：仅改变预测位置的分配（skip → leap），不增加架构复杂度
2. **Looking backward 解码**：巧妙利用前一步的预测填补间隙，零额外推理开销
3. **理论与实验一致**：Attenuation/Consistency 的理论分析在实验中得到验证
4. **即插即用**：可直接应用到已有 MTP 模型（如 Medusa）的解码策略

### 可深入讨论的问题
1. **$k=2$ 的普适性**？论文默认 $k=2$，但不同任务/模型可能有不同的最优 $k$。自适应 $k$ 的选择是关键的未来工作
2. **训练数据规模太小**？Stage 2 仅用 10K 样本。在更大规模数据上 L-MTP 的优势是否更明显？
3. **与 DeepSeek-V3 MTP 的关系**：DeepSeek-V3 已大规模部署 MTP，L-MTP 能否直接替换？
4. **Myopia 悖论**：大模型在远距离预测上更差，这是否意味着 L-MTP 对大模型的收益会递减？
5. **推理加速的实际瓶颈**：speedup ratio 多数在 1.5-2.5×，相比 speculative decoding with draft model 的 3-4× 是否有竞争力？

---

## 8. 技术细节速查

| 项目 | 配置 |
|------|------|
| 默认设置 | $k=2$（stride），$n=4$（heads） |
| Head 架构 | Medusa-style MLP: $z' = z + \text{SiLU}(Wz + b)$，$W_{\text{head}}$ 初始化自原始 head |
| Stage 1 训练 | LR=1e-3, 5 epochs, cosine scheduler, warmup ratio=0.1 |
| Stage 2 训练 | LoRA (rank=32, alpha=16), LR=1e-5, 3 epochs |
| 训练数据 | Stage 1: 全量自蒸馏; Stage 2: 10K (math:code:general=4:4:2) |
| Base 模型 | Llama 3.2-3B/3.1-8B, Qwen 2.5-3B/7B, Gemma 3-4B/12B |
| 预测范围 | MTP: $n=4$ tokens; L-MTP: $k(n-1)+1=7$ tokens |
| 硬件 | 2× NVIDIA H100-80G |
| Speedup | L-MTP 自解码 ~1.5-2.5×; + Medusa 最高 2.43× |
