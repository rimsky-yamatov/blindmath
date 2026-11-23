"""Decoder-only Transformer (RMSNorm, RoPE, SwiGLU, causal attention), random init, from scratch."""
from __future__ import annotations

import math

import torch
import torch.nn as nn
import torch.nn.functional as F

from .config import ModelConfig


class RMSNorm(nn.Module):
    def __init__(self, dim: int, eps: float = 1e-6):
        super().__init__()
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(dim))

    def forward(self, x):
        xf = x.float()
        out = xf * torch.rsqrt(xf.pow(2).mean(-1, keepdim=True) + self.eps)
        return (out * self.weight.float()).type_as(x)


def rope_tables(seq_len: int, head_dim: int, base: float, device):
    inv = 1.0 / (base ** (torch.arange(0, head_dim, 2, device=device).float() / head_dim))
    t = torch.arange(seq_len, device=device).float()
    freqs = torch.outer(t, inv)                      # (T, hd/2)
    return freqs.cos(), freqs.sin()


def apply_rope(x, cos, sin):
    # x: (B, H, T, hd); rotate pairs (even, odd)
    x1, x2 = x[..., 0::2], x[..., 1::2]
    cos, sin = cos[None, None, : x.size(2)], sin[None, None, : x.size(2)]
    out = torch.stack((x1 * cos - x2 * sin, x1 * sin + x2 * cos), dim=-1)
    return out.flatten(-2).type_as(x)


class Attention(nn.Module):
    def __init__(self, cfg: ModelConfig):
        super().__init__()
        assert cfg.d_model % cfg.n_head == 0
        self.n_head, self.hd = cfg.n_head, cfg.d_model // cfg.n_head
        self.qkv = nn.Linear(cfg.d_model, 3 * cfg.d_model, bias=False)
        self.proj = nn.Linear(cfg.d_model, cfg.d_model, bias=False)
        self.dropout = cfg.dropout

    def forward(self, x, cos, sin, past=None):
        """past = (k, v) of earlier positions (inference only). Returns (out, present)."""
        B, T, C = x.shape
        q, k, v = self.qkv(x).view(B, T, 3, self.n_head, self.hd).permute(2, 0, 3, 1, 4)
        q, k = apply_rope(q, cos, sin), apply_rope(k, cos, sin)   # cos/sin already offset to absolute positions
        if past is not None:
            k, v = torch.cat([past[0], k], dim=2), torch.cat([past[1], v], dim=2)
            y = F.scaled_dot_product_attention(q, k, v, is_causal=False)   # single new token sees all past
        else:
            y = F.scaled_dot_product_attention(q, k, v, is_causal=True,
                                               dropout_p=self.dropout if self.training else 0.0)
        return self.proj(y.transpose(1, 2).reshape(B, T, C)), (k, v)


class SwiGLU(nn.Module):
    def __init__(self, cfg: ModelConfig):
        super().__init__()
        self.w1 = nn.Linear(cfg.d_model, cfg.d_ff, bias=False)
        self.w3 = nn.Linear(cfg.d_model, cfg.d_ff, bias=False)
        self.w2 = nn.Linear(cfg.d_ff, cfg.d_model, bias=False)

    def forward(self, x):
        return self.w2(F.silu(self.w1(x)) * self.w3(x))


class Block(nn.Module):
    def __init__(self, cfg: ModelConfig):
        super().__init__()
        self.n1, self.attn = RMSNorm(cfg.d_model), Attention(cfg)
        self.n2, self.mlp = RMSNorm(cfg.d_model), SwiGLU(cfg)

    def forward(self, x, cos, sin, past=None):
        a, present = self.attn(self.n1(x), cos, sin, past)
        x = x + a
        return x + self.mlp(self.n2(x)), present


class GPT(nn.Module):
    def __init__(self, cfg: ModelConfig):
        super().__init__()
        self.cfg = cfg
        self.tok = nn.Embedding(cfg.vocab_size, cfg.d_model)
        self.blocks = nn.ModuleList(Block(cfg) for _ in range(cfg.n_layer))
        self.norm = RMSNorm(cfg.d_model)
        self.head = nn.Linear(cfg.d_model, cfg.vocab_size, bias=False)
        if cfg.tie_embeddings:
            self.head.weight = self.tok.weight
        self.apply(self._init)                       # random initialisation (no pretrained weights)
        for n, p in self.named_parameters():         # scaled residual projections
            if n.endswith("proj.weight") or n.endswith("w2.weight"):
                nn.init.normal_(p, 0.0, 0.02 / math.sqrt(2 * cfg.n_layer))

    @staticmethod
    def _init(m):
        if isinstance(m, nn.Linear):
            nn.init.normal_(m.weight, 0.0, 0.02)
        elif isinstance(m, nn.Embedding):
            nn.init.normal_(m.weight, 0.0, 0.02)

    def n_params(self) -> int:
        return sum(p.numel() for p in self.parameters())

    def forward(self, idx, targets=None, ignore_index: int = -100):
        B, T = idx.shape
        assert T <= self.cfg.max_seq_len, "sequence longer than max_seq_len"
        x = self.tok(idx)
        cos, sin = rope_tables(T, self.cfg.d_model // self.cfg.n_head, self.cfg.rope_base, idx.device)
        for blk in self.blocks:
            x, _ = blk(x, cos, sin)
        logits = self.head(self.norm(x))
        loss = None
        if targets is not None:
            loss = F.cross_entropy(logits.view(-1, logits.size(-1)).float(), targets.view(-1),
                                   ignore_index=ignore_index)
        return logits, loss

    def _step(self, idx, pasts, offset):
        """Forward `idx` (B, T) whose first token sits at absolute position `offset`, using/updating the KV cache."""
        T = idx.size(1)
        x = self.tok(idx)
        cos, sin = rope_tables(offset + T, self.cfg.d_model // self.cfg.n_head, self.cfg.rope_base, idx.device)
        cos, sin = cos[offset:], sin[offset:]
        new = []
        for i, blk in enumerate(self.blocks):
            x, pr = blk(x, cos, sin, None if pasts is None else pasts[i])
            new.append(pr)
        return self.head(self.norm(x)), new

    @torch.no_grad()
    def generate(self, idx, max_new_tokens: int, temperature: float = 0.0, top_k: int | None = None,
                 stop_ids: tuple[int, ...] = ()):
        """Autoregressive sampling with a KV cache; temperature 0 = greedy. Stops at max_seq_len."""
        was_training = self.training
        self.eval()
        idx = idx[:, -self.cfg.max_seq_len:]
        logits, pasts = self._step(idx, None, 0)
        for _ in range(max_new_tokens):
            lg = logits[:, -1, :]
            if temperature <= 0:
                nxt = lg.argmax(-1, keepdim=True)
            else:
                lg = lg / temperature
                if top_k:
                    v, _ = torch.topk(lg, min(top_k, lg.size(-1)))
                    lg = lg.masked_fill(lg < v[:, [-1]], float("-inf"))
                nxt = torch.multinomial(F.softmax(lg, -1), 1)
            idx = torch.cat([idx, nxt], dim=1)
            if (stop_ids and int(nxt[0, 0]) in stop_ids) or idx.size(1) >= self.cfg.max_seq_len:
                break
            logits, pasts = self._step(nxt, pasts, idx.size(1) - 1)
        self.train(was_training)
        return idx
