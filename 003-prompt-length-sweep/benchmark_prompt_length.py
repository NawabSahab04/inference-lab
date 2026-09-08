import json
import time
from urllib.request import Request, urlopen
import math
import statistics
import matplotlib.pyplot as plt
from pathlib import Path

url = "http://172.22.208.1:8000/v1/chat/completions"
OUTPUT_DIR = Path(__file__).resolve().parent

FILLER_REPETITIONS = [32, 128, 512, 1024, 2048]

def generate_prompt(size, run):
    unique_prefix = f"request-{size}-{run}: "
    filler = "blue " * size
    return unique_prefix + filler + " Reply with exactly: OK"

def generate_payload(size, run):
    prompt = generate_prompt(size, run)
    return {
        "model": "google/gemma-4-12b-qat",
        "stream": True,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "temperature": 0,
        "max_tokens": 256,
    }

x_sizes = []
ttft_p50_values = []
ttft_p95_values = []
ttfc_p50_values = []
ttfc_p95_values = []

def percentile(values, p):
    ordered = sorted(values)
    index = math.ceil(len(ordered) * p) - 1
    return ordered[index]

for size in FILLER_REPETITIONS:
    starting = time.perf_counter()
    TTFC_list = []
    TTFT_list = []
    elapsed_list = []
    for i in range(0,20):
        payload = generate_payload(size, i)  # Assuming a default run value
        body = json.dumps(payload).encode("utf-8")
        request = Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        responses = []
        TTFC_start = time.perf_counter()
        TTFT_start = time.perf_counter()
        ttfc_done = 0
        ttft_done = 0
        TTFC = 0
        TTFT = 0
        with urlopen(request) as response:
            chunk_start = time.perf_counter()
            for raw_line in response:
                line = raw_line.decode("utf-8").strip()
                if line.startswith("data: "):
                    data = line[len("data: ") :]
                    if data == "[DONE]":
                        break
                    result = json.loads(data)
                    answer = result["choices"][0]["delta"].get("content", "")
                    output = result["choices"][0]["delta"].get("reasoning_content") or result["choices"][0]["delta"].get("content", "")
                    if output and ttft_done == 0:
                        TTFT = time.perf_counter() - TTFT_start
                        TTFT_list.append(TTFT)
                        ttft_done = 1
                    if answer:
                        if ttfc_done == 0:
                            TTFC = time.perf_counter() - TTFC_start
                            TTFC_list.append(TTFC)
                            ttfc_done = 1
                            chunk_start = time.perf_counter()
                        else:
                            chunk_end = time.perf_counter()
                            chunk_start = time.perf_counter()
                        responses.append(answer)
        elapsed = time.perf_counter() - TTFC_start
        elapsed_list.append(elapsed)

    ttft_p50 = statistics.median(TTFT_list)
    ttft_p95 = percentile(TTFT_list, 0.95)
    ttfc_p50 = statistics.median(TTFC_list)
    ttfc_p95 = percentile(TTFC_list, 0.95)
    elapsed_p50 = statistics.median(elapsed_list)
    elapsed_p95 = percentile(elapsed_list, 0.95)

    x_sizes.append(size)
    ttft_p50_values.append(ttft_p50 * 1000)
    ttft_p95_values.append(ttft_p95 * 1000)
    ttfc_p50_values.append(ttfc_p50 * 1000)
    ttfc_p95_values.append(ttfc_p95 * 1000)

    finished = time.perf_counter()

    print(f"Batch elapsed: {finished - starting:.3f} seconds")
    print(f"TTFC mean: {sum(TTFC_list)/len(TTFC_list):.3f} seconds")
    print(f"TTFT mean: {sum(TTFT_list)/len(TTFT_list):.3f} seconds")
    print(f"TTFC p50: {ttfc_p50:.3f} seconds")
    print(f"TTFT p50: {ttft_p50:.3f} seconds")
    print(f"Elapsed p50: {elapsed_p50:.3f} seconds")
    print(f"TTFC p95: {ttfc_p95:.3f} seconds")
    print(f"TTFT p95: {ttft_p95:.3f} seconds")
    print(f"Elapsed p95: {elapsed_p95:.3f} seconds")
    print()

plt.figure(figsize=(8, 5))

plt.plot(x_sizes, ttft_p50_values, marker="o", label="TTFT p50")
plt.plot(x_sizes, ttft_p95_values, marker="o", label="TTFT p95")

plt.xlabel("Filler repetitions")
plt.ylabel("Latency (ms)")
plt.title("Prompt length vs time to first token")
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "ttft_vs_prompt_length.png", dpi=160)
plt.close()

plt.figure(figsize=(8, 5))

plt.plot(x_sizes, ttft_p50_values, marker="o", label="TTFT p50")
plt.plot(x_sizes, ttfc_p50_values, marker="o", label="TTFC p50")

plt.xlabel("Filler repetitions")
plt.ylabel("Latency (ms)")
plt.title("First generated token vs first visible content")
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "ttft_vs_ttfc.png", dpi=160)
plt.close()
