# BlindMathematics

数学知識だけを学習したAIが、対象問題の名称・歴史・既存研究を一切知らないまま、未知の整数写像の性質を
独立に研究できるかを検証するプロジェクト。最終実験では **関数の定義と主張(Leanの文)だけ** を提示し、
Leanが厳格に受理した証明のみを成功とする。

> 注意: 対象問題は未解決問題です。この基盤で証明が得られる保証はありません。
> このリポジトリが保証するのは「リークがないこと」「成功判定が厳格であること」「途中の発見が全て記録されること」です。

## クイックスタート
```bash
pip install -e ".[dev]"            # torch, numpy, pytest
# Lean 4 (任意だが推奨): elan を入れるか、BLINDMATH_LEAN=/path/to/lean を設定
python -m blindmath.cli build-data --out data/corpus --n 300000 --with-repair   # Phase 2 (監査つき)
python -m blindmath.cli audit data/corpus                                       # 漏洩検査
python -m blindmath.cli train-tokenizer --corpus data/corpus                    # Phase 1
python -m blindmath.cli train --corpus data/corpus --out checkpoints/run0 --preset small --steps 20000
python -m blindmath.cli eval --ckpt checkpoints/run0/latest.pt                  # Phase 4
python -m blindmath.cli phase6 --out runs/phase6                                # Phase 6
python -m blindmath.cli phase7 --ckpt checkpoints/run0/latest.pt --corpus data/corpus --out runs/phase7
```
`scripts/smoke_test.sh` は数分でフルパイプラインを小さく通します。

## 同梱の学習データ(`data/corpus/`、gitには含めずzipに同梱)
- `train.jsonl`(約67.6万件)/ `val.jsonl`(約1.4万件)/ `tokenizer.json`(語彙1024、数字は1桁ずつ)/ `manifest.json` / `quarantine.jsonl`
- 分野: 算術・整数論・Lean証明テンプレ(約15.6万件)・力学系・代数・離散・解析・論理・Leanエラー修復(約1.5千件)。出典は全て自作(CC0相当)
- 再生成: `python -m blindmath.cli build-data --out data/corpus --n 1500000 --seed 20261123 --with-repair --repair-n 1500`
- 漏洩検査: 監査で約2万件を除外済み(`quarantine.jsonl` はメタデータのみで、除外した本文は保存しない)。
  `python -m blindmath.cli audit data/corpus` が0件、独自の生grepでも対象関連語は0件
- Leanコーパスは無作為1,500件をLean 4.15.0で実際にコンパイルし、失敗0件(`python -m blindmath.theorem.verify_corpus`)

## 追加機能と実績(詳細は `docs/results/README.md`、学習手順は `docs/TRAINING.md`)
- 損失は答え・証明部分のみ、KV cache生成、Lean証明ベンチマーク(pass@k)、自己改善(`expert-iter`)、高度なLean証明ファミリー
- CPUで `mini`(3.4M)を2,400ステップ学習済み(`checkpoints/mini_cpu/latest.pt`)。算術ベンチ9.2%、Lean証明pass@1 85%(偏った小規模セット)
- フェーズ7: 対象は証明できず。途中で見つかった定理37件は `docs/results/phase7_mini/theorems/` に記録(全て既存の自動戦略による証明)

## 構成
| パス | 内容 |
|---|---|
| `blindmath/data/` | 合成データ生成器(算術・論理・整数論・代数・離散・解析・力学系・Lean証明)、リーク監査、出典記録 |
| `blindmath/tokenizer/` | 数字を1桁ずつ保つ自作BPE |
| `blindmath/model/` | Decoder-only Transformer(RoPE・RMSNorm・SwiGLU、ランダム初期化) |
| `blindmath/training/` | 8段階カリキュラム、事前学習ループ(再開可能なチェックポイント) |
| `blindmath/evaluation/` | 学習に出ていない問題での完全一致評価 |
| `blindmath/theorem/` | Lean 4連携(厳格受理)、テンプレート検証、**定理ライブラリ** |
| `blindmath/reasoning/` | 軌道・サイクル探索、反例探索、Leanエラーを使う証明修復ループ |
| `blindmath/experiments/` | 台帳(ハッシュ連鎖)、フェーズ6/7、補題発見ループ、対象定義(学習側からは読まれない) |

## 研究ルールの実装
1. **対象問題の情報を学習データに入れない**: `data/audit.py` が名称・文献語・式の構造(`3n+1`型、半分と奇数側のアフィン分岐の組)を検査し、
   該当データは `quarantine.jsonl` に退避。ビルド後に最終ファイルを再監査し、トークナイザ語彙も監査対象。`tests/test_corpus_leak_free.py`。
2. **出典の記録**: 全レコードに `source` / `license` / `generator` / `stage`、`manifest.json` に集計。
3. **事前検索の禁止**: 実験コードはネットワークを使わず、外部AI APIも使わない。
4. **仮説と証明の区別 / 5. 計算と証明の区別**: `experiments/ledger.py` の `kind`(hypothesis / computation / proof_attempt / lean_verified / rediscovery)。
6. **Leanが受理した証明のみ成功**: `sorry`・追加axiom・`native_decide`・文の書き換えを拒否し、`#print axioms` が標準3公理のみであることを確認。
7. **再発見も記録**: `rediscovery` エントリと定理ライブラリの `novelty` 欄。

## 途中で発見した定理の記録
`runs/<name>/theorems/` に保存されます。
- `index.jsonl` / `lean/*.lean`: Leanが厳格に受理した定理(文・証明・証明の出所・使用axiom)
- `conjectures.jsonl`: 予想の状態(`numerically_supported` / `refuted` / `proved`)
- `DISCOVERIES.md`: 一覧(自動生成)
`novelty` は既知カタログに一致する場合のみ `rediscovery`、それ以外は `unclassified`(新規性は自動判定しません)。

## 既知の限界
- 学習データは合成データ(CC0相当、自作)が中心で、教科書由来の自然言語は含みません。
- 小さなモデルでは、Lean証明も演算も高精度にはなりません。`small`/`base` プリセットとGPUを推奨。
