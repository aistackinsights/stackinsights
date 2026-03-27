# OpenAI Sora Shutdown — Migration & Alternatives Guide

Companion scripts for the AIStackInsights article:
**"OpenAI Just Killed Sora. Here's What Happens to the $1B Disney Deal — and the AI Video Market."**

📖 [Read the full article](https://aistackinsights.ai/blog/openai-sora-shutdown-disney-deal-ai-video-future)

---

## Scripts

| File | Description |
|---|---|
| `compare_video_apis.py` | Side-by-side comparison of Runway, Kling, Luma, and Google Veo APIs |
| `sora_migration_guide.py` | Interactive CLI to find the best Sora alternative for your use case |

---

## Requirements

```bash
pip install httpx python-dotenv rich
```

Create a `.env` file:
```
RUNWAY_API_KEY=your_key_here
LUMAAI_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here      # for Veo via Vertex AI
KLING_API_KEY=your_key_here
```

---

## Quick Reference: Sora Alternatives

| Provider | Model | API Available | Best For |
|---|---|---|---|
| Google | Veo 3 | ✅ Vertex AI | Cinematic, long clips |
| Runway | Gen-4 | ✅ REST API | Creative, character consistency |
| Luma AI | Dream Machine | ✅ REST API | Fast, stylized |
| Kling | Kling 2.0 | ✅ REST API | Realistic motion, Chinese market |
| Minimax | Hailuo Video | ✅ REST API | Anime/stylized content |

---

*Part of [AIStackInsights Stackinsights](https://github.com/aistackinsights/stackinsights) — companion code for every article.*
