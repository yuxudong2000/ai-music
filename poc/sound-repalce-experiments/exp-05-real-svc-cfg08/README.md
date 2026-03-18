# exp-05：真实歌曲 SVC 模式 cfg=0.8（CFG 强度调优）

## 验证目标

在 exp-04（SVC cfg=0.7）基础上，将 inference-cfg-rate 从 0.7 提升到 0.8，  
验证 Classifier-Free Guidance 强度对音色相似度的影响。

## 背景

`inference-cfg-rate` 控制 CFG（Classifier-Free Guidance）强度：
- 值越高 → 对目标音色的约束越强 → 音色更贴近参考，但可能引入人工痕迹
- 推荐范围：0.7 ~ 0.9

## 前置条件

1. 已完成 exp-02 的 Step 1（Demucs 分离 source/target）
2. seed-vc/inference.py 已应用 MPS float64 修复（见 exp-04 README）

## 参数配置

| 参数 | 值（变更项加粗） |
|------|---|
| source | 王菲 - 匆匆那年（女声，241s） |
| target | 邓丽君 - 我只在乎你（女声，252s） |
| 转换模式 | SVC（f0-condition=True） |
| auto-f0-adjust | True |
| 扩散步数 | 30 |
| **cfg-rate** | **0.8**（exp-04 为 0.7） |
| 音量处理 | RMS 匹配 |

## 运行步骤

```bash
cd /path/to/ai-music
conda activate ai-music
EXP=poc/sound-repalce-experiments/exp-05-real-svc-cfg08
EXP02=poc/sound-repalce-experiments/exp-02-real-vc-no-vol-fix

# Step 1：seed-vc 声音转换（SVC 模式，cfg=0.8）
HF_ENDPOINT=https://hf-mirror.com python /Users/yuxudong/Documents/seed-vc/inference.py \
  --source $EXP02/intermediate/demucs/source_vocals.wav \
  --target $EXP02/intermediate/demucs/target_vocals.wav \
  --output $EXP/intermediate/seed_vc \
  --diffusion-steps 30 \
  --length-adjust 1.0 \
  --inference-cfg-rate 0.8 \
  --f0-condition True \
  --auto-f0-adjust True \
  --semi-tone-shift 0 \
  --fp16 True

# Step 2：混合（带 RMS 音量匹配）
python -c "
from pydub import AudioSegment
from pathlib import Path
import glob

vc_file = sorted(glob.glob('$EXP/intermediate/seed_vc/*.wav'))[0]
vocals  = AudioSegment.from_wav(vc_file)
orig_v  = AudioSegment.from_wav('$EXP02/intermediate/demucs/source_vocals.wav')
accomp  = AudioSegment.from_wav('$EXP02/intermediate/demucs/source_no_vocals.wav')

vocals = vocals + (orig_v.dBFS - vocals.dBFS)
n = len(accomp)
vocals = vocals[:n] if len(vocals) > n else vocals + AudioSegment.silent(n - len(vocals))
out = '$EXP/output/compare_cfg08.mp3'
Path(out).parent.mkdir(parents=True, exist_ok=True)
accomp.overlay(vocals).export(out, format='mp3', bitrate='320k')
print('输出:', out)
"
```

> 预期耗时：seed-vc SVC 推理约 10 分钟（241s 源音频，MPS，RTF ≈ 2.55×）。

## 文件结构

```
exp-05-real-svc-cfg08/
├── README.md
├── result.md
├── intermediate/
│   └── seed_vc/
│       └── vc_output_svc_cfg08.wav    ← seed-vc SVC cfg=0.8 输出（已存档）
└── output/
    └── compare_cfg08.mp3              ← 最终输出（当前最优同性别配置）
```
