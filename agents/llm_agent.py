import os
import openai
from dotenv import load_dotenv
import re
import json


load_dotenv()

# Настройки API-ключа
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE_URL = os.getenv("OPENAI_API_BASE_URL")
OPENAI_API_MODEL = os.getenv("OPENAI_API_MODEL")


class LLMAgent:
    """Агент для анализа задач с помощью LLM."""

    def models_list(self) -> str:
        """Возвращает список доступных моделей в виде строки."""
        self.client = openai.OpenAI(
            api_key=OPENAI_API_KEY, base_url=OPENAI_API_BASE_URL)
        models = self.client.models.list()

        return "\n".join(model.id for model in models.data)

    def __init__(self):
        self.client = openai.OpenAI(
            api_key=OPENAI_API_KEY, base_url=OPENAI_API_BASE_URL)

    def analyze_task(self, task_description: str) -> dict:
        """
        Анализирует задачу и определяет, какие инструменты нужны.

        :param task_description: Описание задачи
        :return: Словарь с анализом и рекомендациями
        """
        prompt = f"""
        Ты AI-ассистент. Получив задачу, ты должен определить,
        какие инструменты (GitHub, Twitter, Telegram, Tavily)
        нужно использовать для её выполнения, и использовать эти инструменты

        Пример вывода:
        {{
            "summary": "Задача требует публикации в Twitter
                        и уведомления в Telegram.",
            "tools": ["twitter", "telegram"]
        }}

        Важно: верни только этот формат, без дополнительных пояснений!
        Входная задача: {task_description}
        """

        response = self.client.chat.completions.create(
            model=OPENAI_API_MODEL,
            messages=[{"role": "system", "content": "Ты помощник AI."},
                      {"role": "user", "content": prompt}]
        )

        result = response.choices[0].message.content
        # Извлекаем <think>...</think>
        think_match = re.search(r"<think>(.*?)</think>", result, re.DOTALL)
        think_text = think_match.group(1).strip() if think_match else ""

        # Извлекаем JSON
        json_match = re.search(r"(\{.*?\})", result, re.DOTALL)
        json_text = json_match.group(1) if json_match else "{}"

        # Преобразуем JSON в словарь
        try:
            json_data = json.loads(json_text)
        except json.JSONDecodeError:
            print("❌ Ошибка: Модель вернула некорректный JSON!")
            print("Ответ модели:", result)
            json_data = {"summary": "Ошибка обработки", "tools": []}

        return {
            "think": think_text,
            "summary": json_data.get("summary", ""),
            "tools": json_data.get("tools", [])
        }
