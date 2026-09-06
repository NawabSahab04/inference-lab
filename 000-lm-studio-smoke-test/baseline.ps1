$body = @{
  model = "gemma4-12b"
  messages = @(
    @{
      role = "user"
      content = "What is 2 + 2? Answer using one word. Do not explain."
    }
  )
  temperature = 0
  max_tokens = 256
} | ConvertTo-Json -Depth 5

$timer = [System.Diagnostics.Stopwatch]::StartNew()

$response = Invoke-RestMethod `
  -Uri "http://127.0.0.1:1234/v1/chat/completions" `
  -Method Post `
  -ContentType "application/json" `
  -Body $body

$timer.Stop()

$message = $response.choices[0].message

[PSCustomObject]@{
  elapsedSeconds = [Math]::Round($timer.Elapsed.TotalSeconds, 3)
  visibleAnswer = $message.content
  promptTokens = $response.usage.prompt_tokens
  completionTokens = $response.usage.completion_tokens
  reasoningTokens = $response.usage.completion_tokens_details.reasoning_tokens
  finishReason = $response.choices[0].finish_reason
} | Format-List