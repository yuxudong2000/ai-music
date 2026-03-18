# PoC 验证结果总结

> **日期**：2026-03-18  
> **验证范围**：PoC-A（声音替换 — Demucs + seed-vc）  
> **运行环境**：macOS Apple Silicon M2 Pro · Python 3.10 · PyTorch MPS  
> **状态**：✅ 流程跑通，⚠️ 音色相似度待提升

---

## 一、验证目标

验证技术预研文档中 **能力二（声音替换）** 的完整技术链路：

```
源歌曲 MP3 → Demucs 人声分离 → seed-vc 声音转换（Zero-shot）→ 音频混合 → 输出
```

核心验证点：
1. Demucs 能否在 Apple Silicon MPS 上高效分离人声/伴奏？
2. seed-vc 能否在 Apple Silicon MPS 上完成歌唱声音转换（SVC）？
3. 端到端流程的输出音频质量是否满足基本可用标准？

---

## 二、测试数据

### 2.1 TTS 合成测试音频（冒烟测试）

| 文件 | 说明 | 时长 |
|------|------|------|
| `poc/audio/source_voice.wav` | TTS 合成的源语音 | ~5s |
| `poc/audio/target_reference.wav` | TTS 合成的目标参考语音 | ~5s |

### 2.2 真实歌曲（正式测试）

| 文件 | 说明 | 时长 | 采样率 |
|------|------|------|--------|
| `poc/audio/source.mp3` | 源歌曲 | 241s (4分01秒) | 44100Hz 立体声 |
| `poc/audio/target.mp3` | 目标歌手歌曲 | 252s (4分12秒) | 44100Hz 立体声 |

---

## 三、各模块验证结果

### 3.1 M-1：Demucs 人声分离 ✅ 通过

| 指标 | TTS 测试 | 真实歌曲 |
|------|---------|---------|
| **模型** | htdemucs | htdemucs |
| **设备** | MPS（Apple Silicon GPU） | MPS |
| **处理时长** | < 1s | ~23-24s |
| **实时因子** | ~5× 实时 | ~10× 实时 |
| **输出质量** | 完整分离 | 人声与伴奏分离效果良好，但有轻微伴奏泄漏 |

**结论**：Demucs htdemucs 在 Apple Silicon MPS 上运行稳定高效，分离质量满足后续处理要求。

**已知问题**：
- 分离后的人声音轨中仍存在轻微伴奏残留（bleed），当该音轨用作 seed-vc 的目标参考音频时，会影响 Speaker Embedding 的纯净度，进而降低音色转换的相似度
- 尝试使用 `audio-separator`（UVR MDX-Net 模型）对人声做二次净化，但因网络下载模型文件不稳定未完成验证

---

### 3.2 M-2：seed-vc 声音转换 ⚠️ 有条件通过

#### 3.2.1 TTS 冒烟测试 ✅

| 指标 | 结果 |
|------|------|
| **模型** | seed-uvit-whisper-small-wavenet |
| **模式** | VC（普通音色转换，`--f0-condition False`） |
| **扩散步数** | 10 |
| **设备** | MPS |
| **RTF** | 1.52× |
| **输出** | `poc/output/final_poc_a.mp3` |

#### 3.2.2 真实歌曲测试

进行了多组参数对比实验：

| 实验 | 模式 | f0-condition | 扩散步数 | cfg-rate | RTF | 输出文件 |
|------|------|-------------|---------|----------|-----|---------|
| ① | VC | False | 30 | 0.7 | 3.08× | `final_voice_replace.mp3` |
| ② | VC + 音量修复 | False | 30 | 0.7 | 3.08× | `final_voice_replace_v2.mp3` |
| ③ | **SVC** | **True** | 30 | 0.7 | 6.28× | `final_svc_v1.mp3` |
| ④ | SVC | True | 30 | **0.8** | 2.55× | `compare_cfg08.mp3` |

#### 3.2.3 关键发现

**Bug 修复 — MPS float64 兼容性**：
- `--f0-condition True`（SVC 歌唱模式）在 MPS 上崩溃：`TypeError: Cannot convert a MPS Tensor to float64 dtype`
- 根因：`inference.py` 第 329-330 行 `torch.from_numpy(F0).to(device)` 中 numpy 默认 float64，MPS 不支持
- 修复：添加 `.float()` 强制转为 float32：`torch.from_numpy(F0).float().to(device)`
- 修复后 SVC 模式在 MPS 上正常运行

**Bug 修复 — 音量不平衡**：
- seed-vc 输出人声音量极低（-40 dBFS），而原始人声 -16.3 dBFS、伴奏 -19.6 dBFS
- 差距达 **23.8 dB**，直接混合后人声几乎听不到
- 修复：`mix_real.py` 新增 RMS 音量匹配，将转换后人声的响度对齐到原始人声的 RMS 电平

**音色相似度评估**：
- VC 模式（f0-condition=False）：音色与目标有明显差异，不适合歌唱场景
- **SVC 模式**（f0-condition=True）：音色相似度有所提升，但仍与目标存在可感知差距
- cfg-rate 从 0.7 提高到 0.8：音色更贴近目标参考，但差异仍然存在
- 主要瓶颈：**Zero-shot 模式 + 伴奏泄漏的参考音频** 限制了音色还原上限

---

### 3.3 音频混合 ✅ 通过

| 指标 | 结果 |
|------|------|
| **工具** | pydub (AudioSegment) |
| **混合策略** | overlay（叠加） + RMS 音量匹配 |
| **时长对齐** | 以伴奏为基准，人声不足补静音/超出截断 |
| **输出格式** | MP3 320kbps |

---

## 四、端到端性能数据

以真实歌曲（241s / 4分01秒）为基准：

| 步骤 | 耗时 | RTF |
|------|------|-----|
| Demucs 人声分离（MPS） | ~23s | ~10× 实时 |
| seed-vc SVC 推理（MPS, 30步, cfg=0.8） | ~632s (~10.5min) | 2.55× |
| pydub 音频混合 | < 5s | 即时 |
| **端到端总耗时** | **~660s (~11min)** | **~2.7× 实时** |

> 注：seed-vc 推理是性能瓶颈，占总耗时 95% 以上

---

## 五、遗留问题与风险

| 编号 | 问题 | 严重度 | 状态 | 说明 |
|------|------|--------|------|------|
| P-1 | **音色相似度不足** | 🔴 高 | 待解决 | Zero-shot 模式下音色还原有上限；需评估 fine-tune 模式或换用 RVC 方案 |
| P-2 | **参考音频伴奏泄漏** | 🟡 中 | 待解决 | Demucs 分离后的 target vocals 有伴奏残留，污染 Speaker Embedding |
| P-3 | **环境兼容性破坏** | 🔴 高 | 待修复 | 安装 `audio-separator` 后 torch 被升级为 2.10.0，torchaudio 二进制不兼容，Demucs CLI 无法运行 |
| P-4 | **模型下载不稳定** | 🟡 中 | 已缓解 | HuggingFace/GitHub 模型下载经常超时；已通过 `hf-mirror.com` 缓解，但部分大模型仍下载失败 |
| P-5 | **推理速度偏慢** | 🟡 中 | 可接受 | 4分钟歌曲需 ~11 分钟处理（SVC 模式），用户体验一般但可接受 |

---

## 六、结论与建议

### 6.1 PoC-A 结论

| 验证项 | 结论 |
|--------|------|
| Demucs 人声分离 | ✅ **完全满足要求**，MPS 加速效果好，质量稳定 |
| seed-vc Zero-shot 推理 | ⚠️ **流程跑通，但音色相似度不满足"声音替换"的用户期望** |
| 端到端流程 | ✅ **技术链路完整可用**，音频格式/时长/混合均正常 |
| Apple Silicon 兼容性 | ⚠️ **基本兼容，但存在 MPS float64 等坑需要逐个修复** |

### 6.2 下一步建议

**短期（P0 — 修复环境）**：
1. 修复 `torch` / `torchaudio` 版本兼容性问题（回退 torch 到 2.8.0 或升级 torchaudio）
2. 将 seed-vc 的 MPS float64 修复提交到上游仓库或在本项目中记录补丁

**中期（P1 — 提升音色质量）**：
3. **验证 seed-vc Fine-tune**：用 target 人声数据做少量训练（100-500 步），评估音色相似度提升幅度 ← 这是技术预研文档中已规划的核心路径
4. **验证 RVC v2 Fine-tune**：作为 seed-vc 的备选方案，RVC 社区生态更成熟，Fine-tune 流程更简单
5. **人声二次净化**：解决 audio-separator 的模型下载问题，用 MDX-Net/MelBand Roformer 模型对 Demucs 分离的人声做二次净化，提升 Speaker Embedding 纯净度

**长期（P2 — PoC-B）**：
6. 启动 PoC-B 验证"歌词替换与合成"（能力四），这是技术风险最高的模块

---

## 七、产出文件清单

### 7.1 代码

| 文件 | 说明 |
|------|------|
| `poc/poc_a_voice_replace.py` | PoC-A 完整流程脚本（Demucs + seed-vc + pydub） |
| `poc/mix_real.py` | 真实歌曲混合脚本（含 RMS 音量匹配） |
| `poc/generate_source.py` | TTS 生成测试源音频 |
| `poc/generate_target.py` | TTS 生成测试目标音频 |

### 7.2 音频输出

| 文件 | 说明 |
|------|------|
| `poc/output/final_poc_a.mp3` | TTS 冒烟测试输出 |
| `poc/output/real/final_voice_replace.mp3` | 真实歌曲 VC 模式（未修音量） |
| `poc/output/real/final_voice_replace_v2.mp3` | 真实歌曲 VC 模式（已修音量） |
| `poc/output/real/final_svc_v1.mp3` | 真实歌曲 SVC 模式（cfg=0.7） |
| `poc/output/real/compare_cfg07.mp3` | 对比：SVC cfg=0.7 |
| `poc/output/real/compare_cfg08.mp3` | 对比：SVC cfg=0.8 |

### 7.3 修复补丁

| 位置 | 说明 |
|------|------|
| `seed-vc/inference.py` L329-330 | `.float()` 修复 MPS float64 兼容性 |
| `poc/mix_real.py` `match_rms()` | RMS 音量匹配修复 |

---

*文档结束*
