from prometheus_client import Counter, Histogram, Gauge

requests_total = Counter("inference_requests_total", "Total inference requests")

queue_wait_seconds = Histogram(
    "inference_queue_wait_seconds", "Queue wait time",
    buckets=[.005, .01, .025, .05, .1, .25, .5, 1, 2.5, 5]
)

inference_latency_seconds = Histogram(
    "inference_latency_seconds", "Model inference latency",
    buckets=[.1, .25, .5, 1, 2.5, 5, 10, 30]
)

tokens_per_second = Histogram(
    "inference_tokens_per_second", "Token generation rate",
    buckets=[10, 25, 50, 100, 200, 500, 1000]
)

prompt_tokens_total = Counter("inference_prompt_tokens_total", "Total prompt tokens processed")
completion_tokens_total = Counter("inference_completion_tokens_total", "Total completion tokens generated")

gpu_utilization = Gauge("gpu_utilization_percent", "GPU utilization", ["gpu_id"])
gpu_memory_used_mb = Gauge("gpu_memory_used_mb", "GPU memory used MB", ["gpu_id"])
