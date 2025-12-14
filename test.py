from telegram_bot import TelegramBot
from config import APISettings

settings = APISettings()
print(">>> TOKEN:", repr(settings.telegram_token))
print(">>> CHAT_ID:", repr(settings.telegram_chat_id))

bot = TelegramBot(token=settings.telegram_token, chat_id=settings.telegram_chat_id)
result = bot.send_message("Тест: Прямая проверка отправки 🚀")
print(">>> SEND RESULT:", result)