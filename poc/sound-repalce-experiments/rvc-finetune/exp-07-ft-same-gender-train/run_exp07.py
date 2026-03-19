"""
exp-07: RVC Fine-tune 训练脚本 — 邓丽君（同性别）
运行方式：
  cd /Users/yuxudong/Documents/applio
  KMP_DUPLICATE_LIB_OK=TRUE PYTORCH_ENABLE_MPS_FALLBACK=1 \
  conda run -n rvc python /Users/yuxudong/Documents/ai-music/poc/sound-repalce-experiments/rvc-finetune/exp-07-ft-same-gender-train/run_exp07.py
"""

import os
import sys
import time

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
os.environ["PYTORCH_MPS_HIGH_WATERMARK_RATIO"] = "0.0"

# 必须从 applio 目录运行
APPLIO_DIR = "/Users/yuxudong/Documents/applio"
os.chdir(APPLIO_DIR)
sys.path.insert(0, APPLIO_DIR)

from core import (
    run_prerequisites_script,
    run_preprocess_script,
    run_extract_script,
    run_train_script,
    run_index_script,
)

# ─────────────────────────────────────────────
# 配置
# ─────────────────────────────────────────────
MODEL_NAME   = "denglijun_rvc"
DATASET_PATH = "/Users/yuxudong/Documents/ai-music/poc/sound-repalce-experiments/rvc-finetune/exp-07-ft-same-gender-train/training-data/clean-vocals"
SAMPLE_RATE  = 40000
TOTAL_EPOCH  = 200
BATCH_SIZE   = 8    # M2 Pro 32GB，RVC 模型小，batch=8 完全可以
F0_METHOD    = "rmvpe"

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

# ─────────────────────────────────────────────
# Step 0：下载预训练模型（首次运行需要）
# ─────────────────────────────────────────────
log("Step 0/4: 检查并下载预训练模型...")
run_prerequisites_script(
    pretraineds_hifigan=True,   # 下载 f0G40k.pth / f0D40k.pth
    models=True,                # 下载 rmvpe.pt / fcpe.pt / contentvec
    exe=False,                  # macOS 不需要 exe
)
log("Step 0/4: 预训练模型就绪 ✓")

# ─────────────────────────────────────────────
# Step 1：数据预处理
# ─────────────────────────────────────────────
log(f"Step 1/4: 数据预处理 (dataset={DATASET_PATH})...")
result = run_preprocess_script(
    model_name=MODEL_NAME,
    dataset_path=DATASET_PATH,
    sample_rate=SAMPLE_RATE,
    cpu_cores=8,
    cut_preprocess="Automatic",  # 必须是 Skip/Simple/Automatic 三选一
    process_effects=False,
    noise_reduction=False,
    clean_strength=0.7,
    chunk_len=3.0,   # 3 秒一段
    overlap_len=0.3,
    normalization_mode="none",
)
log(f"Step 1/4: {result} ✓")

# ─────────────────────────────────────────────
# Step 2：F0 + HuBERT 特征提取
# ─────────────────────────────────────────────
log(f"Step 2/4: 特征提取 (f0_method={F0_METHOD})...")
result = run_extract_script(
    model_name=MODEL_NAME,
    f0_method=F0_METHOD,
    cpu_cores=8,
    gpu="0",           # extract.py 已 patch：无 CUDA 自动走 MPS
    sample_rate=SAMPLE_RATE,
    embedder_model="contentvec",
    include_mutes=2,
)
log(f"Step 2/4: {result} ✓")

# ─────────────────────────────────────────────
# Step 3：模型训练
# ─────────────────────────────────────────────
log(f"Step 3/4: 开始训练 (epoch={TOTAL_EPOCH}, batch={BATCH_SIZE})...")
result = run_train_script(
    model_name=MODEL_NAME,
    save_every_epoch=20,         # 每 20 epoch 保存一次
    save_only_latest=False,      # 保留所有 checkpoint（方便选最佳）
    save_every_weights=True,
    total_epoch=TOTAL_EPOCH,
    sample_rate=SAMPLE_RATE,
    batch_size=BATCH_SIZE,
    gpu="0",                     # train.py 自动检测 MPS
    overtraining_detector=True,  # 开启过拟合检测
    overtraining_threshold=50,
    pretrained=True,             # 使用预训练权重加速
    cleanup=False,
    index_algorithm="Auto",
    cache_data_in_gpu=False,
    vocoder="HiFi-GAN",
    checkpointing=False,
)
log(f"Step 3/4: {result} ✓")

# ─────────────────────────────────────────────
# Step 4：构建 FAISS 索引
# ─────────────────────────────────────────────
log("Step 4/4: 构建 FAISS 检索索引...")
result = run_index_script(
    model_name=MODEL_NAME,
    index_algorithm="Auto",
)
log(f"Step 4/4: {result} ✓")

log("=" * 50)
log(f"✅ exp-07 训练完成！")
log(f"   模型路径: {APPLIO_DIR}/logs/{MODEL_NAME}/")
log(f"   使用 G_最后epoch.pth 进行推理")
