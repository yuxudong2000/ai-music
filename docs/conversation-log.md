# AI Music 项目 - 对话记录

> **项目仓库**：https://github.com/yuxudong2000/ai-music.git  
> **开始时间**：2026-03-16  
> **记录说明**：按时间顺序记录关键决策、需求变更、技术选型讨论等重要对话内容

---

## 2026-03-16

### 会话一：技术预研选型文档创建

**背景**：需求文档（v0.7）已完成，用户认为之前的技术方案步子太大，决定重新从技术预研选型开始。

**用户需求**：「步子太大了，我们重新从技术方案预研选型开始，最终生成一个技术预研选型文档。在需求里面有四个核心的能力，每项核心能力如何实现？涉及到的核心技术和技术决策点是什么」

**产出**：创建 `docs/tech-research.md`，覆盖四项核心能力的技术模块拆解：
- M-1 人声分离、M-2 声音转换、M-3 LLM 歌词生成、M-4 歌唱重合成

---

### 会话二：技术预研文档 - 补充技术原理

**用户需求**：在技术实现路径之前，先描述产出技术原理（选中了能力一的标题行）

**变更**：为全部四项能力的实现路径前新增「技术原理」小节，解释核心技术概念：
- 能力一：音色、Speaker Embedding、Zero-shot vs Fine-tune
- 能力二：人声分离原理、音色转换（Diffusion）、音频重混合
- 能力三：结构约束来源、LLM 指令遵从、校验与重试
- 能力四：旋律时间结构、F0 提取、时间轴对齐

---

### 会话三：M-1 人声分离 - 方案决策

**用户需求**：增加方案决策部分，该部分选择 Demucs v4（htdemucs 模型）

**决策结论**：
| 决策项 | 内容 |
|---|---|
| 选定方案 | Demucs v4，htdemucs 模型 |
| 安装方式 | `pip install demucs` |
| 调用方式 | Python API / CLI，MPS 加速：`-d mps` |
| 决策理由 | 质量业界最优，Apple Silicon MPS 加速已验证，MIT 协议 |

---

### 会话四：M-2 声音转换 - 方案决策

**用户需求**：增加方案决策部分，选择 seed-vc（SVC 模型：seed-uvit-whisper-base）

**决策结论**：
| 决策项 | 内容 |
|---|---|
| 选定方案 | seed-vc，SVC 专用模型 `seed-uvit-whisper-base`（200M，44.1kHz） |
| 使用模式 | 零样本（Zero-shot） + Fine-tune |
| Python 版本 | 官方建议 Python 3.10 |
| 决策理由 | 歌唱 SVC 评测 SECS/CER 优于 RVCv2；2025-03 官方支持 Apple Silicon |

**附加**：确定声音模型存储规范 `~/.ai-music/voices/{name}/model.pth + config.yml + meta.json`

---

### 会话五：M-3 LLM 歌词生成 - 方案决策

**用户需求**：增加方案决策部分，支持基于配置参数选择云端或本地模型，云端支持 openai、deepseek、qwen，本地支持 Qwen2.5-7B 等

**决策结论**：可插拔 LLM Provider 架构
- 所有云端模型（OpenAI/DeepSeek/Qwen）均兼容 OpenAI SDK 协议，通过 `base_url` + `api_key` + `model` 适配
- 本地 Ollama 暴露同一协议 API，无需额外适配
- 默认推荐 DeepSeek（性价比高，中文能力强，国内访问无障碍）
- 配置文件：`~/.ai-music/config.yml` → `llm.provider`

---

### 会话六：M-4a 时间轴获取 - LRC 文件策略讨论

**用户问题**：如果有歌曲本身的歌词 LRC 文件，是否还需要 ASR 这部分能力？

**结论**：LRC 文件可以完全替代 ASR，确立双路径策略：
- **路径一（首选）**：用户提供 LRC 文件 → 直接解析，跳过 ASR
- **路径二（兜底）**：无 LRC 文件 → WhisperX 自动提取

**影响**：M-4a 章节重写为「双路径策略」，CLI 新增可选参数 `--lrc`

---

### 会话七：M-4b 歌唱合成 - 方案决策

**用户需求**：增加决策部分，同时支持两种路线 A 和 B，通过参数配置选择具体路线

**决策结论**：
| 路线 | 内容 |
|---|---|
| 路线 A（默认）| seed-vc SVC：TTS → F0 提取 → SVC 合成 |
| 路线 B（备选）| DiffSinger SVS：提取乐谱 → DiffSinger 合成 |
| 切换方式 | `~/.ai-music/config.yml` → `synthesis.route: svc / svs` |

---

### 会话八：M-4c 补充

**用户指出**：M-4c（时间轴对齐与音频拉伸）在实现路径中提到但没有专门章节。

**补充内容**：新增 M-4c 完整章节
- **选定方案**：pyrubberband（Rubber Band Library）
- 逐句拉伸/压缩，拉伸比例建议控制在 0.7x~1.4x
- 音高保持（pitch-preserving），不影响旋律

---

### 会话九：字数约束与 M-4c 的关系澄清

**用户问题**：如果在歌词生成过程中已经保证了与原歌词字数/音节数保持一致，M-4c 还有问题么？

**结论**：
- 字数一致 ≠ 演唱时长一致，M-4c 仍然必要
- 原因：TTS 按说话韵律合成，每个字发音时值不固定，不会自动匹配原曲音乐节拍
- 但字数约束大幅缩小拉伸范围（可能的 0.65x → 0.85x~1.15x），音质损失可忽略
- 两者是互补关系：字数约束降低对齐难度，M-4c 做精确微调

**文档更新**：修改 M-4c「核心问题」描述，新增与字数约束关系的说明

---

### 会话十：技术预研文档全面检查 + 汇总表修复

**用户需求**：检查技术预研文档，并修复汇总表

**发现并修复的问题**：
1. 概述模块表 M-4 描述未拆分为 M-4a/M-4b/M-4c
2. 能力四实现路径图中步骤②还写旧的「ASR + 强制对齐」，未体现双路径
3. 4.1 技术原理只有路线 A，补充了路线 B（DiffSinger）的原理说明
4. M-4b 路线 A 用了 TTS 但未说明选用哪个 TTS 引擎 → 补充 TTS 对比表，选定 edge-tts（默认）/pyttsx3（离线 fallback）
5. 汇总表多处旧描述未同步更新

**汇总表最终状态**：

| 模块 | 选型结论 |
|---|---|
| M-1 人声分离 | Demucs v4（htdemucs） |
| M-2 声音转换 | seed-vc（seed-uvit-whisper-base） |
| M-3 LLM | DeepSeek/OpenAI/Qwen（云端）/ Ollama（本地），OpenAI SDK 协议 |
| M-4a 时间轴 | LRC 解析（首选）/ WhisperX（兜底） |
| M-4b TTS 引擎 | edge-tts（默认）/ pyttsx3（离线 fallback） |
| M-4b 歌唱合成 | seed-vc SVC 路线 A（默认）/ DiffSinger 路线 B（备选） |
| M-4c 时间对齐 | pyrubberband |
| CLI 框架 | Typer（基于 Click） |
| 音频处理库 | pydub + ffmpeg |

---

### 会话十一：需求文档更新 - 新增 LRC 提取为独立功能

**背景**：基于技术预研确立的 LRC 文件策略，需回到需求文档，将 LRC 提取作为独立功能。

**用户需求**：「将音频提取歌词 LRC 文件作为独立的功能，并且在后续声音替换和合成中使用 LRC 文件作为输入参数之一」

**需求文档从 v0.7 升级至 v0.8，变更如下**：
- **新增功能一**：LRC 提取（`lrc import` / `lrc extract` / `lrc preview`）
  - 路径一：导入已有 LRC 文件（格式校验+规范化）
  - 路径二：从音频 ASR 自动提取（兜底）
- 原功能一~四编号后移为功能二~五
- 功能五（歌词替换合成）新增 `--lrc` 参数（初始设计为可选）
- 工作流从 A/B/C 扩展为 A/B/C/D
- 新增技术决策项 T-09（LRC 提取方案）
- 术语表新增 LRC File、LRC Extraction、Forced Alignment

---

### 会话十二：LRC 改为必须输入

**用户需求**：「LRC 作为必须输入选项」

**变更**：将功能五（歌词替换合成）中的 `--lrc` 参数从可选改为必须

**更新位置（5 处）**：
1. 项目概述第 5 条：`LRC 文件为必须输入，需在执行本功能前通过功能一预先准备好`
2. 2.5.1 功能描述：改为「**LRC 时间轴文件（必须输入，需通过功能一预先准备）**」，并加注为何必须提前准备
3. 2.5.4 输入规格：`LRC 文件（.lrc，必须提供）`
4. 2.5.5 CLI 示例：注释改为「LRC 为必须参数」
5. 2.6 工作流注意事项：`LRC 文件必须在执行 lyrics-replace 前准备好`

**设计理由**：ASR 在歌唱场景精度有限，需人工核对；强制提前准备避免合成主流程因 ASR 错误失败

---

### 会话十三：建立对话记录文件

**用户需求**：「对当前以及后续所有对话内容持续及时记录到对话记录文件中」

**产出**：创建 `docs/conversation-log.md`，将本次会话全部关键内容录入，后续对话继续追加。

---

### 会话十四：市场竞品调研

**用户问题**：「目前是否有开源的或者商用的产品可以满足我们的需求」

**调研范围**：开源项目（AICoverGen、RVC v2、seed-vc）及商用产品（Suno、Udio、Musicfy、Voicify.ai、网易/QQ AI 翻唱）

**按需求逐项检查结果**：

| 需求 | 市场现状 |
|---|---|
| 功能一：LRC 提取 | ✅ 有成熟技术（WhisperX），但无完整 CLI 工具 |
| 功能二：声音学习 | ✅ RVC v2、seed-vc 均支持，但需手动搭环境 |
| 功能三：声音替换 | ✅ 最成熟，AICoverGen/Musicfy/Voicify 均已实现 |
| 功能四：歌词生成 | ✅ LLM 可直接做，但无与歌曲结构绑定的专用工具 |
| 功能五：换歌词+保留原调+保留原声 | ❌ **市场空白，几乎无现成方案** |

**现有开源项目详情**：

- **AICoverGen**（github.com/SociallyIneptWeeb/AICoverGen）
  - 技术栈：RVC v2 + MDX-Net + ffmpeg
  - 功能：声音克隆翻唱（换音色，保留原旋律和歌词）
  - ❌ 只换音色，**无法换歌词**；需 NVIDIA GPU；无 Apple Silicon 支持

- **RVC v2 WebUI**：最成熟的声音转换工具，社区生态丰富（大量预训练模型），但只做声音转换，不涉及歌词

- **seed-vc**：我们已选型，只是模型本身，无完整工具链

**商用产品详情**：

- **Suno / Udio**：从歌词/描述全新生成歌曲，无法保留原有旋律和音色（「从零生成」而非「改造已有歌曲」）
- **Musicfy / Voicify.ai**：AI cover（换音色），只换音色不能换歌词
- **国内平台 AI 翻唱**：闭源商用，无法自定义，不能换歌词

**关键发现**：Reddit 2025 年 2 月有人明确寻求「换歌词保留原声原调」工具，底下无可用答案，证明这是社区公认的未满足需求。

**结论**：
1. **功能二+三（声音学习+替换）**：市场有方案，但非 Apple Silicon CLI 工具，需自行封装
2. **功能五（换歌词）**：**市场空白**
3. **完整五项需求的组合**：完全没有现成产品，这是我们项目的差异化价值所在
4. 我们可复用 seed-vc / Demucs / WhisperX 等成熟组件，重点攻克功能五这个技术空白

---

## 当前文档状态

| 文档 | 版本 | 路径 |
|---|---|---|
| 需求描述文档 | v0.8 | `docs/requirements.md` |
| 技术预研选型文档 | v0.3 | `docs/tech-research.md` |
| 对话记录 | — | `docs/conversation-log.md` |

---

### 会话十五：搭建开发环境

**用户需求**：「让我们先把开发环境搭建起来」

**环境基础**（已有）：macOS Apple Silicon（arm64）、conda 24.1.2、Homebrew 5.0.12、ffmpeg 7.0.2

**完成步骤**：

1. 创建 conda 虚拟环境 `ai-music`（Python 3.10）
2. 安装 PyTorch 2.10.0（MPS 可用 ✅）
3. 安装 Demucs 4.0.1（M-1 人声分离）
4. WhisperX（M-4a LRC 兜底）——用户跳过，后续按需安装
5. 安装基础依赖：pydub / pyrubberband / edge-tts / pyttsx3 / typer / openai
6. 系统依赖：rubberband 3.3.0（brew install）

**初始化项目结构**：

```
ai-music/
├── src/ai_music/
│   ├── cli.py          # CLI 入口（typer，命令框架）
│   ├── lrc/            # 功能一：LRC 提取
│   ├── voice/          # 功能二：声音学习
│   ├── lyrics/         # 功能四：歌词生成
│   ├── synthesis/      # 功能五：歌词替换合成
│   ├── audio/          # 音频处理公共模块
│   └── config/         # 配置管理
├── tests/
├── scripts/check_env.py  # 环境验证脚本
├── requirements.txt
├── pyproject.toml
└── .gitignore
```

**环境验证结果（15 项全部通过）**：Python 3.10 / PyTorch 2.10 MPS ✅ / Demucs 4.0.1 / pyrubberband 0.4.0 / openai 2.28.0 / edge-tts / typer 0.24.1 / ffmpeg 7.0.2 / rubberband 3.3.0

**注意**：seed-vc 需单独 `git clone` 安装（未通过 pip），待 PoC 阶段处理。

---

---

## 2026-03-17

### 会话十六：PoC-A 冒烟测试 — TTS 合成音频跑通端到端流程

**用户需求**：启动 PoC-A 验证，先用 TTS 合成音频做冒烟测试。

**完成步骤**：
1. `git clone` 安装 seed-vc 到 `/Users/yuxudong/Documents/seed-vc`
2. 使用 `generate_source.py`（edge-tts zh-CN-XiaoxiaoNeural）和 `generate_target.py`（zh-CN-YunxiNeural）生成测试音频
3. 编写 `poc_a_voice_replace.py`：Demucs 人声分离 → seed-vc VC 转换 → pydub 混合
4. 端到端跑通，输出 `final_poc_a.mp3`

**结果**：✅ 流程跑通，Demucs 分离 < 1s，seed-vc 转换 RTF 1.52×

---

### 会话十七：PoC-A 真实歌曲测试 — VC 模式（exp-02）

**用户需求**：用真实歌曲替换 TTS 合成音频，验证真实场景效果。

**测试数据**：
- source：王菲 - 匆匆那年（女声，241s）
- target：邓丽君 - 我只在乎你（女声，252s）

**发现问题 P-2**：seed-vc 输出人声音量极低（-40 dBFS vs 原始人声 -16.3 dBFS），直接混合后人声几乎听不到。

**输出**：`final_voice_replace.mp3`（音量严重失衡，不可用）

---

### 会话十八：PoC-A 音量修复（exp-03）

**修复方案**：`mix_real.py` 新增 `match_rms()` 函数，混合前将转换人声的 RMS 电平对齐到原始人声。

```python
def match_rms(source, reference):
    diff_db = reference.dBFS - source.dBFS
    return source + diff_db
```

**结果**：⚠️ 音量问题解决，但 VC 模式不保留 F0 旋律，听感有明显旋律漂移。

---

### 会话十九：PoC-A 切换 SVC 模式 + MPS Bug 修复（exp-04）

**用户需求**：诊断并修复声音替换中的音高和节奏质量问题。

**关键变更**：
1. 将 `--f0-condition` 从 `False` 改为 `True`（启用 SVC 歌唱模式，保留 F0 旋律）
2. 新增 `--auto-f0-adjust True` 和 `--semi-tone-shift 0`
3. 将扩散步数从 10 提升到 30

**Bug 修复 — MPS float64**：
- `seed-vc/inference.py` 第 329-330 行：`torch.from_numpy(F0).to(device)` → 加 `.float()`
- 根因：numpy 默认 float64，MPS 不支持

**结果**：⭐⭐⭐ SVC cfg=0.7 基本可用，旋律保留但音色相似度仍有差距。

---

### 会话二十：PoC-A CFG 调优（exp-05）

将 `--inference-cfg-rate` 从 0.7 提升到 0.8，验证对音色相似度的影响。

**结果**：⭐⭐⭐+ 音色更贴近目标参考，RTF 改善到 2.55×。**当前同性别场景最优配置。**

---

### 会话二十一：PoC-A 总结文档编写

**产出**：创建 `poc-summary.md`，完整记录：
- 各模块验证结果（Demucs ✅ / seed-vc ⚠️ / 混合 ✅）
- 端到端性能数据（4 分钟歌曲 → 11 分钟处理）
- 遗留问题列表（P-1 ~ P-5）
- 下一步建议

---

## 2026-03-18

### 会话二十二：修复 torch/torchaudio 兼容性

**问题**：安装 `audio-separator` 时 torch 被升级为 2.10.0，torchaudio 二进制不兼容（libtorchaudio.so 加载失败）。

**修复**：`pip install --upgrade torchaudio`（2.8.0 → 2.10.0）

**验证**：torch / torchaudio / demucs CLI / audio-separator / MPS 全部正常。

**附加**：`requirements.txt` 新增 `audio-separator[cpu]==0.42.1`

---

### 会话二十三：参考音频二次净化 — bleedless 模型

**目标**：解决 P-2（参考音频伴奏泄漏问题）。

**完成步骤**：
1. 使用 audio-separator 下载最佳模型 `mel_band_roformer_kim_ft2_bleedless_unwa.ckpt`（870MB）
2. 对 tongyang.mp3 先做 Demucs 一次分离（28s，MPS，RTF ~9.8×）
3. 再用 bleedless 模型做二次净化（98s，RTF ~2.8×）

**净化效果**：响度从 -16.5 dBFS 降至 -17.4 dBFS（-0.8 dB），证明去除了部分残留信号。

---

### 会话二十四：跨性别转换实验（exp-06）

**目标**：用净化后的痛仰乐队人声（男声）作为 target，验证二次净化 + 跨性别转换。

**完成步骤**：
1. 以 bleedless 净化后的痛仰人声作为 seed-vc target 参考音频
2. seed-vc SVC 推理（source 241s，cfg=0.8，30 步）→ 耗时约 37 分钟（RTF ~9.2×）
3. pydub 混合输出 `compare_tongyang_clean_cfg08.mp3`

**发现问题 P-6 — 跨性别转换**：
- source = 王菲（女声，F0 均值 ~280Hz）
- target = 痛仰乐队（男声，F0 均值 ~140Hz）
- 输出听感**仍偏女声**
- 根因：seed-vc SVC 保留 source 的 F0 轮廓，auto-f0-adjust 只做整体平移，F0 仍处于女声区间

**解决方案（已记录）**：
- 方案 A：`--semi-tone-shift -8~-10` 强制降调
- 方案 B：换用同性别 source/target 对
- 方案 C：Fine-tune 模式（长期）

---

### 会话二十五：POC 目录整理（第一轮）

**用户需求**：「整理 POC 目录，按每一轮实验一个子目录的方式整理」

**完成内容**：
1. 创建 6 个实验子目录 `exp-01-smoke-test` ~ `exp-06-bleedless-cross-gender`
2. 迁移 29 个音频文件到各实验的 `input/` / `intermediate/` / `output/` 子目录
3. 为每个实验编写 `README.md`（验证说明）和 `result.md`（验证结果）
4. 清理旧的散乱 `output/` 子目录和脚本
5. 更新 `poc-summary.md` 中的文件路径引用

---

### 会话二十六：POC 目录整理（第二轮 — 用户手动调整）

**用户操作**：手动将 poc 目录按实验类别分成两个子目录：
- `poc/sound-repalce-experiments/` — 声音替换实验
- `poc/lrc-replace-experiments/` — 歌词替换实验（待填充）

**同步更新**：
- `poc/audio/` 音频文件重命名为歌手-歌名格式（`source.mp3` → `wangfei-congcongnanian.mp3`）
- 各实验 `input/` 目录中的文件名同步重命名
- `poc-summary.md` 和各 `README.md` 中的文件路径引用更新

---

### 会话二十七：补全实验 README 可重现运行步骤

**问题**：各实验 README 缺少完整的运行命令，无法独立重现实验。

**修复内容**：
1. 所有 README 新增「前置条件」章节（conda 环境、seed-vc 路径、pip 依赖）
2. 所有 README 新增完整「运行步骤」章节（每一步的 CLI 命令，带 `EXP=` 变量简化路径）
3. 补充预期耗时和依赖关系说明
4. `mix_real.py` 从硬编码路径重构为 `argparse` CLI，可复用于任意实验

---

### 会话二十八：Git LFS 配置 — 音频文件纳入版本管理

**用户需求**：「将音频文件也作为 git 变更的一部分，全部推送到远端仓库」

**完成内容**：
1. 配置 Git LFS 追踪 `*.mp3` / `*.wav` / `*.flac` / `*.ogg` / `*.m4a`（`.gitattributes`）
2. 修改 `.gitignore`：移除旧的音频忽略规则，改为 LFS 管理
3. 提交 35 个音频文件（614MB），通过 LFS 上传 711MB 到远端

---

### 会话二十九：对话记录整理

**用户需求**：「将最近的对话总结并上传」

**产出**：更新 `docs/conversation-log.md`，补充会话十六 ~ 二十九的完整记录（2026-03-17 ~ 2026-03-18）。

---

### 会话三十：代码推送时同步对话记录规则

**用户需求**：「记住之后当需要对代码推送到远端的时候，同时整理本次提交相关的对话信息，与代码一起提交」

**规则已记录到记忆系统**：每次 `git push` 前，必须先整理当次对话信息追加到 `docs/conversation-log.md`，与代码一起提交。

---

### 会话三十一：PoC 遗留问题盘点

**用户需求**：「看看当前 POC 验证还有哪些遗留问题」

**盘点结果**：
- 🟢 已解决：P-2（伴奏泄漏）、P-3（环境兼容性）、P-4（模型下载）
- 🔴 未解决：P-1（音色相似度不足）、P-5（推理速度偏慢，可接受）、P-6（跨性别转换失效）
- P-1 和 P-6 的核心解决方向：**Fine-tune 微调**

---

### 会话三十二：seed-vc Fine-tune PoC 验证计划

**用户需求**：「从 fine-tune 开始，先整理一个 POC 验证计划」

**用户补充信息**：
- 可以提供更多目标歌手的歌曲文件（建议每位歌手 2~3 首）
- 训练数据来源只有歌曲（全部依赖 Demucs + bleedless 净化）
- Mac 配置为 M2 Pro 32GB，可用 batch_size=2

**产出**：制定 `poc/sound-repalce-experiments/seed-vc-finetune/plan.md`，包含：
- 4 轮实验设计（exp-07 ~ exp-10）
- 同性别 Fine-tune（邓丽君）+ 跨性别 Fine-tune（痛仰）
- 完整的训练参数、命令和风险预案

**目录结构**：
```
poc/sound-repalce-experiments/seed-vc-finetune/
├── plan.md                           验证计划
├── exp-07-ft-same-gender-train/      同性别 Fine-tune 训练
├── exp-08-ft-same-gender-infer/      同性别 Fine-tune 推理对比
├── exp-09-ft-cross-gender-train/     跨性别 Fine-tune 训练
└── exp-10-ft-cross-gender-infer/     跨性别 Fine-tune 推理对比
```

---

---

### 会话三十三：Fine-tune 数据准备 — 邓丽君人声提取

**用户需求**：提供邓丽君 5 首歌曲用于 Fine-tune 训练数据准备（放置在 `poc/audio/denglijun/`）。

**完成内容**：
1. 使用 Demucs htdemucs 对 5 首歌曲做人声分离
2. 发现 audio-separator bleedless 二次净化输出文件名冲突（全部覆盖为同一文件）
3. **修复方案**：编写循环脚本，每首歌分别处理到独立临时目录后重命名为 `{songname}_clean.wav`
4. 成功产出 5 个净化人声文件到 `exp-07-ft-same-gender-train/training-data/clean-vocals/`

**产出文件**：
- `denglijun-renchangjiu_clean.wav`（~246s）
- `denglijun-tianmimi_clean.wav`（~211s）
- `denglijun-wozhizaihuni_clean.wav`（~252s）
- `denglijun-xiaocheng_clean.wav`（~154s）
- `denglijun-yueliang_clean.wav`（~209s）

---

### 会话三十四：Fine-tune 训练 — 数据切分与首次训练尝试

**问题发现**：seed-vc `ft_dataset.py` 要求音频时长 1~30 秒，5 首完整歌曲（150-250 秒）全部被跳过，导致 `RecursionError`，训练崩溃。

**解决方案**：创建 `split_audio.py` 脚本，将 5 首歌切分为 20 秒片段（尾部 < 10 秒丢弃）。

**产出**：54 个训练片段（10-20 秒），存放在 `.../clean-vocals/segments/`

**首次启动训练**：以 `--max-steps 500 --batch-size 2 --save-every 100` 参数运行，进程在 MPS 初始化 + 模型加载阶段静默 47 分钟，完全无反馈，无法判断状态，主动中止。

---

### 会话三十五：Fine-tune 监控体系建立

**用户需求**：「在开始新的 fine tune 之前，我期望仔细计划一下，如何能够监控 fine tune 进展及时看到反馈和问题」

**根因分析**（47 分钟无反馈的原因）：
- `Trainer.__init__` 加载 5 个子模型时完全无 print 输出
- 进程 stdout 被 conda 包装层截断，无法实时查看
- 没有日志文件，出错后也无法事后复查

**三层监控方案**：

| 层级 | 方案 | 效果 |
|------|------|------|
| 层 1 | 修改 `seed-vc/train.py`：在 5 个子模型加载前后加 `[init x/5]` print + 耗时 | 可见初始化进度 |
| 层 2 | 训练命令改为 `python -u train.py ... >> /tmp/ft_denglijun.log 2>&1` | 全量日志持久化 |
| 层 3 | 创建 `monitor_train.sh` 监控面板脚本（15s 刷新，显示 loss/checkpoint/内存） | 实时全局视图 |

**train.py 修改内容**（`/Users/yuxudong/Documents/seed-vc/train.py`）：
- `__init__` 中 5 个 `build_*` 调用前后加带耗时的 print
- `train_one_epoch` 中 `print(f"epoch {epoch}, step {iters}, loss: {ema_loss:.4f}, step_time: {step_time:.1f}s")`
- 训练图构建阶段加 `[init]` print

**验证结果（dry run max-steps=1）**：
```
[init 1/5] SV 模型加载完成 (1.1s)
[init 2/5] Semantic 模型加载完成 (4.6s)
[init 3/5] F0 模型加载完成 (1.4s)
[init 4/5] Converter 加载完成 (1.8s)
[init 5/5] Vocoder 加载完成 (3.7s)
[init ✓] 所有子模型加载完成，耗时 12.5s
epoch 0, step 0, loss: 0.5765, step_time: 8.3s
```

**新增脚本**：
- `poc/sound-repalce-experiments/seed-vc-finetune/monitor_train.sh`
- `poc/sound-repalce-experiments/seed-vc-finetune/run_train.sh`
- `poc/sound-repalce-experiments/seed-vc-finetune/split_audio.py`

---

### 会话三十六：Fine-tune 正式训练与中止

**训练参数**：`--batch-size 2 --max-steps 500 --save-every 100 --num-workers 0`

**训练过程（监控数据）**：

| 阶段 | Step | Loss (EMA) | step_time |
|------|------|-----------|-----------|
| 初始化 | — | — | 12.5s |
| 早期（正常） | 0~90 | 0.30 → 0.42 | ~8-18s |
| checkpoint 保存 | 100 | 0.4321 | **370s（异常）** |
| 保存后（慢） | 110 | 0.4348 | ~160s |
| 严重劣化 | 110+ | — | ~530s |

**关键里程碑**：Step 100 的 checkpoint `DiT_epoch_00003_step_00100.pth`（2.1GB）已保存。

**中止原因**：
- 保存 2.1GB checkpoint 触发 macOS 内存压力（Free 降至 0.08GB）
- MPS Unified Memory 内存碎片化，step 时间从 ~10s 劣化至 530s
- 以当前速度估算，500 步需 70+ 小时，不可接受

**已中止**，保留 step 100 的 checkpoint 作为后续续训起点。

**后续优化方向**：
1. `--batch-size 1`（降内存压力）
2. `--save-every 500`（最后只保存一次，避免 2.1GB 文件触发内存问题）
3. `train.py` epoch 结束后加 `torch.mps.empty_cache()`

---

## 2026-03-19

### 会话三十七：切换 RVC Fine-tune 方案 + 深度调研

**背景**：seed-vc Fine-tune 因 2.1GB checkpoint 触发 macOS 内存压力（530s/step），彻底中止。切换到 RVC（Retrieval-based Voice Conversion）方案。

**调研结论**：

| 维度 | seed-vc Fine-tune | RVC Fine-tune |
|------|-------------------|---------------|
| 模型大小 | ~2.1GB/checkpoint | ~60-80MB |
| macOS 兼容性 | ⚠️ MPS 内存压力严重 | ✅ CPU/MPS 均可 |
| 预估训练时间 | 70+ 小时 | ~30-60 分钟 |
| 社区成熟度 | 较新 | ⭐⭐⭐⭐⭐ |

**工具选型**：Applio（IAHispano/Applio），官方支持 macOS，提供 `run-install.sh` 脚本。

**产出文件**：
- `poc/sound-repalce-experiments/rvc-finetune/plan.md`（完整方案，11 个章节）
- `rvc-finetune/exp-07~10/` 目录结构
- `run_train.sh`、`monitor_rvc_train.sh` 监控脚本

---

### 会话三十八：Applio 安装与环境配置

**操作**：
1. 新建 `rvc` conda 环境（Python 3.12，Applio 官方要求）
2. Clone Applio 到 `/Users/yuxudong/Documents/applio/`
3. 手动 `pip install -r requirements.txt` 安装依赖

**关键依赖安装结果**：

| 包 | 版本 | 状态 |
|----|------|------|
| torch | 2.7.1 + MPS | ✅ |
| faiss-cpu | 1.13.2 | ✅ |
| numpy | 2.3.5 | ✅ |
| numba | 0.63.1 | ✅ |
| praat-parselmouth | 0.4.7 | ✅ |
| pyworld | 0.3.5 | ✅（需设置 SDKROOT + conda install libcxx）|
| librosa / soundfile | 0.11.0 / 0.12.1 | ✅ |
| transformers | 4.44.2 | ✅ |

**遇到问题**：
- `pyworld` 编译失败：`fatal error: 'algorithm' file not found`
  - 根因：macOS C++ 头文件路径问题，conda 环境的 include 路径覆盖系统路径
  - 修复：`conda install -n rvc -c conda-forge libcxx` 后正常编译

---

### 会话三十九：exp-07 训练脚本调试与 Bug 修复

**目标**：用邓丽君 5 首歌净化人声（共 ~22 分钟）训练 RVC v2 模型。

**连环 Bug 排查过程**：

| # | Bug | 现象 | 根因 | 修复 |
|---|-----|------|------|------|
| 1 | `gpu=0` → `cuda:0` | 特征提取 `0it`，0 个特征文件 | `extract.py` 硬编码只支持 cuda/cpu，无 MPS 路径 | patch `extract.py` 加 MPS 自动检测分支 |
| 2 | `cut_preprocess="True"` | 预处理报 5/5 完成，但 `sliced_audios/` 为空 | preprocess.py 只匹配 `"Skip"/"Simple"/"Automatic"`，`"True"` 不匹配任何分支 | 改为 `"Automatic"` |
| 3 | 多进程异常静默吞掉 | 进度条显示 5/5 成功，实际 0 个文件 | `try/except` 捕获了错误但继续执行 | 以上两个修复后不再触发 |

**Applio 源码修改**（`/Users/yuxudong/Documents/applio/rvc/train/extract/extract.py` L215）：
```python
# 原始（只支持 cuda/cpu）
devices = ["cpu"] if gpus == "-" else [f"cuda:{idx}" for idx in gpus.split("-")]

# 修复后（自动检测 MPS）
if gpus == "-":
    devices = ["cpu"]
elif gpus == "mps" or (gpus != "-" and not torch.cuda.is_available() and torch.backends.mps.is_available()):
    devices = ["mps"]
else:
    devices = [f"cuda:{idx}" for idx in gpus.split("-")]
```

**当前状态**：exp-07 训练正在运行中 🚀
- 预处理：✅ `Automatic` 切分，生成切片文件
- 特征提取：✅ 走 MPS 路径
- 训练：✅ 进行中，`smoothed_loss_gen=29.412`，正在保存 checkpoint

**exp-08/09/10 推理脚本**已预先创建，exp-07 完成后可直接使用。

---

---

### 会话四十：ACE-Step 深度技术调研 + PoC-B 验证计划

**背景**：PoC 遗留问题梳理后，将「歌词替换与合成（功能五）」列为最高技术风险项。本次对 ACE-Step 进行深度调研，并制定 PoC-B 验证计划。

**调研结论**：

| 维度 | 结论 |
|------|------|
| 核心能力 | Lyric Editing（flow-edit）可直接在原曲 latent 空间替换歌词，保持旋律 |
| 最新版本 | v1.5（2026-01-28），LM + DiT 混合架构 |
| 质量水准 | SongEval 自然度 4.59，**超越所有已测商业模型**（Suno v5 为 4.56）|
| 内存要求 | < 4GB VRAM（M2 Pro 32GB 完全充裕）|
| macOS 支持 | ✅ 官方支持，需 `--bf16 false` |
| M2 Pro 预计速度 | RTF ≈ 1.5~2.5×（4 分钟歌曲约 6~10 分钟处理）|
| 中文支持 | ✅ 中文在 50+ 支持语言中排名靠前 |
| 对比原方案优势 | 无跨域转换问题；端到端；内置时间对齐 |

**三大关键验证问题（PoC-B 必须验证）**：
1. **Q1**：对「真实中文录音」（非 AI 生成）的 Lyric Edit 效果
2. **Q2**：中文字数差异（±0/±3/±6）对音质的影响
3. **Q3**：全曲逐句编辑拼接后的整体连贯性

**产出文件**：
- `poc/sound-repalce-experiments/ace-step-research/ace-step-tech-research.md`（技术调研报告）
- `poc/sound-repalce-experiments/ace-step-research/poc-b-validation-plan.md`（验证计划）

**PoC-B 实验设计（4 个实验，预计 3~4 天）**：

| 实验 | 目标 | 关键验证点 |
|------|------|----------|
| exp-11 | 安装冒烟测试 | 环境兼容性、MPS 稳定性 |
| exp-12 | 单句质量验证（5 组对比）| 旋律保持、字数差异影响 |
| exp-13 | 全曲逐句替换 | 接缝问题、端到端流程 |
| exp-14 | 性能 Benchmark | RTF 实测，M2 Pro 真实速度 |

---

## 当前文档状态

| 文档 | 版本 | 路径 |
|---|---|---|
| 需求描述文档 | v0.8 | `docs/requirements.md` |
| 技术预研选型文档 | v0.3 | `docs/tech-research.md` |
| 对话记录 | — | `docs/conversation-log.md` |
| PoC-A 验证总结 | — | `poc/sound-repalce-experiments/poc-summary.md` |
| seed-vc Fine-tune 计划 | — | `poc/sound-repalce-experiments/seed-vc-finetune/plan.md` |
| RVC Fine-tune 计划 | — | `poc/sound-repalce-experiments/rvc-finetune/plan.md` |
| **ACE-Step 技术调研报告** | v1.0 | `poc/sound-repalce-experiments/ace-step-research/ace-step-tech-research.md` |
| **PoC-B 验证计划** | v1.0 | `poc/sound-repalce-experiments/ace-step-research/poc-b-validation-plan.md` |

---

## 待办事项

- [x] seed-vc 安装与 PoC-A 验证
- [x] seed-vc Fine-tune 尝试（因内存问题中止，切换方案）
- [x] RVC Fine-tune 方案调研与计划制定
- [x] Applio 安装与环境配置（rvc conda 环境，Python 3.12）
- [ ] **RVC Fine-tune 验证**（进行中）
  - [x] Applio 安装 + Bug 修复（extract.py MPS patch + cut_preprocess 修复）
  - [x] exp-07：邓丽君同性别 Fine-tune 训练 ✅（最佳模型 `denglijun_rvc_200e_8400s_best_epoch.pth`）
  - [x] exp-08：同性别推理对比（run_infer_script 参数修复；输出 rvc_idx050/075 + 混音）
  - [ ] exp-09：痛仰跨性别 Fine-tune 训练（**进行中** 🚀 `douwei_rvc`，epoch 2/200）
  - [ ] exp-10：跨性别推理对比（脚本已预先修复，等 exp-09 完成后运行）
- [ ] **PoC-B：歌词替换与合成验证**（进行中）
  - [x] ACE-Step 技术调研
  - [x] PoC-B 验证计划（exp-11~14）
  - [x] ACE-Step v1.5 安装（Python 3.11，conda ace_step 环境）
    - 修正：v1.5 要求 Python >=3.11（非 3.10）
    - 修正：v1.5 启动参数变更（去掉 --bf16/--cpu_offload/--overlapped_decode，改用 --device mps --backend mlx）
    - v1.5 自动识别 M2 Pro 25GB 统一内存，tier=unlimited，mlx 后端
  - [x] 新增人声预处理脚本：Demucs 分离 + 去混响（保留中间产物）
    - 脚本：`poc/audio/process_vocals.py`
    - CLI：`ai-music voice preprocess --input <mp3/wav>`
  - [ ] exp-11：ACE-Step 冒烟测试（模型下载中，`acestep-v15-turbo` 4.79GB + `Qwen3-Embedding` 1.19GB）
  - [ ] exp-12：Lyric Editing 单句质量验证
  - [ ] exp-13：全曲逐句替换流程验证
  - [ ] exp-14：M2 Pro 性能 Benchmark

---

### 会话四十一：RVC 训练推进、人声预处理排查与阶段总结归档

**背景**：在 RVC Fine-tune 方案下继续推进同性别/跨性别实验，同时开始进入歌词替换 PoC-B 的环境验证阶段。

**本轮主要进展**：

1. **RVC 训练与推理**
   - exp-07（邓丽君同性别）训练完成，产出最佳模型：`denglijun_rvc_200e_8400s_best_epoch.pth`
   - exp-08 推理脚本完成适配，修复 `run_infer_script` 新版参数签名问题
   - exp-09（窦唯/痛仰跨性别）训练完成，产出最佳模型：`douwei_rvc_200e_16000s_best_epoch.pth`
   - exp-10 推理脚本发现 `.index` 匹配问题：目录中实际存在 `douwei_rvc.index`，但脚本只匹配 `added_*.index`，导致日志长期显示 `使用索引: (无 index)`

2. **RVC 当前关键问题定位**
   - 在“无 index”情况下，RVC 推理可以稳定跑通，但输出人声仍明显保留原唱风格，目标音色强化有限
   - 在修正脚本并真正启用 `douwei_rvc.index` 后，推理开始阶段触发 `segmentation fault`
   - 初步判断：问题不再是脚本参数，而是 **FAISS / index 检索链路在 Apple Silicon 环境下的原生崩溃风险**

3. **人声预处理链路排查**
   - Demucs 人声分离已稳定跑通，可输出 `vocals.wav / no_vocals.wav`
   - 使用 `audio-separator` 做去回声/去混响时，确认当前版本要求传递真实的 `model_filename`
   - 通过 `audio-separator -l --list_filter dereverb --list_format json` 找到多个可用 dereverb 模型：
     - `dereverb_mel_band_roformer_anvuew_sdr_19.1729.ckpt`
     - `dereverb_mel_band_roformer_less_aggressive_anvuew_sdr_18.8050.ckpt`
     - `dereverb-echo_mel_band_roformer_sdr_13.4843_v2.ckpt`
   - 结论：dereverb 模型本身可用，但调用链路与默认模型名仍需工程化收口

4. **ACE-Step / PoC-B 进展**
   - ACE-Step v1.5 环境已装起，确认 Python 版本要求为 `>=3.11,<3.13`
   - 旧版启动参数 `--bf16 / --cpu_offload / --overlapped_decode` 已失效，v1.5 会自动选择 MPS / mlx 路径
   - PoC-B 目前已完成调研与验证计划，正式效果实验（exp-11~14）尚未完成

5. **阶段总结沉淀**
   - 新增阶段总结文档：`poc/current-progress-summary.md`
   - 汇总当前 POC 进展、已完成事项、核心阻塞问题与下一步优先级

**当前阶段结论**：

- ✅ PoC-A 基础声音替换链路已验证可行
- ✅ RVC Fine-tune 在 Apple Silicon 上可完成训练
- ⚠️ RVC 在不启用 index 时音色强化不足
- ❌ RVC 在启用 index 后出现 `segmentation fault`，成为当前最大阻塞点
- ⚠️ ACE-Step / SoulX-Singer 仍需进入正式对比实验，功能五尚不能收敛最终方案

**下一步优先级**：

1. P0：排查 RVC + FAISS index 崩溃问题
2. P1：推进 ACE-Step 冒烟与单句验证（exp-11 / exp-12）
3. P2：固化人声预处理脚本（分离 → dereverb）
4. P3：推进 SoulX-Singer 同素材对比实验

---

*记录持续更新中*
