"""
turboquant_kv_cache.py
Full TurboQuant KV cache implementation: rotation + PolarQuant + QJL error correction
Article: https://aistackinsights.ai/blog/turboquant-kv-cache-compression-zero-accuracy-loss
Paper: https://arxiv.org/abs/2504.19874
"""
import torch, torch.nn.functional as F
from dataclasses import dataclass, field

class KVCacheRotator:
    def __init__(self, head_dim: int, seed: int = 42):
        torch.manual_seed(seed)
        Q, _ = torch.linalg.qr(torch.randn(head_dim, head_dim))
        self.R = Q

    def rotate(self, v: torch.Tensor) -> torch.Tensor:
        return v @ self.R.T


def cartesian_to_polar_quantized(vectors: torch.Tensor, angle_bits: int = 4):
    radii = torch.norm(vectors, dim=-1, keepdim=True)
    unit = F.normalize(vectors, dim=-1)
    angles = torch.acos(unit.clamp(-1 + 1e-7, 1 - 1e-7))
    n = 2 ** angle_bits
    return radii, (angles / torch.pi * n).to(torch.int8)


def polar_to_cartesian(radii: torch.Tensor, angles: torch.Tensor, angle_bits: int = 4) -> torch.Tensor:
    return radii * torch.cos(angles.float() / (2 ** angle_bits) * torch.pi)


class QJLErrorCorrector:
    def __init__(self, head_dim: int, seed: int = 123):
        torch.manual_seed(seed)
        self.projection = torch.randn(head_dim, head_dim).sign()

    def encode(self, error: torch.Tensor) -> torch.Tensor:
        return (error @ self.projection.T).sign().to(torch.int8)

    def correct(self, query: torch.Tensor, sign_bits: torch.Tensor, scale: float = 1.0) -> torch.Tensor:
        return (query @ self.projection * sign_bits.float()).sum(-1) * scale


class TurboQuantKVCache:
    def __init__(self, head_dim: int, angle_bits: int = 4):
        self.rotator = KVCacheRotator(head_dim)
        self.qjl = QJLErrorCorrector(head_dim)
        self.angle_bits = angle_bits
        self.rk, self.ak, self.ek = [], [], []
        self.rv, self.av = [], []

    def store(self, k: torch.Tensor, v: torch.Tensor):
        rk = self.rotator.rotate(k)
        rv = self.rotator.rotate(v)
        radii_k, ang_k = cartesian_to_polar_quantized(rk, self.angle_bits)
        radii_v, ang_v = cartesian_to_polar_quantized(rv, self.angle_bits)
        err = rk - polar_to_cartesian(radii_k, ang_k, self.angle_bits)
        self.rk.append(radii_k); self.ak.append(ang_k)
        self.ek.append(self.qjl.encode(err))
        self.rv.append(radii_v); self.av.append(ang_v)

    def attend(self, query: torch.Tensor) -> torch.Tensor:
        rq = self.rotator.rotate(query)
        scores = []
        for rk, ak, ek in zip(self.rk, self.ak, self.ek):
            k_approx = polar_to_cartesian(rk, ak, self.angle_bits)
            score = (rq * k_approx).sum(-1) + self.qjl.correct(rq, ek)
            scores.append(score)
        weights = torch.softmax(torch.stack(scores, -1), -1)
        vals = torch.stack([polar_to_cartesian(r, a, self.angle_bits)
                            for r, a in zip(self.rv, self.av)], dim=-2)
        return (weights.unsqueeze(-1) * vals).sum(-2)


if __name__ == "__main__":
    D = 128
    cache = TurboQuantKVCache(head_dim=D)
    for i in range(32):
        k = torch.randn(1, D)
        v = torch.randn(1, D)
        cache.store(k, v)
    q = torch.randn(1, D)
    out = cache.attend(q)
    print(f"Output shape: {out.shape}, norm: {out.norm():.4f}")
    bits_stored = 32 * (D + D * 4 / 8 + D / 8)
    bits_fp16 = 32 * 2 * D * 2
    print(f"Compression ratio: {bits_fp16 / bits_stored:.2f}x")
