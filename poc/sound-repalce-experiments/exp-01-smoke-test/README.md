# exp-01：冒烟测试（TTS 合成音频）

## 验证目标

用最简单的 TTS 合成语音快速验证端到端流程是否可以跑通，不引入真实歌曲的复杂性。

## 技术链路

```
TTS 合成源语音 → Demucs 人声分离 → seed-vc VC 转换 → pydub 混合 → 输出
```

## 前置条件

```bash
# 1. 激活环境
conda activate ai-music

# 2. 确认 seed-vc 仓库已 clone 到本机
ls /Users/yuxudong/Documents/seed-vc/inference.py
# 如果不存在：
git clone https://github.com/Plachtaa/seed-vc.git /Users/yuxudong/Documents/seed-vc

# 3. 确认依赖已安装
pip install demucs pydub edge-tts torch torchaudio
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

## 运行步骤

```bash
# 工作目录：ai-music 项目根目录
cd /path/to/ai-music
conda activate ai-music

# Step 0：生成 TTS 测试音频（如 input/ 下已有文件可跳过）
python poc/sound-repalce-experiments/generate_source.py
python poc/sound-repalce-experiments/generate_target.py
# 输出：poc/audio/source_voice.wav、poc/audio/target_reference.wav

# Step 1：Demucs 人声分离
python -m demucs \
  --two-stems vocals \
  --device mps \
  -n htdemucs \
  -o poc/sound-repalce-experiments/exp-01-smoke-test/intermediate/demucs_raw \
  poc/sound-repalce-experiments/exp-01-smoke-test/input/source_voice.wav
# 输出：intermediate/demucs_raw/htdemucs/source_voice/vocals.wav
#        intermediate/demucs_raw/htdemucs/source_voice/no_vocals.wav

# Step 2：seed-vc 声音转换（VC 模式）
HF_ENDPOINT=https://hf-mirror.com python /Users/yuxudong/Documents/seed-vc/inference.py \
  --source poc/sound-repalce-experiments/exp-01-smoke-test/intermediate/demucs_raw/htdemucs/source_voice/vocals.wav \
  --target poc/sound-repalce-experiments/exp-01-smoke-test/input/target_reference.wav \
  --output poc/sound-repalce-experiments/exp-01-smoke-test/intermediate/seed_vc \
  --diffusion-steps 10 \
  --length-adjust 1.0 \
  --inference-cfg-rate 0.7 \
  --f0-condition False \
  --fp16 True
# 注：首次运行会从 HuggingFace 下载模型（~200MB），需要网络或已配置镜像

# Step 3：音频混合（使用 poc_a_voice_replace.py 的混合逻辑，或用 pydub 手动合并）
python poc/sound-repalce-experiments/poc_a_voice_replace.py \
  --source poc/sound-repalce-experiments/exp-01-smoke-test/input/source_voice.wav \
  --target poc/sound-repalce-experiments/exp-01-smoke-test/input/target_reference.wav \
  --output poc/sound-repalce-experiments/exp-01-smoke-test/output/final_poc_a.mp3 \
  --seed-vc-dir /Users/yuxudong/Documents/seed-vc \
  --diffusion-steps 10
```

> `poc_a_voice_replace.py` 封装了上述 Step 1~3，可以一键运行完整流程。

## 文件结构

```
exp-01-smoke-test/
├── README.md                              ← 本文件（验证说明）
├── result.md                              ← 验证结果
├── input/
│   ├── source_voice.wav                   ← TTS 合成的源语音（edge-tts zh-CN-XiaoxiaoNeural）
│   └── target_reference.wav              ← TTS 合成的目标参考语音（edge-tts zh-CN-YunxiNeural）
├── intermediate/
│   ├── demucs/
│   │   ├── source_voice_vocals.wav        ← Demucs 分离出的人声
│   │   └── source_voice_no_vocals.wav     ← Demucs 分离出的伴奏
│   └── seed_vc/
│       └── vc_output.wav                  ← seed-vc 音色转换输出
└── output/
    └── final_poc_a.mp3                    ← 最终混合输出
```
