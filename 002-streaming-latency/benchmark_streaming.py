import json
import time
from urllib.request import Request, urlopen

url = "http://172.22.208.1:8000/v1/chat/completions"

payload = {
    "model": "google/gemma-4-12b-qat",
    "stream": True,
    "messages": [
        {
            "role": "user",
            "content": "Explain an LLM KV cache in one sentence.",
        }
    ],
    "temperature": 0,
}
starting = time.perf_counter()
body = json.dumps(payload).encode("utf-8")
request = Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
TTFT_list = []
elapsed_list = []
for i in range(0,10):
    responses = []
    TTFT_start = time.perf_counter()
    times = []
    ttft_done = 0
    TTFT = 0
    max_time = 0
    chunks = 0
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
                if answer:
                    chunks += 1
                    if ttft_done == 0:
                        TTFT = time.perf_counter() - TTFT_start
                        TTFT_list.append(TTFT)
                        ttft_done = 1
                        chunk_start = time.perf_counter()
                    else:
                        chunk_end = time.perf_counter()
                        times.append(chunk_end - chunk_start)
                        max_time = max(max_time, chunk_end - chunk_start)
                        chunk_start = time.perf_counter()
                    responses.append(answer)
    elapsed = time.perf_counter() - TTFT_start
    elapsed_list.append(elapsed)


finished = time.perf_counter()
print(f"elapsed: {finished - starting:.3f} seconds")
print(f"TTFT: {TTFT:.3f} seconds")
print(f"Max chunk time: {max_time:.3f} seconds")
print(f"average chunk time: {sum(times)/len(times):.3f} seconds")
print(f"Total chunks: {chunks}")

print(f"TTFT p50: {sorted(TTFT_list)[len(TTFT_list)//2]:.3f} seconds")
print(f"Elapsed p50: {sorted(elapsed_list)[len(elapsed_list)//2]:.3f} seconds")

print(f"TTFT p95: {sorted(TTFT_list)[int(len(TTFT_list)*0.95)]:.3f} seconds")
print(f"Elapsed p95: {sorted(elapsed_list)[int(len(elapsed_list)*0.95)]:.3f} seconds")