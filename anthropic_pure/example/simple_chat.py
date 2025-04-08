import anthropic
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-3-5-haiku-20241022",
    max_tokens=100,
    messages=[
        {
            "role": "user",
            "content": "Hey Claude, tell me a short fun fact about video games!",
        }
    ]
)
print(response.content)