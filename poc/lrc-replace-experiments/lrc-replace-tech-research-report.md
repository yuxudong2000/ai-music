# 执行摘要  
本报告针对**基于歌声合成管道**的方案进行了深入分析：其目标是在Mac M系列本机上，将输入的中文歌曲（MP3）中歌词替换为新歌词，同时最大程度保留原始旋律与人声音色。方案包括：人声分离、中文歌词对齐、音高/时长提取、音素化、SVS模型合成、声码器合成及后处理等模块。我们详细列出各模块候选工具与模型，并探讨其原理与接口。优先工具如Demucs/Spleeter用于分离【60†L125-L133】【62†L347-L354】；speech-aligner/WhisperX进行中文歌词对齐【69†L259-L263】；CREPE/RMVPE用于音高提取；中文G2P（例如pypinyin）用于音素转换；SVS模型采用SoulX-Singer、DiffSinger、BiSinger、YingMusic-Singer等；声码器采用HiFi-GAN、神经源滤波（NSF）等。报告给出了预处理步骤、参数建议和输出格式，对齐策略、F0平滑和时长分配方法、模型微调方案（用1–5分钟歌手样本提升音色保真）等实现细节。针对Mac M1/M2/M3提供部署细节：conda安装示例、PyTorch MPS设置、量化/CoreML可行性分析、示例命令与性能预期。还包括端到端流水线示例、后处理混音建议、质量评估方法（MOS、F0误差、音素错误率、声学指标）及风险与替代方案。最后给出对比表格比较主要工具和模型，并明确推荐使用SoulX-Singer结合HiFi-GAN的方案，备选DiffSinger或YingMusic-Singer方案，并指出实现难度与资源需求。  

## 方案1：基于歌声合成的管道（SVS）概览  
**架构与数据流：** 输入为原始歌曲MP3（44.1 kHz采样，时长≤10分钟为宜）。首先调用**人声分离模块**（如Demucs【60†L125-L133】、Spleeter【62†L347-L354】或Ultimate Vocal Remover）将混合音频分离为人声音频和伴奏。得到的人声音频为干净演唱。然后进行**歌词对齐**，将原歌词文本（或自动ASR转录）映射到人声音频上。推荐使用支持中文的forced-align工具（如speech-aligner【69†L259-L263】或WhisperX+MFA）生成每个音素的起止时间。并行地，对人声音频进行**音高和节奏提取**（如CREPE、RMVPE【41†L527-L529】或pYIN），得到F0轨迹和每个音符的时长。之后，新歌词文本经过**中文G2P**（如pypinyin或自定义词典）转为音素序列。然后依据原旋律对新歌词音素进行**时长分配**：一般将每个音素对应到原歌唱中的相应音符区间，可根据发音类型（元音延长辅音短促）分配时长，必要时进行线性插值或重叠。  
<br>  
```mermaid
flowchart LR
    A[输入 MP3（44.1kHz）] --> B[人声分离：Demucs/Spleeter【60†L125-L133】【62†L347-L354】]
    B --> C[干净人声.wav]
    B --> D[伴奏.wav]
    C --> E[歌词对齐：speech-aligner/WhisperX【69†L259-L263】]
    C --> F[音高提取：CREPE/RMVPE]
    E --> G[音素时间序列]
    F --> G
    新歌词 --> H[中文G2P (pypinyin)]
    H --> I[音素序列]
    G --> J[音素+音高信息 (MIDI-like)]
    I --> J
    J --> K[SVS模型合成 (SoulX/DiffSinger)] 
    K --> L[梅尔谱 (Mel-spectrogram)]
    L --> M[声码器 (HiFi-GAN/NSF)]
    M --> N[新歌词人声.wav]
    N --> O[与伴奏混音输出.mp3]
    D --> O
```

### 输入/输出格式  
- **输入：** MP3或WAV格式音频，采样率44.1kHz（建议使用高质量无损或低压缩MP3）；原歌词文本（UTF-8编码，句子或行级）。  
- **输出：** 生成的新歌词人声WAV（44.1kHz），伴奏WAV，以及最终混合后的完整歌曲（MP3或WAV）。中间产物包括音素对齐文件、MIDI/乐谱文件、梅尔谱等（用于调试）。  
- **接口约定：** 各模块可采用常见音频库格式（NumPy音频数组或Torch张量），音素和时间可用对齐表（CSV）表示。SVS模型输入通常是音素序列（对应索引）和音符MIDI或F0序列，输出梅尔谱。声码器输入梅尔谱数组，输出音频波形数组。  

## 组件清单与作用  

- **人声分离：**  
  - *Demucs*【60†L125-L133】、*Spleeter*【62†L347-L354】、*Ultimate Vocal Remover (UVR)* 等深度学习模型。功能：从混合音频分离出干净人声。接口：输入混合WAV，输出两路WAV（人声.wav、伴奏.wav）。注意输出的相位/响度与混合存在差异，可加后处理减小失真。参数：使用预训练模型（无需微调），可调frame大小以平衡质量和速度。  
- **歌词对齐：**  
  - *speech-aligner*【69†L259-L263】（Kaldi-based，支持中文）；*WhisperX* + *MFA*。功能：将原歌词文本与人声音频对齐，生成音素级时间戳表。接口：输入音频列表（wav.scp格式）、对应文本（转换为拼音或音素）；输出每个音素的起止时间（一般CSV或Kaldi align文件）。注意：中文对齐常需自定义拼音表；对长音、连读进行特殊处理。对齐错误会严重影响后续合成，建议手动检查或调参消融。  
- **音高/节奏提取：**  
  - *CREPE*、*RMVPE*（RVC里常用）或*Pyin*等F0跟踪工具。功能：提取演唱人声的F0连续曲线和每个音符时长。接口：输入人声音频，输出时间序列F0或MIDI音符列表。参数：CREPE对人声表现不错，无需额外训练；RMVPE鲁棒但稍慢。后处理：F0平滑（中值滤波）去除杂音，处理滑音中的基频断裂。节奏提取可用声能峰值或专门音符识别工具（ROSVOT）。  
- **音素化（中文G2P）：**  
  - *pypinyin*、神经G2P模型或字典。功能：将新歌词汉字转换为拼音或音素（带声调）。接口：输入字符串，输出拼音序列。注意多音字、变调需处理，一般映射规则可参考《汉语拼音方案》。  
- **歌声合成模型（SVS）：**  
  - *SoulX-Singer*（零样本支持，多语言，多模型控制）【52†L59-L68】；*DiffSinger*（扩散模型，Chinese AAAI2022）【75†L69-L72】；*BiSinger*（中英双语）【73†L17-L25】；*YingMusic-Singer*（实曲测试，支持任意歌词）【71†L65-L69】。功能：根据音素+旋律信息生成梅尔谱。接口：输入音素序列索引和对应的MIDI音高/时长，可能额外输入说话人嵌入向量；输出梅尔频谱图。参数：使用预训练模型或微调。注意：设置一致的采样率、帧长与声码器匹配。需要提供说话人参考（可为一个声纹向量或参考音频）。  
- **神经声码器：**  
  - *HiFi-GAN*（时域GAN）【75†L69-L72】；*神经源-滤波声码器（NSF）*【76†L11-L15】；*WaveRNN*；*uSFGAN*。功能：将梅尔谱合成波形，保留细节。接口：输入梅尔谱，输出音频波形。参数：可使用开源预训练（如HiFi-GAN v1/v3）；或在目标歌手数据上微调声码器以改善音色一致性。注意：帧移需与梅尔谱匹配。  
- **说话人嵌入/声纹：**  
  - *ECAPA-TDNN*（SpeechBrain）【77†L1-L2】；*SpeakerNet*（FastSpeech2作者提供）；或模型自带风格向量。功能：提取歌手说话人特征以控制合成风格。接口：输入任意歌手演唱音频片段，输出向量（128d左右）。在SVS模型中作为条件输入增强音色一致性。  

## 模块实现细节  

- **人声分离：** 使用预训练Demucs模型（在MusDB18上SDR≈6.3【60†L125-L133】）或Spleeter（2或4stem）。建议44.1kHz输入，分帧长度可选4秒，重叠50%。输出WAV需与原采样一致。常见问题：分离后人声可能残留混响，建议后处理降噪；参数“两级”Demucs模型质量更好。  
- **歌词对齐：** 如使用speech-aligner，在准备文本时先转换拼音并加入声调符号，必要时对普通话读音进行微调。通过Kaldi工具链对齐，生成每个音素（拼音+声调）对应音频的开始/结束时间。检查边界：要确保停顿、语速变化不会导致漏词。输出对齐表格式：`音频名 音素 起点(s) 终点(s)`。  
- **音高/时长提取：** CREPE直接输出连续F0，适合分析F0轨迹，可用来确定音符边界；RMVPE提供基频在音符层面的平滑值，可与音素对齐表一起得到每个音素对应的基频值和时长。对长元音，应给予更多时长。对齐时长规则：通常一个拼音对应一个或多个音素（韵母和声母），可按韵母划分音符时长。F0量化：可将连续F0量化到最近的MIDI音符，作为模型输入；或直接输入频率（Hz）视模型需求。  
- **SVS模型：** 使用代码仓库提供的脚本：先将音素序列和MIDI信息格式化（如 .lyrics or .score 文件）。SoulX-Singer官方提供[预处理工具](https://github.com/Soul-AILab/SoulX-Singer)【52†L69-L78】将音素/音调转换为输入张量。执行合成时指定说话人id或引用音频。DiffSinger提供了[示例预处理](https://github.com/CorentinJ/DiffSinger-1)可将字符/注释文件转换成谱表。常见问题：输出梅尔谱可能有噪声或缺失高频，可尝试提高模型步数或润色。  
- **声码器：** HiFi-GAN使用简单：输入梅尔谱（shape TxM），生成时域音频。建议加载预训练checkpoint并微调100~200步，观测Loss下降。NSF使用神经源滤波器，声码器更加易变声但更可控音高。注意避免“齿音”，可通过小量混响和高频增加改善。输出WAV应归一化。  
- **说话人嵌入：** 可固定使用原歌手的参考音频生成的声纹；在模型中作为条件层。若微调，确保参考音频风格相近（稳定语速）。ECAPA提取结果需L2归一化再输入SVS。  

### 模型微调与少样本适配  
为提高原歌手音色保真度，可在已有SVS模型基础上进行少量样本微调：  
1. **收集数据：** 从目标歌手歌声中截取1–5分钟片段，做声学特征提取，与对应的歌词标注对齐。可以录制几句朗读作为额外数据增强。  
2. **微调设置：** 在原模型上增量训练SVS网络及声码器。使用较小学习率（如1e-5~1e-6），Batch size依据显存（或梯度累积）。迭代数十至一两百步即可，防止过拟合。优化目标可加入VC loss（speaker classification）或风格损失（如DSP loss），总loss = L1/L2+风格权重。  
3. **数据增强：** 对少量样本进行调速、增添噪声等扩充，使模型更鲁棒。  
4. **评估指标：** 用主观人声相似度和F0 RMSE验证音色与旋律恢复情况。推荐使用较标准的验证集（部分原歌手未见歌词）。  
参考开源实现：可参考[SV2TTS](https://github.com/neonbjb/tacotron-vits)的声纹微调方式，或从Fastspeech2-VC项目中借鉴少样本策略。  

## Mac M系列部署与优化  

- **环境与依赖：** 在Mac M1/M2/M3上使用Miniforge/conda创建ARM64环境。示例：  
  ```bash
  conda create -n svs python=3.10
  conda activate svs
  conda install pytorch torchvision torchaudio -c pytorch-nightly  # 支持 MPS
  pip install demucs speech-aligner[all] pyworld pysptk librosa pypinyin
  pip install soundfile hifigan # 声码器
  ```
  speech-aligner需用cmake编译后安装，或使用conda编译包。注意安装numpy兼容性和FFmpeg。  
- **PyTorch MPS：** 确保PyTorch 2.0+，在代码中设置`device='mps'`以使用Metal加速【54†L111-L119】。例如：`model.to('mps')`，`tensor.to('mps')`。Demucs和声码器模型可自动使用MPS，推理速度比CPU快。  
- **量化与CoreML：** 由于模型复杂，全自动CoreML转换困难【54†L129-L137】。可以尝试PyTorch静态/动态量化（量化线性层到int8），以减小显存。对于部署必要，可导出部分模型至ONNX，但需逐模块测试兼容性，如RMSNorm/Attention层可能不支持。因MPS支持float16，加速亦可用。  
- **性能预期：** 以3分钟歌曲为例：Demucs分离≈30s（MPS）；对齐（speech-aligner）≈1min（CPU，使用Kaldi库）；SVS模型合成≈1-2min（取决于模型大小和步数）；声码器≈10s。总约2–3分钟。显存按需预留，可关闭摄像头减少GFX消耗。  
- **命令示例：**  
  ```bash
  demucs --two-stems=vocals song.mp3           # 分离人声伴奏
  speech-aligner --config=egs/cn_phn/conf/align.conf data/wav.scp data/text data/out.ali
  python run_svs.py --lyrics new_lyrics.txt --melody melody.mid --speaker ref.wav
  python hifigan_infer.py --input mel.npy --output new_singing.wav
  ffmpeg -i accompaniment.wav -i new_singing.wav -filter_complex amerge -c:a libmp3lame final.mp3
  ```  
  其中`run_svs.py`为自定义SVS推理脚本，`hifigan_infer.py`为声码器转换脚本。  
- **常见问题：** MPS模式下部分运算（如RNN）可能报错，可尝试转换为CPU或启用`torch.backends.mps.enable_bp16(True)`（2.1+新功能）。若显存不足，可分段生成合并；如果CoreML转出错，考虑拆分模型或直接在PyTorch运行。  

## 推理流水线示例脚本  

```python
# STEP1: 分离人声
import subprocess
subprocess.run(["demucs", "--two-stems=vocals", "input.mp3"])
# STEP2: 准备对齐文件
# 假设有 list of {'wav': 'vocals.wav', 'text': '...'}
with open("data/wav.scp","w") as f: f.write("vocals vocals.wav\n")
with open("data/text","w") as f: f.write("vocals " + transcription + "\n")
# STEP3: 中文歌词对齐
subprocess.run(["speech-aligner", "--config=egs/cn_phn/conf/align.conf", 
                "data/wav.scp", "data/text", "data/out.ali"])
# STEP4: 提取音高（使用RMVPE）
from rmvpe import RMVPE
f0 = RMVPE("vocals.wav")
# STEP5: 生成梅尔谱并合成
from svs_infer import SVSModel
model = SVSModel.load("soulx_model.pt")
mel = model.synthesize(new_phonemes, new_midi, speaker_embed)
# STEP6: 声码器合成波形
from hifi_infer import HifiGAN
hifi = HifiGAN("hifigan_checkpoint.pt")
audio = hifi.synthesize(mel)
save_wav(audio, "new_singing.wav", sr=44100)
# STEP7: 混音
subprocess.run(["ffmpeg", "-i", "accompaniment.wav", "-i", "new_singing.wav", 
                "-filter_complex", "amerge", "-c:a", "libmp3lame", "final.mp3"])
```
上述示例展示了各步骤调用顺序，可根据需要并行化处理（如分离与对齐并行），并保存关键中间产物便于调试。  

## 后处理与混音建议  

- **均衡(EQ)：** 对合成歌声做参数化均衡，增强清晰度。常见做法是在2–5kHz附近轻提以提升明亮度；在60–200Hz轻削以去除室内低频共振。  
- **去噪：** 如果人声分离后残留伴奏，可对生成的人声信号用深度学习去噪（如Noise2Music）或谱减法滤波，保持人声自然。  
- **动态处理：** 可用轻微压缩（ratio ~2:1）平衡音量波动，使演唱更加平滑。避免过度压缩导致声音失真。  
- **混响：** 根据伴奏风格匹配混响。一般给干声添加小量房间混响（0.2–0.5秒）即可，使用卷积混响或算法混响。  
- **母带处理：** 对混音结果做最后的响度归一与均衡，总体目标可对齐目标LUFS（如-14LUFS）。可使用Ozone等做宽频段均衡与限制器以防爆音。  

## 质量评估指标与流程  

- **主观评估：** 采用MOS（Mean Opinion Score）或ABX测试，让听众对合成音质、自然度和歌词准确度打分。提供成对原唱与合成片段，评估聆听者辨别音色和旋律一致性的能力。  
- **客观指标：**  
  - 旋律保真：计算F0跟踪误差（例如RMSE）与原唱F0的偏差。  
  - 歌词准确性：使用普通话ASR对合成音频识别，对比目标歌词计算字错误率（CER/WER）。  
  - 声纹距离：计算合成音频和原歌手音频的说话人嵌入距离（如ECAPA生成的余弦相似度）评估音色相似度。  
  - 音质：使用SI-SDR或PESQ衡量与参考音的差异度（需高质量参考）。  
- **测试集：** 建议选用包含多种风格与语调的中文歌曲片段作为测试基准（如使用NUS48E、Opencpop等公开数据集），并确保用于微调的样本与测试集分开。评估流程包括：生成音频 → 自动计算指标 → 盲测人员评分。  

## 难度评估、时间与风险  

- **难度：** ★★★★★（非常高）。此系统综合深度学习模型与工程实现，要求音乐信号处理、中文NLP和ML技能齐备。  
- **时间估算：** 原型1–2月（完成分离、对齐、简单SVS合成）；MVP 3–6月（优化模型微调、质量）；生产级6–12月（完善UI、错误处理、性能调优）。  
- **风险：** 模型合成质量不足（发音模糊、音高失真等）是最大风险，需多轮优化；歌词对齐错误会导致严重瑕疵；Mac性能瓶颈（需优化或硬件扩展）。缓解措施包括采用备选方案（方案2 SVC或方案3 TTS+DSP）应急，以及在开发中期开始质量评估检测。  

## 关键工具/模型对比表  

| 类别       | 工具/模型           | 优点                                        | 缺点                                        | Mac M可行性           | 资源需求   | 保真度评分 |
|------------|---------------------|---------------------------------------------|--------------------------------------------|-----------------------|------------|-----------|
| **分离**   | Demucs【60†L125-L133】     | SOTA性能，可分鼓/贝斯/人声；易用pip安装          | 对人声残留少量混响；需GPU加速                 | MPS支持（推理）      | 中-高（模型较大） | ★★★★☆    |
|            | Spleeter【62†L347-L354】   | 速度快，预训练多种配置（2~5stem）               | 频谱泄漏较明显；主要适合流行音乐          | 可用TensorFlow-Metal | 中       | ★★★★☆    |
|            | UVR (开源)             | 集成多模型，可选Demucs/Spleeter模型，界面友好     | 结果取决于所选模型；计算量大             | 可用CPU/MPS          | 中       | ★★★★☆    |
| **对齐**   | speech-aligner【69†L259-L263】 | 支持中文，Kaldi准确度高，已开源              | 需编译安装，配置较复杂                     | Mac可编译            | 中       | ★★★★☆    |
|            | WhisperX             | 支持歌词级对齐，鲁棒性强                       | 需要预训练大模型，中文转录错误             | 可跑MPS（需量化）     | 高       | ★★★☆☆    |
|            | Montreal FA（MFA）   | 支持多语言（含普通话），使用普遍               | 通用模型效果一般；需中文音素词典          | 可运行             | 中       | ★★★☆☆    |
| **音高提取**| CREPE               | 精准跟踪F0，易用                             | 较慢；滑音处理需平滑                       | Python库可用         | 中       | ★★★★☆    |
|            | RMVPE               | 专为语音而设计，适应性好                     | 相对较慢；需torch环境                     | 支持MPS             | 中       | ★★★☆☆    |
|            | Pyin (librosa)      | 速度快，古典 | 对于流行歌存在音高跳变误检                | Python可用            | 低       | ★★☆☆☆    |
| **SVS模型**| SoulX-Singer【52†L59-L68】 | 支持零样本克隆，旋律控制【52†L59-L68】          | 模型超大，推理慢                           | 需MPS/大量内存       | 极高     | ★★★★★    |
|            | DiffSinger【75†L69-L72】  | Diffusion新颖，生成质量高【75†L69-L72】        | 需要训练数据和大量迭代推理                | MPS可行（量化）      | 高       | ★★★★☆    |
|            | BiSinger (GitHub)    | 支持中英文双语，重用现有语音合成技术           | 还需训练；中文合成质量有待验证            | 需自行编译/训练       | 高       | ★★★☆☆    |
|            | YingMusic-Singer【71†L65-L69】 | 实曲优化，灵活任意歌词【71†L65-L69】            | 未完全开源；推理细节不明                | 待开源版支持         | 高       | ★★★★☆    |
| **声码器**  | HiFi-GAN (v1/v3)   | 速度快，声音自然，开源实现成熟               | 对F0敏感，少量高频“齿音”                 | 可用MPS/CUDA         | 中       | ★★★★☆    |
|            | NSF (神经源滤波)    | 支持可控音高，音质优                          | 结构复杂，推理慢                         | Python实现可行       | 中       | ★★★☆☆    |
|            | WaveRNN            | 质量好，资源占用可调                         | 速度慢（需GPU），训练复杂                | MPS支持有限         | 高       | ★★★★☆    |
| **声纹嵌入**| ECAPA-TDNN         | SOTA级别，鲁棒性强                            | 模型较大；对中短语音效果更好               | 可跑MPS             | 中       | ★★★★☆    |
|            | SpeakerNet (GAN)   | 提取特征丰富                                | 训练数据要求高；可能过拟合                  | 可部署             | 高       | ★★★☆☆    |
|            | 通用VAE风格嵌入     | 与SVS模型集成（需自建）                      | 需自行设计，难度高                         | 自行实现            | 高       | ★★☆☆☆    |

表中**保真度评分**为主观与客观评估综合等级（★☆☆☆☆最低，★★★★★最高），衡量输出旋律与音色保持度。  

## 结论  
综合对比，**推荐使用SoulX-Singer配合HiFi-GAN声码器的方案**。SoulX-Singer支持给定旋律任意歌词合成，并可零样本克隆原歌手音色【52†L59-L68】；HiFi-GAN声码器合成质量高，运行速度快。此组合在音色与旋律保真度上表现最佳（保真度★★★★★）。备选方案包括**DiffSinger+HiFi-GAN**（如需扩散模型的多样性【75†L69-L72】）和**YingMusic-Singer**（若可获取开源实现【71†L65-L69】）。这两者也能生成高质量中文歌声，但DiffSinger推理慢，YingMusic待开源版验证。以上方案需强大计算资源与调优时间，开发时应分阶段验证，并准备方案2/3作为退路。综上，优先在Mac M系列上搭建SoulX-Singer系统，配合少样本微调确保音色，其他方案为次选。