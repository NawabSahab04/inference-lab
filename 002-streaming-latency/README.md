# Day 2 — Streaming latency

## Question

For one user on the LM Studio server, how much of response latency is waiting
for the first streamed content chunk, and how smoothly do later chunks arrive?

## Why this matters

End-to-end latency combines two different workloads:

- **TTFT (time to first token):** request handling, tokenization, scheduling,
  prompt prefill, and the first decode step.
- **Inter-chunk gap:** the client-observed time between streamed content chunks.
  A chunk may contain more than one tokenizer token, so this is not token
  throughput.

Do not call either number simply "model speed." A configuration can improve one
and worsen the other.

## Run

1. Start the same LM Studio OpenAI-compatible server used for Day 1 on port 8000.
2. Confirm the model in `benchmark_streaming.py` matches the server's model ID.
3. From this directory, run `python3 benchmark_streaming.py`.
4. Save the terminal output and record it below. Run it once after server start
   (cold-ish) and again after a warm-up run. Do not mix those samples.

## Results

| Condition | Runs | TTFT p50 | TTFT p95 | E2E p50 | E2E p95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| warm, sequential | 100 | 0.233 s | 0.243 s | 0.964 s | 0.999 s |

Inter-chunk gaps across the run: mean 18.26 ms, p50 18.16 ms, p95 19.02 ms,
and maximum 25.61 ms. Every response contained 40 content chunks.

## Conclusion

Under sequential single-user load, the user waited about 233 ms before output
began, roughly 24% of the median 964 ms end-to-end latency. Output then arrived
consistently, with a mean client-observed gap of 18.26 ms between content chunks;
therefore end-to-end throughput alone would not describe the initial wait a chat
user experiences.

## What to notice

- The first request may pay lazy initialization or clock/power-state costs.
- For this short prompt, TTFT should be a meaningful fraction of E2E latency.
- Content chunks are not tokenizer tokens. Actual decode tokens per second will
  require the server's `completion_tokens` usage count.

## Day 2 deliverable

Completed: a 100-request warm sequential benchmark, distribution summary, and
written conclusion.
