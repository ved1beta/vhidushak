import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))

import time
import subprocess
import threading
import requests
from prometheus_client import start_http_server
from inference_systems.job_queue.redis_client import pop_job, store_result
from inference_systems.tracing import init_tracer
from inference_systems.metrics import (
    queue_wait_seconds, inference_latency_seconds,
    tokens_per_second, prompt_tokens_total, completion_tokens_total,
    gpu_utilization, gpu_memory_used_mb
)

VLLM_URL = "http://localhost:8001/v1/completions"
MODEL = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

tracer = init_tracer("worker")


def poll_gpu():
    while True:
        try:
            out = subprocess.run(
                ["nvidia-smi", "--query-gpu=index,utilization.gpu,memory.used",
                 "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=5
            ).stdout.strip()
            for line in out.split("\n"):
                idx, util, mem = line.split(", ")
                gpu_utilization.labels(gpu_id=idx).set(float(util))
                gpu_memory_used_mb.labels(gpu_id=idx).set(float(mem))
        except Exception:
            pass
        time.sleep(15)


threading.Thread(target=poll_gpu, daemon=True).start()
start_http_server(8002)

while True:
    job = pop_job()

    with tracer.start_as_current_span("worker_process") as span:
        wait = time.time() - job["created_at"]
        queue_wait_seconds.observe(wait)
        span.set_attribute("queue_wait_ms", round(wait * 1000, 2))
        span.set_attribute("request_id", job["request_id"])

        payload = {"model": MODEL, "prompt": job["prompt"], "max_tokens": 256, "stop": ["</s>"]}

        t0 = time.time()
        with tracer.start_as_current_span("model_inference"):
            response = requests.post(VLLM_URL, json=payload)
        latency = time.time() - t0

        inference_latency_seconds.observe(latency)

        usage = response.json().get("usage", {})
        p_tok = usage.get("prompt_tokens", 0)
        c_tok = usage.get("completion_tokens", 0)
        prompt_tokens_total.inc(p_tok)
        completion_tokens_total.inc(c_tok)
        if latency > 0:
            tokens_per_second.observe(c_tok / latency)

        span.set_attribute("tokens_per_second", round(c_tok / latency, 1) if latency > 0 else 0)

        store_result(job["request_id"], response.json())
        print(f"completed: {job['request_id']} latency={latency:.2f}s tps={c_tok/latency:.1f}")
