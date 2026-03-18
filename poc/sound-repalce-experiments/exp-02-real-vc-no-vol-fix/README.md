# exp-02：真实歌曲 VC 模式（音量未修复）

## 验证目标

用真实歌曲验证 VC 模式（普通音色转换，不保留 F0）的效果，暴露实际问题。

## 技术链路

```
wangfei-congcongnanian.mp3（王菲）→ Demucs 分离 → seed-vc VC → pydub 混合 → 输出
denglijun-wozhizaihuni.mp3（邓丽君）→ Demucs 分离 → 提取目标音色
```

## 前置条件

```bash
conda activate ai-music
# seed-vc 仓库需已 clone：
ls /Users/yuxudong/Documents/seed-vc/inference.py
```

## 参数配置

| 参数 | 值 |
|------|---|
| source | 王菲 - 匆匆那年（女声，241s） |
| target | 邓丽君 - 我只在乎你（女声，252s） |
| 转换模式 | VC（f0-condition=False） |
| 扩散步数 | 30 |
| cfg-rate | 0.7 |
| 音量处理 | 无（直接混合）|
| 设备 | MPS |

## 运行步骤

```bash
cd /path/to/ai-music
conda activate ai-music
EXP=poc/sound-repalce-experiments/exp-02-real-vc-no-vol-fix

# Step 1：分离 source 人声/伴奏
python -m demucs \
  --two-stems vocals --device mps -n htdemucs \
  -o $EXP/intermediate/demucs_raw \
  $EXP/input/wangfei-congcongnanian.mp3
# 输出：$EXP/intermediate/demucs_raw/htdemucs/wangfei-congcongnanian/vocals.wav
#        $EXP/intermediate/demucs_raw/htdemucs/wangfei-congcongnanian/no_vocals.wav

# Step 2：分离 target 人声（仅用于音色参考）
python -m demucs \
  --two-stems vocals --device mps -n htdemucs \
  -o $EXP/intermediate/demucs_raw \
  $EXP/input/denglijun-wozhizaihuni.mp3
# 输出：$EXP/intermediate/demucs_raw/htdemucs/denglijun-wozhizaihuni/vocals.wav

# Step 3：seed-vc 声音转换（VC 模式，不保留 F0）
HF_ENDPOINT=https://hf-mirror.com python /Users/yuxudong/Documents/seed-vc/inference.py \
  --source $EXP/intermediate/demucs_raw/htdemucs/wangfei-congcongnanian/vocals.wav \
  --target $EXP/intermediate/demucs_raw/htdemucs/denglijun-wozhizaihuni/vocals.wav \
  --output $EXP/intermediate/seed_vc \
  --diffusion-steps 30 \
  --length-adjust 1.0 \
  --inference-cfg-rate 0.7 \
  --f0-condition False \
  --fp16 True

# Step 4：混合（无音量匹配，直接叠加）
python -c "
from pydub import AudioSegment
from pathlib import Path
import glob

vc_file = sorted(glob.glob('$EXP/intermediate/seed_vc/*.wav'))[0]
vocals  = AudioSegment.from_wav(vc_file)
accomp  = AudioSegment.from_wav('$EXP/intermediate/demucs_raw/htdemucs/wangfei-congcongnanian/no_vocals.wav')
n = len(accomp)
vocals = vocals[:n] if len(vocals) > n else vocals + AudioSegment.silent(n - len(vocals))
out = '$EXP/output/final_voice_replace.mp3'
Path(out).parent.mkdir(parents=True, exist_ok=True)
accomp.overlay(vocals).export(out, format='mp3', bitrate='320k')
print('输出:', out)
"
```

> **预期现象**：人声音量极低（-40 dBFS vs 伴奏 -19 dBFS），几乎听不到。  
> 这是 exp-03 要解决的问题。

## 文件结构

```
exp-02-real-vc-no-vol-fix/
├── README.md
├── result.md
├── input/
│   ├── wangfei-congcongnanian.mp3     ← 王菲 - 匆匆那年
│   └── denglijun-wozhizaihuni.mp3     ← 邓丽君 - 我只在乎你
├── intermediate/
│   ├── demucs/
│   │   ├── source_vocals.wav          ← source 分离人声（已存档）
│   │   ├── source_no_vocals.wav
│   │   ├── target_vocals.wav          ← target 分离人声（已存档）
│   │   └── target_no_vocals.wav
│   └── seed_vc/
│       └── vc_output.wav              ← seed-vc 输出（已存档）
└── output/
    └── final_voice_replace.mp3        ← 最终输出（音量失衡）
```
