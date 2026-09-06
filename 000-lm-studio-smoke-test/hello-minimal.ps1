$body = @{
    model = "gemma4-12b"
    messages = @(
        @{
            role = "user"
            content = "Say hello in exactly 3 words"
        }
    )
    temperature = 0
} | ConvertTo-Json -Depth 5

$response = Invoke-RestMethod `
  -Uri "http://127.0.0.1:1234/v1/chat/completions" `
  -Method Post `
  -ContentType "application/json" `
  -Body $body


$message = $response.choices[0].message

[PSCustomObject]@{
  visibleAnswer = $message.content
} | Format-List