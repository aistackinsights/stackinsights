"""
bonsai_inference.py — Python wrapper for BitNet.cpp / llama.cpp Bonsai models
Companion script for: https://aistackinsights.ai/blog/1-bit-llms-bonsai-bitnet-on-device-ai-guide

Model size guidance:
  - Bonsai 400M  → classification, keyword extraction, ultra-low-RAM devices (512 MB+)
  - Bonsai 1.7B  → general text tasks, RPi 5, edge devices (2 GB RAM+)
  - Bonsai 3B    → summarization, light reasoning, laptop/desktop (4 GB RAM+)
  - Bonsai 7B    → complex reasoning, code, powerful edge hardware (8 GB RAM+)
"""

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

# Optional: psutil for RAM measurement (pip install psutil)
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# Optional: BitNet.cpp Python bindings (if installed from source)
try:
    import bitnet  # type: ignore
    HAS_BITNET_BINDINGS = True
except ImportError:
    HAS_BITNET_BINDINGS = False


# ---------------------------------------------------------------------------
# Core inference class
# ---------------------------------------------------------------------------

class BitNetInference:
    """
    Unified wrapper for running 1-bit Bonsai models locally.

    Tries BitNet.cpp Python bindings first; falls back to calling the
    llama.cpp (or BitNet.cpp) CLI binary via subprocess.

    Usage:
        model = BitNetInference(binary_path="/path/to/llama-cli")
        model.load_model("/path/to/bonsai-1.7b-q8_0.gguf")
        reply = model.generate("Explain 1-bit quantization in one sentence.")
        print(reply)
    """

    def __init__(
        self,
        binary_path: str = "llama-cli",
        n_threads: int = 4,
        verbose: bool = False,
    ):
        """
        Args:
            binary_path: Path to the llama-cli (or run_inference.py from BitNet.cpp).
                         Defaults to "llama-cli" (must be on PATH).
            n_threads:   CPU thread count. On RPi 5, 4 threads is a sweet spot.
            verbose:     Print raw subprocess output for debugging.
        """
        self.binary_path = binary_path
        self.n_threads = n_threads
        self.verbose = verbose
        self.model_path: str | None = None

        # If bindings are available, store the bound model object here
        self._bound_model: Any = None

    # ------------------------------------------------------------------
    # Model loading
    # ------------------------------------------------------------------

    def load_model(self, model_path: str) -> None:
        """
        Load a GGUF model from disk.

        For BitNet.cpp bindings: initialises the model in-process.
        For subprocess mode: validates the path and stores it for later calls.

        Args:
            model_path: Path to a .gguf model file.
        """
        model_path = str(Path(model_path).expanduser().resolve())
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found: {model_path}")

        self.model_path = model_path

        if HAS_BITNET_BINDINGS:
            # BitNet.cpp Python bindings path
            print(f"[BitNetInference] Loading via Python bindings: {model_path}")
            self._bound_model = bitnet.LLM(model_path=model_path, n_threads=self.n_threads)
        else:
            # Subprocess fallback — model is loaded on each call (stateless CLI)
            print(f"[BitNetInference] Model set (subprocess mode): {model_path}")

    # ------------------------------------------------------------------
    # Text generation
    # ------------------------------------------------------------------

    def generate(
        self,
        prompt: str,
        max_tokens: int = 256,
        temperature: float = 0.7,
        stop: list[str] | None = None,
    ) -> str:
        """
        Generate text from a prompt.

        Args:
            prompt:     The input prompt string.
            max_tokens: Maximum number of tokens to generate.
            temperature: Sampling temperature (0 = greedy, 1 = creative).
            stop:       List of stop strings (generation halts when any is hit).

        Returns:
            Generated text as a string.
        """
        if self.model_path is None:
            raise RuntimeError("Call load_model() before generate().")

        if HAS_BITNET_BINDINGS and self._bound_model is not None:
            return self._generate_bindings(prompt, max_tokens, temperature)
        else:
            return self._generate_subprocess(prompt, max_tokens, temperature, stop)

    def _generate_bindings(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate via BitNet.cpp Python bindings."""
        result = self._bound_model.generate(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return result.strip()

    def _generate_subprocess(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        stop: list[str] | None,
    ) -> str:
        """
        Generate via subprocess call to llama-cli.

        Constructs a command like:
            llama-cli -m model.gguf -p "prompt" -n 256 --temp 0.7 -t 4
        """
        cmd = [
            self.binary_path,
            "-m", self.model_path,
            "-p", prompt,
            "-n", str(max_tokens),
            "--temp", str(temperature),
            "-t", str(self.n_threads),
            "--no-display-prompt",  # only output the generated text
            "-e",                   # escape newlines in prompt
        ]

        if stop:
            for s in stop:
                cmd += ["--stop", s]

        if self.verbose:
            print(f"[BitNetInference] CMD: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"llama-cli failed (exit {result.returncode}):\n{result.stderr}"
            )

        return result.stdout.strip()

    # ------------------------------------------------------------------
    # Zero-shot classification
    # ------------------------------------------------------------------

    def classify(self, text: str, labels: list[str]) -> dict[str, Any]:
        """
        Zero-shot classification using constrained generation.

        Builds a prompt that forces the model to pick exactly one label
        from the provided list, then parses the response.

        Best model sizes:
          - Bonsai 400M / 1.7B for simple category lists (< 10 labels)
          - Bonsai 3B+ for nuanced or overlapping categories

        Args:
            text:   The input text to classify.
            labels: List of candidate labels.

        Returns:
            {
                "label": "chosen_label",
                "confidence": "high" | "medium" | "low",
                "raw": "<raw model output>"
            }
        """
        label_list = "\n".join(f"  - {lbl}" for lbl in labels)
        prompt = (
            f"Classify the following text into exactly one of these categories:\n"
            f"{label_list}\n\n"
            f"Text: {text}\n\n"
            f"Respond with only the category name, nothing else.\n"
            f"Category:"
        )

        raw = self.generate(prompt, max_tokens=32, temperature=0.0)

        # Find the best matching label
        raw_lower = raw.lower().strip()
        matched = None
        for lbl in labels:
            if lbl.lower() in raw_lower:
                matched = lbl
                break

        # Fallback: pick the first token if no clean match
        if matched is None:
            first_word = raw_lower.split()[0] if raw_lower else ""
            for lbl in labels:
                if first_word.startswith(lbl.lower()[:4]):
                    matched = lbl
                    break

        confidence = "high" if matched and raw_lower.strip() == matched.lower() else "medium"
        if matched is None:
            confidence = "low"
            matched = labels[0]  # safe default

        return {"label": matched, "confidence": confidence, "raw": raw}

    # ------------------------------------------------------------------
    # Structured JSON extraction
    # ------------------------------------------------------------------

    def extract_json(self, text: str, schema: dict[str, str]) -> dict[str, Any]:
        """
        Extract structured data from unstructured text according to a schema.

        Best model sizes:
          - Bonsai 1.7B for flat key-value extraction
          - Bonsai 3B+ for nested structures or ambiguous source text

        Args:
            text:   The unstructured input text.
            schema: Dict mapping field names to their descriptions, e.g.
                    {"name": "person's full name", "email": "email address"}

        Returns:
            Parsed dict with the extracted values, or raw string on parse failure.
        """
        fields = "\n".join(f'  "{k}": <{v}>' for k, v in schema.items())
        prompt = (
            f"Extract the following fields from the text below and return valid JSON only.\n"
            f"Fields:\n{fields}\n\n"
            f"Text:\n{text}\n\n"
            f"JSON output (no explanation, no markdown fences):\n"
        )

        raw = self.generate(prompt, max_tokens=512, temperature=0.0)

        # Strip markdown code fences if the model added them
        cleaned = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Try to find a JSON object in the response
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
            return {"_raw": raw, "_error": "JSON parse failed"}


# ---------------------------------------------------------------------------
# Benchmarking helpers
# ---------------------------------------------------------------------------

def _ram_mb() -> float:
    """Return current process RSS in MB (requires psutil)."""
    if not HAS_PSUTIL:
        return -1.0
    proc = psutil.Process(os.getpid())
    return proc.memory_info().rss / (1024 ** 2)


def benchmark(model: BitNetInference, prompts: list[str]) -> None:
    """
    Run a quick benchmark: tokens/sec and RAM delta.

    Args:
        model:   An already-loaded BitNetInference instance.
        prompts: List of prompt strings to test.
    """
    print("\n" + "=" * 60)
    print("BENCHMARK RESULTS")
    print("=" * 60)

    total_tokens = 0
    total_time = 0.0
    ram_before = _ram_mb()

    for i, prompt in enumerate(prompts, 1):
        start = time.perf_counter()
        output = model.generate(prompt, max_tokens=100, temperature=0.0)
        elapsed = time.perf_counter() - start

        # Rough token count: split on whitespace (good enough for benchmarking)
        tokens = len(output.split())
        tps = tokens / elapsed if elapsed > 0 else 0

        total_tokens += tokens
        total_time += elapsed

        print(f"  [{i:02d}] {elapsed:.2f}s | {tps:.1f} tok/s | {tokens} tokens")
        if model.verbose:
            print(f"       Output: {output[:80]}...")

    ram_after = _ram_mb()
    avg_tps = total_tokens / total_time if total_time > 0 else 0

    print(f"\n  Average: {avg_tps:.1f} tok/s over {len(prompts)} prompts")
    if HAS_PSUTIL:
        print(f"  RAM delta: {ram_after - ram_before:+.1f} MB "
              f"(before={ram_before:.0f} MB, after={ram_after:.0f} MB)")
    else:
        print("  RAM: install psutil for memory tracking  (pip install psutil)")
    print("=" * 60)


# ---------------------------------------------------------------------------
# Main — demo + benchmark
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Bonsai model inference demo")
    parser.add_argument(
        "--model", required=True,
        help="Path to GGUF model file (e.g. bonsai-1.7b-q8_0.gguf)"
    )
    parser.add_argument(
        "--binary", default="llama-cli",
        help="Path to llama-cli binary (default: llama-cli on PATH)"
    )
    parser.add_argument("--threads", type=int, default=4, help="CPU threads")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    # --- Load model ---
    ram_start = _ram_mb()
    print(f"RAM before load: {ram_start:.0f} MB")

    llm = BitNetInference(binary_path=args.binary, n_threads=args.threads, verbose=args.verbose)
    llm.load_model(args.model)

    ram_loaded = _ram_mb()
    print(f"RAM after load:  {ram_loaded:.0f} MB  (delta: {ram_loaded - ram_start:+.0f} MB)")

    # --- Generation demo ---
    print("\n--- Generation ---")
    reply = llm.generate(
        "Explain 1-bit quantization in one sentence.",
        max_tokens=80,
        temperature=0.7,
    )
    print(f"Output: {reply}")

    # --- Classification demo ---
    print("\n--- Classification ---")
    result = llm.classify(
        text="The server crashed after the latest deployment.",
        labels=["bug", "feature request", "documentation", "performance"],
    )
    print(f"Label: {result['label']}  (confidence: {result['confidence']})")

    # --- JSON extraction demo ---
    print("\n--- JSON Extraction ---")
    extracted = llm.extract_json(
        text="Contact Jane Doe at jane.doe@example.com, phone 555-1234.",
        schema={
            "name": "full name of the person",
            "email": "email address",
            "phone": "phone number",
        },
    )
    print(f"Extracted: {json.dumps(extracted, indent=2)}")

    # --- Benchmark ---
    sample_prompts = [
        "What is the capital of France?",
        "Summarize: The quick brown fox jumps over the lazy dog.",
        "Translate to Spanish: Hello, how are you?",
        "What is 17 multiplied by 13?",
        "Name three programming languages.",
    ]
    benchmark(llm, sample_prompts)
