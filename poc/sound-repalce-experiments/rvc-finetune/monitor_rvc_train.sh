#!/bin/bash
# =============================================================
# RVC 训练实时监控面板
# 用法：bash monitor_rvc_train.sh [model_name]
# =============================================================

MODEL_NAME="${1:-denglijun_rvc}"
LOG_FILE="/tmp/rvc_train_${MODEL_NAME}.log"
APPLIO_DIR="/Users/yuxudong/Documents/applio"

while true; do
    clear
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║  RVC 训练监控  · 模型: $MODEL_NAME  · $(date '+%H:%M:%S')    ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo ""

    # 进程状态
    echo "【进程状态】"
    PROC=$(ps aux | grep "train.py" | grep -v grep)
    if [ -n "$PROC" ]; then
        echo "$PROC" | awk '{printf "  PID: %s  CPU: %s%%  RSS: %dMB  运行时长: %s\n", $2, $3, int($6/1024), $10}'
    else
        echo "  ⚠️  未检测到 train.py 进程"
    fi
    echo ""

    # 最新训练日志
    echo "【训练日志（最新 8 行）】"
    if [ -f "$LOG_FILE" ]; then
        tail -8 "$LOG_FILE" | sed 's/^/  /'
    else
        echo "  (日志文件不存在: $LOG_FILE)"
    fi
    echo ""

    # Checkpoints
    echo "【Checkpoints】"
    CKPT_DIR="$APPLIO_DIR/logs/$MODEL_NAME"
    if [ -d "$CKPT_DIR" ]; then
        ls -lht "$CKPT_DIR"/G_*.pth 2>/dev/null | head -5 | awk '{printf "  %s  %s\n", $5, $9}' || echo "  (暂无 checkpoint)"
        echo ""
        echo "  目录结构："
        ls "$CKPT_DIR/" 2>/dev/null | head -10 | sed 's/^/  /'
    else
        echo "  (目录不存在: $CKPT_DIR)"
    fi
    echo ""

    # 内存状态
    echo "【内存状态】"
    vm_stat | awk '/Pages free/{f=$3} /Pages inactive/{i=$3} /Pages wired/{w=$3} /Pages active/{a=$3} END{
        page=16384
        printf "  Free: %.1fGB  Active+Wired: %.1fGB  Avail: %.1fGB\n",
        f*page/1073741824, (a+w)*page/1073741824, (f+i)*page/1073741824
    }'
    echo ""
    echo "  (15 秒后刷新，Ctrl+C 退出)"
    sleep 15
done
