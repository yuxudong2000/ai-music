#!/bin/zsh
# Fine-tune 训练监控面板
# 用法: zsh poc/sound-repalce-experiments/seed-vc-finetune/monitor_train.sh [run_name]
#
# 在另一个终端窗口运行此脚本，可实时看到：
#   - 进程状态（CPU/内存）
#   - 训练日志最新内容（初始化进度 + loss 曲线）
#   - Checkpoint 保存情况
#
# 配套启动训练的命令：
#   cd /Users/yuxudong/Documents/seed-vc
#   conda run -n ai-music \
#     HF_ENDPOINT=https://hf-mirror.com \
#     python train.py \
#     --config ./configs/presets/config_dit_mel_seed_uvit_whisper_base_f0_44k.yml \
#     --dataset-dir "<segments_dir>" \
#     --run-name ft_denglijun \
#     --batch-size 2 --max-steps 500 --save-every 100 --num-workers 0 \
#     2>&1 | tee /tmp/ft_denglijun.log

RUN_NAME="${1:-ft_denglijun}"
LOG_FILE="/tmp/${RUN_NAME}.log"
RUNS_DIR="/Users/yuxudong/Documents/seed-vc/runs/${RUN_NAME}"

echo "监控目标: run_name=${RUN_NAME}"
echo "日志文件: ${LOG_FILE}"
echo "Checkpoint 目录: ${RUNS_DIR}"
echo "按 Ctrl+C 退出监控（不会终止训练）"
echo ""

# 等待日志文件出现
while [ ! -f "$LOG_FILE" ]; do
  echo "$(date '+%H:%M:%S') 等待训练启动（${LOG_FILE} 不存在）..."
  sleep 3
done

echo "$(date '+%H:%M:%S') 检测到日志文件，开始监控！"
echo ""

INTERVAL=15  # 刷新间隔（秒）

while true; do
  clear
  echo "╔══════════════════════════════════════════════════════════════╗"
  echo "║       seed-vc Fine-tune 监控面板  $(date '+%H:%M:%S')             ║"
  echo "╚══════════════════════════════════════════════════════════════╝"
  echo ""

  # --- 进程状态 ---
  echo "▶ 进程状态"
  PROC=$(ps aux | grep "train.py" | grep -v grep)
  if [ -z "$PROC" ]; then
    echo "  ⚠️  没有找到 train.py 进程（训练可能已结束或尚未启动）"
  else
    echo "$PROC" | awk '{printf "  PID:%-6s  CPU:%-6s  MEM:%-6s  RSS:%sMB\n", $2, $3"%", $4"%", int($6/1024)}'
  fi
  echo ""

  # --- 训练阶段识别 ---
  LAST_INIT=$(grep "\[init" "$LOG_FILE" 2>/dev/null | tail -1)
  LAST_STEP=$(grep "epoch.*step.*loss" "$LOG_FILE" 2>/dev/null | tail -1)
  LAST_SAVE=$(grep "Saving\.\." "$LOG_FILE" 2>/dev/null | tail -1)
  LAST_ERROR=$(grep -i "error\|traceback\|exception" "$LOG_FILE" 2>/dev/null | tail -1)

  echo "▶ 当前阶段"
  if [ -n "$LAST_ERROR" ]; then
    echo "  🔴 发现错误！最后错误行："
    echo "  $LAST_ERROR"
  elif [ -n "$LAST_STEP" ]; then
    echo "  🟢 训练进行中"
    echo "  最新步：$LAST_STEP"
    # 提取 step 数
    STEP=$(echo "$LAST_STEP" | grep -oE 'step [0-9]+' | grep -oE '[0-9]+' | tail -1)
    if [ -n "$STEP" ]; then
      echo "  进度：Step ${STEP}/500 ($(echo "$STEP * 100 / 500" | bc)%)"
    fi
  elif [ -n "$LAST_INIT" ]; then
    echo "  🟡 初始化加载中"
    echo "  最新进度：$LAST_INIT"
  else
    echo "  ⏳ 等待启动..."
  fi
  echo ""

  # --- 日志最新内容 ---
  echo "▶ 训练日志（最新 20 行）"
  tail -20 "$LOG_FILE" 2>/dev/null | sed 's/^/  /'
  echo ""

  # --- Checkpoint 状态 ---
  echo "▶ Checkpoint 文件"
  CKPTS=$(ls -lht "$RUNS_DIR"/*.pth 2>/dev/null)
  if [ -z "$CKPTS" ]; then
    echo "  (暂无 checkpoint，等待 step 100...)"
  else
    echo "$CKPTS" | awk '{printf "  %-50s  %s\n", $9, $5}' | sed "s|${RUNS_DIR}/||"
  fi
  echo ""

  # --- 统计 loss 趋势（最近 5 条）---
  echo "▶ Loss 趋势（最近 5 条）"
  LOSS_LINES=$(grep "epoch.*step.*loss" "$LOG_FILE" 2>/dev/null | tail -5)
  if [ -z "$LOSS_LINES" ]; then
    echo "  (训练未开始)"
  else
    echo "$LOSS_LINES" | sed 's/^/  /'
  fi
  echo ""

  echo "─────────────────────────────────────────────────"
  echo "  刷新间隔: ${INTERVAL}s | 按 Ctrl+C 退出监控"
  sleep "$INTERVAL"
done
