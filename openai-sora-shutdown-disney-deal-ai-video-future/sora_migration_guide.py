"""
sora_migration_guide.py
────────────────────────
Interactive CLI to help Sora users find the best alternative for their use case.
Asks a few questions about your workflow and recommends the best provider + plan.

Article: https://aistackinsights.ai/blog/openai-sora-shutdown-disney-deal-ai-video-future
Repo:    https://github.com/aistackinsights/stackinsights/tree/main/openai-sora-shutdown-disney-deal-ai-video-future

Requirements:
    pip install rich

Usage:
    python sora_migration_guide.py
"""

import sys

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt, IntPrompt
    from rich.table import Table
    from rich.text import Text
    console = Console()
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


# ─── Provider recommendations ─────────────────────────────────────────────────

RECOMMENDATIONS = {
    ("short", "creative", "individual"):     ("Luma Dream Machine", "Fastest, cheapest, great for creative shorts. $30/mo Pro plan covers ~1,000 seconds.", "https://lumalabs.ai/dream-machine"),
    ("short", "creative", "team"):           ("Runway Gen-4", "Best creative tooling + team collaboration. API-ready. $95/mo Standard.", "https://runwayml.com"),
    ("short", "realistic", "individual"):    ("Kling 2.0", "Best realistic motion for short clips. Affordable at ~$0.02/s.", "https://klingai.com"),
    ("short", "realistic", "team"):          ("Runway Gen-4", "Most reliable API + cinematic realism. Strong enterprise support.", "https://runwayml.com"),
    ("long", "creative", "individual"):      ("Google Veo 3", "Up to 60s clips, cinematic quality. Vertex AI access required.", "https://cloud.google.com/vertex-ai/generative-ai/docs/video"),
    ("long", "creative", "team"):            ("Google Veo 3", "Scale, infrastructure, and longest clips in the market. Enterprise-grade.", "https://cloud.google.com/vertex-ai/generative-ai/docs/video"),
    ("long", "realistic", "individual"):     ("Google Veo 3", "60s photorealistic video. Best long-form alternative to Sora.", "https://cloud.google.com/vertex-ai/generative-ai/docs/video"),
    ("long", "realistic", "team"):           ("Google Veo 3", "Google enterprise + Vertex AI + longest clips. The only Sora-scale alternative.", "https://cloud.google.com/vertex-ai/generative-ai/docs/video"),
}

ALTERNATIVE_MAP = {
    "Runway Gen-4":       {"api": True,  "img2vid": True,  "price": "$0.05/s",   "max_clip": "10s",  "docs": "https://docs.dev.runwayml.com/"},
    "Luma Dream Machine": {"api": True,  "img2vid": True,  "price": "$0.03/s",   "max_clip": "9s",   "docs": "https://lumalabs.ai/dream-machine/api/"},
    "Kling 2.0":          {"api": True,  "img2vid": True,  "price": "$0.02/s",   "max_clip": "30s",  "docs": "https://docs.klingai.com/"},
    "Google Veo 3":       {"api": True,  "img2vid": True,  "price": "$0.035/s",  "max_clip": "60s",  "docs": "https://cloud.google.com/vertex-ai/generative-ai/docs/video"},
    "Minimax Hailuo":     {"api": True,  "img2vid": True,  "price": "$0.015/s",  "max_clip": "6s",   "docs": "https://platform.minimax.chat/"},
}


# ─── Questionnaire ────────────────────────────────────────────────────────────

def ask(prompt: str, choices: list[tuple[str, str]]) -> str:
    """Display a numbered menu and return the user's selection key."""
    if HAS_RICH:
        console.print(f"\n[bold cyan]{prompt}[/bold cyan]")
        for i, (key, label) in enumerate(choices, 1):
            console.print(f"  [bold]{i}.[/bold] {label}")
        while True:
            try:
                choice = IntPrompt.ask("  →", default=1)
                if 1 <= choice <= len(choices):
                    return choices[choice - 1][0]
            except (ValueError, KeyboardInterrupt):
                pass
    else:
        print(f"\n{prompt}")
        for i, (key, label) in enumerate(choices, 1):
            print(f"  {i}. {label}")
        while True:
            try:
                choice = int(input("  → ") or "1")
                if 1 <= choice <= len(choices):
                    return choices[choice - 1][0]
            except (ValueError, KeyboardInterrupt):
                pass


def show_recommendation(name: str, reason: str, url: str) -> None:
    details = ALTERNATIVE_MAP.get(name, {})
    if HAS_RICH:
        console.print()
        panel = Panel(
            f"[bold green]✅ Recommended: {name}[/bold green]\n\n"
            f"{reason}\n\n"
            f"[dim]Max clip:[/dim] {details.get('max_clip','—')}   "
            f"[dim]Price:[/dim] {details.get('price','—')}   "
            f"[dim]API:[/dim] {'✅' if details.get('api') else '❌'}   "
            f"[dim]Image→Video:[/dim] {'✅' if details.get('img2vid') else '❌'}\n\n"
            f"[link={url}]{url}[/link]",
            title="🎬 Your Sora Migration Pick",
            border_style="green",
        )
        console.print(panel)
        console.print("\n[bold]Compare all providers:[/bold] python compare_video_apis.py\n")
    else:
        print(f"\n✅ Recommended: {name}")
        print(f"   {reason}")
        print(f"   Max clip: {details.get('max_clip','—')} | Price: {details.get('price','—')}")
        print(f"   Docs: {url}")


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    if HAS_RICH:
        console.print(Panel(
            "[bold]OpenAI shut down Sora on March 26, 2026.[/bold]\n"
            "Answer 3 quick questions to find your best alternative.",
            title="🎬 Sora Migration Guide — AIStackInsights",
            border_style="cyan",
        ))
    else:
        print("\n=== Sora Migration Guide — AIStackInsights ===")
        print("OpenAI shut down Sora on March 26, 2026.")
        print("Answer 3 questions to find your best alternative.\n")

    clip_length = ask(
        "What length of video clips do you typically need?",
        [
            ("short", "Short clips (under 15 seconds) — social media, quick demos"),
            ("long",  "Longer clips (15s–60s+) — storytelling, ads, film production"),
        ]
    )

    style = ask(
        "What type of video output matters most to you?",
        [
            ("creative", "Creative / stylized — artistic, animated, expressive"),
            ("realistic", "Realistic / cinematic — photorealistic, film-quality"),
        ]
    )

    scale = ask(
        "How are you using it?",
        [
            ("individual", "Individual / solo creator"),
            ("team",       "Team or enterprise — multiple users, API integration"),
        ]
    )

    key = (clip_length, style, scale)
    name, reason, url = RECOMMENDATIONS.get(key, (
        "Runway Gen-4",
        "Strong all-rounder for most Sora workflows. Great API and cinematic quality.",
        "https://runwayml.com"
    ))

    show_recommendation(name, reason, url)


if __name__ == "__main__":
    main()
