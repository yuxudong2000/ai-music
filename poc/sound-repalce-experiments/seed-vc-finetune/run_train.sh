#!/bin/zsh
# Fine-tune 训练启动脚本
# 用法: zsh run_train.sh [run_name] [max_steps]
#
# 这个脚本直接在 conda 环境中运行训练，并将所有输出重定向到日志文件。
# 与 monitor_train.sh 配合使用：
#   窗口1: zsh run_train.sh ft_denglijun 500
#   窗口2: zsh monitor_train.sh ft_denglijun

RUN_NAME="${1:-ft_denglijun}"
MAX_STEPS="${2:-500}"
SEGMENTS_DIR="/Users/yuxudong/Documents/ai-music/poc/sound-repalce-experiments/seed-vc-finetune/exp-07-ft-same-gender-train/training-data/clean-vocals/segments"
LOG_FILE="/tmp/${RUN_NAME}.log"

echo "=== seed-vc Fine-tune 训练 ==="
echo "run_name:   ${RUN_NAME}"
echo "max_steps:  ${MAX_STEPS}"
echo "dataset:    ${SEGMENTS_DIR}"
echo "log_file:   ${LOG_FILE}"
echo ""
echo "训练日志将写入: ${LOG_FILE}"
echo "可以用以下命令实时查看:"
echo "  tail -f ${LOG_FILE}"
echo "或运行监控面板:"
echo "  zsh poc/sound-repalce-experiments/seed-vc-finetune/monitor_train.sh ${RUN_NAME}"
echo ""

# 激活 conda 环境并运行训练（直接重定向到文件）
source /Users/yuxudong/miniconda3/etc/profile.d/conda.sh
conda activate ai-music

export HF_ENDPOINT=https://hf-mirror.com

cd /Users/yuxudong/Documents/seed-vc

echo "=== 训练启动 $(date) ===" > "$LOG_FILE"

python train.py \
  --config ./configs/presets/config_dit_mel_seed_uvit_whisper_base_f0_44k.yml \
  --dataset-dir "$SEGMENTS_DIR" \
  --run-name "$RUN_NAME" \
  --batch-size 2 \
  --max-steps "$MAX_STEPS" \
  --save-every 100 \
  --num-workers 0 \
  2>&1 | tee -a "$LOG_FILE"

echo ""
echo "=== 训练结束 $(date) ==="
