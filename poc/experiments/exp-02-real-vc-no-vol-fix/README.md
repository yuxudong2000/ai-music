# exp-02：真实歌曲 VC 模式（音量未修复）

## 验证目标

用真实歌曲验证 VC 模式（普通音色转换，不保留 F0）的效果，暴露实际问题。

## 技术链路

```
source.mp3（王菲）→ Demucs 分离 → seed-vc VC → pydub 混合 → 输出
target.mp3（邓丽君）→ Demucs 分离 → 提取目标音色
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

## 文件结构

```
exp-02-real-vc-no-vol-fix/
├── README.md
├── result.md
├── input/
│   ├── source.mp3            ← 王菲 - 匆匆那年
│   └── target.mp3            ← 邓丽君 - 我只在乎你
├── intermediate/
│   ├── demucs/
│   │   ├── source_vocals.wav
│   │   ├── source_no_vocals.wav
│   │   ├── target_vocals.wav
│   │   └── target_no_vocals.wav
│   └── seed_vc/
│       └── vc_output.wav
└── output/
    └── final_voice_replace.mp3
```
