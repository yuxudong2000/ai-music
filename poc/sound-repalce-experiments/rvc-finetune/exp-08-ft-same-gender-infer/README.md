# exp-08：同性别 Fine-tune 推理对比

## 目标
使用 exp-07 训练的 RVC 模型推理，与 exp-05（seed-vc Zero-shot）对比音色相似度。

## Source 音频
- 使用 `seed-vc-finetune/exp-07-ft-same-gender-train/` 的源音频（王菲 or 其他女声）

## 推理命令
```python
from rvc.infer.infer import VoiceConverter

vc = VoiceConverter()
vc.convert_audio(
    audio_input_path="source/wangfei_vocal.wav",
    audio_output_path="output/wangfei_to_denglijun_rvc.wav",
    model_path="../exp-07-ft-same-gender-train/rvc-logs/G_200.pth",
    index_path="../exp-07-ft-same-gender-train/rvc-logs/added_IVF*.index",
    pitch=0,
    filter_radius=3,
    index_rate=0.75,
    f0_method="rmvpe",
)
```

## 对比维度
| 维度 | exp-05（seed-vc Zero-shot） | exp-08（RVC Fine-tune） |
|------|---------------------------|------------------------|
| 音色相似度 | ⭐⭐⭐+ | 待验证 |
| 旋律保持 | ✅ | 待验证 |
| 推理速度 | ~2.5×RT | 待验证 |

## 结果
- [ ] 推理完成
- 主观评价：待填写
