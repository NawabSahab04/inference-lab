# Week 1 — Single-GPU inference characterization

## System under test

- GPU: NVIDIA GeForce RTX 5060 Ti, 16 GB VRAM
- Host memory: 16 GB DDR5
- Model: `google/gemma-4-12b-qat` (7.15 GB quantized model)
- Server: LM Studio's OpenAI-compatible API
- Client: Python benchmark programs running in WSL
- Context and parallel capacity: varied where stated; otherwise held constant

## Metric definitions

- **TTFT (time to first token):** request start to the first non-empty generated
  reasoning or content chunk.
- **TTFC (time to first content):** request start to the first user-visible
  content chunk. For this reasoning model, hidden reasoning can make TTFC later
  than TTFT. Without reasoning they may be close, but are not guaranteed equal.
- **E2E latency:** request start to completion of the response stream.
- **Decode throughput:** completion tokens after the first token divided by
  `E2E - TTFT`. This approximates the ongoing, or steady-state, decode rate
  after prefill and the first decode step.
- **Aggregate throughput:** total completion tokens from all requests divided by
  experiment wall time.

## Experimental findings

### Streaming separates startup latency from generation

In the [Day 2 benchmark](../002-streaming-latency), 100 warm sequential requests
had a TTFT p50 of 233 ms and E2E p50 of 964 ms. TTFT was about 24% of E2E,
while subsequent content chunks arrived at an average interval of 18.26 ms.
Chunks are transport units and may contain multiple tokenizer tokens, so their
spacing is not token throughput.

### Longer prompts increase prefill latency

In the [Day 3 sweep](../003-prompt-length-sweep), TTFT p50 increased from 146 ms
with 32 filler repetitions to 1.257 s with 2,048 repetitions, an 8.6x increase.
Prefill projects and stores K/V states for the prompt and performs attention
over it before generation can begin. Building the stored K/V tensors is linear
in prompt length; standard prompt attention contains quadratic work. A GPU
changes execution speed and parallelism, not those algorithmic complexities.

### Longer outputs increase E2E latency

In the [Day 4 sweep](../004-output-length-sweep), increasing the completion from
16 to 256 tokens raised E2E p50 from 391 ms to 5.330 s. Approximate decode
throughput ranged from 49 to 59 tokens/s. Longer runs better represent
steady-state decoding because fixed stream and finalization costs distort short
runs more strongly.

Day 4 held the prompt constant; it did not show that decode is independent of
prompt length. Each new token attends to the cached K/V states of the prompt and
all prior generated tokens. A longer starting prompt therefore increases the
memory traffic and work of every decode step.

### Concurrency improves throughput until the server saturates

The [Day 5 sweep](../005-concurrency-sweep) produced the following results for
20 requests with 64 completion tokens each:

| Concurrency | TTFT p50 | E2E p50 | Aggregate tok/s |
| ---: | ---: | ---: | ---: |
| 1 | 0.132 s | 1.503 s | 42.50 |
| 2 | 0.176 s | 1.620 s | 78.84 |
| 4 | 0.228 s | 1.807 s | 141.02 |
| 8 | 1.917 s | 3.376 s | 147.70 |

The server batches work from multiple active sequences into larger GPU
operations. This increased hardware utilization and amortized overhead; it was
not individual GPU cores switching independently between requests. Throughput
scaled well through the configured capacity of four active sequences. Going
from concurrency four to eight added only 4.7% throughput while TTFT p50 rose
8.4x because excess requests waited for sequence slots.

### Context capacity is reserved memory, not prompt content

The [Day 6 measurements](../006-vram-kv-cache) found 8,385 MiB idle VRAM at a
32,768-token context with parallel capacity one, versus 13,132 MiB at a
262,144-token context with capacity four. The configured context is the maximum
available capacity; it is not automatically appended to each prompt.

During generation, allocated VRAM varied by only 7 MiB because LM Studio had
already reserved most serving memory. Tokens filled preallocated buffers, which
changed their contents without substantially changing the allocation reported
by `nvidia-smi`. This does not mean the populated KV cache itself used only
7 MiB.

## Performance model

For a request:

```text
E2E latency = queue time + prefill time + decode time
decode time ≈ sum(time per token at that token's current context length)
```

Prompt length mainly raises prefill and the cost of each later decode step.
Output length increases the number of sequential decode steps. Concurrency can
raise aggregate throughput through batching, but after active-sequence capacity
is full it primarily adds queue time and worsens tail latency.

## Limitations

- All timings are client-observed and include local HTTP and parsing overhead.
- Day 3 used filler repetitions rather than exact tokenizer-token counts.
- The tests used one model, quantization, GPU, server, and mostly one workload.
- The benchmarks were closed-loop bursts, not an open-loop arrival process.
- LM Studio exposes limited server-side scheduling and kernel-level timing.
- `nvidia-smi` allocation does not isolate model weights, KV cache, compute
  buffers, fragmentation, or allocator overhead.

## Next hypothesis

At a fixed 32,768-token context and concurrency eight, reducing LM Studio's
parallel capacity from four to one should reduce idle VRAM by approximately
447 MiB, based on Day 6. Aggregate throughput should fall toward single-request
throughput, while TTFT p50 and p95 should rise because eight requests must pass
through one active-sequence slot instead of four. An admitted request may decode
slightly faster without sharing a batch, but queueing should dominate its total
latency.
