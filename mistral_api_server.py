# mistral_api_server.py

from fastapi import FastAPI, Request
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

app = FastAPI()

# Load model once at startup
model_id = "mistralai/Mistral-7B-Instruct-v0.3"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id, torch_dtype=torch.float16, device_map="auto"
)

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str
    messages: list[ChatMessage]
    temperature: float = 0.2
    max_tokens: int = 256

# Add both routes
import time

@app.post("/chat/completions")
@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    prompt = ""
    for msg in request.messages:
        prompt += f"{msg.role}: {msg.content}\n"
    prompt += "assistant:"

    try:
        start = time.time()
        print(f"🧠 Prompt received:\n{prompt[:300]}...\n---")

        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        print("📦 Inputs prepared")

        output = model.generate(
            **inputs,
            max_new_tokens=request.max_tokens,
            temperature=request.temperature,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
        print("🎉 Model output generated")

        completion = tokenizer.decode(output[0], skip_special_tokens=True)
        print(f"📤 Raw output:\n{completion[:300]}...\n---")

        answer = completion.replace(prompt, "").strip()
        duration = round(time.time() - start, 2)
        print(f"✅ Response extracted in {duration}s")

        return {
            "id": "chatcmpl-local",
            "object": "chat.completion",
            "model": model_id,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": answer},
                "finish_reason": "stop"
            }]
        }

    except Exception as e:
        print(f"❌ Exception during generation: {e}")
        return {
            "id": "chatcmpl-failed",
            "object": "chat.completion",
            "model": model_id,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": "An error occurred."},
                "finish_reason": "error"
            }],
            "error": str(e)
        }
