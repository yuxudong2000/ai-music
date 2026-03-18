# seed-vc Fine-tune PoC 验证计划

<!-- anchor:background -->
## 1. 背景与目标

### 1.1 问题背景

PoC-A（声音替换）已完成 6 轮 Zero-shot 实验（exp-01 ~ exp-06），核心结论：
- **流程跑通**：Demucs 分离 + seed-vc SVC 推理 + pydub 混合 端到端可用
- **P-1 音色相似度不足**（🔴 高）：Zero-shot cfg=0.8 是当前最优，但音色与目标仍有可感知差距
- **P-6 跨性别转换失效**（🔴 高）：女声→男声时 F0 仍处于女声区间，输出偏女声

技术预研文档已规划：seed-vc Fine-tune 是解决 P-1 的核心路径（"最少 1 条语音，100 步即可完成"）。

### 1.2 验证目标

| 编号 | 验证目标 | 对应问题 |
|------|---------|---------|
| G-1 | Fine-tune 能否显著提升同性别音色相似度 | P-1 |
| G-2 | Fine-tune 能否改善跨性别转换效果 | P-6 |
| G-3 | Fine-tune 在 Apple Silicon MPS 上能否正常训练 | 环境兼容 |
| G-4 | 确定最优训练参数（步数/数据量/batch） | 参数调优 |
| G-5 | 评估 Fine-tune 的时间成本是否可接受 | 用户体验 |

### 1.3 成功标准

- 同性别场景：Fine-tune 后的音色相似度主观评价优于 Zero-shot（exp-05 baseline）
- 跨性别场景：Fine-tune 后是否需要配合降调，或 Fine-tune 本身能否对齐音域
- MPS 训练可完成且耗时合理（期望 < 30 分钟）
- 产出一套可复用的 Fine-tune 训练流程和推荐参数

<!-- anchor:data-prep -->
## 2. 数据准备

### 2.1 训练数据来源

Fine-tune 的训练数据 = target 歌手的纯人声音频。seed-vc 要求：
- 格式：WAV（推荐）或其他常见音频格式
- 采样率：会自动重采样到 44100Hz（SVC 模型）
- 质量：**尽可能纯净，无 BGM/噪声**（文档原文："Training data should be as clean as possible, BGM or noise is not desired"）
- 最小数据量：**1 条语音即可**，推荐多条以提升效果

### 2.2 数据准备流程

```
目标歌手歌曲.mp3
  → Demucs htdemucs 分离人声
    → audio-separator bleedless 二次净化（exp-06 已验证有效）
      → 纯净人声.wav（用于训练）
```

### 2.3 具体数据集

用户确认可以补充更多目标歌手的歌曲文件，建议每位歌手准备 2~3 首（共 8~12 分钟人声）：

**邓丽君（同性别实验）**：

| 序号 | 歌曲 | 来源 | 状态 |
|------|------|------|------|
| 1 | 我只在乎你 | 已有（`poc/audio/denglijun-wozhizaihuni.mp3`） | ✅ |
| 2 | 待用户提供 | 建议：《月亮代表我的心》《甜蜜蜜》等 | ⏳ |
| 3 | 待用户提供 | 可选补充 | ⏳ |

**痛仰乐队（跨性别实验）**：

| 序号 | 歌曲 | 来源 | 状态 |
|------|------|------|------|
| 1 | 再见杰克 | 已有（`poc/audio/tongyang.mp3`） | ✅ |
| 2 | 待用户提供 | 建议：《公路之歌》《西湖》等 | ⏳ |
| 3 | 待用户提供 | 可选补充 | ⏳ |

**处理流程（每首歌）**：
```
歌曲.mp3 → Demucs htdemucs 分离 → bleedless 二次净化 → 纯人声.wav → 放入训练目录
```

> 注：seed-vc 训练数据只需放在一个目录中，所有 .wav 文件会被自动加载。更多数据 = 更稳定的音色学习。

<!-- anchor:experiment-design -->
## 3. 实验设计

### 3.1 实验矩阵

共 4 轮实验，编号沿用 exp-07 ~ exp-10：

| 实验编号 | 场景 | 训练配置 | 验证目标 |
|---------|------|---------|---------|
| **exp-07** | 同性别 Fine-tune（邓丽君） | 训练 500 步 | G-1, G-3, G-4 |
| **exp-08** | 同性别 Fine-tune 推理对比 | 用 exp-07 模型推理，对比 exp-05 Zero-shot | G-1 |
| **exp-09** | 跨性别 Fine-tune（痛仰） | 训练 500 步 | G-2, G-4 |
| **exp-10** | 跨性别 Fine-tune 推理对比 | 用 exp-09 模型推理，对比 exp-06 | G-2 |

### 3.2 exp-07：同性别 Fine-tune 训练（邓丽君）

**目标**：用邓丽君纯净人声对 seed-vc SVC 模型进行 Fine-tune。

**训练参数**：

| 参数 | 值 | 说明 |
|------|---|------|
| config | `config_dit_mel_seed_uvit_whisper_base_f0_44k.yml` | SVC 44kHz 歌唱模型 |
| dataset-dir | 邓丽君纯人声目录 | Demucs + bleedless 净化后的 .wav 文件 |
| run-name | `ft_denglijun` | |
| batch-size | 2 | M2 Pro 32GB 内存充裕，可用 batch_size=2 |
| max-steps | 500 | 官方推荐 100~500 步 |
| save-every | 100 | 每 100 步保存一次 checkpoint |
| device | mps | Apple Silicon GPU |

**训练命令**：
```bash
cd /Users/yuxudong/Documents/seed-vc
HF_ENDPOINT=https://hf-mirror.com python train.py \
  --config ./configs/presets/config_dit_mel_seed_uvit_whisper_base_f0_44k.yml \
  --dataset-dir <denglijun_clean_vocals_dir> \
  --run-name ft_denglijun \
  --batch-size 1 \
  --max-steps 500 \
  --save-every 100 \
  --gpu 0
```

**预期产出**：
- `./runs/ft_denglijun/ft_model.pth` — Fine-tuned 模型权重
- `./runs/ft_denglijun/config_dit_mel_seed_uvit_whisper_base_f0_44k.yml` — 对应配置

**关注点**：
- MPS 设备兼容性（`device: cuda` 需要改为 `mps`，或通过 `--gpu` 参数处理）
- 是否需要再次修复 float64 等 MPS 兼容问题
- 训练耗时和内存占用

### 3.3 exp-08：同性别 Fine-tune 推理对比

**目标**：用 Fine-tuned 模型对同一 source（王菲）做推理，与 exp-05（Zero-shot cfg=0.8）对比。

**推理命令**（与 exp-05 只差 `--checkpoint` 和 `--config` 参数）：
```bash
HF_ENDPOINT=https://hf-mirror.com python inference.py \
  --source <王菲人声.wav> \
  --target <邓丽君净化人声.wav> \
  --output <exp-08/intermediate/seed_vc/> \
  --checkpoint ./runs/ft_denglijun/ft_model.pth \
  --config ./runs/ft_denglijun/config_dit_mel_seed_uvit_whisper_base_f0_44k.yml \
  --diffusion-steps 30 \
  --inference-cfg-rate 0.8 \
  --f0-condition True \
  --auto-f0-adjust True \
  --fp16 True
```

**对比维度**：

| 维度 | exp-05（Zero-shot） | exp-08（Fine-tune） |
|------|-------------------|-------------------|
| 音色相似度 | ⭐⭐⭐+ | 待验证 |
| 旋律保持 | ✅ | 待验证 |
| 推理速度 | RTF 2.55× | 待验证 |
| 人工痕迹 | 轻微 | 待验证 |

### 3.4 exp-09：跨性别 Fine-tune 训练（痛仰）

与 exp-07 结构相同，但使用痛仰乐队的人声训练数据（已有 bleedless 净化版本）。

**关注点**：
- Fine-tune 是否能让模型学到男声的 F0 分布，从而改善跨性别转换
- 是否仍需配合 `--semi-tone-shift` 降调

### 3.5 exp-10：跨性别 Fine-tune 推理对比

用 Fine-tuned 痛仰模型推理，与 exp-06（Zero-shot 跨性别）对比。
额外测试：配合 `--semi-tone-shift -8` 降调的效果。

<!-- anchor:risk -->
## 4. 风险与预案

| 风险 | 可能性 | 影响 | 预案 |
|------|--------|------|------|
| MPS 训练不兼容（train.py 硬编码 CUDA） | 🟡 中 | 阻塞 | 检查 train.py 代码，修改 device 逻辑；或改用 CPU 训练（慢但可行） |
| 训练内存不足（M2 Pro 16GB） | 🟡 中 | 阻塞 | 降低 batch_size 到 1，减小 max_len；极端情况用 CPU |
| Fine-tune 后音色提升不明显 | 🟡 中 | 需调整策略 | 增加训练步数到 1000~2000；增加训练数据（多首歌曲）；评估 RVC v2 作为备选 |
| Fine-tune 后出现过拟合（如音色对但音质下降） | 🟡 中 | 需平衡 | 使用中间 checkpoint（如 step 200/300）做推理对比，找到最佳步数 |
| 跨性别 Fine-tune 无效 | 🟡 中 | 需降调方案 | 配合 `--semi-tone-shift -8~-10`；或放弃跨性别 Zero-shot，产品层面引导用户用同性别参考 |

<!-- anchor:execution -->
## 5. 执行步骤

### Phase 1：环境准备（预计 30 分钟）

1. 检查 `train.py` 的 device 处理逻辑，确认 MPS 兼容性
2. 如需修复，记录 patch 位置
3. 准备邓丽君纯净人声训练数据（Demucs + bleedless 流程，数据在 exp-02 已有 Demucs 结果，需补做 bleedless）

### Phase 2：同性别 Fine-tune 实验（exp-07/08，预计 1~2 小时）

1. exp-07：执行 Fine-tune 训练（500 步）
2. 观察训练 loss 曲线
3. exp-08：用 Fine-tuned 模型推理，与 exp-05 对比

### Phase 3：跨性别 Fine-tune 实验（exp-09/10，预计 1~2 小时）

1. exp-09：用痛仰人声训练（500 步）
2. exp-10：推理对比 + 降调实验

### Phase 4：总结与决策（预计 30 分钟）

1. 更新 poc-summary.md 中 P-1/P-6 的状态
2. 确定后续声音学习功能的技术路线
3. 如果 seed-vc Fine-tune 效果不理想，评估是否需要引入 RVC v2

<!-- anchor:output -->
## 6. 预期产出

| 产出 | 路径 |
|------|------|
| exp-07 训练 checkpoint | `seed-vc/runs/ft_denglijun/ft_model.pth` |
| exp-08 推理结果 | `poc/sound-repalce-experiments/seed-vc-finetune/exp-08-ft-same-gender-infer/output/` |
| exp-09 训练 checkpoint | `seed-vc/runs/ft_tongyang/ft_model.pth` |
| exp-10 推理结果 | `poc/sound-repalce-experiments/seed-vc-finetune/exp-10-ft-cross-gender-infer/output/` |
| 更新的 poc-summary.md | P-1/P-6 状态更新 |
| MPS 兼容性 patch | 如有 |
