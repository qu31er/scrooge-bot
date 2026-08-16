import telebot
import time
import threading
import config
from database import Database
from crypto import CryptoBot
from handlers import register_all_handlers
from functions import autoposting

bot = telebot.TeleBot(config.BOT_TOKEN, parse_mode="HTML")
db = Database()
crypto = CryptoBot()

print("бот запускается")
print(f"бот: @{bot.get_me().username}")
print(f"админы: {config.ADMIN_IDS}")

# регистрируем обработчики
register_all_handlers(bot, db, crypto)

# запуск автопостинга
thread = threading.Thread(target=autoposting, args=(bot, db), daemon=True)
thread.start()
print("автопостинг запущен")

if __name__ == '__main__':
    # удаляем вебхук
    bot.remove_webhook()
    print("вебхук удален")
    
    # запускаем polling
    print("бот запущен")
    bot.polling(none_stop=True, interval=1)