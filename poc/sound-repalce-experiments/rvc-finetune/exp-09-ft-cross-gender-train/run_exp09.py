"""
exp-09: RVC Fine-tune 训练 — 痛仰（跨性别）
运行方式：

  cd /Users/yuxudong/Documents/applio
  KMP_DUPLICATE_LIB_OK=TRUE PYTORCH_ENABLE_MPS_FALLBACK=1 PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0 \
  /Users/yuxudong/miniconda3/envs/rvc/bin/python \
  /Users/yuxudong/Documents/ai-music/poc/sound-repalce-experiments/rvc-finetune/exp-09-ft-cross-gender-train/run_exp09.py
"""

import os, sys, time, glob
from pathlib import Path

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
os.environ["PYTORCH_MPS_HIGH_WATERMARK_RATIO"] = "0.0"

APPLIO_DIR = "/Users/yuxudong/Documents/applio"
os.chdir(APPLIO_DIR)
sys.path.insert(0, APPLIO_DIR)

from core import run_preprocess_script, run_extract_script, run_train_script, run_index_script

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

# ─────────────────────────────────────────────
# 配置
# ─────────────────────────────────────────────
MODEL_NAME   = "douwei_rvc"
# 痛仰净化人声目录（exp-07 训练数据里的 bleedless 结果，或手动放置）
DATASET_PATH = "/Users/yuxudong/Documents/ai-music/poc/sound-repalce-experiments/rvc-finetune/exp-09-ft-cross-gender-train/training-data/clean-vocals_dereverb"
SAMPLE_RATE  = 40000
TOTAL_EPOCH  = 200
BATCH_SIZE   = 8
F0_METHOD    = "rmvpe"

# 检查数据目录
wav_files = glob.glob(f"{DATASET_PATH}/*.wav")
if not wav_files:
    log(f"⚠️  数据目录为空！请先把痛仰净化人声放到：{DATASET_PATH}")
    log("    可从 seed-vc-finetune 里复制：")
    log("    cp /Users/yuxudong/Documents/ai-music/poc/sound-repalce-experiments/seed-vc-finetune/exp-09-ft-cross-gender-train/training-data/clean-vocals/*.wav " + DATASET_PATH + "/")
    sys.exit(1)

log(f"发现 {len(wav_files)} 个训练音频")

# ─────────────────────────────────────────────
# Step 1：数据预处理
# ─────────────────────────────────────────────
log(f"Step 1/4: 数据预处理...")
result = run_preprocess_script(
    model_name=MODEL_NAME,
    dataset_path=DATASET_PATH,
    sample_rate=SAMPLE_RATE,
    cpu_cores=8,
    cut_preprocess="Automatic",  # 必须是 Skip/Simple/Automatic 三选一
    process_effects=False,
    noise_reduction=False,
    clean_strength=0.7,
    chunk_len=3.0,
    overlap_len=0.3,
    normalization_mode="none",
)
log(f"Step 1/4: {result} ✓")

# ─────────────────────────────────────────────
# Step 2：特征提取
# ─────────────────────────────────────────────
log(f"Step 2/4: 特征提取...")
result = run_extract_script(
    model_name=MODEL_NAME,
    f0_method=F0_METHOD,
    cpu_cores=8,
    gpu="0",          # extract.py 已 patch：无 CUDA 自动走 MPS
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
    save_every_epoch=20,
    save_only_latest=False,
    save_every_weights=True,
    total_epoch=TOTAL_EPOCH,
    sample_rate=SAMPLE_RATE,
    batch_size=BATCH_SIZE,
    gpu="0",                     # train.py 自动检测 MPS
    overtraining_detector=True,
    overtraining_threshold=50,
    pretrained=True,
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
result = run_index_script(model_name=MODEL_NAME, index_algorithm="Auto")
log(f"Step 4/4: {result} ✓")

log("=" * 50)
log(f"✅ exp-09 训练完成！")
log(f"   模型路径: {APPLIO_DIR}/logs/{MODEL_NAME}/")
