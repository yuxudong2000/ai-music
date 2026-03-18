# exp-05：真实歌曲 SVC 模式 cfg=0.8（CFG 强度调优）

## 验证目标

在 exp-04（SVC cfg=0.7）基础上，将 inference-cfg-rate 从 0.7 提升到 0.8，  
验证 Classifier-Free Guidance 强度对音色相似度的影响。

## 背景

`inference-cfg-rate` 控制 CFG（Classifier-Free Guidance）强度：
- 值越高 → 对目标音色的约束越强 → 音色更贴近参考，但可能引入人工痕迹
- 推荐范围：0.7 ~ 0.9

## 参数配置

| 参数 | 值（变更项加粗） |
|------|---|
| source | 王菲 - 匆匆那年（女声，241s） |
| target | 邓丽君 - 我只在乎你（女声，252s） |
| 转换模式 | SVC（f0-condition=True） |
| auto-f0-adjust | True |
| 扩散步数 | 30 |
| **cfg-rate** | **0.8**（exp-04 为 0.7） |
| 音量处理 | RMS 匹配 |

## 文件结构

```
exp-05-real-svc-cfg08/
├── README.md
├── result.md
├── intermediate/
│   └── seed_vc/
│       └── vc_output_svc_cfg08.wav
└── output/
    └── compare_cfg08.mp3
```
