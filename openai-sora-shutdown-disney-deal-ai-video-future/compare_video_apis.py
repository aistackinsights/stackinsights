"""
compare_video_apis.py
─────────────────────
Side-by-side comparison of AI video generation APIs to help Sora users migrate.
Queries each provider's API, submits a test prompt, and benchmarks generation time.

Article: https://aistackinsights.ai/blog/openai-sora-shutdown-disney-deal-ai-video-future
Repo:    https://github.com/aistackinsights/stackinsights/tree/main/openai-sora-shutdown-disney-deal-ai-video-future

Requirements:
    pip install httpx python-dotenv rich

Usage:
    python compare_video_apis.py
    python compare_video_apis.py --prompt "A golden retriever running through autumn leaves" --duration 5
    python compare_video_apis.py --providers runway luma kling
"""

import argparse
import os
import sys
import time
from dataclasses import dataclass

try:
    import httpx
except ImportError:
    print("ERROR: httpx not installed. Run: pip install httpx")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    console = Console()
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


# ─── Provider definitions ─────────────────────────────────────────────────────

@dataclass
class VideoProvider:
    name: str
    api_base: str
    env_key: str
    model: str
    max_duration_s: int
    price_per_second: float   # USD, approximate
    supports_image_to_video: bool
    strengths: list[str]
    limitations: list[str]
    docs_url: str


PROVIDERS = {
    "runway": VideoProvider(
        name="Runway Gen-4",
        api_base="https://api.dev.runwayml.com/v1",
        env_key="RUNWAY_API_KEY",
        model="gen4_turbo",
        max_duration_s=10,
        price_per_second=0.05,
        supports_image_to_video=True,
        strengths=["Character consistency", "Cinematic quality", "Inpainting/outpainting", "Strong API"],
        limitations=["10s max per clip", "Expensive at scale", "US/EU focused"],
        docs_url="https://docs.dev.runwayml.com/",
    ),
    "luma": VideoProvider(
        name="Luma Dream Machine",
        api_base="https://api.lumalabs.ai/dream-machine/v1",
        env_key="LUMAAI_API_KEY",
        model="dream-machine",
        max_duration_s=9,
        price_per_second=0.03,
        supports_image_to_video=True,
        strengths=["Fast generation", "Good motion quality", "Stylized outputs", "Affordable"],
        limitations=["9s max", "Less cinematic than Runway", "Character consistency weaker"],
        docs_url="https://lumalabs.ai/dream-machine/api/",
    ),
    "kling": VideoProvider(
        name="Kling 2.0",
        api_base="https://api.klingai.com/v1",
        env_key="KLING_API_KEY",
        model="kling-v2",
        max_duration_s=30,
        price_per_second=0.02,
        supports_image_to_video=True,
        strengths=["Realistic motion", "30s clips", "Image-to-video", "Affordable", "Strong Chinese market"],
        limitations=["Latency can be high", "API docs partially in Chinese", "Rate limits"],
        docs_url="https://docs.klingai.com/",
    ),
    "minimax": VideoProvider(
        name="Minimax Hailuo",
        api_base="https://api.minimax.chat/v1",
        env_key="MINIMAX_API_KEY",
        model="video-01",
        max_duration_s=6,
        price_per_second=0.015,
        supports_image_to_video=True,
        strengths=["Stylized/anime quality", "Fast", "Cheap", "Good for short clips"],
        limitations=["6s max", "Less photorealistic", "Smaller ecosystem"],
        docs_url="https://platform.minimax.chat/",
    ),
    "google": VideoProvider(
        name="Google Veo 3",
        api_base="https://us-central1-aiplatform.googleapis.com/v1",
        env_key="GOOGLE_API_KEY",
        model="veo-3.0-generate-preview",
        max_duration_s=60,
        price_per_second=0.035,
        supports_image_to_video=True,
        strengths=["Longest clips (up to 60s)", "Cinematic quality", "Google scale + infrastructure", "Native with YouTube/Workspace"],
        limitations=["Vertex AI setup required", "Enterprise pricing", "Research preview features"],
        docs_url="https://cloud.google.com/vertex-ai/generative-ai/docs/video/generate-videos",
    ),
}


# ─── API calls ────────────────────────────────────────────────────────────────

def submit_runway(provider: VideoProvider, prompt: str, duration: int) -> dict:
    """Submit a generation request to Runway Gen-4."""
    api_key = os.environ.get(provider.env_key, "")
    if not api_key:
        return {"status": "skipped", "reason": f"{provider.env_key} not set"}

    headers = {"Authorization": f"Bearer {api_key}", "X-Runway-Version": "2024-11-06"}
    payload = {
        "promptText": prompt,
        "model": provider.model,
        "duration": min(duration, provider.max_duration_s),
        "ratio": "1280:720",
    }
    try:
        start = time.time()
        r = httpx.post(f"{provider.api_base}/image_to_video", headers=headers,
                       json=payload, timeout=30)
        elapsed = time.time() - start
        if r.status_code == 200:
            data = r.json()
            return {"status": "submitted", "id": data.get("id"), "elapsed_s": round(elapsed, 2)}
        return {"status": "error", "code": r.status_code, "detail": r.text[:200]}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


def submit_luma(provider: VideoProvider, prompt: str, duration: int) -> dict:
    """Submit a generation request to Luma Dream Machine."""
    api_key = os.environ.get(provider.env_key, "")
    if not api_key:
        return {"status": "skipped", "reason": f"{provider.env_key} not set"}

    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "prompt": prompt,
        "aspect_ratio": "16:9",
        "loop": False,
    }
    try:
        start = time.time()
        r = httpx.post(f"{provider.api_base}/generations", headers=headers,
                       json=payload, timeout=30)
        elapsed = time.time() - start
        if r.status_code in (200, 201):
            data = r.json()
            return {"status": "submitted", "id": data.get("id"), "elapsed_s": round(elapsed, 2)}
        return {"status": "error", "code": r.status_code, "detail": r.text[:200]}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


# ─── Comparison display ───────────────────────────────────────────────────────

def show_comparison_table(selected: list[str]) -> None:
    """Display a side-by-side comparison of providers."""
    providers = {k: v for k, v in PROVIDERS.items() if k in selected}

    if HAS_RICH:
        table = Table(title="🎬 AI Video API Comparison — Sora Alternatives", expand=True)
        table.add_column("", style="bold", width=20)
        for p in providers.values():
            table.add_column(p.name, ratio=1)

        rows = [
            ("Max Duration", *[f"{p.max_duration_s}s" for p in providers.values()]),
            ("Price/second", *[f"~${p.price_per_second:.3f}" for p in providers.values()]),
            ("Image→Video", *["✅" if p.supports_image_to_video else "❌" for p in providers.values()]),
            ("API Docs", *[p.docs_url.split("/")[2] for p in providers.values()]),
            ("Best For", *[p.strengths[0] for p in providers.values()]),
            ("Limitation", *[p.limitations[0] for p in providers.values()]),
        ]
        for row in rows:
            table.add_row(*row)
        console.print(table)
    else:
        print("\n=== AI Video API Comparison ===")
        for key, p in providers.items():
            print(f"\n{p.name} ({key})")
            print(f"  Max duration : {p.max_duration_s}s")
            print(f"  Price/second : ~${p.price_per_second:.3f}")
            print(f"  Image→Video  : {'Yes' if p.supports_image_to_video else 'No'}")
            print(f"  Best for     : {', '.join(p.strengths[:2])}")
            print(f"  Limitation   : {p.limitations[0]}")
            print(f"  Docs         : {p.docs_url}")


def run_test_submissions(selected: list[str], prompt: str, duration: int) -> None:
    """Submit test generation requests to each provider."""
    submit_fns = {
        "runway": submit_runway,
        "luma": submit_luma,
        # kling, minimax, google: add equivalent submit functions as needed
    }

    print(f"\nSubmitting test prompt to {len(selected)} provider(s)...")
    print(f"Prompt: \"{prompt}\"\n")

    for key in selected:
        provider = PROVIDERS[key]
        fn = submit_fns.get(key)
        if fn is None:
            print(f"  [{provider.name}] ⚠ Submission not yet implemented — check docs: {provider.docs_url}")
            continue
        result = fn(provider, prompt, duration)
        if result["status"] == "submitted":
            print(f"  [{provider.name}] ✅ Submitted — job ID: {result.get('id')} ({result.get('elapsed_s')}s)")
        elif result["status"] == "skipped":
            print(f"  [{provider.name}] ⏭ Skipped — {result.get('reason')}")
        else:
            print(f"  [{provider.name}] ❌ Error — {result.get('detail', '')[:80]}")


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Compare AI video generation APIs — Sora migration guide",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python compare_video_apis.py                                     # show comparison table
  python compare_video_apis.py --submit                            # submit test to all configured APIs
  python compare_video_apis.py --providers runway luma             # compare specific providers
  python compare_video_apis.py --prompt "A fox running at sunset" --duration 5 --submit
        """,
    )
    parser.add_argument("--providers", nargs="+", choices=list(PROVIDERS.keys()),
                        default=list(PROVIDERS.keys()), help="Which providers to compare")
    parser.add_argument("--prompt", type=str,
                        default="A cinematic shot of a futuristic city skyline at golden hour",
                        help="Prompt for test generation")
    parser.add_argument("--duration", type=int, default=5, help="Clip duration in seconds")
    parser.add_argument("--submit", action="store_true",
                        help="Actually submit test generations (requires API keys in .env)")
    args = parser.parse_args()

    show_comparison_table(args.providers)

    if args.submit:
        run_test_submissions(args.providers, args.prompt, args.duration)
    else:
        print("\n💡 Add --submit to test actual API submissions (requires API keys in .env)\n")


if __name__ == "__main__":
    main()
