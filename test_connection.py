from openai import OpenAI
from dotenv import load_dotenv
import os

# Загружаем переменные окружения
load_dotenv()

# Загружаем ключи API
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE_URL = os.getenv("OPENAI_API_BASE_URL")
DEEPSEEK_MODEL = os.getenv("OPENAI_API_MODEL")

print(OPENAI_API_BASE_URL)
print(OPENAI_API_KEY)

client = OpenAI(
    base_url=OPENAI_API_BASE_URL,
    api_key=OPENAI_API_KEY
)

response = client.chat.completions.create(
    model=DEEPSEEK_MODEL,
    messages=[
        {"role": "system", "content": "Добродушный весельчак"},
        {"role": "user", "content": ""},
    ],
    max_tokens=512,
    temperature=0.6,
    top_p=0.95,
    presence_penalty=0,
    stream=True,
)
for chunk in response:
    if chunk.choices and chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
