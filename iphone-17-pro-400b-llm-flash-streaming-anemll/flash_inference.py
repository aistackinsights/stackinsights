# flash_inference.py
# Stream token generation from a model larger than your available RAM.
# Works on Apple Silicon via MLX's lazy evaluation + unified memory.
#
# Requirements: pip install mlx mlx-lm
# Docs: https://github.com/ml-explore/mlx-examples/tree/main/llms/mlx_lm

from mlx_lm import load, stream_generate

# Load a large model — MLX uses lazy evaluation so weights
# aren't all loaded to unified memory at once.
# Swap the model ID for any mlx-community quantized model.
model, tokenizer = load(
    "mlx-community/Qwen2.5-72B-Instruct-4bit",
    tokenizer_config={"trust_remote_code": True},
)

prompt = "Explain the difference between MoE and dense transformers in 3 bullet points."

messages = [{"role": "user", "content": prompt}]
formatted = tokenizer.apply_chat_template(
    messages,
    add_generation_prompt=True,
    tokenize=False,
)

# stream_generate yields tokens as they are produced.
# max_tokens caps generation length; temp controls sampling randomness.
print("Response: ", end="", flush=True)
for token_text in stream_generate(
    model,
    tokenizer,
    prompt=formatted,
    max_tokens=512,
    temp=0.6,
):
    print(token_text, end="", flush=True)
print()
