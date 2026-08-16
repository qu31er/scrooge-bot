import telebot
import threading
import config
from handlers import register_all_handlers
from functions import autoposting

bot = telebot.TeleBot(config.BOT_TOKEN, parse_mode="HTML")

register_all_handlers(bot)

threading.Thread(target=autoposting, args=(bot, None), daemon=True).start()

if __name__ == '__main__':
    bot.remove_webhook()
    print("бот запущен")
    bot.polling(none_stop=True, interval=1)