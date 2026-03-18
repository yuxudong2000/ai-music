# exp-04：真实歌曲 SVC 模式 cfg=0.7（保留 F0 旋律）

## 验证目标

切换为 SVC 歌唱模式（f0-condition=True），保留原始 F0 旋律轮廓，验证歌唱场景下的效果。  
同时修复 MPS float64 兼容性 Bug。

## Bug 修复（必须在运行前应用）

文件：`/Users/yuxudong/Documents/seed-vc/inference.py`，第 329-330 行：

```python
# 修复前（MPS 上会 crash：Cannot convert a MPS Tensor to float64 dtype）
F0_ori = torch.from_numpy(F0_ori).to(device)[None]
F0_alt = torch.from_numpy(F0_alt).to(device)[None]

# 修复后（加 .float() 强制转为 float32）
F0_ori = torch.from_numpy(F0_ori).float().to(device)[None]
F0_alt = torch.from_numpy(F0_alt).float().to(device)[None]
```

根因：numpy 默认 float64，MPS 不支持 float64 tensor。

## 前置条件

1. 已完成 exp-02 的 Step 1（Demucs 分离 source 和 target，中间文件已存在）
2. 已应用上述 Bug 修复到 seed-vc/inference.py

## 参数配置

| 参数 | 值 |
|------|---|
| source | 王菲 - 匆匆那年（女声，241s） |
| target | 邓丽君 - 我只在乎你（女声，252s） |
| **转换模式** | **SVC（f0-condition=True）** |
| **auto-f0-adjust** | **True** |
| 扩散步数 | 30 |
| cfg-rate | 0.7 |
| 音量处理 | RMS 匹配 |

## 运行步骤

```bash
cd /path/to/ai-music
conda activate ai-music
EXP=poc/sound-repalce-experiments/exp-04-real-svc-cfg07
EXP02=poc/sound-repalce-experiments/exp-02-real-vc-no-vol-fix

# Step 1：seed-vc 声音转换（SVC 模式，保留 F0）
# 使用 exp-02 的 Demucs 分离结果作为输入
HF_ENDPOINT=https://hf-mirror.com python /Users/yuxudong/Documents/seed-vc/inference.py \
  --source $EXP02/intermediate/demucs/source_vocals.wav \
  --target $EXP02/intermediate/demucs/target_vocals.wav \
  --output $EXP/intermediate/seed_vc \
  --diffusion-steps 30 \
  --length-adjust 1.0 \
  --inference-cfg-rate 0.7 \
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

# RMS 匹配
vocals = vocals + (orig_v.dBFS - vocals.dBFS)
n = len(accomp)
vocals = vocals[:n] if len(vocals) > n else vocals + AudioSegment.silent(n - len(vocals))
out = '$EXP/output/compare_cfg07.mp3'
Path(out).parent.mkdir(parents=True, exist_ok=True)
accomp.overlay(vocals).export(out, format='mp3', bitrate='320k')
print('输出:', out)
"
```

> 预期耗时：seed-vc SVC 推理约 25 分钟（241s 源音频，MPS）。

## 文件结构

```
exp-04-real-svc-cfg07/
├── README.md
├── result.md
├── intermediate/
│   └── seed_vc/
│       └── vc_output_svc_cfg07.wav    ← seed-vc SVC 输出（已存档）
└── output/
    ├── final_svc_v1.mp3               ← 最终输出（与 compare_cfg07.mp3 相同）
    └── compare_cfg07.mp3              ← 对比命名版本
```
