# PixCell: A Generative Foundation Model for Digital Histopathology Images

> **论文信息**: Yellapragada, Graikos et al., Stony Brook University & Argonne National Laboratory
>
> **arXiv**: 2506.05127v2 (2025.12)
>
> **关键词**: Diffusion Transformer, 病理图像生成, 自监督条件引导, Virtual Staining
>
> **代码/模型**: [Project Page](https://pixcell-project.github.io/) | PixCell-256 | PixCell-1024 | Synthetic TCGA-10M

---

## 1. Motivation & Problem

### 1.1 判别式基础模型的三个结构性瓶颈

计算病理领域目前以 SSL / VLM 等**判别式**基础模型为主流（UNI、Virchow、Hoptimus 等），但存在三个它们无法解决的问题：

1. **标注稀缺** — patch 级标注依赖病理学家，成本高、规模受限；即使用 SSL encoder + linear probe，小数据集（如 BACH 仅 218 训练样本）仍会严重过拟合
2. **隐私壁垒** — 机构间数据共享受限于 IRB / 患者隐私 / 数据所有权，导致各站点只能在自有数据上训练，模型泛化性差、存在人群偏差
3. **生成任务超出判别模型能力** — virtual staining（H&E → IHC）本质上需要从参考图像**合成**全新图像，判别式模型无法胜任

### 1.2 本文定位

构建**首个病理图像生成式基础模型 (PixCell)**，用一个统一的生成模型同时应对：

- **数据增强** — 合成语义一致的变体图像扩充小数据集
- **隐私保护数据共享** — 合成整个数据集的替代品，代替原始患者数据进行跨机构共享
- **Virtual IHC Staining** — 利用大规模 H&E 预训练获得的生成先验，适配到 H&E → IHC 的 stain translation

核心 insight：自然图像生成模型依赖大规模 image-text pairs（如 LAION-5B 的 58.5 亿对），但病理领域**不存在**这种规模的 image-caption 数据。PixCell 用 **SSL encoder 的 embedding 替代 text caption** 作为条件信号，从而绕开了这一瓶颈，实现了无标注的大规模条件训练。

---

## 2. Data: PanCan-30M

论文构建了目前最大规模的病理图像生成训练集 **PanCan-30M**：

| 数据来源 | WSI 数量 | Patches 数量 |
|---------|---------|-------------|
| TCGA diagnostic (FFPE) | 11,766 | 9,192,388 |
| TCGA fresh frozen | 18,310 | 3,698,529 |
| CPTAC | 6,124 | 2,200,109 |
| SBU (内部数据) | 5,698 | 6,689,518 |
| GTEx (正常组织) | 25,713 | 7,896,145 |
| 其他公开数据 (NLST 等) | 1,573 | 1,143,288 |
| **总计** | **69,184** | **30,819,977** |

> **[Figure 1a: PanCan-30M 数据集组成]**
> Caption: PanCan-30M 的 WSI 来源分布，包含来自 28 种器官类型的 69,184 张 WSI。

> **[Figure 20: 各器官 patch 数量分布]**
> Caption: PanCan-30M 按器官类型统计的 patch 数量分布柱状图。肺、乳腺、肾是占比最大的三类，总计 30,819,977 patches。

关键特征：
- 所有 patch 为 **1024×1024 px**，对应 20× 放大倍数（0.5 μm/px）
- 覆盖 **28 种器官类型**，包括癌症和良性组织
- 全部为 **H&E 染色**，不使用 stain normalization
- 使用 DS-MIL 的代码进行 patch extraction 和 tissue thresholding
- 单独划出 **PanCan-Test**（230 万 patches）作为 held-out test set

> **注意**：PanCan-Test 是 **patch-level split**（非 slide-level）。这意味着同一 WSI 的不同 patches 可能分布在 train/test 中，in-distribution 评估可能偏乐观。

---

## 3. Method

### 3.1 整体架构总览

PixCell 采用 **Latent Diffusion Model (LDM)** 范式，在压缩的 latent space 中训练扩散模型，而非直接在像素空间操作。

> **[Figure 1b: PixCell 模型架构和训练流程]**
> Caption: PixCell 架构概览。渐进式训练从 256×256 开始，逐步提升到 1024×1024。每个阶段以 UNI-2h 提取的 embedding 为条件，通过 cross-attention 注入 DiT。

整体数据流：

```
输入图像 (1024×1024×3)
    ↓ [SD3 VAE Encoder, frozen]
VAE Latent (128×128×16)
    ↓ [加噪 → DiT 去噪, 训练阶段]
去噪后 Latent (128×128×16)
    ↓ [SD3 VAE Decoder, frozen]
合成图像 (1024×1024×3)
```

条件信号流：

```
参考图像 (1024×1024)
    ↓ [切分为 4×4 = 16 个 256×256 tiles]
16 个 tiles
    ↓ [UNI-2h encoder, frozen]
16×1536 embedding matrix (保留空间信息)
    ↓ [cross-attention 注入 DiT blocks]
条件引导生成
```

三大组件各自的选择理由：

#### 3.1.1 为什么选 SD3 VAE 而非 SDXL VAE？

| VAE | Latent Dim | 下采样倍数 | 病理 PSNR |
|-----|-----------|----------|----------|
| SDXL | 4 | ×8 | 26.93 |
| **SD3** | **16** | **×8** | **31.79** |

- PSNR 在 1000 张随机 256×256 PanCan-Test tiles 上测量
- SD3 VAE 的 16-dim latent 虽然比 SDXL 的 4-dim 更大（增加下游计算量），但重建质量显著更高
- 对于病理图像这种高频纹理丰富的域，**VAE 的重建精度是生成质量的理论上限**——用 4-dim 会在 VAE 编解码阶段就丢失关键细胞级细节
- VAE 全程 **frozen**，仅用于编码/解码，不参与扩散模型训练
- 训练前**一次性预提取**所有 3080 万 patches 的 VAE latent 并存储到磁盘，训练时直接读取，避免重复编码

#### 3.1.2 为什么选 DiT 而非 U-Net？

Backbone 采用 **Diffusion Transformer (DiT)**，架构改自 PixArt-σ（PixArt 系列最新版本）：

- **28 个 DiT block**，每个 block 包含：Self-Attention → **Cross-Attention** → FFN
- 输入：将 VAE latent patchify 为 token 序列（类似 ViT 的处理方式）
- Self-Attention：捕获 latent patches 之间的空间关系
- **Cross-Attention** 是条件注入的核心机制：
  - Key/Value 来自 UNI-2h embedding（条件信号）
  - Query 来自 latent token（图像内容）
  - 每个 latent token 都可以 attend to 条件 embedding，实现语义引导
- 时间步信息（diffusion timestep）通过 **adaptive layer norm (adaLN)** 注入（来自 PixArt 的设计）

选择 DiT 而非 U-Net 的原因：
- DiT 的 scaling 是**同构堆叠**（加深=堆更多 block，加宽=增大 hidden dim），设计空间简单、行为可预测，且直接继承 LLM/ViT 领域成熟的 scaling laws；U-Net 的 scaling 涉及多个耦合轴（分辨率层级数、每层通道数、attention 位置、skip connection 维度匹配），设计空间更复杂
- DiT 的核心运算（矩阵乘法、attention）对现代 GPU 高度友好；U-Net 的异构运算（多分辨率卷积、skip concat、上下采样）硬件优化更困难
- Cross-attention 天然支持**变长条件输入**（256px 用 1 个 token，512px 用 4 个，1024px 用 16 个），架构不需要修改
- PixArt 系列已在自然图像上验证了 DiT 的高效性，PixCell 将这一范式迁移到病理域

#### 3.1.3 为什么用 SSL Embedding 替代 Text Caption？

这是 PixCell 能 scale up 的**最关键设计**。

```
自然图像:  text prompt  → CLIP text encoder  → embedding → cross-attention → DiT
PixCell:   参考图像      → UNI-2h encoder     → embedding → cross-attention → DiT
```

具体细节：
- **UNI-2h**：大规模病理基础模型（SSL encoder），在 H&E **和 IHC** 图像上训练，输出 1536 维 embedding
- 对每张 1024×1024 图像，UNI-2h 将其切分为 4×4 = 16 个 256×256 tiles，每个 tile 提取一个 1536 维 embedding
- 最终条件为 **16×1536** 的 embedding 矩阵（保留空间信息）
- 同样在训练前一次性预提取所有 embedding 并存储
- 训练时以 **10% 概率 drop condition**（置为 zero），以支持 Classifier-Free Guidance (CFG)

**推理时的使用方式**：
- 给定一张参考图像，提取其 UNI-2h embedding
- 用该 embedding 作为条件，从随机噪声生成一张**语义一致但像素不同**的新图像
- 等价于从"以该 embedding 为中心的图像分布"中采样

> **关键区别**：text caption 是**多对多**的——一句"a breast tissue slide"可以描述极其多样的图像。而一个 UNI embedding **几乎是一对一的**——只对应形态高度相似的少量图像。这导致了后续 CFG scale 选择的巨大差异（详见 3.4）。

**与 LRDM [29] 的关系**：LRDM（同组前作）首先提出了用 SSL embedding 条件化 diffusion model 的思路。PixCell 是其大规模版本，将数据量从小数据集扩展到 3000 万 patches，并引入 DiT 架构和渐进式训练。

### 3.2 渐进式训练策略

**核心思路**：不直接在 1024×1024 上训练（latent 为 128×128×16，计算量大、收敛慢），而是从低分辨率逐步提升。先学局部细胞/纹理结构（低分辨率迭代快），再学远距离组织架构一致性（高分辨率）。这借鉴了 PixArt 系列在自然图像上的做法。

> **[Figure 8: PixCell-256 与 PixCell-1024 模型结构对比]**
> Caption: (a) PixCell-256 以单个 1×1536 UNI-2h embedding 为条件，处理 32×32×16 的 VAE latent；(b) PixCell-1024 以 4×4=16 个空间排列的 1536 维 embeddings 为条件，处理 128×128×16 的 VAE latent。

**关键前提**：所有训练都在**预提取的 VAE latent 和 UNI-2h embedding** 上进行，不需要读取原始像素图像。低分辨率阶段的训练样本通过从高分辨率 latent 中裁切获得：

#### Stage 1: 256×256 (PixCell-256)

```
原始 VAE latent (128×128×16, 对应 1024×1024 图像)
    ↓ 裁切 16 个不重叠的 32×32×16 crops
每个 crop 对应原图中一个 256×256 区域
    ↓ 配对
该区域对应的 1 个 1536 维 UNI-2h embedding
    = 一个训练样本
```

- 30M 图像 × 16 crops = **480M 个训练样本**
- 训练 **120K steps**, batch size **4096**, 16 GPUs
- 模型学到：细胞形态、局部纹理、染色特征

#### Stage 2: 512×512 (中间过渡)

```
原始 VAE latent (128×128×16)
    ↓ 裁切 4 个不重叠的 64×64×16 crops
每个 crop 对应 512×512 区域
    ↓ 配对
该区域对应的 2×2 = 4 个 1536 维 embedding (空间排列)
    = 一个训练样本
```

- 30M × 4 = **120M 个训练样本**
- 用 Stage 1 权重初始化，训练 **60K steps**, batch size **1536**, 24 GPUs
- 过渡阶段：让模型适应**多 token 条件**和中等尺度的组织结构

#### Stage 3: 1024×1024 (PixCell-1024)

```
直接使用完整的 128×128×16 VAE latent
    ↓ 配对
完整的 4×4 = 16 个 1536 维 embedding (空间排列)
    = 一个训练样本
```

- **30M 个训练样本**（原始数据规模）
- 用 Stage 2 权重初始化，训练 **80K steps**, batch size **384**, 32 GPUs
- 模型学到：跨区域的组织架构一致性、全局结构协调

训练参数汇总：

| 阶段 | 分辨率 | Latent 尺寸 | 有效样本数 | 训练步数 | Batch Size | GPU | 条件维度 |
|------|--------|-----------|----------|---------|-----------|-----|---------|
| Stage 1 | 256×256 | 32×32×16 | 480M | 120K | 4096 | 16 | 1×1536 |
| Stage 2 | 512×512 | 64×64×16 | 120M | 60K | 1536 | 24 | 4×1536 |
| Stage 3 | 1024×1024 | 128×128×16 | 30M | 80K | 384 | 32 | 16×1536 |

所有阶段共用：
- **优化器**：AdamW, weight decay = 0.03, learning rate = 2×10⁻⁵ (constant, 无 scheduler)
- **硬件**：NVIDIA DGX A100 集群（每节点 8×A100 320GB, 2×AMD EPYC 7742, SSD 25GB/s）
- **总计算量**：约 **3000 node-hours**（含探索性实验）
- **Condition drop rate**：10%（用于 CFG）
- 每个阶段仅训练 **~1 epoch**，避免过拟合

**设计亮点**：
- Cross-attention 天然支持变长 condition token（1→4→16），模型架构三个阶段完全相同
- 低分辨率阶段样本量大、batch size 大、迭代快；高分辨率阶段 per-sample 信息更丰富
- 预提取特征 → 训练时完全不需要图像 I/O 和 encoder forward pass → 极大加速训练

### 3.3 超高分辨率生成（2048+ px）

PixCell-1024 原生生成 1024×1024 图像。为生成更大分辨率，借鉴 LRDM [29] / MultiDiffusion [6] 的 **patch-wise generation algorithm**：

```
目标大图 (e.g., 4096×4096)
    ↓ 划分为重叠的 1024×1024 区域
每个区域以其对应的 UNI-2h embedding 为条件
    ↓ 独立去噪
重叠区域通过 latent averaging 融合
    ↓ VAE 解码
最终连贯大图 (4096×4096)
```

> **[Figure 12: 4096×4096 合成图像示例]**
> Caption: PixCell-1024 使用 patch-wise generation 合成的 4096×4096 病理图像，兼顾全局组织架构和局部细胞细节。建议放大查看。

> **[Figure 11: 2048×2048 合成图像与 baseline 对比]**
> Caption: 2048×2048 生成对比。∞-Brush 产生模糊细节，ZoomLDM 结构不够真实，PixCell 最佳。

### 3.4 Classifier-Free Guidance (CFG) 的特殊性

训练时以 10% 概率随机 drop condition embedding（设为 0），推理时用标准 CFG 公式：

$$\hat{\epsilon}(x_t, c) = \epsilon(x_t, \varnothing) + w \cdot [\epsilon(x_t, c) - \epsilon(x_t, \varnothing)]$$

通过 grid search 在 PanCan-Test 上确定最优 guidance scale $w$：

| $w$ | 1 | 1.2 | 1.4 | 1.6 | 1.8 | **2** | 3 | 5 |
|-----|---|-----|-----|-----|-----|-------|---|---|
| PixCell-256 FID | 13.25 | 12.21 | 11.16 | 10.67 | 10.34 | **9.65** | 9.81 | 10.54 |
| PixCell-1024 FID | 8.39 | **7.92** | 8.55 | 9.14 | 9.72 | 10.83 | 15.2 | 20.59 |

- PixCell-256 最优 $w$ = **2.0**，PixCell-1024 = **1.2**
- 远低于自然图像 text-to-image 模型的典型值（通常 ~6-7.5）

**为什么最优 scale 这么低？**

一个 text caption（如 "a cat"）可以描述极其多样的图像 → 条件信号模糊 → 需要强 guidance 来提升保真度。而一个 UNI embedding 只对应形态高度相似的少量图像 → 条件信号已经很精确 → 过强的 guidance 反而导致 mode collapse / 生成伪影。

PixCell-1024 的 $w$ 更低（1.2 vs 2.0），因为 16 个空间排列的 embedding 比单个 embedding 提供了更精确的条件信号。

### 3.5 数据增强策略

生成的合成图像继承参考图像的类别标签，用于扩充小数据集。论文提出两种策略：

#### 3.5.1 Vanilla Augmentation

最直接的方式：

```
训练集中每张真实图像
    ↓ [UNI-2h, 提取 embedding]
embedding
    ↓ [PixCell, 条件生成]
合成图像（继承原图的类别标签）
    ↓
训练集 = 真实 + 合成 (double size)
```

适用场景：下游 classifier 使用的 encoder 与条件 encoder (UNI-2h) 相同或相似时效果最好。

#### 3.5.2 Test-time Constraint-Guided Augmentation

**问题**：当下游 classifier 使用的 encoder（如 Virchow-2, Hoptimus-1）与 PixCell 的条件 encoder (UNI-2h) 不同时，vanilla augmentation 可能不足以保证在**目标 encoder 的 embedding 空间**中的语义一致性。

**解决方案**（来自同组工作 [28]）：在 diffusion sampling 过程中施加额外约束：

```
标准采样:    x_{t-1} = f(x_t, c)
约束采样:    x_{t-1} = f(x_t, c) + λ·∇_{x_t} sim(Φ(x̂_0), Φ(x_real))
```

其中 $\Phi$ 是目标 encoder（如 Virchow-2），$\hat{x}_0$ 是当前步的预测干净图像。在每个去噪步额外引入一个梯度信号，推动生成结果在目标 encoder 空间与参考图像更相似。

实际使用时，通过 grid search 在 validation set 上为每个 (encoder, dataset) pair 选择最优策略：
- 搜索空间：增强策略 {Vanilla, Test-time} × guidance scale {1,2,3,4} × lr {1e-3, 1e-4, 1e-5} × weight decay {0, 1e-3, 1e-4}

### 3.6 Virtual Staining Pipeline

这是论文中最具创新性的应用，将一个仅在 H&E 上训练的生成模型适配到 IHC 合成任务。

#### 3.6.1 关键观察：PixCell 的跨 stain 泛化

> **[Figure 18: OOD IHC 图像作为参考的生成结果]**
> Caption: 用 OOD 的 IHC 图像提取 UNI-2h embedding 作为条件，PixCell-256（仅在 H&E 上训练）可以生成 IHC 风格的变体。说明模型学到的生成先验具有跨 stain 泛化能力。

**为什么这能 work？** 因为 UNI-2h 同时在 H&E 和 IHC 图像上训练过，对 IHC 图像也能提取有意义的 embedding。PixCell 在大规模训练中学到了"从 embedding 到图像外观"的通用映射，这个映射对 OOD 的 IHC embedding 也部分成立。

但直接用 IHC embedding 条件化的结果质量有限。论文的目标是更实用的场景：**给定 H&E 图像，生成同一组织区域的 IHC 图像**。

#### 3.6.2 完整 Pipeline

> **[Figure 10: H&E → IHC virtual staining 的完整 pipeline]**
> Caption: Virtual staining pipeline 三步流程。Step 1: UNI-2h 提取 H&E embedding；Step 2: Rectified Flow MLP 将 H&E embedding 转换为 IHC embedding；Step 3: 转换后的 embedding 作为条件，送入带 LoRA 的 PixCell-1024 生成 IHC 图像。

```
H&E image (1024×1024)
    ↓ [UNI-2h, frozen]
H&E embeddings (16×1536)
    ↓ [Rectified Flow MLP, 训练在 paired data 上, 每种 IHC stain 一个]
IHC embeddings (16×1536)
    ↓ [PixCell-1024 + LoRA, LoRA 训练在目标 IHC data 上]
Virtual IHC image (1024×1024)
```

三个组件各自独立训练，推理时串联。以下逐一展开。

#### 3.6.3 Rectified Flow：Embedding Space 的 Domain Transfer

**目标**：学习一个从 H&E embedding 分布到 IHC embedding 分布的映射。

**为什么不直接学一个回归 MLP？** 因为 H&E → IHC 不是一对一映射——同一 H&E 可能对应多种 IHC 表达强度。Rectified Flow 建模**分布到分布**的映射，保留多样性。

**Rectified Flow [55]** 是一种 flow matching 方法，学习两个分布之间的最优传输路径：
- 给定 paired data $(e_{H\&E}, e_{IHC})$，分别是同一组织区域的 H&E 和 IHC 图像的 UNI-2h embedding
- 学习一个**速度场** $v_\theta$，使得从 $e_{H\&E}$ 出发，沿 $v_\theta$ 积分可以到达 $e_{IHC}$
- 网络结构：**残差 MLP**（简单且高效）

训练细节：
- 从 1024×1024 paired images 中提取 loosely-paired 的 256×256 crops
- 分别提取 UNI-2h embedding 作为 $(e_{H\&E}, e_{IHC})$ pair
- 每种 IHC stain 单独训练一个 Rectified Flow（HER2、ER、PR、Ki67 各一个）
- **500 epochs, batch size 512, lr = 1e-4**

推理：从 H&E embedding 出发，用 **Euler ODE solver 积分 100 步**到达 IHC embedding。

> **关键优势**：整个 pipeline 在 **patch-level embedding 空间**操作，不要求 pixel-perfect alignment。这对 MIST 这类只有粗略配对的数据（来自相邻切片，天然存在位移）非常友好。如果直接在像素空间做 stain translation，就需要精确对齐的训练数据。

#### 3.6.4 LoRA：Stain-Specific 微调

仅靠 embedding transfer 生成的 IHC 图像质量不够高——PixCell 毕竟只在 H&E 上训练过，decoder 不熟悉 IHC 的视觉特征。引入 LoRA 微调解决：

> **[Figure 9: 带/不带 LoRA 的 virtual staining 效果对比]**
> Caption: H&E → IHC stain translation 结果。无 LoRA 时生成的 IHC 图像语义方向正确但视觉质量差（模糊、色彩偏移）；加入 LoRA 后质量显著提升，接近真实 IHC 图像。

LoRA 配置：
- 仅在 DiT 的 **cross-attention 层** 添加 low-rank adapter
- 每种 IHC stain 单独训练一个 LoRA
- 训练数据：目标 IHC stain 的图像（不需要 paired H&E）
- **10 epochs, batch size 4, lr = 1e-4**
- Condition drop rate: 10%（保持 CFG 能力）
- **单张 A5000 24GB GPU** 即可训练（~10K iterations）

> **LoRA 的分工**：Rectified Flow 负责"将条件信号从 H&E domain 搬到 IHC domain"（embedding space 的 domain transfer），LoRA 负责"让 decoder 知道 IHC 图像长什么样"（pixel space 的视觉适配）。两者解耦，各自独立且高效。

#### 3.6.5 两个评估数据集

| 数据集 | Patch 尺寸 | IHC Stains | 配对方式 | 分辨率 |
|--------|----------|-----------|---------|-------|
| **MIST** [52] | 1024×1024 | HER2, ER, PR, Ki67 | Loosely-paired（相邻切片，存在位移） | 0.4661 μm/px |
| **HER2Match** [46] | 512×512 | HER2 | Pixel-accurate（re-staining 技术） | 40× |

> **注意**：MIST 的分辨率 (0.4661 μm/px) 与 PixCell 训练分辨率 (0.5 μm/px) 略有差异，这也是 LoRA 有必要的原因之一——除了适应 IHC 视觉特征，还需要适应微小的分辨率偏差。

#### 3.6.6 Virtual Staining 的评估方法

论文指出传统的 pixel-level metrics（PSNR, SSIM）对 virtual staining **不适用**——loosely-paired 数据本身就没有 pixel alignment，且临床诊断关注的是细胞核染色比例而非像素一致性。因此采用两类评估：

**感知指标**（分布级）：Fréchet Distance 衡量生成 IHC 与真实 IHC 的分布距离
- FID (Inceptionv3) — 通用视觉感知
- FHD (Hoptimus-1) — 病理特异性感知
- FVD (Virchow-2) — 病理特异性感知

**诊断评估**（临床级）：更直接地评估生成 IHC 的临床可用性
1. 用 **DeepLIIF** [25] 自动分割 stained / unstained 细胞核
2. 按临床标准为 IHC 图像打诊断标签：

| Stain | Positive | Low Positive / Inconclusive | Negative |
|-------|----------|---------------------------|----------|
| **ER** | ≥10% 阳性核 | 1-10% | <1% |
| **PR** | >1% | — | ≤1% |
| **Ki67** | >30% | 5-30% (Inconclusive) | <5% |

3. 比较合成 IHC 与真实 IHC 的诊断标签一致性
4. 报告：weighted F1, macro F1, Cohen's κ, weighted κ, MCC
5. 另请 board-certified 病理学家在 **blind** 条件下对子集评估，验证自动化评估的可靠性

### 3.7 ControlNet：细胞级可控生成

在 PixCell-256 基础上添加 ControlNet，引入 cell segmentation mask 作为额外条件，实现外观与布局的解耦。

> **[Figure 13: Cell Mask ControlNet 结构]**
> Caption: PixCell-256 + Cell ControlNet。UNI embedding 控制图像外观/风格（颜色、组织类型），cell mask 控制细胞数量和空间布局。两种条件信号通过 ControlNet 的 zero-initialized linear layer 融合。

```
参考图像 → UNI-2h embedding → 控制外观/风格
                                    ↓ cross-attention
Cell mask → ControlNet (复制 DiT 各层 + zero-init linear) → 控制细胞布局
                                    ↓ 特征融合
PixCell-256 DiT → 合成图像
```

训练：
- 用预训练 **CellViT-SAM-H** [34] 从 PanCan-30M 中随机采样 10,000 张图像提取 binary cell mask
- 以 (image, UNI embedding, cell mask) 三元组训练 ControlNet
- **25K iterations, batch size 4, lr = 1e-5, AdamW**

> **[Figure 14: ControlNet 生成示例]**
> Caption: Cell mask ControlNet 生成示例。Style image 提供 UNI embedding，mask 提供布局。当两者信号冲突时（top 行列 6-7），生成可能不完全遵循 mask，因为 UNI embedding 本身也编码了部分 cell layout 信息。Guidance scale w=2.5。

**Targeted data augmentation 实验**（Lizard 数据集 [26]）：
- 为测试集图像提取 UNI embedding，配对训练集的 cell mask
- 生成具有测试集外观 + 已知 mask 标签的合成图像，作为额外训练数据
- 注意：这**不需要**测试集的 ground truth mask（只用了外观信息）

| 指标 | Baseline | + PixCell 增强 |
|------|----------|--------------|
| Accuracy | 0.857 | **0.890** |
| Dice | 0.629 | **0.653** |
| IoU | 0.751 | **0.802** |

---

## 4. 实验结果

### 4.1 图像生成质量

评估数据集设计（由近及远的泛化测试）：
- **PanCan-Test** (within-distribution)：同分布 held-out，230 万 patches
- **SPIDER** (cross-source)：不同 imaging center 的 Breast/Colorectal/Skin/Thorax，33.9 万 patches，**未参与训练**
- **Non-H&E** (stain robustness)：HistAI 中的非 H&E 染色 WSI，340 万 patches，**未参与训练**

> **[Figure 2a: Fréchet Distance 对比 (FID / FHD / FVD)]**
> Caption: PixCell 在 PanCan-Test、SPIDER（跨站点）、Non-H&E（跨染色）三个数据集上，使用通用 (Inceptionv3) 和病理特异性 (Hoptimus-1, Virchow-2) encoder 度量 Fréchet Distance，全面优于 LRDM 和 ZoomLDM。

关键数字：
- 在 pathology-specific 的 FHD (Hoptimus-1) 上，PixCell-256 比次优方法低约 **50%**
- 在 SPIDER 和 Non-H&E（都未参与训练）上同样最优 → 强泛化能力
- PixCell-1024: Crop FID **7.92**, CLIP FID **0.68**，生成速度 **2.5s/image**（LRDM 60s, ZoomLDM 28s）

> **[Table 6: PixCell-1024 与 baseline 的 1024×1024 生成质量对比]**
> Caption: PixCell-1024 在 TCGA-BRCA 上的 Crop FID、CLIP FID 和生成速度全面领先。生成速度比 ZoomLDM 快 11×，比 LRDM 快 24×。

**病理学家评估**（4096×4096 合成区域，blind 对比 PixCell vs ZoomLDM）：

> **[Figure 2b: 病理学家 image quality 评分]**
> Caption: 两位 board-certified 病理学家对 4096×4096 合成区域的五项评分（组织架构 Tissue Architecture、细胞形态 Cell Morphology、清晰度 Sharpness、色彩保真度 Color Fidelity、真实感 Realism），PixCell 在 BRCA 和 PRAD 上全面优于 ZoomLDM。评分采用 1-3 ordinal scale。

> **[Figure 2c: 病理学家 subtyping 准确率]**
> Caption: 病理学家基于合成 BRCA 区域的 lobular vs ductal carcinoma 分型准确率达 94.4%（N=18 WSIs），与真实图像结果几乎一致。唯一的不一致是 1 例被标为 "Unsure"。

### 4.2 语义保持与数据增强

> **[Figure 3: embedding 相似度、定性对比、数据增强效果]**
> Caption: (a) 合成图像与真实图像在 Hoptimus-1、KEEP、Virchow-2 三个独立 encoder embedding 空间的 cosine similarity，PixCell 在所有 encoder 上最高（>0.7），显著优于 LRDM 和 ZoomLDM；(b) Real vs Synthetic 定性对比，合成图像保留了关键形态学特征但生成了不同的像素级变体；(c) 在 4 个小数据集上，用合成数据增强后，三种 SOTA encoder 的平均 F1 一致提升约 3%。

数据增强的增益在小数据集尤为显著——这些数据集的 k-NN 性能远低于 linear probe，说明过拟合严重：

| 数据集 | 训练样本数 | UNI-2h k-NN → Linear Probe → + 增强 |
|-------|---------|--------------------------------------|
| BACH | 218 | 79.4 → 87.0 → **87.9** |
| BRACS | 3,657 | 52.3 → 63.9 → **65.1** |
| Break-His | 936 | 74.1 → 78.0 → **86.8** |
| mHist | 1,743 | 67.8 → 80.4 → **81.8** |

### 4.3 隐私保护合成数据共享

> **[Table 1: SSL encoder 在真实 vs 合成数据上的 k-NN 性能]**
> Caption: DINOv2 ViT-B 分别在 TCGA Real (10M)、TCGA Synthetic (10M, PixCell 生成)、TCGA Real + HistAI Synthetic (10M+10M) 上训练 100K iterations，在 9 个下游 patch 分类任务上的 k-NN balanced accuracy。

| 训练数据 | 平均 Balanced Acc |
|---------|-----------------|
| TCGA Real (10M) | 77.89% |
| TCGA Synthetic (10M) | 76.64% (Δ = -1.25%) |
| TCGA Real + HistAI Synthetic (10M+10M) | **79.11%** (Δ = +1.22%) |

模拟的跨机构场景：

```
Institute 1 (拥有 TCGA)                 Institute 2 (拥有 HistAI)
    │                                       │
    │                                       ↓ [PixCell 生成合成替代]
    │                                   HistAI Synthetic (10M)
    │                                       │
    │               ←── 共享合成数据 ──────────┘
    ↓
TCGA Real + HistAI Synthetic → 训练 DINOv2 → 79.11% (超越单独 TCGA 的 77.89%)
```

关键发现：
- 合成数据可作为真实数据的 **drop-in replacement**，性能仅差 1.25%
- 但直接用同分布合成数据 double 训练集（TCGA Real 100% + Syn 100%）**没有增益**（76.76%）
- 只有引入**新分布**的合成数据（HistAI）才能提升泛化性
- 在 data-constrained 场景（仅 50% real slides），补充合成数据也能从 76.22% 恢复到 76.87%

### 4.4 Virtual IHC Staining

> **[Figure 4: MIST 数据集上各 IHC stain 的 Fréchet Distance 对比]**
> Caption: MIST 上 HER2、ER、PR、Ki67 四种 IHC stain 的 FD 对比（PixCell vs ASP vs USIGAN），使用 Inceptionv3、Hoptimus-1、Virchow-2 三种 encoder。PixCell 在 pathology-specific encoder 上全面领先。

> **[Figure 5: HER2Match 数据集上的 Fréchet Distance 对比]**
> Caption: HER2Match 上的 FD 对比。左侧为 Klöckner et al. 报告的 baseline 结果（Pyramid Pix2Pix、ASP、BCI、Stainer、Dual Diffusion、Consistency Model、Brownian Bridge），右侧为重训练的 USIGAN baseline 和 PixCell。PixCell 在 pathology-specific encoder 上超越所有方法。

> **[Figure 6: 自动化和病理学家的诊断一致性评估]**
> Caption: ER、PR、Ki67 的诊断评估。(a) 自动化评估（DeepLIIF）的 wF1、mF1、κ、κw、MCC；(b) 病理学家 blind 评估。PixCell 在所有 stain 的所有 metric 上均显著优于 ASP 和 USIGAN。

> **[Figure 7: Virtual staining 定性对比 (MIST)]**
> Caption: H&E → IHC stain translation 定性对比。USIGAN baseline 未能翻译关键诊断特征（如细胞核染色模式），PixCell 准确翻译了 H&E 到 IHC 的细胞特征。

> **[Figure 19: Virtual staining 定性对比 (HER2Match)]**
> Caption: HER2Match virtual staining 示例。HER2Match 包含更多 negative 区域，是更困难的数据集。USIGAN 倾向于 over-stain（高 false positive rate），PixCell 更准确地捕获了目标分布。

---

## 5. 思考与讨论

### 5.1 值得肯定的设计

1. **SSL embedding 条件化的范式价值** — 彻底绕开了病理领域缺乏 image-text pairs 的核心瓶颈，使大规模无标注训练成为可能
2. **渐进式训练 + 预提取特征** — 训练时完全不需要原始图像 I/O 和 encoder forward pass，极大加速训练，且 cross-attention 天然支持变长条件
3. **Virtual staining pipeline 的 modular 设计** — Rectified Flow (embedding transfer) + LoRA (visual adaptation) 解耦，各自独立且轻量，可在单张 A5000 上完成
4. **评估设计全面** — 三个梯度的泛化测试（in-distribution / cross-source / cross-stain）+ 自动化 + 病理学家 blind 评估 + 诊断级评估

### 5.2 可深入讨论的问题

1. **合成数据的"天花板效应"**
   - TCGA Real 100% + Syn 100% 没有增益（76.76% vs 77.89%），说明同分布合成数据不能提供新信息
   - 只有引入新分布（HistAI）才有提升 → 合成数据的价值在于**跨机构分布的模拟**，而非简单的数据量翻倍
   - 这对我们使用合成数据增强的场景有什么启示？

2. **隐私保证的实际强度**
   - 论文承认生成模型可能 leak 训练数据（引用 Carlini et al. 2023 的 diffusion model training data extraction 工作）
   - 合成数据共享仅是"第一步"，不能替代严格的隐私保护方法（如 differential privacy）
   - 条件生成（conditioning on real embeddings）可能比无条件生成泄露更多信息——embedding 本身是否包含可识别的患者信息？

3. **Virtual staining 的 pipeline 依赖链**
   - UNI-2h 对 IHC 的编码能力 → Rectified Flow 的 domain transfer 质量 → LoRA 的视觉适配 → 最终 IHC 质量
   - 任何一个环节出问题都会影响最终结果
   - 如果目标 stain 是 UNI-2h 训练时未见过的稀有 IHC stain，整个 pipeline 可能失效

4. **诊断评估的可靠性**
   - DeepLIIF 作为自动评估工具，本身与病理学家的一致性在 PR (κ=0.516) 和 Ki67 (κ=0.554) 上偏低（Table 10）
   - 这意味着论文报告的诊断评估结果受限于 DeepLIIF 的准确性
   - 更严格的验证应该完全基于病理学家评估，但成本更高

5. **PanCan-Test 的 split 策略**
   - Patch-level split（非 slide-level）可能导致 train/test data leakage（同一 WSI 的相邻 patches 极其相似）
   - 好在论文还在 SPIDER 和 Non-H&E 上做了 out-of-distribution 评估，部分缓解了这一担忧

6. **与 LPFM 的对比与互补**
   - LPFM 定位为**低层级**病理基础模型（修复+虚拟染色），PixCell 定位为**生成式**基础模型（数据增强+隐私共享+虚拟染色）
   - Virtual staining 是两者的交集：LPFM 直接在像素空间做条件生成（需要 paired data），PixCell 在 embedding 空间做 domain transfer（只需 loosely-paired data）
   - PixCell 的优势在于不需要 pixel-aligned pairs，LPFM 的优势在于端到端的像素级控制
   - 两者是否可以结合？如 PixCell 做初步 stain transfer → LPFM 做质量精炼

---

## 6. 技术细节速查

| 项目 | 详情 |
|------|------|
| **训练数据** | PanCan-30M: 69,184 H&E WSIs → 30,819,977 patches (1024×1024, 20×) |
| **测试数据** | PanCan-Test (2.3M), SPIDER (339K, OOD), Non-H&E (3.4M, OOD) |
| **VAE** | Stable Diffusion 3 VAE (frozen), ×8 下采样, latent dim=16, PSNR 31.79 |
| **Backbone** | DiT (28 blocks, 改自 PixArt-σ), adaLN for timestep, cross-attention for condition |
| **条件 Encoder** | UNI-2h (frozen), 1536 维 embedding per 256×256 tile |
| **条件注入** | Cross-attention (Key/Value = UNI embedding, Query = latent token) |
| **渐进训练** | 256→512→1024, 每阶段~1 epoch, constant lr=2e-5 |
| **优化器** | AdamW, weight decay=0.03 |
| **CFG scale** | PixCell-256: w=2.0, PixCell-1024: w=1.2 |
| **硬件** | 32× A100, ~3000 node-hours |
| **Virtual staining** | Rectified Flow (残差 MLP, 500 epochs) + LoRA (cross-attn, 10 epochs, 单张 A5000) |
| **推理速度** | PixCell-1024: 2.5s/image (vs ZoomLDM 28s, LRDM 60s) |
| **增强效果** | 4 小数据集平均 F1 +3% |
| **合成 SSL** | TCGA Syn: 76.64% vs Real: 77.89% (Δ=-1.25%) |
| **评估指标** | FID/FHD/FVD, Embedding cosine similarity, wF1/mF1/κ/MCC (virtual staining) |
| **评估工具** | Clean-FID, DeepLIIF (IHC 诊断评估), Thunder benchmark (SSL 评估) |
