"""Stage 0: list the models available to this API key (no token cost)."""
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()  # reads .env into environment variables; the key never appears in code
client = Anthropic()  # picks up ANTHROPIC_API_KEY from the environment

for m in client.models.list(limit=20):
    print(m.id, "-", m.display_name)
