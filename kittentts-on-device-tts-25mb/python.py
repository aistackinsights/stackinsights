from kittentts import KittenTTS
import soundfile as sf
import numpy as np

# Load the 25MB nano model (downloads from HuggingFace on first run)
# Swap in "KittenML/kitten-tts-mini-0.8" for best quality
model = KittenTTS("KittenML/kitten-tts-nano-0.8-int8")

# Single-sentence synthesis
audio = model.generate(
    "KittenTTS delivers high-quality speech synthesis without a GPU.",
    voice="Jasper",       # Options: Bella, Jasper, Luna, Bruno, Rosie, Hugo, Kiki, Leo
    speed=1.0,            # 0.5 = half speed, 1.5 = 50% faster
    clean_text=True       # Expands numbers, currencies, and units to words
)

# Save to WAV at 24kHz
sf.write("output.wav", audio, 24000)
print(f"Generated {len(audio) / 24000:.1f}s of audio")

# Batch synthesis — concatenate segments for longer content
paragraphs = [
    "Chapter one. The introduction.",
    "It was March 2026, and TTS models had finally gotten small.",
    "The 25 megabyte model ran without a GPU in sight.",
]

segments = [
    model.generate(text, voice="Bruno", clean_text=True)
    for text in paragraphs
]

full_audio = np.concatenate(segments)
sf.write("chapter_one.wav", full_audio, 24000)
print(f"Total duration: {len(full_audio) / 24000:.1f}s")
