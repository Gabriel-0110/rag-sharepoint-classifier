from huggingface_hub import login
from transformers import AutoTokenizer, AutoModelForCausalLM
import os

# 1️⃣ Authenticate the hub
login(token="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")

# 2️⃣ Now load the model
model_id = "mistralai/Mistral-7B-Instruct-v0.3"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model     = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="auto",
    torch_dtype="auto"
)
