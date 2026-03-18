# exp-06：bleedless 二次净化 + 跨性别转换

## 验证目标

同时验证两件事：

1. **参考音频二次净化**：使用 `audio-separator` 的 `mel_band_roformer_kim_ft2_bleedless_unwa` 模型对 Demucs 分离后的人声做二次净化，去除伴奏残留，提升 Speaker Embedding 纯净度。
2. **跨性别转换**：使用男声（痛仰乐队）作为 target，女声（王菲）作为 source，验证 seed-vc 的跨性别转换能力。

## 技术链路

```
tongyang.mp3（痛仰，男声）
  └─[Demucs htdemucs]──► tongyang_vocals_raw.wav（一次分离，含伴奏泄漏）
       └─[audio-separator bleedless 870MB]──► tongyang_vocals_cleaned.wav（二次净化）
                                                       │
                              作为 target 参考音色      │
source.mp3（王菲，女声）                                ▼
  └─[Demucs]──► source_vocals.wav ──[seed-vc SVC, cfg=0.8]──► vc_output.wav
                                                                     │
                source_no_vocals.wav（伴奏）──[混合 + RMS]──► compare_tongyang_clean_cfg08.mp3
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

## 文件结构

```
exp-06-bleedless-cross-gender/
├── README.md
├── result.md
├── input/
│   ├── source.mp3                    ← 王菲 - 匆匆那年（女声）
│   └── target_tongyang.mp3           ← 痛仰乐队 - 再见杰克（男声）
├── intermediate/
│   ├── demucs/
│   │   ├── source_vocals.wav         ← source 分离人声
│   │   ├── source_no_vocals.wav      ← source 伴奏
│   │   └── tongyang_vocals_raw.wav   ← tongyang 一次分离（含泄漏）
│   ├── bleedless/
│   │   └── tongyang_vocals_cleaned.wav  ← 二次净化结果（目标音色）
│   └── seed_vc/
│       └── vc_output.wav             ← 转换结果
└── output/
    └── compare_tongyang_clean_cfg08.mp3  ← 最终输出
```

## 注意

此实验跨性别场景（女→男）由于 seed-vc SVC 保留原始 F0 轮廓，输出听感仍偏女声。  
如需解决：加 `--semi-tone-shift -8~-10` 降调，或改用同性别 source/target 对。
