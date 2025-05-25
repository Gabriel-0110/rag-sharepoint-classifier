#!/bin/bash

# Load conda functions
source /home/azureuser/miniconda3/etc/profile.d/conda.sh
conda activate rag

# Preload model
python3 -c 'from mistral_api_server import tokenizer, model; print("✅ Model preloaded")'

# Start server
exec uvicorn mistral_api_server:app --host 0.0.0.0 --port 8001
