const body = {
  model: "gemma4-12b",
  messages: [
    {
      role: "user",
      content: "What is 2 + 2? Answer using one word. Do not explain."
    }
  ],
  temperature: 0,
  max_tokens: 256
};

const started = performance.now();

const response = await fetch("http://127.0.0.1:1234/v1/chat/completions", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body)
});

const result = await response.json();
const elapsedSeconds = (performance.now() - started) / 1000;

const message = result.choices[0].message;
const usage = result.usage;

console.log({
  elapsedSeconds: elapsedSeconds.toFixed(3),
  visibleAnswer: message.content,
  promptTokens: usage.prompt_tokens,
  completionTokens: usage.completion_tokens,
  reasoningTokens: usage.completion_tokens_details?.reasoning_tokens ?? 0,
  finishReason: result.choices[0].finish_reason
});