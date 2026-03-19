# ACE-Step PoC-B 验证计划

> **版本**：v1.0  
> **制定日期**：2026-03-19  
> **关联文档**：`ace-step-tech-research.md`（本计划基于该调研报告制定）  
> **验证目标**：评估 ACE-Step 的 Lyric Editing 功能是否满足「功能五：歌词替换与合成」的技术要求

---

## 一、验证目标与成功标准

### 1.1 核心验证目标

| 编号 | 验证目标 | 对应调研风险 |
|------|---------|------------|
| **G-1** | ACE-Step 能否在 M2 Pro 本地正常运行 | R-6（环境兼容性）|
| **G-2** | Lyric Editing 对真实中文歌曲的旋律保持度是否可接受 | R-1（真实录音效果）|
| **G-3** | 中文歌词替换时的声调保持质量（新歌词声调与旋律 F0 的兼容性）| R-2（中文声调）|
| **G-4** | 不同字数差异（±0/±3/±6字）对音质的影响 | R-3（字数差异）|
| **G-5** | 原歌手音色的保持程度 | R-4（音色保持）|
| **G-6** | 全曲逐句编辑拼接后的整体连贯性 | R-5（接缝问题）|

### 1.2 成功标准

| 标准 | 定义 | 最低通过线 |
|------|------|----------|
| **S-1 旋律保持** | 新歌词演唱的 F0 曲线与原曲 F0 曲线的余弦相似度 | ≥ 0.80 |
| **S-2 音色保持** | 新旧人声的 Speaker Embedding 余弦相似度（ECAPA-TDNN）| ≥ 0.75 |
| **S-3 音质** | 无明显失真、噪声、接缝突变 | 主观评分 ≥ 3/5 |
| **S-4 歌词清晰度** | 新歌词可听辨识 | 主观评分 ≥ 3.5/5 |
| **S-5 运行速度** | RTF ≤ 3.0×（4分钟歌曲处理时间 ≤ 12分钟）| RTF ≤ 3.0× |
| **S-6 环境稳定** | 整个流程无崩溃、无 OOM | 零崩溃 |

---

## 二、测试数据准备

### 2.1 测试音频（复用现有资产）

| 文件 | 用途 | 来源 |
|------|------|------|
| `poc/audio/wangfei-congcongnanian.mp3` | 主测试曲目（女声，中文，4:01）| 已有 |
| `poc/audio/source_voice.wav` | TTS 冒烟测试参考 | 已有 |
| 邓丽君净化人声片段（任选 1 首）| Fine-tune 后音色对比 | exp-07 数据 |

### 2.2 测试歌词对

为「从从年年」准备 3 组歌词替换对：

**替换对 A（字数完全相同）**
```
# 原句（选「从从年年」第一段前 4 句）
从来没有一个人   → 今夜月光好皎洁
那样的爱过我     → 照在青石小路上
...
```

**替换对 B（字数差 ±2~3 字）**
```
从来没有一个人（7字）→ 月光轻洒窗台（6字，差-1）
那样的爱过我（6字）  → 带走了所有的思念（8字，差+2）
```

**替换对 C（字数差 ±5~6 字）**
```
# 测试极限情况，预期可能失败
```

> 注：具体歌词请根据「从从年年」LRC 文件的实际内容制定，确保时间戳精确。

---

## 三、实验设计

### 3.1 Phase 1：环境准备（预计半天）

#### exp-11：ACE-Step 安装与冒烟测试

**目标**：验证 ACE-Step 能否在 M2 Pro macOS 上正常运行。

| 步骤 | 操作 |
|------|------|
| 1 | 创建 `ace_step` conda 环境（Python 3.10）|
| 2 | Clone ACE-Step v1.5 仓库 |
| 3 | 安装依赖（`pip install -e .`）|
| 4 | 以 `--bf16 false` 启动 Gradio 界面 |
| 5 | 上传一段 30 秒音频，修改 1 句歌词 |

**通过标准**：
- 无崩溃，正常输出修改后音频
- 推理时间 < 60 秒（30 秒音频）

**预期的 macOS 问题点**：
- `--bf16 false` 必须设置（官方已知问题）
- 可能需要 `PYTORCH_ENABLE_MPS_FALLBACK=1`（某些算子不支持 MPS）
- 若 MPS 不稳定，退回到 CPU 运行（速度会慢 3-5×）

**关键命令**：
```bash
conda create -n ace_step python=3.10 -y
conda activate ace_step
git clone https://github.com/ace-step/ACE-Step-1.5.git
cd ACE-Step-1.5
pip install -e .

# 启动（macOS 必须关闭 bf16）
PYTORCH_ENABLE_MPS_FALLBACK=1 \
acestep --bf16 false --cpu_offload true --overlapped_decode true --port 7865
```

---

### 3.2 Phase 2：核心功能验证（预计 1~2 天）

#### exp-12：Lyric Editing 单句质量验证

**目标**：验证 G-2、G-3、G-4、G-5。

**测试矩阵**：

| 实验编号 | 测试音频 | 歌词对 | 替换句数 | edit_strength | 预期测试点 |
|---------|---------|--------|---------|--------------|-----------|
| exp-12-A | 从从年年（前20s）| A（字数相同）| 1 句 | 0.5 | 基线效果 |
| exp-12-B | 从从年年（前20s）| A（字数相同）| 1 句 | 0.7 | 更强编辑 |
| exp-12-C | 从从年年（前20s）| A（字数相同）| 1 句 | 0.9 | 最强编辑 |
| exp-12-D | 从从年年（前20s）| B（字数差±2）| 1 句 | 0.7 | 字数差异 |
| exp-12-E | 从从年年（前20s）| C（字数差±5）| 1 句 | 0.7 | 极限字数 |

**评测指标**：
```
每组输出收集：
- F0 曲线对比图（原曲 vs 修改后）
- 主观评分（旋律相似/音色保持/歌词清晰/音质）
- 运行时间
```

**产出文件结构**：
```
exp-12-lyric-edit-single/
├── README.md          # 实验说明和结论
├── run_exp12.py       # 自动化运行脚本
├── test_audio/        # 测试输入
│   └── wangfei_clip_20s.wav
├── output/
│   ├── exp12-A-s05.wav
│   ├── exp12-B-s07.wav
│   ├── exp12-C-s09.wav
│   ├── exp12-D-char-diff2.wav
│   └── exp12-E-char-diff5.wav
└── results.md         # 评测结果记录
```

---

#### exp-13：全曲逐句替换流程验证

**目标**：验证 G-6（接缝问题）和端到端完整流程。

**流程设计**：

```python
# 全曲逐句替换概念流程
import lrc_parser
from acestep import edit_lyrics

# 1. 解析 LRC 文件
lrc = lrc_parser.parse("wangfei.lrc")
new_lyrics_map = load_new_lyrics("new_lyrics.txt")  # 新旧歌词对应关系

# 2. 逐句替换（串行，每次使用上一句的输出作为下一句的输入）
current_audio = "wangfei.mp3"
for sentence in lrc.sentences:
    current_audio = edit_lyrics(
        audio=current_audio,
        start_time=sentence.start,
        end_time=sentence.end,
        old_lyric=sentence.text,
        new_lyric=new_lyrics_map[sentence.text],
        edit_mode="only_lyrics",
        edit_strength=0.7,
    )

# 3. 最终输出
save(current_audio, "output_full.mp3")
```

**测试范围**：
- 选「从从年年」前 1 分钟（约 5~6 句）
- 只替换歌词句，间奏段保持不变

**产出文件结构**：
```
exp-13-full-song-flow/
├── README.md
├── run_exp13.py       # 全曲流程脚本
├── test_audio/
│   ├── wangfei_1min.wav
│   └── wangfei_1min.lrc   # 对应片段的 LRC
├── test_lyrics/
│   ├── original.txt   # 原歌词（从 LRC 提取）
│   └── new_lyrics.txt # 替换用新歌词
├── output/
│   └── exp13-full-1min.mp3
└── results.md
```

---

### 3.3 Phase 3：性能 Benchmark（1 天）

#### exp-14：M2 Pro 性能基准测试

| 测试项 | 参数 | 测量指标 |
|--------|------|---------|
| 推理速度（27 steps）| 1 分钟音频 | 实际耗时，RTF 计算 |
| 推理速度（27 steps）| 4 分钟音频 | 实际耗时，RTF 计算 |
| 内存占用 | 标准模式 | 峰值内存（Activity Monitor）|
| 内存占用 | cpu_offload 模式 | 峰值内存 |
| 首次加载时间 | 冷启动 | 模型加载时间 |

**目标**：确认 RTF ≤ 3.0×，为产品化阶段的性能规划提供依据。

---

## 四、降级预案

若 ACE-Step 验证失败，按以下顺序启动备选方案：

### 4.1 降级路线 A：TTS + RVC 修正版

适用场景：ACE-Step 中文效果不达标（Q2/Q3 未通过）

```
edge-tts(新歌词) → 说话音频
    ↓ [音节级 F0 映射]（按 LRC 时间戳对齐原 F0 到新 TTS）
    ↓ [RVC 推理 + Fine-tune 模型]（复用 exp-07 训练成果）
    ↓ [pyrubberband 微调时长]
    ↓ mix with 伴奏
```

**触发条件**：exp-12 结果主观评分 < 3/5

### 4.2 降级路线 B：DiffSinger SVS（长期备选）

适用场景：对质量要求极高，愿意接受更复杂的流程

**触发条件**：路线 A 和 C 都不达标时启动独立 PoC

---

## 五、实验顺序与时间安排

```
[当前]  exp-07 训练完成（等待）
           ↓
[下一步] exp-08（同性别推理对比）
           ↓
         exp-09（痛仰跨性别训练）
           ↓
         exp-10（跨性别推理对比）
           ↓
[PoC-B]  exp-11（ACE-Step 安装冒烟）    ← 半天
           ↓
         exp-12（单句质量验证）          ← 1 天
           ↓
         exp-13（全曲流程）              ← 1 天
           ↓
         exp-14（性能 Benchmark）        ← 0.5 天
           ↓
         PoC-B 总结与技术选型决策
```

**总预计时间**：PoC-B 共约 3~4 天（在 exp-07~10 完成后）

---

## 六、决策标准

验证完成后，根据以下标准做出最终技术选型决策：

| 场景 | 决策 |
|------|------|
| G-2~G-6 全部通过 | ✅ 采用 ACE-Step 路线 C 作为主方案 |
| G-2、G-6 通过，G-3/G-4 有限制 | ⚠️ 采用路线 C + 字数约束（提示用户字数需匹配）|
| G-2 未通过（真实录音效果差）| 🔄 启动降级路线 A（TTS + RVC）|
| 所有路线均未通过 | 🔄 启动降级路线 B（DiffSinger）+ 延期评估 |

---

## 七、产出物规划

| 产出物 | 说明 | 路径 |
|--------|------|------|
| 实验目录 | exp-11~14 完整脚本和结果 | `poc/sound-repalce-experiments/ace-step-research/exp-11~14/` |
| PoC-B 总结 | 验证结论、选型决策、遗留问题 | `poc/sound-repalce-experiments/ace-step-research/poc-b-summary.md` |
| 技术预研文档更新 | 更新 M-4b 候选方案为路线 C 首选 | `docs/tech-research.md`（版本升级到 v0.4）|

---

*验证计划结束*  
*基于文档：`ace-step-tech-research.md` v1.0*
