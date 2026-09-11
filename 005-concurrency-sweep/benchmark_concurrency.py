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
        "max_tokens": 256,
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
    # Stream response
    
    # Measure TTFT and E2E
    # Capture usage
    # Return a dictionary of measurements
    return {
        "request_id": request_id,
        "TTFT": TTFT,
        "usage": usage,
        "elapsed": elapsed,
        "completion_tokens": usage["completion_tokens"] if usage else None,
        "finish_reason": finish_reason,
    }

experiment_started = time.perf_counter()

with ThreadPoolExecutor(max_workers=2) as executor:
    results = list(executor.map(run_request, range(2)))

experiment_elapsed = time.perf_counter() - experiment_started

print(results)
print(f"Experiment wall time: {experiment_elapsed:.3f} seconds")