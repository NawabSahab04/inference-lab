import json
import time
from urllib.request import Request, urlopen
import math
import statistics
import matplotlib.pyplot as plt
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

url = "http://172.22.208.1:8000/v1/chat/completions"
OUTPUT_DIR = Path(__file__).resolve().parent

def generate_payload(run):
    return {
        "model": "google/gemma-4-12b-qat",
        "stream": True,
        "stream_options": {"include_usage": True},
        "messages": [
            {
                "role": "user",
                "content": "Output the integers starting at 1, separated by spaces. Continue indefinitely.",
            }
        ],
        "temperature": 0,
        "max_tokens": 64,
    }
def run_request(request_id):
    # Build request
    payload = generate_payload(request_id)
    body = json.dumps(payload).encode("utf-8")
    request = Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    # Send request and measure TTFT
    TTFT = None
    usage = None
    finish_reason = None
    elapsed = None
    completion_tokens = None
    TTFT_start = time.perf_counter()
    ttft_done = 0
    with urlopen(request) as response:
        for raw_line in response:
            line = raw_line.decode("utf-8").strip()
            if line.startswith("data: "):
                data = line[len("data: ") :]
                if data == "[DONE]":
                    break
                result = json.loads(data)
                if result.get("usage"):
                    usage = result["usage"]
                    continue
                choices = result.get("choices", [])
                if not choices:
                    continue
                choice = choices[0]
                if choice.get("finish_reason"):
                    finish_reason = choice["finish_reason"]
                answer = result["choices"][0]["delta"].get("content", "")
                output = result["choices"][0]["delta"].get("reasoning_content") or result["choices"][0]["delta"].get("content", "")
                if output and ttft_done == 0:
                    TTFT = time.perf_counter() - TTFT_start
                    ttft_done = 1
    elapsed = time.perf_counter() - TTFT_start
    return {
        "request_id": request_id,
        "TTFT": TTFT,
        "usage": usage,
        "elapsed": elapsed,
        "completion_tokens": usage["completion_tokens"] if usage else None,
        "finish_reason": finish_reason,
    }

experiment_started = time.perf_counter()
concurrency_levels = [1, 2, 4, 8]
ttft_p50s, ttft_p95s, e2e_p50s, e2e_p95s, throughputs = [], [], [], [], []
run_request("warmup")
for concurrency in concurrency_levels:
    conc_started = time.perf_counter()
    print(f"Running benchmark with concurrency level: {concurrency}")
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        results = list(executor.map(run_request, range(20)))
    print(f"Results for concurrency {concurrency}:")
    ttfts = [result["TTFT"] for result in results]
    elapsed_times = [result["elapsed"] for result in results]
    total_tokens = sum(result["completion_tokens"] for result in results)

    aggregate_throughput = total_tokens / (time.perf_counter() - conc_started)
    print(f"TTFTs: {ttfts}")
    print(f"Elapsed times: {elapsed_times}")
    print(f"Total tokens generated: {total_tokens}")
    print(f"Aggregate throughput (tokens/sec): {aggregate_throughput:.2f}")
    ttft_p50s.append(statistics.median(ttfts) * 1000)
    ttft_p95s.append(sorted(ttfts)[math.ceil(len(ttfts) * 0.95) - 1] * 1000)
    e2e_p50s.append(statistics.median(elapsed_times) * 1000)
    e2e_p95s.append(sorted(elapsed_times)[math.ceil(len(elapsed_times) * 0.95) - 1] * 1000)
    throughputs.append(aggregate_throughput)

plt.plot(concurrency_levels, throughputs, marker="o")
plt.xlabel("Concurrency")
plt.ylabel("Aggregate throughput (tokens/second)")
plt.title("Concurrency vs aggregate throughput")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "concurrency_vs_throughput.png", dpi=160)
plt.close()

plt.plot(concurrency_levels, ttft_p50s, marker="o", label="TTFT p50")
plt.plot(concurrency_levels, ttft_p95s, marker="o", label="TTFT p95")
plt.xlabel("Concurrency")
plt.ylabel("TTFT (ms)")
plt.title("Concurrency vs time to first token")
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "concurrency_vs_ttft.png", dpi=160)
plt.close()

plt.plot(concurrency_levels, e2e_p50s, marker="o", label="E2E p50")
plt.plot(concurrency_levels, e2e_p95s, marker="o", label="E2E p95")
plt.xlabel("Concurrency")
plt.ylabel("E2E latency (ms)")
plt.title("Concurrency vs end-to-end latency")
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "concurrency_vs_e2e.png", dpi=160)
plt.close()
