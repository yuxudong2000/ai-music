# exp-03：真实歌曲 VC 模式（RMS 音量修复）

## 验证目标

在 exp-02 基础上，修复 seed-vc 输出音量过低的问题，验证 RMS 音量匹配方案。

## 修复内容

`mix_real.py` 新增 `match_rms()` 函数，在混合前将转换人声的 RMS 电平对齐到原始人声。

```python
def match_rms(source, reference):
    diff_db = reference.dBFS - source.dBFS
    return source + diff_db
```

## 参数配置

| 参数 | 值 |
|------|---|
| source | 王菲 - 匆匆那年（女声，241s） |
| target | 邓丽君 - 我只在乎你（女声，252s） |
| 转换模式 | VC（f0-condition=False） |
| 扩散步数 | 30 |
| cfg-rate | 0.7 |
| **音量处理** | **RMS 匹配（新增）** |

## 文件结构

```
exp-03-real-vc-rms-fix/
├── README.md
├── result.md
├── intermediate/
│   └── seed_vc/
│       └── vc_output_cfg07.wav   ← 复用 exp-02 的 seed-vc 输出
└── output/
    └── final_voice_replace_v2.mp3
```

> 注：input/ 与 intermediate/demucs/ 复用 exp-02，不重复存储。
