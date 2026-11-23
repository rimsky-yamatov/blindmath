#!/usr/bin/env bash
# Small end-to-end run (minutes on CPU): data -> audit -> tokenizer -> train -> eval -> phase6/7.
set -euo pipefail
OUT=${1:-/tmp/blindmath_smoke}
python -m blindmath.cli build-data --out "$OUT/corpus" --n 20000 --seed 1
python -m blindmath.cli audit "$OUT/corpus"
python -m blindmath.cli train-tokenizer --corpus "$OUT/corpus" --vocab-size 768
python -m blindmath.cli train --corpus "$OUT/corpus" --tokenizer "$OUT/corpus/tokenizer.json" \
  --out "$OUT/run" --preset tiny --steps 200 --batch-size 8 --log-every 50 --eval-every 100 --save-every 200
python -m blindmath.cli eval --ckpt "$OUT/run/latest.pt" --corpus "$OUT/corpus" --per-domain 5
python -m blindmath.cli phase6 --out "$OUT/phase6" --upper 500
python -m blindmath.cli phase7 --ckpt "$OUT/run/latest.pt" --corpus "$OUT/corpus" --out "$OUT/phase7" \
  --samples 2 --rounds 1 --discover-limit 5 --upper 1000
