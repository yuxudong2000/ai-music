# Exp-11a vs Exp-11b：歌词替换双轨对比实验计划

> **版本**：v1.0  
> **制定日期**：2026-03-19  
> **目的**：用同一段真实中文歌曲对 ACE-Step（路线C）和 SoulX-Singer（路线D）进行主观质量对比，作为最终技术选型的决策依据  
> **关联文档**：`method-comparison-evaluation.md`

---

## 一、实验设计原则

### 控制变量
- **相同输入**：王菲《从从年年》前 30 秒人声片段（同一个 WAV 文件）
- **相同歌词对**：用同一对「原歌词 → 新歌词」进行替换
- **相同评测标准**：主观 MOS 评分 + 3 项客观指标
- **唯一变量**：所用技术方案（ACE-Step vs SoulX-Singer）

### 字数约束
为控制难度，新歌词字数与原歌词**字数差 ≤ 2 字/句**，避免因字数差异引入干扰变量。

---

## 二、测试素材准备

### 2.1 音频素材（30 秒片段）

```bash
# 从现有音频提取前 30 秒（使用 ffmpeg）
ffmpeg -i poc/audio/wangfei-congcongnanian.mp3 \
  -t 30 -acodec pcm_s16le -ar 44100 \
  poc/lrc-replace-experiments/exp-comparison/test_audio/wangfei_30s.wav
```

> 文件保存至：`poc/lrc-replace-experiments/exp-comparison/test_audio/wangfei_30s.wav`

### 2.2 歌词对准备

需要先确认《从从年年》前 30 秒的实际歌词内容（用 LRC 文件核对时间轴）。  
以下为示意性歌词对，**执行前需根据实际 LRC 替换为真实歌词**：

```
# 前 30 秒通常包含 2~4 句歌词
# 以下为占位示例，执行前需核实

原句1（~0:00~0:07）：从来没有一个人     （7字）
新句1             ：月光洒在石阶上     （7字，字数相同）

原句2（~0:07~0:15）：那样的爱过我       （6字）
新句2             ：带走了旧时光       （6字，字数相同）

原句3（~0:15~0:22）：从来没有一个人     （7字）  ← 可能重复
新句3             ：月光洒在石阶上     （7字）

原句4（~0:22~0:30）：那样温柔           （4字）
新句4             ：轻声诉说           （4字，字数相同）
```

> **动作项**：
> 1. 使用 `poc/audio/wangfei-congcongnanian.lrc`（若存在）核实前 30 秒歌词
> 2. 将歌词对写入 `test_lyrics/lyrics_pair.json`

### 2.3 歌词对文件格式

```json
// poc/lrc-replace-experiments/exp-comparison/test_lyrics/lyrics_pair.json
{
  "song": "王菲-从从年年",
  "clip_duration": "0:00~0:30",
  "char_diff_constraint": "≤2字/句",
  "sentences": [
    {
      "id": 1,
      "start": 0.0,
      "end": 7.0,
      "original": "从来没有一个人",
      "replacement": "月光洒在石阶上"
    },
    {
      "id": 2,
      "start": 7.0,
      "end": 15.0,
      "original": "那样的爱过我",
      "replacement": "带走了旧时光"
    }
  ]
}
```

---

## 三、Exp-11a：ACE-Step 路线（路线C）

### 3.1 环境准备

```bash
# 新建 conda 环境
conda create -n ace_step python=3.10 -y
conda activate ace_step

# 安装 ACE-Step v1.5
git clone https://github.com/ace-step/ACE-Step-1.5.git
cd ACE-Step-1.5
pip install -e .

# 验证安装
python -c "import acestep; print('ACE-Step OK')"
```

### 3.2 macOS 启动配置

```bash
# 必须设置参数（避免 bf16 报错）
PYTORCH_ENABLE_MPS_FALLBACK=1 \
acestep \
  --bf16 false \
  --cpu_offload true \
  --overlapped_decode true \
  --port 7865
```

### 3.3 实验步骤

**步骤 1**：上传 `wangfei_30s.wav`，确认可以正常加载

**步骤 2**：使用 Edit Tab，参数设置如下：

| 参数 | 值 | 说明 |
|------|-----|------|
| `edit_mode` | `only_lyrics` | 只改歌词，保持旋律和音色 |
| `edit_strength` | `0.7` | 中等编辑强度（先用这个值）|
| 目标时间段 | 0~30秒（全段）| 一次性替换所有歌词 |
| 原歌词输入 | 前 30 秒原歌词文本 | 从 LRC 提取 |
| 新歌词输入 | 替换后歌词文本 | 按 `lyrics_pair.json` |

**步骤 3**：若全段一次替换效果不好，改为逐句替换：
```
句1：edit(0~7s, 原句1→新句1)  → 保存中间产物
句2：edit(7~15s, 原句2→新句2)  → 保存中间产物
...
最终拼接
```

**步骤 4**：输出文件保存为：
```
exp-comparison/output/exp11a-acestep-full.wav
exp-comparison/output/exp11a-acestep-s07.wav   # 如测试不同 edit_strength
exp-comparison/output/exp11a-acestep-s09.wav
```

### 3.4 记录项

- [ ] 安装是否成功（macOS MPS 稳定性）
- [ ] 推理时间（30 秒音频的实际耗时）
- [ ] 输出音频主观初听感受
- [ ] 是否有明显失真/噪声/接缝问题

---

## 四、Exp-11b：SoulX-Singer 路线（路线D）

### 4.1 环境准备

```bash
# 新建 conda 环境
conda create -n soulx python=3.10 -y
conda activate soulx

# 安装 SoulX-Singer
git clone https://github.com/Soul-AILab/SoulX-Singer.git
cd SoulX-Singer
pip install -r requirements.txt

# 下载预训练模型（从 HuggingFace）
# 建议使用 hf-mirror.com 加速
HF_ENDPOINT=https://hf-mirror.com python scripts/download_models.py
```

### 4.2 实验步骤

**步骤 1：人声分离**（提取干净人声用于 F0 提取）

```bash
# 使用 Demucs 分离人声（已在 PoC-A 验证过）
conda activate ai-music
python -c "
import demucs.separate
demucs.separate.main([
    '-n', 'htdemucs',
    '--two-stems', 'vocals',
    '-d', 'mps',
    'poc/lrc-replace-experiments/exp-comparison/test_audio/wangfei_30s.wav',
    '-o', 'poc/lrc-replace-experiments/exp-comparison/test_audio/separated/'
])
"
# 输出：separated/htdemucs/wangfei_30s/vocals.wav
```

**步骤 2：F0 旋律曲线提取**

```bash
conda activate soulx
python -c "
import torchcrepe
import torchaudio
import torch

# 加载人声
audio, sr = torchaudio.load('test_audio/separated/htdemucs/wangfei_30s/vocals.wav')
audio = audio.mean(0)  # 转单声道

# 提取 F0（10ms 帧率）
f0, periodicity = torchcrepe.predict(
    audio.unsqueeze(0), sr,
    fmin=50, fmax=1000,
    model='full',
    decoder=torchcrepe.decode.weighted_argmax,
    return_periodicity=True,
    device='mps'  # Apple Silicon MPS
)

# 保存 F0 曲线
torch.save({'f0': f0, 'periodicity': periodicity},
           'test_audio/wangfei_30s_f0.pt')
print(f'F0 shape: {f0.shape}')
"
```

**步骤 3：G2P 音素转换**（将新歌词转为音素序列）

```bash
python -c "
# 使用 pypinyin 转换中文歌词为拼音/音素
from pypinyin import pinyin, Style

new_lyrics = ['月光洒在石阶上', '带走了旧时光']
for line in new_lyrics:
    phones = pinyin(line, style=Style.TONE3)
    print(f'{line}: {phones}')
"
```

**步骤 4：SoulX-Singer SVS 推理**

```bash
python inference.py \
  --config configs/soulx_singer.yaml \
  --audio_path test_audio/wangfei_30s.wav \
  --f0_path test_audio/wangfei_30s_f0.pt \
  --lyrics "月光洒在石阶上 带走了旧时光" \
  --output exp-comparison/output/exp11b-soulx-full.wav \
  --device mps  # 若 MPS 不稳定则改 cpu
```

> **注**：实际命令参数需参考 SoulX-Singer 官方 README，上述为示意

**步骤 5**：输出文件保存为：
```
exp-comparison/output/exp11b-soulx-full.wav
```

### 4.3 记录项

- [ ] 安装是否成功（MPS 是否支持）
- [ ] F0 提取质量（是否有异常点、未检测到 F0 的段落）
- [ ] 推理时间（30 秒音频的实际耗时）
- [ ] 输出音频主观初听感受
- [ ] G2P 音素转换准确性

---

## 五、主观质量评测（双盲对比）

### 5.1 评测方式

**ABX 测试**：同时播放三段音频：
- A：`exp11a-acestep-full.wav`（ACE-Step 输出）
- B：`exp11b-soulx-full.wav`（SoulX-Singer 输出）  
- X：`wangfei_30s.wav`（原曲，作为参考）

对每一项维度，对 A 和 B 分别打分（1~5分，5分最好）。

### 5.2 评测量表

| 维度 | 评分项 | 说明 |
|------|--------|------|
| **旋律保持** | 新歌词演唱的旋律是否与原曲基本一致 | 1=完全不同 / 5=几乎一致 |
| **音色相似度** | 新人声是否像原歌手王菲 | 1=完全不像 / 5=几乎一样 |
| **歌词清晰度** | 新歌词是否能清晰听懂 | 1=完全听不懂 / 5=非常清晰 |
| **自然度** | 演唱是否自然流畅，无明显失真/接缝 | 1=极不自然 / 5=非常自然 |
| **整体满意度** | 综合评价，能否接受作为产品输出 | 1=完全不可接受 / 5=可直接使用 |

### 5.3 评分记录表

```
实验者：___________    评测日期：___________

                    Exp-11a (ACE-Step)    Exp-11b (SoulX-Singer)
旋律保持          ___/5                  ___/5
音色相似度        ___/5                  ___/5
歌词清晰度        ___/5                  ___/5
自然度            ___/5                  ___/5
整体满意度        ___/5                  ___/5
合计              ___/25                 ___/25

主观总结：
ACE-Step 表现：
___________________________________________________

SoulX-Singer 表现：
___________________________________________________

推荐选型：
___________________________________________________
```

### 5.4 客观指标（辅助参考）

| 指标 | 含义 | 计算方式 |
|------|------|---------|
| **F0 RMSE** | 旋律偏差（Hz）| `librosa.yin` 分别提取原曲和输出人声 F0，计算 RMSE |
| **Speaker Cosine** | 音色相似度 | ECAPA-TDNN 提取 speaker embedding，计算余弦相似度 |
| **MCD** | Mel-Cepstral Distortion | 原曲人声 vs 合成人声的 MCD（dB） |

---

## 六、决策标准

| 情况 | 决策 |
|------|------|
| ACE-Step 整体满意度 ≥ 3.5，且 ≥ SoulX-Singer | ✅ 选路线 C（流程更简单）|
| SoulX-Singer 整体满意度 ≥ 3.5，且显著优于 ACE-Step（差距 ≥ 0.5 分）| ✅ 选路线 D |
| 两者差距 < 0.5 分 | ✅ 选路线 C（工程复杂度更低）|
| 两者整体满意度均 < 3 分 | 🔄 启动路线 A（TTS + RVC Fine-tune）|
| ACE-Step 安装失败/macOS 不兼容 | 🔄 直接选路线 D |
| SoulX-Singer 安装失败/macOS 不兼容 | 🔄 直接选路线 C |

---

## 七、产出文件结构

```
poc/lrc-replace-experiments/exp-comparison/
├── README.md                          # 本计划文档
├── test_audio/
│   ├── wangfei_30s.wav               # 测试输入（30秒片段）
│   └── separated/                    # Demucs 分离结果
│       └── htdemucs/wangfei_30s/
│           ├── vocals.wav
│           └── no_vocals.wav
├── test_lyrics/
│   ├── lyrics_pair.json              # 歌词替换对（需核实后填写）
│   └── original_lrc_30s.lrc         # 前 30 秒 LRC 时间轴
├── output/
│   ├── exp11a-acestep-full.wav       # ACE-Step 输出
│   └── exp11b-soulx-full.wav        # SoulX-Singer 输出
├── run_exp11a.py                     # ACE-Step 运行脚本
├── run_exp11b.py                     # SoulX-Singer 运行脚本
└── results.md                        # 评测结果记录（实验后填写）
```

---

## 八、实验顺序建议

```
当前：等待 exp-07（邓丽君 RVC 训练）完成

下一步（并行准备）：
  ├── 准备测试素材（剪 30 秒片段 + 核实歌词对）
  └── 搭建两个 conda 环境（ace_step / soulx）

实验执行顺序（建议依次进行，避免内存冲突）：
  1. exp-11a：ACE-Step 安装 + 推理           （预计半天）
  2. exp-11b：SoulX-Singer 安装 + 推理       （预计 1 天）
  3. 双盲主观评测（ABX）                      （1小时）
  4. 计算客观指标                             （2小时）
  5. 撰写 results.md，做出选型决策            （1小时）
```

---

*实验计划结束 | 执行后在 `results.md` 中记录结论*
