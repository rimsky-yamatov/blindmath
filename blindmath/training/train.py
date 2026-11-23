"""Pre-training loop: random init, curriculum, cosine LR, grad clip, AMP on GPU, resumable checkpoints."""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import time

import torch

from blindmath.model import GPT, ModelConfig
from blindmath.model.config import make_config
from blindmath.tokenizer import MathTokenizer
from blindmath.training.curriculum import phase_for_step, stage_weights, steps_per_phase
from blindmath.training.data import TokenizedCorpus


def pick_device(name: str = "auto") -> torch.device:
    if name != "auto":
        return torch.device(name)
    if torch.cuda.is_available():
        return torch.device("cuda")
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def lr_at(step: int, total: int, max_lr: float, warmup: int, min_ratio: float = 0.1) -> float:
    if step < warmup:
        return max_lr * (step + 1) / warmup
    p = (step - warmup) / max(1, total - warmup)
    return max_lr * (min_ratio + (1 - min_ratio) * 0.5 * (1 + math.cos(math.pi * p)))


def make_optimizer(model: GPT, lr: float, wd: float) -> torch.optim.Optimizer:
    decay = [p for n, p in model.named_parameters() if p.dim() >= 2]
    no_decay = [p for n, p in model.named_parameters() if p.dim() < 2]
    return torch.optim.AdamW([{"params": decay, "weight_decay": wd}, {"params": no_decay, "weight_decay": 0.0}],
                             lr=lr, betas=(0.9, 0.95))


@torch.no_grad()
def evaluate(model, corpus, device, seq_len, batch_size, n_batches=8, seed=1234) -> float:
    model.eval()
    rng = random.Random(seed)
    w = {s: 1.0 for s in range(1, 9)}
    losses = []
    for _ in range(n_batches):
        x, y = corpus.batch(rng, w, batch_size, seq_len, device)
        _, loss = model(x, y)
        losses.append(loss.item())
    model.train()
    return sum(losses) / len(losses)


def save_checkpoint(path, model, opt, step, cfg: ModelConfig, extra: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    torch.save({"model": model.state_dict(), "opt": opt.state_dict() if opt else None, "step": step,
                "config": cfg.to_dict(), **extra}, tmp)
    os.replace(tmp, path)


def load_model(ckpt_path: str, device="cpu") -> tuple[GPT, dict]:
    ck = torch.load(ckpt_path, map_location=device, weights_only=False)
    model = GPT(ModelConfig(**ck["config"]))
    model.load_state_dict(ck["model"])
    return model.to(device).eval(), ck


def train(args) -> dict:
    device = pick_device(args.device)
    torch.manual_seed(args.seed)
    rng = random.Random(args.seed)
    tok = MathTokenizer.load(args.tokenizer)
    out = args.out
    os.makedirs(out, exist_ok=True)
    tok.save(os.path.join(out, "tokenizer.json"))

    cfg = make_config(args.preset, tok.vocab_size)
    if args.seq_len:
        cfg.max_seq_len = args.seq_len
    model = GPT(cfg).to(device)                 # random init: no pretrained weights anywhere
    if args.init_from:                                  # only for self-play rounds; never pretrained external weights
        model.load_state_dict(torch.load(args.init_from, map_location=device, weights_only=False)["model"])
    opt = make_optimizer(model, args.lr, args.weight_decay)
    start = 0
    latest = os.path.join(out, "latest.pt")
    if args.resume and os.path.exists(latest):
        ck = torch.load(latest, map_location=device, weights_only=False)
        model.load_state_dict(ck["model"]); opt.load_state_dict(ck["opt"]); start = ck["step"]
        print(f"resumed from step {start}")

    mask = not args.no_mask_prompt
    train_c = TokenizedCorpus([os.path.join(args.corpus, "train.jsonl"), *args.extra_train], tok, cfg.max_seq_len, mask)
    val_c = TokenizedCorpus(os.path.join(args.corpus, "val.jsonl"), tok, cfg.max_seq_len, mask)
    plan = steps_per_phase(args.steps)
    use_amp = device.type == "cuda"
    log_path = os.path.join(out, "train_log.jsonl")
    print(f"device={device} params={model.n_params() / 1e6:.2f}M docs={train_c.n_docs} plan={plan}")

    model.train()
    t0, tokens = time.time(), 0
    for step in range(start, args.steps):
        phase = phase_for_step(step, plan)
        lr = lr_at(step, args.steps, args.lr, args.warmup)
        for g in opt.param_groups:
            g["lr"] = lr
        loss_acc = 0.0
        for _ in range(args.grad_accum):
            x, y = train_c.batch(rng, stage_weights(phase), args.batch_size, cfg.max_seq_len, device)
            with torch.autocast(device_type=device.type, dtype=torch.bfloat16, enabled=use_amp):
                _, loss = model(x, y)
            (loss / args.grad_accum).backward()
            loss_acc += loss.item() / args.grad_accum
            tokens += x.numel()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step(); opt.zero_grad(set_to_none=True)

        if (step + 1) % args.log_every == 0 or step + 1 == args.steps:
            rec = {"step": step + 1, "phase": phase, "loss": round(loss_acc, 5), "lr": lr,
                   "tok_per_s": int(tokens / (time.time() - t0))}
            if (step + 1) % args.eval_every == 0 or step + 1 == args.steps:
                rec["val_loss"] = round(evaluate(model, val_c, device, cfg.max_seq_len, args.batch_size), 5)
            print(json.dumps(rec))
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec) + "\n")
        if (step + 1) % args.save_every == 0 or step + 1 == args.steps:
            save_checkpoint(latest, model, opt, step + 1, cfg, {"tokenizer": "tokenizer.json"})
            save_checkpoint(os.path.join(out, f"step_{step + 1:07d}.pt"), model, None, step + 1, cfg,
                            {"tokenizer": "tokenizer.json"})
    return {"steps": args.steps, "out": out}


def add_args(ap: argparse.ArgumentParser):
    ap.add_argument("--corpus", default="data/corpus")
    ap.add_argument("--tokenizer", default="data/corpus/tokenizer.json")
    ap.add_argument("--out", default="checkpoints/run0")
    ap.add_argument("--preset", default="tiny", choices=["tiny", "mini", "small", "base"])
    ap.add_argument("--seq-len", type=int, default=0)
    ap.add_argument("--steps", type=int, default=2000)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--grad-accum", type=int, default=1)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--weight-decay", type=float, default=0.1)
    ap.add_argument("--warmup", type=int, default=100)
    ap.add_argument("--log-every", type=int, default=50)
    ap.add_argument("--eval-every", type=int, default=250)
    ap.add_argument("--save-every", type=int, default=500)
    ap.add_argument("--device", default="auto")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--no-mask-prompt", action="store_true", help="train on the question text too")
    ap.add_argument("--extra-train", nargs="*", default=[], help="more JSONL files (e.g. self-play proofs)")
    ap.add_argument("--init-from", default=None, help="continue from a checkpoint's weights (fresh optimizer)")


if __name__ == "__main__":
    p = argparse.ArgumentParser(); add_args(p); train(p.parse_args())
