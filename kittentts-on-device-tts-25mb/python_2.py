from kittentts import KittenTTS

model = KittenTTS("KittenML/kitten-tts-mini-0.8")  # 80MB, best quality

# Direct-to-file synthesis with speed control
model.generate_to_file(
    "Generating voice output for a product demo.",
    output_path="demo.wav",
    voice="Luna",
    speed=0.9,          # Slightly slower = more gravitas
    sample_rate=24000,
    clean_text=True
)

# List all available voices programmatically
print(model.available_voices)
# ['Bella', 'Jasper', 'Luna', 'Bruno', 'Rosie', 'Hugo', 'Kiki', 'Leo']
