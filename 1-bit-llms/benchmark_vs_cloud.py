"""
benchmark_vs_cloud.py — Local Bonsai vs. Anthropic cloud cost/latency comparison
Companion script for: https://aistackinsights.ai/blog/1-bit-llms-bonsai-bitnet-on-device-ai-guide

Usage:
    # Full benchmark (needs ANTHROPIC_API_KEY env var)
    python benchmark_vs_cloud.py --model bonsai-1.7b-q8_0.gguf

    # Local only — no API key required
    python benchmark_vs_cloud.py --model bonsai-1.7b-q8_0.gguf --local-only

    # Specify llama-cli binary location
    python benchmark_vs_cloud.py --model bonsai-1.7b-q8_0.gguf --binary /opt/llama.cpp/llama-cli

Pricing reference (as of 2025):
    claude-haiku-3:  $0.25 / 1M input tokens + $1.25 / 1M output tokens
    Bonsai local:    ~$0.00 / token (electricity marginal cost only)
"""

import argparse
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field

# ── Cloud SDK ──────────────────────────────────────────────────────────────
try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

# ── psutil for optional RAM tracking ──────────────────────────────────────
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


# ---------------------------------------------------------------------------
# Pricing constants
# ---------------------------------------------------------------------------

# Anthropic claude-haiku-3 pricing (USD per 1M tokens)
CLOUD_INPUT_COST_PER_1M  = 0.25
CLOUD_OUTPUT_COST_PER_1M = 1.25

# Local cost: electricity only — negligible per request.
# You can set a custom $/hour for your hardware and threads.
LOCAL_WATT_PER_HOUR = 15.0          # ~15 W for RPi 5 under load
ELECTRICITY_USD_PER_KWH = 0.12      # average US rate


# ---------------------------------------------------------------------------
# Sample prompts covering diverse task types
# ---------------------------------------------------------------------------

SAMPLE_PROMPTS = [
    # (prompt, expected_output_tokens)
    ("What is the capital of Germany?",                              20),
    ("List three benefits of edge AI in one sentence each.",         80),
    ("Translate to French: The model runs entirely offline.",        30),
    ("Summarize in one sentence: 1-bit LLMs store weights as -1, 0, or +1.", 40),
    ("What does RAM stand for?",                                     15),
    ("Give a Python one-liner to reverse a list.",                   25),
    ("Name two open-source 1-bit LLM projects.",                    30),
    ("What is the difference between quantization and pruning?",    80),
    ("Explain latency vs. throughput in one sentence.",              40),
    ("Why is on-device AI better for privacy?",                     60),
]


# ---------------------------------------------------------------------------
# Result data structures
# ---------------------------------------------------------------------------

@dataclass
class RequestResult:
    prompt: str
    output: str
    input_tokens: int
    output_tokens: int
    latency_sec: float
    tokens_per_sec: float
    cost_usd: float
    error: str = ""


@dataclass
class BenchmarkSummary:
    backend: str
    results: list[RequestResult] = field(default_factory=list)

    @property
    def success_count(self) -> int:
        return sum(1 for r in self.results if not r.error)

    @property
    def avg_latency(self) -> float:
        valid = [r.latency_sec for r in self.results if not r.error]
        return sum(valid) / len(valid) if valid else 0.0

    @property
    def avg_tps(self) -> float:
        valid = [r.tokens_per_sec for r in self.results if not r.error]
        return sum(valid) / len(valid) if valid else 0.0

    @property
    def total_cost(self) -> float:
        return sum(r.cost_usd for r in self.results)

    @property
    def total_input_tokens(self) -> int:
        return sum(r.input_tokens for r in self.results)

    @property
    def total_output_tokens(self) -> int:
        return sum(r.output_tokens for r in self.results)

    def cost_per_1m_output(self) -> float:
        """Effective cost per 1M output tokens across all requests."""
        if self.total_output_tokens == 0:
            return 0.0
        return (self.total_cost / self.total_output_tokens) * 1_000_000


# ---------------------------------------------------------------------------
# Local Bonsai runner
# ---------------------------------------------------------------------------

def run_local(
    prompt: str,
    model_path: str,
    binary: str = "llama-cli",
    max_tokens: int = 128,
    threads: int = 4,
) -> RequestResult:
    """
    Run a single prompt against the local Bonsai model via llama-cli subprocess.

    Cost is computed from wall-clock time × estimated watt-hours.
    """
    cmd = [
        binary,
        "-m", model_path,
        "-p", prompt,
        "-n", str(max_tokens),
        "--temp", "0.3",
        "-t", str(threads),
        "--no-display-prompt",
        "-e",
    ]

    # Rough token estimate for input (whitespace split)
    input_tokens = len(prompt.split())

    start = time.perf_counter()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        elapsed = time.perf_counter() - start

        if result.returncode != 0:
            return RequestResult(
                prompt=prompt, output="", input_tokens=input_tokens,
                output_tokens=0, latency_sec=elapsed, tokens_per_sec=0.0,
                cost_usd=0.0, error=result.stderr[:200],
            )

        output = result.stdout.strip()
        output_tokens = len(output.split())
        tps = output_tokens / elapsed if elapsed > 0 else 0.0

        # Cost: electricity (W × hours × $/kWh)
        hours = elapsed / 3600
        cost = (LOCAL_WATT_PER_HOUR / 1000) * hours * ELECTRICITY_USD_PER_KWH

        return RequestResult(
            prompt=prompt, output=output,
            input_tokens=input_tokens, output_tokens=output_tokens,
            latency_sec=elapsed, tokens_per_sec=tps, cost_usd=cost,
        )

    except subprocess.TimeoutExpired:
        elapsed = time.perf_counter() - start
        return RequestResult(
            prompt=prompt, output="", input_tokens=input_tokens,
            output_tokens=0, latency_sec=elapsed, tokens_per_sec=0.0,
            cost_usd=0.0, error="timeout",
        )


# ---------------------------------------------------------------------------
# Cloud (Anthropic) runner
# ---------------------------------------------------------------------------

def run_cloud(
    prompt: str,
    client: "anthropic.Anthropic",
    model: str = "claude-haiku-3-20240307",
    max_tokens: int = 128,
) -> RequestResult:
    """
    Run a single prompt against the Anthropic API and measure cost + latency.

    Cost formula:
        (input_tokens / 1M) × $0.25  +  (output_tokens / 1M) × $1.25
    """
    start = time.perf_counter()
    try:
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        elapsed = time.perf_counter() - start

        output = response.content[0].text if response.content else ""
        input_tokens  = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        tps = output_tokens / elapsed if elapsed > 0 else 0.0

        cost = (
            (input_tokens  / 1_000_000) * CLOUD_INPUT_COST_PER_1M +
            (output_tokens / 1_000_000) * CLOUD_OUTPUT_COST_PER_1M
        )

        return RequestResult(
            prompt=prompt, output=output,
            input_tokens=input_tokens, output_tokens=output_tokens,
            latency_sec=elapsed, tokens_per_sec=tps, cost_usd=cost,
        )

    except Exception as exc:
        elapsed = time.perf_counter() - start
        return RequestResult(
            prompt=prompt, output="", input_tokens=0,
            output_tokens=0, latency_sec=elapsed, tokens_per_sec=0.0,
            cost_usd=0.0, error=str(exc)[:200],
        )


# ---------------------------------------------------------------------------
# Report printer
# ---------------------------------------------------------------------------

COL = {
    "prompt":   40,
    "latency":  10,
    "tps":      10,
    "cost":     14,
    "status":   8,
}

def _header(backend: str) -> None:
    w = sum(COL.values()) + len(COL) * 3
    print(f"\n{'─' * w}")
    print(f"  Backend: {backend}")
    print(f"{'─' * w}")
    print(
        f"  {'Prompt':<{COL['prompt']}} "
        f"{'Latency':>{COL['latency']}} "
        f"{'Tok/s':>{COL['tps']}} "
        f"{'Cost (USD)':>{COL['cost']}} "
        f"{'Status':<{COL['status']}}"
    )
    print(f"{'─' * w}")


def _row(r: RequestResult) -> None:
    prompt_short = (r.prompt[:37] + "...") if len(r.prompt) > 40 else r.prompt
    status = "✓" if not r.error else f"ERR"
    cost_str = f"${r.cost_usd:.6f}"
    print(
        f"  {prompt_short:<{COL['prompt']}} "
        f"{r.latency_sec:>{COL['latency']}.2f}s "
        f"{r.tokens_per_sec:>{COL['tps']}.1f} "
        f"{cost_str:>{COL['cost']}} "
        f"{status:<{COL['status']}}"
    )


def print_summary(local: BenchmarkSummary, cloud: BenchmarkSummary | None) -> None:
    print("\n" + "═" * 72)
    print("  SUMMARY — Local Bonsai  vs.  Cloud (claude-haiku-3)")
    print("═" * 72)
    print(f"  {'Metric':<30} {'Local Bonsai':>18} {'Cloud API':>18}")
    print(f"  {'─' * 66}")

    def fmt(val: float | str, suffix: str = "") -> str:
        if isinstance(val, float):
            return f"{val:.4f}{suffix}"
        return str(val)

    cloud_latency = fmt(cloud.avg_latency, "s") if cloud else "N/A"
    cloud_tps     = fmt(cloud.avg_tps, " tok/s") if cloud else "N/A"
    cloud_total   = fmt(cloud.total_cost) if cloud else "N/A"
    cloud_per1m   = fmt(cloud.cost_per_1m_output()) if cloud else "N/A"

    rows = [
        ("Avg latency / request",
            f"{local.avg_latency:.4f}s", cloud_latency),
        ("Avg tokens / second",
            f"{local.avg_tps:.1f} tok/s", cloud_tps),
        ("Total cost (10 prompts)",
            f"${local.total_cost:.6f}", f"${cloud.total_cost:.6f}" if cloud else "N/A"),
        ("Effective $/1M output tokens",
            f"~${local.cost_per_1m_output():.4f}", f"${cloud.cost_per_1m_output():.4f}" if cloud else "N/A"),
        ("Requires internet",
            "No", "Yes"),
        ("Data leaves device",
            "No", "Yes"),
        ("API key needed",
            "No", "Yes"),
    ]

    for label, lval, cval in rows:
        print(f"  {label:<30} {lval:>18} {cval:>18}")

    print("═" * 72)
    if cloud:
        ratio = cloud.total_cost / max(local.total_cost, 1e-9)
        print(f"\n  💡 Cloud cost is ~{ratio:.0f}× higher than local electricity cost.")
    print(
        "  💡 Local latency depends heavily on hardware — RPi 5 is slower than a laptop.\n"
        "  💡 Cloud latency includes network round-trip.\n"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark local Bonsai vs. Anthropic cloud API"
    )
    parser.add_argument(
        "--model", required=True,
        help="Path to GGUF model file (e.g. bonsai-1.7b-q8_0.gguf)"
    )
    parser.add_argument(
        "--binary", default="llama-cli",
        help="Path to llama-cli binary (default: llama-cli)"
    )
    parser.add_argument(
        "--threads", type=int, default=4,
        help="CPU threads for local inference (default: 4)"
    )
    parser.add_argument(
        "--max-tokens", type=int, default=128,
        help="Max output tokens per request (default: 128)"
    )
    parser.add_argument(
        "--local-only", action="store_true",
        help="Skip cloud benchmark (no API key needed)"
    )
    parser.add_argument(
        "--cloud-model", default="claude-haiku-3-20240307",
        help="Anthropic model to benchmark against (default: claude-haiku-3-20240307)"
    )
    args = parser.parse_args()

    # ── Validate model path ───────────────────────────────────────────────
    if not os.path.exists(args.model):
        print(f"ERROR: Model file not found: {args.model}", file=sys.stderr)
        sys.exit(1)

    # ── Setup cloud client ────────────────────────────────────────────────
    cloud_client = None
    if not args.local_only:
        if not HAS_ANTHROPIC:
            print("WARNING: 'anthropic' package not installed. Run: pip install anthropic")
            print("         Falling back to --local-only mode.\n")
            args.local_only = True
        else:
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                print("WARNING: ANTHROPIC_API_KEY not set. Use --local-only or set the env var.")
                print("         Falling back to --local-only mode.\n")
                args.local_only = True
            else:
                cloud_client = anthropic.Anthropic(api_key=api_key)

    # ── Run local benchmark ───────────────────────────────────────────────
    local_summary = BenchmarkSummary(backend=f"Bonsai local  ({args.model})")
    _header(local_summary.backend)

    for prompt, _ in SAMPLE_PROMPTS:
        r = run_local(prompt, args.model, args.binary, args.max_tokens, args.threads)
        local_summary.results.append(r)
        _row(r)

    # ── Run cloud benchmark ───────────────────────────────────────────────
    cloud_summary: BenchmarkSummary | None = None
    if not args.local_only and cloud_client:
        cloud_summary = BenchmarkSummary(backend=f"Anthropic  ({args.cloud_model})")
        _header(cloud_summary.backend)

        for prompt, _ in SAMPLE_PROMPTS:
            r = run_cloud(prompt, cloud_client, args.cloud_model, args.max_tokens)
            cloud_summary.results.append(r)
            _row(r)

    # ── Print summary table ───────────────────────────────────────────────
    print_summary(local_summary, cloud_summary)


if __name__ == "__main__":
    main()
