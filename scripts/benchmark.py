"""
Benchmark script for the distributed inference system.

Usage:
    python scripts/benchmark.py                    # default: 10 requests, 4 concurrent
    python scripts/benchmark.py --total 50 --concurrency 8
    python scripts/benchmark.py --prompt "What is a neural network?"
"""

import argparse
import time
import statistics
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

API_URL = "http://localhost:8000"

PROMPTS = [
    "Explain transformers in machine learning.",
    "What is gradient descent?",
    "How does attention mechanism work?",
    "What is a neural network?",
    "Explain backpropagation.",
    "What is reinforcement learning?",
    "How does BERT work?",
    "What is tokenization in NLP?",
]


def submit_job(prompt):
    t0 = time.time()
    r = requests.post(f"{API_URL}/generate", params={"prompt": prompt}, timeout=10)
    r.raise_for_status()
    request_id = r.json()["request_id"]
    submit_latency = (time.time() - t0) * 1000
    return request_id, submit_latency, t0


def poll_result(request_id, submitted_at, timeout=120):
    deadline = time.time() + timeout
    while time.time() < deadline:
        r = requests.get(f"{API_URL}/result/{request_id}", timeout=5)
        data = r.json()
        if data.get("status") != "processing":
            e2e_latency = (time.time() - submitted_at) * 1000
            return data, e2e_latency
        time.sleep(0.5)
    return None, None


def run_single(prompt):
    request_id, submit_ms, t0 = submit_job(prompt)
    result, e2e_ms = poll_result(request_id, t0)
    return {
        "request_id": request_id,
        "submit_ms": submit_ms,
        "e2e_ms": e2e_ms,
        "success": result is not None,
        "tokens": result.get("usage", {}).get("completion_tokens", 0) if result else 0,
    }


def run_benchmark(total, concurrency, prompt=None):
    prompts = [prompt or PROMPTS[i % len(PROMPTS)] for i in range(total)]

    print(f"\nBenchmark: {total} requests | concurrency={concurrency} | API={API_URL}\n")
    print(f"{'#':<5} {'status':<10} {'submit_ms':<12} {'e2e_ms':<12} {'tokens'}")
    print("-" * 55)

    results = []
    start = time.time()

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = {pool.submit(run_single, p): i for i, p in enumerate(prompts)}
        for future in as_completed(futures):
            i = futures[future]
            try:
                r = future.result()
                results.append(r)
                status = "OK" if r["success"] else "TIMEOUT"
                print(f"{i+1:<5} {status:<10} {r['submit_ms']:<12.1f} {r['e2e_ms'] or 0:<12.1f} {r['tokens']}")
            except Exception as e:
                print(f"{i+1:<5} {'ERROR':<10} {str(e)}")

    wall_time = time.time() - start
    successful = [r for r in results if r["success"] and r["e2e_ms"]]

    if not successful:
        print("\nNo successful requests.")
        return

    e2e_times = [r["e2e_ms"] for r in successful]
    submit_times = [r["submit_ms"] for r in successful]
    total_tokens = sum(r["tokens"] for r in successful)

    e2e_times.sort()
    n = len(e2e_times)

    print("\n" + "=" * 55)
    print("RESULTS SUMMARY")
    print("=" * 55)
    print(f"  Total requests:     {total}")
    print(f"  Successful:         {len(successful)}/{total}")
    print(f"  Wall time:          {wall_time:.2f}s")
    print(f"  Throughput:         {len(successful)/wall_time:.2f} req/s")
    print(f"  Total tokens out:   {total_tokens}")
    print(f"  Tokens/sec:         {total_tokens/wall_time:.1f}")
    print()
    print(f"  Submit latency p50: {statistics.median(submit_times):.1f}ms")
    print(f"  E2E latency p50:    {e2e_times[int(n*0.50)]:.0f}ms")
    print(f"  E2E latency p90:    {e2e_times[int(n*0.90)]:.0f}ms")
    print(f"  E2E latency p95:    {e2e_times[min(int(n*0.95), n-1)]:.0f}ms")
    print(f"  E2E latency p99:    {e2e_times[min(int(n*0.99), n-1)]:.0f}ms")
    print(f"  E2E latency max:    {max(e2e_times):.0f}ms")
    print("=" * 55)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--total", type=int, default=10)
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--prompt", type=str, default=None)
    args = parser.parse_args()

    run_benchmark(args.total, args.concurrency, args.prompt)
