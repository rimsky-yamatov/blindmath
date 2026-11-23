from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass
class ModelConfig:
    vocab_size: int = 1024
    n_layer: int = 6
    n_head: int = 6
    d_model: int = 384
    d_ff: int = 1024          # SwiGLU hidden size
    max_seq_len: int = 512
    dropout: float = 0.0
    rope_base: float = 10000.0
    tie_embeddings: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


# Random-initialised from scratch; pick by hardware.
PRESETS = {
    "tiny":  dict(n_layer=2, n_head=4, d_model=128, d_ff=344,  max_seq_len=256),   # CPU smoke tests
    "mini":  dict(n_layer=4, n_head=4, d_model=256, d_ff=688,  max_seq_len=320),   # ~3.5M params, CPU-trainable
    "small": dict(n_layer=6, n_head=6, d_model=384, d_ff=1024, max_seq_len=512),   # laptop GPU / strong CPU
    "base":  dict(n_layer=12, n_head=12, d_model=768, d_ff=2048, max_seq_len=1024),  # single desktop GPU
}


def make_config(preset: str, vocab_size: int, **overrides) -> ModelConfig:
    cfg = ModelConfig(vocab_size=vocab_size, **PRESETS[preset])
    for k, v in overrides.items():
        setattr(cfg, k, v)
    return cfg
