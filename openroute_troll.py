import time
import re
import signal
import sys
import telebot
from dotenv import load_dotenv
import os
import openai

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE_URL = os.getenv("OPENAI_API_BASE_URL")
OPENAI_API_MODEL = os.getenv("OPENAI_API_MODEL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
proxy_base_url = OPENAI_API_BASE_URL+'/chat/completions'


class LLMtrol:
    """Агент для анализа задач с помощью LLM."""

    def __init__(self):
        self.client = openai.OpenAI(
            api_key=OPENAI_API_KEY, base_url=OPENAI_API_BASE_URL)

    def analyze_task(self, task: str) -> dict:
        """
        Анализирует задачу и определяет, какие инструменты нужны.
        
        :param task: Запрос
        :return: Словарь think и summary
        """
        prompt = task
        print(prompt)
        
        # Добавляем счетчик попыток для предотвращения бесконечного цикла
        max_attempts = 3
        attempts = 0
        
        while attempts < max_attempts:
            attempts += 1
            response = self.client.chat.completions.create(
                model=OPENAI_API_MODEL,
                messages=[{"role": "system", "content": "Ты AI-троль. Ты жесткий циник, можешь прямо стебаться и троллить человека. Но информацию должен давать всегда настоящую и проверенную. Отвечай коротко, много текста не нужно. Ты сидишь в чате, и развлекаешь его членов."},
                        {"role": "user", "content": prompt}]
            )
            print(response)
            
            result = response.choices[0].message.content
            
            # Проверяем, что result не пустой
            if result and result.strip():
                break
            
            # Если пустой ответ, ждем немного перед повторной попыткой
            time.sleep(2)
        
        # Если после всех попыток результат все еще пустой, используем запасной ответ
        if not result or not result.strip():
            result = "Хм, даже мой сарказм-модуль завис. Попробуй еще раз, смертный."
        
        return {"summary": result}

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
llm_agent = LLMtrol()


@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id, "Привет! Я бот. Отправь мне сообщение, и я передам его нейросети.")


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    print("ok")
    analysis = llm_agent.analyze_task(message.text)
    summary = analysis["summary"]
    # Отправляем текстовый ответ
    bot.reply_to(message, summary)


def main():
    while True:
        try:
            bot.polling(none_stop=True, timeout=25)
        except Exception:
            time.sleep(5)


def signal_handler(sig, frame):
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)  # Обработка SIGINT
    main()

