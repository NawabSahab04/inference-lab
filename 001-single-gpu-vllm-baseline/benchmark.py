import json
import time
from urllib.request import Request, urlopen

url = "http://127.0.0.1:8000/v1/chat/completions"

payload = {
    "model": "/home/samrath/models/SmolLM2-360M-Instruct",
    "messages": [
        {
            "role": "user",
            "content": "Explain an LLM KV cache in one sentence.",
        }
    ],
    "temperature": 0
}

body = json.dumps(payload).encode("utf-8")
request = Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")

started = time.perf_counter()
with urlopen(request) as response:
    raw_response = response.read()

finished = time.perf_counter()

result = json.loads(raw_response)

answer = result["choices"][0]["message"]["content"]

print(answer)
print(f"elapsed: {finished - started:.3f} seconds")