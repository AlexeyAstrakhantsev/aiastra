import os
import openai
from dotenv import load_dotenv

load_dotenv()


class LLM:
    """Класс для работы с OpenAI GPT API."""

    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY")
        openai.api_key = self.api_key

    def generate_text(self, prompt: str) -> str:
        """
        Генерирует текст с помощью OpenAI GPT.

        :param prompt: Входная строка для генерации
        :return: Сгенерированный ответ
        """
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
        )
        return response["choices"][0]["message"]["content"].strip()
