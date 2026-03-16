import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))

import uuid
import time
from fastapi import FastAPI
from prometheus_client import make_asgi_app
from inference_systems.job_queue.redis_client import push_job, get_result
from inference_systems.tracing import init_tracer
from inference_systems.metrics import requests_total

app = FastAPI()
app.mount("/metrics", make_asgi_app())
tracer = init_tracer("api-gateway")


@app.post("/generate")
def generate(prompt: str):
    with tracer.start_as_current_span("api_request"):
        requests_total.inc()
        request_id = str(uuid.uuid4())
        job = {
            "request_id": request_id,
            "prompt": prompt,
            "created_at": time.time()
        }
        push_job(job)
        return {"status": "queued", "request_id": request_id}


@app.get("/result/{request_id}")
def get_result_api(request_id: str):
    result = get_result(request_id)
    return result if result else {"status": "processing"}
