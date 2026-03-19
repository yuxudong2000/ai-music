# RVC Fine-tune PoC 验证计划

<!-- anchor:background -->
## 1. 背景与目标

### 1.1 切换 RVC 的原因

PoC-A 阶段已完成 seed-vc Fine-tune 尝试（exp-07），但遇到严重问题：

| 问题 | 详情 |
|------|------|
| **训练极度缓慢** | seed-vc 模型体积 2.1GB/checkpoint，保存一次触发 MPS 内存压力，步速从 10s 劣化至 530s/step |
| **内存占用过高** | M2 Pro 32GB 在 batch=2 时内存压到 0.08GB Free，出现严重 swap |
| **架构不适合 Apple Silicon** | seed-vc 使用 DiT（扩散 Transformer），MPS 对部分算子支持有限 |

**RVC 的优势**：
- 模型体积小（~60-80MB），训练 checkpoint 不会触发 OOM/swap
- 架构更简单（基于 VITS），对 CPU/MPS 友好
- 社区验证充分，macOS 上 CPU 训练成功案例多
- 训练管线清晰：preprocess → extract f0 → extract feature → train → build index → infer
- 可复用已有的 5 首邓丽君净化人声数据（无需重新处理）

### 1.2 验证目标

| 编号 | 验证目标 | 对应问题 |
|------|---------|---------|
| G-1 | RVC Fine-tune 能否显著提升同性别音色相似度 | P-1（音色相似度不足） |
| G-2 | RVC Fine-tune 能否改善跨性别转换效果 | P-6（跨性别转换失效） |
| G-3 | RVC 在 Apple Silicon（MPS/CPU）上能否完成训练 | 环境兼容性 |
| G-4 | 确定最优训练参数（epoch/batch/f0_method） | 参数调优 |
| G-5 | 评估训练时间成本（期望 < 2 小时） | 用户体验 |

### 1.3 成功标准

- 同性别：Fine-tune 后音色相似度主观评价优于 Zero-shot（exp-05 baseline）
- 跨性别：Fine-tune 后 F0 曲线向男声区间对齐，或配合降调后效果明显改善
- 训练可在 MPS/CPU 上完成，不崩溃
- 产出一套可复用的 RVC 训练流程和推荐参数

---

<!-- anchor:rvc-tech -->
## 2. RVC 技术原理

### 2.1 架构概述

RVC（Retrieval-based Voice Conversion）基于以下关键技术栈：

```
输入音频（源声）
    │
    ▼
[ContentVec / HuBERT]  ← 提取语义内容特征（去除音色信息）
    │
    ▼
[FAISS 检索]  ← 从训练集特征库中检索最相似的目标音色特征
    │
    ▼
[VITS 解码器]  ← 结合 F0（音高）+ 音色特征生成目标声音
    │
    ▼
输出音频（目标音色）
```

**与 seed-vc 的核心区别**：
- seed-vc：扩散模型（DiT），参数量大（2GB），生成质量高但慢
- RVC：基于 VITS + 检索，参数量小（60-80MB），速度快，训练友好

### 2.2 训练流程（5 个阶段）

```
训练数据（.wav）
    │
    ▼
Step 1: preprocess_dataset.py
        ├── 使用 ffmpeg 读取音频（自动支持 mp3/wav/m4a）
        ├── 沉默检测 + 切分（每段 ≤ 4 秒，overlap 0.3s）
        ├── 保存 16kHz 单声道 → logs/{exp}/1_16k_wavs/
        └── 保存 40kHz 单声道 → logs/{exp}/0_gt_wavs/
    │
    ▼
Step 2a: extract_f0_print.py
         └── 提取 F0（音高曲线）→ logs/{exp}/2a_f0/ + 2b-f0nsf/
             F0 方法可选：pm / harvest / crepe / rmvpe（推荐 rmvpe）
    │
    ▼
Step 2b: extract_feature_print.py
         └── HuBERT 提取 256-dim 语义特征 → logs/{exp}/3_feature256/
    │
    ▼
Step 3: train_nsf_sim_cache_sid_load_pretrain.py
        ├── 基于预训练权重（pretrained/f0G40k.pth + f0D40k.pth）微调
        ├── 每隔 save_every_epoch 保存 G_{epoch}.pth / D_{epoch}.pth
        └── 输出：logs/{exp}/G_{epoch}.pth（最终使用 G，不需要 D）
    │
    ▼
Step 4: train_index.py（可选但推荐）
        └── 基于 FAISS 构建检索索引 → logs/{exp}/add_XXX.index
```

### 2.3 推理流程

```
源音频 + 目标音色索引（.index）+ 目标音色模型（G.pth）
    │
    ├── 提取源音频 F0（音高）
    ├── 提取源音频 HuBERT 语义特征
    ├── FAISS 检索目标音色特征
    └── VITS 解码：F0 + 目标特征 → 目标音色音频
```

---

<!-- anchor:tool-selection -->
## 3. 工具选型

### 3.1 方案比较

| 工具 | 类型 | macOS 支持 | 训练方式 | 适合程度 |
|------|------|-----------|---------|---------|
| **RVC-Project/WebUI** | 原版 WebUI | ⚠️ 部分问题（faiss-gpu 不支持） | 图形界面 | 一般 |
| **Applio** | 改进版 WebUI + CLI | ✅ macOS 官方支持 | GUI + CLI | ⭐⭐⭐ |
| **blaisewf/rvc-cli** | 纯 CLI | ✅ | 命令行 | 已归档（2025-07） |
| **IAHispano/Applio** | 最活跃维护 | ✅ macOS run-install.sh | Gradio 界面 + Python API | ⭐⭐⭐⭐ |

### 3.2 选择：Applio（IAHispano/Applio）

**理由**：
1. ✅ 官方支持 macOS（`run-install.sh` 脚本，已在 Apple Silicon 上验证）
2. ✅ 提供 TensorBoard 监控（`run-tensorboard.sh`）
3. ✅ 同时提供 GUI 和 Python API，可以用 CLI 控制训练
4. ✅ 社区活跃（GitHub Stars ~24k），文档完整
5. ✅ 使用 `faiss-cpu` 代替 `faiss-gpu`（Apple Silicon 原生支持）
6. ✅ 模型产物小（~60-80MB），无 checkpoint 内存压力

**仓库**：https://github.com/IAHispano/Applio

### 3.3 关键依赖

```
Python 3.10+
torch >= 2.0（MPS 支持）
faiss-cpu（macOS 用 CPU 版本）
librosa, soundfile, scipy
praat-parselmouth（f0 提取 pm 方法）
pyworld（f0 提取 harvest 方法）
huggingface_hub（下载预训练权重）
```

---

<!-- anchor:data-prep -->
## 4. 数据准备

### 4.1 可复用的现有数据

已有 `exp-07-ft-same-gender-train/training-data/clean-vocals/` 目录下的 5 个净化人声文件：

| 文件 | 时长 | 状态 |
|------|------|------|
| `denglijun-renchangjiu_clean.wav` | ~246s | ✅ 可直接用 |
| `denglijun-tianmimi_clean.wav` | ~211s | ✅ 可直接用 |
| `denglijun-wozhizaihuni_clean.wav` | ~252s | ✅ 可直接用 |
| `denglijun-xiaocheng_clean.wav` | ~154s | ✅ 可直接用 |
| `denglijun-yueliang_clean.wav` | ~209s | ✅ 可直接用 |

> **注意**：RVC 的 preprocess_dataset.py 会自动切分音频（每段 ≤ 4 秒），**无需提前手动切段**。可以直接将完整的净化人声文件作为输入。

**总时长约 22 分钟**，对于 RVC 训练非常充足（推荐 5-30 分钟）。

### 4.2 数据处理说明

RVC 对输入数据的要求：
- 格式：WAV（ffmpeg 支持的其他格式也可，推荐 WAV）
- 采样率：任意（preprocess 会自动重采样到 16kHz 和 40kHz）
- 质量：纯净人声，BGM 越少越好（我们已做了 Demucs + bleedless 二次净化）
- 文件组织：所有 .wav 文件放在同一个目录（不支持子目录）

### 4.3 跨性别实验数据

痛仰乐队（`poc/audio/tongyang/`）：
- 目前只有 `再见杰克.mp3`，经过 Demucs + bleedless 净化
- 需要在 exp-09 实验前，将净化后的文件准备好

---

<!-- anchor:experiment-design -->
## 5. 实验设计

### 5.1 实验矩阵（沿用 exp-07~10 编号体系）

| 实验编号 | 场景 | 核心动作 | 验证目标 |
|---------|------|---------|---------|
| **exp-07** | 同性别 Fine-tune（邓丽君） | RVC 训练，对比 seed-vc | G-1, G-3, G-4 |
| **exp-08** | 同性别 Fine-tune 推理对比 | RVC 模型推理，与 exp-05 Zero-shot 对比 | G-1 |
| **exp-09** | 跨性别 Fine-tune（痛仰） | RVC 训练男声 | G-2, G-4 |
| **exp-10** | 跨性别 Fine-tune 推理对比 | 对比 exp-06 Zero-shot | G-2 |

> **注**：此计划为 RVC 版本，替代原 seed-vc 版本（seed-vc 版本因内存问题中止）。

### 5.2 exp-07：同性别 Fine-tune 训练（邓丽君）

#### 5.2.1 环境安装

```bash
# clone Applio
cd /Users/yuxudong/Documents
git clone https://github.com/IAHispano/Applio.git applio
cd applio

# 安装依赖（macOS 脚本）
bash run-install.sh
# 或使用已有的 conda 环境手动安装
conda activate audio
pip install -r requirements.txt
```

#### 5.2.2 预训练模型下载

Applio 使用的预训练模型（从 HuggingFace 自动下载）：
- `rvc/models/pretraineds/f0G40k.pth`（Generator，~60MB）
- `rvc/models/pretraineds/f0D40k.pth`（Discriminator，~60MB）
- `rvc/models/embedders/`（ContentVec HuBERT 模型）

#### 5.2.3 训练步骤（5 步流水线）

**Step 1：数据预处理**

```bash
cd /Users/yuxudong/Documents/applio
python rvc/train/preprocess/preprocess.py \
    --model_name "denglijun_rvc" \
    --dataset_path "/Users/yuxudong/Documents/ai-music/poc/sound-repalce-experiments/seed-vc-finetune/exp-07-ft-same-gender-train/training-data/clean-vocals" \
    --sample_rate 40000 \
    --cpu_cores 8 \
    --cut_preprocess True \
    --process_effects False \
    --noise_reduction False
```

预期产出：
- `logs/denglijun_rvc/0_gt_wavs/`（40kHz 切段）
- `logs/denglijun_rvc/1_16k_wavs/`（16kHz 切段）

**Step 2a：F0 音高提取**

```bash
python rvc/train/extract/extract_f0_print.py \
    --model_name "denglijun_rvc" \
    --f0_method "rmvpe" \
    --hop_length 128
```

> F0 方法推荐：`rmvpe`（最准确，尤其是歌唱音频）

**Step 2b：HuBERT 特征提取**

```bash
python rvc/train/extract/extract_feature_print.py \
    --model_name "denglijun_rvc" \
    --version "v2" \
    --gpu "0" \
    --embedder_model "contentvec"
```

> 在 macOS 上 gpu 可填 "0"（MPS），特征提取不涉及训练，MPS 兼容性更好

**Step 3：模型训练**

```bash
python rvc/train/train.py \
    --model_name "denglijun_rvc" \
    --save_every_epoch 10 \
    --save_only_latest True \
    --save_every_weights True \
    --total_epoch 200 \
    --sample_rate 40000 \
    --batch_size 4 \
    --gpu "0" \
    --overtraining_detector False \
    --cleanup False \
    --cache_data_in_gpu False \
    --use_warmup True \
    --version "v2"
```

> 关键参数说明：
> - `total_epoch 200`：推荐 100-300 epoch（数据量 22 分钟，200 epoch 约 30-60 分钟）
> - `batch_size 4`：RVC 模型小，batch=4 对 32GB 内存完全无压力
> - `save_only_latest True`：只保存最新 checkpoint，避免磁盘占用

**Step 4：构建检索索引**

```bash
python rvc/train/train.py \
    --index_algorithm "Auto" \
    --model_name "denglijun_rvc"
```

或直接用 `train_index.py`（具体参数在正式安装后确认）

#### 5.2.4 训练监控

```bash
# 启动 TensorBoard
bash run-tensorboard.sh
# 浏览器访问 http://localhost:6006
```

监控指标：
- `loss/d_total`（判别器损失）
- `loss/g_total`（生成器损失）
- `mels`（梅尔频谱对比，最直观反映音质）

#### 5.2.5 推荐训练参数

| 参数 | 推荐值 | 说明 |
|------|--------|------|
| `total_epoch` | 200 | 22 分钟数据，200 epoch 效果稳定 |
| `batch_size` | 4 | M2 Pro 32GB，可用 8（更快） |
| `f0_method` | rmvpe | 歌唱音频最准确 |
| `save_every_epoch` | 10 | 每 10 epoch 保存一次 |
| `version` | v2 | RVC v2（更高质量） |
| `sample_rate` | 40000 | 高保真 |

### 5.3 exp-08：同性别 Fine-tune 推理对比

**目标**：用邓丽君 RVC 模型对王菲《我愿意》人声做转换，与 exp-05（seed-vc Zero-shot）对比。

**推理命令**（Applio Python API）：

```python
# 方式一：通过 Applio WebUI 操作（最简单）
# 方式二：通过 CLI 脚本（精确控制参数）
from rvc.infer.infer import VoiceConverter

vc = VoiceConverter()
vc.convert_audio(
    audio_input_path="path/to/wangfei_vocal.wav",
    audio_output_path="path/to/output.wav",
    model_path="logs/denglijun_rvc/G_200.pth",
    index_path="logs/denglijun_rvc/added_IVF*.index",
    pitch=0,              # 半音偏移，同性别用 0
    filter_radius=3,
    index_rate=0.75,      # 检索权重（0.5-0.75 推荐）
    volume_envelope=0.25,
    protect=0.33,
    f0_method="rmvpe",
    hop_length=128,
)
```

**对比维度**：

| 维度 | exp-05（seed-vc Zero-shot） | exp-08（RVC Fine-tune） |
|------|---------------------------|------------------------|
| 音色相似度 | ⭐⭐⭐+ | 待验证 |
| 旋律保持 | ✅ | 待验证 |
| 音质清晰度 | ✅ | 待验证 |
| 推理速度 | RTF 2.55× | 待验证（预估 RTF <1×） |

### 5.4 exp-09：跨性别 Fine-tune 训练（痛仰）

与 exp-07 流程相同，使用痛仰乐队净化人声作为训练数据。

**推理参数差异**：
- `pitch=-8`（降调 8 个半音，解决女声→男声 F0 偏移问题）
- 可先试 `pitch=0`，观察 F0 是否自动对齐

### 5.5 exp-10：跨性别 Fine-tune 推理对比

对比维度与 exp-08 类似，额外测试不同 pitch 参数下的效果。

---

<!-- anchor:risk -->
## 6. 风险与预案

| 风险 | 可能性 | 影响 | 预案 |
|------|--------|------|------|
| **faiss-cpu 安装失败（Apple Silicon）** | 🟡 中 | 阻塞 index 构建 | 使用 `conda install faiss-cpu` 代替 pip；或跳过 index 步骤（index 只影响推理精度，不影响基础功能） |
| **HuBERT 特征提取 MPS 兼容问题** | 🟡 中 | 阻塞特征提取 | 切换到 CPU 运行：设置 `PYTORCH_ENABLE_MPS_FALLBACK=1` |
| **训练时 loss 不下降（数据量不足）** | 🟢 低 | 效果差 | 检查数据预处理结果（段数/时长），增加 epoch |
| **模型过拟合（纯人声特征过学习）** | 🟡 中 | 音质金属感 | 使用中间 epoch checkpoint（如 epoch 100）对比 |
| **推理时 pitch 对齐问题** | 🟡 中 | 跨性别失效 | 使用 `pitch` 参数手动调整半音；对比不同值 |
| **Applio 版本兼容性** | 🟢 低 | 安装失败 | 固定版本安装；参考 requirements.txt |

---

<!-- anchor:monitoring -->
## 7. 训练监控方案

### 7.1 TensorBoard（推荐）

Applio 原生支持 TensorBoard，提供：
- **梅尔频谱可视化**：训练中的音频样本 vs 真实目标（最直观）
- **Loss 曲线**：G/D loss 趋势，判断是否收敛
- **实时更新**：每个 epoch 完成后刷新

```bash
# 启动 TensorBoard
cd /Users/yuxudong/Documents/applio
bash run-tensorboard.sh
# 访问 http://localhost:6006
```

### 7.2 命令行监控脚本

参考 seed-vc finetune 的 `monitor_train.sh`，创建类似的 `monitor_rvc_train.sh`：

```bash
#!/bin/bash
# 监控 RVC 训练进展
while true; do
    clear
    echo "=== RVC 训练状态 $(date '+%H:%M:%S') ==="
    # 进程状态
    ps aux | grep "train.py" | grep -v grep | awk '{print "CPU:"$3"% RSS:"int($6/1024)"MB"}'
    # 最新日志
    echo "--- 最新日志 ---"
    tail -5 /tmp/rvc_train.log 2>/dev/null
    # Checkpoints
    echo "--- Checkpoints ---"
    ls -lht logs/denglijun_rvc/G_*.pth 2>/dev/null | head -5
    sleep 15
done
```

### 7.3 训练日志重定向

```bash
python rvc/train/train.py [参数] >> /tmp/rvc_train.log 2>&1 &
tail -f /tmp/rvc_train.log
```

---

<!-- anchor:directory -->
## 8. 目录结构

```
poc/sound-repalce-experiments/rvc-finetune/
├── plan.md                     ← 本文件
├── monitor_rvc_train.sh        ← 实时监控脚本（待创建）
├── run_train.sh                ← 训练启动脚本（待创建）
├── infer.py                    ← 推理脚本（待创建）
│
├── exp-07-ft-same-gender-train/
│   ├── README.md
│   ├── training-data/
│   │   └── clean-vocals/       ← 符号链接或引用 seed-vc-finetune 已有数据
│   ├── rvc-logs/               ← Applio logs/denglijun_rvc/ 的产出
│   │   ├── 0_gt_wavs/
│   │   ├── 1_16k_wavs/
│   │   ├── 2a_f0/
│   │   ├── 3_feature256/
│   │   ├── G_200.pth           ← 训练产出（最终模型）
│   │   └── added_*.index       ← FAISS 索引
│   └── config.json             ← 训练参数记录
│
├── exp-08-ft-same-gender-infer/
│   ├── README.md
│   ├── source/                 ← 源音频（王菲人声）
│   └── output/                 ← RVC 转换结果
│
├── exp-09-ft-cross-gender-train/
│   ├── README.md
│   └── training-data/
│       └── clean-vocals/       ← 痛仰净化人声
│
└── exp-10-ft-cross-gender-infer/
    ├── README.md
    ├── source/
    └── output/
```

---

<!-- anchor:execution -->
## 9. 执行步骤

### Phase 0：环境安装与验证（预计 30 分钟）

1. [ ] clone Applio 到 `/Users/yuxudong/Documents/applio`
2. [ ] 运行 `bash run-install.sh` 或手动 `pip install -r requirements.txt`
3. [ ] 验证关键依赖：`faiss-cpu`、`torch`（MPS）、`praat-parselmouth`
4. [ ] 下载预训练权重（f0G40k.pth + f0D40k.pth，~120MB）
5. [ ] **干运行测试**：使用少量数据（1 首歌）跑完 5 步流水线，确认无报错

### Phase 1：同性别 Fine-tune 实验（exp-07/08，预计 1-2 小时）

1. [ ] 准备数据目录（软链接或复制 5 首邓丽君净化人声）
2. [ ] 执行 preprocess（5 步流水线的 step 1）
3. [ ] 执行 extract f0（step 2a）
4. [ ] 执行 extract feature（step 2b）
5. [ ] 启动训练，开启 TensorBoard 监控
6. [ ] 等待训练完成（epoch 200），观察 loss 收敛
7. [ ] 构建 FAISS 索引（step 4）
8. [ ] exp-08：用 Fine-tuned 模型推理，与 exp-05 对比
9. [ ] 记录结论到 README.md

### Phase 2：跨性别 Fine-tune 实验（exp-09/10，预计 1 小时）

1. [ ] 准备痛仰人声（确认 bleedless 净化已完成）
2. [ ] 同 Phase 1 执行训练流水线
3. [ ] exp-10：推理对比，测试不同 pitch 值（-6/-8/-10）
4. [ ] 记录最优 pitch 参数

### Phase 3：总结与决策（预计 30 分钟）

1. [ ] 更新 poc-summary.md 中 P-1/P-6 的状态
2. [ ] 决定后续技术路线（RVC vs seed-vc vs 其他方案）
3. [ ] 如果效果仍不理想，评估 GPT-SoVITS 等其他方案

---

<!-- anchor:output -->
## 10. 预期产出

| 产出 | 路径 |
|------|------|
| 邓丽君 RVC 模型 | `applio/logs/denglijun_rvc/G_200.pth` |
| 邓丽君 FAISS 索引 | `applio/logs/denglijun_rvc/added_*.index` |
| exp-08 推理结果 | `rvc-finetune/exp-08-ft-same-gender-infer/output/` |
| 痛仰 RVC 模型 | `applio/logs/tongyang_rvc/G_200.pth` |
| exp-10 推理结果 | `rvc-finetune/exp-10-ft-cross-gender-infer/output/` |
| 更新的 poc-summary.md | P-1/P-6 状态更新 |

---

## 11. seed-vc vs RVC 关键对比

| 维度 | seed-vc Fine-tune | RVC Fine-tune |
|------|-------------------|---------------|
| 模型大小 | ~2.1GB/checkpoint | ~60-80MB/checkpoint |
| 训练架构 | DiT（扩散 Transformer） | VITS + 检索 |
| macOS 兼容性 | ⚠️ MPS 内存压力严重 | ✅ CPU 友好，faiss-cpu 可用 |
| 预估训练时间 | ~70h（遇到内存问题） | ~30-60 分钟（CPU/MPS）|
| 推理速度 | RTF 2.55× | RTF <1×（更快）|
| 歌声转换质量 | 支持 SVC 模式 | 支持（可调 pitch） |
| 社区成熟度 | 较新 | ⭐⭐⭐⭐⭐ 非常成熟 |
| 音色相似度上限 | 较高（扩散模型）| 中高（检索+解码）|
