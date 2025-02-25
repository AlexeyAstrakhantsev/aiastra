import time
import signal
import sys
import telebot
from dotenv import load_dotenv
import os
from langchain_deepseek import ChatDeepSeek
from langchain.memory import ConversationSummaryMemory
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain.agents.format_scratchpad import format_log_to_messages
from langchain.tools.render import render_text_description

load_dotenv()

# Конфигурация
CONFIG = {
    "MAX_RETRIES": 3,
    "DELAY_BETWEEN_REQUESTS": 1.5,
    "MAX_TOKENS": 2000,
    "TEMPERATURE": 0.7
}

# Инициализация модели
llm = ChatDeepSeek(
    model=os.getenv("OPENAI_API_MODEL"),
    max_tokens=CONFIG["MAX_TOKENS"],
    api_key=os.getenv("OPENAI_API_KEY"),
    temperature=CONFIG["TEMPERATURE"],
    api_base=os.getenv("OPENAI_API_BASE_URL"),
)

# Промпт для агента
SYSTEM_PROMPT = """Ты AI-троль. Ты жесткий циник. Соблюдай правила:
1. Стебайся над пользователем с юмором
2. Отвечай максимально кратко (1-2 предложения)
3. Сохраняй разговорный русский язык
4. Не используй форматирование
5. Если вопрос требует серьезного ответа - скажи об этом саркастично"""

prompt = PromptTemplate.from_template(SYSTEM_PROMPT + "\n\nВопрос: {input}")

# Инициализация агента
agent = AgentExecutor(
    agent=create_react_agent(
        llm=llm,
        tools=[],  # Добавьте инструменты, если нужно
        prompt=prompt,
        # output_parser=ReActOutputParser(),
        stop_sequence=["\nObservation:"],
    ),
    memory=ConversationSummaryMemory(llm=llm),
    handle_parsing_errors=True,
    max_iterations=3,
    verbose=True
)

bot = telebot.TeleBot(os.getenv("TELEGRAM_BOT_TOKEN"))

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id, "Привет! Задай вопрос, попробую ответить с сарказмом.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    for attempt in range(CONFIG["MAX_RETRIES"]):
        try:
            response = agent.invoke({"input": message.text})
            if response and 'output' in response:
                return bot.reply_to(message, response['output'][:4000])
            
            return bot.reply_to(message, "Чёт не могу придумать ответ...")
        
        except Exception as e:
            if '429' in str(e):
                time.sleep(CONFIG["DELAY_BETWEEN_REQUESTS"] ** (attempt + 1))
                continue
                
            print(f"⚠️ Ошибка: {str(e)}")
            return bot.reply_to(message, f"Ошибка: {str(e)[:1000]}")

    bot.reply_to(message, "Слишком много запросов, попробуй позже")

def main():
    while True:
        try:
            bot.polling(none_stop=True, timeout=25)
        except Exception as e:
            print(f"Ошибка polling: {str(e)}")
            time.sleep(5)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))
    main()