# Install the mamba-ssm package (requires CUDA-capable GPU)
# pip install mamba-ssm transformers torch

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

model_id = "state-spaces/mamba-3-1.5b"

tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    torch_dtype=torch.bfloat16,
    device_map="auto",
)

prompt = "Explain the difference between a state space model and a transformer in three sentences:"
inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

with torch.no_grad():
    output = model.generate(
        **inputs,
        max_new_tokens=256,
        temperature=0.7,
        do_sample=True,
    )

print(tokenizer.decode(output[0], skip_special_tokens=True))
