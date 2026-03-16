import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))

from fastapi import FastAPI
from inference_systems.job_queue.redis_client import push_job, get_result
import uuid

app = FastAPI()

@app.post("/generate")
def generate(prompt: str):

    request_id = str(uuid.uuid4())

    job = {
        "request_id": request_id,
        "prompt": prompt
    }

    push_job(job)

    return {
        "status": "queued",
        "request_id": request_id
    }


@app.get("/result/{request_id}")
def get_result_api(request_id: str):
    result = get_result(request_id)
    return result if result else {"status": "processing"}