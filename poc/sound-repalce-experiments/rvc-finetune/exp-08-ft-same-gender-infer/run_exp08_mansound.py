"""
exp-08: RVC Fine-tune 推理 — 痛仰→邓丽君（不同性别）
运行方式（exp-07 训练完成后）：

  cd /Users/yuxudong/Documents/applio
  KMP_DUPLICATE_LIB_OK=TRUE PYTORCH_ENABLE_MPS_FALLBACK=1 \
  /Users/yuxudong/miniconda3/envs/rvc/bin/python \
  /Users/yuxudong/Documents/ai-music/poc/sound-repalce-experiments/rvc-finetune/exp-08-ft-same-gender-infer/run_exp08_mansound.py
"""

import os, sys, glob, time, shutil
from pathlib import Path

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
os.environ["PYTORCH_MPS_HIGH_WATERMARK_RATIO"] = "0.0"

APPLIO_DIR = "/Users/yuxudong/Documents/applio"
os.chdir(APPLIO_DIR)
sys.path.insert(0, APPLIO_DIR)

from core import run_infer_script

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

# ─────────────────────────────────────────────────────────────
# 路径配置
# ─────────────────────────────────────────────────────────────
EXP_BASE = "/Users/yuxudong/Documents/ai-music/poc/sound-repalce-experiments"

# Source: 王菲人声（exp-02 里的分离结果）
SOURCE_WAV = f"/Users/yuxudong/Documents/ai-music/poc/audio/tongyang/tongyang-2/source_vocals.wav"
SOURCE_NO_VOC = f"/Users/yuxudong/Documents/ai-music/poc/audio/tongyang/tongyang-2/source_no_vocals.wav"

# RVC 模型（exp-07 训练产物）
MODEL_DIR = f"{APPLIO_DIR}/logs/denglijun_rvc"
OUTPUT_DIR = f"{EXP_BASE}/rvc-finetune/exp-08-ft-same-gender-infer/output-man"
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────────────────────
# 找推理模型文件（导出格式，包含 config 字段）
# 注意：G_*.pth 是训练原始 checkpoint，不能直接用于推理
#       推理需要 Applio 导出的 {model_name}_*e_*s*.pth 文件
# ─────────────────────────────────────────────────────────────
MODEL_NAME = "denglijun_rvc"

# 优先找 best_epoch 版本
best_files = sorted(glob.glob(f"{MODEL_DIR}/{MODEL_NAME}_*best_epoch.pth"))
all_export = sorted(glob.glob(f"{MODEL_DIR}/{MODEL_NAME}_*.pth"))
index_files = sorted(glob.glob(f"{MODEL_DIR}/added_*.index"))

if best_files:
    PTH_PATH = best_files[-1]   # best epoch 优先
elif all_export:
    PTH_PATH = all_export[-1]   # 取最新导出
else:
    raise FileNotFoundError(
        f"找不到推理模型文件（{MODEL_NAME}_*.pth），请先完成 exp-07 训练。\n"
        f"路径: {MODEL_DIR}\n"
        f"提示：G_*.pth 是训练 checkpoint，不能直接用于推理。"
    )

INDEX_PATH = index_files[-1] if index_files else ""

log(f"使用模型: {PTH_PATH}")
log(f"使用索引: {INDEX_PATH or '(无 index，跳过检索)'}")
log(f"Source:   {SOURCE_WAV}")

# ─────────────────────────────────────────────────────────────
# 多组参数对比推理（pitch=0，index_rate 分别 0.5 / 0.75）
# ─────────────────────────────────────────────────────────────
CONFIGS = [
    {"tag": "rvc_idx050", "index_rate": 0.50, "pitch": 0},
    {"tag": "rvc_idx075", "index_rate": 0.75, "pitch": 0},
]

for cfg in CONFIGS:
    out_wav = f"{OUTPUT_DIR}/{cfg['tag']}.wav"
    log(f"推理中: {cfg['tag']} (index_rate={cfg['index_rate']}, pitch={cfg['pitch']})...")
    t0 = time.time()
    run_infer_script(
        pitch                    = cfg["pitch"],
        index_rate               = cfg["index_rate"],
        volume_envelope          = 0.25,
        protect                  = 0.33,
        f0_method                = "rmvpe",
        input_path               = SOURCE_WAV,
        output_path              = out_wav,
        pth_path                 = PTH_PATH,
        index_path               = INDEX_PATH,
        split_audio              = False,
        f0_autotune              = False,
        f0_autotune_strength     = 1.0,
        proposed_pitch           = False,
        proposed_pitch_threshold = 155.0,
        clean_audio              = True,
        clean_strength           = 0.5,
        export_format            = "WAV",
        embedder_model           = "contentvec",
        formant_shifting         = False,
        formant_qfrency          = 1.0,
        formant_timbre           = 1.0,
        post_process             = False,
        reverb                   = False,
        pitch_shift              = False,
        limiter                  = False,
        gain                     = False,
        distortion               = False,
        chorus                   = False,
        bitcrush                 = False,
        clipping                 = False,
        compressor               = False,
        delay                    = False,
    )
    dt = time.time() - t0
    log(f"完成 {cfg['tag']} → {out_wav}  ({dt:.1f}s)")

# ─────────────────────────────────────────────────────────────
# 混音：RVC 人声 + 王菲伴奏（RMS 对齐）
# ─────────────────────────────────────────────────────────────
log("混音：RVC 人声 + 王菲伴奏...")
try:
    from pydub import AudioSegment
    orig_v = AudioSegment.from_wav(SOURCE_WAV)
    accomp = AudioSegment.from_wav(SOURCE_NO_VOC)

    for cfg in CONFIGS:
        rvc_wav = f"{OUTPUT_DIR}/{cfg['tag']}.wav"
        out_mp3 = f"{OUTPUT_DIR}/{cfg['tag']}_mixed.mp3"
        vocals  = AudioSegment.from_wav(rvc_wav)
        # RMS 音量对齐
        vocals  = vocals + (orig_v.dBFS - vocals.dBFS)
        n = len(accomp)
        vocals  = vocals[:n] if len(vocals) > n else vocals + AudioSegment.silent(n - len(vocals))
        accomp.overlay(vocals).export(out_mp3, format="mp3", bitrate="320k")
        log(f"混音完成: {out_mp3}")
except Exception as e:
    log(f"混音失败（可跳过）: {e}")

log("=" * 50)
log("✅ exp-08 推理完成！")
log(f"   输出目录: {OUTPUT_DIR}")
log("   对比 exp-05 基线: poc/sound-repalce-experiments/exp-05-real-svc-cfg08/output/compare_cfg08.mp3")
