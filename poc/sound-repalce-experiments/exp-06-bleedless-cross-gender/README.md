# exp-06：bleedless 二次净化 + 跨性别转换

## 验证目标

同时验证两件事：

1. **参考音频二次净化**：使用 `audio-separator` 的 `mel_band_roformer_kim_ft2_bleedless_unwa` 模型对 Demucs 分离后的人声做二次净化，去除伴奏残留，提升 Speaker Embedding 纯净度。
2. **跨性别转换**：使用男声（痛仰乐队）作为 target，女声（王菲）作为 source，验证 seed-vc 的跨性别转换能力。

## 技术链路

```
target_tongyang.mp3（痛仰，男声）
  └─[Demucs htdemucs]──► tongyang_vocals_raw.wav（一次分离，含伴奏泄漏）
       └─[audio-separator bleedless 870MB]──► tongyang_vocals_cleaned.wav（二次净化）
                                                       │
                              作为 target 参考音色      │
wangfei-congcongnanian.mp3（王菲，女声）               ▼
  └─[Demucs]──► source_vocals.wav ──[seed-vc SVC, cfg=0.8]──► vc_output.wav
                                                                     │
                source_no_vocals.wav（伴奏）──[混合 + RMS]──► compare_tongyang_clean_cfg08.mp3
```

## 前置条件

```bash
conda activate ai-music

# 确认 audio-separator 已安装
pip install audio-separator[cpu]

# 下载 bleedless 模型（870MB，首次运行会自动下载，或手动触发）
python -c "
from audio_separator.separator import Separator
s = Separator(model_file_dir='/tmp/audio-separator-models/')
s.load_model('mel_band_roformer_kim_ft2_bleedless_unwa.ckpt')
print('模型就绪')
"
# 注：下载约 870MB，网络较慢时需等待 10~20 分钟

# seed-vc MPS float64 修复（见 exp-04 README）已应用
```

## 参数配置

| 参数 | 值 |
|------|---|
| source | 王菲 - 匆匆那年（**女声**，241s） |
| target | 痛仰乐队 - 再见杰克（**男声**，274s）|
| **性别关系** | **跨性别（女→男）** |
| 二次净化模型 | mel_band_roformer_kim_ft2_bleedless_unwa（870MB） |
| 转换模式 | SVC（f0-condition=True） |
| auto-f0-adjust | True |
| semi-tone-shift | 0（未降调） |
| 扩散步数 | 30 |
| cfg-rate | 0.8 |

## 运行步骤

```bash
cd /path/to/ai-music
conda activate ai-music
EXP=poc/sound-repalce-experiments/exp-06-bleedless-cross-gender

# Step 1：Demucs 分离 source（王菲）
python -m demucs \
  --two-stems vocals --device mps -n htdemucs \
  -o $EXP/intermediate/demucs_raw \
  $EXP/input/wangfei-congcongnanian.mp3

# Step 2：Demucs 分离 target（痛仰）
python -m demucs \
  --two-stems vocals --device mps -n htdemucs \
  -o $EXP/intermediate/demucs_raw \
  $EXP/input/target_tongyang.mp3

# Step 3：audio-separator 二次净化痛仰人声（去除伴奏泄漏）
audio-separator \
  $EXP/intermediate/demucs_raw/htdemucs/target_tongyang/vocals.wav \
  --model_filename "mel_band_roformer_kim_ft2_bleedless_unwa.ckpt" \
  --model_file_dir /tmp/audio-separator-models \
  --output_dir $EXP/intermediate/bleedless \
  --output_format WAV \
  --single_stem Vocals
# 输出：$EXP/intermediate/bleedless/vocals_(vocals)_mel_band_roformer_kim_ft2_bleedless_unwa.wav
# 耗时：约 1.5 分钟（274s 音频，MPS，RTF ≈ 2.8×）

# Step 4：seed-vc 声音转换（用净化后的痛仰人声作为 target）
HF_ENDPOINT=https://hf-mirror.com python /Users/yuxudong/Documents/seed-vc/inference.py \
  --source $EXP/intermediate/demucs_raw/htdemucs/wangfei-congcongnanian/vocals.wav \
  --target $EXP/intermediate/bleedless/vocals_\(vocals\)_mel_band_roformer_kim_ft2_bleedless_unwa.wav \
  --output $EXP/intermediate/seed_vc \
  --diffusion-steps 30 \
  --length-adjust 1.0 \
  --inference-cfg-rate 0.8 \
  --f0-condition True \
  --auto-f0-adjust True \
  --semi-tone-shift 0 \
  --fp16 True
# 耗时：约 37 分钟（241s 源音频，MPS，RTF ≈ 9.2×，因 target 较长 F0 提取慢）

# Step 5：混合（带 RMS 音量匹配）
python -c "
from pydub import AudioSegment
from pathlib import Path
import glob

vc_file  = sorted(glob.glob('$EXP/intermediate/seed_vc/*.wav'))[0]
vocals   = AudioSegment.from_wav(vc_file)
orig_v   = AudioSegment.from_wav('$EXP/intermediate/demucs_raw/htdemucs/wangfei-congcongnanian/vocals.wav')
accomp   = AudioSegment.from_wav('$EXP/intermediate/demucs_raw/htdemucs/wangfei-congcongnanian/no_vocals.wav')

vocals = vocals + (orig_v.dBFS - vocals.dBFS)
n = len(accomp)
vocals = vocals[:n] if len(vocals) > n else vocals + AudioSegment.silent(n - len(vocals))
out = '$EXP/output/compare_tongyang_clean_cfg08.mp3'
Path(out).parent.mkdir(parents=True, exist_ok=True)
accomp.overlay(vocals).export(out, format='mp3', bitrate='320k')
print('输出:', out)
"
```

## 文件结构

```
exp-06-bleedless-cross-gender/
├── README.md
├── result.md
├── input/
│   ├── wangfei-congcongnanian.mp3             ← 王菲 - 匆匆那年（女声，source）
│   └── target_tongyang.mp3                    ← 痛仰乐队 - 再见杰克（男声，target）
├── intermediate/
│   ├── demucs/
│   │   ├── source_vocals.wav                  ← 王菲人声（已存档）
│   │   ├── source_no_vocals.wav               ← 王菲伴奏（已存档）
│   │   └── tongyang_vocals_raw.wav            ← 痛仰一次分离人声（已存档，含泄漏）
│   ├── bleedless/
│   │   └── tongyang_vocals_cleaned.wav        ← bleedless 二次净化结果（已存档）
│   └── seed_vc/
│       └── vc_output.wav                      ← 转换结果（已存档）
└── output/
    └── compare_tongyang_clean_cfg08.mp3        ← 最终输出
```

## 注意

此实验跨性别场景（女→男）由于 seed-vc SVC 保留原始 F0 轮廓，输出听感仍偏女声。

解决方案：
- **方案 A**：加 `--semi-tone-shift -8~-10` 降调（快速验证）
- **方案 B**：换用同性别 source/target 对
- **方案 C**：seed-vc 或 RVC fine-tune 模式（长期）
