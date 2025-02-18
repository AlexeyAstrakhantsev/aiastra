import os
import logging
from tavily import TavilyClient
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настраиваем логирование
logger = logging.getLogger(__name__)


class TavilyAgent:
    """Агент для поиска информации в интернете с помощью Tavily."""

    def __init__(self) -> None:
        self.api_key = os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            raise ValueError(
                "❌ Не указан API-ключ Tavily. ")
        self.client = TavilyClient(self.api_key)

    def search(self, query: str, max_results: int = 5) -> list[str]:
        """
        Выполняет поиск информации в интернете.

        :param query: Строка запроса.
        :param max_results: Количество результатов (по умолчанию 5).
        :return: Список URL с найденными источниками.
        """
        try:
            logger.info(f"🔍 Выполняем поиск в Tavily: {query}")
            results = self.client.search(query, max_results=max_results)
            urls = [result["url"] for result in results.get("results", [])]
            logger.info(f"✅ Найдено {len(urls)} результатов.")
            return urls
        except Exception as e:
            logger.error(f"❌ Ошибка при поиске: {e}")
            return []
