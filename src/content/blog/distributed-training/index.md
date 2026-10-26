---
title: 分布式训练基础与显存优化
description: 从显存占用估算出发，梳理 DDP、ZeRO、FSDP 等分布式训练算法，以及梯度累积与梯度裁剪等实用技巧。
publishDate: '2026-10-26'
tags:
- distributed training
- memory optimization
- deep learning
heroImage:
  src: ./image.png
  alt: 分布式训练基础与显存优化
draft: false
language: Chinese
comment: true
ai: human
---

## 基础知识

### 模型训练显存占用计算

估算公式：训练峰值显存 ≈ 模型状态（参数 + 梯度 + 优化器状态） + 激活值 + 临时工作区与内存碎片

激活值与批次大小、序列长度（训练数据输入）相关，临时工作区和碎片和底层有关，这两部分是动态的。

对于不同优化器，可估算的模型状态显存占用估算表如下：

| 优化器类型 | 参数 (Parameters) | 梯度 (Gradients) | 优化器状态 (Optimizer States) | 总显存占用 | 说明 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **SGD** | $4N$ (FP32) | $4N$ (FP32) | $0$ | **$8N$** | 无额外维护状态，最省显存。 |
| **SGD with Momentum** | $4N$ (FP32) | $4N$ (FP32) | $4N$ (FP32) | **$12N$** | 额外维护 1 个动量缓存。 |
| **Adam / AdamW** | $4N$ (FP32) | $4N$ (FP32) | $8N$ (FP32) | **$16N$** | 额外维护一阶矩(m)和二阶矩(v)。 |
| **混合精度Adam** *(如 AMP)* | $2N$ (FP16) | $2N$ (FP16) | $8N$ (FP32) | **$12N$** (或 $16N$)* | 参数和梯度用半精度，优化器状态保持全精度。 |

> *实际的混合精度训练，为了防止梯度下溢并保证参数更新精度，通常会隐式维护一份 FP32 的“主权重副本”（$4N$）
>
> 为什么要分fp32和fp16两个权重？以A100为例，fp32算力 大约 19.5 TFLOPS，bf16 算力 312 TFLOPS，混合精度计算速度大幅提升，同时显存带宽占用也减小。


## 分布式训练算法

分布式训练算法有数据并行、模型并行、混合并行，下面从常用的数据并行来介绍

### DDP（Distributed Data Parallel）

每张卡有完整的模型副本，把数据拆分到多张卡上，每张卡用自己的数据算梯度；更新参数之前进行梯度同步（All-Reduce），把所有卡上的梯度取平均，然后把平均值写回每一张卡。并没有省模型状态的显存


### ZeRO（Zero Redundancy Optimizer）

由DeepSpeed提出，ZeRO有1~3 三个stage，其核心思想是在反向传播的时候参数更新是独立的，这个时候可以将参数/梯度/优化器状态平均切分，每张卡上只负责自己那部分参数，前向时需要同步参数。

#### ZeRO-1：切分优化器状态

ZeRO-1 将优化器状态按照DP rank 切分，每个 rank 只保存并更新 $1/N$ 的优化器状态。但参数和梯度仍然保持完整副本。以Adam为例，参数为$N$的模型在$M$张卡上分布式训练，显存占用为 $4N + 4N + 8N/M = 8N + 8N/M$

#### ZeRO-2：再切分梯度

在 ZeRO-1 基础上，梯度也按相同方式切分。原本 DDP 使用的 all-reduce 被替换为 reduce-scatter（梯度只拿卡上自己负责的那部分），每个 rank 只保留与自己负责的优化器状态所对应的那部分梯度。通信量并不增加，但每卡梯度显存降到 $4N + 4N/M + 8N/M = 4N + 12N/M$。

#### ZeRO-3：再切分参数

ZeRO-3 进一步将模型参数本身切分到各 rank，每个 rank 只常驻 $1/N$ 的参数。前向和反向传播中，每当需要某一层的完整参数时，通过 all-gather（每张卡参数同步） 临时物化，计算完成后立即释放。反向传播中，参数 all-gather、梯度计算、梯度 reduce-scatter、参数释放依次进行。每卡显存降到$2N$

### FSDP（Fully Sharded Data Parallel）

概念上与 ZeRO-3 等价：同时切分优化器状态、梯度和参数，需要时 all-gather，用完即释放。但 FSDP 是 PyTorch 原生实现。

## 相关知识

### 梯度累计（Gradient Accumulation）

模型在训练时大 batch 梯度估计更稳定，训练更平滑，能更好利用并行硬件，但是 batch 太大显存会爆。梯度累积是一种在显存有限时模拟大 batch size 训练的技巧，用 `K` 个小 batch 的梯度平均，近似一次大 batch 的梯度更新。

> batch 变大降低了梯度估计方差，使更大步长更稳定；同时为了补偿每 epoch 更新次数减少，经验上可以放大学习率。经验上SGD算法随batch size近似线性缩放，Adam/自适应优化器随平方根缩放

使用 DDP 时，每次 `backward()` 默认会触发梯度 all-reduce。如果累积 `K` 步，前 `K-1` 步其实不需要同步梯度，可以省通信。

PyTorch 提供 `no_sync()`：

```python
for step, batch in enumerate(dataloader):
    is_last = (step + 1) % accum_steps == 0

    if not is_last:
        with model.no_sync():
            loss = model(batch) / accum_steps
            loss.backward()
    else:
        loss = model(batch) / accum_steps
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()
```

### 梯度裁剪

梯度裁剪是一种防止梯度过大导致训练不稳定的技术。它在反向传播算出梯度之后、优化器更新参数之前，对梯度做一个限制：如果梯度太大，就把它按比例缩小或截断到某个范围。

有按范数裁剪和按值裁剪两种，前者更常用。

按照范数裁剪保持梯度方向不变，只改变长度，PyTorch 对应 `torch.nn.utils.clip_grad_norm_`，它返回裁剪前的总范数，可以用来监控：

```python
total_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
```

#### 和梯度累计一起使用

梯度累积多次 `backward()` 后才 `step()`。梯度裁剪应该只在真正更新前做一次，对累积后的最终梯度裁剪：

#### 和DDP一起使用

分布式训练配合梯度累积的 `no_sync()` 时，前 `K-1` 个 micro-batch 不同步、也不裁剪，最后一次同步后再裁剪

#### max_norm 经验值

1.0 通用，基于 batch size 的经验公式是：`max_norm = sqrt(batch_size) / 10`；此外可以通过函数返回裁剪前的梯度范数进行监控。





