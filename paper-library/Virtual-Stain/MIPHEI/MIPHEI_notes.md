# MIPHEI-ViT: Multiplex Immunofluorescence Prediction from H&E Images using ViT Foundation Models

> **论文信息**: Guillaume Balezo (Sanofi), Roger Trullo (InstaDeep/Sanofi), Albert Pla Planas (Sanofi), Etienne Decenciere (Mines Paris PSL), Thomas Walter (Mines Paris, Institut Curie, INSERM) | arXiv: 2505.10294v1, May 16, 2025
> **关键词**: Computer Vision, Histopathology, Image Translation, Foundation Model, In Silico Labelling
> **代码**: 未公开

---

## 1. Motivation & Problem

### 1.1 问题背景

Multiplex immunofluorescence (mIF) 是肿瘤微环境 (TME) 研究的重要工具，能够在单张组织切片上同时检测 **多达数十种蛋白标记物**，实现对免疫细胞亚群、上皮、基质、血管等组织组分的空间定位与定量分析。然而 mIF 存在根本性的实际瓶颈：

- **成本高昂**：试剂费用、设备投入（如 Vectra/CODEX 等多光谱成像平台）以及高度专业化的实验流程使其难以大规模部署。
- **通量受限**：一次实验耗时数小时至数天，无法应对回顾性大队列 (retrospective cohort) 的分析需求。
- **组织消耗**：需要珍贵的临床样本切片，而很多回顾性队列只有 H&E 染色切片存档。

与此同时，H&E 染色切片几乎在所有病理诊断流程中都是标准操作，存量数据极为庞大。**核心科学假设** 是：H&E 图像中已经编码了足够丰富的形态学信息（细胞核形态、组织结构、染色质密度、细胞间距等），可以通过深度学习"解码"出 mIF 标记物的空间分布——即 **in silico labelling**。

### 1.2 现有方法的局限

此前的 in silico labelling 工作存在以下不足：

1. **标记物数量有限**：如 HEMIT 等方法仅预测 2-3 个通道（DAPI + CD3 + Pan-CK），远不能覆盖 TME 的复杂性。
2. **编码器能力不足**：多数方法使用从头训练的 CNN 或 ImageNet 预训练模型，缺乏对病理图像特异性特征的建模能力。
3. **GAN 带来的伪影问题**：Pix2Pix 等对抗训练框架虽能提升视觉质量，但实验表明（本文 Table 1）GAN discriminator 会**降低**细胞级别的分类准确率——这是一个重要的反直觉发现。
4. **泛化性差**：在训练数据集上表现尚可，但迁移到新数据集/新中心时性能急剧下降。
5. **评估指标不够全面**：仅使用 PSNR/SSIM 等像素级指标，忽视了对下游生物学分析真正重要的细胞级别准确性。

### 1.3 本文定位

MIPHEI 的核心贡献可概括为：

- **首次将病理学 ViT Foundation Model（H-optimus-0, ViT-G/14）** 集成到 U-Net 架构中用于 mIF 预测任务，利用大规模预训练带来的丰富特征表示；
- 提出 **ViTMatte 集成策略**：并行 CNN 流提供金字塔特征 + ViT bottleneck，平衡了全局上下文与局部细节；
- 同时预测 **16 个标记物通道**（涵盖 nuclear content, immune lineages, epithelium, stroma, vasculature, proliferation），是目前最全面的 mIF 预测工作之一；
- 在三个独立数据集（ORION, HEMIT, IMMUcan）上系统验证，包括 **跨数据集泛化** 和 **连续切片对比**（非同一组织）；
- 提出了结合 **像素级 + 细胞级** 的多层次评估框架。

---

## 2. Method

### 2.1 整体架构

MIPHEI 采用 **U-Net 启发的 encoder-decoder 架构**（参见 `figures/fig2_architecture.png`），关键设计决策如下：

```
Input (H&E, 256×256, 0.5 mpp)
    │
    ├──→ [ViT Foundation Model Encoder (H-optimus-0, ViT-G/14)]
    │         │
    │         └──→ Bottleneck features (global context)
    │
    ├──→ [Parallel CNN Stream] ──→ Multi-scale pyramidal features
    │
    └──→ [Decoder: Upsample + Skip Connections + Dual 3×3 Conv + BN + ReLU]
              │
              └──→ Multiple Output Heads (per-marker, Tanh activation)
```

**编码器选择**：H-optimus-0 是一个 ViT-G/14 模型（约 1.1B 参数），在大规模病理图像上预训练。文中对比了三个 foundation model：
- CTransPath（Swin Transformer, 较小）
- UNI v2（DINOv2 based）
- **H-optimus-0**（最终选择，性能最优）

### 2.2 核心模块详解

#### 2.2.1 ViT 集成策略：UNETR vs. ViTMatte

这是本文最重要的架构设计选择。ViT 输出的是 **等分辨率的 token 序列**（所有 token 在同一空间尺度），而 U-Net 的 decoder 需要 **多尺度金字塔特征**。文中探索了两种解决方案：

**方案一：UNETR**
- 直接从 ViT 不同层提取 token → reshape 为 2D feature map → transpose convolution 逐步上采样
- 优点：结构简洁
- 缺点：ViT 的中间层 token 并非为不同分辨率设计，转置卷积上采样可能引入棋盘伪影

**方案二：ViTMatte（最终采用）**
- 添加一个 **并行的轻量级 CNN 流**，独立处理输入 H&E 图像，产生传统的金字塔特征（多尺度）
- ViT encoder 仅负责 **bottleneck 层**的全局特征提取
- Decoder 的 skip connections 来自 CNN 流的多尺度特征，而非 ViT 中间层
- **关键优势**：CNN 天然提供局部细节和空间精确性，ViT 提供全局语义理解，二者互补

消融实验（Table 1）显示 ViTMatte 在 Cell AUC (0.876 vs 0.868) 和 Cell F1 (0.438 vs 0.431) 上均优于 UNETR，虽然 PSNR 略低（27.78 vs 27.86）——再次说明 **像素级指标与细胞级指标可以不一致**。

#### 2.2.2 Decoder 设计

Decoder 的每个 stage 包含：
1. **Nearest neighbor interpolation** 上采样（2x），避免转置卷积的棋盘伪影
2. 与对应 encoder 层的 **skip connection** 拼接
3. **Dual 3×3 convolution** + BatchNorm + ReLU
4. 最后一层：**多个独立输出 head**，每个 head 对应一个 marker，使用 **Tanh 激活函数**

Tanh 激活对应输出范围 $[-1, 1]$，目标值被缩放到 $[-0.9, 0.9]$ 以避免梯度饱和区。

#### 2.2.3 损失函数

采用 **加权 MSE 损失**，权重通过 inverse variance 自动学习：

$$\mathcal{L}_{\text{wMSE}} = \lambda \sum_{j=1}^{C} \frac{1}{\sigma_j^2} \cdot \mathcal{L}_{\text{MSE}, j}$$

其中：
- $C$ 是标记物通道数（16）
- $\sigma_j^2$ 是第 $j$ 个通道的可学习方差参数
- $\lambda$ 是全局权重系数
- $\mathcal{L}_{\text{MSE}, j} = \frac{1}{N} \sum_{i=1}^{N} (y_{ij} - \hat{y}_{ij})^2$

**设计动机**：不同 marker 的信号强度差异极大（如 Pan-CK 阳性区域占比远大于 PD-L1），固定等权重会导致模型过度优化"容易"的通道。Inverse variance weighting 本质上是一种 **uncertainty-based multi-task weighting**（类似 Kendall et al., 2018 的思想），让模型自动平衡各通道的学习难度。

**重要决策：不使用 GAN**。Table 1 显示 Pix2Pix（加入 discriminator）的 Cell AUC 从 0.868 降至 0.817，Cell F1 从 0.431 降至 0.410。原因可能是：GAN 优化视觉真实感（高频细节），但会引入 hallucinated structures，对细胞级分类有害。

#### 2.2.4 LoRA 微调策略

对 ViT encoder 使用 **Low-Rank Adaptation (LoRA)**：
- 仅在 attention 层的 **Q 和 V 投影矩阵** 上添加低秩适配器
- Rank $r = 8$，scaling factor $\alpha = 1$
- 其余 ViT 参数冻结

消融对比（Table 1）：
| 策略 | Cell AUC | Cell F1 |
|---|---|---|
| Frozen encoder | 0.857 | 0.413 |
| LoRA (r=8, α=1) | **0.868** | **0.431** |

LoRA 以极少的额外参数（约 0.1% 的 ViT 参数量）带来了显著提升，说明 **domain-specific adaptation 是必要的**，但全量 fine-tuning 在数据量有限（41 WSIs）时可能过拟合。

### 2.3 预处理流水线

预处理流水线是本文的重要工程贡献（参见 `figures/fig1_preprocessing_pipeline.png`）：

#### Step 1: 配准 (Registration)
使用 **Valis** 工具将 H&E 图像与 mIF 图像进行配准。由于 ORION 数据集的 H&E 和 mIF 来自**同一组织切片**（先做 mIF 再做 H&E），配准质量较高。

#### Step 2: Tile 选择与质量控制
- Otsu 阈值化筛除背景 tile
- 训练一个 **CNN 分类器** 检测配准失败的 tile（约 10% 被排除）
- 最终获得约 400k 训练 tiles

#### Step 3: 自发荧光 (Autofluorescence, AF) 校正
mIF 信号中混有组织自发荧光，必须扣除：

$$I_{\text{cor}} = \max(0, \, I_{\text{IF}} - \lambda \cdot I_{\text{AF}} + b)$$

其中 $I_{\text{AF}}$ 是单独采集的自发荧光通道，$\lambda$ 和 $b$ 是校正参数。

校正后进行 **log-normalization**：

$$I_{\text{norm}} = 255 \cdot \log\left(\frac{\min(I_{\text{cor}}, \, q_{0.999})}{q_{0.999}} + 1\right)$$

$q_{0.999}$ 是 99.9% 分位数，用于截断极端离群值。Log 变换压缩动态范围，使信号分布更适合网络学习。

#### Step 4: 伪标签生成 (Pseudo-labelling)
用于细胞级别评估：
1. **Cellpose** 在 DAPI 通道上做核分割
2. 核边界向外 **2 μm dilation** 作为细胞区域
3. 计算每个细胞在各 marker 通道上的 **平均强度**
4. **GMM (Gaussian Mixture Model)** 聚类区分阳性/阴性
5. **Hierarchical gating**：模拟流式细胞术的门控策略，处理 marker 间的生物学层级关系（如 CD3+ 才能进一步判断 CD4+/CD8+）

---

## 3. 数据

参见 `figures/fig3_dataset_overview.png`。

### 3.1 ORION CRC 数据集（训练 + 验证 + 测试）

| 属性 | 详情 |
|---|---|
| 来源 | 结直肠癌 (CRC) 组织 |
| WSI 数量 | 41 张 |
| 通道 | 18 通道 mIF（15 markers + Hoechst + AF + 空白） + 同一组织 H&E |
| 标记物 | Hoechst, Pan-CK, E-cadherin, CD45, CD3e, CD4, CD8a, CD45RO, CD20, CD68, CD163, FOXP3, PD-L1, SMA, CD31, Ki-67 |
| 划分 | 37 train / 2 val / 2 test |
| Tile 数量 | ~400k（筛选后） |
| 分辨率 | 256×256 @ 0.5 mpp |
| 配准方式 | 同一切片（H&E 和 mIF 在同一组织上，先 mIF 后 H&E） |

**16 个标记物覆盖的生物学类别**：
- **核内容**: Hoechst (DAPI equivalent)
- **上皮**: Pan-CK, E-cadherin
- **免疫 T 细胞**: CD3e, CD4, CD8a, CD45RO
- **免疫 B 细胞**: CD20
- **免疫泛白细胞**: CD45
- **巨噬细胞**: CD68, CD163
- **调节性 T 细胞**: FOXP3
- **免疫检查点**: PD-L1
- **基质**: SMA (α-Smooth Muscle Actin)
- **血管**: CD31
- **增殖**: Ki-67

### 3.2 HEMIT 数据集（仅测试）

| 属性 | 详情 |
|---|---|
| 来源 | 外部公开数据集 |
| Patch 数量 | 5,292 paired patches |
| 通道 | DAPI + CD3 + Pan-CK |
| 分辨率 | 1024×1024 @ 40× |
| 配准方式 | 同一组织切片 |

### 3.3 IMMUcan CRC 数据集（仅测试）

| 属性 | 详情 |
|---|---|
| 来源 | IMMUcan 项目，CRC |
| WSI 数量 | 35 slides |
| 通道 | DAPI + CD3 + CD8 + CD4 + FOXP3 + Pan-CK |
| Tile 数量 | ~17,000 |
| **关键差异** | **连续切片** (consecutive sections)，H&E 和 mIF 不在同一组织上 |

IMMUcan 的连续切片设定使其成为最严格的外部验证——因为不存在像素级对应关系，只能进行 **tile 级别的细胞计数相关性** 分析（Pearson correlation）。

---

## 4. 实验设计与结果

### 4.1 训练细节

| 参数 | 值 |
|---|---|
| Tile 尺寸 | 256×256 @ 0.5 mpp |
| 目标值范围 | $[-0.9, 0.9]$（配合 Tanh） |
| 优化器 | Adam |
| 学习率 | $2 \times 10^{-4}$，训练过半后线性衰减 |
| Warmup | 前 400 iterations 线性 warmup |
| Weight decay | $10^{-5}$ |
| Gradient clipping | max norm = 1 |
| Dropout | 0.1 |
| Batch size | 16 |
| 硬件 | 单卡 NVIDIA A100 |

**数据增强策略**：
- 几何：随机翻转 (flips)
- 像素级：coarse dropout, brightness/contrast 调整, Gaussian blur, Gaussian noise
- **染色增强** (stain augmentation)：模拟 H&E 染色变异
- **CycleGAN 风格迁移**：训练 ORION → IMMUcan 的 CycleGAN，生成 IMMUcan 风格的 H&E 图像作为训练增强，提升跨域泛化能力

### 4.2 评估指标体系

本文提出了 **多层次评估框架**，这是一个重要贡献：

#### 像素级指标
- **PSNR** (Peak Signal-to-Noise Ratio)：衡量重建保真度
- **SSIM** (Structural Similarity Index)：衡量结构相似性

#### 细胞级指标（更具生物学意义）
- **Cell AUC**：对每个细胞核计算其在预测 mIF 上的平均强度，以伪标签为 ground truth 计算 AUC
- **Cell F1**：在验证集上训练一个 **logistic regression 分类器**，将预测的平均荧光强度映射为阳性/阴性判定，在测试集上报告 F1

#### 跨数据集指标（IMMUcan）
- **Pearson Correlation**：每个 tile 内的细胞计数（预测 vs. ground truth）的 Pearson 相关系数——因为连续切片无法做像素/细胞级对齐

### 4.3 整体性能（Table 2）

| 指标 | MIPHEI (ORION训练) | HEMIT (HEMIT训练) | HEMIT* (ORION训练) | HEMIT (ORION训练) | Random |
|---|---|---|---|---|---|
| ORION AUC | **0.876** | - | 0.831 | 0.701 | - |
| ORION F1 | **0.438** | - | 0.360 | 0.253 | 0.140 |
| HEMIT AUC | **0.844** | 0.863 | 0.764 | 0.598 | - |
| HEMIT F1 | **0.701** | 0.663 | 0.471 | 0.481 | 0.333 |
| IMMUcan Pearson | **0.690** | - | 0.667 | 0.422 | - |

**关键发现**：
1. MIPHEI 在 HEMIT 测试集上的 Cell F1 (0.701) **超过了 HEMIT 自身** (0.663)，尽管 MIPHEI 并未在 HEMIT 数据上训练。这说明 Foundation Model + 大规模 ORION 训练数据的组合具有强大的跨域泛化能力。
2. HEMIT* 是将 HEMIT 架构在 ORION 上重新训练的版本，MIPHEI 仍然大幅领先（F1: 0.438 vs 0.360），证明架构优势而非仅仅是数据优势。
3. 直接将 HEMIT 原模型应用于 ORION 数据（域外测试）性能严重下降（AUC: 0.701, F1: 0.253），而 MIPHEI 跨域到 HEMIT 时仍保持较好性能（AUC: 0.844），证明 foundation model 编码器的泛化能力。

### 4.4 逐 Marker 性能分析（Figure 5a, ORION 测试集）

参见 `figures/fig5_evaluation.png`。

| 难度层级 | Marker | Cell F1 | 分析 |
|---|---|---|---|
| **容易** | E-cadherin | 0.903 | 上皮标记物，H&E 中上皮结构极为明显 |
| **容易** | Pan-CK | 0.884 | 同上，角蛋白广泛表达于上皮 |
| **中等** | CD45 | 0.681 | 泛白细胞标记，免疫细胞在 H&E 中可被识别 |
| **中等** | CD3e | 0.572 | T 细胞，形态学上有一定可辨识度 |
| **中等** | SMA | 0.564 | 平滑肌/基质，H&E 中肌纤维母细胞可见 |
| **较难** | CD45RO, CD4, CD8a | 0.229-0.572 | T 细胞亚群，形态学差异微妙 |
| **较难** | CD31 | 0.386 | 血管内皮，小血管不易辨识 |
| **较难** | CD68 | 0.362 | 巨噬细胞 |
| **困难** | CD20 | 0.30 | B 细胞 |
| **困难** | CD163 | 0.206 | M2 巨噬细胞亚型 |
| **极难** | FOXP3 | 0.114 | 调节性 T 细胞，核内转录因子 |
| **几乎不可预测** | PD-L1 | 0.048 | 免疫检查点分子，表达高度异质性 |

**生物学解读**：预测难度与 marker 的 **H&E 形态学可辨识度** 高度相关。上皮标记物（Pan-CK, E-cadherin）在 H&E 中对应清晰的组织结构，F1 > 0.88。免疫细胞亚群（CD4/CD8/FOXP3）形态学差异极小，需要分子水平信息，预测困难。PD-L1 几乎不可预测（F1=0.048），可能因为其表达受微环境信号调控而非细胞形态决定。

### 4.5 IMMUcan 跨数据集验证

| Marker | Pearson Correlation |
|---|---|
| CD4 | 0.80 |
| CD3e | 0.73 |
| CD8 | 0.69 |
| Pan-CK | 0.63 |
| FOXP3 | 0.60 |

在 **连续切片**（非同一组织）的严格条件下，仍然获得了 0.60-0.80 的 Pearson 相关系数。考虑到连续切片本身就存在组织形变和细胞分布差异，这一结果相当有说服力。

参见 `figures/fig4_prediction_pipeline.png` 中的可视化预测结果。

---

## 5. 消融实验

Table 1 提供了系统的消融分析（均在 ORION 测试集上）：

### 5.1 Foundation Model 对比

| 编码器 | 参数量级 | PSNR | SSIM | Cell AUC | Cell F1 |
|---|---|---|---|---|---|
| U-Net-ResNet50 | ~25M | 26.54 | 0.832 | 0.812 | 0.344 |
| U-Net-ConvNeXtv2 Large | ~200M | 27.40 | 0.839 | 0.840 | 0.379 |
| CTransPath (Swin) | ~28M | 26.96 | 0.837 | 0.812 | 0.351 |
| UNI v2 (DINOv2) | ~300M | 27.73 | 0.838 | 0.862 | 0.424 |
| **H-optimus-0 (ViT-G/14)** | **~1.1B** | **27.86** | **0.840** | **0.868** | **0.431** |

**结论**：Foundation model 的规模和预训练数据量与下游性能正相关。H-optimus-0 (ViT-G/14) 全面领先，比传统 ResNet50 U-Net 在 Cell F1 上提升 **+25.3%** (0.344→0.431)。

### 5.2 GAN vs. Generator-only

| 配置 | Cell AUC | Cell F1 |
|---|---|---|
| Generator only | **0.868** | **0.431** |
| Pix2Pix (GAN) | 0.817 | 0.410 |

GAN discriminator **损害了细胞级准确率**。这与直觉相悖——GAN 通常被认为能产生更"真实"的图像。但对于 mIF 预测任务，"视觉真实感"并不等于"生物学准确性"。Discriminator 可能鼓励模型生成看起来像 mIF 的假信号（hallucination），在像素层面可能更"好看"，但在细胞级别引入了假阳性。

### 5.3 微调策略

| 策略 | Cell AUC | Cell F1 |
|---|---|---|
| Frozen encoder | 0.857 | 0.413 |
| **LoRA (r=8, α=1)** | **0.868** | **0.431** |

LoRA 微调在冻结基础上进一步提升了 Cell AUC (+1.1%) 和 Cell F1 (+4.4%)，且计算开销很小。

### 5.4 ViT 集成策略

| 策略 | PSNR | Cell AUC | Cell F1 |
|---|---|---|---|
| UNETR | **27.86** | 0.868 | 0.431 |
| **ViTMatte** | 27.78 | **0.876** | **0.438** |

ViTMatte 在像素级指标（PSNR）上略低，但在 **细胞级指标上全面优于 UNETR**。这再次验证了：像素级和细胞级指标可以矛盾，而细胞级指标对生物学应用更为重要。

---

## 6. Discussion & 局限性

### 6.1 主要贡献总结

1. **Foundation model 的有效集成**：证明了大规模病理学预训练 ViT 在 image translation 任务中的价值，其丰富的特征表示是跨域泛化的基础。
2. **ViTMatte 架构设计**：巧妙解决了 ViT 缺乏多尺度特征的问题，并行 CNN 流 + ViT bottleneck 是一种通用的设计模式。
3. **全面的评估框架**：提出 pixel-level + cell-level + cross-dataset 多层次评估，推动了该领域的评估标准。
4. **实际应用前景**：回顾性队列挖掘 (mining retrospective cohorts)、生物标记物发现 (biomarker discovery)、药物研发中的虚拟染色。

### 6.2 局限性

1. **训练数据规模极小**：仅 41 张 WSI（37 train），这是一个严重瓶颈。虽然通过 foundation model 预训练缓解了部分问题，但更多训练数据几乎必然能带来提升。
2. **细胞分类器的域适应问题**：Cell F1 评估中使用的 logistic regression 分类器在验证集上训练，迁移到新数据集时需要重新标定——这限制了其作为端到端解决方案的实用性。
3. **PD-L1 几乎不可预测**（F1=0.048）：免疫检查点分子的表达可能更多受转录调控而非细胞形态决定，纯形态学方法存在根本性天花板。
4. **评估伪标签的噪声**：GMM + hierarchical gating 生成的伪标签本身有误差，Cell AUC/F1 的上限受限于伪标签质量。
5. **连续切片验证的固有噪声**：IMMUcan 使用连续切片（非同一组织），Pearson correlation 存在系统性偏低，难以区分"模型误差"和"切片间生物学差异"。
6. **单一癌种**：仅在 CRC 上训练和主要验证，对其他癌种（肺癌、乳腺癌等）的泛化性未知。

---

## 7. 个人思考与组会讨论点

### 7.1 方法论层面

1. **ViTMatte vs. UNETR 的选择逻辑**：ViTMatte 本质上承认了 ViT 在低层局部特征提取上不如 CNN，因此用 CNN 补足。这引出一个更深层的问题——如果 CNN 流已经提供了足够好的 skip connections，ViT bottleneck 的真正贡献是什么？是全局上下文（self-attention 的长程依赖），还是预训练带来的丰富语义特征？可以设计实验：用随机初始化的 ViT 做 bottleneck（保留架构但去除预训练知识）来分离这两个因素。

2. **GAN 伤害细胞准确率的发现值得深入探讨**：这是否意味着所有 image translation 任务中 GAN 都不适用于下游定量分析？还是可以通过修改 discriminator（如 patch-level + cell-level dual discriminator）来缓解？

3. **Inverse variance weighting 的学习动态**：$\sigma_j^2$ 的演化过程值得可视化——哪些通道在训练早期就收敛，哪些一直保持高不确定性？这与 marker 的预测难度是否一致？

4. **LoRA rank=8 是否最优？** 文中未报告 rank 的消融。对于 ViT-G/14 这样的超大模型，rank=8 可能过低。rank=16/32 是否能进一步提升？

### 7.2 数据与评估层面

5. **41 张 WSI 的数据效率惊人**——这主要归功于 foundation model 的预训练。但如果有 500+ WSI，性能天花板在哪里？数据量-性能的 scaling curve 是什么样的？

6. **Cell F1 的评估管线本身引入了额外的学习步骤**（logistic regression）。这使得 Cell F1 既取决于 mIF 预测质量，也取决于分类器的适配度，二者耦合在一起难以解耦。更理想的评估方式可能是直接使用 marker positivity threshold（如 GMM 直接应用于预测信号）。

7. **FOXP3 和 PD-L1 的低 F1 值是否真的不可接受？** 对于某些应用（如肿瘤免疫浸润的粗粒度评估），即使单细胞分类 F1 较低，tile/region 级别的统计量可能仍然准确。IMMUcan 的 FOXP3 Pearson=0.60 说明了这一点。

### 7.3 应用前景

8. **临床转化路径**：最直接的应用是对大规模回顾性 H&E 队列进行虚拟 mIF 标注，产生 spatial immune profiling 数据用于生存分析/biomarker 发现。但需要注意——模型的系统性偏差（如倾向于低估稀有免疫细胞亚群）可能导致生物学结论的偏差。

9. **与空间转录组学的关系**：MIPHEI 预测的是蛋白水平的空间分布；如果将同样的思路扩展到 spatial transcriptomics（从 H&E 预测基因表达的空间分布），是否可以复用类似的架构？

10. **Foundation model 的选择是否会随时间变化？** H-optimus-0 目前是最优的，但病理学 FM 更新迅速（如 Virchow, Prov-GigaPath 等）。架构设计应当对编码器的替换保持灵活性。

### 7.4 推荐的讨论问题

- 对于新的癌种（如肺癌），是否需要从头收集配对数据训练，还是 ORION CRC 上训练的模型可以直接迁移？
- 如何定义 mIF 预测质量的"可用性阈值"——Cell F1 达到多少才能用于下游分析？
- 是否可以设计一种 confidence-aware 的预测机制，让模型对不确定的区域输出"不确定"而非噪声预测？

---

## 8. 技术细节速查

### 8.1 架构参数
```
Encoder:        H-optimus-0 (ViT-G/14, ~1.1B params)
Integration:    ViTMatte (parallel CNN + ViT bottleneck)
LoRA:           rank=8, alpha=1, on Q,V projections
Decoder:        Nearest upsample + dual 3×3 conv + BN + ReLU
Output heads:   16 independent heads, Tanh activation
Output range:   [-0.9, 0.9]
```

### 8.2 训练超参数
```
Input:          256×256 tiles @ 0.5 mpp
Optimizer:      Adam, lr=2e-4
LR schedule:    Linear warmup (400 iters) → linear decay (after 50%)
Weight decay:   1e-5
Grad clip:      max_norm=1
Dropout:        0.1
Batch size:     16
Hardware:       1× NVIDIA A100
```

### 8.3 损失函数
$$\mathcal{L}_{\text{wMSE}} = \lambda \sum_{j=1}^{16} \frac{1}{\sigma_j^2} \cdot \frac{1}{N}\sum_{i=1}^{N}(y_{ij} - \hat{y}_{ij})^2$$

### 8.4 自发荧光校正
$$I_{\text{cor}} = \max(0, \, I_{\text{IF}} - \lambda \cdot I_{\text{AF}} + b)$$
$$I_{\text{norm}} = 255 \cdot \log\left(\frac{\min(I_{\text{cor}}, \, q_{0.999})}{q_{0.999}} + 1\right)$$

### 8.5 关键性能数字

| 最佳配置 (ViTMatte + H-optimus-0 + LoRA) | 值 |
|---|---|
| ORION Cell AUC | 0.876 |
| ORION Cell F1 (mean) | 0.438 |
| Pan-CK F1 | 0.884 |
| E-cadherin F1 | 0.903 |
| CD3e F1 | 0.572 |
| HEMIT Cell F1 (跨域) | 0.701 |
| IMMUcan Pearson (连续切片) | 0.690 |

### 8.6 Figure 索引
- `figures/fig1_preprocessing_pipeline.png` — 预处理流水线（配准 → tile 选择 → AF 校正 → 伪标签）
- `figures/fig2_architecture.png` — MIPHEI 架构（ViTMatte 集成策略）
- `figures/fig3_dataset_overview.png` — 三个数据集概览
- `figures/fig4_prediction_pipeline.png` — 预测流水线与可视化结果
- `figures/fig5_evaluation.png` — 逐 Marker 评估分析
