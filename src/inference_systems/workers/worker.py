import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))

import requests
from inference_systems.job_queue.redis_client import pop_job, store_result

VLLM_URL = "http://localhost:8001/v1/completions"


while True:

    job = pop_job()

    prompt = job["prompt"]
    request_id = job["request_id"]

    payload = {
        "model": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        "prompt": prompt,
        "max_tokens": 100
    }

    response = requests.post(VLLM_URL, json=payload)
    store_result(request_id, response.json())

    print("completed:", request_id)