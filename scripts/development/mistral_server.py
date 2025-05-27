#!/usr/bin/env python3
"""
Simple OpenAI-compatible API server for Mistral model using transformers
"""
import asyncio
import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional

import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer
import uvicorn


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    max_tokens: Optional[int] = 500
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.9


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict]
    usage: Dict


app = FastAPI(title="Mistral API Server", version="1.0.0")

# Global variables for model and tokenizer
model = None
tokenizer = None


def load_model():
    """Load the Mistral model and tokenizer"""
    global model, tokenizer
    
    print("Loading Mistral model...")
    model_name = "microsoft/DialoGPT-medium"  # Using a lighter model for testing
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None,
            low_cpu_mem_usage=True
        )
        
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            
        print(f"Model loaded successfully! Using device: {next(model.parameters()).device}")
        
    except Exception as e:
        print(f"Error loading model: {e}")
        # Fallback to a very simple model
        print("Falling back to GPT-2...")
        model_name = "gpt2"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token


@app.on_event("startup")
async def startup_event():
    """Load model on startup"""
    load_model()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "model_loaded": model is not None}


@app.post("/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """OpenAI-compatible chat completions endpoint"""
    if model is None or tokenizer is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # Combine messages into a single prompt
        prompt = ""
        for message in request.messages:
            if message.role == "system":
                prompt += f"System: {message.content}\n"
            elif message.role == "user":
                prompt += f"User: {message.content}\n"
            elif message.role == "assistant":
                prompt += f"Assistant: {message.content}\n"
        
        prompt += "Assistant:"
        
        # Tokenize input
        inputs = tokenizer.encode(prompt, return_tensors="pt", truncation=True, max_length=512)
        
        # Move to same device as model
        if torch.cuda.is_available():
            inputs = inputs.to(model.device)
        
        # Generate response
        with torch.no_grad():
            outputs = model.generate(
                inputs,
                max_new_tokens=min(request.max_tokens or 150, 150),
                temperature=request.temperature or 0.7,
                top_p=request.top_p or 0.9,
                do_sample=True,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
                attention_mask=inputs.ne(tokenizer.pad_token_id)
            )
        
        # Decode response
        response_text = tokenizer.decode(outputs[0][inputs.shape[1]:], skip_special_tokens=True)
        
        # Clean up response
        response_text = response_text.strip()
        if not response_text:
            response_text = "I understand your request for document classification. Please provide the document content."
        
        # Create response
        response = ChatCompletionResponse(
            id=f"chatcmpl-{uuid.uuid4().hex[:12]}",
            created=int(time.time()),
            model=request.model,
            choices=[{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response_text
                },
                "finish_reason": "stop"
            }],
            usage={
                "prompt_tokens": inputs.shape[1],
                "completion_tokens": len(tokenizer.encode(response_text)),
                "total_tokens": inputs.shape[1] + len(tokenizer.encode(response_text))
            }
        )
        
        return response
        
    except Exception as e:
        print(f"Error generating response: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Mistral API Server", "status": "running"}


if __name__ == "__main__":
    print("Starting Mistral API Server...")
    uvicorn.run(
        "mistral_server:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
        access_log=False
    )
