# exp-03：真实歌曲 VC 模式（RMS 音量修复）

## 验证目标

在 exp-02 基础上，修复 seed-vc 输出音量过低的问题，验证 RMS 音量匹配方案。

## 修复内容

`mix_real.py` 新增 `match_rms()` 函数，在混合前将转换人声的 RMS 电平对齐到原始人声：

```python
def match_rms(source, reference):
    diff_db = reference.dBFS - source.dBFS
    return source + diff_db
```

## 前置条件

已完成 exp-02 的 Step 1~3（intermediate/ 下的文件已存在），或重新执行 exp-02 的 Step 1~3。

## 参数配置

| 参数 | 值 |
|------|---|
| source | 王菲 - 匆匆那年（女声，241s） |
| target | 邓丽君 - 我只在乎你（女声，252s） |
| 转换模式 | VC（f0-condition=False） |
| 扩散步数 | 30 |
| cfg-rate | 0.7 |
| **音量处理** | **RMS 匹配（本实验新增）** |

## 运行步骤

```bash
cd /path/to/ai-music
conda activate ai-music
EXP=poc/sound-repalce-experiments/exp-03-real-vc-rms-fix
EXP02=poc/sound-repalce-experiments/exp-02-real-vc-no-vol-fix

# Step 1~3 复用 exp-02 的结果（seed-vc 输出文件）
# 如果没有 exp-02 的中间文件，先跑 exp-02 的 Step 1~3

# Step 4：混合（带 RMS 音量匹配）
python -c "
from pydub import AudioSegment
from pathlib import Path

def match_rms(src, ref):
    return src + (ref.dBFS - src.dBFS)

# 使用 exp-02 的 seed-vc 输出
vocals = AudioSegment.from_wav('$EXP02/intermediate/seed_vc/vc_output.wav')
orig_v = AudioSegment.from_wav('$EXP02/intermediate/demucs/source_vocals.wav')
accomp = AudioSegment.from_wav('$EXP02/intermediate/demucs/source_no_vocals.wav')

print(f'转换人声: {vocals.dBFS:.1f} dBFS')
print(f'原始人声: {orig_v.dBFS:.1f} dBFS')
vocals = match_rms(vocals, orig_v)
print(f'补偿后人声: {vocals.dBFS:.1f} dBFS')

n = len(accomp)
vocals = vocals[:n] if len(vocals) > n else vocals + AudioSegment.silent(n - len(vocals))
out = '$EXP/output/final_voice_replace_v2.mp3'
Path(out).parent.mkdir(parents=True, exist_ok=True)
accomp.overlay(vocals).export(out, format='mp3', bitrate='320k')
print('输出:', out)
"
```

> 也可以直接使用 `mix_real.py`（修改脚本内的路径后运行）。

## 文件结构

```
exp-03-real-vc-rms-fix/
├── README.md
├── result.md
├── intermediate/
│   └── seed_vc/
│       └── vc_output_cfg07.wav    ← 复用 exp-02 的 seed-vc 输出（已存档）
└── output/
    └── final_voice_replace_v2.mp3 ← 最终输出（音量已修复）
```

> 注：input/ 与 intermediate/demucs/ 复用 exp-02，不重复存储。
