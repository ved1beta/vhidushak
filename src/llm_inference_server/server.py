import uuid
import time
import logging
import requests
from fastapi import FastAPI

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

app = FastAPI()
session = requests.Session()

MODEL = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
VLLM_URL = "http://localhost:8001/v1/completions"


@app.post("/generate")
def generate(prompt: str):
    request_id = str(uuid.uuid4())
    formatted = f"<|system|>\nYou are a helpful assistant.</s>\n<|user|>\n{prompt}</s>\n<|assistant|>\n"

    t0 = time.time()
    response = session.post(VLLM_URL, json={"model": MODEL, "prompt": formatted, "max_tokens": 256, "stop": ["</s>"]})
    latency = round((time.time() - t0) * 1000, 2)

    log.info(f"request_id={request_id} latency={latency}ms")
    return {"request_id": request_id, "latency_ms": latency, "response": response.json()}
