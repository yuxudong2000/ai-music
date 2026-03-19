# exp-07：同性别 Fine-tune 训练（邓丽君 × RVC）

## 目标
使用邓丽君 5 首歌曲的净化人声训练 RVC v2 模型，验证能否提升音色相似度（对应 G-1）。

## 训练数据
使用 `seed-vc-finetune/exp-07-ft-same-gender-train/training-data/clean-vocals/` 的数据：
- 共 5 首歌，约 22 分钟净化人声
- 已经过 Demucs htdemucs + bleedless 二次净化

## 训练参数
| 参数 | 值 |
|------|-----|
| model_name | denglijun_rvc |
| total_epoch | 200 |
| batch_size | 4 |
| f0_method | rmvpe |
| sample_rate | 40000 |
| version | v2 |

## 训练命令
```bash
cd poc/sound-repalce-experiments/rvc-finetune
bash run_train.sh denglijun_rvc
```

## 产出
- `rvc-logs/G_200.pth`（训练模型）
- `rvc-logs/added_*.index`（FAISS 索引）

## 结果
- [ ] 训练完成
- Loss 收敛情况：待填写
- 模型大小：待填写
- 耗时：待填写
