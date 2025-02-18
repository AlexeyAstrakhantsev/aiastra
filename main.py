import logging
from agents.langchain_agent import build_agent_chain
from agents.telegram_agent import bot

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем цепочку LangChain
agent_chain = build_agent_chain()


def process_task(task_description: str):
    """Обрабатывает задачу с помощью цепочки LangChain."""
    initial_input = {"task_description": task_description}
    logger.info(f"🎯 Новая задача: {task_description}")

    result = agent_chain.invoke(initial_input)

    logger.info(f"📢 Результат выполнения: {result}")
    print(result)

    return result.get("response", "⚠️ Произошла ошибка при выполнении задачи")


@bot.message_handler(commands=['task'])
def handle_task_command(message):
    """Обрабатывает команду /task <описание_задачи>."""
    task_description = message.text.replace("/task", "").strip()
    if not task_description:
        bot.reply_to(message, "⚠️ Укажите описание задачи после команды /task")
        return

    bot.reply_to(message, f"⏳ Анализирую задачу: {task_description}")
    result = process_task(task_description)
    bot.send_message(message.chat.id, result)


def main():
    """Запуск бота для обработки входящих сообщений."""
    logger.info("🚀 AI-агент запущен!")
    bot.polling(none_stop=True)


if __name__ == "__main__":
    main()
