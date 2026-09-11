import json
import time
from urllib.request import Request, urlopen
import math
import statistics
import matplotlib.pyplot as plt
from pathlib import Path

url = "http://172.22.208.1:8000/v1/chat/completions"
OUTPUT_DIR = Path(__file__).resolve().parent

MAX_TOKEN_VALUES = [16, 32, 64, 128, 256]

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
        "max_tokens": MAX_TOKEN_VALUES[run],
    }

x_sizes = []
ttft_p50_values = []
ttft_p95_values = []
ttfc_p50_values = []
ttfc_p95_values = []
completion_p50_values = []
e2e_p50_values = []
e2e_p95_values = []
decode_p50_values = []

def percentile(values, p):
    ordered = sorted(values)
    index = math.ceil(len(ordered) * p) - 1
    return ordered[index]

for run in range(len(MAX_TOKEN_VALUES)):
    starting = time.perf_counter()
    TTFC_list = []
    TTFT_list = []
    decode_throughputs = []
    completion_token_counts = []
    elapsed_list = []
    for i in range(0,20):
        usage = None
        finish_reason = None # could be moved outside the loop if we only care about the last one
        payload = generate_payload(run)
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
        completion_tokens = usage["completion_tokens"]
        decode_seconds = elapsed - TTFT

        decode_throughput = (completion_tokens - 1) / decode_seconds

        completion_token_counts.append(completion_tokens)
        decode_throughputs.append(decode_throughput)

    ttft_p50 = statistics.median(TTFT_list)
    ttft_p95 = percentile(TTFT_list, 0.95)
    ttfc_p50 = statistics.median(TTFC_list)
    ttfc_p95 = percentile(TTFC_list, 0.95)
    elapsed_p50 = statistics.median(elapsed_list)
    elapsed_p95 = percentile(elapsed_list, 0.95)
    completion_p50 = statistics.median(completion_token_counts)
    decode_p50 = statistics.median(decode_throughputs)

    completion_p50_values.append(completion_p50)
    e2e_p50_values.append(elapsed_p50 * 1000)
    e2e_p95_values.append(elapsed_p95 * 1000)
    decode_p50_values.append(decode_p50)
    x_sizes.append(MAX_TOKEN_VALUES[run])
    ttft_p50_values.append(ttft_p50 * 1000)
    ttft_p95_values.append(ttft_p95 * 1000)
    ttfc_p50_values.append(ttfc_p50 * 1000)
    ttfc_p95_values.append(ttfc_p95 * 1000)

    finished = time.perf_counter()

    print(f"finish reason: {finish_reason}")
    if usage.get("prompt_tokens") is not None:
        print(f"prompt tokens: {usage['prompt_tokens']}")
    if usage.get("completion_tokens") is not None:
        print(f"completion tokens: {usage['completion_tokens']}")
    if usage.get("completion_tokens_details", {}).get("reasoning_tokens") is not None:
        print(
            "reasoning tokens:",
            usage.get("completion_tokens_details", {}).get("reasoning_tokens", 0),
        )
    print(f"Batch elapsed: {finished - starting:.3f} seconds")
    print(f"TTFC mean: {sum(TTFC_list)/len(TTFC_list):.3f} seconds")
    print(f"TTFT mean: {sum(TTFT_list)/len(TTFT_list):.3f} seconds")
    print(f"TTFC p50: {ttfc_p50:.3f} seconds")
    print(f"TTFT p50: {ttft_p50:.3f} seconds")
    print(f"Elapsed p50: {elapsed_p50:.3f} seconds")
    print(f"TTFC p95: {ttfc_p95:.3f} seconds")
    print(f"TTFT p95: {ttft_p95:.3f} seconds")
    print(f"Elapsed p95: {elapsed_p95:.3f} seconds")
    print(f"Max tokens: {MAX_TOKEN_VALUES[run]}")
    print(f"Completion tokens p50: {statistics.median(completion_token_counts):.3f}")
    print(f"Decode throughput p50: {statistics.median(decode_throughputs):.3f} tokens/second")
    print()

plt.figure(figsize=(8, 5))

plt.plot(
    completion_p50_values,
    e2e_p50_values,
    marker="o",
    label="E2E p50",
)
plt.plot(
    completion_p50_values,
    e2e_p95_values,
    marker="o",
    label="E2E p95",
)


#actual completion tokens vs e2e p50
plt.xlabel("Max Tokens")
plt.ylabel("E2E Latency (ms)")
plt.title("Actual completion tokens vs E2E p50")
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "actual_completion_tokens_vs_e2e_p50.png", dpi=160)
plt.close()

plt.figure(figsize=(8, 5))

#actual completion tokens vs decode throughput p95
plt.plot(
    completion_p50_values,
    decode_p50_values,
    marker="o",
    label="Decode throughput p50",
)

plt.xlabel("Max Tokens")
plt.ylabel("Decode Throughput (tokens/second)")
plt.title("Actual completion tokens vs Decode Throughput p50")
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "actual_completion_tokens_vs_decode_throughput_p50.png", dpi=160)
plt.close()
