import pytest

torch = pytest.importorskip("torch")
from blindmath.model import GPT, ModelConfig  # noqa: E402


def test_forward_loss_and_generate():
    cfg = ModelConfig(vocab_size=50, n_layer=2, n_head=2, d_model=32, d_ff=64, max_seq_len=16)
    m = GPT(cfg)
    x = torch.randint(0, 50, (2, 16))
    logits, loss = m(x, x)
    assert logits.shape == (2, 16, 50) and loss.item() > 0
    out = m.generate(x[:1, :4], 6)
    assert out.shape == (1, 10)


def test_causality():
    cfg = ModelConfig(vocab_size=50, n_layer=2, n_head=2, d_model=32, d_ff=64, max_seq_len=16)
    m = GPT(cfg).eval()
    a = torch.randint(0, 50, (1, 8)); b = a.clone(); b[0, -1] = (b[0, -1] + 1) % 50
    la, _ = m(a); lb, _ = m(b)
    assert torch.allclose(la[:, :-1], lb[:, :-1], atol=1e-5)   # earlier positions never see the future


def test_kv_cache_matches_full_forward():
    cfg = ModelConfig(vocab_size=50, n_layer=2, n_head=2, d_model=32, d_ff=64, max_seq_len=24)
    m = GPT(cfg).eval()
    prompt = torch.randint(0, 50, (1, 5))
    out = m.generate(prompt, 10)                       # cached greedy decoding
    ids = prompt
    for _ in range(10):                                # reference: full recompute each step
        lg, _ = m(ids)
        ids = torch.cat([ids, lg[:, -1].argmax(-1, keepdim=True)], dim=1)
    assert torch.equal(out, ids)
