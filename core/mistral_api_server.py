from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, validator
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import time
import uuid
from typing import List, Optional, Generator, Union, Dict, Any
import asyncio
import logging
from contextlib import asynccontextmanager
import gc

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI with lifespan context
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load model once at startup
    logger.info("Loading model...")
    try:
        # Move global declaration to the top of the function
        global tokenizer, model, model_id
        
        model_id = "mistralai/Mistral-7B-Instruct-v0.3"
        
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        
        # Load model with optimizations
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=torch.float16,  # Use half-precision
            device_map="auto",          # Automatic device mapping
            low_cpu_mem_usage=True,     # Optimize CPU memory usage
        )
        
        # Performance optimization: Set to eval mode
        model.eval()
        
        # Additional optimization: Enable attention caching for faster inference
        model.config.use_cache = True
        
        logger.info(f"Model {model_id} loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

    yield
    
    # Shutdown: Release resources
    logger.info("Shutting down and releasing resources...")
    if 'model' in globals():
        del model
    if 'tokenizer' in globals():
        del tokenizer
    gc.collect()
    torch.cuda.empty_cache()
    logger.info("Resources released")

app = FastAPI(lifespan=lifespan)

class ChatMessage(BaseModel):
    role: str
    content: str

    @validator('role')
    def validate_role(cls, v):
        if v not in ['system', 'user', 'assistant']:
            raise ValueError('Role must be system, user, or assistant')
        return v

class ChatRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: float = Field(0.2, ge=0.0, le=2.0)
    max_tokens: int = Field(256, ge=1, le=4096)
    stream: bool = False

class UsageInfo(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class ChatResponseMessage(BaseModel):
    role: str
    content: str

class ChatResponseChoice(BaseModel):
    index: int
    message: ChatResponseMessage
    finish_reason: str

class ChatResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[ChatResponseChoice]
    usage: UsageInfo

def format_prompt(messages: List[ChatMessage]) -> str:
    """Format messages into a prompt optimized for Mistral."""
    formatted_prompt = ""
    for msg in messages:
        if msg.role == "system":
            formatted_prompt += f"<s>[INST] {msg.content} [/INST]\n"
        elif msg.role == "user":
            formatted_prompt += f"<s>[INST] {msg.content} [/INST]\n"
        elif msg.role == "assistant":
            formatted_prompt += f"{msg.content}</s>\n"
    
    # Final turn starts
    formatted_prompt += "<s>[INST] "
    last_user_msg = next((msg.content for msg in reversed(messages) if msg.role == "user"), "")
    if last_user_msg:
        formatted_prompt += last_user_msg
    formatted_prompt += " [/INST]\n"
    
    return formatted_prompt

def generate_stream(request_id: str, prompt: str, max_tokens: int, temperature: float) -> Generator[str, None, None]:
    """Generate streaming response tokens."""
    # Encode prompt
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    input_length = len(inputs.input_ids[0])
    
    # Generate initial token
    tokens_generated = 0
    gen_start_time = time.time()
    
    # Stream tokens as they're generated
    with torch.no_grad():
        generated_ids = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=temperature,
            do_sample=True if temperature > 0 else False,
            pad_token_id=tokenizer.eos_token_id,
            repetition_penalty=1.1,
            # Stream results
            streamer=None,  # We're handling streaming manually for more control
            return_dict_in_generate=True,
            output_scores=False
        )
    
    # Decode output
    output = tokenizer.decode(generated_ids.sequences[0][input_length:], skip_special_tokens=True)
    tokens_generated = len(tokenizer.encode(output))
    
    # Calculate time
    gen_time = time.time() - gen_start_time
    tokens_per_sec = tokens_generated / gen_time if gen_time > 0 else 0
    
    logger.info(f"Generated {tokens_generated} tokens in {gen_time:.2f}s ({tokens_per_sec:.2f} tokens/s)")
    
    yield output

@app.post("/chat/completions", response_model=Union[ChatResponse, Dict[str, Any]])
@app.post("/v1/chat/completions", response_model=Union[ChatResponse, Dict[str, Any]])
async def chat_completions(request: ChatRequest, background_tasks: BackgroundTasks):
    try:
        # Generate unique ID for the request
        request_id = f"chatcmpl-{uuid.uuid4().hex}"
        created_timestamp = int(time.time())
        
        # Format prompt using improved template for better Mistral results
        prompt = format_prompt(request.messages)
        
        # Check input length
        tokens = tokenizer.encode(prompt)
        prompt_token_count = len(tokens)
        if prompt_token_count > 4096:  # Adjust based on model context window
            raise HTTPException(status_code=400, detail="Input too long")
        
        start = time.time()
        logger.info(f"Request {request_id}: Processing prompt with {prompt_token_count} tokens")
        
        # Handle streaming case
        if request.stream:
            async def stream_generator():
                content = ""
                for token in generate_stream(request_id, prompt, request.max_tokens, request.temperature):
                    content = token
                    # Format each chunk for OpenAI compatibility
                    chunk = {
                        "id": request_id,
                        "object": "chat.completion.chunk",
                        "created": created_timestamp,
                        "model": model_id,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {"content": token},
                                "finish_reason": None
                            }
                        ]
                    }
                    yield f"data: {chunk}\n\n"
                
                # Send final chunk with finish reason
                completion_token_count = len(tokenizer.encode(content))
                final_chunk = {
                    "id": request_id,
                    "object": "chat.completion.chunk",
                    "created": created_timestamp,
                    "model": model_id,
                    "choices": [
                        {
                            "index": 0,
                            "delta": {},
                            "finish_reason": "stop"
                        }
                    ],
                    "usage": {
                        "prompt_tokens": prompt_token_count,
                        "completion_tokens": completion_token_count,
                        "total_tokens": prompt_token_count + completion_token_count
                    }
                }
                yield f"data: {final_chunk}\n\n"
                yield "data: [DONE]\n\n"
                
                # Clean cache after response complete
                background_tasks.add_task(torch.cuda.empty_cache)
                background_tasks.add_task(gc.collect)
                
            return StreamingResponse(stream_generator(), media_type="text/event-stream")
        
        # Non-streaming case
        else:
            # Prepare inputs
            inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
            
            # Optimize non-streaming generation
            with torch.no_grad():
                # Performance optimization: Use optimized generation settings
                output = model.generate(
                    **inputs,
                    max_new_tokens=request.max_tokens,
                    temperature=request.temperature,
                    do_sample=True if request.temperature > 0 else False,
                    pad_token_id=tokenizer.eos_token_id,
                    repetition_penalty=1.1,  # Avoid repetitive text
                    num_beams=1,  # Simpler beam search for faster generation
                )
                
            # Process output
            completion = tokenizer.decode(output[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
            answer = completion.strip()
            completion_token_count = len(tokenizer.encode(answer))
            
            duration = round(time.time() - start, 2)
            logger.info(f"Response generated in {duration}s, {completion_token_count} tokens")
            
            # Schedule memory cleanup after response
            background_tasks.add_task(torch.cuda.empty_cache)
            background_tasks.add_task(gc.collect)
            
            # Create response
            return ChatResponse(
                id=request_id,
                object="chat.completion",
                created=created_timestamp,
                model=model_id,
                choices=[
                    ChatResponseChoice(
                        index=0,
                        message=ChatResponseMessage(role="assistant", content=answer),
                        finish_reason="stop"
                    )
                ],
                usage=UsageInfo(
                    prompt_tokens=prompt_token_count,
                    completion_tokens=completion_token_count,
                    total_tokens=prompt_token_count + completion_token_count
                )
            )

    except torch.cuda.OutOfMemoryError:
        # Clean up on CUDA OOM
        torch.cuda.empty_cache()
        gc.collect()
        logger.error("CUDA out of memory error")
        raise HTTPException(
            status_code=503, 
            detail="GPU memory exceeded. Try reducing max_tokens or input length."
        )
    except Exception as e:
        logger.error(f"Error during generation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Generation error: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint with GPU stats"""
    gpu_stats = {}
    if torch.cuda.is_available():
        gpu_stats = {
            "gpu_name": torch.cuda.get_device_name(0),
            "memory_allocated": f"{torch.cuda.memory_allocated(0) / 1024**3:.2f} GB",
            "memory_reserved": f"{torch.cuda.memory_reserved(0) / 1024**3:.2f} GB",
            "max_memory": f"{torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB"
        }
    
    return {
        "status": "healthy", 
        "model": model_id,
        "gpu": gpu_stats
    }

if __name__ == "__main__":
    import uvicorn
    # Run with optimized settings
    uvicorn.run(
        "mistral_api_server:app", 
        host="0.0.0.0", 
        port=8001,
        workers=1  # Multiple workers can cause GPU memory issues
    )