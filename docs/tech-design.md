# AI Music 工具 - 技术方案设计文档

> **版本**：v0.1（草稿 - 待填充）  
> **创建日期**：2026-03-16  
> **状态**：进行中  
> **前置文档**：[需求描述文档 v0.7](./requirements.md) · [工作计划](./tech-design-plan.md)

---

## 1. 技术架构总览

> *待完成（T-B1 ~ T-B4 完成后填充）*

### 1.1 整体技术栈

| 层次 | 技术选型 | 说明 |
|---|---|---|
| CLI 框架 | 待定 | — |
| 人声分离 | 待定（T-A2） | — |
| 声音转换 | 待定（T-A3） | — |
| 歌词重合成 | 待定（T-A4） | — |
| AI 歌词生成 | 待定（T-A5） | — |
| 运行环境 | 待定（T-A1） | — |

### 1.2 模块关系图

> *待完成*

### 1.3 数据流总览

> *待完成*

---

## 2. 各模块技术选型

### 2.1 运行环境（T-A1 / T-08）

**结论**：✅ 已确定

| 项目 | 决策 | 说明 |
|---|---|---|
| **目标操作系统** | macOS（Apple Silicon / M 系列） | 第一期以 Mac M 系列为主要目标平台 |
| **Python 版本** | **3.10** | 主要 ML 库（Demucs、RVC、seed-vc）均明确建议 3.10；3.11/3.12 存在部分库兼容性问题 |
| **加速后端** | **PyTorch MPS**（Metal Performance Shaders） | M 系列芯片内置 GPU 核心，可通过 MPS 后端加速 PyTorch 运算，无需独立显卡 |
| **CPU-only 回退** | 支持 | 对于 MPS 不支持的算子，自动回退至 CPU；部分操作（如 FFmpeg 音频处理）纯 CPU 运行 |
| **包管理** | **conda**（推荐）或 `venv` | conda 在 Apple Silicon 上对 arm64 原生库支持更好，推荐使用 `miniforge` / `mambaforge` |
| **内存要求** | 建议 ≥ 16 GB | M 系列统一内存（Unified Memory），同时充当 CPU 和 GPU 内存；主要模型（Demucs HTDemucs ~83M、seed-vc ~200M）合计约 8~10 GB |

**关键说明**：

1. **MPS vs CUDA**：Apple Silicon 无 NVIDIA GPU，无法使用 CUDA。PyTorch 自 1.12 起支持 MPS 后端，可获得约 3~5x 相比纯 CPU 的加速，但部分算子尚未完整支持 MPS，需关注各库的兼容性说明。

2. **Python 3.10 选型依据**：
   - `Demucs v4`：官方建议 Python 3.8+，3.10 兼容性最佳
   - `RVC`：Apple Silicon 环境明确建议 `python@3.10`（via brew）
   - `seed-vc`（2025-03 新增 Apple Silicon 支持）：官方文档明确写 "Suggested python **3.10**"
   - Python 3.12 的部分 ML 库（如 numpy 1.x / triton）存在兼容性问题，暂不推荐

3. **Demucs MPS 支持**：`demucs v4`（htdemucs）已支持通过 `-d mps` 参数启用 MPS 加速，可在 M 系列 Mac 上正常运行。

4. **性能预期（无独立 GPU 影响）**：
   - 人声分离（Demucs）：3 分钟歌曲约需 1~3 分钟（MPS 加速）
   - 声音转换（seed-vc）：推理时间约为音频时长的 2~4 倍（CPU/MPS）
   - 总处理时间预计在需求要求的"3 倍歌曲时长"范围内，但接近上限

**安装环境示例**：

```bash
# 使用 miniforge 创建隔离环境（推荐）
conda create -n ai-music python=3.10
conda activate ai-music

# 安装 PyTorch（MPS 支持，Apple Silicon 原生）
pip install torch torchaudio

# 验证 MPS 可用性
python -c "import torch; print(torch.backends.mps.is_available())"  # 应输出 True
```

---

### 2.2 人声与伴奏分离（T-A2 / T-04）

> *待完成*

**候选方案对比**：

| 方案 | 分离质量 | 推理速度 | 本地运行 | 模型大小 | 许可证 |
|---|---|---|---|---|---|
| Demucs（Meta） | — | — | — | — | — |
| Spleeter（Deezer） | — | — | — | — | — |
| UVR（Ultimate Vocal Remover） | — | — | — | — | — |

**结论**：待定

---

### 2.3 人声音色转换（T-A3 / T-05）

> *待完成*

**候选方案对比**：

| 方案 | 转换质量 | 训练时间 | 推理速度 | 模型大小 | 活跃度 |
|---|---|---|---|---|---|
| RVC（Retrieval-based Voice Conversion） | — | — | — | — | — |
| so-vits-svc | — | — | — | — | — |

**结论**：待定

---

### 2.4 歌词替换与重合成（T-A4 / T-06）

> *待完成*

这是技术难度最高的模块，需要解决两个子问题：

**子问题 A：是否需要显式的歌词时间轴对齐文件？**

| 方案 | 描述 | 是否需要时间轴文件 |
|---|---|---|
| 方案一：端到端方案 | — | 否（自动推断） |
| 方案二：对齐 + 合成分离 | — | 是（需功能四提前生成） |

**子问题 B：TTS + 旋律对齐方案对比**：

| 方案 | 合成质量 | 旋律保真度 | 实现复杂度 |
|---|---|---|---|
| VITS | — | — | — |
| BERT-VITS2 | — | — | — |
| 其他 | — | — | — |

**结论**：待定

---

### 2.5 AI 歌词生成（T-A5 / T-07）

> *待完成*

**候选方案对比**：

| 方案 | 生成质量 | 成本 | 离线能力 | 延迟 |
|---|---|---|---|---|
| OpenAI GPT-4o API | — | — | 否 | — |
| Anthropic Claude API | — | — | 否 | — |
| 本地 LLM（Qwen / DeepSeek 等） | — | — | 是 | — |

**结论**：待定

---

### 2.6 声音模型管理规范（T-A6 / T-01/T-02/T-03）

> *待完成*

| 项目 | 决策 | 说明 |
|---|---|---|
| 本地存储路径 | 待定（如 `~/.ai-music/voices/`） | — |
| 模型文件格式 | 待定 | — |
| 系统预设声音数量/风格 | 待定 | — |
| 训练耗时目标 | 待定 | — |
| 跨机器导入/导出 | 待定 | — |

---

## 3. CLI 架构设计（T-B1）

> *待完成*

### 3.1 CLI 框架选型

**候选**：Typer（基于 Click，支持类型注解）/ Click（成熟稳定）

**结论**：待定

### 3.2 命令结构设计

```
ai-music
├── voice
│   ├── learn       # 声音学习
│   ├── update      # 追加参考音频更新模型
│   ├── list        # 查看声音模型列表
│   └── remove      # 删除声音模型
├── voice-replace   # 声音替换
├── lyrics
│   ├── generate    # AI 生成歌词
│   ├── template    # 导出结构模板
│   └── align       # 提取歌词时间轴（视技术方案是否必须）
└── lyrics-replace  # 歌词替换与合成
```

### 3.3 通用参数规范

> *待完成*

---

## 4. 模块划分与接口设计（T-B2）

> *待完成*

### 4.1 模块边界

```
┌─────────────────────────────────────────────────────┐
│                    CLI 入口层                         │
└──────────────┬──────────────────────────────────────┘
               │
    ┌──────────▼──────────┐
    │     核心业务模块      │
    ├─────────────────────┤
    │  voice_learning     │  声音学习（训练 + 管理）
    │  voice_replacement  │  声音替换
    │  lyrics_generation  │  歌词生成（调用 LLM）
    │  lyrics_synthesis   │  歌词替换与重合成
    └──────────┬──────────┘
               │
    ┌──────────▼──────────┐
    │     基础设施层        │
    ├─────────────────────┤
    │  vocal_separator    │  人声分离（共用）
    │  alignment          │  时间轴提取（共用）
    │  model_store        │  声音模型存储管理
    │  llm_client         │  LLM 调用封装
    └─────────────────────┘
```

### 4.2 各模块接口定义

> *待完成（T-B2 完成后填充）*

---

## 5. 数据流与文件规范（T-B3）

> *待完成*

### 5.1 声音学习数据流

```
输入：参考音频文件（MP3） + 声音名称
  → 人声分离（可选，过滤伴奏）
  → 音色特征提取 / 模型训练
  → 保存声音模型文件到本地存储
输出：声音模型文件（存储于 ~/.ai-music/voices/<name>/）
```

### 5.2 声音替换数据流

```
输入：歌曲 MP3 + 声音名称
  → 人声分离 → 纯人声音轨 + 伴奏音轨
  → 加载声音模型 → 人声音色转换
  → 转换后人声 + 伴奏混合
输出：替换后歌曲 MP3
```

### 5.3 歌词生成数据流

```
输入：原歌词 TXT + 创作提示词
  → 解析歌词结构（段落数/句数/字数）
  → 构建 Prompt → 调用 LLM API
  → 解析输出 → 校验结构约束
  → 如有偏差给出警告并确认
输出：新歌词 TXT（含结构注释）
```

### 5.4 歌词替换与合成数据流

```
输入：歌曲 MP3 + 新歌词 TXT [+ 时间轴对齐文件（视方案）]
  → 人声分离 → 纯人声音轨 + 伴奏音轨
  → 获取时间轴（自动识别 or 读取对齐文件）
  → TTS 合成新歌词 → 旋律时间轴对齐
  → 合成新人声 + 伴奏混合
输出：新歌词版歌曲 MP3
```

### 5.5 本地文件存储规范

> *待完成（T-A6 完成后填充）*

---

## 6. 多语言扩展架构（T-B4）

> *待完成*

语言处理模块（ASR / TTS / 对齐）需设计为可替换的插拔式组件：

```python
# 示意设计（非最终实现）
class LanguageBackend(ABC):
    @abstractmethod
    def transcribe(self, audio_path: str) -> LyricsAlignment: ...
    
    @abstractmethod
    def synthesize(self, text: str, alignment: LyricsAlignment) -> str: ...

class ChineseBackend(LanguageBackend):
    ...

class EnglishBackend(LanguageBackend):
    ...
```

---

## 7. 错误处理与用户体验（T-B5）

> *待完成*

### 7.1 进度展示

> *待完成*

### 7.2 错误码规范

> *待完成*

### 7.3 帮助文档规范

> *待完成*

---

## 8. 技术可行性验证（PoC 计划）（T-C1）

> *待完成*

**PoC 目标**：在正式开发前，验证以下两个高风险点的可行性：

1. **声音转换 PoC**：使用选定方案，实现一次完整的声音替换流程（输入歌曲 MP3 → 输出替换声音的 MP3）
2. **歌词重合成 PoC**：使用选定方案，实现一次完整的歌词替换合成流程（输入歌曲 MP3 + 新歌词 → 输出新歌词版 MP3）

**验收标准**：能够端到端跑通，输出音频可听（不要求完美质量）

---

## 9. 项目结构设计（T-C2）

> *待完成*

```
ai-music/
├── docs/
│   ├── requirements.md         # 需求文档
│   ├── tech-design-plan.md     # 技术方案工作计划
│   └── tech-design.md          # 技术方案设计文档（本文档）
├── ai_music/
│   ├── __init__.py
│   ├── cli/                    # CLI 入口层
│   ├── core/                   # 核心业务模块
│   │   ├── voice_learning/
│   │   ├── voice_replacement/
│   │   ├── lyrics_generation/
│   │   └── lyrics_synthesis/
│   ├── infra/                  # 基础设施层
│   │   ├── vocal_separator/
│   │   ├── alignment/
│   │   ├── model_store/
│   │   └── llm_client/
│   └── utils/
├── tests/
├── pyproject.toml
└── README.md
```

---

## 10. 开发迭代计划（T-C3）

> *待完成（T-C1 PoC 验证通过后制定）*

---

*文档结束*
