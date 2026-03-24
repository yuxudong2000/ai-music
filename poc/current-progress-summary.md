# POC 当前进展总结

> **日期**：2026-03-24  
> **范围**：PoC-A / RVC Fine-tune / 歌词替换 PoC-B  
> **状态**：进行中

---

## 一、阶段结论

当前 POC 已经从最初的 `seed-vc Zero-shot` 验证，逐步推进到：

1. **PoC-A：声音替换端到端流程已跑通**
2. **RVC Fine-tune：同性别与跨性别训练均已完成**
3. **RVC 推理脚本已适配当前 Applio 参数签名**
4. **歌词替换路线已切换到 ACE-Step / SoulX-Singer 并行验证思路**
5. **新的关键阻塞点明确为：RVC 检索索引（FAISS）在 Apple Silicon 上启用后触发 segmentation fault**

一句话总结：

> **流程已经从“能不能跑通”阶段，进入到“质量优化与稳定性排障”阶段。**

---

## 二、已完成的工作

### 2.1 技术调研与方案收敛

已完成多份核心技术文档：

- `docs/tech-research.md`：项目技术预研总文档
- `poc/lrc-replace-experiments/ace-step-research/ace-step-tech-research.md`
- `poc/lrc-replace-experiments/ace-step-research/poc-b-validation-plan.md`
- `poc/lrc-replace-experiments/method-comparison-evaluation.md`
- `poc/lrc-replace-experiments/exp-comparison/README.md`
- `poc/lrc-replace-experiments/exp-comparison/results.md`

关键认知更新：

- **SoulX-Singer 已开源并可用**，不再是“不可落地”的候选方案
- 对于“歌词替换与合成（功能五）”，当前采用：
  - **路线 C：ACE-Step Lyric Edit**
  - **路线 D：SoulX-Singer SVS / SVC**
  进行后续对比验证

---

### 2.2 PoC-A：声音替换基础链路验证完成

已完成从输入歌曲到最终混音输出的端到端流程：

- Demucs 人声分离
- seed-vc / SVC 声音替换
- pydub 重混合
- 多轮参数调优（SVC 模式、CFG、音量修复）

结论：

- **同性别场景基本可用**
- **跨性别场景效果有限**，根因是 SVC 强保留源音频 F0 与唱法

相关历史实验：

- `exp-01` ~ `exp-06`
- `poc/sound-repalce-experiments/poc-summary.md`

---

### 2.3 RVC Fine-tune 链路已完成训练

#### exp-07：邓丽君同性别 Fine-tune

训练完成，最佳模型：

- `denglijun_rvc_200e_8400s_best_epoch.pth`

结果：

- exp-08 已成功产出多组推理结果
- 推理脚本已修复当前 Applio 的参数签名变更

#### exp-09：窦唯 / 痛仰跨性别 Fine-tune

训练完成，最佳模型：

- `douwei_rvc_200e_16000s_best_epoch.pth`

说明：

- 数据来自净化后的人声数据集
- 训练目录中已存在 `.index` 文件：`douwei_rvc.index`

---

### 2.4 人声预处理链路已跑通第一步

已验证：

- **Demucs 人声分离成功**
  - 可稳定输出：`vocals.wav` / `no_vocals.wav`

对 `audio-separator` 的排查结果：

- 当前 CLI 需要传入真实的 `model_filename`
- `dereverb_mel_band_roformer` 只是前缀，不是有效模型名
- 当前环境中确认存在多个真实 dereverb 模型，例如：
  - `dereverb_mel_band_roformer_anvuew_sdr_19.1729.ckpt`
  - `dereverb_mel_band_roformer_less_aggressive_anvuew_sdr_18.8050.ckpt`
  - `dereverb-echo_mel_band_roformer_sdr_13.4843_v2.ckpt`

结论：

- **去混响/去回声模型可用，但调用方式需要传完整模型文件名**
- 这条链路还没有完全固化成稳定脚本方案

---

### 2.5 ACE-Step 环境已基本就绪

已完成：

- Python 版本要求确认：**v1.5 需要 Python 3.11~3.12**
- 启动参数差异确认：
  - 旧参数 `--bf16 / --cpu_offload / --overlapped_decode` 已不适用于 v1.5
  - 当前应由 v1.5 自动识别 Apple Silicon，并使用 `mlx` / `mps` 路径

当前状态：

- 环境已安装
- 模型下载曾启动
- **但 exp-11~14 的正式效果验证尚未完成**

---

## 三、当前最关键的问题

### 3.1 RVC 音色替换后仍更像原唱

现象：

- 使用 RVC 训练后的目标模型做推理后，输出人声仍然明显保留原唱特征
- 调整 `index_rate` 从 `0.5` 到 `0.95`，主观差异不大

根因已经确认：

- 之前脚本日志显示：`使用索引: (无 index)`
- 也就是说虽然模型已训练完成，但推理阶段**没有真正加载检索索引**
- 在这种情况下，`index_rate` 几乎不会起作用

进一步排查：

- `.index` 文件其实存在：`douwei_rvc.index`
- 问题是脚本只匹配了 `added_*.index`，没有匹配到 `douwei_rvc.index`

---

### 3.2 启用 index 后触发 segmentation fault

在修正 index 路径后，日志变成：

- `使用索引: /Users/yuxudong/Documents/applio/logs/douwei_rvc/douwei_rvc.index`

随后推理在开始阶段直接崩溃：

- `segmentation fault`

这说明：

- 不是 Python 参数错误
- 不是模型文件错误
- 而是 **native 层（大概率 FAISS）在 Apple Silicon / 当前环境中崩溃**

当前判断：

> **RVC 的“纯网络推理”能跑，但一旦启用 FAISS 检索索引，就会在当前 macOS Apple Silicon 环境中触发原生崩溃。**

这是目前最核心的技术阻塞点。

---

### 3.3 `audio-separator` 去回声链路尚未完全固化

现状：

- 命令参数格式已摸清
- 可用模型列表已找到
- 但仍需要把“默认模型名、命令调用方式、输出命名”彻底稳定下来

当前阶段可认为：

- **人声分离已稳定**
- **去回声/去混响还处在最后一轮工程收口阶段**

---

### 3.4 歌词替换 PoC-B 尚未进入结果产出阶段

目前 PoC-B 的状态更偏向：

- 方案调研完成
- 实验计划完成
- 环境准备已完成大半

但尚未完成：

- ACE-Step 单句替换效果验证
- ACE-Step 全曲逐句替换验证
- SoulX-Singer 同素材 AB 对比
- 主观评测结果沉淀

所以功能五目前还不能下最终结论。

---

## 四、当前可确认的结论

### 4.1 已确认可行

- Demucs 在 Apple Silicon 上可稳定工作
- PoC-A 声音替换链路已跑通
- RVC Fine-tune 在 Apple Silicon 上可完成训练
- ACE-Step v1.5 可在当前机器上安装运行
- `audio-separator` 的 dereverb 模型在当前环境中是可枚举可调用的

### 4.2 已确认不可作为最终答案

- seed-vc Zero-shot 无法解决跨性别音色迁移问题
- RVC 在**不启用 index**时，目标音色强化有限
- 当前 RVC + index 在 Apple Silicon 上存在稳定性风险

### 4.3 当前最值得继续推进的两条线

1. **RVC 检索崩溃排障**
   - 先确认是 `.index` 文件问题、FAISS 版本问题，还是 Apple Silicon 原生兼容性问题
2. **ACE-Step / SoulX-Singer 对比验证**
   - 这条线更贴近功能五的最终目标

---

## 五、建议的下一步优先级

### P0：排查 RVC + index 崩溃

优先做：

1. 最小化测试：单独加载 `.index` 文件，看是否直接崩溃
2. 重新构建 index 文件，确认是否是旧索引损坏
3. 排查 `faiss-cpu` 与当前 Apple Silicon / numpy 版本兼容性
4. 若无解，考虑暂时放弃 index 检索路线，只把 RVC 作为“可训练但检索不稳定”的备选方案

### P1：推进 ACE-Step 冒烟与单句验证

按 `poc-b-validation-plan.md` 执行：

- exp-11：安装/启动冒烟测试
- exp-12：单句歌词替换质量验证

### P2：固化人声预处理脚本

目标：

- 一个稳定脚本完成：分离 → 去混响/去回声 → 标准化输出
- 保留全部中间产物，便于后续训练和对比

### P3：SoulX-Singer 并行验证

- 选择与 ACE-Step 相同的 30 秒素材
- 用同一段歌词做主观对比
- 为最终方案选型提供依据

---

## 六、当前状态总览（简表）

| 模块 | 当前状态 | 结论 |
|------|----------|------|
| PoC-A 声音替换 | ✅ 已完成 | 端到端可跑通 |
| seed-vc Zero-shot | ⚠️ 已验证 | 同性别可用，跨性别不足 |
| RVC 训练 | ✅ 已完成 | 同/跨性别模型均已产出 |
| RVC 推理（无 index） | ✅ 可运行 | 更像原唱，目标音色不足 |
| RVC 推理（有 index） | ❌ 崩溃 | segmentation fault，待排障 |
| 人声分离 | ✅ 已稳定 | Demucs 可用 |
| 去混响/去回声 | ⚠️ 部分打通 | 模型名与调用方式已明确，仍待收口 |
| ACE-Step | ⚠️ 环境基本就绪 | 正式实验尚未完成 |
| SoulX-Singer | ⚠️ 已完成调研 | 尚未进入正式对比实验 |

---

## 七、结语

当前项目已经跨过“是否可做”的阶段，进入“哪条路线真正稳定、可交付”的筛选阶段。

最重要的现实判断是：

> **RVC 已证明“训练可以做”，但“检索索引启用后崩溃”使它暂时还不能作为稳定方案直接收敛。**

因此，接下来最值得投入的方向是：

1. **快速判断 RVC index 崩溃是否可修**
2. **并行推进 ACE-Step / SoulX-Singer 的歌词替换主线验证**

---

*本文件用于记录当前阶段性认知，后续可持续更新为阶段周报或 POC 状态报告。*
