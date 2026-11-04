"""Stage 0: first LLM call. Print the answer AND the token usage."""
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic(timeout=30, max_retries=1)

response = client.messages.create(
    model="claude-haiku-5-5",
    max_tokens=20,  # hard cap on output tokens = hard cap on cost
    messages=[{"role": "user", "content": "En una frase: qué hace un AI engineer?"}],
)

print(response.content[0].text)
print("---")
print("stop_reason:", response.stop_reason)
print("input_tokens:", response.usage.input_tokens, "| output_tokens:", response.usage.output_tokens)
