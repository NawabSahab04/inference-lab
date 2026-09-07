# One-year inference-engineering roadmap

The goal is to become someone who can form a performance hypothesis, measure it
correctly, make a targeted change, and explain the trade-off. Build the habit:
every experiment has a question, a controlled setup, raw results, and a short
conclusion.

## Monthly arc

| Months | Focus | Evidence you should produce |
| --- | --- | --- |
| 1–2 | Single-request mechanics | Reproducible TTFT, throughput, memory, and quality baselines |
| 3–4 | Serving engines and batching | Load tests; concurrency/latency curves; continuous batching analysis |
| 5–6 | Memory and model formats | KV-cache budget, quantization comparisons, OOM diagnosis |
| 7–8 | Advanced inference | Speculative decoding, prefix caching, structured output, routing |
| 9–10 | Production reliability | Metrics, tracing, queues, rate limits, overload behavior |
| 11–12 | Systems design and portfolio | A documented serving system and performance case studies |

## First week

| Day | Question | Deliverable |
| --- | --- | --- |
| 0 | Can I call a local model? | LM Studio request and response inspection |
| 1 | How fast is one vLLM request? | Non-streaming E2E baseline |
| 2 | Where does that latency go? | TTFT and decode-throughput baseline |
| 3 | Does prompt length change TTFT? | Prompt-length sweep and chart |
| 4 | Does output length change E2E time? | Output-length sweep and model of latency |
| 5 | What happens with concurrent users? | Concurrency sweep with p50/p95 latency |
| 6 | What memory limits concurrency? | VRAM/KV-cache observations and explanation |
| 7 | What did I learn? | One-page weekly report and next hypothesis |

## Rules for each lab

1. Change one independent variable at a time.
2. State model, engine version, hardware, flags, prompt, and run count.
3. Report distributions (at least p50 and p95), not a single lucky run.
4. Separate warm from cold measurements.
5. Keep raw output and write the conclusion before changing the next variable.
