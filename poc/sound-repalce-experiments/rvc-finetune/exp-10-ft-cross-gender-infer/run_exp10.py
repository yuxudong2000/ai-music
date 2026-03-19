"""
exp-10: RVC Fine-tune 推理 — 王菲→痛仰（跨性别，对比 exp-06）
运行方式（exp-09 训练完成后）：

  cd /Users/yuxudong/Documents/applio
  KMP_DUPLICATE_LIB_OK=TRUE PYTORCH_ENABLE_MPS_FALLBACK=1 \
  /Users/yuxudong/miniconda3/envs/rvc/bin/python \
  /Users/yuxudong/Documents/ai-music/poc/sound-repalce-experiments/rvc-finetune/exp-10-ft-cross-gender-infer/run_exp10.py
"""

import os, sys, glob, time
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

# Source: 王菲人声（同 exp-06）
SOURCE_WAV   = f"{EXP_BASE}/exp-02-real-vc-no-vol-fix/intermediate/demucs/source_vocals.wav"
SOURCE_NO_VOC= f"{EXP_BASE}/exp-02-real-vc-no-vol-fix/intermediate/demucs/source_no_vocals.wav"

# RVC 模型（exp-09 训练产物）
MODEL_DIR  = f"{APPLIO_DIR}/logs/tongyang_rvc"
OUTPUT_DIR = f"{EXP_BASE}/rvc-finetune/exp-10-ft-cross-gender-infer/output"
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

# 找最新 checkpoint
pth_files   = sorted(glob.glob(f"{MODEL_DIR}/G_*.pth"))
index_files = sorted(glob.glob(f"{MODEL_DIR}/added_*.index"))

if not pth_files:
    raise FileNotFoundError(f"找不到模型，请先完成 exp-09 训练。路径: {MODEL_DIR}")

PTH_PATH   = pth_files[-1]
INDEX_PATH = index_files[-1] if index_files else ""

log(f"使用模型: {PTH_PATH}")
log(f"使用索引: {INDEX_PATH or '(无 index)'}")

# ─────────────────────────────────────────────────────────────
# 多组 pitch 对比（跨性别核心参数）
# ─────────────────────────────────────────────────────────────
CONFIGS = [
    {"tag": "rvc_pitch0",   "pitch":  0,  "index_rate": 0.75},
    {"tag": "rvc_pitch-4",  "pitch": -4,  "index_rate": 0.75},
    {"tag": "rvc_pitch-8",  "pitch": -8,  "index_rate": 0.75},
    {"tag": "rvc_pitch-12", "pitch": -12, "index_rate": 0.75},
]

for cfg in CONFIGS:
    out_wav = f"{OUTPUT_DIR}/{cfg['tag']}.wav"
    log(f"推理中: {cfg['tag']} (pitch={cfg['pitch']})...")
    t0 = time.time()
    run_infer_script(
        pitch          = cfg["pitch"],
        filter_radius  = 3,
        index_rate     = cfg["index_rate"],
        volume_envelope= 0.25,
        protect        = 0.33,
        hop_length     = 128,
        f0_method      = "rmvpe",
        input_path     = SOURCE_WAV,
        output_path    = out_wav,
        pth_path       = PTH_PATH,
        index_path     = INDEX_PATH,
        split_audio    = False,
        f0_autotune    = False,
        f0_autotune_strength = 1.0,
        clean_audio    = True,
        clean_strength = 0.5,
        export_format  = "WAV",
        embedder_model = "contentvec",
        upscale_audio  = False,
        formant_shifting = False,
        formant_qfrency = 1.0,
        formant_timbre  = 1.0,
        post_process   = False,
        reverb=False, pitch_shift=False, limiter=False, gain=False,
        distortion=False, chorus=False, bitcrush=False, clipping=False,
        compressor=False, delay=False, sliders=None,
        sample_rate    = 44100,
    )
    dt = time.time() - t0
    log(f"完成 {cfg['tag']} ({dt:.1f}s)")

# ─────────────────────────────────────────────────────────────
# 混音
# ─────────────────────────────────────────────────────────────
log("混音：RVC 人声 + 王菲伴奏...")
try:
    from pydub import AudioSegment
    orig_v = AudioSegment.from_wav(SOURCE_WAV)
    accomp = AudioSegment.from_wav(SOURCE_NO_VOC)

    for cfg in CONFIGS:
        rvc_wav = f"{OUTPUT_DIR}/{cfg['tag']}.wav"
        out_mp3 = f"{OUTPUT_DIR}/{cfg['tag']}_mixed.mp3"
        if not Path(rvc_wav).exists():
            continue
        vocals  = AudioSegment.from_wav(rvc_wav)
        vocals  = vocals + (orig_v.dBFS - vocals.dBFS)
        n = len(accomp)
        vocals  = vocals[:n] if len(vocals) > n else vocals + AudioSegment.silent(n - len(vocals))
        accomp.overlay(vocals).export(out_mp3, format="mp3", bitrate="320k")
        log(f"混音完成: {out_mp3}")
except Exception as e:
    log(f"混音失败（可跳过）: {e}")

log("=" * 50)
log("✅ exp-10 推理完成！")
log(f"   输出目录: {OUTPUT_DIR}")
log("   对比 exp-06 基线: poc/sound-repalce-experiments/exp-06-bleedless-cross-gender/output/")
log("   推荐先听 rvc_pitch-8_mixed.mp3（降调 8 个半音）")
