#!/bin/bash
# =============================================================
# RVC Fine-tune 训练启动脚本
# 用法：bash run_train.sh <model_name> [total_epoch] [batch_size]
#
# 示例：
#   bash run_train.sh denglijun_rvc         # 默认 200 epoch, batch=4
#   bash run_train.sh denglijun_rvc 300 8   # 自定义参数
# =============================================================

set -e

MODEL_NAME="${1:-denglijun_rvc}"
TOTAL_EPOCH="${2:-200}"
BATCH_SIZE="${3:-4}"
LOG_FILE="/tmp/rvc_train_${MODEL_NAME}.log"

APPLIO_DIR="/Users/yuxudong/Documents/applio"
DATA_DIR="/Users/yuxudong/Documents/ai-music/poc/sound-repalce-experiments"

if [ "$MODEL_NAME" = "denglijun_rvc" ]; then
    DATASET_PATH="${DATA_DIR}/seed-vc-finetune/exp-07-ft-same-gender-train/training-data/clean-vocals"
elif [ "$MODEL_NAME" = "tongyang_rvc" ]; then
    DATASET_PATH="${DATA_DIR}/rvc-finetune/exp-09-ft-cross-gender-train/training-data/clean-vocals"
else
    echo "未知 model_name: $MODEL_NAME"
    echo "支持: denglijun_rvc, tongyang_rvc"
    exit 1
fi

echo "=== RVC Fine-tune 启动 ==="
echo "模型名: $MODEL_NAME"
echo "数据目录: $DATASET_PATH"
echo "Epochs: $TOTAL_EPOCH"
echo "Batch: $BATCH_SIZE"
echo "日志: $LOG_FILE"
echo "========================="

cd "$APPLIO_DIR"

# 激活 conda 环境
source ~/miniconda3/etc/profile.d/conda.sh || source ~/anaconda3/etc/profile.d/conda.sh
conda activate audio

# Step 1: 数据预处理
echo "[$(date '+%H:%M:%S')] Step 1/4: 数据预处理..." | tee -a "$LOG_FILE"
python rvc/train/preprocess/preprocess.py \
    --model_name "$MODEL_NAME" \
    --dataset_path "$DATASET_PATH" \
    --sample_rate 40000 \
    --cpu_cores 8 \
    --cut_preprocess True \
    --process_effects False \
    --noise_reduction False 2>&1 | tee -a "$LOG_FILE"

# Step 2a: F0 提取
echo "[$(date '+%H:%M:%S')] Step 2/4: F0 音高提取（rmvpe）..." | tee -a "$LOG_FILE"
PYTORCH_ENABLE_MPS_FALLBACK=1 python rvc/train/extract/extract_f0_print.py \
    --model_name "$MODEL_NAME" \
    --f0_method "rmvpe" \
    --hop_length 128 2>&1 | tee -a "$LOG_FILE"

# Step 2b: HuBERT 特征提取
echo "[$(date '+%H:%M:%S')] Step 3/4: HuBERT 特征提取..." | tee -a "$LOG_FILE"
PYTORCH_ENABLE_MPS_FALLBACK=1 python rvc/train/extract/extract_feature_print.py \
    --model_name "$MODEL_NAME" \
    --version "v2" \
    --gpu "0" \
    --embedder_model "contentvec" 2>&1 | tee -a "$LOG_FILE"

# Step 3: 模型训练
echo "[$(date '+%H:%M:%S')] Step 4/4: 模型训练（epoch=${TOTAL_EPOCH}, batch=${BATCH_SIZE}）..." | tee -a "$LOG_FILE"
PYTORCH_ENABLE_MPS_FALLBACK=1 python -u rvc/train/train.py \
    --model_name "$MODEL_NAME" \
    --save_every_epoch 10 \
    --save_only_latest False \
    --save_every_weights True \
    --total_epoch "$TOTAL_EPOCH" \
    --sample_rate 40000 \
    --batch_size "$BATCH_SIZE" \
    --gpu "0" \
    --overtraining_detector False \
    --cleanup False \
    --cache_data_in_gpu False \
    --use_warmup True \
    --version "v2" 2>&1 | tee -a "$LOG_FILE"

echo "[$(date '+%H:%M:%S')] ✅ 训练完成！日志：$LOG_FILE"
echo "Checkpoint: $APPLIO_DIR/logs/$MODEL_NAME/"
