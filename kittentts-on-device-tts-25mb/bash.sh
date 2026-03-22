# Linux users: install CPU-only torch first to avoid ~1GB of NVIDIA packages
pip install torch --index-url https://download.pytorch.org/whl/cpu

# Then install KittenTTS
pip install https://github.com/KittenML/KittenTTS/releases/download/0.8.1/kittentts-0.8.1-py3-none-any.whl

# Linux users may also need PortAudio for playback
# sudo apt install libportaudio2
