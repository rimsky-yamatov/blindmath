# 本格学習ガイド

## 規模の目安
| プリセット | パラメータ | 推奨環境 | 目安 |
|---|---|---|---|
| `tiny` | 約0.5M | CPU | 動作確認のみ |
| `mini` | 約3.4M | CPU(1コアで約3.9k tok/s) | この環境で実際に回した設定 |
| `small` | 約11M | ノートGPU / 強いCPU | 数時間〜 |
| `base` | 約85M | デスクトップGPU(12GB以上) | 本格学習。`--grad-accum` でバッチ調整 |

## コマンド例(GPU)
```bash
python -m blindmath.cli build-data --out data/corpus --n 5000000 --seed 1 --with-repair --repair-n 10000   # 同梱版より大きく(シャード分割される)
python -m blindmath.cli train-tokenizer --corpus data/corpus --vocab-size 2048
python -m blindmath.cli train --corpus data/corpus --tokenizer data/corpus/tokenizer.json \
  --out checkpoints/base --preset base --steps 200000 --batch-size 32 --grad-accum 4 --lr 6e-4 --warmup 2000 --resume
python -m blindmath.cli eval --ckpt checkpoints/base/latest.pt
python -m blindmath.cli lean-eval --ckpt checkpoints/base/latest.pt --n 200 --k 16
```
`--resume` を付けておけば、中断しても最新のチェックポイントから再開します。

## 自己改善ループ(Leanが検証した自分の証明で再学習)
```bash
python -m blindmath.cli expert-iter --ckpt checkpoints/base/latest.pt --out data/corpus/self_play.jsonl --n 2000 --k 8
python -m blindmath.cli train ... --extra-train data/corpus/self_play.jsonl --init-from checkpoints/base/latest.pt --out checkpoints/base_r1
```
自己生成データは `source=self_play:<ckpt>` と記録され、監査(`audit`)も通します。

## 損失の設計
問題文(`Q:`)側はコンテキストとして使い、`Work:` / `A:` 以降(推論と答え・証明)のみに損失をかけます(`--no-mask-prompt` で無効化)。
