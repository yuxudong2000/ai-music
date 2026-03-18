# exp-01：冒烟测试（TTS 合成音频）

## 验证目标

用最简单的 TTS 合成语音快速验证端到端流程是否可以跑通，不引入真实歌曲的复杂性。

## 技术链路

```
TTS 合成源语音 → Demucs 人声分离 → seed-vc VC 转换 → pydub 混合 → 输出
```

## 参数配置

| 参数 | 值 |
|------|---|
| 分离模型 | htdemucs |
| 转换模型 | seed-uvit-whisper-small-wavenet |
| 转换模式 | VC（f0-condition=False） |
| 扩散步数 | 10 |
| cfg-rate | 0.7 |
| 设备 | MPS（Apple Silicon） |

## 文件结构

```
exp-01-smoke-test/
├── README.md                         ← 本文件（验证说明）
├── result.md                         ← 验证结果
├── input/
│   ├── source_voice.wav              ← TTS 合成的源语音（edge-tts）
│   └── target_reference.wav         ← TTS 合成的目标参考语音（edge-tts）
├── intermediate/
│   ├── demucs/
│   │   ├── source_voice_vocals.wav  ← Demucs 分离出的人声
│   │   └── source_voice_no_vocals.wav ← Demucs 分离出的伴奏
│   └── seed_vc/
│       └── vc_output.wav            ← seed-vc 音色转换输出
└── output/
    └── final_poc_a.mp3              ← 最终混合输出
```

## 运行脚本

```bash
cd /path/to/ai-music
conda activate ai-music

# 生成测试音频
python poc/generate_source.py
python poc/generate_target.py

# 运行完整流程
python poc/poc_a_voice_replace.py \
  --source poc/experiments/exp-01-smoke-test/input/source_voice.wav \
  --target poc/experiments/exp-01-smoke-test/input/target_reference.wav \
  --output poc/experiments/exp-01-smoke-test/output
```
