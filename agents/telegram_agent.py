import os
import logging
import telebot
from dotenv import load_dotenv

load_dotenv()

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Глобальный бот для обработки команд
bot = telebot.TeleBot(os.getenv("TELEGRAM_BOT_TOKEN"))


class TelegramAgent:
    """Агент для отправки сообщений в Telegram через бота."""

    def __init__(self) -> None:
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.bot = bot  # Используем глобальный экземпляр бота

    async def send_message(self, message: str) -> str:
        """
        Отправляет сообщение в Telegram.

        :param message: Текст сообщения
        :return: Статус отправки
        """
        try:
            self.bot.send_message(chat_id=self.chat_id, text=message)
            logger.info(f"✅ Сообщение отправлено: {message}")
            return "успешно отправлено"
        except Exception as e:
            error_msg = f"❌ Ошибка отправки сообщения: {e}"
            logger.error(error_msg)
            return error_msg


# Обработчики команд перемещены на уровень модуля
@bot.message_handler(commands=["start"])
def start_command(message):
    bot.send_message(message.chat.id, "🤖 Привет! Я ваш AI-агент.")


@bot.message_handler(commands=["help"])
def help_command(message):
    bot.send_message(
        message.chat.id,
        "📜 Доступные команды:\n"
        "/start - Запуск бота\n"
        "/help - Список команд\n"
        "/echo <текст> - Повторить ваше сообщение"
    )


if __name__ == "__main__":
    logger.info("🚀 Бот запущен и ожидает команды...")
    bot.polling(none_stop=True)
