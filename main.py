import telebot
from telebot import types
import time
import threading
import sys
import os

import config
from database import Database
from crypto import CryptoBot
from handlers import register_all_handlers
from functions import autoposting

# инициализация конфигов
bot = telebot.TeleBot(config.BOT_TOKEN, parse_mode="HTML")
db = Database()
crypto = CryptoBot()

print("Бот запускается...")
print(f"Бот: @{bot.get_me().username}")
print(f"Админы: {config.ADMIN_IDS}")
print(f"Комиссия: {config.COMMISSION}%")

# регистрация обработчиков
register_all_handlers(bot, db, crypto)

# запуск фоновых задач
def start_background():
    thread = threading.Thread(target=autoposting, args=(bot, db), daemon=True)
    thread.start()
    print("Фоновые задачи запущены")

start_background()

if __name__ == '__main__':
    if config.WEBHOOK_URL:
        # режим вебхука
        from flask import Flask, request
        app = Flask(__name__)
        
        bot.remove_webhook()
        time.sleep(1)
        bot.set_webhook(url=f"{config.WEBHOOK_URL}/webhook")
        print(f"вебхук установлен: {config.WEBHOOK_URL}/webhook")
        
        @app.route('/webhook', methods=['POST'])
        def webhook():
            update = types.Update.de_json(request.stream.read().decode('utf-8'))
            bot.process_new_updates([update])
            return 'OK', 200
        
        @app.route('/health', methods=['GET'])
        def health():
            return 'OK', 200
        
        app.run(host='0.0.0.0', port=config.PORT)
    else:
        #polling
        print("запуск в режиме polling")
        bot.polling(none_stop=True, interval=1)