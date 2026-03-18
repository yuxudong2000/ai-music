# exp-04：真实歌曲 SVC 模式 cfg=0.7（保留 F0 旋律）

## 验证目标

切换为 SVC 歌唱模式（f0-condition=True），保留原始 F0 旋律轮廓，验证歌唱场景下的效果。  
同时修复 MPS float64 兼容性 Bug。

## Bug 修复

`seed-vc/inference.py` L329-330：

```python
# 修复前（MPS 崩溃）
F0_ori = torch.from_numpy(F0_ori).to(device)[None]

# 修复后
F0_ori = torch.from_numpy(F0_ori).float().to(device)[None]
```

根因：numpy 默认 float64，MPS 不支持 float64 tensor。

## 参数配置

| 参数 | 值 |
|------|---|
| source | 王菲 - 匆匆那年（女声，241s） |
| target | 邓丽君 - 我只在乎你（女声，252s） |
| **转换模式** | **SVC（f0-condition=True）** |
| **auto-f0-adjust** | **True** |
| 扩散步数 | 30 |
| cfg-rate | 0.7 |
| 音量处理 | RMS 匹配 |

## 文件结构

```
exp-04-real-svc-cfg07/
├── README.md
├── result.md
├── intermediate/
│   └── seed_vc/
│       └── vc_output_svc_cfg07.wav
└── output/
    ├── final_svc_v1.mp3     ← 最终混合输出
    └── compare_cfg07.mp3    ← 同上（对比命名版本）
```
